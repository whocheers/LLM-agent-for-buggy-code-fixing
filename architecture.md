# Architecture: ReAct Code Fixing Agent with LangGraph

## System Architecture

```
┌───────────────────────────────────────────────────────────────────┐
│                     main.py (Orchestrator)                        │
│  CLI args → Load Dataset → Init LLM → Init Agent → Evaluate      │
└──────┬──────────────┬──────────────────────┬──────────────────────┘
       │              │                      │
       ▼              ▼                      ▼
┌────────────┐ ┌──────────────┐  ┌─────────────────────────┐
│ config.py  │ │ LLM Factory  │  │ evaluation/              │
│ provider,  │ │ (llm_factory │  │  dataset.py              │
│ model,     │ │  .py)        │  │   HumanEvalFix loader    │
│ iterations,│ │              │  │   (164 Python samples)   │
│ timeouts,  │ │ • Qwen local │  │  metrics.py              │
│ docker cfg │ │ • OpenAI API │  │   Evaluator (pass@1)     │
└────────────┘ │ • Claude API │  │   JSON result export     │
               └──────┬───────┘  └─────────────────────────┘
                      │
                      ▼
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║                 CodeFixingAgent (react_agent.py)                   ║
║                                                                   ║
║  ┌─────────────────────────────────────────────────────────────┐  ║
║  │              ReAct Pattern (Yao et al., 2022)               │  ║
║  │                                                              │  ║
║  │  Unlike chain-of-thought (reasoning only) or pure tool use  │  ║
║  │  (acting only), ReAct interleaves BOTH in a closed loop:    │  ║
║  │                                                              │  ║
║  │    REASON → ACT → OBSERVE → REASON → ACT → OBSERVE → ...   │  ║
║  │                                                              │  ║
║  │  REASON:  LLM analyzes buggy code, identifies root cause    │  ║
║  │  ACT:     LLM generates fix, calls execute_code tool        │  ║
║  │  OBSERVE: Agent inspects test results (pass/fail/error)     │  ║
║  │                                                              │  ║
║  │  This grounds reasoning in real execution feedback,          │  ║
║  │  reducing hallucination and enabling self-correction.        │  ║
║  └─────────────────────────────────────────────────────────────┘  ║
║                                                                   ║
║  ┌─────────────────────────────────────────────────────────────┐  ║
║  │            LangGraph StateGraph (Compiled)                  │  ║
║  │                                                              │  ║
║  │  State: messages[] | buggy_code | test_code | fixed_code    │  ║
║  │         iteration  | max_iterations                         │  ║
║  │                                                              │  ║
║  │            ┌─────────────────────┐                           │  ║
║  │            │    "agent" node     │                           │  ║
║  │            │  LLM.invoke()       │◄──────────────┐           │  ║
║  │            │  REASON + plan ACT  │               │           │  ║
║  │            └─────────┬───────────┘               │           │  ║
║  │              _should_continue()                  │           │  ║
║  │               │               │                  │           │  ║
║  │    has tool    │    "end" or   │                  │ loop      │  ║
║  │    calls       │    max iters  │                  │ back      │  ║
║  │               ▼               ▼                  │           │  ║
║  │  ┌──────────────────┐  ┌──────────────┐          │           │  ║
║  │  │  "tools" node    │  │ "extract"    │          │           │  ║
║  │  │  ToolNode:       │  │  Parse fixed │          │           │  ║
║  │  │  ACT + OBSERVE   │──┘  code from   │          │           │  ║
║  │  │  (execute code   │  │  ```python   │          │           │  ║
║  │  │   against tests) │  │  blocks      │          │           │  ║
║  │  └────────┬─────────┘  └──────┬───────┘          │           │  ║
║  │           └───────────────────┼──────────────────┘           │  ║
║  │           (up to 5 iters)     ▼                              │  ║
║  │                          ┌────────┐                          │  ║
║  │                          │  END   │                          │  ║
║  │                          └────────┘                          │  ║
║  └─────────────────────────────────────────────────────────────┘  ║
║                                                                   ║
╚══════════════════════════╤════════════════════════════════════════╝
                           │ tool call
                           ▼
          ┌──────────────────────────────────┐
          │  CodeExecutor (code_executor.py) │
          │  Docker sandbox (preferred)      │
          │    no-network, read-only,        │
          │    non-root, mem/cpu limits      │
          │  Subprocess fallback (timeout)   │
          └──────────────────────────────────┘
```

## Mermaid Diagram (renders on GitHub)

```mermaid
flowchart TB
    subgraph Main["main.py — Orchestrator"]
        CLI["CLI Args: provider, subset-size, max-iterations"]
    end

    subgraph Config["config.py"]
        CFG["LLM provider, model, iterations, timeouts, Docker settings"]
    end

    subgraph LLMFactory["LLM Factory"]
        LLM["Qwen (local) | OpenAI | Claude"]
    end

    subgraph Dataset["evaluation/"]
        HEF["HumanEvalFixDataset — 164 Python samples"]
        Eval["Evaluator — pass@1, JSON export"]
    end

    subgraph Agent["CodeFixingAgent (react_agent.py)"]
        direction TB

        subgraph ReAct["ReAct: Reasoning + Acting (Yao et al., 2022)"]
            Loop["REASON → ACT → OBSERVE → loop\nGrounds LLM in real execution feedback\nReduces hallucination via self-correction"]
        end

        subgraph Graph["LangGraph StateGraph"]
            AgentNode["'agent' — LLM reasons about bug"]
            AgentNode -->|"tool_calls"| ToolsNode["'tools' — execute code + tests"]
            ToolsNode -->|"loop back"| AgentNode
            AgentNode -->|"done / max iters"| Extract["'extract' — parse fixed code"]
            Extract --> EndNode([END])
        end
    end

    subgraph Executor["CodeExecutor"]
        Docker["Docker sandbox: no-network, read-only, non-root"]
        Sub["Subprocess fallback: timeout only"]
    end

    CLI --> LLMFactory --> Agent
    CLI --> Dataset --> Agent
    Agent -->|"tool call"| Executor
    Agent -->|"fixed code"| Eval
```
