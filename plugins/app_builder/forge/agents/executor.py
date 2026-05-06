import asyncio
import tempfile
import os
import sys
import json
import subprocess
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from enum import Enum
import logging
import traceback

logger = logging.getLogger(__name__)


class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class ExecutionStatus(Enum):
    SUCCESS = "success"
    TIMEOUT = "timeout"
    ERROR = "error"
    FAILED = "failed"
    RESOURCE_EXCEEDED = "resource_exceeded"


class Executor:
    """
    🔥 Code Executor Agent - Runs generated code safely
    Compatible with Arena agent system
    """

    TIMEOUT = 10  # seconds
    MAX_MEMORY_MB = 512  # Maximum memory allowed for process
    MAX_RETRIES = 2
    RETRY_DELAY = 1  # seconds

    def __init__(self, name: str, bus, context: Dict):
        """
        Initialize Executor agent (compatible with Arena)
        
        Args:
            name: Agent name
            bus: Event bus instance
            context: Runtime context
        """
        self.name = name
        self.bus = bus
        self.context = context
        self.runtime = context.get("runtime")
        
        self.metrics = {}
        self.execution_history = []
        self.active_processes = {}
        
        logger.info(f"[{self.name}] Initialized")

    def register(self) -> None:
        """Register event subscriptions"""
        self._log(LogLevel.INFO, "Subscribed → CODE_GENERATED, CODE_FIXED")
        self.bus.subscribe("CODE_GENERATED", self.handle)
        self.bus.subscribe("CODE_FIXED", self.handle)

    # ─────────────────────────────────────────────
    # 📥 MAIN HANDLER
    # ─────────────────────────────────────────────
    async def handle(self, message):
        """Main message handler"""
        
        message_type = (
            message.message_type 
            if hasattr(message, "message_type") 
            else message.get("message_type")
        )
        
        if message_type not in ["CODE_GENERATED", "CODE_FIXED"]:
            return

        payload = (
            message.payload 
            if hasattr(message, "payload") 
            else message.get("payload", {})
        ) or {}
        
        files: Dict[str, str] = payload.get("files", {})
        user_id = payload.get("user_id", "default_user")
        execution_id = payload.get("execution_id", self._generate_execution_id())

        self._log(
            LogLevel.INFO,
            "Running code execution",
            user_id=user_id,
            execution_id=execution_id,
            file_count=len(files),
            message_type=message_type
        )

        result = await self._execute_project(files, execution_id)

        # 🚀 Send to tester
        completion_message = {
            "message_type": "CODE_EXECUTED",
            "sender": self.name,
            "recipient": "tester",
            "payload": {
                **payload,
                "execution": result,
                "execution_id": execution_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        await self.bus.publish(completion_message)

        self._log(
            LogLevel.INFO,
            "Sent CODE_EXECUTED",
            execution_id=execution_id,
            success=result.get("success"),
            returncode=result.get("returncode")
        )

        # Record metrics
        self._record_execution(execution_id, result)

    # ─────────────────────────────────────────────
    # 🚀 PROJECT EXECUTION ENGINE
    # ─��───────────────────────────────────────────
    async def _execute_project(self, files: Dict[str, str], execution_id: str) -> Dict[str, Any]:
        """Execute project with enhanced error handling and resource management"""

        # Validate files
        validation_error = self._validate_files(files)
        if validation_error:
            self._log(LogLevel.WARNING, f"File validation failed: {validation_error}")
            return {
                "success": False,
                "error": validation_error,
                "stdout": "",
                "stderr": validation_error,
                "execution_status": ExecutionStatus.ERROR.value,
                "execution_id": execution_id
            }

        try:
            with tempfile.TemporaryDirectory() as tmpdir:

                # 📁 Write files to temp dir with validation
                write_result = self._write_files_to_temp(tmpdir, files)
                if not write_result["success"]:
                    self._log(LogLevel.ERROR, f"File write failed: {write_result['error']}")
                    return {
                        "success": False,
                        "error": write_result["error"],
                        "stdout": "",
                        "stderr": write_result["error"],
                        "execution_status": ExecutionStatus.ERROR.value,
                        "execution_id": execution_id
                    }

                # 🚀 Run main.py with retry logic
                for attempt in range(self.MAX_RETRIES):
                    self._log(
                        LogLevel.DEBUG,
                        f"Execution attempt {attempt + 1}/{self.MAX_RETRIES}",
                        execution_id=execution_id
                    )

                    result = await self._run_code(tmpdir, execution_id)

                    # If successful or hard error, don't retry
                    if result["success"] or result.get("execution_status") in [
                        ExecutionStatus.ERROR.value,
                        ExecutionStatus.RESOURCE_EXCEEDED.value
                    ]:
                        return result

                    # For transient errors, retry with delay
                    if attempt < self.MAX_RETRIES - 1:
                        self._log(
                            LogLevel.WARNING,
                            f"Retrying after {self.RETRY_DELAY}s",
                            execution_id=execution_id,
                            attempt=attempt + 1
                        )
                        await asyncio.sleep(self.RETRY_DELAY)

                return result

        except Exception as e:
            error_trace = traceback.format_exc()
            self._log(
                LogLevel.ERROR,
                f"Unexpected execution error: {str(e)}",
                error=str(e),
                execution_id=execution_id
            )
            return {
                "success": False,
                "error": str(e),
                "stdout": "",
                "stderr": error_trace,
                "execution_status": ExecutionStatus.ERROR.value,
                "execution_id": execution_id,
                "timestamp": datetime.utcnow().isoformat()
            }

    # ─────────────────────────────────────────────
    # ✅ FILE VALIDATION
    # ─────────────────────────────────────────────
    def _validate_files(self, files: Dict[str, str]) -> Optional[str]:
        """Validate files before execution"""
        
        if not files:
            return "No files provided"

        if "main.py" not in files:
            return "main.py not found"

        # Validate file paths for security (prevent directory traversal)
        for path in files.keys():
            if ".." in path or path.startswith("/"):
                return f"Invalid file path: {path}"

        # Check for suspicious patterns
        main_content = files.get("main.py", "")
        dangerous_patterns = [
            "__import__",
            "exec(",
            "eval(",
            "os.system(",
        ]
        
        for pattern in dangerous_patterns:
            if pattern in main_content:
                self._log(
                    LogLevel.WARNING,
                    f"Suspicious pattern detected in main.py: {pattern}"
                )

        return None

    # ─────────────────────────────────────────────
    # 📁 FILE WRITING
    # ─────────────────────────────────────────────
    def _write_files_to_temp(self, tmpdir: str, files: Dict[str, str]) -> Dict[str, Any]:
        """Write files to temporary directory with error handling"""
        
        try:
            for path, content in files.items():
                try:
                    full_path = os.path.join(tmpdir, path)

                    # Create directories
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)

                    # Write file with encoding handling
                    with open(full_path, "w", encoding="utf-8") as f:
                        f.write(content)

                    self._log(LogLevel.DEBUG, f"Wrote file", file=path, size=len(content))

                except Exception as e:
                    self._log(LogLevel.ERROR, f"Failed to write file {path}", error=str(e))
                    return {
                        "success": False,
                        "error": f"Failed to write {path}: {str(e)}"
                    }

            return {"success": True}

        except Exception as e:
            return {
                "success": False,
                "error": f"Temp directory error: {str(e)}"
            }

    # ─────────────────────────────────────────────
    # ⚙️ CODE EXECUTION
    # ─────────────────────────────────────────────
    async def _run_code(self, tmpdir: str, execution_id: str) -> Dict[str, Any]:
        """Run the Python code with timeout and resource monitoring"""
        
        process = None
        try:
            # Create subprocess
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                "main.py",
                cwd=tmpdir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, "PYTHONUNBUFFERED": "1"}
            )

            self._log(
                LogLevel.DEBUG,
                "Process started",
                execution_id=execution_id,
                pid=process.pid
            )

            # Track process
            self.active_processes[execution_id] = process.pid

            try:
                # Wait for process with timeout
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.TIMEOUT
                )

                stdout_text = stdout.decode(errors="replace")
                stderr_text = stderr.decode(errors="replace")
                success = process.returncode == 0

                # Check resource usage
                resource_check = self._check_resource_usage(tmpdir)

                self._log(
                    LogLevel.INFO,
                    "Process completed",
                    execution_id=execution_id,
                    returncode=process.returncode,
                    success=success,
                    stdout_length=len(stdout_text),
                    stderr_length=len(stderr_text)
                )

                return {
                    "success": success,
                    "returncode": process.returncode,
                    "stdout": stdout_text,
                    "stderr": stderr_text,
                    "execution_status": ExecutionStatus.SUCCESS.value if success else ExecutionStatus.FAILED.value,
                    "execution_id": execution_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "resource_usage": resource_check
                }

            except asyncio.TimeoutError:
                # Handle timeout
                self._log(
                    LogLevel.WARNING,
                    "Process timeout - killing",
                    execution_id=execution_id,
                    timeout=self.TIMEOUT,
                    pid=process.pid
                )

                process.kill()
                
                try:
                    await asyncio.wait_for(process.wait(), timeout=2)
                except asyncio.TimeoutError:
                    process.kill()

                return {
                    "success": False,
                    "error": "Execution timeout",
                    "stdout": "",
                    "stderr": f"Process exceeded {self.TIMEOUT}s time limit",
                    "execution_status": ExecutionStatus.TIMEOUT.value,
                    "execution_id": execution_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "timeout": self.TIMEOUT
                }

        except Exception as e:
            error_trace = traceback.format_exc()
            self._log(
                LogLevel.ERROR,
                f"Process execution error: {str(e)}",
                error=str(e),
                execution_id=execution_id
            )

            if process and process.pid:
                try:
                    process.kill()
                except:
                    pass

            return {
                "success": False,
                "error": str(e),
                "stdout": "",
                "stderr": error_trace,
                "execution_status": ExecutionStatus.ERROR.value,
                "execution_id": execution_id,
                "timestamp": datetime.utcnow().isoformat()
            }

        finally:
            # Clean up tracking
            if execution_id in self.active_processes:
                del self.active_processes[execution_id]

    # ─────────────────────────────────────────────
    # 📊 RESOURCE MONITORING
    # ─────────────────────────────────────────────
    def _check_resource_usage(self, tmpdir: str) -> Dict[str, Any]:
        """Check resource usage of executed code"""
        
        try:
            # Get directory size
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(tmpdir):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(filepath)
                    except:
                        pass

            return {
                "temp_dir_size_mb": round(total_size / (1024 * 1024), 2),
                "within_limits": total_size < (self.MAX_MEMORY_MB * 1024 * 1024)
            }

        except Exception as e:
            self._log(LogLevel.WARNING, f"Resource check failed: {str(e)}")
            return {"resource_check_error": str(e)}

    # ─────────────────────────────────────────────
    # 📊 LOGGING & METRICS
    # ─────────────────────────────────────────────
    def _log(self, level: LogLevel, message: str, **context):
        """Structured logging with context"""
        timestamp = datetime.utcnow().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "agent": self.name,
            "level": level.value,
            "message": message,
            **context
        }

        # Format for console
        context_str = " | ".join(f"{k}={v}" for k, v in context.items()) if context else ""
        log_msg = f"[{self.name}] {message}"
        if context_str:
            log_msg += f" | {context_str}"
        
        # Log based on level
        if level == LogLevel.DEBUG:
            logger.debug(log_msg)
        elif level == LogLevel.INFO:
            logger.info(log_msg)
        elif level == LogLevel.WARNING:
            logger.warning(log_msg)
        elif level == LogLevel.ERROR:
            logger.error(log_msg)

        # Store in history
        self.execution_history.append(log_entry)

    def _record_execution(self, execution_id: str, result: Dict[str, Any]):
        """Record execution metrics"""
        
        execution_record = {
            "execution_id": execution_id,
            "success": result.get("success"),
            "status": result.get("execution_status"),
            "returncode": result.get("returncode"),
            "stdout_length": len(result.get("stdout", "")),
            "stderr_length": len(result.get("stderr", "")),
            "timestamp": result.get("timestamp"),
            "timeout": result.get("timeout"),
            "resource_usage": result.get("resource_usage")
        }

        self.execution_history.append(execution_record)

        # Update metrics
        status = result.get("execution_status", ExecutionStatus.ERROR.value)
        self.metrics[f"executions_{status}"] = self.metrics.get(f"executions_{status}", 0) + 1
        self.metrics["total_executions"] = self.metrics.get("total_executions", 0) + 1

        self._log(
            LogLevel.DEBUG,
            "Execution recorded",
            execution_id=execution_id,
            status=status
        )

    def _generate_execution_id(self) -> str:
        """Generate unique execution ID"""
        import uuid
        return str(uuid.uuid4())[:8]

    # ─────────────────────────────────────────────
    # 📈 METRICS & MONITORING
    # ─────────────────────────────────────────────
    def get_metrics(self) -> Dict[str, Any]:
        """Get all execution metrics"""
        return {
            "metrics": self.metrics,
            "active_processes": len(self.active_processes),
            "total_history_entries": len(self.execution_history)
        }

    def get_execution_history(self, limit: int = 100) -> List[Dict]:
        """Get recent execution history"""
        return self.execution_history[-limit:]

    def get_active_processes(self) -> Dict[str, int]:
        """Get list of active processes"""
        return self.active_processes

    def kill_execution(self, execution_id: str) -> bool:
        """Forcefully kill an execution"""
        if execution_id in self.active_processes:
            pid = self.active_processes[execution_id]
            try:
                os.kill(pid, 9)
                self._log(LogLevel.WARNING, f"Killed execution", execution_id=execution_id, pid=pid)
                return True
            except Exception as e:
                self._log(LogLevel.ERROR, f"Failed to kill execution", execution_id=execution_id, error=str(e))
                return False
        return False

    # ─────────────────────────────────────────────
    # AGENT INTERFACE (for chain)
    # ─────────────────────────────────────────────
    async def run(self, task: Dict) -> Dict:
        """
        Run executor as part of agent chain
        
        Args:
            task: Task containing code to execute
        
        Returns:
            Execution result
        """
        logger.info(f"[{self.name}] Running as chain agent")
        
        files = task.get("files", {})
        execution_id = self._generate_execution_id()
        
        result = await self._execute_project(files, execution_id)
        
        return {
            "message": "✅ Execution complete",
            "execution": result,
            "success": result.get("success")
        }