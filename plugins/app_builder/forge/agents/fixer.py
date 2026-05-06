import re
import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class Fixer:
    """
    🔥 Code Fixer Agent - Fixes code issues from failed reviews
    Compatible with Arena agent system
    """

    MAX_ATTEMPTS = 3
    LLM_MAX_RETRIES = 2
    LLM_RETRY_BACKOFF = 2  # seconds

    # Issue pattern detection
    ISSUE_PATTERNS = {
        "import_error": re.compile(r"(ModuleNotFoundError|ImportError|No module named).*", re.IGNORECASE),
        "syntax_error": re.compile(r"SyntaxError.*", re.IGNORECASE),
        "type_error": re.compile(r"TypeError.*", re.IGNORECASE),
        "name_error": re.compile(r"(NameError|undefined).*", re.IGNORECASE),
        "attribute_error": re.compile(r"AttributeError.*", re.IGNORECASE),
        "runtime_error": re.compile(r"(RuntimeError|Exception).*", re.IGNORECASE),
        "missing_dependency": re.compile(r"(No module named|Cannot find|not found).*", re.IGNORECASE),
    }

    # Package mapping for common issues
    PACKAGE_MAPPING = {
        "fastapi": ["fastapi", "pydantic"],
        "streamlit": ["streamlit"],
        "requests": ["requests"],
        "pandas": ["pandas"],
        "numpy": ["numpy"],
        "pytest": ["pytest"],
        "flask": ["flask"],
        "django": ["django"],
    }

    def __init__(self, name: str, bus, context: Dict):
        """
        🔥 Initialize Fixer agent (compatible with Arena)
        
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
        self.fix_history = []
        
        logger.info(f"[{self.name}] Initialized")

    def register(self) -> None:
        """Register event subscriptions"""
        self._log(LogLevel.INFO, "Subscribed → REVIEW_FAILED")
        self.bus.subscribe("REVIEW_FAILED", self.handle)

    async def handle(self, message):
        """Main handler for review failures"""
        
        message_type = (
            message.message_type 
            if hasattr(message, "message_type") 
            else message.get("message_type")
        )
        
        if message_type != "REVIEW_FAILED":
            return

        payload = (
            message.payload 
            if hasattr(message, "payload") 
            else message.get("payload", {})
        ) or {}
        
        files: Dict[str, str] = payload.get("files", {})
        issues: List[str] = payload.get("issues", [])
        attempts = payload.get("fix_attempts", 0)

        self._log(
            LogLevel.INFO,
            f"Attempt {attempts + 1} | Issues found: {len(issues)}",
            attempt=attempts + 1,
            issue_count=len(issues),
            file_count=len(files)
        )

        # 🛑 HARD STOP - Max attempts reached
        if attempts >= self.MAX_ATTEMPTS:
            self._log(
                LogLevel.WARNING,
                "Max attempts reached → forcing final result",
                max_attempts=self.MAX_ATTEMPTS
            )

            # Publish final message
            final_message = {
                "message_type": "CODE_FINAL",
                "sender": self.name,
                "recipient": "assembler",
                "payload": {
                    **payload,
                    "final_status": "failed_after_max_attempts"
                }
            }
            
            await self.bus.publish(final_message)
            self._record_metric("max_attempts_reached", 1, {"attempt": attempts + 1})
            return

        # Categorize issues for targeted fixes
        categorized_issues = self._categorize_issues(issues)
        self._log(LogLevel.DEBUG, "Issues categorized", categories=list(categorized_issues.keys()))

        fixed_files = {}
        issue_text = " ".join(issues).lower()
        files_with_errors = []

        for path, content in files.items():
            try:
                # Non-python files → handle separately
                if not path.endswith(".py"):
                    fixed_files[path] = self._handle_non_python_file(path, content, issues)
                    self._log(LogLevel.DEBUG, f"Fixed non-Python file", file=path)
                    continue

                updated = content

                # ─────────────────────────────
                # ⚡ FAST RULE FIXES (cheap + instant)
                # ─────────────────────────────
                if "st.button" in issue_text or "streamlit not used" in issue_text:
                    updated = self._inject_button_logic(updated)
                    self._log(LogLevel.DEBUG, "Applied button logic fix", file=path)

                if "__main__" in issue_text:
                    updated = self._remove_main_block(updated)
                    self._log(LogLevel.DEBUG, "Removed main block", file=path)

                updated = self._normalize_operations(updated)

                # ─────────────────────────────
                # 🧠 AI FIX (only when needed)
                # ─────────��───────────────────
                if self._needs_ai_fix(issue_text):
                    try:
                        self._log(LogLevel.INFO, f"🧠 AI fixing", file=path, attempt=attempts + 1)
                        updated = await self._llm_fix_with_retry(updated, issues)
                        
                        # Validate fix
                        if not self._validate_fix(content, updated, issues):
                            self._log(
                                LogLevel.WARNING,
                                "AI fix validation failed, reverting",
                                file=path
                            )
                            files_with_errors.append((path, "ai_fix_validation_failed"))
                        else:
                            self._log(LogLevel.DEBUG, "AI fix validated successfully", file=path)
                            
                    except Exception as e:
                        self._log(
                            LogLevel.ERROR,
                            f"AI fix failed: {str(e)}",
                            file=path,
                            error=str(e)
                        )
                        files_with_errors.append((path, f"ai_fix_error: {str(e)}"))

                fixed_files[path] = updated

            except Exception as e:
                self._log(
                    LogLevel.ERROR,
                    f"Unexpected error fixing {path}: {str(e)}",
                    file=path,
                    error=str(e)
                )
                fixed_files[path] = content  # Keep original on error
                files_with_errors.append((path, str(e)))

        # Record metrics
        self._record_metric("files_processed", len(files), {"attempt": attempts + 1})
        self._record_metric("files_with_errors", len(files_with_errors), {"attempt": attempts + 1})

        # 🚀 SEND BACK TO TESTER
        fixed_message = {
            "message_type": "CODE_FIXED",
            "sender": self.name,
            "recipient": "tester",
            "payload": {
                **payload,
                "files": fixed_files,
                "fix_attempts": attempts + 1,
                "files_with_errors": files_with_errors,
            }
        }
        
        await self.bus.publish(fixed_message)

        self._log(
            LogLevel.INFO,
            f"✅ Sent CODE_FIXED (attempt {attempts + 1})",
            attempt=attempts + 1,
            files_fixed=len(fixed_files)
        )

    # ─────────────────────────────
    # 🧠 ISSUE CATEGORIZATION
    # ─────────────────────────────
    def _categorize_issues(self, issues: List[str]) -> Dict[str, List[str]]:
        """Group issues by pattern for targeted fixes"""
        categorized = {pattern: [] for pattern in self.ISSUE_PATTERNS}
        
        for issue in issues:
            matched = False
            for pattern_name, regex in self.ISSUE_PATTERNS.items():
                if regex.search(issue):
                    categorized[pattern_name].append(issue)
                    matched = True
                    break
            
            if not matched:
                categorized["runtime_error"].append(issue)
        
        return categorized

    # ─────────────────────────────
    # 🧠 AI DECISION
    # ────────────────────────��────
    def _needs_ai_fix(self, issue_text: str) -> bool:
        """Decide when to use AI (avoid wasting tokens)"""
        triggers = [
            "error",
            "exception",
            "traceback",
            "syntax",
            "import",
            "module not found",
            "typeerror",
            "nameerror",
            "attributeerror",
            "runtime",
            "failed",
            "crash"
        ]
        return any(t in issue_text for t in triggers)

    # ─────────────────────────────
    # 🤖 LLM FIX ENGINE WITH RETRY
    # ─────────────────────────────
    async def _llm_fix_with_retry(self, code: str, issues: List[str]) -> str:
        """LLM fix with exponential backoff retry logic"""
        
        for attempt in range(self.LLM_MAX_RETRIES):
            try:
                engine = getattr(self.runtime, "engine", None) if self.runtime else None
                if not engine or not hasattr(engine, "llm"):
                    self._log(LogLevel.WARNING, "No LLM available, skipping AI fix")
                    return code

                prompt = f"""You are a senior Python debugger.

