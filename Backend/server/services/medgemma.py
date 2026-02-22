"""MedGemma model service for inference.

Based on the working hello.py implementation, this service wraps the MedGemma model
for use in the FastAPI server.
"""

import torch
from PIL import Image
from pathlib import Path
from typing import Optional, List, Dict, Any, AsyncIterator
from transformers import AutoModelForImageTextToText, AutoProcessor
from server.config import settings
from server.services.system_prompts import get_system_prompt, get_tool_usage_instructions
from server.api.schemas.request import ChatDomain, ChatMode
import asyncio
from queue import Queue
from threading import Thread
import time
import logging

logger = logging.getLogger(__name__)


# Default maximum tokens for generation
DEFAULT_MAX_TOKENS = 1024  # Match test script default


def format_tools_for_prompt(tools: List[Dict[str, Any]]) -> str:
    """Format tool schemas into a human-readable prompt section.
    
    Args:
        tools: List of tool schemas from MCP server
        
    Returns:
        Formatted string describing available tools
    """
    if not tools:
        return ""
    
    tool_descriptions = []
    for tool in tools:
        name = tool.get("name", "unknown")
        description = tool.get("description", "")
        input_schema = tool.get("inputSchema", {})
        properties = input_schema.get("properties", {})
        required = input_schema.get("required", [])
        
        # Format parameters
        params_list = []
        for param_name, param_info in properties.items():
            param_type = param_info.get("type", "any")
            param_desc = param_info.get("description", "")
            is_required = param_name in required
            req_marker = " (required)" if is_required else " (optional)"
            params_list.append(f"  - {param_name} ({param_type}){req_marker}: {param_desc}")
        
        params_str = "\n".join(params_list) if params_list else "  No parameters"
        
        tool_desc = f"""### {name}
{description}
Parameters: {params_str}
Usage: tool_code{{"tool": "{name}", "args": {{"param_name": value, ...}}}}
"""
        tool_descriptions.append(tool_desc)
    
    return "\n".join(tool_descriptions)


def get_device_and_dtype():
    """Determine the best device and dtype for the model."""
    # Check for environment variable to force CPU (useful for API server with MPS issues)
    import os
    if os.environ.get("FORCE_CPU", "false").lower() == "true":
        return torch.device("cpu"), torch.float32
    
    if torch.cuda.is_available():
        return torch.device("cuda"), torch.float16
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        # MPS often has limited float16 support; use float32 on MPS
        return torch.device("mps"), torch.float32
    return torch.device("cpu"), torch.float32


