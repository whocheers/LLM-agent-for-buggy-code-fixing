"""Sandboxed code execution tool using Docker."""

import tempfile
import os
import subprocess
from typing import Dict, Any, Optional
from config import Config


class CodeExecutor:
    """Execute Python code in a sandboxed Docker container."""

    def __init__(self, timeout: int = Config.DOCKER_TIMEOUT):
        """Initialize the code executor.

        Args:
            timeout: Maximum execution time in seconds.
        """
        self.timeout = timeout
        self.docker_image = Config.DOCKER_IMAGE
        self.memory_limit = Config.DOCKER_MEMORY_LIMIT

    def _check_docker_available(self) -> bool:
        """Check if Docker is available."""
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def execute(self, code: str, test_code: Optional[str] = None) -> Dict[str, Any]:
        """Execute Python code in a sandboxed environment.

        Attempts to use Docker for secure sandboxing. If Docker is unavailable,
        falls back to subprocess execution (UNSAFE - see security warnings).

        Args:
            code: The Python code to execute.
            test_code: Optional test code to run after the main code.

        Returns:
            Dictionary containing:
                - success: Whether execution succeeded
                - output: Standard output
                - error: Error message if any
                - timeout: Whether execution timed out
                - sandboxed: Whether execution was sandboxed (Docker) or not
        """
        # Check if Docker is available, fallback to subprocess if not
        if not self._check_docker_available():
            print("⚠️  Docker not available - using UNSAFE subprocess fallback")
            result = self._execute_subprocess(code, test_code)
            result["sandboxed"] = False
            return result

        try:
            result = self._execute_docker(code, test_code)
            result["sandboxed"] = True
            return result
        except Exception as e:
            # Fallback to subprocess execution if Docker fails
            print(f"⚠️  Docker execution failed ({e}) - using UNSAFE subprocess fallback")
            result = self._execute_subprocess(code, test_code)
            result["sandboxed"] = False
            return result

    def _execute_docker(self, code: str, test_code: Optional[str] = None) -> Dict[str, Any]:
        """Execute code using Docker with enhanced security."""
        # Combine code and test code
        full_code = code
        if test_code:
            full_code = f"{code}\n\n{test_code}"

        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(full_code)
            temp_file = f.name

        try:
            # Run in Docker with enhanced security
            docker_cmd = [
                "docker", "run",
                "--rm",
                # Network isolation
                "--network", "none",
                # Resource limits
                "--memory", self.memory_limit,
                "--cpus", "1",
                "--pids-limit", "50",  # Prevent fork bombs
                # Security options
                "--read-only",  # Read-only root filesystem
                "--tmpfs", "/tmp:rw,noexec,nosuid,size=100m",  # Writable /tmp but no execution
                "--user", "nobody",  # Run as non-root user
                "--cap-drop", "ALL",  # Drop all capabilities
                "--security-opt", "no-new-privileges",  # Prevent privilege escalation
                # Mount code file
                "-v", f"{temp_file}:/code.py:ro",  # Mount as read-only
                self.docker_image,
                "python", "/code.py"
            ]

            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None,
                "timeout": False
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "error": f"Execution timed out after {self.timeout} seconds",
                "timeout": True
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": f"Execution error: {str(e)}",
                "timeout": False
            }
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file)
            except:
                pass

    def _execute_subprocess(self, code: str, test_code: Optional[str] = None) -> Dict[str, Any]:
        """Execute code using subprocess (UNSAFE FALLBACK - use only for testing).

        WARNING: This method provides NO sandboxing and should NOT be used in production
        or with untrusted code. The code runs directly on the host system with:
        - Full filesystem access
        - Network access
        - Access to environment variables and secrets
        - Ability to modify or delete files

        Only timeout protection is provided. Use Docker for secure sandboxing.
        """
        import warnings
        warnings.warn(
            "SECURITY WARNING: Executing code WITHOUT sandboxing! "
            "This is unsafe for untrusted code. Install Docker for proper sandboxing.",
            UserWarning,
            stacklevel=2
        )

        # Combine code and test code
        full_code = code
        if test_code:
            full_code = f"{code}\n\n{test_code}"

        # Create a temporary file instead of using -c to avoid command line injection
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(full_code)
            temp_file = f.name

        try:
            # Use -I flag for isolated mode (ignore environment variables like PYTHONPATH)
            result = subprocess.run(
                ["python", "-I", "-u", temp_file],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                # Minimal environment to reduce attack surface
                env={"PATH": os.environ.get("PATH", "")},
            )

            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None,
                "timeout": False
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "error": f"Execution timed out after {self.timeout} seconds",
                "timeout": True
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": f"Execution error: {str(e)}",
                "timeout": False
            }
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file)
            except:
                pass


def execute_code_tool(code: str, test_code: str = "") -> str:
    """Tool function for the agent to execute code in a sandboxed environment.

    Args:
        code: The Python code to execute.
        test_code: Optional test code to validate the solution.

    Returns:
        String describing the execution result.
    """
    executor = CodeExecutor()
    result = executor.execute(code, test_code if test_code else None)

    # Include sandbox status in the output
    sandbox_status = "🔒 Sandboxed (Docker)" if result.get("sandboxed", False) else "⚠️  UNSANDBOXED"

    if result["success"]:
        output = result["output"] if result["output"] else "Code executed successfully with no output."
        return f"✓ Execution successful! [{sandbox_status}]\nOutput:\n{output}"
    else:
        error_msg = result["error"] if result["error"] else "Unknown error"
        if result["timeout"]:
            return f"✗ Execution timed out! [{sandbox_status}]\nError: {error_msg}"
        return f"✗ Execution failed! [{sandbox_status}]\nError:\n{error_msg}"