Fix the code based on the issues.

CODE:
{code}

ISSUES:
{issues}

RULES:
- Return ONLY valid Python code
- Do not explain anything
- Do not remove working logic
- Fix imports, syntax, runtime errors

OUTPUT:
"""

                response = await engine.llm.generate(prompt, temperature=0.1)
                cleaned = self._clean_code(response)
                
                self._record_metric(
                    "llm_fix_success",
                    1,
                    {"attempt": attempt + 1}
                )
                return cleaned

            except Exception as e:
                self._log(
                    LogLevel.WARNING,
                    f"LLM fix attempt {attempt + 1}/{self.LLM_MAX_RETRIES} failed: {str(e)}",
                    attempt=attempt + 1,
                    error=str(e)
                )
                
                if attempt < self.LLM_MAX_RETRIES - 1:
                    backoff_time = self.LLM_RETRY_BACKOFF ** attempt
                    self._log(LogLevel.DEBUG, f"Backing off for {backoff_time}s before retry")
                    await asyncio.sleep(backoff_time)
                else:
                    self._record_metric("llm_fix_failed", 1, {"max_retries": self.LLM_MAX_RETRIES})
                    return code

        return code

    # ─────────────────────────────
    # ✅ FIX VALIDATION
    # ──────────────────���──────────
    def _validate_fix(self, original: str, fixed: str, issues: List[str]) -> bool:
        """Validate if fix is actually better"""
        
        try:
            # Basic syntax check
            compile(fixed, '<string>', 'exec')
        except SyntaxError as e:
            self._log(LogLevel.WARNING, f"Fixed code has syntax error: {str(e)}")
            return False

        # Check that we didn't lose too much code
        original_lines = len([l for l in original.split("\n") if l.strip()])
        fixed_lines = len([l for l in fixed.split("\n") if l.strip()])
        
        if fixed_lines < original_lines * 0.3:
            self._log(
                LogLevel.WARNING,
                f"Fixed code lost too much content: {original_lines} → {fixed_lines} lines"
            )
            return False

        # Check that critical imports are preserved
        original_imports = set(re.findall(r"^import\s+(\w+)|^from\s+(\w+)", original, re.MULTILINE))
        fixed_imports = set(re.findall(r"^import\s+(\w+)|^from\s+(\w+)", fixed, re.MULTILINE))
        
        if original_imports and not fixed_imports:
            self._log(LogLevel.WARNING, "Fixed code lost all imports")
            return False

        self._log(LogLevel.DEBUG, "Fix validation passed")
        return True

    # ─────────────────────────────
    # 🧼 CLEAN LLM OUTPUT
    # ─────────────────────────────
    def _clean_code(self, text: str) -> str:
        """Remove markdown formatting from LLM output"""
        text = re.sub(r"```python|```", "", text)
        text = re.sub(r"^```.*?$", "", text, flags=re.MULTILINE)
        return text.strip()

    # ─────────────────────────────
    # 📦 NON-PYTHON FIXES
    # ─────────────────────────────
    def _handle_non_python_file(self, path: str, content: str, issues: List[str]) -> str:
        """Handle non-Python file fixes"""

        issue_text = " ".join(issues).lower()

        # Auto-fix requirements.txt
        if path == "requirements.txt":
            content = self._fix_requirements(content, issue_text, issues)

        # Auto-fix setup.py
        elif path == "setup.py":
            content = self._fix_setup_py(content, issue_text)

        # Auto-fix .env files
        elif path.endswith(".env"):
            content = self._fix_env_file(content, issue_text)

        return content

    def _fix_requirements(self, content: str, issue_text: str, issues: List[str]) -> str:
        """Fix requirements.txt by adding missing packages"""
        existing_packages = set(
            line.strip().split("==")[0].split(">=")[0].split("<=")[0].lower()
            for line in content.split("\n")
            if line.strip() and not line.startswith("#")
        )

        packages_to_add = set()

        # Map issues to required packages
        for package, keywords in self.PACKAGE_MAPPING.items():
            if any(kw in issue_text for kw in keywords):
                for pkg in keywords:
                    if pkg not in existing_packages:
                        packages_to_add.add(pkg)

        # Add detected packages
        if packages_to_add:
            content_lines = content.rstrip().split("\n")
            for pkg in sorted(packages_to_add):
                content_lines.append(pkg)
                self._log(LogLevel.DEBUG, f"Added {pkg} to requirements.txt")
            content = "\n".join(content_lines)

        return content.strip()

    def _fix_setup_py(self, content: str, issue_text: str) -> str:
        """Fix setup.py file"""
        # Ensure install_requires is present if dependencies are needed
        if "install_requires" not in content and any(kw in issue_text for kw in ["import", "module not found"]):
            content = content.replace(
                ")",
                """    install_requires=[],
)"""
            )
        return content

    def _fix_env_file(self, content: str, issue_text: str) -> str:
        """Fix .env files"""
        # Ensure common env vars are present
        required_vars = ["API_KEY", "DEBUG", "DATABASE_URL"]
        existing_vars = set(line.split("=")[0] for line in content.split("\n") if "=" in line)

        for var in required_vars:
            if var not in existing_vars:
                content += f"\n{var}=your_value_here"
                self._log(LogLevel.DEBUG, f"Added {var} to .env file")

        return content.strip()

    # ─────────────────────────────
    # 🔧 RULE FIXES
    # ─────────────────────────────
    def _inject_button_logic(self, code: str) -> str:
        """Inject Streamlit button logic if missing"""
        if "st.button" in code:
            return code

        return code.strip() + """

