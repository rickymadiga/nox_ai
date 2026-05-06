# agent.py — v5 CODE ASSISTANT (Debugger → Fixer → Reviewer + Full Chain Support 🔥)

from typing import Dict, Any, Optional
import json
import re
import difflib
import logging

logger = logging.getLogger(__name__)


class CodeAssistantAgent:
    """
    🔥 Code Assistant Agent - Handles debugging, fixing, and reviewing code
    Full integration with engine and proper response forwarding
    """
    
    def __init__(self, runtime):
        self.runtime = runtime
        self.name = "code_assistant"
        logger.info(f"[{self.name.upper()}] Initialized")

    # ─────────────────────────────────────────────
    # ENTRY (ENGINE COMPATIBLE) 🔥
    # ─────────────────────────────────────────────
    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        🔥 Main entry point compatible with engine chain
        
        Args:
            task: Contains prompt, user_id, context, previous_result, chain_history
        
        Returns:
            Formatted response for engine with fixed code
        """
        try:
            prompt = task.get("prompt", "")
            user_id = task.get("user_id", "default_user")
            context = task.get("context", {}) or {}
            
            # 🔥 Get previous results from chain
            previous_result = task.get("previous_result", {})
            chain_history = task.get("chain_history", {})
            
            logger.info(f"[{self.name.upper()}] Processing for {user_id}: {prompt[:50]}...")
            
            # Core processing
            result = await self.handle(prompt, user_id, context, previous_result, chain_history)

            # 🔥 CRITICAL: Return in engine-compatible format
            return {
                "type": "code_result",
                "message": result.get("message", "✅ Code analysis complete"),
                "mode": result.get("mode"),
                "updated_files": result.get("updated_files", {}),  # 🔥 FIXED CODE
                "diffs": result.get("diffs", {}),  # 🔥 BEFORE/AFTER
                "structured": result.get("structured"),
                "analysis": result.get("analysis"),
                "root_cause": result.get("root_cause"),
                "summary": result.get("summary"),
                "agent": self.name,
                "error": result.get("error")
            }
        
        except Exception as e:
            logger.error(f"[{self.name.upper()}] Fatal error: {e}", exc_info=True)
            return {
                "type": "code_result",
                "message": f"❌ Error: {str(e)}",
                "mode": "error",
                "updated_files": {},
                "diffs": {},
                "error": str(e)
            }

    # ─────────────────────────────────────────────
    # CONTEXT BUILDER
    # ─────────────────────────────────────────────
    def _build_project_context(self, user_id: str, max_files: int = 10) -> str:
        """
        Build project context from runtime
        
        Args:
            user_id: User identifier
            max_files: Max files to include
        
        Returns:
            Formatted project context string
        """
        try:
            # Try to get from runtime.projects
            projects = getattr(self.runtime, "projects", {})
            project = projects.get(user_id, {})

            if not project or not project.get("files"):
                logger.debug(f"[{self.name.upper()}] No active project for {user_id}")
                return "No active project loaded."

            files = project["files"]
            context = "=== PROJECT SNAPSHOT ===\n\n"

            for i, path in enumerate(sorted(files.keys())):
                if i >= max_files:
                    context += f"\n... and {len(files) - max_files} more files"
                    break

                content = files[path]
                if len(content) > 5000:
                    content = content[:5000] + "\n...[TRUNCATED]"

                context += f"\n--- {path} ---\n{content}\n"

            logger.debug(f"[{self.name.upper()}] Built context with {min(len(files), max_files)} files")
            return context
        
        except Exception as e:
            logger.error(f"[{self.name.upper()}] Context build error: {e}")
            return "Error loading project context."

    # ─────────────────────────────────────────────
    # MODE DETECTION (CHAIN-AWARE)
    # ─────────────────────────────────────────────
    def _detect_mode(self, prompt: str, context: Optional[Dict] = None) -> str:
        """
        Detect operation mode from prompt and context
        
        Args:
            prompt: User prompt
            context: Task context
        
        Returns:
            Mode: "debugger", "fixer", "reviewer", or "general"
        """
        # 🔥 Check for mode override from chain
        if context and context.get("mode_override"):
            logger.info(f"[{self.name.upper()}] Using chain override: {context['mode_override']}")
            return context["mode_override"]

        p = prompt.lower()

        # Priority order: debugger > fixer > reviewer > general
        if any(k in p for k in ["fix", "bug", "error", "broken", "debug", "crash", "issue"]):
            logger.info(f"[{self.name.upper()}] Mode → debugger")
            return "debugger"

        if any(k in p for k in ["improve", "refactor", "optimize", "clean", "enhance"]):
            logger.info(f"[{self.name.upper()}] Mode → fixer")
            return "fixer"

        if any(k in p for k in ["review", "audit", "check", "inspect"]):
            logger.info(f"[{self.name.upper()}] Mode → reviewer")
            return "reviewer"

        logger.info(f"[{self.name.upper()}] Mode → general")
        return "general"

    # ─────────────────────────────────────────────
    # DIFF GENERATION 🔥 (CRITICAL)
    # ─────────────────────────────────────────────
    def _generate_diff(self, old: str, new: str, filename: str = "code.py") -> str:
        """
        Generate unified diff between old and new code
        
        Args:
            old: Original code
            new: Updated code
            filename: File name for diff header
        
        Returns:
            Unified diff string
        """
        try:
            old_lines = old.splitlines(keepends=True)
            new_lines = new.splitlines(keepends=True)

            diff_lines = difflib.unified_diff(
                old_lines,
                new_lines,
                fromfile=f"{filename} (original)",
                tofile=f"{filename} (fixed)",
                lineterm=""
            )

            diff_text = "".join(diff_lines)
            logger.debug(f"[{self.name.upper()}] Generated diff for {filename} ({len(diff_text)} bytes)")
            return diff_text
        
        except Exception as e:
            logger.error(f"[{self.name.upper()}] Diff generation error: {e}")
            return f"Error generating diff: {str(e)}"

    # ─────────────────────────────────────────────
    # MOCK LLM (for testing without real API)
    # ─────────────────────────────────────────────
    async def _generate_fixes(self, prompt: str, mode: str, context: str) -> str:
        """
        Generate fixes using LLM or fallback mock
        
        Args:
            prompt: User prompt
            mode: Operation mode
            context: Project context
        
        Returns:
            LLM response
        """
        engine = getattr(self.runtime, "engine", None)
        
        # 🔥 Try real LLM first
        if engine and hasattr(engine, "llm") and engine.llm:
            try:
                logger.info(f"[{self.name.upper()}] Using real LLM")
                result = await engine.llm.generate(prompt, temperature=0.2)
                return result
            except Exception as e:
                logger.warning(f"[{self.name.upper()}] LLM error: {e}, using mock")
        
        # 🔥 Fallback to mock for demo
        logger.info(f"[{self.name.upper()}] Using mock LLM (no real API)")
        return self._generate_mock_response(mode)

    def _generate_mock_response(self, mode: str) -> str:
            """
            Generate mock response for testing
        
            Args:
            mode: Operation mode
        
            Returns:
            Mock JSON response
            """
            if mode == "debugger":
                return json.dumps({
                "analysis": "Found missing error handling and potential null reference",
                "root_cause": "The function does not validate input parameters before use",
                "files_affected": ["main.py"],
                "recommendations": ["Add input validation", "Add try-catch blocks"]
            })
        
            elif mode == "fixer":
                # 🔥 More realistic fixer response
                return json.dumps({
                "analysis": "Fixed error handling, added input validation, and improved robustness",
                "fixed_files": {
                    "main.py": '''def process_data(data):
    """Process data with proper error handling and validation"""
    
    # Input validation
    if not data:
        raise ValueError("Data cannot be empty")
    
    if not isinstance(data, (list, dict)):
        raise TypeError(f"Expected list or dict, got {type(data).__name__}")
    
    try:
        result = {}
        
        if isinstance(data, dict):
            for key, value in data.items():
                if value is not None:
                    result[key] = value
        else:
            for i, item in enumerate(data):
                if item is None:
                    continue
                if not isinstance(item, dict):
                    raise TypeError(f"List item {i} is not a dict")
                
                required_keys = {"id", "value"}
                if not required_keys.issubset(item.keys()):
                    raise KeyError(f"Item {i} missing required keys: {required_keys}")
                
                result[item["id"]] = item["value"]
        
        return result
    
            except KeyError as e:
            raise ValueError(f"Missing required field: {e}")
            except TypeError as e:
            raise ValueError(f"Type error: {e}")
            except Exception as e:
            raise RuntimeError(f"Processing error: {str(e)}")
            '''
                },
                "summary": "Added comprehensive input validation, type checking, and improved error handling"
            })
        
            else:
                return json.dumps({
                "analysis": "Code review complete",
                "issues": ["No critical issues found"],
                "suggestions": ["Consider adding docstrings"]
            })

    # ─────────────────────────────────────────────
    # CORE ENGINE 🔥
    # ─────────────────────────────────────────────
    async def handle(
        self,
        prompt: str,
        user_id: str = "default_user",
        context: Optional[Dict] = None,
        previous_result: Optional[Dict] = None,
        chain_history: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        🔥 Core processing logic
        
        Args:
            prompt: User prompt
            user_id: User identifier
            context: Task context (may have mode_override)
            previous_result: Result from previous chain step (e.g., debugger output)
            chain_history: Full chain history
        
        Returns:
            Complete result with fixed code and diffs
        """
        try:
            context = context or {}
            
            logger.info(f"[{self.name.upper()}] Starting analysis for {user_id}")

            # 🔥 Build project context
            project_context = self._build_project_context(user_id)
            
            # 🔥 Detect mode (check context first for overrides)
            mode = self._detect_mode(prompt, context)
            
            logger.info(f"[{self.name.upper()}] Mode: {mode}")

            # ─────────────────────────────
            # BUILD SYSTEM PROMPT
            # ─────────────────────────────
            if mode == "debugger":
                system = """You are a senior debugging engine. Analyze the code and identify issues.

Return JSON with this exact structure:
{
  "analysis": "detailed analysis of issues found",
  "root_cause": "what caused the issue",
  "files_affected": ["file.py"],
  "recommendations": ["fix 1", "fix 2"]
}"""

            elif mode == "fixer":
                # 🔥 If we have debugger output, use it in the prompt
                if previous_result and previous_result.get("analysis"):
                    system = f"""You are a senior software engineer. Fix the issues found in the code analysis.

ANALYSIS RESULT:
{previous_result.get("analysis")}

ROOT CAUSE:
{previous_result.get("root_cause")}

RECOMMENDATIONS:
{previous_result.get("recommendations", [])}

Return JSON with this exact structure:
{{
  "analysis": "what was fixed",
  "fixed_files": {{
    "filename.py": "COMPLETE CORRECTED CODE HERE"
  }},
  "summary": "summary of changes"
}}

IMPORTANT: Always provide COMPLETE file content, not snippets!"""
                else:
                    system = """You are a senior software engineer. Fix ALL issues in the code.

Return JSON with this exact structure:
{
  "analysis": "what was fixed",
  "fixed_files": {
    "filename.py": "COMPLETE CORRECTED CODE HERE",
    "other.py": "COMPLETE CORRECTED CODE HERE"
  },
  "summary": "summary of changes"
}

IMPORTANT: Always provide COMPLETE file content, not snippets!"""

            elif mode == "reviewer":
                system = """You are a strict code reviewer. Review the code quality.

Return JSON with this exact structure:
{
  "analysis": "overall assessment",
  "issues": ["issue 1", "issue 2"],
  "risks": ["potential risk 1"],
  "suggestions": ["improvement 1"]
}"""

            else:
                system = "You are a helpful coding assistant. Provide helpful responses."

            full_prompt = f"""{system}

PROJECT CONTEXT:
{project_context}

USER REQUEST:
{prompt}"""

            logger.debug(f"[{self.name.upper()}] Full prompt length: {len(full_prompt)}")

            # ─────────────────────────────
            # GET LLM RESPONSE
            # ─────────────────────────────
            llm_response = await self._generate_fixes(full_prompt, mode, project_context)
            logger.info(f"[{self.name.upper()}] Received LLM response ({len(llm_response)} chars)")

            # ─────────────────────────────
            # PARSE JSON RESPONSE
            # ─────────────────────────────
            parsed = None
            updated_files = {}
            diffs = {}
            analysis = ""
            root_cause = ""
            summary = ""

            try:
                # Extract JSON from markdown code blocks
                match = re.search(r"```json(.*?)```", llm_response, re.DOTALL)
                json_str = match.group(1).strip() if match else llm_response.strip()
                
                parsed = json.loads(json_str)
                logger.info(f"[{self.name.upper()}] Successfully parsed JSON response")
                
            except json.JSONDecodeError as e:
                logger.warning(f"[{self.name.upper()}] JSON parse error: {e}")
                try:
                    parsed = json.loads(llm_response.strip())
                except:
                    parsed = None
            except Exception as e:
                logger.error(f"[{self.name.upper()}] Parse error: {e}")
                parsed = None

            # ─────────────────────────────
            # EXTRACT AND APPLY FIXES 🔥
            # ─────────────────────────────
            if parsed and isinstance(parsed, dict):
                # Extract metadata
                analysis = parsed.get("analysis", "")
                root_cause = parsed.get("root_cause", "")
                summary = parsed.get("summary", "")

                # Get fixed files
                fixed_files = parsed.get("fixed_files", {})
                logger.info(f"[{self.name.upper()}] Found {len(fixed_files)} fixed files")

                if fixed_files and isinstance(fixed_files, dict):
                    # Get existing files from project
                    projects = getattr(self.runtime, "projects", {})
                    project = projects.get(user_id, {})
                    existing_files = project.get("files", {}) if project else {}

                    # 🔥 GENERATE DIFFS AND STORE FIXED CODE
                    for filepath, new_code in fixed_files.items():
                        if not isinstance(new_code, str):
                            logger.warning(f"[{self.name.upper()}] Invalid code type for {filepath}")
                            continue
                        
                        old_code = existing_files.get(filepath, "")
                        
                        # Generate unified diff
                        diff = self._generate_diff(old_code, new_code, filepath)
                        diffs[filepath] = diff
                        
                        # Store fixed code for frontend
                        updated_files[filepath] = new_code
                        
                        logger.info(f"[{self.name.upper()}] Fixed: {filepath} ({len(new_code)} chars)")
                        
                        # Apply change to runtime if project exists
                        if user_id in projects and projects[user_id].get("files"):
                            projects[user_id]["files"][filepath] = new_code
                            logger.info(f"[{self.name.upper()}] Updated runtime: {filepath}")

            # ─────────────────────────────
            # RETURN COMPLETE RESULT 🔥
            # ─────────────────────────────
            result = {
                "mode": mode,
                "message": f"✅ {mode.capitalize()} complete - {len(updated_files)} files updated",
                "response": summary or analysis or root_cause or "Done",
                "structured": parsed,
                "updated_files": updated_files,  # 🔥 FIXED CODE
                "diffs": diffs,  # 🔥 BEFORE/AFTER DIFFS
                "analysis": analysis,
                "root_cause": root_cause,
                "summary": summary
            }

            logger.info(f"[{self.name.upper()}] Processing complete: {result['message']}")
            return result

        except Exception as e:
            logger.error(f"[{self.name.upper()}] Handle error: {e}", exc_info=True)
            return {
                "mode": "error",
                "message": f"❌ Error: {str(e)}",
                "error": str(e),
                "updated_files": {},
                "diffs": {}
            }