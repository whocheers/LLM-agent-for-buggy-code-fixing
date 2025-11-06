"""Test script to verify ReAct agent with tool access."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.agent.react_agent import CodeFixingAgent
from src.agent.llm_factory import create_llm
from config import Config


def test_react_agent():
    """Test the ReAct agent with a simple buggy function."""

    print("=" * 60)
    print("Testing ReAct Agent with Tool Access")
    print("=" * 60)

    # Simple buggy code: multiply function that adds instead
    buggy_code = """def multiply(a, b):
    return a + b  # Bug: should multiply, not add
"""

    # Test cases
    test_code = """
assert multiply(2, 3) == 6, "2 * 3 should equal 6"
assert multiply(5, 4) == 20, "5 * 4 should equal 20"
assert multiply(0, 10) == 0, "0 * 10 should equal 0"
print("All tests passed!")
"""

    prompt = "A function that multiplies two numbers"

    print("\n📝 Buggy Code:")
    print(buggy_code)
    print("\n🧪 Test Cases:")
    print(test_code)

    # Create LLM (use Qwen as default, or OpenAI if API key is set)
    print("\n🤖 Initializing LLM...")
    try:
        # Try OpenAI first if available (faster for testing)
        if Config.OPENAI_API_KEY and Config.OPENAI_API_KEY != "your-api-key-here":
            print("   Using OpenAI GPT-4o-mini")
            llm = create_llm("openai")
        else:
            print("   Using local Qwen model (this may take a while...)")
            llm = create_llm("qwen")
    except Exception as e:
        print(f"   ❌ Error creating LLM: {e}")
        return

    # Create agent with limited iterations for testing
    print("\n🔧 Creating ReAct agent...")
    agent = CodeFixingAgent(llm, max_iterations=5)

    # Run the agent
    print("\n🚀 Running ReAct agent (Reason -> Act -> Observe loop)...")
    print("-" * 60)

    try:
        fixed_code = agent.fix_code(buggy_code, test_code, prompt)

        print("\n" + "=" * 60)
        print("✅ Agent finished!")
        print("=" * 60)
        print("\n📦 Fixed Code:")
        print(fixed_code)

        # Test the fixed code
        print("\n🧪 Verifying fixed code...")
        from src.tools.code_executor import CodeExecutor
        executor = CodeExecutor()
        result = executor.execute(fixed_code, test_code)

        if result["success"]:
            print("✅ Fixed code passes all tests!")
            print(f"Output: {result['output']}")
        else:
            print("❌ Fixed code still has issues:")
            print(f"Error: {result['error']}")

    except Exception as e:
        print(f"\n❌ Error during agent execution: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_react_agent()
