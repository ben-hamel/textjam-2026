const std = @import("std");
const ma = @cImport(@cInclude("miniaudio.h"));

const RING_SIZE: u32 = 8192;
const RING_MASK: u32 = RING_SIZE - 1;

pub const SharedState = struct {
    gain: std.atomic.Value(f32) = .init(0.5),
    tone: std.atomic.Value(f32) = .init(0.5),
    volume: std.atomic.Value(f32) = .init(0.5),
    bypassed: std.atomic.Value(bool) = .init(false),
    // audio-thread-only filter state
    prev: f32 = 0.0,
    // lock-free ring buffer: capture -> playback
    ring_buf: [RING_SIZE]f32 = [_]f32{0.0} ** RING_SIZE,
    ring_write: std.atomic.Value(u32) = .init(0),
    ring_read: std.atomic.Value(u32) = .init(0),
};

pub const AudioEngine = struct {
    capture: ma.ma_device,
    playback: ma.ma_device,

    pub fn init(state: *SharedState) !AudioEngine {
        var engine: AudioEngine = undefined;

        var cap_cfg = ma.ma_device_config_init(ma.ma_device_type_capture);
        cap_cfg.capture.format = ma.ma_format_f32;
        cap_cfg.capture.channels = 1;
        cap_cfg.sampleRate = 44100;
        cap_cfg.dataCallback = captureCallback;
        cap_cfg.pUserData = state;

        if (ma.ma_device_init(null, &cap_cfg, &engine.capture) != ma.MA_SUCCESS)
            return error.CaptureInitFailed;

        var play_cfg = ma.ma_device_config_init(ma.ma_device_type_playback);
        play_cfg.playback.format = ma.ma_format_f32;
        play_cfg.playback.channels = 1;
        play_cfg.sampleRate = 44100;
        play_cfg.dataCallback = playbackCallback;
        play_cfg.pUserData = state;

        if (ma.ma_device_init(null, &play_cfg, &engine.playback) != ma.MA_SUCCESS) {
            ma.ma_device_uninit(&engine.capture);
            return error.PlaybackInitFailed;
        }

        if (ma.ma_device_start(&engine.capture) != ma.MA_SUCCESS or
            ma.ma_device_start(&engine.playback) != ma.MA_SUCCESS)
        {
            ma.ma_device_uninit(&engine.capture);
            ma.ma_device_uninit(&engine.playback);
            return error.AudioStartFailed;
        }

        return engine;
    }

    pub fn deinit(self: *AudioEngine) void {
        ma.ma_device_uninit(&self.capture);
        ma.ma_device_uninit(&self.playback);
    }
};

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
