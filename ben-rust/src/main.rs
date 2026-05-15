use anyhow::Result;
use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};
use dialoguer::{Select, theme::ColorfulTheme};
use ringbuf::{
    HeapRb,
    traits::{Consumer, Producer, Split},
};

fn main() -> Result<()> {
    let host = cpal::default_host();

    // Configure inputs and outputs
    let output_devices: Vec<_> = host.output_devices()?.collect();
    let input_devices: Vec<_> = host.input_devices()?.collect();
    let output_device = select_device(&host, &output_devices, "Pick your output:");
    let input_device = select_device(&host, &input_devices, "Pick Input");

    //Configure stream defualts
    let sample_rate = input_device.default_input_config()?.sample_rate();
    let buffer_frames: usize = 512;
    let buffer_size = cpal::BufferSize::Fixed(buffer_frames as u32);

    let stream_config = cpal::StreamConfig {
        channels: 2,
        sample_rate,
        buffer_size,
    };

    dbg!(&stream_config);

    //RINGBUFF
    let ring = HeapRb::<f32>::new(buffer_frames * 2 * 4);
    let (mut producer, mut consumer) = ring.split();

    // INPUT STREAM
    let input_stream_config = stream_config.clone();
    let input_data_fn = move |data: &[f32], _info: &cpal::InputCallbackInfo| {
        // println!("{}", data[0]);
        let mut output_fell_behind = false;
        for &sample in data {
            if producer.try_push(sample).is_err() {
                output_fell_behind = true;
            }
        }
        if output_fell_behind {
            eprintln!("output stream fell behind: try increasing latency");
        }
    };
    let input_error_fn = |err| eprintln!("Error: {}", err);
    let input_stream = input_device.build_input_stream(
        &input_stream_config,
        input_data_fn,
        input_error_fn,
        None,
    )?;

    // OUTPUT STREAM
    let output_stream_config = stream_config.clone();
    let output_data_fn = move |data: &mut [f32], _info: &cpal::OutputCallbackInfo| {
        let mut input_fell_behind = false;
        for sample in data {
            *sample = match consumer.try_pop() {
                Some(s) => s,
                None => {
                    input_fell_behind = true;
                    0.0
                }
            };
        }
        if input_fell_behind {
            eprintln!("input stream fell behind: try increasing latency");
        }
    };
    let output_error_fn = |err| eprintln!("Error: {}", err);
    let output_stream = output_device.build_output_stream(
        &output_stream_config,
        output_data_fn,
        output_error_fn,
        None,
    )?;

    //not sure if need thsese
    input_stream.play()?;
    output_stream.play()?;

    let mut user_input = String::new();
    std::io::stdin().read_line(&mut user_input)?;

    Ok(())
}

fn select_device(host: &cpal::Host, devices: &[cpal::Device], msg: &str) -> cpal::Device {
    let device_names: Vec<String> = devices
        .iter()
        .map(|d| d.description().unwrap().name().to_string())
        .collect();

    let select_output = Select::with_theme(&ColorfulTheme::default())
        .with_prompt(msg)
        .default(0)
        .items(&device_names)
        .interact()
        .unwrap();

    let id = devices[select_output].id().unwrap();
    host.device_by_id(&id).expect("device not found")
}
