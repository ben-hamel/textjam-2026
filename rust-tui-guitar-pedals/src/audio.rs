use anyhow::Result;
use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};
use cpal::{Stream, StreamConfig};
use ringbuf::{HeapRb, traits::{Consumer, Producer, Split}};
use std::path::PathBuf;
use std::sync::{Arc, Mutex};

use crate::pedal::FuzzPedal;

pub struct AudioEngine {
    _input_stream: Option<Stream>,
    _output_stream: Stream,
    _file_thread: Option<std::thread::JoinHandle<()>>,
}

impl AudioEngine {
    pub fn new(pedal: Arc<Mutex<FuzzPedal>>, file_path: Option<PathBuf>) -> Result<Self> {
        let host = cpal::default_host();
        let output_device = host.default_output_device().ok_or_else(|| anyhow::anyhow!("no output device"))?;

        let config = StreamConfig {
            channels: 1,
            sample_rate: cpal::SampleRate(44100),
            buffer_size: cpal::BufferSize::Fixed(256),
        };

        let ring = HeapRb::<f32>::new(8192);
        let (mut prod, mut cons) = ring.split();

        let (input_stream, file_thread) = if let Some(path) = file_path {
            let reader = hound::WavReader::open(&path)?;
            let spec = reader.spec();
            let channels = spec.channels as usize;

            let samples: Vec<f32> = match spec.sample_format {
                hound::SampleFormat::Float => {
                    reader.into_samples::<f32>().map(|s| s.unwrap()).collect()
                }
                hound::SampleFormat::Int => {
                    let max = (1u32 << (spec.bits_per_sample - 1)) as f32;
                    reader.into_samples::<i32>().map(|s| s.unwrap() as f32 / max).collect()
                }
            };

            let frames = samples.len() / channels;
            let handle = std::thread::spawn(move || {
                let mut frame = 0;
                loop {
                    let mut mono = 0.0f32;
                    for c in 0..channels {
                        mono += samples[frame * channels + c];
                    }
                    mono /= channels as f32;

                    while prod.try_push(mono).is_err() {
                        std::thread::sleep(std::time::Duration::from_micros(100));
                    }

                    frame = (frame + 1) % frames;
                }
            });

            (None, Some(handle))
        } else {
            let input_device = host.default_input_device()
                .ok_or_else(|| anyhow::anyhow!("no input device"))?;
            let stream = input_device.build_input_stream(
                &config,
                move |data: &[f32], _| {
                    for &s in data {
                        let _ = prod.try_push(s);
                    }
                },
                |e| eprintln!("input error: {e}"),
                None,
            )?;
            stream.play()?;
            (Some(stream), None)
        };

        let output_stream = output_device.build_output_stream(
            &config,
            move |data: &mut [f32], _| {
                for s in data.iter_mut() {
                    *s = cons.try_pop().unwrap_or(0.0);
                }
                if let Ok(mut p) = pedal.try_lock() {
                    p.process(data);
                }
            },
            |e| eprintln!("output error: {e}"),
            None,
        )?;

        output_stream.play()?;

        Ok(Self {
            _input_stream: input_stream,
            _output_stream: output_stream,
            _file_thread: file_thread,
        })
    }
}
