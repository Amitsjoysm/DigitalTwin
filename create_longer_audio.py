#!/usr/bin/env python3
"""
Create a longer test audio file for voice cloning
"""

import wave
import math
import tempfile

def create_longer_test_audio():
    """Create a 30-second test audio file"""
    sample_rate = 44100
    duration = 30.0  # 30 seconds
    frames = int(sample_rate * duration)
    
    # Generate a more complex audio pattern (multiple tones)
    audio_data = []
    for i in range(frames):
        # Mix multiple frequencies to simulate speech-like patterns
        t = i / sample_rate
        value1 = 0.3 * math.sin(2 * math.pi * 440 * t)  # A4
        value2 = 0.2 * math.sin(2 * math.pi * 880 * t)  # A5
        value3 = 0.1 * math.sin(2 * math.pi * 220 * t)  # A3
        
        # Add some variation to simulate speech patterns
        envelope = 0.5 + 0.5 * math.sin(2 * math.pi * 0.5 * t)  # Slow modulation
        
        combined = (value1 + value2 + value3) * envelope
        value = int(16000 * combined)  # Scale to 16-bit range
        audio_data.append(value)
    
    # Create temporary WAV file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
    
    with wave.open(temp_file.name, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        
        # Convert to bytes
        audio_bytes = b''.join([value.to_bytes(2, 'little', signed=True) for value in audio_data])
        wav_file.writeframes(audio_bytes)
    
    temp_file.close()
    print(f"Created 30-second test audio: {temp_file.name}")
    return temp_file.name

if __name__ == "__main__":
    create_longer_test_audio()