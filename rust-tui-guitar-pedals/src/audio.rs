use anyhow::Result;
use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};
use cpal::{Stream, StreamConfig};
use ringbuf::{HeapRb, traits::{Consumer, Producer, Split}};
use std::sync::{Arc, Mutex};

use crate::pedal::FuzzPedal;

pub struct AudioEngine {
    _input_stream: Stream,
    _output_stream: Stream,
}

impl AudioEngine {
    pub fn new(pedal: Arc<Mutex<FuzzPedal>>) -> Result<Self> {
        let host = cpal::default_host();
        let input_device = host.default_input_device().ok_or_else(|| anyhow::anyhow!("no input device"))?;
        let output_device = host.default_output_device().ok_or_else(|| anyhow::anyhow!("no output device"))?;

        let config = StreamConfig {
            channels: 1,
            sample_rate: cpal::SampleRate(44100),
            buffer_size: cpal::BufferSize::Fixed(256),
        };

        let ring = HeapRb::<f32>::new(8192);
        let (mut prod, mut cons) = ring.split();

        let input_stream = input_device.build_input_stream(
            &config,
            move |data: &[f32], _| {
                for &s in data {
                    let _ = prod.try_push(s);
                }
            },
            |e| eprintln!("input error: {e}"),
            None,
        )?;

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

        input_stream.play()?;
        output_stream.play()?;

        Ok(Self {
            _input_stream: input_stream,
            _output_stream: output_stream,
        })
    }
}
