#!/usr/bin/env python3
"""
Direct MedGemma Model Test
Tests the model without any API overhead to check performance.
"""

import time
import torch
from PIL import Image
import numpy as np
from transformers import AutoModelForImageTextToText, AutoProcessor


def get_device_and_dtype():
    """Determine the best device and dtype for the model."""
    if torch.cuda.is_available():
        return torch.device("cuda"), torch.float16
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return torch.device("mps"), torch.float32
    return torch.device("cpu"), torch.float32


def create_dummy_image():
    """Create a dummy gray image for text-only queries."""
    return Image.fromarray(np.zeros((896, 896, 3), dtype=np.uint8))


def main():
    print("=" * 60)
    print("DIRECT MODEL TEST - NO API OVERHEAD")
    print("=" * 60)
    
    # Get device info
    device, dtype = get_device_and_dtype()
    print(f"\n🔧 Device: {device}")
    print(f"🔧 Dtype: {dtype}")
    
    # Model name (from server/config.py)
    model_name = "google/medgemma-4b-it"
    
    # Load model
    print(f"\n⏳ Loading model: {model_name}...")
    load_start = time.time()
    
    processor = AutoProcessor.from_pretrained(model_name)
    # Don't use device_map="auto" with transformers 5.0 + MPS (has bugs)
    model = AutoModelForImageTextToText.from_pretrained(
        model_name,
        dtype=dtype
    )
    model = model.to(device)
    
    load_time = time.time() - load_start
    print(f"✅ Model loaded in {load_time:.2f} seconds")
    
    # Prepare test message
    test_message = "What is the primary difference between WBCs and RBCs"
    print(f"\n💬 Test message: '{test_message}'")
    
    # Create dummy image
    print("\n🖼️  Creating dummy image for text-only query...")
    image = create_dummy_image()
    
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
    template_start = time.time()
    prompt = processor.apply_chat_template(
        messages,
        add_generation_prompt=True,
        tokenize=False
    )
    template_time = time.time() - template_start
    print(f"✅ Template applied in {template_time:.3f} seconds")
    
    # Process inputs
    print("\n⚙️  Processing inputs...")
    process_start = time.time()
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
    
    process_time = time.time() - process_start
    print(f"✅ Inputs processed in {process_time:.3f} seconds")
    
    # Get input length
    input_len = inputs["input_ids"].shape[1]
    print(f"📊 Input tokens: {input_len}")
    
    # Generate
    print("\n🚀 Generating response...")
    gen_start = time.time()
    
    with torch.no_grad():
        generation = model.generate(
            **inputs,
            max_new_tokens=1024,  # Limit for testing
            do_sample=False  # Greedy decoding
        )
    
    gen_time = time.time() - gen_start
    print(f"✅ Generation completed in {gen_time:.2f} seconds")
    
    # Decode response
    print("\n📤 Decoding response...")
    decode_start = time.time()
    gen_tokens = generation[0, input_len:]
    gen_tokens_cpu = gen_tokens.detach().cpu().tolist()
    response = processor.decode(gen_tokens_cpu, skip_special_tokens=True)
    decode_time = time.time() - decode_start
    print(f"✅ Decoded in {decode_time:.3f} seconds")
    
    # Output tokens
    output_tokens = len(gen_tokens_cpu)
    tokens_per_sec = output_tokens / gen_time if gen_time > 0 else 0
    print(f"📊 Output tokens: {output_tokens}")
    print(f"📊 Tokens/sec: {tokens_per_sec:.2f}")
    
    # Print response
    print("\n" + "=" * 60)
    print("RESPONSE:")
    print("=" * 60)
    print(response)
    print("=" * 60)
    
    # Summary
    total_time = load_time + template_time + process_time + gen_time + decode_time
    print(f"\n⏱️  TIMING BREAKDOWN:")
    print(f"   Model Loading:    {load_time:.2f}s")
    print(f"   Template:         {template_time:.3f}s")
    print(f"   Input Processing: {process_time:.3f}s")
    print(f"   Generation:       {gen_time:.2f}s")
    print(f"   Decoding:         {decode_time:.3f}s")
    print(f"   ─────────────────────────────")
    print(f"   TOTAL:            {total_time:.2f}s")
    print(f"\n✨ Test completed successfully!")


if __name__ == "__main__":
    main()
