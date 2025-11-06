"""ReAct-style agent for fixing buggy Python code using LangGraph."""

from typing import TypedDict, Annotated, Sequence
import operator
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool
from config import Config
from src.tools.code_executor import execute_code_tool


class AgentState(TypedDict):
    """State for the ReAct agent."""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    buggy_code: str
    test_code: str
    fixed_code: str
    iteration: int
    max_iterations: int


class CodeFixingAgent:
    """ReAct-style agent that iteratively fixes buggy Python code."""

    def __init__(self, llm, max_iterations: int = Config.MAX_ITERATIONS):
        """Initialize the code fixing agent.

        Args:
            llm: Language model to use for the agent.
            max_iterations: Maximum number of fix attempts.
        """
        self.llm = llm
        self.max_iterations = max_iterations
        self.tools = []
        self.llm_with_tools = None
        self.graph = None

    def _create_tool(self, test_code: str):
        """Create a tool for code execution with the specific test code."""
        @tool
        def execute_code(code: str) -> str:
            """Execute Python code with the provided test cases to check if it works correctly.

            Args:
                code: The Python code to test.

            Returns:
                Execution result showing if tests passed or failed.
            """
            return execute_code_tool(code, test_code)

        return execute_code

    def _should_continue(self, state: AgentState) -> str:
        """Determine if the agent should continue or end.

        Args:
            state: Current agent state.

        Returns:
            Next node to execute: "tools", "end", or "max_iterations".
        """
        messages = state["messages"]
        last_message = messages[-1]

        # Check if max iterations reached
        if state["iteration"] >= state["max_iterations"]:
            return "max_iterations"

        # If the last message has tool calls, continue to tools
        if hasattr(last_message, "tool_calls") and len(last_message.tool_calls) > 0:
            return "tools"

        # If the message indicates completion, end
        if isinstance(last_message, AIMessage):
            content = last_message.content.lower()
            if "fixed code:" in content or "final solution:" in content:
                return "end"

        # Otherwise, end the conversation
        return "end"

    def _call_model(self, state: AgentState):
        """Call the language model with tool access.

        Args:
            state: Current agent state.

        Returns:
            Updated state with model response.
        """
        messages = state["messages"]
        # Use the LLM with tools bound
        response = self.llm_with_tools.invoke(messages)

        # Increment iteration
        new_iteration = state["iteration"] + 1

        return {
            "messages": [response],
            "iteration": new_iteration
        }

    def _extract_fixed_code(self, state: AgentState) -> AgentState:
        """Extract the final fixed code from the conversation.

        Args:
            state: Current agent state.

        Returns:
            Updated state with extracted fixed code.
        """
        messages = state["messages"]

        # Look through messages from most recent to find code blocks
        for message in reversed(messages):
            if isinstance(message, AIMessage):
                content = message.content

                # Try to extract code from markdown code blocks
                if "```python" in content:
                    # Extract from ```python ... ```
                    parts = content.split("```python")
                    if len(parts) > 1:
                        code_part = parts[-1].split("```")[0].strip()
                        return {"fixed_code": code_part}
                elif "```" in content:
                    # Extract from ``` ... ```
                    parts = content.split("```")
                    if len(parts) >= 3:
                        code_part = parts[-2].strip()
                        # Remove language identifier if present
                        if code_part.startswith("python\n"):
                            code_part = code_part[7:]
                        return {"fixed_code": code_part}

        # If no code block found, return the buggy code as fallback
        return {"fixed_code": state["buggy_code"]}

    def _build_graph(self) -> StateGraph:
        """Build the agent graph with tool execution capability.

        Returns:
            Compiled agent graph.
        """
        # Create the graph
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("agent", self._call_model)
        workflow.add_node("tools", ToolNode(self.tools))
        workflow.add_node("extract", self._extract_fixed_code)

        # Set entry point
        workflow.set_entry_point("agent")

        # Add conditional edges from agent
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "tools": "tools",  # Execute tools
                "end": "extract",
                "max_iterations": "extract"
            }
        )

        # Add edge from tools back to agent for iterative reasoning
        workflow.add_edge("tools", "agent")

        # Add edge from extract to end
        workflow.add_edge("extract", END)

        return workflow.compile()

    def fix_code(self, buggy_code: str, test_code: str, prompt: str = "") -> str:
        """Fix the buggy code using ReAct pattern with tool access.

        Args:
            buggy_code: The buggy Python code to fix.
            test_code: Test cases to validate the fix.
            prompt: Optional description of what the code should do.

        Returns:
            Fixed Python code.
        """
        # Create the code execution tool for this specific test
        execute_tool = self._create_tool(test_code)
        self.tools = [execute_tool]

        # Bind tools to the LLM
        self.llm_with_tools = self.llm.bind_tools(self.tools)

        # Build the graph with tools
        self.graph = self._build_graph()

        # Create the system message with ReAct instructions
        system_message = SystemMessage(content="""You are an expert Python programmer tasked with fixing buggy code using a ReAct (Reasoning + Acting) approach.

You have access to a tool called 'execute_code' that runs Python code with test cases in a sandboxed environment.

Your workflow should be:
1. **REASON**: Analyze the buggy code and identify potential issues
2. **ACT**: Use the execute_code tool to test your proposed fix
3. **OBSERVE**: Examine the execution results
4. **ITERATE**: If tests fail, reason about the failure and try again

IMPORTANT: You MUST use the execute_code tool to test your fixes. Do not just provide a solution without testing it first.

When you've confirmed your fix works (tests pass), provide the final solution in a markdown code block:
```python
# Your verified fixed code here
```

Be systematic and use the tool to validate your fixes.""")

        # Create the user message
        user_content = f"""Please fix the following buggy Python code.

"""
        if prompt:
            user_content += f"**Description:** {prompt}\n\n"

        user_content += f"""**Buggy Code:**
```python
{buggy_code}
```

**Test Cases:**
```python
{test_code}
```

Please analyze the bug and provide the fixed code."""

        user_message = HumanMessage(content=user_content)

        # Initialize state
        initial_state = {
            "messages": [system_message, user_message],
            "buggy_code": buggy_code,
            "test_code": test_code,
            "fixed_code": "",
            "iteration": 0,
            "max_iterations": self.max_iterations
        }

        # Run the graph
        try:
            final_state = self.graph.invoke(initial_state)
            return final_state.get("fixed_code", buggy_code)
        except Exception as e:
            print(f"Error during code fixing: {e}")
            return buggy_code
