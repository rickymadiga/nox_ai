# tester.py - Test Execution Agent (COMPLETE)
import asyncio
import logging
import re
import subprocess
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class TesterAgent:
    """Runs tests on generated fixes."""
    
    def __init__(self, runtime: Optional[Dict[str, Any]] = None):
        self.runtime = runtime or {}
        self.name = "tester"
        logger.info("TesterAgent initialized")

    async def run_tests(self, 
                       fixes: List[Dict[str, Any]], 
                       test_files: List[str],
                       test_commands: List[str], 
                       context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute all test commands on fixes.
        
        Args:
            fixes: List of code fixes to test
            test_files: Test files to run
            test_commands: Commands to execute for testing
            context: Runtime context
        
        Returns:
            Test results with pass/fail counts and coverage
        """
        results = {
            "passed_tests": 0,
            "failed_tests": 0,
            "coverage": 0,
            "all_passed": True,
            "test_output": [],
            "errors": [],
            "status": "pending"
        }
        
        try:
            # If no test files or commands, treat as passing (nothing to test)
            if not test_files and not test_commands:
                logger.warning("No tests to run - auto-passing")
                return {
                    **results,
                    "all_passed": True,
                    "message": "No tests configured",
                    "status": "skipped"
                }
            
            logger.info(f"Starting test execution with {len(test_commands)} commands")
            
            # Execute each test command
            for cmd in test_commands:
                try:
                    logger.debug(f"Executing test command: {cmd}")
                    output = await self._run_command(cmd)
                    
                    # Store truncated output
                    truncated_output = output[:500] if output else ""
                    results["test_output"].append({
                        "command": cmd,
                        "output": truncated_output,
                        "success": "FAILED" not in output and "error" not in output.lower()
                    })
                    
                    # Parse test results
                    if self._is_test_failure(output):
                        results["all_passed"] = False
                        results["failed_tests"] += 1
                        logger.warning(f"Test failed for command: {cmd}")
                    else:
                        results["passed_tests"] += 1
                        logger.info(f"Test passed for command: {cmd}")
                    
                    # Extract coverage percentage if available
                    coverage = self._extract_coverage(output)
                    if coverage is not None:
                        results["coverage"] = coverage
                
                except Exception as e:
                    logger.error(f"Test command failed: {cmd} - {e}")
                    results["errors"].append(str(e))
                    results["all_passed"] = False
                    results["failed_tests"] += 1
            
            results["status"] = "completed"
            
            # Log summary
            logger.info(
                f"Test execution complete: {results['passed_tests']} passed, "
                f"{results['failed_tests']} failed, "
                f"{results['coverage']}% coverage"
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Test execution failed: {e}", exc_info=True)
            return {
                **results,
                "all_passed": False,
                "errors": [str(e)],
                "status": "error"
            }

    async def _run_command(self, cmd: str) -> str:
        """
        Execute shell command and capture output.
        
        Args:
            cmd: Command to execute
        
        Returns:
            Combined stdout and stderr output
        """
        try:
            # Use subprocess to run the command
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=None
            )
            
            output = result.stdout + result.stderr
            return output
            
        except subprocess.TimeoutExpired:
            logger.error(f"Test command timed out: {cmd}")
            return "TIMEOUT: Test execution exceeded 60 seconds"
        except Exception as e:
            logger.error(f"Error running command: {cmd} - {e}")
            return f"ERROR: {str(e)}"

    def _is_test_failure(self, output: str) -> bool:
        """Check if test output indicates failure."""
        if not output:
            return False
        
        failure_indicators = [
            "FAILED",
            "failed",
            "ERROR",
            "error",
            "exception",
            "Exception",
            "Traceback",
            "FAIL",
            "AssertionError"
        ]
        
        return any(indicator in output for indicator in failure_indicators)

    def _extract_coverage(self, output: str) -> Optional[int]:
        """Extract code coverage percentage from output."""
        try:
            # Look for patterns like "coverage: 85%" or "85% coverage"
            match = re.search(r'(\d+)\s*%\s*(?:coverage|covered)', output, re.IGNORECASE)
            if match:
                return int(match.group(1))
            
            # Look for "85% Complete" or similar
            match = re.search(r'(\d+)\s*%', output)
            if match:
                return int(match.group(1))
            
            return None
        except Exception as e:
            logger.debug(f"Error extracting coverage: {e}")
            return None

    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Legacy method for backward compatibility.
        
        Args:
            task: Task dict with test configuration
        
        Returns:
            Test results
        """
        return await self.run_tests(
            fixes=task.get("fixes", []),
            test_files=task.get("test_files", []),
            test_commands=task.get("test_commands", []),
            context=task.get("context", {})
        )