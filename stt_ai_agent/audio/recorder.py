"""Audio recording functionality."""

import numpy as np
import sounddevice as sd
import soundfile as sf
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any


class AudioRecorder:
    """Audio recording with high-quality processing."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize audio recorder with configuration."""
        self.config = config
        self.sample_rate = config["audio"]["sample_rate"]
        self.channels = config["audio"]["channels"]
        # Set audio devices if specified
        input_dev = config["audio"].get("input_device")
        output_dev = config["audio"].get("output_device")
        if input_dev is not None or output_dev is not None:
            # sounddevice expects a tuple (input, output) or single int
            sd.default.device = (
                input_dev if input_dev is not None else sd.default.device[0],
                output_dev if output_dev is not None else sd.default.device[1],
            )
        self.output_dir = Path(config["output"]["audio_output_dir"])
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def record(
        self, 
        duration: int, 
        output_file: Optional[str] = None
    ) -> str:
        """
        Record audio for specified duration.
        
        Args:
            duration: Recording duration in seconds
            output_file: Optional output file path
            
        Returns:
            Path to recorded audio file
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"recording_{timestamp}.wav"
        else:
            output_file = Path(output_file)
            output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Record audio
        recording = sd.rec(
            int(duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype=np.float32
        )
        
        # Wait for recording to complete
        sd.wait()
        
        # Save audio file
        sf.write(str(output_file), recording, self.sample_rate)
        
        return str(output_file)
    
    def get_available_devices(self) -> list:
        """Get list of available audio input devices."""
        devices = sd.query_devices()
        input_devices = [
            device for device in devices 
            if device['max_input_channels'] > 0
        ]
        return input_devices
    
    def set_input_device(self, device_id: int) -> None:
        """Set the input device for recording."""
        sd.default.device[0] = device_id
