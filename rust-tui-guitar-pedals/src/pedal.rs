pub struct FuzzPedal {
    pub gain: f32,
    pub tone: f32,
    pub volume: f32,
    pub bypassed: bool,
    prev: f32,
}

impl FuzzPedal {
    pub fn new() -> Self {
        Self {
            gain: 0.5,
            tone: 0.5,
            volume: 0.5,
            bypassed: false,
            prev: 0.0,
        }
    }

    pub fn process(&mut self, buf: &mut [f32]) {
        if self.bypassed {
            return;
        }
        let alpha = self.tone.clamp(0.01, 0.99);
        for s in buf.iter_mut() {
            let driven = (*s * (1.0 + self.gain * 19.0)).tanh();
            self.prev = (1.0 - alpha) * self.prev + alpha * driven;
            *s = self.prev * self.volume;
        }
    }
}
