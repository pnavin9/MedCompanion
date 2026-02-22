#!/usr/bin/env python3
"""
Test if MedGemma works in the medasr-test-env environment.

This tests if both MedASR and MedGemma can coexist in the same environment,
which would allow for a complete speech-to-medical-response pipeline.

Run with:
    source medasr-test-env/bin/activate
    python test_medgemma_in_medasr_env.py
"""

import time
import sys


def check_dependencies():
    """Check if required dependencies are installed."""
    print("Checking dependencies...")
    missing = []
    
    try:
        import transformers
        print(f"✅ transformers: {transformers.__version__}")
    except ImportError:
        missing.append("transformers")
    
    try:
        import torch
        print(f"✅ torch: {torch.__version__}")
    except ImportError:
        missing.append("torch")
    
    try:
        from PIL import Image
        import PIL
        print(f"✅ PIL: {PIL.__version__}")
    except ImportError:
        missing.append("Pillow")
    
    try:
        import numpy
        print(f"✅ numpy: {numpy.__version__}")
    except ImportError:
        missing.append("numpy")
    
    if missing:
        print(f"\n❌ Missing dependencies: {', '.join(missing)}")
        print("\nInstall with:")
        print("  pip install torch transformers Pillow numpy")
        return False
    
    return True


def test_medgemma_loading():
    """Test if MedGemma model can be loaded."""
    print("\n" + "=" * 60)
    print("TEST: MEDGEMMA MODEL LOADING")
    print("=" * 60)
    
    try:
        import torch
        from transformers import AutoModelForImageTextToText, AutoProcessor
        from PIL import Image
        import numpy as np
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    
    # Get device
    if torch.cuda.is_available():
        device = torch.device("cuda")
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        device = torch.device("mps")
    else:
        device = torch.device("cpu")
    
    print(f"\n🔧 Device: {device}")
    
    model_name = "google/medgemma-4b-it"
    
    # Try to load processor first (faster)
    print(f"\n⏳ Loading processor: {model_name}...")
    try:
        start = time.time()
        processor = AutoProcessor.from_pretrained(model_name)
        elapsed = time.time() - start
        print(f"✅ Processor loaded in {elapsed:.2f} seconds")
    except Exception as e:
        print(f"❌ Processor loading failed: {e}")
        return False
    
    # Try to load model
    print(f"\n⏳ Loading model: {model_name}...")
    print("   (This may take a while on first run - downloading ~8GB)")
    try:
        start = time.time()
        # Don't use device_map="auto" with transformers 5.0 + MPS (has bugs)
        # Load to CPU first, then move to device
        model = AutoModelForImageTextToText.from_pretrained(
            model_name,
            dtype=torch.float32 if device.type in ["cpu", "mps"] else torch.float16
        )
        # Move to device manually
        model = model.to(device)
        elapsed = time.time() - start
        print(f"✅ Model loaded in {elapsed:.2f} seconds")
    except Exception as e:
        print(f"❌ Model loading failed: {e}")
        print("\nFull error traceback:")
        import traceback
        traceback.print_exc()
        print("\nPossible issues:")
        print("  - Insufficient memory (need ~8GB RAM)")
        print("  - Need to accept model terms at https://huggingface.co/google/medgemma-4b-it")
        print("  - Transformers version incompatibility")
        return False
    
    return True


