# main.py - Complete Example (FIXED)
import asyncio
import logging
import json
from planner import PlannerAgent
from fixer import CodeFixerEngine, MockCodeRepository
from tester import TesterAgent
from reviewer import ReviewerAgent
from orchestrator import AICodeFixingOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point for the AI code fixing pipeline."""
    
    print("🚀 Starting AI Code Fixing Agent...\n")
    
    # Initialize runtime
    runtime = {
        "llm": None  # Add LLM instance if available
    }
    
    # Initialize agents
    planner = PlannerAgent(runtime)
    fixer = CodeFixerEngine(runtime, code_repository=MockCodeRepository())
    tester = TesterAgent(runtime)
    reviewer = ReviewerAgent(runtime)
    
    # Initialize orchestrator
    orchestrator = AICodeFixingOrchestrator(
        planner_agent=planner,
        fixer_agent=fixer,
        test_agent=tester,
        review_agent=reviewer,
        runtime=runtime
    )
    
    # Define task
    task = {
        "prompt": "Fix the syntax error in main.py",
        "error_trace": "SyntaxError: unexpected indent on line 42"
    }
    
    # Execute the pipeline (synchronous call)
    result = orchestrator.run(task)
    
    # Display results
    print("\n" + "="*50)
    print("=== FINAL RESULT ===")
    print("="*50)
    
    print(f"Status: {result.get('status', 'unknown')}")
    print(f"Execution ID: {result.get('execution_id', 'unknown')}")
    
    if result.get("error"):
        print(f"Error: {result['error']}")
    
    # Print summary
    if result.get("summary"):
        print(result["summary"])
    
    # Print execution log
    if result.get("execution_log"):
        print("\n📋 Execution Log:")
        for log in result["execution_log"]:
            print(f"  [{log['stage']}] {log['message']}")
    
    # Print detailed results if approved
    if result.get("status") == "approved":
        print("\n✅ APPROVED - Ready for deployment!")
        if result.get("deployment"):
            print(f"Deployment: {result['deployment']}")
    else:
        print("\n❌ NOT APPROVED - Review required")
    
    return result


async def main_async():
    """Async entry point for the AI code fixing pipeline."""
    
    print("🚀 Starting AI Code Fixing Agent (Async)...\n")
    
    # Initialize runtime
    runtime = {
        "llm": None  # Add LLM instance if available
    }
    
    # Initialize agents
    planner = PlannerAgent(runtime)
    fixer = CodeFixerEngine(runtime, code_repository=MockCodeRepository())
    tester = TesterAgent(runtime)
    reviewer = ReviewerAgent(runtime)
    
    # Initialize orchestrator
    orchestrator = AICodeFixingOrchestrator(
        planner_agent=planner,
        fixer_agent=fixer,
        test_agent=tester,
        review_agent=reviewer,
        runtime=runtime
    )
    
    # Define task
    task = {
        "prompt": "Fix the syntax error in main.py",
        "error_trace": "SyntaxError: unexpected indent on line 42"
    }
    
    # Execute the pipeline (async call)
    result = await orchestrator.run_async(task)
    
    # Display results
    print("\n" + "="*50)
    print("=== FINAL RESULT ===")
    print("="*50)
    
    print(f"Status: {result.get('status', 'unknown')}")
    print(f"Execution ID: {result.get('execution_id', 'unknown')}")
    
    if result.get("error"):
        print(f"Error: {result['error']}")
    
    # Print summary
    if result.get("summary"):
        print(result["summary"])
    
    # Print execution log
    if result.get("execution_log"):
        print("\n📋 Execution Log:")
        for log in result["execution_log"]:
            print(f"  [{log['stage']}] {log['message']}")
    
    # Print detailed results if approved
    if result.get("status") == "approved":
        print("\n✅ APPROVED - Ready for deployment!")
        if result.get("deployment"):
            print(f"Deployment: {result['deployment']}")
    else:
        print("\n❌ NOT APPROVED - Review required")
    
    return result


if __name__ == "__main__":
    # Use synchronous main() for engine compatibility
    result = main()
    
    print("\n" + json.dumps(result, indent=2, default=str))