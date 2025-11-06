# LLM-Based Code Fixing Agent

An AI agent that automatically fixes buggy Python code using a ReAct-style approach with LangGraph. The agent is evaluated on the HumanEvalFix benchmark.

## Overview

This project implements an LLM-based agent that:
- Analyzes buggy Python code
- Identifies and fixes bugs
- Validates fixes using test cases
- Uses a ReAct (Reasoning + Acting) approach with iterative refinement
- Executes code in a sandboxed environment for safety

## Architecture

### Components

1. **ReAct Agent** (`src/agent/react_agent.py`)
   - Implements reasoning and action loop
   - Uses LangGraph for agent orchestration
   - Iteratively fixes code based on test feedback

2. **Code Executor** (`src/tools/code_executor.py`)
   - Sandboxed code execution (Docker-based when available)
   - Fallback to subprocess with timeout
   - Safe execution of LLM-generated code

3. **Evaluation System** (`src/evaluation/`)
   - HumanEvalFix dataset loader
   - pass@1 metric implementation
   - Result tracking and reporting

4. **LLM Support**
   - Qwen (local, open-source)
   - OpenAI (GPT-4, GPT-3.5)
   - Anthropic Claude

## Installation

### Prerequisites

- Python 3.8+
- Docker (optional, for sandboxed execution)
- At least 4GB RAM (for running local models)

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd evaluation_of_agentic_system
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. (Optional) Configure API keys for cloud LLMs:
```bash
# For OpenAI
export OPENAI_API_KEY="your-api-key"

# For Anthropic
export ANTHROPIC_API_KEY="your-api-key"
```

## Configuration

Edit `config.py` to customize:

- **LLM Provider**: Choose between `"qwen"`, `"openai"`, or `"anthropic"`
- **Model Settings**: Temperature, max tokens, iterations
- **Dataset**: Subset size for faster testing
- **Docker**: Memory limits and timeouts

```python
class Config:
    LLM_PROVIDER: str = "qwen"  # or "openai" or "anthropic"
    QWEN_MODEL_NAME: str = "Qwen/Qwen2.5-Coder-0.5B-Instruct"
    MAX_ITERATIONS: int = 5
    DATASET_SUBSET_SIZE: Optional[int] = 5  # None for full dataset
```

## Usage

### Basic Evaluation

Run evaluation with default settings (Qwen model, small subset):

```bash
python main.py
```

### Advanced Options

```bash
# Use OpenAI
python main.py --provider openai --subset-size 10

# Use full dataset
python main.py --subset-size None

# Adjust max iterations
python main.py --max-iterations 10

# Custom output directory
python main.py --output-dir my_results
```

### Command-Line Arguments

- `--provider`: LLM provider (`qwen`, `openai`, `anthropic`)
- `--subset-size`: Number of samples to evaluate (default: 5)
- `--max-iterations`: Maximum fix attempts per task (default: 5)
- `--output-dir`: Directory for results (default: `results`)

## Results

The evaluation produces:

1. **Console Output**: Real-time progress and summary statistics
2. **Results JSON**: Summary with pass@1 score
3. **Detailed JSON**: Full results with code fixes and errors

Example summary:
```
============================================================
EVALUATION SUMMARY
============================================================
Total tasks:      5
Passed:           3 (60.0%)
Failed:           2
Timeout:          0

pass@1 score:     60.00%
============================================================
```

## Dataset

The system uses **HumanEvalFix** (Python subset), which contains:
- Buggy Python code
- Test cases for validation
- Problem descriptions

If the full dataset is unavailable, a fallback dataset with 5 sample tasks is used for testing.

## Sandboxed Execution

Code execution is sandboxed for safety:

### With Docker (Recommended)
- Isolated containers
- No network access
- Memory and CPU limits
- Automatic cleanup

### Without Docker (Fallback)
- Subprocess execution
- Timeout protection
- Limited isolation

To use Docker:
```bash
# Pull Python image
docker pull python:3.10-slim

# Run evaluation
python main.py
```

## Implementation Details

### ReAct Agent Flow

1. **Reasoning**: Agent analyzes buggy code and tests
2. **Action**: Generates a fix
3. **Observation**: Executes code and observes results
4. **Iteration**: Refines fix if tests fail
5. **Completion**: Returns final solution

### pass@1 Metric

The pass@1 metric measures the percentage of problems solved on the first attempt:

```
pass@1 = (# of tasks with passing tests) / (total # of tasks) × 100%
```

## Example

### Input (Buggy Code)
```python
def add(a, b):
    return a - b  # Bug: should be addition
```

### Test Cases
```python
assert add(2, 3) == 5
assert add(-1, 1) == 0
```

### Output (Fixed Code)
```python
def add(a, b):
    return a + b  # Fixed: now performs addition
```

## Project Structure

```
evaluation_of_agentic_system/
├── config.py                 # Configuration settings
├── main.py                   # Main evaluation script
├── requirements.txt          # Python dependencies
├── README.md                # This file
├── src/
│   ├── agent/
│   │   ├── react_agent.py   # ReAct agent implementation
│   │   └── llm_factory.py   # LLM creation utilities
│   ├── evaluation/
│   │   ├── dataset.py       # Dataset loader
│   │   └── metrics.py       # Evaluation metrics
│   └── tools/
│       └── code_executor.py # Sandboxed execution
├── data/                     # Dataset cache (auto-created)
└── results/                  # Evaluation results (auto-created)
```

## Troubleshooting

### Docker Not Available
The system automatically falls back to subprocess execution if Docker is unavailable. For better sandboxing, install Docker:
```bash
# macOS
brew install --cask docker

# Ubuntu
sudo apt-get install docker.io
```

### Memory Issues with Local Models
If running Qwen model causes memory issues:
1. Use a smaller model (e.g., `Qwen/Qwen2.5-Coder-0.5B-Instruct`)
2. Use cloud API (OpenAI or Anthropic)
3. Reduce `MAX_TOKENS` in config.py

### Dataset Loading Fails
The system uses a fallback dataset if HumanEvalFix can't be loaded. To use the full dataset:
```bash
pip install datasets
```

## Performance

Typical performance (on fallback dataset):

| Model | pass@1 | Time per Task |
|-------|--------|---------------|
| Qwen 0.5B | 40-60% | ~10s |
| GPT-4 | 80-100% | ~5s |
| Claude Sonnet | 80-100% | ~5s |

*Note: Results vary based on task complexity*

## Future Improvements

- [ ] Add support for more LLM providers (Ollama, LLaMA)
- [ ] Implement pass@k (k > 1) evaluation
- [ ] Add visualization of agent reasoning process
- [ ] Support for other programming languages
- [ ] Enhanced sandboxing with resource monitoring
- [ ] Caching of successful fixes

## References

- **HumanEvalFix Paper**: [https://arxiv.org/abs/2308.07124](https://arxiv.org/abs/2308.07124)
- **ReAct Paper**: [https://arxiv.org/abs/2210.03629](https://arxiv.org/abs/2210.03629)
- **LangGraph**: [https://github.com/langchain-ai/langgraph](https://github.com/langchain-ai/langgraph)

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

