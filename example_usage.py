"""Example script showing how to use the code fixing agent."""

from src.agent import create_llm, CodeFixingAgent
from src.tools import CodeExecutor
from config import Config


def example_simple_fix():
    """Example: Fix a simple buggy function."""
    print("="*60)
    print("EXAMPLE: Fixing a Simple Bug")
    print("="*60 + "\n")

    # Buggy code
    buggy_code = """
def multiply(a, b):
    return a + b  # Bug: should multiply, not add
"""

    # Test cases
    test_code = """
assert multiply(2, 3) == 6
assert multiply(4, 5) == 20
assert multiply(-1, 3) == -3
"""

    prompt = "Write a function that multiplies two numbers."

    print("Buggy Code:")
    print(buggy_code)
    print("\nTest Cases:")
    print(test_code)
    print("\n" + "-"*60)

    # Initialize LLM and agent
    print("\nInitializing agent...")
    llm = create_llm(provider=Config.LLM_PROVIDER)
    agent = CodeFixingAgent(llm, max_iterations=3)

    # Fix the code
    print("Fixing code...\n")
    fixed_code = agent.fix_code(buggy_code, test_code, prompt)

    print("Fixed Code:")
    print(fixed_code)
    print("\n" + "-"*60)

    # Test the fix
    print("\nTesting the fix...")
    executor = CodeExecutor()
    result = executor.execute(fixed_code, test_code)

    if result["success"]:
        print("✓ All tests passed!")
    else:
        print(f"✗ Tests failed: {result['error']}")

    print("\n" + "="*60 + "\n")


def example_direct_execution():
    """Example: Directly execute code without the agent."""
    print("="*60)
    print("EXAMPLE: Direct Code Execution")
    print("="*60 + "\n")

    code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

print(f"Fibonacci(5) = {fibonacci(5)}")
print(f"Fibonacci(10) = {fibonacci(10)}")
"""

    print("Code to execute:")
    print(code)
    print("\n" + "-"*60)

    executor = CodeExecutor(timeout=5)
    result = executor.execute(code)

    print("\nExecution Result:")
    if result["success"]:
        print("✓ Success!")
        print(f"Output:\n{result['output']}")
    else:
        print("✗ Failed!")
        print(f"Error:\n{result['error']}")

    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("CODE FIXING AGENT - EXAMPLES")
    print("="*60 + "\n")

    # Run examples
    try:
        example_direct_execution()
        example_simple_fix()
    except Exception as e:
        print(f"\nError running examples: {e}")
        print("\nMake sure you have:")
        print("1. Installed all requirements: pip install -r requirements.txt")
        print("2. Set up API keys if using cloud LLMs")
        print("3. Configured config.py with your preferred LLM provider")
