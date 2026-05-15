use cpal::traits::{DeviceTrait, HostTrait};
use std::io;
use std::io::Write;

fn main() {
    let host = cpal::default_host();

    let output_devices: Vec<_> = host.output_devices().unwrap().collect();

    println!("Pick an output device:");
    for (i, device) in output_devices.iter().enumerate() {
        println!("[{}] {}", i, device.description().unwrap());
    }

    print!("> ");
    std::io::stdout().flush().unwrap();

    let mut input = String::new();
    io::stdin()
        .read_line(&mut input)
        .expect("Failed to read line");

    let index: usize = input.trim().parse().expect("Please enter a number");
    let id = output_devices[index].id().unwrap();
    let selected_output_device = host.device_by_id(&id).expect("device not found");

    let input_devices: Vec<_> = host.input_devices().unwrap().collect();

    println!("Pick you input device");

    for (i, device) in input_devices.iter().enumerate() {
        println!("[{}] {}", i, device.description().unwrap());
    }

    print!("> ");
    std::io::stdout().flush().unwrap();

    let mut input2 = String::new();
    io::stdin()
        .read_line(&mut input2)
        .expect("Failed to read line");

    let input_index: usize = input2.trim().parse().expect("Please enter a number");
    let input_id = input_devices[input_index].id().unwrap();
    let selected_input_device = host.device_by_id(&input_id).expect("device not found");

    println!(
        "Output: {}, Input: {}",
        selected_output_device.description().unwrap(),
        selected_input_device.description().unwrap()
    );
}
