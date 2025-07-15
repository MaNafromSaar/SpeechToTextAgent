"""Audio recording functionality."""

import numpy as np
import sounddevice as sd
import soundfile as sf
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import os


class AudioRecorder:
    """Audio recording with high-quality processing and professional interface support."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize audio recorder with configuration."""
        self.config = config
        self.sample_rate = config["audio"]["sample_rate"]
        self.channels = config["audio"]["channels"]
        
        # Professional audio interface settings
        self.exclusive_mode = config["audio"].get("exclusive_mode", False)
        self.custom_sample_rate = config["audio"].get("custom_sample_rate")
        self.buffer_size = config["audio"].get("buffer_size")
        
        # Override sample rate if custom one is specified
        if self.custom_sample_rate:
            self.sample_rate = self.custom_sample_rate
        
        # Set audio devices if specified
        input_dev = config["audio"].get("input_device")
        output_dev = config["audio"].get("output_device")
        
        if input_dev is not None or output_dev is not None:
            # Set default device
            if input_dev is not None and output_dev is not None:
                sd.default.device = (input_dev, output_dev)
            elif input_dev is not None:
                sd.default.device = (input_dev, sd.default.device[1] if hasattr(sd.default.device, '__len__') else None)
            elif output_dev is not None:
                sd.default.device = (sd.default.device[0] if hasattr(sd.default.device, '__len__') else None, output_dev)
        
        # Configure for professional interfaces
        self._configure_professional_audio()
        
        self.output_dir = Path(config["output"]["audio_output_dir"])
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _configure_professional_audio(self):
        """Configure settings optimized for professional audio interfaces."""
        # Check if we're using professional interfaces
        try:
            current_device = sd.query_devices(sd.default.device)
            if isinstance(current_device, dict):
                devices = [current_device]
            else:
                devices = current_device
                
            host_apis = sd.query_hostapis()
            
            for device in devices:
                if device is None:
                    continue
                    
                host_api = host_apis[device['hostapi']]
                api_name = host_api['name'].upper()
                
                # Check if this is a professional interface
                is_professional = any(pro_type in api_name for pro_type in ['ASIO', 'CORE AUDIO', 'JACK'])
                
                if is_professional:
                    # Set low-latency parameters for professional interfaces
                    if self.buffer_size:
                        # Note: sounddevice doesn't directly expose buffer size,
                        # but we can use blocksize parameter in recording
                        self.recording_blocksize = self.buffer_size
                    else:
                        # Use smaller blocksize for professional interfaces
                        self.recording_blocksize = 256 if 'ASIO' in api_name else 512
                    
                    # Set exclusive mode for supported platforms
                    if self.exclusive_mode and ('ASIO' in api_name or 'CORE AUDIO' in api_name):
                        # This would require platform-specific configuration
                        # For now, we'll use optimal settings within sounddevice
                        pass
                        
                    print(f"✅ Professional interface detected: {device['name']} [{host_api['name']}]")
                    print(f"   Low latency: {device.get('default_low_input_latency', 0):.3f}s")
                    if hasattr(self, 'recording_blocksize'):
                        print(f"   Buffer size: {self.recording_blocksize} samples")
                    
        except Exception as e:
            # Fallback to standard settings if professional config fails
            self.recording_blocksize = 1024
            print(f"⚠️  Professional audio config failed, using standard settings: {e}")
    
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
            output_path = self.output_dir / f"recording_{timestamp}.wav"
        else:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Professional interface optimizations
        recording_kwargs = {
            'samplerate': self.sample_rate,
            'channels': self.channels,
            'dtype': np.float32
        }
        
        # Add blocksize for professional interfaces
        if hasattr(self, 'recording_blocksize'):
            recording_kwargs['blocksize'] = self.recording_blocksize
        
        try:
            # Record audio with professional settings
            recording = sd.rec(
                int(duration * self.sample_rate),
                **recording_kwargs
            )
            
            # Wait for recording to complete
            sd.wait()
            
            # Validate recording
            if recording is None or len(recording) == 0:
                raise RuntimeError("Recording failed - no audio data captured")
            
            # Check for clipping or very low levels
            max_amplitude = np.max(np.abs(recording))
            if max_amplitude > 0.95:
                print("⚠️  Warning: Audio may be clipping (very high levels)")
            elif max_amplitude < 0.001:
                print("⚠️  Warning: Very low audio levels detected")
            
            # Save audio file with high quality
            sf.write(
                str(output_path), 
                recording, 
                self.sample_rate,
                subtype='PCM_24'  # Use 24-bit for professional quality
            )
            
            print(f"✅ Recorded {duration}s at {self.sample_rate}Hz ({max_amplitude:.3f} peak)")
            
        except Exception as e:
            raise RuntimeError(f"Recording failed: {e}")
        
        return str(output_path)
    
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
