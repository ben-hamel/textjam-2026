const std = @import("std");
const audio = @import("audio.zig");
const App = @import("app.zig").App;

const c = @cImport({
    @cInclude("termios.h");
    @cInclude("unistd.h");
});

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

pub fn main(init: std.process.Init) !void {
    const arena = init.arena.allocator();
    const args = try init.minimal.args.toSlice(arena);

    var file_path: ?[*:0]const u8 = null;
    var i: usize = 1;
    while (i < args.len) : (i += 1) {
        if (std.mem.eql(u8, args[i], "--file") and i + 1 < args.len) {
            file_path = args[i + 1].ptr;
            i += 1;
        }
    }

    var state = audio.SharedState{};
    var engine = try audio.AudioEngine.init(&state, file_path);
    defer engine.deinit();

    enableRawMode();
    defer disableRawMode();

    var app = App.init(&state);
    app.run();
}
