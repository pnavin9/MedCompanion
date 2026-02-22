# MedASR Quick Reference Guide

Based on the official [MedASR Model Card](https://huggingface.co/google/medasr)

## Model Overview

**MedASR** is a medical automatic speech recognition model from Google Health AI, specifically trained for medical dictation and clinical conversations.

- **Architecture**: Conformer-based CTC
- **Parameters**: 105M
- **Training Data**: ~5000 hours of de-identified medical speech
- **Release Date**: December 18, 2025
- **Version**: 1.0.0

## Quick Start

### Installation

```bash
# Required: transformers >= 5.0.0 from GitHub
pip install git+https://github.com/huggingface/transformers.git@65dc261512cbdb1ee72b88ae5b222f2605aad8e5

# Other dependencies
pip install torch librosa soundfile torchaudio huggingface_hub
```

### Model Access

1. Visit https://huggingface.co/google/medasr
2. Accept the Health AI Developer Foundations terms
3. Authenticate: `huggingface-cli login`

### Usage (Pipeline API)

```python
from transformers import pipeline
import huggingface_hub

# Download test audio
audio = huggingface_hub.hf_hub_download('google/medasr', 'test_audio.wav')

# Initialize pipeline
pipe = pipeline("automatic-speech-recognition", model="google/medasr")

# Transcribe with recommended parameters
result = pipe(
    audio,
    chunk_length_s=20,  # Official recommendation
    stride_length_s=2    # Official recommendation
)

print(result["text"])
```

### Usage (Direct Model)

```python
from transformers import AutoModelForCTC, AutoProcessor
import librosa
import torch

# Load model
processor = AutoProcessor.from_pretrained("google/medasr")
model = AutoModelForCTC.from_pretrained("google/medasr")

# Process audio
audio, sr = librosa.load("audio.wav", sr=16000)
inputs = processor(audio, sampling_rate=sr, return_tensors="pt", padding=True)

# Generate transcription
outputs = model.generate(**inputs)
text = processor.batch_decode(outputs)[0]

print(text)
```

## Performance Metrics

MedASR achieves state-of-the-art performance on medical speech:

| Dataset | Type | WER (greedy) | WER (+ LM) |
|---------|------|--------------|------------|
| RAD-DICT | Radiology | 6.6% | **4.6%** |
| GENERAL-DICT | General/Internal | 9.3% | **6.9%** |
| FM-DICT | Family Medicine | 8.1% | **5.8%** |
| Eye Gaze (MIMIC) | Multi-speaker | 6.6% | **5.2%** |

*Note: "+ LM" uses 6-gram language model with beam search (size 8)*

Comparison to other models (greedy decoding):
- Gemini 2.5 Pro: 5.9-16.4% WER
- Gemini 2.5 Flash: 9.3-27.1% WER
- Whisper v3 Large: 12.5-33.1% WER

## Audio Requirements

### Optimal Input Specifications

- **Sample Rate**: 16kHz (mono-channel)
- **Format**: int16 waveform
- **Quality**: High-quality microphone recording
- **Language**: English (US English preferred)
- **Content**: Medical terminology, dictation, or clinical conversations

### Training Data Characteristics

- Primarily US English speakers (native)
- High-quality microphone recordings
- Both male and female speakers (higher proportion male)
- De-identified medical data

## Known Limitations

Based on official model card:

### 1. Language & Accent
- **English only** (no multilingual support)
- Optimized for US English speakers
- May have reduced performance with non-US accents

### 2. Audio Quality
- Trained on professional-grade microphones
- Performance degrades with:
  - Low-quality audio
  - Background noise
  - Poor microphone quality
  - Multiple overlapping speakers

### 3. Medical Terminology
- Strong on established medical vocabulary
- May struggle with:
  - Very recent medications/procedures (< 10 years)
  - Non-standard medication names
  - Emerging medical terminology

### 4. Date/Time Handling
- Trained on de-identified data (dates removed)
- May have inconsistent date format handling
- Can be improved with fine-tuning or language model decoding

### 5. Speaker Demographics
- Best performance on speakers matching training data:
  - Native English speakers from US
  - Adult voices
  - Clear pronunciation

## Use Cases

### ✅ Ideal For:
- Radiology dictation
- Physician-patient conversations
- Clinical notes transcription
- Medical documentation
- Telemedicine recordings
- Medical education content

### ⚠️ Requires Fine-tuning For:
- Non-US English accents
- Low-quality audio environments
- Specialized medical sub-domains
- Recent medical terminology (post-2015)
- Multi-speaker scenarios with overlap

### ❌ Not Suitable For:
- Non-English languages
- Real-time critical care decisions (without validation)
- Direct clinical diagnosis (requires human review)
- Low-quality/noisy recordings (without adaptation)

## Integration with MedGemma

MedASR can be combined with [MedGemma](https://huggingface.co/google/medgemma-4b-it) for a complete speech-to-medical-response pipeline:

```
Speech Audio → MedASR → Text → MedGemma → Medical Response
```

Example use case:
1. Patient describes symptoms (audio)
2. MedASR transcribes to text
3. MedGemma analyzes and provides medical information
4. Result: Voice-activated medical AI assistant

## Fine-tuning

For custom applications, fine-tuning is recommended:

- **Notebook**: [Fine-tuning tutorial](https://github.com/google-health/medasr/blob/main/notebooks/fine_tune_with_hugging_face.ipynb)
- **When to fine-tune**:
  - Your audio quality differs from training data
  - You need specific medical terminology
  - You have non-US speakers
  - You need better date/time handling

## Resources

- **Model Card**: https://huggingface.co/google/medasr
- **Official Docs**: https://developers.google.com/health-ai-developer-foundations/medasr
- **GitHub**: https://github.com/Google-Health/medasr
- **Quick Start Notebook**: [Colab](https://github.com/google-health/medasr/blob/main/notebooks/quick_start_with_hugging_face.ipynb)
- **Fine-tuning Notebook**: [Colab](https://github.com/google-health/medasr/blob/main/notebooks/fine_tune_with_hugging_face.ipynb)
- **License**: Health AI Developer Foundations terms

## Important Notes

1. **Model Access**: Requires accepting terms at https://huggingface.co/google/medasr
2. **Not for Direct Clinical Use**: All outputs require validation and clinical correlation
3. **Safety Evaluation**: Model evaluated for safety on 100 examples specifically for medical context
4. **De-identified Training**: All training data was rigorously de-identified
5. **Research & Development**: Intended as a starting point for developers, not end-user product

## Support

- **Issues**: https://github.com/Google-Health/medasr/issues
- **Discussions**: https://github.com/Google-Health/medasr/discussions
- **Contact**: See official documentation for support channels
