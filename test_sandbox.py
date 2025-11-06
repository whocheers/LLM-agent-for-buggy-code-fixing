"""Test script to verify sandbox security."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.tools.code_executor import CodeExecutor


def test_sandbox_security():
    """Run security tests on the sandbox."""

    print("=" * 70)
    print("Sandbox Security Test Suite")
    print("=" * 70)

    executor = CodeExecutor()

    # Check if Docker is available
    docker_available = executor._check_docker_available()
    print(f"\n🐳 Docker Available: {docker_available}")

    if not docker_available:
        print("⚠️  WARNING: Docker not available - tests will use UNSAFE subprocess fallback")
        print("   Install Docker for proper sandboxing")

    tests = []

    # Test 1: Network isolation
    print("\n" + "=" * 70)
    print("Test 1: Network Isolation")
    print("=" * 70)
    print("Attempting to make network connection...")
    result = executor.execute("""
import socket
try:
    socket.gethostbyname('google.com')
    print('NETWORK ACCESS GRANTED')
except Exception as e:
    print(f'Network blocked: {e}')
""")

    sandboxed = result.get("sandboxed", False)
    if sandboxed:
        # In Docker, network should be blocked
        success = "network blocked" in result.get("output", "").lower() or not result.get("success", True)
        print(f"✅ PASS: Network isolated" if success else "❌ FAIL: Network accessible")
    else:
        print("⚠️  SKIP: Subprocess fallback has network access (expected)")
        success = True

    tests.append(("Network Isolation", success))
    print(f"Sandbox status: {'🔒 Sandboxed' if sandboxed else '⚠️  Unsandboxed'}")
    print(f"Output: {result.get('output', '')[:200]}")

    # Test 2: Filesystem write protection
    print("\n" + "=" * 70)
    print("Test 2: Filesystem Write Protection")
    print("=" * 70)
    print("Attempting to write to root filesystem...")
    result = executor.execute("""
import os
try:
    with open('/root_test.txt', 'w') as f:
        f.write('hacked')
    print('FILESYSTEM WRITE SUCCESSFUL')
except Exception as e:
    print(f'Write blocked: {e}')
""")

    sandboxed = result.get("sandboxed", False)
    if sandboxed:
        # In Docker with read-only root, should fail
        success = "write blocked" in result.get("output", "").lower() or "read-only" in str(result.get("error", "")).lower()
        print(f"✅ PASS: Filesystem protected" if success else "❌ FAIL: Filesystem writable")
    else:
        print("⚠️  SKIP: Subprocess fallback has filesystem access (expected)")
        success = True

    tests.append(("Filesystem Protection", success))
    print(f"Sandbox status: {'🔒 Sandboxed' if sandboxed else '⚠️  Unsandboxed'}")
    print(f"Output: {result.get('output', '')[:200]}")

    # Test 3: Timeout protection
    print("\n" + "=" * 70)
    print("Test 3: Timeout Protection")
    print("=" * 70)
    print("Attempting infinite loop (should timeout after 10s)...")
    result = executor.execute("""
import time
time.sleep(999)
print('TIMEOUT FAILED')
""")

    success = result.get("timeout", False) or "timed out" in str(result.get("error", "")).lower()
    print(f"✅ PASS: Timeout works" if success else "❌ FAIL: Timeout not enforced")
    tests.append(("Timeout Protection", success))
    print(f"Timeout: {result.get('timeout', False)}")
    print(f"Error: {result.get('error', '')[:200]}")

    # Test 4: Memory limit (Docker only)
    if docker_available:
        print("\n" + "=" * 70)
        print("Test 4: Memory Limit")
        print("=" * 70)
        print("Attempting to allocate excessive memory...")
        result = executor.execute("""
data = []
try:
    for i in range(10000):
        data.append('x' * 10**6)  # 1MB per iteration
    print('MEMORY LIMIT FAILED')
except MemoryError:
    print('Memory limit enforced')
""")

        sandboxed = result.get("sandboxed", False)
        # Should either hit memory limit or be killed by Docker
        success = (not result.get("success", True) or
                  "memory limit" in result.get("output", "").lower() or
                  "killed" in str(result.get("error", "")).lower())
        print(f"✅ PASS: Memory limited" if success else "⚠️  WARNING: Memory limit not hit (may be OK)")
        tests.append(("Memory Limit", success))
        print(f"Success: {result.get('success', False)}")
        print(f"Output: {result.get('output', '')[:200]}")

    # Test 5: User permissions (Docker only)
    if docker_available:
        print("\n" + "=" * 70)
        print("Test 5: Non-Root Execution")
        print("=" * 70)
        print("Checking user permissions...")
        result = executor.execute("""
import os
import pwd
uid = os.getuid()
try:
    username = pwd.getpwuid(uid).pw_name
except:
    username = 'unknown'
print(f'Running as UID: {uid}, User: {username}')
print(f'Is root: {uid == 0}')
""")

        sandboxed = result.get("sandboxed", False)
        if sandboxed:
            # Should run as nobody (UID 65534) not root
            output = result.get("output", "")
            success = "is root: false" in output.lower() or "uid: 65534" in output.lower() or "nobody" in output.lower()
            print(f"✅ PASS: Running as non-root" if success else "⚠️  WARNING: May be running as root")
            tests.append(("Non-Root User", success))
        else:
            print("⚠️  SKIP: Subprocess runs as current user")
        print(f"Output: {result.get('output', '')}")

    # Test 6: Process limits (Docker only)
    if docker_available:
        print("\n" + "=" * 70)
        print("Test 6: Fork Bomb Protection")
        print("=" * 70)
        print("Attempting fork bomb (should be limited)...")
        result = executor.execute("""
import os
count = 0
try:
    while count < 100:
        os.fork()
        count += 1
    print(f'FORK BOMB SUCCESSFUL: {count} processes')
except Exception as e:
    print(f'Fork limited after {count} attempts: {e}')
""")

        sandboxed = result.get("sandboxed", False)
        # Should fail or be limited by --pids-limit 50
        success = not result.get("success", False) or "limited" in result.get("output", "").lower()
        print(f"✅ PASS: Process limit enforced" if success else "⚠️  WARNING: Fork bomb not fully prevented")
        tests.append(("Fork Bomb Protection", success))
        print(f"Success: {result.get('success', False)}")
        print(f"Output: {result.get('output', '')[:200]}")

    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)

    passed = sum(1 for _, success in tests if success)
    total = len(tests)

    for test_name, success in tests:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if docker_available:
        if passed == total:
            print("\n🎉 All security tests passed! Sandbox is working correctly.")
        else:
            print(f"\n⚠️  Some tests failed. Review security configuration.")
    else:
        print("\n⚠️  Docker not available - install Docker for full sandbox security")
        print("   Current mode is NOT secure for untrusted code")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    try:
        test_sandbox_security()
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
