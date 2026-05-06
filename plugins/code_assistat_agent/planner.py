# planner.py — Intelligent Planner (UPGRADED - Better inline detection)

import re
import logging
from typing import Dict, Any, List
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Classification of error types."""
    SYNTAX = "syntax"
    RUNTIME = "runtime"
    LOGIC = "logic"
    PERFORMANCE = "performance"
    SECURITY = "security"
    STYLE = "style"
    UNKNOWN = "unknown"


class PlannerAgent:
    def __init__(self, runtime=None):
        self.runtime = runtime or {}
        logger.info("PlannerAgent initialized")

    # ─────────────────────────────
    # ENTRY
    # ─────────────────────────────
    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        prompt = task.get("prompt", "")
        error_trace = task.get("error_trace", "")
        files = task.get("files", {}) or {}

        logger.info(f"[Planner] Planning: {prompt[:80]}")

        # 🔥 STEP 0: Check if we have inline code first
        has_inline_code = self._detect_inline_code(prompt, error_trace)
        
        if has_inline_code:
            logger.info("[Planner] Detected INLINE code - using <inline_code>")
            inferred_files = ["<inline_code>"]
            files_map = {"<inline_code>": prompt}
        else:
            # 🔥 STEP 1: Extract files mentioned
            inferred_files = self._extract_files(prompt)

            # 🔥 STEP 2: Extract code blocks
            code_blocks = self._extract_code_blocks(prompt)

            # 🔥 STEP 3: If code blocks exist → attach virtual files
            if code_blocks:
                logger.info(f"[Planner] Found {len(code_blocks)} code blocks")

                for i, code in enumerate(code_blocks):
                    filename = self._infer_filename_from_code(code, i)
                    files[filename] = code
                    inferred_files.append(filename)

            # 🔥 STEP 4: If still empty → infer default
            if not inferred_files:
                inferred_files = self._infer_default_files(prompt, ErrorType.UNKNOWN)

            files_map = files

        # 🔥 STEP 5: Remove duplicates
        inferred_files = list(set(inferred_files))

        if not inferred_files:
            inferred_files = ["<inline_code>"]
            logger.warning("[Planner] No files found, using fallback: <inline_code>")

        logger.info(f"[Planner] Files → {inferred_files}")

        # 🔥 STEP 6: Analyze error content
        error_type = self._classify_error(prompt, error_trace)
        error_details = self._extract_error_details(error_trace)

        # 🔥 STEP 7: Analyze code structure
        code_analysis = self._analyze_code_structure(
            self._extract_code_blocks(prompt), 
            error_trace
        )

        # 🔥 STEP 8: Generate detailed execution plan
        strategy = self._detect_strategy(prompt, error_type, code_analysis)
        execution_steps = self._generate_execution_steps(strategy, error_type, code_analysis)
        priority = self._assess_priority(error_type, error_details)

        return {
            "status": "success",
            "files_to_modify": inferred_files,  # ✅ CRITICAL KEY
            "files": inferred_files,  # Backward compatibility
            "files_map": files_map,
            "strategy": strategy,
            "priority": priority,
            "execution_steps": execution_steps,
            "error_type": error_type.value,
            "error_details": error_details,
            "code_analysis": code_analysis,
            "steps": execution_steps  # Backward compatibility
        }

    # ─────────────────────────────
    # INLINE CODE DETECTION (NEW)
    # ─────────────────────────────
    def _detect_inline_code(self, prompt: str, error_trace: str) -> bool:
        """
        Detect if code is provided inline in prompt.
        
        Returns:
            True if inline code detected
        """
        combined = f"{prompt} {error_trace}"
        
        # Code indicators
        code_patterns = [
            r"def\s+\w+\s*\(",  # Python function definition
            r"class\s+\w+\s*:",  # Python class definition
            r"function\s+\w+\s*\{",  # JavaScript function
            r"const\s+\w+\s*=",  # JavaScript const
            r"async\s+def\s+",  # Python async function
            r"def\s+\w+.*:\n\s+",  # Python function with body
        ]
        
        has_code_pattern = any(re.search(pattern, combined) for pattern in code_patterns)
        
        if has_code_pattern:
            logger.info("[Planner] Found code pattern indicators")
            return True
        
        # Check for code blocks
        if "```" in prompt or ">>>>" in prompt:
            logger.info("[Planner] Found code block markers")
            return True
        
        # Check for common code keywords
        code_keywords = ["import ", "return ", "if ", "for ", "while ", "try:"]
        has_code_keywords = any(keyword in combined for keyword in code_keywords)
        
        if has_code_keywords and len(prompt) > 50:
            logger.info("[Planner] Found code keywords")
            return True
        
        return False

    # ─────────────────────────────
    # ERROR CLASSIFICATION
    # ─────────────────────────────
    def _classify_error(self, prompt: str, error_trace: str) -> ErrorType:
        """Classify the type of error."""
        combined = f"{prompt} {error_trace}".lower()

        syntax_keywords = ["syntax", "indent", "unexpected", "≤", "none", "invalid", "colon", "quote"]
        if any(k in combined for k in syntax_keywords):
            logger.info("[Planner] Classified as SYNTAX error")
            return ErrorType.SYNTAX

        runtime_keywords = ["traceback", "error:", "exception", "attributeerror", "typeerror", "keyerror"]
        if any(k in combined for k in runtime_keywords):
            logger.info("[Planner] Classified as RUNTIME error")
            return ErrorType.RUNTIME

        logic_keywords = ["wrong output", "incorrect", "logic", "algorithm"]
        if any(k in combined for k in logic_keywords):
            logger.info("[Planner] Classified as LOGIC error")
            return ErrorType.LOGIC

        perf_keywords = ["slow", "performance", "optimize", "memory"]
        if any(k in combined for k in perf_keywords):
            logger.info("[Planner] Classified as PERFORMANCE issue")
            return ErrorType.PERFORMANCE

        security_keywords = ["security", "vulnerability", "inject", "xss"]
        if any(k in combined for k in security_keywords):
            logger.info("[Planner] Classified as SECURITY issue")
            return ErrorType.SECURITY

        style_keywords = ["format", "style", "lint", "pep8"]
        if any(k in combined for k in style_keywords):
            logger.info("[Planner] Classified as STYLE issue")
            return ErrorType.STYLE

        logger.info("[Planner] Classified as UNKNOWN")
        return ErrorType.UNKNOWN

    def _extract_error_details(self, error_trace: str) -> Dict[str, Any]:
        """Extract detailed error information."""
        details = {
            "line_number": None,
            "error_message": "",
            "affected_variables": [],
            "stack_depth": 0
        }

        line_match = re.search(r'line (\d+)', error_trace, re.IGNORECASE)
        if line_match:
            details["line_number"] = int(line_match.group(1))

        msg_match = re.search(r'(?:Error|Exception):\s*(.+?)(?:\n|$)', error_trace)
        if msg_match:
            details["error_message"] = msg_match.group(1).strip()

        var_matches = re.findall(r'\b([a-zA-Z_]\w*)\b', error_trace)
        details["affected_variables"] = list(set(var_matches))[:10]

        details["stack_depth"] = len(re.findall(r'File ".+"', error_trace))

        return details

    # ─────────────────────────────
    # FILE EXTRACTION
    # ─────────────────────────────
    def _extract_files(self, prompt: str) -> List[str]:
        """Extract file paths from prompt."""
        pattern = r"\b[\w\-]+\.(?:py|js|ts|jsx|tsx|html|css|json|java|cpp|go|rs|rb|php)\b"
        files = re.findall(pattern, prompt)
        logger.debug(f"[Planner] Extracted files: {files}")
        return files

    # ─────────────────────────────
    # CODE BLOCK EXTRACTION
    # ─────────────────────────────
    def _extract_code_blocks(self, prompt: str) -> List[str]:
        """Extract code blocks from prompt."""
        blocks = []

        # Markdown ``` blocks
        matches = re.findall(r"```(?:\w+)?\n(.*?)```", prompt, re.DOTALL)
        blocks.extend(matches)
        logger.debug(f"[Planner] Found {len(matches)} markdown code blocks")

        # Indented code blocks
        indented = re.findall(r"^    +(.+)$", prompt, re.MULTILINE)
        if indented:
            blocks.append("\n".join(indented))
            logger.debug("[Planner] Found indented code block")

        # Inline Python-like detection
        if "def " in prompt or "function" in prompt or "class " in prompt:
            blocks.append(prompt)
            logger.debug("[Planner] Found inline function/class definition")

        return [b.strip() for b in blocks if b.strip() and len(b) > 20]

    # ─────────────────────────────
    # CODE STRUCTURE ANALYSIS
    # ─────────────────────────────
    def _analyze_code_structure(self, code_blocks: List[str], error_trace: str) -> Dict[str, Any]:
        """Analyze code structure and characteristics."""
        analysis = {
            "languages": set(),
            "has_functions": False,
            "has_classes": False,
            "has_imports": False,
            "complexity": "low",
            "estimated_lines": 0,
            "keywords_found": []
        }

        combined_code = "\n".join(code_blocks)

        if "import " in combined_code or "from " in combined_code:
            analysis["languages"].add("python")
        if "function " in combined_code or "=>" in combined_code:
            analysis["languages"].add("javascript")
        if "const " in combined_code or "let " in combined_code:
            analysis["languages"].add("typescript")

        analysis["has_functions"] = bool(re.search(r'\b(def|function)\s+\w+', combined_code))
        analysis["has_classes"] = bool(re.search(r'\b(class|interface)\s+\w+', combined_code))
        analysis["has_imports"] = bool(re.search(r'\b(import|require|from)\s+', combined_code))

        num_lines = len(combined_code.split('\n'))
        num_loops = len(re.findall(r'\b(for|while)\b', combined_code))
        num_conditionals = len(re.findall(r'\b(if|else|elif)\b', combined_code))

        analysis["estimated_lines"] = num_lines
        complexity_score = num_lines + (num_loops * 2) + (num_conditionals * 1.5)
        if complexity_score > 50:
            analysis["complexity"] = "high"
        elif complexity_score > 20:
            analysis["complexity"] = "medium"
        else:
            analysis["complexity"] = "low"

        analysis["keywords_found"] = self._extract_keywords(combined_code, error_trace)
        analysis["languages"] = list(analysis["languages"])

        logger.debug(f"[Planner] Code analysis: {analysis}")
        return analysis

    def _extract_keywords(self, code: str, error_trace: str) -> List[str]:
        """Extract important keywords from code and error."""
        keywords = set()

        code_keywords = re.findall(r'\b(def|class|for|while|if|else|try|except|import|return|yield)\b', code)
        keywords.update(code_keywords)

        error_keywords = re.findall(r'\b(None|TypeError|ValueError|KeyError|Index|Syntax|Import|Name)\b', error_trace)
        keywords.update(error_keywords)

        return list(keywords)[:15]

    # ─────────────────────────────
    # FILENAME INFERENCE
    # ─────────────────────────────
    def _infer_filename_from_code(self, code: str, index: int) -> str:
        """Infer filename from code content."""
        code_lower = code.lower()

        func_match = re.search(r'def\s+(\w+)', code)
        if func_match:
            return f"{func_match.group(1)}.py"

        class_match = re.search(r'class\s+(\w+)', code)
        if class_match:
            return f"{class_match.group(1)}.py"

        if "import " in code or "def " in code:
            return f"module_{index}.py"
        if "function" in code or "=>" in code or "const " in code:
            return f"app_{index}.js"
        if "<div" in code or "DOCTYPE" in code:
            return f"component_{index}.html"

        return f"file_{index}.py"

    # ─────────────────────────────
    # DEFAULT FILE INFERENCE
    # ─────────────────────────────
    def _infer_default_files(self, prompt: str, error_type: ErrorType) -> List[str]:
        """Infer default files based on context."""
        p = prompt.lower()

        if "react" in p or "jsx" in p:
            return ["App.jsx"]
        if "django" in p or "flask" in p:
            return ["app.py"]
        if "fastapi" in p:
            return ["main.py"]
        if "nodejs" in p or "express" in p:
            return ["server.js"]

        if "api" in p:
            return ["api.py"]
        if "html" in p:
            return ["index.html"]
        if "css" in p:
            return ["styles.css"]

        if error_type == ErrorType.SYNTAX:
            return ["<inline_code>"]
        if error_type == ErrorType.LOGIC:
            return ["algorithm.py"]

        return ["<inline_code>"]

    # ─────────────────────────────
    # STRATEGY DETECTION
    # ─────────────────────────────
    def _detect_strategy(self, prompt: str, error_type: ErrorType, analysis: Dict[str, Any]) -> str:
        """Detect optimal fix strategy."""
        p = prompt.lower()

        if error_type == ErrorType.SYNTAX:
            logger.info("[Planner] Strategy: pattern_based (syntax)")
            return "pattern_based"

        if error_type == ErrorType.RUNTIME:
            logger.info("[Planner] Strategy: llm_based (runtime)")
            return "llm_based"

        if error_type == ErrorType.LOGIC:
            logger.info("[Planner] Strategy: test_driven")
            return "test_driven"

        if error_type == ErrorType.PERFORMANCE:
            logger.info("[Planner] Strategy: optimization")
            return "optimization"

        if error_type == ErrorType.SECURITY:
            logger.info("[Planner] Strategy: security_fix")
            return "security_fix"

        if "test" in p or "unit" in p:
            return "test_driven"
        if "optimize" in p or "performance" in p:
            return "optimization"
        if "refactor" in p or "clean" in p:
            return "refactor"

        logger.info("[Planner] Strategy: llm_based (default)")
        return "llm_based"

    # ─────────────────────────────
    # EXECUTION STEPS GENERATION
    # ─────────────────────────────
    def _generate_execution_steps(self, strategy: str, error_type: ErrorType, analysis: Dict[str, Any]) -> List[str]:
        """Generate detailed execution steps."""
        steps = ["analyze"]

        if strategy == "pattern_based":
            steps.extend(["detect_pattern", "apply_fix", "validate"])
        elif strategy == "llm_based":
            steps.extend(["understand_context", "generate_fix", "validate"])
        elif strategy == "test_driven":
            steps.extend(["write_tests", "implement_fix", "run_tests"])
        elif strategy == "optimization":
            steps.extend(["profile", "identify_bottleneck", "optimize"])
        elif strategy == "security_fix":
            steps.extend(["audit", "identify_vulnerability", "patch"])
        elif strategy == "refactor":
            steps.extend(["review_structure", "refactor", "test"])

        steps.extend(["test", "review"])

        return steps

    # ─────────────────────────────
    # PRIORITY ASSESSMENT
    # ─────────────────────────────
    def _assess_priority(self, error_type: ErrorType, error_details: Dict[str, Any]) -> str:
        """Assess priority level."""
        if error_type == ErrorType.SECURITY:
            return "critical"
        if error_type == ErrorType.RUNTIME:
            return "high"
        if error_type == ErrorType.SYNTAX:
            return "high"
        if error_type == ErrorType.LOGIC:
            return "medium"
        if error_type == ErrorType.PERFORMANCE:
            return "medium"
        if error_type == ErrorType.STYLE:
            return "low"

        return "medium"