if st.button("Run"):
    st.write("Action triggered")
"""

    def _remove_main_block(self, code: str) -> str:
        """Remove if __name__ == '__main__' block"""
        lines = code.splitlines()
        cleaned = []
        skip = False

        for line in lines:
            if "if __name__" in line:
                skip = True
                continue
            if skip and line.strip() == "":
                continue
            if skip and not line.startswith(" "):
                skip = False
            if not skip:
                cleaned.append(line)

        return "\n".join(cleaned).strip()

    def _normalize_operations(self, code: str) -> str:
        """Normalize operation names"""
        return (
            code.replace("'Addition'", "'Add'")
                .replace("'Subtraction'", "'Subtract'")
                .replace("'Multiplication'", "'Multiply'")
                .replace("'Division'", "'Divide'")
        )

    # ─────────────────────────────
    # 📊 LOGGING & METRICS
    # ─────────────────────────────
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
        self.fix_history.append(log_entry)

    def _record_metric(self, metric_name: str, value: float, tags: Dict[str, str] = None):
        """Record metrics for monitoring"""
        self.metrics[metric_name] = {
            "value": value,
            "timestamp": datetime.utcnow().isoformat(),
            "tags": tags or {}
        }
        self._log(LogLevel.DEBUG, f"Metric recorded", metric=metric_name, value=value)

    def get_metrics(self) -> Dict:
        """Get all recorded metrics"""
        return self.metrics

    def get_history(self) -> List[Dict]:
        """Get all log history"""
        return self.fix_history

    # ─────────────────────────────
    # AGENT INTERFACE (for chain)
    # ─────────────────────────────
    async def run(self, task: Dict) -> Dict:
        """
        Run fixer as part of agent chain
        
        Args:
            task: Task containing code to fix
        
        Returns:
            Fixed code result
        """
        logger.info(f"[{self.name}] Running as chain agent")
        
        files = task.get("files", {})
        issues = task.get("issues", [])
        
        fixed_files = {}
        for path, content in files.items():
            if path.endswith(".py"):
                fixed = content
                
                # Apply quick fixes
                fixed = self._inject_button_logic(fixed)
                fixed = self._remove_main_block(fixed)
                fixed = self._normalize_operations(fixed)
                
                fixed_files[path] = fixed
            else:
                fixed_files[path] = content
        
        return {
            "message": "✅ Fixer complete",
            "updated_files": fixed_files,
            "mode": "fixer"
        }