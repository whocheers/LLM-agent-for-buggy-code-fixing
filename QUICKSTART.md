# Quick Start Guide

Get started with the Code Fixing Agent in 5 minutes!

## Option 1: Automated Setup (Recommended)

```bash
# Run the setup script
./setup.sh

# Activate virtual environment
source venv/bin/activate

# Run evaluation with default settings (uses Qwen, 5 samples)
python main.py
```

## Option 2: Manual Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run evaluation
python main.py
```

## Testing with Different LLM Providers

### 1. Local Model (Qwen) - Free, No API Key Required

```bash
# Already configured by default
python main.py --provider qwen --subset-size 5
```

**Note**: First run will download the model (~500MB). Requires ~4GB RAM.

### 2. OpenAI (Fastest, Requires API Key)

```bash
# Set API key
export OPENAI_API_KEY="your-api-key-here"

# Run evaluation
python main.py --provider openai --subset-size 5
```

### 3. Anthropic Claude (Highest Quality, Requires API Key)

```bash
# Set API key
export ANTHROPIC_API_KEY="your-api-key-here"

# Run evaluation
python main.py --provider anthropic --subset-size 5
```

## Quick Examples

### Example 1: Run on 3 samples with OpenAI
```bash
python main.py --provider openai --subset-size 3
```

### Example 2: Run full dataset with local model
```bash
python main.py --provider qwen
```

### Example 3: Try the interactive example
```bash
python example_usage.py
```

## Understanding the Output

After running, you'll see:

1. **Console Output**: Real-time progress
   ```
   [1/5] Task: test/0
   ✓ Generated fix
   ✓ Tests passed!
   ```

2. **Summary Statistics**:
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

3. **Result Files** (in `results/` directory):
   - `results_<provider>_<timestamp>.json`: Summary with metrics
   - `detailed_<provider>_<timestamp>.json`: Full results with code

## Troubleshooting

### "Docker not available"
This is normal! The system automatically falls back to subprocess execution. Your code will still run safely.

### "Out of memory" with Qwen
Try a smaller model or use a cloud API:
```python
# In config.py, change:
QWEN_MODEL_NAME: str = "Qwen/Qwen2.5-Coder-0.5B-Instruct"
# Or use:
LLM_PROVIDER: str = "openai"
```

### "Dataset loading failed"
The system uses a built-in fallback dataset with 5 examples. This is expected and sufficient for testing.

## Next Steps

1. **Customize Configuration**: Edit `config.py` to adjust settings
2. **Review Results**: Check the `results/` directory for detailed output
3. **Extend the Agent**: Modify `src/agent/react_agent.py` to improve performance
4. **Try More Samples**: Increase `--subset-size` for comprehensive evaluation

## Need Help?

- Check `README.md` for full documentation
- Review `example_usage.py` for code samples
- See `config.py` for all configuration options
