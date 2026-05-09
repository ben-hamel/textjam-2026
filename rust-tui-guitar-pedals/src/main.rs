mod app;
mod audio;
mod pedal;

use anyhow::Result;
use crossterm::terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen};
use crossterm::ExecutableCommand;
use ratatui::backend::CrosstermBackend;
use ratatui::Terminal;
use std::io::stdout;
use std::sync::{Arc, Mutex};

use app::App;
use audio::AudioEngine;
use pedal::FuzzPedal;

fn main() -> Result<()> {
    let pedal = Arc::new(Mutex::new(FuzzPedal::new()));
    let _engine = AudioEngine::new(Arc::clone(&pedal))?;

    enable_raw_mode()?;
    stdout().execute(EnterAlternateScreen)?;
    let backend = CrosstermBackend::new(stdout());
    let mut terminal = Terminal::new(backend)?;

    let result = App::new(Arc::clone(&pedal)).run(&mut terminal);

    disable_raw_mode()?;
    stdout().execute(LeaveAlternateScreen)?;

    result
}
