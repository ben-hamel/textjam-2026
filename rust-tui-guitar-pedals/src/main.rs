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
    let args: Vec<String> = std::env::args().collect();
    let file_path = args.windows(2)
        .find(|w| w[0] == "--file")
        .map(|w| std::path::PathBuf::from(&w[1]));

    let pedal = Arc::new(Mutex::new(FuzzPedal::new()));
    let _engine = AudioEngine::new(Arc::clone(&pedal), file_path)?;

    enable_raw_mode()?;
    stdout().execute(EnterAlternateScreen)?;
    let backend = CrosstermBackend::new(stdout());
    let mut terminal = Terminal::new(backend)?;

    let result = App::new(Arc::clone(&pedal)).run(&mut terminal);

    disable_raw_mode()?;
    stdout().execute(LeaveAlternateScreen)?;

    result
}
