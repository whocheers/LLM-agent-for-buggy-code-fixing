"""Factory for creating LLM instances."""

from typing import Optional
from config import Config


def create_llm(provider: str = Config.LLM_PROVIDER, temperature: float = Config.TEMPERATURE):
    """Create an LLM instance based on the provider.

    Args:
        provider: LLM provider ("qwen", "openai", or "anthropic").
        temperature: Temperature for generation.

    Returns:
        LLM instance.
    """
    if provider == "qwen":
        return create_qwen_llm(temperature)
    elif provider == "openai":
        return create_openai_llm(temperature)
    elif provider == "anthropic":
        return create_anthropic_llm(temperature)
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")


def create_qwen_llm(temperature: float = Config.TEMPERATURE):
    """Create a Qwen LLM instance using HuggingFace.

    Args:
        temperature: Temperature for generation.

    Returns:
        Qwen LLM instance.
    """
    try:
        from langchain_huggingface import HuggingFacePipeline
        from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
        import torch

        print(f"Loading Qwen model: {Config.QWEN_MODEL_NAME}")
        print("This may take a while on first run...")

        # Load tokenizer and model
        tokenizer = AutoTokenizer.from_pretrained(
            Config.QWEN_MODEL_NAME,
            trust_remote_code=True
        )

        # Force CPU on Mac to avoid MPS BFloat16 issues
        import platform
        device = "cpu" if platform.system() == "Darwin" else "auto"

        model = AutoModelForCausalLM.from_pretrained(
            Config.QWEN_MODEL_NAME,
            torch_dtype=torch.float32,  # Use float32 for CPU compatibility
            device_map=device,
            trust_remote_code=True
        )

        # Create pipeline
        pipe = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            max_new_tokens=Config.MAX_TOKENS,
            temperature=temperature,
            do_sample=temperature > 0,
        )

        llm = HuggingFacePipeline(pipeline=pipe)
        print("Qwen model loaded successfully!")
        return llm

    except ImportError as e:
        print(f"Error: Required packages not installed. {e}")
        print("Install with: pip install transformers torch accelerate langchain-huggingface")
        raise
    except Exception as e:
        print(f"Error loading Qwen model: {e}")
        raise


def create_openai_llm(temperature: float = Config.TEMPERATURE):
    """Create an OpenAI LLM instance.

    Args:
        temperature: Temperature for generation.

    Returns:
        OpenAI LLM instance.
    """
    try:
        from langchain_openai import ChatOpenAI

        if not Config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not set in environment variables")

        llm = ChatOpenAI(
            model=Config.OPENAI_MODEL,
            temperature=temperature,
            max_tokens=Config.MAX_TOKENS,
            api_key=Config.OPENAI_API_KEY
        )
        print(f"OpenAI model ({Config.OPENAI_MODEL}) initialized successfully!")
        return llm

    except ImportError:
        print("Error: langchain-openai not installed.")
        print("Install with: pip install langchain-openai")
        raise
    except Exception as e:
        print(f"Error initializing OpenAI: {e}")
        raise


def create_anthropic_llm(temperature: float = Config.TEMPERATURE):
    """Create an Anthropic Claude LLM instance.

    Args:
        temperature: Temperature for generation.

    Returns:
        Anthropic LLM instance.
    """
    try:
        from langchain_anthropic import ChatAnthropic

        if not Config.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not set in environment variables")

        llm = ChatAnthropic(
            model=Config.ANTHROPIC_MODEL,
            temperature=temperature,
            max_tokens=Config.MAX_TOKENS,
            api_key=Config.ANTHROPIC_API_KEY
        )
        print(f"Anthropic model ({Config.ANTHROPIC_MODEL}) initialized successfully!")
        return llm

    except ImportError:
        print("Error: langchain-anthropic not installed.")
        print("Install with: pip install langchain-anthropic")
        raise
    except Exception as e:
        print(f"Error initializing Anthropic: {e}")
        raise
