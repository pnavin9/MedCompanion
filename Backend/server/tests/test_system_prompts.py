"""Unit tests for system prompts service."""

import pytest
from pathlib import Path
from server.services.system_prompts import (
    get_system_prompt, 
    list_available_prompts,
    clear_prompt_cache,
    PROMPTS_DIR
)


def test_radiology_diagnose_prompt():
    """Test loading radiology diagnose prompt."""
    prompt = get_system_prompt("radiology", "diagnose")
    assert "radiologist" in prompt.lower()
    assert "diagnosing" in prompt.lower() or "diagnose" in prompt.lower()
    assert "IMPORTANT" in prompt  # Has base disclaimer


def test_general_consult_prompt():
    """Test loading general consult prompt."""
    prompt = get_system_prompt("general", "consult")
    assert "medical assistant" in prompt.lower() or "consultation" in prompt.lower()
    assert "IMPORTANT" in prompt


def test_pathology_diagnose_prompt():
    """Test loading pathology diagnose prompt."""
    prompt = get_system_prompt("pathology", "diagnose")
    assert "pathologist" in prompt.lower()
    assert "IMPORTANT" in prompt


def test_dermatology_plan_prompt():
    """Test loading dermatology plan prompt."""
    prompt = get_system_prompt("dermatology", "plan")
    assert "dermatologist" in prompt.lower()
    assert "plan" in prompt.lower() or "treatment" in prompt.lower()
    assert "IMPORTANT" in prompt


def test_case_insensitive():
    """Test that domain/mode are case-insensitive."""
    prompt1 = get_system_prompt("Radiology", "Diagnose")
    prompt2 = get_system_prompt("radiology", "diagnose")
    assert prompt1 == prompt2


def test_invalid_combination_fallback():
    """Test fallback to default for invalid combinations."""
    prompt = get_system_prompt("invalid_domain", "invalid_mode")
    assert "medical assistant" in prompt.lower()
    assert "IMPORTANT" in prompt


def test_list_available_prompts():
    """Test listing all available prompts."""
    available = list_available_prompts()
    assert "radiology" in available
    assert "diagnose" in available["radiology"]
    assert "consult" in available["radiology"]
    assert "plan" in available["radiology"]
    
    assert "general" in available
    assert "pathology" in available
    assert "dermatology" in available


def test_cache_functionality():
    """Test LRU cache is working."""
    # First call
    prompt1 = get_system_prompt("radiology", "diagnose")
    # Second call should hit cache
    prompt2 = get_system_prompt("radiology", "diagnose")
    assert prompt1 == prompt2
    
    # Clear cache and reload
    clear_prompt_cache()
    prompt3 = get_system_prompt("radiology", "diagnose")
    assert prompt3 == prompt1


def test_prompts_directory_exists():
    """Test that prompts directory is properly set up."""
    assert PROMPTS_DIR.exists(), f"Prompts directory not found: {PROMPTS_DIR}"
    assert (PROMPTS_DIR / "_base.txt").exists(), "Base disclaimer file missing"
    assert (PROMPTS_DIR / "_default.txt").exists(), "Default prompt file missing"


def test_all_domain_mode_combinations():
    """Test that all expected domain/mode combinations exist."""
    domains = ["general", "radiology", "pathology", "dermatology"]
    modes = ["consult", "plan", "diagnose"]
    
    for domain in domains:
        for mode in modes:
            prompt = get_system_prompt(domain, mode)
            assert len(prompt) > 0, f"Empty prompt for {domain}/{mode}"
            assert "IMPORTANT" in prompt, f"Missing disclaimer for {domain}/{mode}"


def test_base_disclaimer_appended():
    """Test that base disclaimer is appended to all prompts."""
    prompt = get_system_prompt("radiology", "diagnose")
    base_file = PROMPTS_DIR / "_base.txt"
    
    with open(base_file, 'r', encoding='utf-8') as f:
        base_text = f.read().strip()
    
    assert base_text in prompt, "Base disclaimer not appended to prompt"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
