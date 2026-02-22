"""System prompt management for MedGemma.

This module provides file-based system prompt loading with caching.
Prompts are organized by domain and mode in the prompts/ directory.
"""

from pathlib import Path
from typing import Dict
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

# Path to prompts directory
PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


@lru_cache(maxsize=128)
def get_system_prompt(domain: str, mode: str) -> str:
    """
    Load system prompt from file system.
    
    Args:
        domain: Medical domain (e.g., "radiology", "general")
        mode: Interaction mode (e.g., "diagnose", "consult")
    
    Returns:
        Complete system prompt with base disclaimer appended
    
    Raises:
        FileNotFoundError: If prompts directory doesn't exist
    """
    
    # Normalize inputs to lowercase
    domain = domain.lower()
    mode = mode.lower()
    
    # Try specific domain/mode file
    prompt_file = PROMPTS_DIR / domain / f"{mode}.txt"
    
    if prompt_file.exists():
        logger.info(f"Loading prompt from {prompt_file}")
        return _load_prompt_file(prompt_file)
    
    # Fallback to default
    default_file = PROMPTS_DIR / "_default.txt"
    logger.warning(f"Prompt not found for {domain}/{mode}, using default")
    
    if not default_file.exists():
        raise FileNotFoundError(f"Default prompt file not found: {default_file}")
    
    return _load_prompt_file(default_file)


def _load_prompt_file(file_path: Path) -> str:
    """
    Load prompt file and append base disclaimer.
    
    Args:
        file_path: Path to the prompt file
    
    Returns:
        Prompt text with base disclaimer appended
    """
    base_file = PROMPTS_DIR / "_base.txt"
    
    # Load base disclaimer
    base_text = ""
    if base_file.exists():
        with open(base_file, 'r', encoding='utf-8') as f:
            base_text = f.read().strip()
    
    # Load specific prompt
    with open(file_path, 'r', encoding='utf-8') as f:
        prompt_text = f.read().strip()
    
    # Combine: prompt + base disclaimer
    if base_text:
        return f"{prompt_text}\n\n{base_text}"
    return prompt_text


def list_available_prompts() -> Dict[str, list]:
    """
    List all available domain/mode combinations.
    Useful for validation and debugging.
    
    Returns:
        Dict mapping domains to available modes
    """
    available = {}
    
    if not PROMPTS_DIR.exists():
        return available
    
    for domain_dir in PROMPTS_DIR.iterdir():
        if domain_dir.is_dir() and not domain_dir.name.startswith('_'):
            modes = []
            for mode_file in domain_dir.glob("*.txt"):
                modes.append(mode_file.stem)
            available[domain_dir.name] = modes
    
    return available


def clear_prompt_cache():
    """Clear the LRU cache. Useful for hot-reloading prompts in development."""
    get_system_prompt.cache_clear()
    get_tool_usage_instructions.cache_clear()
    logger.info("Prompt cache cleared")


@lru_cache(maxsize=1)
def get_tool_usage_instructions() -> str:
    """
    Load tool usage instructions from file.
    
    Returns:
        Tool usage instructions text
    """
    instructions_file = PROMPTS_DIR / "tool_usage_instructions.txt"
    
    if not instructions_file.exists():
        logger.warning(f"Tool usage instructions not found: {instructions_file}")
        return ""
    
    with open(instructions_file, 'r', encoding='utf-8') as f:
        return f.read().strip()
