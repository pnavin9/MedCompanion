#!/usr/bin/env python3
"""
Direct MedASR Model Test
Tests the MedASR model for medical speech recognition.

IMPORTANT: Run this with the medasr-test-env environment:
    source medasr-test-env/bin/activate
    python test_medasr_direct.py

Requirements:
    - transformers >= 5.0.0 (install specific commit from GitHub)
    - librosa
    - soundfile
    - torchaudio
    - huggingface_hub (for downloading official test audio)

Installation:
    pip install torch librosa soundfile torchaudio huggingface_hub
    pip install git+https://github.com/huggingface/transformers.git@65dc261512cbdb1ee72b88ae5b222f2605aad8e5

Model Access:
    You must accept the model terms at https://huggingface.co/google/medasr
    Then authenticate: huggingface-cli login
"""

import time
import torch
import numpy as np
from pathlib import Path
from typing import Optional


def check_dependencies():
    """Check if required dependencies are installed."""
    missing = []
    
    try:
        import transformers
        print(f"✅ transformers: {transformers.__version__}")
        # Check version
        version = tuple(map(int, transformers.__version__.split('.')[:2]))
        if version < (5, 0):
            print(f"⚠️  WARNING: transformers version {transformers.__version__} detected.")
            print("   MedASR requires transformers >= 5.0.0")
            print("   Install with: pip install git+https://github.com/huggingface/transformers.git")
    except ImportError:
        missing.append("transformers")
    
    try:
        import librosa
        print(f"✅ librosa: {librosa.__version__}")
    except ImportError:
        missing.append("librosa")
    
    try:
        import soundfile
        print(f"✅ soundfile: {soundfile.__version__}")
    except ImportError:
        missing.append("soundfile")
    
    try:
        import torchaudio
        print(f"✅ torchaudio: {torchaudio.__version__}")
    except ImportError:
        missing.append("torchaudio")
    
    if missing:
        print(f"\n❌ Missing dependencies: {', '.join(missing)}")
        print("\nInstall with:")
        print("  pip install librosa soundfile torchaudio")
        print("  pip install git+https://github.com/huggingface/transformers.git")
        return False
    
    return True


def get_device():
    """Determine the best device for the model."""
    if torch.cuda.is_available():
        return torch.device("cuda")
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def create_test_audio():
    """Create a simple test audio signal (1 second of 440 Hz sine wave)."""
    import librosa
    
    duration = 1.0  # seconds
    sr = 16000  # sample rate
    frequency = 440  # Hz (A4 note)
    
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    audio = 0.5 * np.sin(2 * np.pi * frequency * t)
    
    return audio.astype(np.float32), sr


def test_pipeline_approach():
    """Test MedASR using the Pipeline API (simpler approach)."""
    print("\n" + "=" * 60)
    print("TEST 1: PIPELINE API APPROACH")
    print("=" * 60)
    
    try:
        from transformers import pipeline
    except ImportError as e:
        print(f"❌ Failed to import pipeline: {e}")
        return
    
    model_name = "google/medasr"
    
    # Load pipeline
    print(f"\n⏳ Loading ASR pipeline: {model_name}...")
    load_start = time.time()
    
    try:
        device = get_device()
        print(f"🔧 Device: {device}")
        
        asr_pipeline = pipeline(
            "automatic-speech-recognition",
            model=model_name,
            device=device if device.type != "cpu" else -1
        )
        
        load_time = time.time() - load_start
        print(f"✅ Pipeline loaded in {load_time:.2f} seconds")
        
    except Exception as e:
        print(f"❌ Failed to load pipeline: {e}")
        print("\nNote: If you get a model loading error, ensure you have:")
        print("  1. transformers >= 5.0.0")
        print("  2. Internet connection to download the model")
        return
    
    # Create test audio
    print("\n🎵 Creating test audio...")
    audio, sr = create_test_audio()
    print(f"   Sample rate: {sr} Hz")
    print(f"   Duration: {len(audio) / sr:.2f} seconds")
    
    # Run inference
    print("\n🚀 Running speech recognition...")
    infer_start = time.time()
    
    try:
        result = asr_pipeline(
            audio,
            chunk_length_s=20,  # Process in 20-second chunks (official recommendation)
            stride_length_s=2   # 2-second stride between chunks (official recommendation)
            # Note: return_timestamps removed - MedASR requires explicit 'char' or 'word' if needed
        )
        
        infer_time = time.time() - infer_start
        print(f"✅ Inference completed in {infer_time:.2f} seconds")
        
        # Print results
        print("\n" + "=" * 60)
        print("TRANSCRIPTION:")
        print("=" * 60)
        print(result["text"])
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Inference failed: {e}")
        return
    
    print("\n✨ Pipeline test completed!")


