# MedASR Test Suite

This directory contains test files for the **MedASR** (Medical Automatic Speech Recognition) model from Google Health AI.

## Why Separate Environment?

MedASR requires **transformers >= 5.0.0**, which may conflict with other dependencies in the main project. Therefore, we maintain a separate virtual environment (`medasr-test-env`) specifically for MedASR testing.

## Setup Instructions

### 1. Ensure Environment Exists

The `medasr-test-env` environment should already exist. If not, create it:

```bash
python3 -m venv medasr-test-env
```

### 2. Activate Environment

```bash
source medasr-test-env/bin/activate
```

### 3. Install Dependencies

```bash
# Install basic dependencies
pip install torch librosa soundfile torchaudio huggingface_hub

# Install specific transformers version from GitHub (required for MedASR)
# MedASR requires transformers >= 5.0.0
pip install git+https://github.com/huggingface/transformers.git@65dc261512cbdb1ee72b88ae5b222f2605aad8e5
```

> **Note**: The specific commit hash is from the official MedASR documentation. You can also use the latest version from GitHub.

### 4. Run Tests

**Option A: Using the test script directly**
```bash
python test_medasr_direct.py
```

**Option B: Using the convenience script (recommended)**
```bash
./test_medasr.sh
```

The convenience script automatically activates the correct environment and runs the tests.

## Test File: `test_medasr_direct.py`

This comprehensive test suite includes four testing approaches:

### Test 1: Pipeline API Approach (Simpler)
- Uses `transformers.pipeline` for ASR
- **Chunk length**: 20 seconds (official recommendation)
- **Stride length**: 2 seconds (official recommendation)
- Easier to use, less control
- Good for quick testing

### Test 2: Direct Model Approach (More Control)
- Uses `AutoModelForCTC` and `AutoProcessor`
- Uses `model.generate()` for inference (official method)
- More control over the inference process
- Useful for debugging and optimization

### Test 3: Official Test Audio
- Downloads test audio from Hugging Face Hub
- **Requires**: Accepting model terms at https://huggingface.co/google/medasr
- Uses real medical audio provided by Google

### Test 4: Custom Audio File Testing (Optional)
- Tests with your own audio files
- Uncomment and provide path to your audio file
- Supports WAV, MP3, and other common formats

## Test Audio

The test suite includes three types of audio:

1. **Synthetic Audio (Tests 1 & 2)**: A 440 Hz sine wave for basic functionality testing
2. **Official Test Audio (Test 3)**: Downloaded from Hugging Face Hub - real medical audio
3. **Custom Audio (Test 4)**: Your own audio files

### Using Custom Audio

To test with your own audio:

1. Prepare a medical audio recording (WAV format, 16kHz recommended)
2. Uncomment the `test_with_audio_file()` call in `main()`
3. Provide the path to your audio file

Example:
```python
test_with_audio_file("/path/to/medical_audio.wav")
```

### Audio Requirements (from official model card)

- **Format**: Mono-channel, 16kHz, int16 waveform
- **Quality**: High-quality microphone audio (model trained on professional recordings)
- **Language**: English only (US English preferred)
- **Content**: Medical terminology, radiology dictation, or physician-patient conversations

## Expected Output

The test suite will:
1. Check all dependencies
2. Display device information (CPU/CUDA/MPS)
3. Load the MedASR model
4. Process audio and generate transcriptions
5. Show timing information for each step

## Troubleshooting

### Issue: `transformers` version too old
**Solution:** Install the specific version from GitHub
```bash
pip install git+https://github.com/huggingface/transformers.git@65dc261512cbdb1ee72b88ae5b222f2605aad8e5
```

### Issue: Model download fails / Access denied
**Solution:** You must accept the model terms on Hugging Face
1. Visit https://huggingface.co/google/medasr
2. Log in to your Hugging Face account
3. Click "Agree and access repository"
4. Authenticate using: `huggingface-cli login`

### Issue: Official test audio download fails
**Solution:** Same as above - requires model access approval
```bash
# After accepting terms, login to Hugging Face
huggingface-cli login
```

### Issue: Audio processing errors
**Solution:** Ensure all audio libraries are installed
```bash
pip install librosa soundfile torchaudio huggingface_hub
```

### Issue: Poor transcription quality
**Possible causes (from official limitations):**
- Low-quality or noisy audio (model trained on high-quality microphones)
- Non-US English accents
- Recent medical terms (< 10 years old)
- Background noise or multiple speakers

**Solution:** Consider fine-tuning on your specific audio type

### Issue: Memory errors
**Solution:** MedASR has 105M parameters. Try:
- Using CPU instead of GPU/MPS
- Processing shorter audio chunks (reduce `chunk_length_s`)
- Ensure sufficient RAM (8GB+ recommended)

## Model Information

- **Model Name:** `google/medasr`
- **Model Type:** Conformer-based CTC ASR
- **Parameters:** 105M
- **Input:** Mono-channel 16kHz audio, int16 waveform
- **Output:** Text transcription
- **Specialty:** Medical speech recognition (radiology, physician-patient conversations)
- **Training Data:** ~5000 hours of de-identified medical speech
- **Performance:** 4.6-6.9% WER on medical dictation (with language model)
- **License:** Health AI Developer Foundations terms

### Key Limitations (from official model card)

1. **Language**: English only (primarily US English)
2. **Audio Quality**: Trained on high-quality microphones; performance may deteriorate with:
   - Low-quality audio
   - Background noise
   - Poor microphone quality
3. **Speaker Diversity**: 
   - Most training data from native English speakers in the US
   - Higher proportion of male speakers
4. **Medical Terms**: May not include all recent medications/procedures (past 10 years)
5. **Dates/Times**: Performance on different date formats may be lacking (trained on de-identified data)

### Performance Benchmarks

From the official model card, MedASR with 6-gram language model achieves:

| Dataset | Description | WER |
|---------|-------------|-----|
| RAD-DICT | Radiology dictation | 4.6% |
| GENERAL-DICT | General/internal medicine | 6.9% |
| FM-DICT | Family medicine | 5.8% |
| Eye Gaze (MIMIC) | 998 MIMIC cases | 5.2% |

Greedy decoding (without language model) typically adds 1-2% to WER.

## References

- [MedASR Model Card](https://developers.google.com/health-ai-developer-foundations/medasr/model-card)
- [MedASR GitHub](https://github.com/Google-Health/medasr)
- [MedASR on Hugging Face](https://huggingface.co/google/medasr)
- [Get Started Guide](https://developers.google.com/health-ai-developer-foundations/medasr/get-started)

## Notes

- The test uses synthetic audio by default; transcription may not be meaningful
- For meaningful results, use actual medical audio recordings
- MedASR is optimized for medical terminology and clinical speech
- First run will download the model (~500MB) from Hugging Face
