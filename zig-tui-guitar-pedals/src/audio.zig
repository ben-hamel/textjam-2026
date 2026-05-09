const std = @import("std");
const ma = @cImport(@cInclude("miniaudio.h"));

const RING_SIZE: u32 = 8192;
const RING_MASK: u32 = RING_SIZE - 1;

pub const SharedState = struct {
    gain: std.atomic.Value(f32) = .init(0.5),
    tone: std.atomic.Value(f32) = .init(0.5),
    volume: std.atomic.Value(f32) = .init(0.5),
    bypassed: std.atomic.Value(bool) = .init(false),
    running: std.atomic.Value(bool) = .init(true),
    // audio-thread-only filter state
    prev: f32 = 0.0,
    // lock-free ring buffer: source -> playback
    ring_buf: [RING_SIZE]f32 = [_]f32{0.0} ** RING_SIZE,
    ring_write: std.atomic.Value(u32) = .init(0),
    ring_read: std.atomic.Value(u32) = .init(0),
};

pub const AudioEngine = struct {
    capture: ?ma.ma_device,
    playback: ma.ma_device,

    pub fn init(state: *SharedState, file_path: ?[*:0]const u8) !AudioEngine {
        var engine: AudioEngine = .{ .capture = null, .playback = undefined };

        if (file_path) |path| {
            const t = try std.Thread.spawn(.{}, fileLooper, .{ state, path });
            t.detach();
        } else {
            var cap_cfg = ma.ma_device_config_init(ma.ma_device_type_capture);
            cap_cfg.capture.format = ma.ma_format_f32;
            cap_cfg.capture.channels = 1;
            cap_cfg.sampleRate = 44100;
            cap_cfg.dataCallback = captureCallback;
            cap_cfg.pUserData = state;

            engine.capture = undefined;
            if (ma.ma_device_init(null, &cap_cfg, &engine.capture.?) != ma.MA_SUCCESS)
                return error.CaptureInitFailed;
        }

        var play_cfg = ma.ma_device_config_init(ma.ma_device_type_playback);
        play_cfg.playback.format = ma.ma_format_f32;
        play_cfg.playback.channels = 1;
        play_cfg.sampleRate = 44100;
        play_cfg.dataCallback = playbackCallback;
        play_cfg.pUserData = state;

        if (ma.ma_device_init(null, &play_cfg, &engine.playback) != ma.MA_SUCCESS) {
            if (engine.capture) |*cap| ma.ma_device_uninit(cap);
            return error.PlaybackInitFailed;
        }

        if (engine.capture) |*cap| {
            if (ma.ma_device_start(cap) != ma.MA_SUCCESS) {
                ma.ma_device_uninit(cap);
                ma.ma_device_uninit(&engine.playback);
                return error.CaptureStartFailed;
            }
        }

        if (ma.ma_device_start(&engine.playback) != ma.MA_SUCCESS) {
            if (engine.capture) |*cap| ma.ma_device_uninit(cap);
            ma.ma_device_uninit(&engine.playback);
            return error.PlaybackStartFailed;
        }

        return engine;
    }

    pub fn deinit(self: *AudioEngine) void {
        if (self.capture) |*cap| ma.ma_device_uninit(cap);
        ma.ma_device_uninit(&self.playback);
    }
};

fn pushSample(state: *SharedState, s: f32) void {
    while (state.running.load(.acquire)) {
        const w = state.ring_write.load(.acquire);
        if (w -% state.ring_read.load(.acquire) < RING_SIZE) {
            state.ring_buf[w & RING_MASK] = s;
            state.ring_write.store(w +% 1, .release);
            return;
        }
        std.Thread.yield() catch {};
    }
}

fn fileLooper(state: *SharedState, path: [*:0]const u8) void {
    var cfg = ma.ma_decoder_config_init(ma.ma_format_f32, 1, 44100);
    var decoder: ma.ma_decoder = undefined;
    if (ma.ma_decoder_init_file(path, &cfg, &decoder) != ma.MA_SUCCESS) return;
    defer _ = ma.ma_decoder_uninit(&decoder);

    var buf: [512]f32 = undefined;
    while (state.running.load(.acquire)) {
        var frames_read: ma.ma_uint64 = 0;
        const result = ma.ma_decoder_read_pcm_frames(&decoder, &buf, buf.len, &frames_read);
        for (buf[0..@intCast(frames_read)]) |s| pushSample(state, s);
        if (result == ma.MA_AT_END or frames_read == 0)
            _ = ma.ma_decoder_seek_to_pcm_frame(&decoder, 0);
    }
}

fn captureCallback(
    device: [*c]ma.ma_device,
    _: ?*anyopaque,
    input: ?*const anyopaque,
    frame_count: ma.ma_uint32,
) callconv(.c) void {
    const state: *SharedState = @ptrCast(@alignCast(device.*.pUserData));
    const in_buf: [*]const f32 = @ptrCast(@alignCast(input));
    for (in_buf[0..frame_count]) |s| {
        const w = state.ring_write.load(.acquire);
        if (w -% state.ring_read.load(.acquire) < RING_SIZE) {
            state.ring_buf[w & RING_MASK] = s;
            state.ring_write.store(w +% 1, .release);
        }
    }
}

fn playbackCallback(
    device: [*c]ma.ma_device,
    output: ?*anyopaque,
    _: ?*const anyopaque,
    frame_count: ma.ma_uint32,
) callconv(.c) void {
    const state: *SharedState = @ptrCast(@alignCast(device.*.pUserData));
    const out_buf: [*]f32 = @ptrCast(@alignCast(output));

    for (out_buf[0..frame_count]) |*s| {
        const r = state.ring_read.load(.acquire);
        if (r != state.ring_write.load(.acquire)) {
            s.* = state.ring_buf[r & RING_MASK];
            state.ring_read.store(r +% 1, .release);
        } else {
            s.* = 0.0;
        }
    }

    if (state.bypassed.load(.acquire)) return;

    const gain = state.gain.load(.acquire);
    const tone = state.tone.load(.acquire);
    const volume = state.volume.load(.acquire);
    const alpha = std.math.clamp(tone, 0.01, 0.99);

    for (out_buf[0..frame_count]) |*s| {
        const driven = std.math.tanh(s.* * (1.0 + gain * 19.0));
        state.prev = (1.0 - alpha) * state.prev + alpha * driven;
        s.* = state.prev * volume;
    }
}
