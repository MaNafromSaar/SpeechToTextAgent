# Professional Audio Interface Setup Guide

This guide explains how to set up professional audio interfaces with the STT AI Agent, including ASIO (Windows), Core Audio (macOS), and JACK (Linux) support.

## Overview

The STT AI Agent supports professional audio interfaces through the `sounddevice` library, which uses PortAudio and can access:

- **ASIO drivers** (Windows) - Low-latency professional audio
- **Core Audio** (macOS) - Native macOS audio system
- **JACK** (Linux) - Professional audio server
- **DirectSound/WASAPI** (Windows) - Standard Windows audio
- **ALSA** (Linux) - Standard Linux audio

## Quick Setup

### 1. List Available Devices
```bash
# In Docker container
docker-compose run --rm stt-agent stt-agent list-devices

# Or natively
stt-agent list-devices
```

This will show all audio devices with their API types. Professional interfaces are marked with 🎛️.

### 2. Configure Audio Devices
```bash
# Interactive configuration wizard
stt-agent configure-audio
```

This wizard will:
- Detect professional interfaces
- Guide you through device selection
- Set optimal parameters for your interface
- Save configuration to `.env` file

### 3. Test Your Setup
```bash
# Test recording with your configured device
stt-agent test-audio --duration 5

# Test specific device
stt-agent test-audio --device 5 --duration 5
```

## Platform-Specific Setup

### Windows (ASIO)

**Prerequisites:**
1. Install ASIO drivers for your interface
2. Ensure interface is connected and powered on

**Popular Professional Interfaces:**
- **Focusrite Scarlett series**
  - Install Focusrite Control software
  - Use ASIO drivers for best performance
  - Typical settings: 48kHz, 128-256 samples buffer

- **RME interfaces**
  - Install TotalMix FX
  - Use RME ASIO drivers
  - Excellent low-latency performance: 64-128 samples

- **PreSonus AudioBox/Quantum**
  - Install Universal Control
  - Use PreSonus ASIO drivers

- **Steinberg UR series**
  - Install dspMixFx software
  - Use Yamaha Steinberg USB ASIO

**Example .env configuration:**
```bash
# For Focusrite Scarlett 2i2 (example)
AUDIO_INPUT_DEVICE=5
AUDIO_OUTPUT_DEVICE=5
AUDIO_EXCLUSIVE_MODE=true
AUDIO_CUSTOM_SAMPLE_RATE=48000
AUDIO_BUFFER_SIZE=128
```

### macOS (Core Audio)

**Prerequisites:**
1. Interfaces typically work out-of-the-box with Core Audio
2. Install manufacturer's control software if available

**Popular Professional Interfaces:**
- **Apogee Element/Symphony series**
  - Install Apogee Control software
  - Excellent built-in Core Audio support
  - Can achieve very low latency: 32-64 samples

- **Universal Audio Apollo series**
  - Install Universal Audio Console
  - Built-in DSP processing
  - Low-latency monitoring

- **MOTU interfaces**
  - Install MOTU Audio Setup utility
  - Great for multi-channel recording

**Example .env configuration:**
```bash
# For Apogee Element 88 (example)
AUDIO_INPUT_DEVICE=4
AUDIO_OUTPUT_DEVICE=4
AUDIO_EXCLUSIVE_MODE=true
AUDIO_CUSTOM_SAMPLE_RATE=96000
AUDIO_BUFFER_SIZE=64
```

### Linux (JACK/ALSA)

**Prerequisites:**
1. Install JACK audio server: `sudo apt install jackd2`
2. Install interface-specific drivers if needed
3. Configure JACK for your interface

**Setup JACK:**
```bash
# Start JACK with professional interface
jackd -d alsa -d hw:1 -r 48000 -p 256 -n 2

# Or use QjackCtl for GUI configuration
```

**Example .env configuration:**
```bash
# For professional interface via JACK
AUDIO_INPUT_DEVICE=2
AUDIO_OUTPUT_DEVICE=2
AUDIO_EXCLUSIVE_MODE=true
AUDIO_CUSTOM_SAMPLE_RATE=48000
AUDIO_BUFFER_SIZE=256
```

## Docker Considerations

### Limitations in Docker
- ASIO drivers don't work in Linux containers
- Core Audio is macOS-specific
- Container audio is limited to ALSA/PulseAudio

### Recommended Approach
For professional audio work, we recommend:

1. **Run natively** on the host system for professional interfaces
2. **Use Docker** for development and basic testing
3. **Use host networking** in Docker for better audio access

### Native Installation
```bash
# Clone and install natively for professional audio
git clone <repository>
cd SpeechToTextAgent
pip install -e .
stt-agent configure-audio
```

## Sample Rates and Buffer Sizes

### Professional Sample Rates
- **44.1 kHz** - CD quality, good for speech
- **48 kHz** - Video standard, recommended for STT
- **88.2 kHz** - High quality, 2x CD
- **96 kHz** - Studio standard
- **176.4/192 kHz** - Ultra high quality

### Buffer Sizes (Lower = Less Latency)
- **32-64 samples** - Ultra low latency (1-3ms)
- **128 samples** - Low latency (3-6ms) - Recommended
- **256 samples** - Moderate latency (6-12ms)
- **512+ samples** - Higher latency but more stable

## Troubleshooting

### Common Issues

**"Error querying device" - Device Not Available**
```bash
# Check if device is in use
stt-agent list-devices
# Try different device ID
stt-agent test-audio --device X
```

**High CPU Usage / Audio Dropouts**
```bash
# Increase buffer size
AUDIO_BUFFER_SIZE=512
# Or lower sample rate
AUDIO_CUSTOM_SAMPLE_RATE=48000
```

**No Audio Detected**
```bash
# Check levels
stt-agent test-audio --duration 5
# Verify device selection
stt-agent configure-audio
```

### Professional Interface Specific

**ASIO Drivers (Windows)**
- Ensure no other applications are using exclusive mode
- Update ASIO drivers from manufacturer
- Check Windows audio exclusive mode settings

**Core Audio (macOS)**
- Check Audio MIDI Setup.app settings
- Verify sample rate matches in system preferences
- Some interfaces need manufacturer software running

## Configuration Examples

### Studio Recording Setup
```bash
# High-quality studio recording
AUDIO_INPUT_DEVICE=5
AUDIO_CUSTOM_SAMPLE_RATE=96000
AUDIO_BUFFER_SIZE=128
AUDIO_EXCLUSIVE_MODE=true
AUDIO_BIT_DEPTH=24
```

### Podcast/Streaming Setup
```bash
# Optimized for real-time processing
AUDIO_INPUT_DEVICE=3
AUDIO_CUSTOM_SAMPLE_RATE=48000
AUDIO_BUFFER_SIZE=256
AUDIO_EXCLUSIVE_MODE=true
AUDIO_BIT_DEPTH=24
```

### Low-Latency Monitoring
```bash
# Ultra-low latency for live work
AUDIO_INPUT_DEVICE=4
AUDIO_CUSTOM_SAMPLE_RATE=48000
AUDIO_BUFFER_SIZE=64
AUDIO_EXCLUSIVE_MODE=true
```

## Performance Tips

1. **Close other audio applications** when using exclusive mode
2. **Use dedicated USB ports** for audio interfaces
3. **Disable Wi-Fi and other interruptions** during recording
4. **Run on AC power** (not battery) for consistent performance
5. **Use SSD storage** for better I/O performance
6. **Monitor CPU usage** and adjust buffer sizes accordingly

For best results with professional audio interfaces, consider running the STT AI Agent natively rather than in Docker containers.
