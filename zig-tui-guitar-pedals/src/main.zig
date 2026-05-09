const std = @import("std");
const audio = @import("audio.zig");

const c = @cImport({
    @cInclude("sys/ioctl.h");
    @cInclude("termios.h");
    @cInclude("unistd.h");
    @cInclude("poll.h");
});

const KNOBS = [_][]const u8{ "GAIN", "TONE", "VOLUME" };
const STEP: f32 = 0.05;

var orig_termios: c.struct_termios = undefined;

fn enableRawMode() void {
    _ = c.tcgetattr(c.STDIN_FILENO, &orig_termios);
    var raw = orig_termios;
    raw.c_lflag &= ~@as(c_ulong, @intCast(c.ECHO | c.ICANON));
    raw.c_cc[c.VMIN] = 0;
    raw.c_cc[c.VTIME] = 0;
    _ = c.tcsetattr(c.STDIN_FILENO, c.TCSAFLUSH, &raw);
}

fn disableRawMode() void {
    _ = c.tcsetattr(c.STDIN_FILENO, c.TCSAFLUSH, &orig_termios);
}

fn termSize() struct { cols: u16, rows: u16 } {
    var ws: c.winsize = undefined;
    _ = c.ioctl(c.STDOUT_FILENO, c.TIOCGWINSZ, &ws);
    return .{ .cols = ws.ws_col, .rows = ws.ws_row };
}

fn pollKey(timeout_ms: i32) ?u8 {
    var fds = [1]c.struct_pollfd{.{
        .fd = c.STDIN_FILENO,
        .events = c.POLLIN,
        .revents = 0,
    }};
    const ready = c.poll(&fds, 1, timeout_ms);
    if (ready <= 0) return null;
    var byte: u8 = 0;
    _ = c.read(c.STDIN_FILENO, &byte, 1);
    return byte;
}

fn readEscapeSeq() ?u8 {
    const b1 = pollKey(10) orelse return null;
    if (b1 != '[') return null;
    const b2 = pollKey(10) orelse return null;
    return b2;
}

fn write(s: []const u8) void {
    _ = c.write(c.STDOUT_FILENO, s.ptr, s.len);
}

fn writeFmt(comptime fmt: []const u8, args: anytype) void {
    var buf: [256]u8 = undefined;
    const s = std.fmt.bufPrint(&buf, fmt, args) catch return;
    write(s);
}

fn moveTo(row: u16, col: u16) void {
    writeFmt("\x1b[{d};{d}H", .{ row, col });
}

fn gauge(val: f32, width: u16, selected: bool) void {
    const filled: u16 = @intFromFloat(@as(f32, @floatFromInt(width)) * val);
    if (selected) write("\x1b[33;1m") else write("\x1b[0m");
    var i: u16 = 0;
    while (i < width) : (i += 1) {
        if (i < filled) write("█") else write("░");
    }
    write("\x1b[0m");
}

fn drawUI(state: *audio.SharedState, selected: usize, cols: u16, rows: u16) void {
    const gain = state.gain.load(.acquire);
    const tone = state.tone.load(.acquire);
    const volume = state.volume.load(.acquire);
    const bypassed = state.bypassed.load(.acquire);

    write("\x1b[2J");
    write("\x1b[?25l");

    const box_w = @min(cols -| 2, 60);
    const box_h: u16 = 12;
    const left: u16 = (cols -| box_w) / 2 + 1;
    const top: u16 = (rows -| box_h) / 2 + 1;

    // top border
    moveTo(top, left);
    write("┌");
    writeFmt("\x1b[{d}b", .{box_w - 2});
    write("─");
    write("┐");

    // title
    const title = " FUZZ PEDAL ";
    const title_col = left + (box_w - @as(u16, @intCast(title.len))) / 2;
    moveTo(top, title_col);
    write(title);

    // side borders
    var r: u16 = 1;
    while (r < box_h - 1) : (r += 1) {
        moveTo(top + r, left);
        write("│");
        moveTo(top + r, left + box_w - 1);
        write("│");
    }

    // bottom border
    moveTo(top + box_h - 1, left);
    write("└");
    writeFmt("\x1b[{d}b", .{box_w - 2});
    write("─");
    write("┘");

    // knobs
    const knob_w: u16 = (box_w - 6) / 3;
    const knob_values = [_]f32{ gain, tone, volume };
    for (KNOBS, 0..) |name, i| {
        const kx = left + 2 + @as(u16, @intCast(i)) * (knob_w + 1);
        const ky = top + 2;

        const label_col = kx + (knob_w -| @as(u16, @intCast(name.len))) / 2;
        moveTo(ky, label_col);
        if (i == selected) write("\x1b[33;1m") else write("\x1b[0m");
        write(name);
        write("\x1b[0m");

        moveTo(ky + 1, kx);
        gauge(knob_values[i], knob_w, i == selected);

        moveTo(ky + 2, kx + (knob_w -| 4) / 2);
        writeFmt("{d:.2}", .{knob_values[i]});
    }

    // bypass status
    const bypass_row = top + 6;
    const status_label = if (bypassed) "○  BYPASS" else "◉  ENGAGED";
    const status_col = left + (box_w -| @as(u16, @intCast(status_label.len))) / 2;
    moveTo(bypass_row, status_col);
    if (bypassed) write("\x1b[90m") else write("\x1b[32;1m");
    write(status_label);
    write("\x1b[0m");

    // hint
    const hint = "← → knob   ↑ ↓ adjust   space bypass   q quit";
    const hint_col = left + (box_w -| @as(u16, @intCast(hint.len))) / 2;
    moveTo(top + box_h - 2, hint_col);
    write("\x1b[90m");
    write(hint);
    write("\x1b[0m");

    moveTo(rows, 1);
}

fn adjustParam(state: *audio.SharedState, sel: usize, delta: f32) void {
    const ptr = switch (sel) {
        0 => &state.gain,
        1 => &state.tone,
        else => &state.volume,
    };
    const old = ptr.load(.acquire);
    ptr.store(std.math.clamp(old + delta, 0.0, 1.0), .release);
}

pub fn main() !void {
    var state = audio.SharedState{};
    var engine = try audio.AudioEngine.init(&state);
    defer engine.deinit();

    enableRawMode();
    defer disableRawMode();
    defer write("\x1b[?25h");

    var selected: usize = 0;

    while (true) {
        const sz = termSize();
        drawUI(&state, selected, sz.cols, sz.rows);

        const key = pollKey(50) orelse continue;

        if (key == 'q') break;

        if (key == ' ') {
            const cur = state.bypassed.load(.acquire);
            state.bypassed.store(!cur, .release);
            continue;
        }

        if (key == 0x1b) {
            const seq = readEscapeSeq() orelse continue;
            switch (seq) {
                'D' => if (selected > 0) { selected -= 1; },
                'C' => if (selected + 1 < KNOBS.len) { selected += 1; },
                'A' => adjustParam(&state, selected, STEP),
                'B' => adjustParam(&state, selected, -STEP),
                else => {},
            }
        }
    }

    write("\x1b[2J\x1b[H");
}
