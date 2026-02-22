#!/usr/bin/env python3
"""
medgemma_run.py

Minimal runnable script to query google/medgemma-4b-it with an image+text prompt.
Sensible device/dtype selection, uses apply_chat_template(add_generation_prompt=True)
and slices off the prompt tokens after generation (this is the common cause of '<pad>'/echo).
"""
import argparse
from pathlib import Path
import torch
from PIL import Image
from transformers import AutoProcessor, AutoModelForImageTextToText

def get_device_and_dtype():
    if torch.cuda.is_available():
        return torch.device("cuda"), torch.float16
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        # MPS often has limited float16 support; use float32 on MPS to avoid unsupported ops.
        return torch.device("mps"), torch.float32
    return torch.device("cpu"), torch.float32

def load_image(path: Path):
    img = Image.open(path).convert("RGB")
    return img

def main():
    parser = argparse.ArgumentParser(description="Run google/medgemma-4b-it image+text inference")
    parser.add_argument("--image", "-i", type=Path, default=None,
                        help="Path to an RGB image file. If omitted, a gray dummy image is used.")
    parser.add_argument("--prompt", "-p", type=str, default="What is hemoglobin?",
                        help="Text prompt to ask the model about the image.")
    parser.add_argument("--max-new-tokens", type=int, default=256)
    args = parser.parse_args()

    device, dtype = get_device_and_dtype()
    print(f"Device: {device}, dtype: {dtype}")

    # Load image (or dummy)
    if args.image and args.image.exists():
        image = load_image(args.image)
    else:
        # dummy mid-gray image matching model's expected size (896x896)
        image = Image.new("RGB", (896, 896), color=(128, 128, 128))
        print("No image provided or not found — using dummy image (896x896 gray).")

    # Load processor + model
    processor = AutoProcessor.from_pretrained("google/medgemma-4b-it")
    # Use dtype argument (preferred over torch_dtype). device_map="auto" can help on multi-device setups.
    model = AutoModelForImageTextToText.from_pretrained(
        "google/medgemma-4b-it",
        device_map="auto",
        dtype=dtype
    )

    # Build messages following the Gemma3 template (image then text)
    messages = [
        {"role": "system", "content": [{"type": "text", "text": "You are a helpful medical assistant."}]},
        {"role": "user", "content": [{"type": "image", "image": image}, {"type": "text", "text": args.prompt}]}
    ]

    # Apply chat template; IMPORTANT: add_generation_prompt=True
    inputs = processor.apply_chat_template(
        messages,
        add_generation_prompt=True,
        tokenize=True,
        return_dict=True,
        return_tensors="pt"
    )

    # Move tensors to device carefully:
    # keep input_ids/attention masks as ints on device, but ensure pixel_values uses the chosen dtype.
    for k, v in inputs.items():
        if isinstance(v, torch.Tensor):
            if k == "pixel_values":
                inputs[k] = v.to(device=device, dtype=dtype)
            else:
                inputs[k] = v.to(device=device)

    # Compute length of input prompt tokens so we can slice them off after generation
    if "input_ids" not in inputs:
        raise RuntimeError("Processor did not return input_ids. Check processor.apply_chat_template usage.")
    input_len = inputs["input_ids"].shape[1]
    print(f"Input token length (will be sliced off): {input_len}")

    # Generate
    generation = model.generate(**inputs, max_new_tokens=args.max_new_tokens, do_sample=False)

    # Slice off the prompt tokens so we only decode the model's new tokens
    # generation shape: (batch, seq_len_total). We want generation[0, input_len:].
    gen_tokens = generation[0, input_len:]
    # Convert to list/CPU before decoding if needed
    gen_tokens_cpu = gen_tokens.detach().cpu().tolist()

    # Decode using the processor. This returns the assistant text (skip special tokens).
    answer = processor.decode(gen_tokens_cpu, skip_special_tokens=True)
    print("\n--- MODEL ANSWER ---\n")
    print(answer)
    print("\n--------------------\n")

if __name__ == "__main__":
    main()
