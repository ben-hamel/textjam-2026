use anyhow::Result;
use crossterm::event::{self, Event, KeyCode, KeyEventKind};
use ratatui::layout::{Alignment, Constraint, Direction, Layout};
use ratatui::style::{Color, Modifier, Style};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Borders, Gauge, Paragraph};
use ratatui::Frame;
use std::sync::{Arc, Mutex};
use std::time::Duration;

use crate::pedal::FuzzPedal;

const KNOBS: [&str; 3] = ["GAIN", "TONE", "VOLUME"];
const STEP: f32 = 0.05;

pub struct App {
    pedal: Arc<Mutex<FuzzPedal>>,
    selected: usize,
}

impl App {
    pub fn new(pedal: Arc<Mutex<FuzzPedal>>) -> Self {
        Self { pedal, selected: 0 }
    }

    pub fn run<B: ratatui::backend::Backend>(&mut self, terminal: &mut ratatui::Terminal<B>) -> Result<()> {
        loop {
            terminal.draw(|f| self.draw(f))?;

            if event::poll(Duration::from_millis(50))? {
                if let Event::Key(key) = event::read()? {
                    if key.kind != KeyEventKind::Press {
                        continue;
                    }
                    match key.code {
                        KeyCode::Char('q') => return Ok(()),
                        KeyCode::Left => self.selected = self.selected.saturating_sub(1),
                        KeyCode::Right => {
                            if self.selected + 1 < KNOBS.len() {
                                self.selected += 1;
                            }
                        }
                        KeyCode::Up => self.adjust(STEP),
                        KeyCode::Down => self.adjust(-STEP),
                        KeyCode::Char(' ') => {
                            let mut p = self.pedal.lock().unwrap();
                            p.bypassed = !p.bypassed;
                        }
                        _ => {}
                    }
                }
            }
        }
    }

    fn adjust(&self, delta: f32) {
        let mut p = self.pedal.lock().unwrap();
        let val = match self.selected {
            0 => &mut p.gain,
            1 => &mut p.tone,
            _ => &mut p.volume,
        };
        *val = (*val + delta).clamp(0.0, 1.0);
    }

    fn draw(&self, f: &mut Frame) {
        let p = self.pedal.lock().unwrap();
        let (gain, tone, volume, bypassed) = (p.gain, p.tone, p.volume, p.bypassed);
        drop(p);

        let area = f.area();
        let block = Block::default()
            .borders(Borders::ALL)
            .title(" FUZZ PEDAL ");
        let inner = block.inner(area);
        f.render_widget(block, area);

        let rows = Layout::default()
            .direction(Direction::Vertical)
            .constraints([
                Constraint::Length(1),
                Constraint::Length(3),
                Constraint::Length(1),
                Constraint::Length(1),
                Constraint::Length(1),
                Constraint::Min(0),
                Constraint::Length(1),
            ])
            .split(inner);

        let knob_values = [gain, tone, volume];
        let cols = Layout::default()
            .direction(Direction::Horizontal)
            .constraints([
                Constraint::Ratio(1, 3),
                Constraint::Ratio(1, 3),
                Constraint::Ratio(1, 3),
            ])
            .split(rows[1]);

        for (i, (&name, &val)) in KNOBS.iter().zip(knob_values.iter()).enumerate() {
            let selected = i == self.selected;
            let style = if selected {
                Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD)
            } else {
                Style::default()
            };
            let gauge = Gauge::default()
                .block(Block::default().title(name).title_alignment(Alignment::Center))
                .gauge_style(style)
                .ratio(val as f64)
                .label(format!("{:.2}", val));
            f.render_widget(gauge, cols[i]);
        }

        let (bypass_sym, bypass_label, bypass_color) = if bypassed {
            ("○", "BYPASS", Color::DarkGray)
        } else {
            ("◉", "ENGAGED", Color::Green)
        };

        let status = Paragraph::new(Line::from(vec![
            Span::styled(bypass_sym, Style::default().fg(bypass_color)),
            Span::raw("  "),
            Span::styled(bypass_label, Style::default().fg(bypass_color).add_modifier(Modifier::BOLD)),
        ]))
        .alignment(Alignment::Center);
        f.render_widget(status, rows[3]);

        let hint = Paragraph::new("← → knob   ↑ ↓ adjust   space bypass   q quit")
            .alignment(Alignment::Center)
            .style(Style::default().fg(Color::DarkGray));
        f.render_widget(hint, rows[6]);
    }
}