class MedGemmaService:
    """Service for MedGemma model inference."""
    
    def __init__(self):
        """Initialize the MedGemma service."""
        self.device, self.dtype = get_device_and_dtype()
        self.model = None
        self.processor = None
        self.model_loaded = False
        
    def load_model(self):
        """Load the MedGemma model and processor."""
        if self.model_loaded:
            return
            
        print(f"Loading MedGemma model on {self.device} with dtype {self.dtype}...")
        
        # Load processor
        self.processor = AutoProcessor.from_pretrained(settings.model_name)
        
        # Load model (transformers 5.0: don't use device_map with MPS, has bugs)
        self.model = AutoModelForImageTextToText.from_pretrained(
            settings.model_name,
            dtype=self.dtype
        )
        # Move to device manually (bypass accelerate bug with MPS in transformers 5.0)
        self.model = self.model.to(self.device)
        
        self.model_loaded = True
        print("MedGemma model loaded successfully!")
        
    def load_image(self, image_path: str) -> Image.Image:
        """Load an image from path."""
        img = Image.open(image_path).convert("RGB")
        return img
    
    def create_dummy_image(self) -> Image.Image:
        """Create a dummy gray image for text-only queries."""
        import numpy as np
        return Image.fromarray(np.zeros((896, 896, 3), dtype=np.uint8))
    
    def prepare_messages(
        self,
        conversation_history: List[Dict[str, Any]],
        user_message: str,
        image: Optional[Image.Image] = None,
        domain: ChatDomain = ChatDomain.GENERAL,
        mode: ChatMode = ChatMode.CONSULT,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """Prepare messages in the format expected by MedGemma.
        
        Args:
            conversation_history: Previous messages in the conversation
            user_message: Current user message
            image: Optional image for multimodal input
            domain: Medical domain for specialized behavior
            mode: Interaction mode for specialized behavior
            tools: Optional list of tool schemas to inject into system prompt
            
        Returns:
            List of messages formatted for MedGemma
        """
        messages = []
        
        # Add DYNAMIC system message based on domain/mode
        system_prompt = get_system_prompt(domain.value, mode.value)
        
        # Inject tools into system prompt if provided
        if tools:
            tool_text = format_tools_for_prompt(tools)
            tool_instructions = get_tool_usage_instructions()
            system_prompt += f"\n\n{tool_instructions}\n\n{tool_text}"
            logger.info(f"[MedGemma] Injected {len(tools)} tools into system prompt")
        
        # DEBUG: Log what prompt is being used
        print(f"[MedGemma] Using domain='{domain.value}', mode='{mode.value}'")
        
        messages.append({
            "role": "system",
            "content": [{"type": "text", "text": system_prompt}]
        })
        
        # Add conversation history
        for msg in conversation_history:
            role = msg.get("role")
            content = msg.get("content")
            
            if isinstance(content, str):
                messages.append({
                    "role": role,
                    "content": [{"type": "text", "text": content}]
                })
            else:
                messages.append({"role": role, "content": content})
        
        # Add current user message
        user_content = []
        if image is not None:
            user_content.append({"type": "image", "image": image})
        user_content.append({"type": "text", "text": user_message})
        
        messages.append({
            "role": "user",
            "content": user_content
        })
        
        return messages
    
    def generate_response(
        self,
        user_message: str,
        conversation_history: List[Dict[str, Any]] = None,
        image_path: Optional[str] = None,
        domain: ChatDomain = ChatDomain.GENERAL,
        mode: ChatMode = ChatMode.CONSULT,
        max_new_tokens: int = DEFAULT_MAX_TOKENS,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Generate a response from MedGemma.
        
        Args:
            user_message: The user's message text
            conversation_history: Previous messages in the conversation
            image_path: Optional path to an image file
            domain: Medical domain for specialized behavior
            mode: Interaction mode for specialized behavior
            max_new_tokens: Maximum number of tokens to generate
            tools: Optional list of tool schemas from MCP server
            
        Returns:
            The generated response text
        """
        gen_start = time.time()
        
        if not self.model_loaded:
            logger.info("[MEDGEMMA] Model not loaded, loading now...")
            t0 = time.time()
            self.load_model()
            logger.info(f"[MEDGEMMA] Model loaded: {time.time()-t0:.2f}s")
        
        if conversation_history is None:
            conversation_history = []
        
        # Load image if provided, otherwise use dummy
        t1 = time.time()
        if image_path and Path(image_path).exists():
            image = self.load_image(image_path)
            logger.info(f"[MEDGEMMA] Loaded image from {image_path}: {time.time()-t1:.3f}s")
        else:
            # MedGemma requires an image, use dummy for text-only
            image = self.create_dummy_image()
            logger.info(f"[MEDGEMMA] Created dummy image: {time.time()-t1:.3f}s")
        
        # Prepare messages with domain/mode
        t2 = time.time()
        messages = self.prepare_messages(conversation_history, user_message, image, domain, mode, tools)
        logger.info(f"[MEDGEMMA] Prepared messages: {time.time()-t2:.3f}s")
        
        # Apply chat template (text only, no tokenization - like test script)
        t3 = time.time()
        prompt = self.processor.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=False
        )
        logger.info(f"[MEDGEMMA] Applied chat template: {time.time()-t3:.3f}s")
        
        # Process inputs (tokenize + add image - like test script)
        t4 = time.time()
        inputs = self.processor(
            text=prompt,
            images=image,
            return_tensors="pt"
        )
        logger.info(f"[MEDGEMMA] Processed inputs: {time.time()-t4:.3f}s")
        
        # Move tensors to device
        t5 = time.time()
        for k, v in inputs.items():
            if isinstance(v, torch.Tensor):
                if k == "pixel_values":
                    inputs[k] = v.to(device=self.device, dtype=self.dtype)
                else:
                    inputs[k] = v.to(device=self.device)
        logger.info(f"[MEDGEMMA] Moved tensors to {self.device}: {time.time()-t5:.3f}s")
        
        # Get input length for slicing
        input_len = inputs["input_ids"].shape[1]
        logger.info(f"[MEDGEMMA] Input tokens: {input_len}")
        
        # Generate
        t6 = time.time()
        logger.info("[MEDGEMMA] Starting generation...")
        
        # Force MPS synchronization before generation
        if self.device.type == "mps":
            torch.mps.synchronize()
            logger.info("[MEDGEMMA] MPS synchronized before generation")
        
        with torch.no_grad():
            generation = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False  # Match test script exactly
            )
        
        # Force MPS synchronization after generation
        if self.device.type == "mps":
            torch.mps.synchronize()
            logger.info("[MEDGEMMA] MPS synchronized after generation")
        
        gen_time = time.time() - t6
        logger.info(f"[MEDGEMMA] Generation complete: {gen_time:.2f}s")
        
        # Slice off the prompt tokens and decode
        t7 = time.time()
        gen_tokens = generation[0, input_len:]
        gen_tokens_cpu = gen_tokens.detach().cpu().tolist()
        
        # Decode the response
        response = self.processor.decode(gen_tokens_cpu, skip_special_tokens=True)
        logger.info(f"[MEDGEMMA] Decoded {len(gen_tokens_cpu)} tokens: {time.time()-t7:.3f}s")
        logger.info(f"[MEDGEMMA] Tokens/sec: {len(gen_tokens_cpu)/gen_time:.2f}")
        logger.info(f"[MEDGEMMA] Total generation time: {time.time()-gen_start:.2f}s")
        
        return response
    
    async def generate_response_stream(
        self,
        user_message: str,
        conversation_history: List[Dict[str, Any]] = None,
        image_path: Optional[str] = None,
        domain: ChatDomain = ChatDomain.GENERAL,
        mode: ChatMode = ChatMode.CONSULT,
        max_new_tokens: int = DEFAULT_MAX_TOKENS,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> AsyncIterator[str]:
        """Generate a streaming response from MedGemma.
        
        This is a simplified streaming implementation that generates the full response
        and yields it in chunks. A true streaming implementation would use TextIteratorStreamer.
        
        Args:
            user_message: The user's message text
            conversation_history: Previous messages in the conversation
            image_path: Optional path to an image file
            domain: Medical domain for specialized behavior
            mode: Interaction mode for specialized behavior
            max_new_tokens: Maximum number of tokens to generate
            tools: Optional list of tool schemas from MCP server
            
        Yields:
            Chunks of the generated response
        """
        # For now, generate full response and stream it in chunks
        response = await asyncio.to_thread(
            self.generate_response,
            user_message,
            conversation_history,
            image_path,
            domain,
            mode,
            max_new_tokens,
            tools
        )
        
        # Stream the response line by line to preserve markdown formatting
        lines = response.split('\n')
        for i, line in enumerate(lines):
            if i > 0:
                yield '\n'  # Yield newline to preserve formatting
            
            # Stream each line word by word
            words = line.split()
            for j, word in enumerate(words):
                if j > 0:
                    yield ' '
                yield word
                await asyncio.sleep(0.01)  # Small delay for streaming effect


# Global service instance
medgemma_service = MedGemmaService()