def test_model_direct_approach():
    """Test MedASR by running the model directly (more control)."""
    print("\n" + "=" * 60)
    print("TEST 2: DIRECT MODEL APPROACH")
    print("=" * 60)
    
    try:
        from transformers import AutoModelForCTC, AutoProcessor
        import librosa
    except ImportError as e:
        print(f"❌ Failed to import required libraries: {e}")
        return
    
    model_name = "google/medasr"
    
    # Load processor and model
    print(f"\n⏳ Loading model: {model_name}...")
    load_start = time.time()
    
    try:
        device = get_device()
        print(f"🔧 Device: {device}")
        
        processor = AutoProcessor.from_pretrained(model_name)
        model = AutoModelForCTC.from_pretrained(model_name)
        model.to(device)
        model.eval()
        
        load_time = time.time() - load_start
        print(f"✅ Model loaded in {load_time:.2f} seconds")
        
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        print("\nNote: Ensure transformers >= 5.0.0 and internet connection")
        return
    
    # Create test audio
    print("\n🎵 Creating test audio...")
    audio, sr = create_test_audio()
    
    # Process audio
    print("\n⚙️  Processing audio...")
    process_start = time.time()
    
    try:
        # Resample if needed (MedASR expects 16kHz)
        target_sr = 16000
        if sr != target_sr:
            audio = librosa.resample(audio, orig_sr=sr, target_sr=target_sr)
            sr = target_sr
        
        # Process with processor
        inputs = processor(
            audio,
            sampling_rate=sr,
            return_tensors="pt"
        )
        
        # Move to device
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        process_time = time.time() - process_start
        print(f"✅ Audio processed in {process_time:.3f} seconds")
        
        # Get the actual input key (might be 'input_features' or 'input_values')
        input_key = list(inputs.keys())[0]
        print(f"📊 Input key: {input_key}")
        print(f"📊 Input shape: {inputs[input_key].shape}")
        
    except Exception as e:
        print(f"❌ Audio processing failed: {e}")
        return
    
    # Run inference
    print("\n🚀 Running inference...")
    infer_start = time.time()
    
    try:
        with torch.no_grad():
            # Use model.generate() as per official documentation
            outputs = model.generate(**inputs)
        
        # Decode (official method)
        transcription = processor.batch_decode(outputs)[0]
        
        infer_time = time.time() - infer_start
        print(f"✅ Inference completed in {infer_time:.2f} seconds")
        print(f"📊 Output shape: {outputs.shape}")
        
        # Print results
        print("\n" + "=" * 60)
        print("TRANSCRIPTION:")
        print("=" * 60)
        print(transcription)
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Inference failed: {e}")
        return
    
    print("\n✨ Direct model test completed!")


def test_with_official_audio():
    """Test MedASR with the official test audio from Hugging Face Hub."""
    print("\n" + "=" * 60)
    print("TEST 3: OFFICIAL TEST AUDIO FROM HUGGING FACE")
    print("=" * 60)
    
    try:
        import huggingface_hub
    except ImportError:
        print("❌ huggingface_hub not installed")
        print("   Install with: pip install huggingface_hub")
        return
    
    # Download official test audio
    print("\n📥 Downloading official test audio...")
    try:
        audio_path = huggingface_hub.hf_hub_download('google/medasr', 'test_audio.wav')
        print(f"✅ Downloaded to: {audio_path}")
    except Exception as e:
        print(f"❌ Failed to download test audio: {e}")
        print("   This may require accepting the model terms on Hugging Face")
        return
    
    test_with_audio_file(audio_path)


