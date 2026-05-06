# reviewer.py - Code Review Agent (COMPLETE)
import ast
import logging
import re
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class ReviewerAgent:
    """Performs automated code review on fixes."""
    
    def __init__(self, runtime: Optional[Dict[str, Any]] = None):
        self.runtime = runtime or {}
        self.name = "reviewer"
        logger.info("ReviewerAgent initialized")

    async def review_fixes(self, 
                          fixes: List[Dict[str, Any]], 
                          test_results: Dict[str, Any],
                          context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Review code fixes for quality, safety, and best practices.
        
        Args:
            fixes: List of code fixes to review
            test_results: Results from test execution
            context: Runtime context
        
        Returns:
            Review results with approval status and issues found
        """
        issues = []
        risk_score = 0
        
        try:
            if not fixes:
                logger.warning("No fixes to review")
                return {
                    "approved": False,
                    "issues": [{"type": "error", "message": "No fixes to review"}],
                    "risk_level": "high",
                    "confidence": 0,
                    "reviewer": "automated"
                }
            
            logger.info(f"Starting code review for {len(fixes)} fix(es)")
            
            # Review each fix
            for fix in fixes:
                file_path = fix.get("file_path", "unknown")
                original = fix.get("original_code", "")
                fixed = fix.get("fixed_code", "")
                
                if not original or not fixed:
                    logger.warning(f"Incomplete fix for {file_path}")
                    continue
                
                # Check 1: Syntax validity
                syntax_valid = self._check_syntax(file_path, fixed)
                if not syntax_valid:
                    issues.append({
                        "type": "syntax_error",
                        "file": file_path,
                        "severity": "critical",
                        "message": "Code has syntax errors"
                    })
                    risk_score += 50
                    logger.error(f"Syntax error in {file_path}")
                
                # Check 2: Code size explosion
                size_ok = self._check_code_size(file_path, original, fixed)
                if not size_ok:
                    issues.append({
                        "type": "excessive_changes",
                        "file": file_path,
                        "severity": "warning",
                        "original_size": len(original),
                        "fixed_size": len(fixed),
                        "message": "Code size increased significantly"
                    })
                    risk_score += 20
                    logger.warning(f"Excessive changes in {file_path}")
                
                # Check 3: Dangerous patterns
                dangerous = self._check_dangerous_patterns(file_path, original, fixed)
                if dangerous:
                    for danger in dangerous:
                        issues.append({
                            "type": "dangerous_pattern",
                            "file": file_path,
                            "pattern": danger,
                            "severity": "critical",
                            "message": f"Potentially dangerous pattern: {danger}"
                        })
                        risk_score += 40
                    logger.error(f"Dangerous patterns found in {file_path}")
                
                # Check 4: Code quality metrics
                quality = self._check_code_quality(file_path, fixed)
                if not quality["passes"]:
                    issues.append({
                        "type": "quality_issue",
                        "file": file_path,
                        "severity": "warning",
                        "message": quality["message"]
                    })
                    risk_score += 10
            
            # Check 5: Test coverage requirement
            coverage = test_results.get("coverage", 0)
            if coverage < 70 and coverage > 0:
                issues.append({
                    "type": "low_coverage",
                    "coverage": coverage,
                    "severity": "warning",
                    "message": f"Test coverage is {coverage}%, recommend 70%+"
                })
                risk_score += 15
                logger.warning(f"Low test coverage: {coverage}%")
            
            # Check 6: Test results
            if not test_results.get("all_passed", True):
                issues.append({
                    "type": "test_failure",
                    "severity": "critical",
                    "message": f"Tests failed: {test_results.get('failed_tests', 0)} failures"
                })
                risk_score += 30
                logger.error("Tests failed during review")
            
            # Determine approval based on critical issues
            critical_issues = [i for i in issues if i.get("severity") == "critical"]
            approved = len(critical_issues) == 0
            
            result = {
                "approved": approved,
                "issues": issues,
                "risk_level": self._assess_risk_level(risk_score),
                "risk_score": risk_score,
                "confidence": max(0, 100 - risk_score),
                "critical_issues": len(critical_issues),
                "warning_issues": len([i for i in issues if i.get("severity") == "warning"]),
                "reviewer": "automated"
            }
            
            logger.info(
                f"Code review complete: {'✓ Approved' if approved else '✗ Rejected'} "
                f"(risk: {result['risk_level']}, confidence: {result['confidence']}%)"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Code review failed: {e}", exc_info=True)
            return {
                "approved": False,
                "issues": [{"type": "error", "message": str(e)}],
                "risk_level": "high",
                "confidence": 0,
                "reviewer": "automated"
            }

    def _check_syntax(self, file_path: str, code: str) -> bool:
        """Check if code has valid syntax."""
        try:
            if file_path.endswith(".py"):
                ast.parse(code)
            return True
        except SyntaxError as e:
            logger.debug(f"Syntax error in {file_path}: {e}")
            return False

    def _check_code_size(self, file_path: str, original: str, fixed: str) -> bool:
        """Check if code size explosion occurred (more than 3x growth)."""
        if len(original) == 0:
            return True
        
        growth_factor = len(fixed) / len(original)
        is_ok = growth_factor <= 3.0
        
        if not is_ok:
            logger.debug(f"Code growth in {file_path}: {growth_factor:.2f}x")
        
        return is_ok

    def _check_dangerous_patterns(self, file_path: str, original: str, fixed: str) -> List[str]:
        """Check for dangerous patterns that weren't in original."""
        dangerous_patterns = [
            "eval(",
            "exec(",
            "system(",
            "os.remove",
            "__import__",
            "subprocess.call",
            "pickle.loads",
            "yaml.load"
        ]
        
        found = []
        for pattern in dangerous_patterns:
            if pattern in fixed and pattern not in original:
                found.append(pattern)
                logger.warning(f"Dangerous pattern '{pattern}' found in {file_path}")
        
        return found

    def _check_code_quality(self, file_path: str, code: str) -> Dict[str, Any]:
        """Check basic code quality metrics."""
        issues = []
        
        # Check for very long lines (>120 chars)
        long_lines = sum(1 for line in code.split('\n') if len(line) > 120)
        if long_lines > 0:
            issues.append(f"{long_lines} lines exceed 120 characters")
        
        # Check for deeply nested code (>4 levels)
        max_indent = max((len(line) - len(line.lstrip())) // 4 
                        for line in code.split('\n') if line.strip())
        if max_indent > 4:
            issues.append(f"Nesting depth of {max_indent} levels (recommend ≤ 4)")
        
        # Check for commented-out code (multiple #'s in a row)
        commented = sum(1 for line in code.split('\n') 
                       if line.strip().startswith('##'))
        if commented > len(code.split('\n')) * 0.1:
            issues.append("High amount of commented-out code")
        
        return {
            "passes": len(issues) == 0,
            "message": "; ".join(issues) if issues else "Code quality OK"
        }

    def _assess_risk_level(self, score: int) -> str:
        """Map risk score to risk level."""
        if score >= 80:
            return "critical"
        elif score >= 50:
            return "high"
        elif score >= 20:
            return "medium"
        else:
            return "low"

    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Legacy method for backward compatibility.
        
        Args:
            task: Task dict with review configuration
        
        Returns:
            Review results
        """
        return await self.review_fixes(
            fixes=task.get("fixes", []),
            test_results=task.get("test_results", {}),
            context=task.get("context", {})
        )