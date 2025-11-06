"""HumanEvalFix dataset loader."""

import json
import os
from typing import List, Dict, Any, Optional
from datasets import load_dataset
from config import Config


class HumanEvalFixDataset:
    """Loader for the HumanEvalFix dataset."""

    def __init__(self, subset_size: Optional[int] = None):
        """Initialize the dataset loader.

        Args:
            subset_size: Number of samples to load. If None, load all samples.
        """
        self.subset_size = subset_size
        self.data = None

    def load(self) -> List[Dict[str, Any]]:
        """Load the HumanEvalFix dataset.

        Returns:
            List of dataset samples, each containing:
                - task_id: Unique identifier
                - buggy_code: The buggy code to fix
                - test: Test cases to validate the fix
                - prompt: Description of what the code should do
        """
        print("Loading HumanEvalFix dataset...")

        try:
            # Try to load from BigCode's datasets
            dataset = load_dataset("bigcode/humanevalpack", "python")

            # Convert to our format
            samples = []
            for idx, item in enumerate(dataset['test']):
                if self.subset_size and idx >= self.subset_size:
                    break

                sample = {
                    "task_id": item.get("task_id", f"task_{idx}"),
                    "buggy_code": item.get("buggy_solution", ""),
                    "test": item.get("test", ""),
                    "prompt": item.get("prompt", ""),
                    "fixed_code": item.get("canonical_solution", ""),  # Ground truth for reference
                }
                samples.append(sample)

            self.data = samples
            print(f"Loaded {len(samples)} samples from HumanEvalFix dataset.")
            return samples

        except Exception as e:
            print(f"Error loading from datasets library: {e}")
            print("Falling back to manual dataset creation...")
            return self._load_fallback_dataset()

    def _load_fallback_dataset(self) -> List[Dict[str, Any]]:
        """Create a small fallback dataset for testing."""
        # This is a minimal example dataset for testing when the full dataset isn't available
        samples = [
            {
                "task_id": "test/0",
                "prompt": "Write a function that returns the sum of two numbers.",
                "buggy_code": """def add(a, b):
    return a - b  # Bug: should be addition, not subtraction
""",
                "test": """
assert add(2, 3) == 5
assert add(-1, 1) == 0
assert add(0, 0) == 0
""",
                "fixed_code": """def add(a, b):
    return a + b
"""
            },
            {
                "task_id": "test/1",
                "prompt": "Write a function that checks if a number is even.",
                "buggy_code": """def is_even(n):
    return n % 2 == 1  # Bug: should check == 0 for even
""",
                "test": """
assert is_even(2) == True
assert is_even(3) == False
assert is_even(0) == True
assert is_even(-2) == True
""",
                "fixed_code": """def is_even(n):
    return n % 2 == 0
"""
            },
            {
                "task_id": "test/2",
                "prompt": "Write a function that returns the maximum of two numbers.",
                "buggy_code": """def max_two(a, b):
    if a < b:  # Bug: should be > for returning max
        return a
    return b
""",
                "test": """
assert max_two(5, 3) == 5
assert max_two(1, 10) == 10
assert max_two(-5, -3) == -3
""",
                "fixed_code": """def max_two(a, b):
    if a > b:
        return a
    return b
"""
            },
            {
                "task_id": "test/3",
                "prompt": "Write a function that reverses a string.",
                "buggy_code": """def reverse_string(s):
    return s  # Bug: doesn't reverse the string
""",
                "test": """
assert reverse_string("hello") == "olleh"
assert reverse_string("") == ""
assert reverse_string("a") == "a"
""",
                "fixed_code": """def reverse_string(s):
    return s[::-1]
"""
            },
            {
                "task_id": "test/4",
                "prompt": "Write a function that counts vowels in a string.",
                "buggy_code": """def count_vowels(s):
    vowels = "aeiou"
    count = 0
    for char in s.lower():
        if char not in vowels:  # Bug: should be 'in vowels'
            count += 1
    return count
""",
                "test": """
assert count_vowels("hello") == 2
assert count_vowels("AEIOU") == 5
assert count_vowels("xyz") == 0
assert count_vowels("") == 0
""",
                "fixed_code": """def count_vowels(s):
    vowels = "aeiou"
    count = 0
    for char in s.lower():
        if char in vowels:
            count += 1
    return count
"""
            }
        ]

        if self.subset_size:
            samples = samples[:self.subset_size]

        self.data = samples
        print(f"Created fallback dataset with {len(samples)} samples.")
        return samples

    def save_to_file(self, filepath: str):
        """Save the dataset to a JSON file.

        Args:
            filepath: Path to save the dataset.
        """
        if self.data is None:
            self.load()

        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(self.data, f, indent=2)
        print(f"Dataset saved to {filepath}")

    @staticmethod
    def load_from_file(filepath: str) -> List[Dict[str, Any]]:
        """Load dataset from a JSON file.

        Args:
            filepath: Path to the dataset file.

        Returns:
            List of dataset samples.
        """
        with open(filepath, 'r') as f:
            return json.load(f)
