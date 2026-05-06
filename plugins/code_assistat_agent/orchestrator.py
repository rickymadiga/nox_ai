# orchestrator.py - Complete execution pipeline (FIXED - Thread-based Sync)
import asyncio
import logging
import json
import uuid
import subprocess
import re
import ast
import threading
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class ExecutionStatus(Enum):
    """Orchestrator stage statuses."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    APPROVED = "approved"
    REJECTED = "rejected"
    DEPLOYED = "deployed"


@dataclass
class ExecutionLog:
    """Track execution progress."""
    timestamp: str
    stage: str
    status: str
    message: str
    details: Dict[str, Any]


class AICodeFixingOrchestrator:
    """
    End-to-end orchestrator for AI-powered code fixing.
    Implements the complete pipeline: Analyze → Plan → Fix → Test → Review → Deploy
    """

    def __init__(self, 
                 planner_agent,
                 fixer_agent, 
                 test_agent: Optional['TestExecutionAgent'] = None,
                 review_agent: Optional['CodeReviewAgent'] = None,
                 runtime: Optional[Dict[str, Any]] = None):
        """
        Initialize the orchestrator with required agents.
        """
        self.planner = planner_agent
        self.fixer = fixer_agent
        self.test_agent = test_agent
        self.review = review_agent
        self.runtime = runtime or {}
        
        # State tracking
        self.execution_logs: List[ExecutionLog] = []
        self.current_status = ExecutionStatus.PENDING
        logger.info("AICodeFixingOrchestrator initialized")

    def _is_event_loop_running(self) -> bool:
        """Check if an event loop is already running."""
        try:
            asyncio.get_running_loop()
            return True
        except RuntimeError:
            return False

    def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synchronous entry point for the orchestrator.
        Handles both running and non-running event loops.
        
        Args:
            task: {"prompt": str, "error_trace": str, "context": str}
        
        Returns:
            Execution result
        """
        if not task:
            logger.error("Task is None or empty")
            return {
                "status": "failed",
                "error": "Task is required",
                "execution_log": []
            }
        
        try:
            # Build context from task
            context = {
                "prompt": task.get("prompt", ""),
                "error_trace": task.get("error_trace", ""),
                "context": task.get("context", ""),
                "files": task.get("files", {})
            }
            
            logger.info(f"Starting orchestrator.run() with task: {task.get('prompt', '')[:50]}")
            
            # 🔥 CHECK IF EVENT LOOP IS ALREADY RUNNING
            if self._is_event_loop_running():
                logger.info("Event loop is already running - using thread executor")
                # Engine is async - run in separate thread
                return self._run_in_thread(task, context)
            else:
                # Event loop is not running - use normal asyncio.run()
                logger.info("Event loop is not running - using asyncio.run()")
                result = asyncio.run(
                    self.execute_fix(task, context)
                )
                logger.info(f"Orchestrator.run() completed with status: {result.get('status')}")
                return result
            
        except Exception as e:
            logger.error(f"Orchestrator.run() failed: {str(e)}", exc_info=True)
            return {
                "status": "failed",
                "error": str(e),
                "execution_log": []
            }

    def _run_in_thread(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the pipeline in a separate thread to avoid event loop conflicts.
        
        Args:
            task: Task to execute
            context: Context for execution
        
        Returns:
            Execution result
        """
        result_container = {}
        exception_container = {}
        
        def run_in_new_thread():
            try:
                # This runs in a completely separate thread with its own event loop
                result = asyncio.run(
                    self.execute_fix(task, context)
                )
                result_container['result'] = result
            except Exception as e:
                logger.error(f"Error in thread: {str(e)}", exc_info=True)
                exception_container['exception'] = e
        
        # Create and run thread
        thread = threading.Thread(target=run_in_new_thread, daemon=False)
        thread.start()
        thread.join(timeout=300)  # 5 minute timeout
        
        # Check results
        if exception_container:
            exc = exception_container['exception']
            logger.error(f"Thread execution failed: {exc}")
            return {
                "status": "failed",
                "error": str(exc),
                "execution_log": []
            }
        
        if thread.is_alive():
            logger.error("Thread execution timed out")
            return {
                "status": "failed",
                "error": "Execution timeout (exceeded 5 minutes)",
                "execution_log": []
            }
        
        return result_container.get('result', {
            "status": "failed",
            "error": "Unknown error in thread execution",
            "execution_log": []
        })

    async def run_async(self, task: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Async entry point for running the orchestrator.
        Use this for direct async calls.
        
        Args:
            task: Task dictionary
            context: Optional context dictionary
        
        Returns:
            Execution result
        """
        if context is None:
            context = {
                "prompt": task.get("prompt", ""),
                "error_trace": task.get("error_trace", ""),
                "context": task.get("context", ""),
                "files": task.get("files", {})
            }
        
        return await self.execute_fix(task, context)

    async def execute_fix(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute complete fixing pipeline (async).
        """
        execution_id = self._generate_execution_id()
        logger.info(f"[{execution_id}] Starting fix execution")
        
        try:
            # Stage 1: PLANNING
            self._log_stage("PLANNING", ExecutionStatus.IN_PROGRESS, "Analyzing task and creating plan")
            plan = await self._execute_planning(task, context)
            
            if not plan.get("files_to_modify"):
                self._log_stage("PLANNING", ExecutionStatus.FAILED, "Planner failed to identify files")
                raise ValueError("Planner failed to identify files to modify")
            
            self._log_stage("PLANNING", ExecutionStatus.SUCCESS, "Plan created successfully")
            
            # Stage 2: FIXING
            self._log_stage("FIXING", ExecutionStatus.IN_PROGRESS, "Generating code fixes")
            fixes = await self._execute_fixing(plan, context)
            
            if not fixes or not fixes.get("fixes"):
                self._log_stage("FIXING", ExecutionStatus.FAILED, "Fixer generated no fixes")
                raise ValueError("Fixer failed to generate fixes")
            
            self._log_stage("FIXING", ExecutionStatus.SUCCESS, "Fixes generated successfully")
            
            # Stage 3: TESTING
            self._log_stage("TESTING", ExecutionStatus.IN_PROGRESS, "Running tests on fixes")
            test_results = await self._execute_testing(fixes, context)
            
            # Stage 4: REVIEW
            self._log_stage("REVIEWING", ExecutionStatus.IN_PROGRESS, "Performing code review")
            review_results = await self._execute_review(fixes, test_results, context)
            
            # Determine final status
            tests_passed = test_results.get("all_passed", False)
            review_approved = review_results.get("approved", False)
            
            if review_approved and tests_passed:
                final_status = ExecutionStatus.APPROVED
                self._log_stage("APPROVAL", ExecutionStatus.APPROVED, "All stages passed - ready to deploy")
            else:
                final_status = ExecutionStatus.REJECTED
                reasons = []
                if not tests_passed:
                    reasons.append("tests failed")
                if not review_approved:
                    reasons.append("review rejected")
                self._log_stage("APPROVAL", ExecutionStatus.REJECTED, f"Rejected: {', '.join(reasons)}")
            
            # Stage 5: DEPLOYMENT (if approved)
            deploy_result = None
            if final_status == ExecutionStatus.APPROVED:
                self._log_stage("DEPLOYMENT", ExecutionStatus.IN_PROGRESS, "Applying fixes to codebase")
                deploy_result = await self._execute_deployment(fixes, context)
                self._log_stage("DEPLOYMENT", ExecutionStatus.SUCCESS, "Fixes deployed")
            else:
                deploy_result = {"deployed": False, "reason": "Not approved"}
            
            # Compile final result
            result = {
                "execution_id": execution_id,
                "status": final_status.value,
                "timestamp": datetime.utcnow().isoformat(),
                "plan": plan,
                "fixes": [self._serialize_fix(f) for f in fixes.get("fixes", [])],
                "test_results": test_results,
                "review_results": review_results,
                "deployment": deploy_result,
                "execution_log": [self._serialize_log(log) for log in self.execution_logs],
                "summary": self._create_summary(fixes, test_results, review_results, deploy_result)
            }
            
            logger.info(f"[{execution_id}] Execution completed: {final_status.value}")
            return result
            
        except Exception as e:
            logger.error(f"[{execution_id}] Execution failed: {str(e)}", exc_info=True)
            self._log_stage("ERROR", ExecutionStatus.FAILED, str(e))
            return {
                "execution_id": execution_id,
                "status": ExecutionStatus.FAILED.value,
                "error": str(e),
                "execution_log": [self._serialize_log(log) for log in self.execution_logs]
            }

    async def _execute_planning(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Stage 1: Create execution plan."""
        try:
            if not self.planner:
                raise ValueError("Planner agent not initialized")
            
            if asyncio.iscoroutinefunction(self.planner.run):
                plan = await self.planner.run(task)
            else:
                plan = self.planner.run(task)
            
            if not isinstance(plan, dict):
                raise ValueError("Planner returned invalid response type")
            
            self._log_detail("PLANNING", {
                "files": plan.get("files_to_modify", []),
                "strategy": plan.get("strategy"),
                "priority": plan.get("priority"),
                "steps": len(plan.get("steps", []))
            })
            
            logger.info(f"Planning complete: {len(plan.get('files_to_modify', []))} files identified")
            return plan
        except Exception as e:
            logger.error(f"Planning failed: {e}")
            raise
        

    async def _execute_fixing(self, plan: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Stage 2: Generate actual code fixes."""
        try:
            if not self.fixer:
                raise ValueError("Fixer agent not initialized")
        
            # 🔥 NEW: Handle both old and new plan formats
            files_to_modify = plan.get("files_to_modify") or plan.get("files") or []
        
            logger.info(f"Files to modify: {files_to_modify}")
        
            if not files_to_modify:
                logger.warning("No files specified in plan")
                raise ValueError("No files to fix")
        
            # If files are virtual (<inline_code>), extract from context
            if files_to_modify == ["<inline_code>"]:
                logger.info("Detected inline code - extracting from context")
                inline_code = context.get("prompt", "") or context.get("error_trace", "")
                if inline_code:
                    context["files"] = {"<inline_code>": inline_code}
                    logger.info("Prepared inline code for fixing")
        
            # Build a modified plan for the fixer
            fixer_plan = {
                "files_to_modify": files_to_modify,
                "strategy": plan.get("strategy", "llm_based"),
                "priority": plan.get("priority", "medium"),
                "steps": plan.get("execution_steps", []),
                "error_type": plan.get("error_type", "unknown"),
                "languages": plan.get("languages", [])
            }
        
            fixes = await self.fixer.generate_fixes(fixer_plan, context)
        
            if not isinstance(fixes, dict):
                raise ValueError("Fixer returned invalid response type")
        
            num_fixes = len(fixes.get("fixes", []))
            if num_fixes == 0:
                raise ValueError("Fixer generated no fixes")
        
            self._log_detail("FIXING", {
                "fixes_generated": num_fixes,
                "files": files_to_modify,
                "test_files_detected": len(fixes.get("test_files", [])),
                "test_commands": len(fixes.get("test_commands", []))
            })
        
            logger.info(f"Fixing complete: {num_fixes} fixes generated")
            return fixes
        except Exception as e:
            logger.error(f"Fixing failed: {e}")
            raise

    async def _execute_testing(self, fixes: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Stage 3: Validate fixes with tests."""
        try:
            if not self.test_agent:
                logger.warning("No test agent provided - auto-passing tests")
                return {
                    "all_passed": True,
                    "passed_tests": 0,
                    "failed_tests": 0,
                    "coverage": 0,
                    "status": "skipped"
                }
            
            if asyncio.iscoroutinefunction(self.test_agent.run_tests):
                test_results = await self.test_agent.run_tests(
                    fixes=fixes.get("fixes", []),
                    test_files=fixes.get("test_files", []),
                    test_commands=fixes.get("test_commands", []),
                    context=context
                )
            else:
                test_results = self.test_agent.run_tests(
                    fixes=fixes.get("fixes", []),
                    test_files=fixes.get("test_files", []),
                    test_commands=fixes.get("test_commands", []),
                    context=context
                )
            
            if not isinstance(test_results, dict):
                raise ValueError("Test agent returned invalid response type")
            
            passed = test_results.get("passed_tests", 0)
            failed = test_results.get("failed_tests", 0)
            coverage = test_results.get("coverage", 0)
            
            self._log_detail("TESTING", {
                "passed": passed,
                "failed": failed,
                "coverage": coverage,
                "all_passed": test_results.get("all_passed", False)
            })
            
            logger.info(f"Testing complete: {passed} passed, {failed} failed, {coverage}% coverage")
            return test_results
        except Exception as e:
            logger.error(f"Testing failed: {e}")
            return {
                "all_passed": False,
                "error": str(e),
                "passed_tests": 0,
                "failed_tests": 0,
                "coverage": 0
            }

    async def _execute_review(self, 
                             fixes: Dict[str, Any], 
                             test_results: Dict[str, Any],
                             context: Dict[str, Any]) -> Dict[str, Any]:
        """Stage 4: Conduct code review."""
        try:
            if not self.review:
                logger.warning("No review agent provided - auto-approving")
                return {
                    "approved": True,
                    "issues": [],
                    "risk_level": "low",
                    "confidence": 50,
                    "status": "skipped"
                }
            
            if asyncio.iscoroutinefunction(self.review.review_fixes):
                review_results = await self.review.review_fixes(
                    fixes=fixes.get("fixes", []),
                    test_results=test_results,
                    context=context
                )
            else:
                review_results = self.review.review_fixes(
                    fixes=fixes.get("fixes", []),
                    test_results=test_results,
                    context=context
                )
            
            if not isinstance(review_results, dict):
                raise ValueError("Review agent returned invalid response type")
            
            self._log_detail("REVIEWING", {
                "approved": review_results.get("approved", False),
                "issues_found": len(review_results.get("issues", [])),
                "risk_level": review_results.get("risk_level"),
                "confidence": review_results.get("confidence", 0)
            })
            
            logger.info(f"Code review complete: {'✓ Approved' if review_results.get('approved') else '✗ Rejected'}")
            return review_results
        except Exception as e:
            logger.error(f"Review failed: {e}")
            return {
                "approved": False,
                "error": str(e),
                "issues": [{"type": "error", "message": str(e)}],
                "risk_level": "high",
                "confidence": 0
            }

    async def _execute_deployment(self, fixes: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Stage 5: Apply fixes to codebase."""
        try:
            deployed_files = []
            failed_files = []
            
            for fix in fixes.get("fixes", []):
                file_path = fix.get("file_path")
                fixed_code = fix.get("fixed_code")
                
                if not file_path or not fixed_code:
                    logger.warning(f"Invalid fix: missing file_path or fixed_code")
                    failed_files.append(file_path or "unknown")
                    continue
                
                success = self._apply_code_fix(file_path, fixed_code, context)
                if success:
                    deployed_files.append(file_path)
                    logger.info(f"Successfully deployed fix to {file_path}")
                else:
                    failed_files.append(file_path)
                    logger.warning(f"Failed to deploy fix for {file_path}")
            
            self._log_detail("DEPLOYMENT", {
                "files_deployed": len(deployed_files),
                "files_failed": len(failed_files),
                "files": deployed_files
            })
            
            return {
                "deployed": len(deployed_files) > 0,
                "files_deployed": deployed_files,
                "files_failed": failed_files,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            return {
                "deployed": False,
                "error": str(e)
            }

    async def generate_fixes(self, plan, context):
        """
        Adapter method to match orchestrator expectations.
        Converts internal diff generation into standardized fix format.
        """
        try:
            files = plan.get("files_to_modify", [])
            fixes = []

            for file_path in files:
                original_code = context.get("files", {}).get(file_path, "")

                # Use your existing logic
                diff_result = self._generate_diffs(original_code)

                fixed_code = diff_result.get("fixed_code") if isinstance(diff_result, dict) else diff_result

                fixes.append({
                    "file_path": file_path,
                    "original_code": original_code,
                    "fixed_code": fixed_code,
                    "change_description": "AI-generated fix",
                    "risk_level": "medium"
                })

            return {
                "fixes": fixes,
                "test_files": [],
                "test_commands": []
            }

        except Exception as e:
            return {
                "fixes": [],
                "error": str(e)
            }

    def _apply_code_fix(self, file_path: str, fixed_code: str, context: Dict[str, Any]) -> bool:
        """Apply a code fix to the actual file."""
        try:
            if "files" in context and isinstance(context["files"], dict):
                context["files"][file_path] = fixed_code
                logger.debug(f"Applied fix to {file_path} (in-memory)")
                return True
            
            try:
                from pathlib import Path
                Path(file_path).parent.mkdir(parents=True, exist_ok=True)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_code)
                logger.debug(f"Applied fix to {file_path} (filesystem)")
                return True
            except Exception as e:
                logger.error(f"Failed to write {file_path}: {e}")
                return False
        except Exception as e:
            logger.error(f"Error applying fix: {e}")
            return False

    def _log_stage(self, stage: str, status: ExecutionStatus, message: str):
        """Log a pipeline stage."""
        log = ExecutionLog(
            timestamp=datetime.utcnow().isoformat(),
            stage=stage,
            status=status.value,
            message=message,
            details={}
        )
        self.execution_logs.append(log)
        logger.info(f"[{stage}] {message}")

    def _log_detail(self, stage: str, details: Dict[str, Any]):
        """Add details to the last log entry."""
        if self.execution_logs:
            self.execution_logs[-1].details = details

    def _serialize_log(self, log: ExecutionLog) -> Dict[str, Any]:
        """Serialize execution log to dictionary."""
        return {
            "timestamp": log.timestamp,
            "stage": log.stage,
            "status": log.status,
            "message": log.message,
            "details": log.details
        }

    def _serialize_fix(self, fix: Any) -> Dict[str, Any]:
        """Serialize fix object to dictionary."""
        if isinstance(fix, dict):
            return fix
        return {
            "file_path": getattr(fix, "file_path", "unknown"),
            "change_description": getattr(fix, "change_description", ""),
            "risk_level": getattr(fix, "risk_level", "unknown")
        }

    def _create_summary(self, fixes: Dict[str, Any], 
                       test_results: Dict[str, Any],
                       review_results: Dict[str, Any],
                       deploy_result: Dict[str, Any]) -> str:
        """Create human-readable summary."""
        num_fixes = len(fixes.get("fixes", []))
        tests_passed = test_results.get("all_passed", False)
        approved = review_results.get("approved", False)
        deployed = deploy_result.get("deployed", False) if deploy_result else False
        
        summary = f"""
╔════════════════════════════════════════╗
║       EXECUTION SUMMARY                ║
╠════════════════════════════════════════╣
║ Fixes Generated:      {num_fixes:<22} ║
║ Tests Passed:         {str(tests_passed):<22} ║
║ Code Review:          {('✓ Approved' if approved else '✗ Rejected'):<22} ║
║ Deployment:           {('✓ Deployed' if deployed else '✗ Not deployed'):<22} ║
╠════════════════════════════════════════╣
║ Test Coverage:        {test_results.get('coverage', 0)}%{' '*17} ║
║ Risk Level:           {review_results.get('risk_level', 'unknown'):<22} ║
║ Issues Found:         {len(review_results.get('issues', [])):<22} ║
╚════════════════════════════════════════╝
"""
        return summary

    def _generate_execution_id(self) -> str:
        """Generate unique execution ID."""
        return f"exec-{uuid.uuid4().hex[:8]}"