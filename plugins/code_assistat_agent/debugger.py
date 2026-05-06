import logging
import re
import json
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class DebuggerAgent:
    """
    Analyzes test results and fixes to identify root causes of issues.
    Provides debugging insights and verification results.
    """

    def __init__(self, runtime):
        self.runtime = runtime
        self.name = "debugger"
        logger.info("DebuggerAgent initialized")

    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Debug and verify fixes based on test results.

        Args:
            task: Dictionary containing:
                - fixes: Dictionary with fixed code and changes
                - test: Test results from TesterAgent
                - review: Optional review results
                - context: Optional context about the issue

        Returns:
            Dictionary containing:
                - issues: List of identified issues
                - root_cause: Identified root cause
                - suggestions: Debugging suggestions
                - verified: Whether fixes are verified as working
                - recommendations: Next steps or recommendations
        """
        try:
            fixes = task.get("fixes", {})
            test_results = task.get("test", {})
            review_results = task.get("review", {})
            context = task.get("context", "")

            logger.info("Starting debug and verification process")

            issues = []
            root_cause = "Unknown"
            suggestions = []
            verified = False
            recommendations = []

            # Analyze test results
            if not test_results.get("passed", False):
                test_issues = await self._analyze_test_failures(test_results, fixes, context)
                issues.extend(test_issues)
                root_cause = self._determine_root_cause(test_issues)
                suggestions = self._generate_debugging_suggestions(test_issues, fixes)
            else:
                verified = True
                logger.info("All tests passed - fixes verified as working")

            # Analyze review results if available
            if review_results:
                review_issues = self._analyze_review_results(review_results, fixes)
                issues.extend(review_issues)
                
                # Update root cause if review found issues
                if review_issues and not verified:
                    root_cause = self._determine_root_cause(review_issues)

            # Perform additional diagnostics
            diagnostic_issues = await self._perform_diagnostics(fixes, test_results, context)
            issues.extend(diagnostic_issues)

            # Generate recommendations
            if not verified:
                recommendations = self._generate_recommendations(issues, root_cause, fixes)

            result = {
                "issues": issues,
                "root_cause": root_cause,
                "suggestions": suggestions,
                "verified": verified,
                "recommendations": recommendations,
                "total_issues": len(issues),
                "analysis_complete": True
            }

            logger.info(
                f"Debug complete: Verified={verified}, "
                f"Root cause='{root_cause}', Issues found={len(issues)}"
            )
            return result

        except Exception as e:
            logger.error(f"Error in debugger: {str(e)}", exc_info=True)
            return {
                "issues": [{"type": "debug_error", "message": str(e)}],
                "root_cause": "Debugging process failed",
                "suggestions": ["Check logs for detailed error information"],
                "verified": False,
                "recommendations": ["Retry debugging or examine logs"],
                "error": str(e)
            }

    async def _analyze_test_failures(
        self,
        test_results: Dict[str, Any],
        fixes: Dict[str, Any],
        context: str
    ) -> List[Dict[str, Any]]:
        """Analyze test failures in detail."""
        issues = []

        failed_count = test_results.get("failed_count", 0)
        test_details = test_results.get("test_results", [])

        if failed_count > 0:
            logger.warning(f"Analyzing {failed_count} test failures")

            for test_detail in test_details:
                if test_detail.get("status") == "failed":
                    issue = {
                        "type": "test_failure",
                        "severity": "high",
                        "test_name": test_detail.get("test_name", "unknown"),
                        "test_file": test_detail.get("test_file", "unknown"),
                        "message": test_detail.get("message", "Test failed"),
                        "analysis": await self._analyze_specific_failure(test_detail, fixes, context)
                    }
                    issues.append(issue)

        return issues

    async def _analyze_specific_failure(
        self,
        test_detail: Dict[str, Any],
        fixes: Dict[str, Any],
        context: str
    ) -> str:
        """Analyze a specific test failure."""
        test_name = test_detail.get("test_name", "")
        message = test_detail.get("message", "")

        # Look for common patterns
        if "AssertionError" in message:
            return "Test assertion failed - expected value mismatch"
        elif "TypeError" in message:
            return "Type error in code - check data types"
        elif "AttributeError" in message:
            return "Attribute not found - check object properties"
        elif "KeyError" in message:
            return "Dictionary key not found - check key names"
        elif "ValueError" in message:
            return "Invalid value provided - check input validation"
        elif "ImportError" in message:
            return "Import error - check dependencies"
        elif "NameError" in message:
            return "Name not defined - check variable names"
        else:
            return f"Test failure: {message[:100]}"

    def _analyze_review_results(
        self,
        review_results: Dict[str, Any],
        fixes: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Analyze review results for issues."""
        issues = []

        if not review_results.get("approved", False):
            logger.warning("Code review did not approve changes")

            review_issues = review_results.get("issues", [])
            for issue in review_issues:
                if issue.get("severity") in ["critical", "high"]:
                    issues.append({
                        "type": "review_issue",
                        "severity": issue.get("severity", "medium"),
                        "file": issue.get("file", "unknown"),
                        "message": issue.get("message", "Review issue"),
                        "line": issue.get("line", 0)
                    })

        return issues

    async def _perform_diagnostics(
        self,
        fixes: Dict[str, Any],
        test_results: Dict[str, Any],
        context: str
    ) -> List[Dict[str, Any]]:
        """Perform additional diagnostics."""
        issues = []

        fixed_files = fixes.get("fixed_files", {})

        for file_path, content in fixed_files.items():
            # Check for common issues
            diagnostics = self._check_common_issues(file_path, content)
            issues.extend(diagnostics)

        return issues

    @staticmethod
    def _check_common_issues(file_path: str, content: str) -> List[Dict[str, Any]]:
        """Check for common coding issues."""
        issues = []

        # Check for infinite loops
        if re.search(r'while\s+True', content):
            issues.append({
                "type": "potential_issue",
                "severity": "medium",
                "file": file_path,
                "message": "Infinite loop detected (while True)"
            })

        # Check for uninitialized variables
        if re.search(r'\bx\b|\by\b|\btemp\b', content):
            issues.append({
                "type": "potential_issue",
                "severity": "low",
                "file": file_path,
                "message": "Generic variable names detected - consider more descriptive names"
            })

        # Check for missing error handling
        if re.search(r'\.open\(|\.read\(|\.execute\(', content):
            if not re.search(r'try:|except', content):
                issues.append({
                    "type": "potential_issue",
                    "severity": "medium",
                    "file": file_path,
                    "message": "File/database operations without error handling"
                })

        return issues

    @staticmethod
    def _determine_root_cause(issues: List[Dict[str, Any]]) -> str:
        """Determine the primary root cause from issues."""
        if not issues:
            return "Unknown"

        # Prioritize by severity
        critical = [i for i in issues if i.get("severity") == "critical"]
        if critical:
            return critical[0].get("message", "Critical issue detected")

        high = [i for i in issues if i.get("severity") == "high"]
        if high:
            return high[0].get("message", "High severity issue")

        # Return first issue message
        return issues[0].get("message", "Issue detected")

    @staticmethod
    def _generate_debugging_suggestions(
        issues: List[Dict[str, Any]],
        fixes: Dict[str, Any]
    ) -> List[str]:
        """Generate debugging suggestions based on issues."""
        suggestions = []

        for issue in issues[:3]:  # Limit to top 3
            message = issue.get("message", "")

            if "AssertionError" in message or "assertion" in message.lower():
                suggestions.append("Check test expectations vs. actual values")
                suggestions.append("Add debug prints to trace variable values")

            if "TypeError" in message or "type" in message.lower():
                suggestions.append("Verify input types match expected types")
                suggestions.append("Add type hints or validation")

            if "AttributeError" in message or "attribute" in message.lower():
                suggestions.append("Check object initialization")
                suggestions.append("Verify attribute names are correct")

            if "NameError" in message or "not defined" in message.lower():
                suggestions.append("Check variable scope and initialization")
                suggestions.append("Look for typos in variable names")

        # Add general suggestions
        if not suggestions:
            suggestions.append("Review the error message carefully")
            suggestions.append("Add logging to track execution flow")

        return suggestions

    @staticmethod
    def _generate_recommendations(
        issues: List[Dict[str, Any]],
        root_cause: str,
        fixes: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on debug results."""
        recommendations = []

        if not issues:
            recommendations.append("✓ All verifications passed - fixes appear to be working correctly")
            return recommendations

        # Based on issue types
        issue_types = [i.get("type") for i in issues]

        if "test_failure" in issue_types:
            recommendations.append("Review and update the fix implementation")
            recommendations.append("Consider adding more comprehensive test cases")

        if "review_issue" in issue_types:
            recommendations.append("Address code quality issues identified by reviewer")
            recommendations.append("Run code quality checks again")

        if "potential_issue" in issue_types:
            recommendations.append("Add error handling for file/database operations")
            recommendations.append("Use more descriptive variable names")

        # Final recommendations
        if len(issues) > 3:
            recommendations.append("Multiple issues found - prioritize by severity")

        recommendations.append("Re-run tests after addressing issues")

        return recommendations