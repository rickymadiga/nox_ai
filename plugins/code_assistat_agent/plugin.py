# plugin.py — Code Assistant Plugin (COMPLETELY FIXED - Separate Agents)
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class CodeAssistantAgent:
    """
    Wrapper agent for the AI Code Fixing Orchestrator.
    Handles routing, delegation, and result adaptation to engine format.
    """

    def __init__(self, runtime):
        """
        Initialize the code assistant agent.
        
        Args:
            runtime: Runtime environment with agent registry
        """
        self.runtime = runtime
        self.name = "code_assistant"
        self._orchestrator = None
        self._agents_cache = {}
        
        logger.info("CodeAssistantAgent initialized")

    def _import_agents(self):
        """Import all agent classes."""
        try:
            from .orchestrator import AICodeFixingOrchestrator
            from .planner import PlannerAgent
            from .fixer import CodeFixerEngine, MockCodeRepository
            from .tester import TesterAgent
            from .reviewer import ReviewerAgent
            
            return {
                'AICodeFixingOrchestrator': AICodeFixingOrchestrator,
                'PlannerAgent': PlannerAgent,
                'CodeFixerEngine': CodeFixerEngine,
                'MockCodeRepository': MockCodeRepository,
                'TesterAgent': TesterAgent,
                'ReviewerAgent': ReviewerAgent
            }
        except Exception as e:
            logger.error(f"Failed to import agents: {e}", exc_info=True)
            raise

    def _get_planner(self):
        """Get or create planner."""
        if 'planner' in self._agents_cache:
            return self._agents_cache['planner']
        
        try:
            agents = self._import_agents()
            PlannerAgent = agents['PlannerAgent']
            
            planner = PlannerAgent({"bus": getattr(self.runtime, "bus", None)})
            self._agents_cache['planner'] = planner
            logger.info("✅ Created PlannerAgent")
            return planner
        except Exception as e:
            logger.error(f"Failed to create planner: {e}", exc_info=True)
            raise

    def _get_fixer(self):
        """Get or create fixer."""
        if 'fixer' in self._agents_cache:
            return self._agents_cache['fixer']
        
        try:
            agents = self._import_agents()
            CodeFixerEngine = agents['CodeFixerEngine']
            MockCodeRepository = agents['MockCodeRepository']
            
            fixer = CodeFixerEngine(
                {"bus": getattr(self.runtime, "bus", None)},
                code_repository=MockCodeRepository()
            )
            self._agents_cache['fixer'] = fixer
            logger.info("✅ Created CodeFixerEngine")
            return fixer
        except Exception as e:
            logger.error(f"Failed to create fixer: {e}", exc_info=True)
            raise

    def _get_tester(self):
        """Get or create tester."""
        if 'tester' in self._agents_cache:
            return self._agents_cache['tester']
        
        try:
            agents = self._import_agents()
            TesterAgent = agents['TesterAgent']
            
            tester = TesterAgent({"bus": getattr(self.runtime, "bus", None)})
            self._agents_cache['tester'] = tester
            logger.info("✅ Created TesterAgent")
            return tester
        except Exception as e:
            logger.error(f"Failed to create tester: {e}", exc_info=True)
            raise

    def _get_reviewer(self):
        """Get or create reviewer."""
        if 'reviewer' in self._agents_cache:
            return self._agents_cache['reviewer']
        
        try:
            agents = self._import_agents()
            ReviewerAgent = agents['ReviewerAgent']
            
            reviewer = ReviewerAgent({"bus": getattr(self.runtime, "bus", None)})
            self._agents_cache['reviewer'] = reviewer
            logger.info("✅ Created ReviewerAgent")
            return reviewer
        except Exception as e:
            logger.error(f"Failed to create reviewer: {e}", exc_info=True)
            raise

    def _build_orchestrator(self):
        """
        Build orchestrator with properly initialized agents.
        
        Returns:
            Initialized AICodeFixingOrchestrator instance
        """
        if self._orchestrator is not None:
            return self._orchestrator
        
        try:
            agents = self._import_agents()
            AICodeFixingOrchestrator = agents['AICodeFixingOrchestrator']
            
            logger.info("Building orchestrator with separate agents...")
            
            # Get each agent independently
            planner = self._get_planner()
            fixer = self._get_fixer()
            tester = self._get_tester()
            reviewer = self._get_reviewer()
            
            # Verify types
            logger.info(f"Planner type: {type(planner).__name__}")
            logger.info(f"Fixer type: {type(fixer).__name__}")
            logger.info(f"Tester type: {type(tester).__name__}")
            logger.info(f"Reviewer type: {type(reviewer).__name__}")
            
            # Verify methods exist
            assert hasattr(planner, 'run'), "Planner missing run method"
            assert hasattr(fixer, 'generate_fixes'), "Fixer missing generate_fixes method"
            assert hasattr(tester, 'run_tests'), "Tester missing run_tests method"
            assert hasattr(reviewer, 'review_fixes'), "Reviewer missing review_fixes method"
            
            logger.info("✅ All agents verified")
            
            # Build orchestrator
            self._orchestrator = AICodeFixingOrchestrator(
                planner_agent=planner,
                fixer_agent=fixer,
                test_agent=tester,
                review_agent=reviewer,
                runtime={"bus": getattr(self.runtime, "bus", None)}
            )
            
            logger.info("✅ Orchestrator built successfully")
            return self._orchestrator
            
        except Exception as e:
            logger.error(f"❌ Failed to build orchestrator: {e}", exc_info=True)
            raise

    def _adapt_result_to_engine_format(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adapt orchestrator result to engine format.
        """
        try:
            if not isinstance(result, dict):
                logger.warning(f"Result is not a dict: {type(result)}")
                return self._error_response("Invalid result format")
            
            status = result.get("status", "unknown")
            logger.info(f"Adapting result with status: {status}")
            
            # ✅ SUCCESS CASE
            if status == "approved":
                logger.info("Status is 'approved' - SUCCESS case")
                
                deployment = result.get("deployment", {})
                fixes = result.get("fixes", [])
                
                updated_files = {}
                for fix in fixes:
                    if isinstance(fix, dict):
                        file_path = fix.get("file_path")
                        fixed_code = fix.get("fixed_code")
                        if file_path and fixed_code:
                            updated_files[file_path] = fixed_code
                
                return {
                    "type": "code_result",
                    "mode": "fixer",
                    "analysis": "Code issues fixed successfully",
                    "root_cause": "",
                    "updated_files": updated_files,
                    "diffs": self._generate_diffs(result),
                    "summary": f"✅ Fixes applied to {len(updated_files)} file(s)",
                    "structured": result,
                    "deployment_info": deployment
                }
            
            # ✅ FAILURE CASE
            elif status == "failed" or status == "rejected":
                logger.info(f"Status is '{status}' - FAILURE case")
                
                error = result.get("error", "Unknown error")
                execution_log = result.get("execution_log", [])
                
                root_cause = error
                for log in execution_log:
                    if log.get("status") == "failed":
                        root_cause = log.get("message", error)
                        break
                
                return {
                    "type": "code_result",
                    "mode": "debugger",
                    "analysis": error,
                    "root_cause": root_cause,
                    "updated_files": {},
                    "diffs": {},
                    "summary": f"❌ Fix attempt failed: {error}",
                    "structured": result,
                    "error": error,
                    "execution_log": execution_log
                }
            
            else:
                logger.warning(f"Unknown status: {status}")
                return {
                    "type": "code_result",
                    "analysis": f"Execution completed with status: {status}",
                    "root_cause": "",
                    "updated_files": {},
                    "diffs": {},
                    "summary": f"Status: {status}",
                    "structured": result
                }
        
        except Exception as e:
            logger.error(f"Error adapting result: {e}", exc_info=True)
            return self._error_response(str(e))

    def _generate_diffs(self, result: Dict[str, Any]) -> Dict[str, str]:
        """Generate diff representation from fixes."""
        diffs = {}
        try:
            for fix in result.get("fixes", []):
                if isinstance(fix, dict):
                    file_path = fix.get("file_path")
                    original = fix.get("original_code", "")
                    fixed = fix.get("fixed_code", "")
                    description = fix.get("change_description", "")
                    
                    if file_path:
                        diffs[file_path] = {
                            "description": description,
                            "lines_changed": len(fixed.split('\n')) - len(original.split('\n')),
                            "changes": description
                        }
        except Exception as e:
            logger.warning(f"Error generating diffs: {e}")
        
        return diffs

    def _error_response(self, error: str) -> Dict[str, Any]:
        """Generate error response in engine format."""
        return {
            "type": "code_result",
            "mode": "debugger",
            "analysis": error,
            "root_cause": error,
            "updated_files": {},
            "diffs": {},
            "summary": f"❌ Error: {error}",
            "error": error
        }

    def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the code fixing pipeline and adapt result to engine format.
        """
        if not task:
            logger.error("Task is None or empty")
            return self._error_response("Task is required")
        
        try:
            logger.info(f"🔥 CodeAssistantAgent.run() called")
            logger.info(f"   Prompt: {task.get('prompt', '')[:60]}")
            
            # Build orchestrator
            orchestrator = self._build_orchestrator()
            
            # Run orchestrator
            logger.info("Executing orchestrator.run()...")
            result = orchestrator.run(task)
            
            logger.info(f"Orchestrator returned status: {result.get('status')}")
            
            # Adapt result
            adapted_result = self._adapt_result_to_engine_format(result)
            
            logger.info(f"✅ CodeAssistantAgent.run() completed")
            return adapted_result
            
        except Exception as e:
            logger.error(f"❌ CodeAssistantAgent.run() failed: {str(e)}", exc_info=True)
            return self._error_response(str(e))

    def validate(self, task: Dict[str, Any]) -> bool:
        """Validate task structure."""
        if not isinstance(task, dict):
            logger.warning("Task is not a dictionary")
            return False
        
        if not task.get("prompt"):
            logger.warning("Task missing 'prompt' field")
            return False
        
        return True

    def get_info(self) -> Dict[str, Any]:
        """Get agent information."""
        return {
            "name": self.name,
            "type": "orchestrator",
            "description": "AI-powered code fixing and analysis orchestrator",
            "capabilities": [
                "code_analysis",
                "automatic_fixing",
                "test_execution",
                "code_review",
                "deployment"
            ]
        }


def register(runtime):
    """Register the CodeAssistantAgent with the runtime."""
    try:
        # Create main wrapper agent
        agent = CodeAssistantAgent(runtime)
        runtime.register_agent("code_assistant", agent)
        logger.info("✅ CodeAssistantAgent registered successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to register CodeAssistantAgent: {e}", exc_info=True)
        raise

    # Register capabilities
    try:
        runtime.register_capability(
            agent_name="code_assistant",
            intent="coding",
            keywords=[
                "fix code", "fix this", "fix the bug", "debug", "debug this",
                "there's a bug", "error", "fix error", "fix issue", "not working",
                "crash", "broken", "runtime error", "traceback", "exception",
                "improve code", "optimize", "refactor", "clean up", "clean code",
                "make it better", "performance", "best practices",
                "explain code", "explain this", "what does this do", "how does this work",
                "code review", "review this",
                "write function", "create function", "add feature", "implement",
                "create api", "build endpoint", "python code", "javascript",
                "typescript", "react", "backend", "frontend", "fullstack",
                "can you fix", "help me fix", "solve this error", "improve this code"
            ]
        )
        logger.info("✅ Capabilities registered")
    except Exception as e:
        logger.warning(f"⚠️ Could not register capabilities: {e}")

    # Set priority
    try:
        runtime.capabilities.set_priority("code_assistant", 25)
        logger.info("✅ Priority set to 25")
    except Exception as e:
        logger.warning(f"⚠️ Could not set priority: {e}")

    print("🚀 Code Assistant Plugin ready!")