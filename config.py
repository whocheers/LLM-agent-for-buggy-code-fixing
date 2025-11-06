"""Configuration file for the code fixing agent."""

import os
from typing import Optional

class Config:
    """Configuration for the agent and evaluation."""

    # LLM Configuration
    # You can change this to use different models
    # Options: "qwen", "openai", "anthropic"
    LLM_PROVIDER: str = "qwen"

    # For Qwen (local model)
    QWEN_MODEL_NAME: str = "Qwen/Qwen2.5-Coder-0.5B-Instruct"

    # For OpenAI (if using OpenAI instead)
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL: str = "gpt-4o-mini"

    # For Anthropic (if using Claude instead)
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"

    # Agent Configuration
    MAX_ITERATIONS: int = 5
    TEMPERATURE: float = 0.2
    MAX_TOKENS: int = 2048

    # Evaluation Configuration
    DATASET_SUBSET_SIZE: Optional[int] = None  # Set to an integer to use a subset, None for full dataset
    NUM_SAMPLES_PER_TASK: int = 1  # For pass@k evaluation
    TIMEOUT_SECONDS: int = 10  # Timeout for code execution

    # Docker Configuration (for sandboxed execution)
    DOCKER_IMAGE: str = "python:3.10-slim"
    DOCKER_MEMORY_LIMIT: str = "512m"
    DOCKER_TIMEOUT: int = 10

    # Paths
    DATA_DIR: str = "data"
    RESULTS_DIR: str = "results"
