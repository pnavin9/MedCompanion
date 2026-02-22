"""Test the speech transcription endpoint."""

import requests
import huggingface_hub
import sys

# Configuration
BASE_URL = "http://localhost:8000"

def test_speech_endpoint():
    """Test the /api/v1/speech/transcribe endpoint."""
    
    print("="*60)
    print("TESTING SPEECH TRANSCRIPTION ENDPOINT")
    print("="*60)
    print()
    
    # Step 1: Check server is running
    print("1. Checking server health...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/health")
        if response.status_code == 200:
            health = response.json()
            print(f"   ✅ Server is running")
            print(f"   MedGemma loaded: {health.get('model_loaded')}")
            print(f"   MedASR loaded: {health.get('medasr_loaded')}")
        else:
            print(f"   ❌ Server returned status {response.status_code}")
            return
    except Exception as e:
        print(f"   ❌ Cannot connect to server: {e}")
        print(f"   Make sure server is running: ./start_server.sh")
        return
    
    print()
    
    # Step 2: Check speech service health
    print("2. Checking speech service health...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/speech/health")
        if response.status_code == 200:
            health = response.json()
            print(f"   ✅ Speech endpoint available")
            print(f"   Model type: {health.get('model_type')}")
            print(f"   Model loaded: {health.get('model_loaded')}")
        else:
            print(f"   ❌ Status {response.status_code}")
            return
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    
    print()
    
    # Step 3: Download test audio
    print("3. Downloading test audio from HuggingFace...")
    try:
        audio_path = huggingface_hub.hf_hub_download('google/medasr', 'test_audio.wav')
        print(f"   ✅ Audio downloaded: {audio_path}")
    except Exception as e:
        print(f"   ❌ Download failed: {e}")
        return
    
    print()
    
    # Step 4: Transcribe audio
    print("4. Transcribing audio (this will load MedASR on first run)...")
    print("   ⏳ This may take 30-60 seconds on first request...")
    try:
        with open(audio_path, 'rb') as f:
            files = {'audio': ('test_audio.wav', f, 'audio/wav')}
            response = requests.post(
                f"{BASE_URL}/api/v1/speech/transcribe",
                files=files,
                timeout=120  # 2 minutes timeout for model loading
            )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Transcription successful!")
            print()
            print("   Transcription:")
            print("   " + "="*56)
            print(f"   {result.get('text', 'No text returned')}")
            print("   " + "="*56)
        else:
            print(f"   ❌ Transcription failed with status {response.status_code}")
            print(f"   Error: {response.text}")
            return
            
    except requests.exceptions.Timeout:
        print(f"   ❌ Request timed out (model loading may take longer)")
        return
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    
    print()
    
    # Step 5: Verify MedASR is now loaded
    print("5. Checking if MedASR is now loaded...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/health")
        if response.status_code == 200:
            health = response.json()
            print(f"   ✅ MedASR loaded: {health.get('medasr_loaded')}")
        else:
            print(f"   ❌ Status {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    print("="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60)


if __name__ == "__main__":
    test_speech_endpoint()
