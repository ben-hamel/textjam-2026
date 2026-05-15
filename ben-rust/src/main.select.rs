use cpal::traits::{DeviceTrait, HostTrait};
use dialoguer::{Select, theme::ColorfulTheme};

fn main() {
    let host = cpal::default_host();

    let output_devices: Vec<_> = host.output_devices().unwrap().collect();

    let device_names: Vec<String> = output_devices
        .iter()
        .map(|d| {
            d.description()
                .map(|desc| desc.to_string())
                .unwrap_or_else(|_| "Unknown".to_string())
        })
        .collect();

    let selection = Select::with_theme(&ColorfulTheme::default())
        .with_prompt("Choose your weapon.. i mean output")
        .items(&device_names)
        .default(0)
        .interact()
        .unwrap();

    let id = output_devices[selection].id().unwrap();
    let selected_output_device = host.device_by_id(&id).expect("device not found");

    println!("Output: {}", selected_output_device.description().unwrap());
}
