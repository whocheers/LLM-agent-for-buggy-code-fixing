"""Main script for evaluating the code fixing agent on HumanEvalFix."""

import os
import argparse
import json
from datetime import datetime
from tqdm import tqdm

from config import Config
from src.agent import create_llm, CodeFixingAgent
from src.evaluation import HumanEvalFixDataset, Evaluator


def main():
    """Run the evaluation."""
    parser = argparse.ArgumentParser(description="Evaluate code fixing agent on HumanEvalFix")
    parser.add_argument(
        "--provider",
        type=str,
        default=Config.LLM_PROVIDER,
        choices=["qwen", "openai", "anthropic"],
        help="LLM provider to use"
    )
    parser.add_argument(
        "--subset-size",
        type=int,
        default=Config.DATASET_SUBSET_SIZE,
        help="Number of samples to evaluate (None for all)"
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=Config.MAX_ITERATIONS,
        help="Maximum iterations for the agent"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=Config.RESULTS_DIR,
        help="Directory to save results"
    )

    args = parser.parse_args()

    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)

    print("="*60)
    print("CODE FIXING AGENT EVALUATION")
    print("="*60)
    print(f"LLM Provider: {args.provider}")
    print(f"Max Iterations: {args.max_iterations}")
    print(f"Subset Size: {args.subset_size if args.subset_size else 'Full dataset'}")
    print("="*60 + "\n")

    # Load dataset
    print("Step 1: Loading dataset...")
    dataset = HumanEvalFixDataset(subset_size=args.subset_size)
    samples = dataset.load()
    print(f"✓ Loaded {len(samples)} samples\n")

    # Initialize LLM
    print("Step 2: Initializing LLM...")
    try:
        llm = create_llm(provider=args.provider)
        print("✓ LLM initialized\n")
    except Exception as e:
        print(f"✗ Error initializing LLM: {e}")
        print("\nPlease check your configuration and try again.")
        return

    # Initialize agent
    print("Step 3: Initializing agent...")
    agent = CodeFixingAgent(llm, max_iterations=args.max_iterations)
    print("✓ Agent initialized\n")

    # Initialize evaluator
    evaluator = Evaluator(timeout=Config.TIMEOUT_SECONDS)

    # Run evaluation
    print("Step 4: Running evaluation...")
    print("-" * 60)

    results = []

    for idx, sample in enumerate(tqdm(samples, desc="Fixing code")):
        task_id = sample["task_id"]
        buggy_code = sample["buggy_code"]
        test_code = sample["test"]
        prompt = sample.get("prompt", "")

        print(f"\n[{idx+1}/{len(samples)}] Task: {task_id}")

        # Fix the code using the agent
        try:
            fixed_code = agent.fix_code(buggy_code, test_code, prompt)
            print(f"✓ Generated fix")
        except Exception as e:
            print(f"✗ Error generating fix: {e}")
            fixed_code = buggy_code

        # Evaluate the fix
        eval_result = evaluator.evaluate_single(fixed_code, test_code, task_id)

        # Store detailed result
        results.append({
            "task_id": task_id,
            "prompt": prompt,
            "buggy_code": buggy_code,
            "fixed_code": fixed_code,
            "test_code": test_code,
            "passed": eval_result["passed"],
            "error": eval_result.get("error", ""),
        })

        if eval_result["passed"]:
            print(f"✓ Tests passed!")
        else:
            print(f"✗ Tests failed: {eval_result.get('error', 'Unknown error')[:100]}")

    print("\n" + "-" * 60)

    # Print summary
    evaluator.print_summary()

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = os.path.join(args.output_dir, f"results_{args.provider}_{timestamp}.json")
    evaluator.save_results(results_file)

    # Save detailed results
    detailed_file = os.path.join(args.output_dir, f"detailed_{args.provider}_{timestamp}.json")
    with open(detailed_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Detailed results saved to {detailed_file}")

    print("\n" + "="*60)
    print("EVALUATION COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()
