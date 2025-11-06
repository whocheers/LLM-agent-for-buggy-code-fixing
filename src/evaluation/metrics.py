"""Evaluation metrics for code fixing."""

import json
from typing import List, Dict, Any
from src.tools.code_executor import CodeExecutor


class Evaluator:
    """Evaluator for generated code fixes."""

    def __init__(self, timeout: int = 10):
        """Initialize the evaluator.

        Args:
            timeout: Maximum execution time for each test in seconds.
        """
        self.executor = CodeExecutor(timeout=timeout)
        self.results = []

    def evaluate_single(self, fixed_code: str, test_code: str, task_id: str) -> Dict[str, Any]:
        """Evaluate a single code fix.

        Args:
            fixed_code: The fixed code to evaluate.
            test_code: Test cases to run.
            task_id: Identifier for the task.

        Returns:
            Dictionary containing evaluation results.
        """
        result = self.executor.execute(fixed_code, test_code)

        eval_result = {
            "task_id": task_id,
            "passed": result["success"],
            "output": result.get("output", ""),
            "error": result.get("error", ""),
            "timeout": result.get("timeout", False)
        }

        self.results.append(eval_result)
        return eval_result

    def calculate_pass_at_k(self, k: int = 1) -> float:
        """Calculate pass@k metric.

        For pass@1, this is simply the percentage of tests passed on first attempt.

        Args:
            k: Number of attempts (for pass@k metric).

        Returns:
            Pass@k score as a percentage.
        """
        if not self.results:
            return 0.0

        passed_count = sum(1 for r in self.results if r["passed"])
        total_count = len(self.results)

        pass_rate = (passed_count / total_count) * 100
        return pass_rate

    def get_summary(self) -> Dict[str, Any]:
        """Get evaluation summary.

        Returns:
            Dictionary containing summary statistics.
        """
        if not self.results:
            return {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "timeout": 0,
                "pass@1": 0.0
            }

        passed = sum(1 for r in self.results if r["passed"])
        failed = sum(1 for r in self.results if not r["passed"] and not r["timeout"])
        timeout = sum(1 for r in self.results if r["timeout"])

        return {
            "total": len(self.results),
            "passed": passed,
            "failed": failed,
            "timeout": timeout,
            "pass@1": self.calculate_pass_at_k(1)
        }

    def save_results(self, filepath: str):
        """Save evaluation results to a JSON file.

        Args:
            filepath: Path to save results.
        """
        summary = self.get_summary()
        output = {
            "summary": summary,
            "detailed_results": self.results
        }

        with open(filepath, 'w') as f:
            json.dump(output, f, indent=2)

        print(f"\nEvaluation results saved to {filepath}")

    def print_summary(self):
        """Print evaluation summary to console."""
        summary = self.get_summary()

        print("\n" + "="*60)
        print("EVALUATION SUMMARY")
        print("="*60)
        print(f"Total tasks:      {summary['total']}")
        print(f"Passed:           {summary['passed']} ({summary['passed']/summary['total']*100:.1f}%)" if summary['total'] > 0 else "Passed: 0")
        print(f"Failed:           {summary['failed']}")
        print(f"Timeout:          {summary['timeout']}")
        print(f"\npass@1 score:     {summary['pass@1']:.2f}%")
        print("="*60 + "\n")