def test_medgemma_inference():
    """Test if MedGemma can run inference."""
    print("\n" + "=" * 60)
    print("TEST: MEDGEMMA INFERENCE")
    print("=" * 60)
    
    try:
        import torch
        from transformers import AutoModelForImageTextToText, AutoProcessor
        from PIL import Image
        import numpy as np
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    
    # Get device
    if torch.cuda.is_available():
        device = torch.device("cuda")
        dtype = torch.float16
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        device = torch.device("mps")
        dtype = torch.float32
    else:
        device = torch.device("cpu")
        dtype = torch.float32
    
    model_name = "google/medgemma-4b-it"
    
    # Load model
    print(f"\n⏳ Loading MedGemma...")
    try:
        processor = AutoProcessor.from_pretrained(model_name)
        # Don't use device_map="auto" with transformers 5.0 + MPS (has bugs)
        model = AutoModelForImageTextToText.from_pretrained(
            model_name,
            dtype=dtype
        )
        # Move to device manually
        model = model.to(device)
        print("✅ Model loaded")
    except Exception as e:
        print(f"❌ Loading failed: {e}")
        return False
    
    # Create dummy image
    print("\n🖼️  Creating dummy image...")
    image = Image.fromarray(np.zeros((896, 896, 3), dtype=np.uint8))
    
    # Prepare test message
    test_message = "What is hypertension?"
    print(f"\n💬 Test message: '{test_message}'")
    
    # Prepare messages
    messages = [
        {
            "role": "system",
            "content": [{"type": "text", "text": "You are a helpful medical AI assistant."}]
        },
        {
            "role": "user",
            "content": [
                {"type": "image", "image": image},
                {"type": "text", "text": test_message}
            ]
        }
    ]
    
    # Apply chat template
    print("\n📝 Applying chat template...")
    try:
        prompt = processor.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=False
        )
        print("✅ Template applied")
    except Exception as e:
        print(f"❌ Template failed: {e}")
        return False
    
    # Process inputs
    print("\n⚙️  Processing inputs...")
    try:
        inputs = processor(
            text=prompt,
            images=image,
            return_tensors="pt"
        )
        
        # Move tensors to device
        for k, v in inputs.items():
            if isinstance(v, torch.Tensor):
                if k == "pixel_values":
                    inputs[k] = v.to(device=device, dtype=dtype)
                else:
                    inputs[k] = v.to(device=device)
        
        print("✅ Inputs processed")
    except Exception as e:
        print(f"❌ Processing failed: {e}")
        return False
    
    # Generate
    print("\n🚀 Generating response...")
    try:
        start = time.time()
        input_len = inputs["input_ids"].shape[1]
        
        with torch.no_grad():
            generation = model.generate(
                **inputs,
                max_new_tokens=256,  # Shorter for testing
                do_sample=False
            )
        
        elapsed = time.time() - start
        print(f"✅ Generation completed in {elapsed:.2f} seconds")
        
        # Decode response
        gen_tokens = generation[0, input_len:]
        gen_tokens_cpu = gen_tokens.detach().cpu().tolist()
        response = processor.decode(gen_tokens_cpu, skip_special_tokens=True)
        
        # Print response
        print("\n" + "=" * 60)
        print("RESPONSE:")
        print("=" * 60)
        print(response)
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ Generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("MEDGEMMA IN MEDASR-TEST-ENV COMPATIBILITY TEST")
    print("=" * 60)
    print("\nTesting if MedGemma can run in the medasr-test-env environment.")
    print("This would enable a complete speech-to-medical-response pipeline:")
    print("  Audio → MedASR → Text → MedGemma → Medical Response")
    print()
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Dependency check failed")
        sys.exit(1)
    
    # Test model loading
    if not test_medgemma_loading():
        print("\n❌ MedGemma loading test failed")
        print("\n⚠️  CONCLUSION:")
        print("   MedGemma CANNOT run in medasr-test-env with current configuration.")
        print("   You may need separate environments for MedASR and MedGemma.")
        sys.exit(1)
    
    # Test inference
    if not test_medgemma_inference():
        print("\n❌ MedGemma inference test failed")
        print("\n⚠️  CONCLUSION:")
        print("   MedGemma can load but cannot run inference in medasr-test-env.")
        print("   You may need separate environments for MedASR and MedGemma.")
        sys.exit(1)
    
    # Success!
    print("\n" + "=" * 60)
    print("✅ SUCCESS: MEDGEMMA WORKS IN MEDASR-TEST-ENV!")
    print("=" * 60)
    print("\n🎉 Both MedASR and MedGemma can run in the same environment!")
    print("\n📝 This enables a unified pipeline:")
    print("   1. Audio input → MedASR → Text transcription")
    print("   2. Text transcription → MedGemma → Medical response")
    print("\n💡 You can now build a complete voice-activated medical AI assistant")
    print("   using a single environment (medasr-test-env)!")
    print("\n✨ Test completed successfully!")


if __name__ == "__main__":
    main()