def test_with_audio_file(audio_path: str):
    """Test MedASR with an actual audio file."""
    print("\n" + "=" * 60)
    print(f"TEST 4: AUDIO FILE - {Path(audio_path).name}")
    print("=" * 60)
    
    if not Path(audio_path).exists():
        print(f"❌ Audio file not found: {audio_path}")
        return
    
    try:
        from transformers import pipeline
        import librosa
    except ImportError as e:
        print(f"❌ Failed to import required libraries: {e}")
        return
    
    # Load audio
    print(f"\n🎵 Loading audio file...")
    try:
        audio, sr = librosa.load(audio_path, sr=16000)
        print(f"✅ Audio loaded: {len(audio) / sr:.2f} seconds")
    except Exception as e:
        print(f"❌ Failed to load audio: {e}")
        return
    
    # Load pipeline
    print(f"\n⏳ Loading ASR pipeline...")
    try:
        device = get_device()
        asr_pipeline = pipeline(
            "automatic-speech-recognition",
            model="google/medasr",
            device=device if device.type != "cpu" else -1
        )
        print(f"✅ Pipeline loaded")
    except Exception as e:
        print(f"❌ Failed to load pipeline: {e}")
        return
    
    # Transcribe
    print("\n🚀 Transcribing...")
    start = time.time()
    
    try:
        result = asr_pipeline(
            audio,
            chunk_length_s=20,  # Official recommendation
            stride_length_s=2   # Official recommendation
            # Note: return_timestamps removed - MedASR requires explicit 'char' or 'word' if needed
        )
        
        elapsed = time.time() - start
        print(f"✅ Transcription completed in {elapsed:.2f} seconds")
        
        # Print results
        print("\n" + "=" * 60)
        print("TRANSCRIPTION:")
        print("=" * 60)
        print(result["text"])
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Transcription failed: {e}")


def main():
    """Run all MedASR tests."""
    print("=" * 60)
    print("MEDASR MODEL TEST SUITE")
    print("=" * 60)
    print("\nThis test suite requires the medasr-test-env environment.")
    print("Make sure you've activated it before running!")
    print()
    
    # Check dependencies
    print("Checking dependencies...")
    if not check_dependencies():
        print("\n❌ Please install missing dependencies first.")
        return
    
    print(f"\n🔧 PyTorch: {torch.__version__}")
    print(f"🔧 Device: {get_device()}")
    
    # Test 1: Pipeline approach
    test_pipeline_approach()
    
    # Test 2: Direct model approach
    test_model_direct_approach()
    
    # Test 3: Official test audio from Hugging Face
    print("\n" + "=" * 60)
    print("Attempting to test with official audio from Hugging Face...")
    print("(This requires accepting model terms at https://huggingface.co/google/medasr)")
    print("=" * 60)
    test_with_official_audio()
    
    # Test 4: Custom audio file (if provided)
    # You can add a path to a real audio file here
    # test_with_audio_file("/path/to/your/audio.wav")
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUITE COMPLETED")
    print("=" * 60)
    print("\n📝 Notes:")
    print("  - MedASR is designed for medical speech recognition")
    print("  - Test 1 & 2 use synthetic audio (440 Hz sine wave)")
    print("  - Test 3 downloads official test audio from Hugging Face (requires model access)")
    print("  - For custom audio testing, uncomment test_with_audio_file() with your audio path")
    print("\n⚠️  Model Limitations (from official model card):")
    print("  - English-only (trained on US English speakers)")
    print("  - Best with high-quality microphone audio")
    print("  - May struggle with recent medical terms (< 10 years old)")
    print("  - Date format handling may need fine-tuning")
    print("\n✨ All tests completed!")


if __name__ == "__main__":
    main()
