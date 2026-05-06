# agent.py — Intent-Aware Planner (Production Level 🔥)

import re
import logging
from typing import Dict, Any, List, Tuple
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class Intent(Enum):
    """Intent classification enum."""
    CODE_FIX = "code_fix"
    CODE_DEBUG = "code_debug"
    CODE_REVIEW = "code_review"
    CODE_OPTIMIZE = "code_optimize"
    CODE_REFACTOR = "code_refactor"
    GENERATE_CODE = "generate_code"
    APP_BUILD = "app_build"
    MATH_COMPUTE = "math_compute"
    WEB_SEARCH = "web_search"
    WEATHER_QUERY = "weather_query"
    DATA_ANALYSIS = "data_analysis"
    TEST_WRITE = "test_write"
    DOC_GENERATE = "doc_generate"
    VIDEO_GENERATE = "video_generate"
    PHOTO_GENERATE = "photo_generate"
    UNKNOWN = "unknown"


class Complexity(Enum):
    """Task complexity levels."""
    TRIVIAL = "trivial"
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    CRITICAL = "critical"


@dataclass
class IntentAnalysis:
    """Result of intent analysis."""
    intent: Intent
    confidence: float
    complexity: Complexity
    priority: str
    keywords_matched: List[str]
    error_type: str
    languages_detected: List[str]
    agents_required: List[str]
    strategy: str
    reasoning: str


class PlannerAgent:
    """
    Advanced Intent-Aware Planner
    
    Routes tasks to appropriate agents based on:
    - Intent detection (what the user wants)
    - Error analysis (what went wrong)
    - Code analysis (what languages/frameworks)
    - Context awareness (state of the system)
    - Confidence scoring (how sure we are)
    """

    def __init__(self, runtime):
        self.runtime = runtime
        self.confidence_threshold = 0.15
        
        logger.info("PlannerAgent initialized (Intent-Aware)")

        # ═══════════════════════════════════════
        # INTENT MAPPING (with keywords & patterns)
        # ═══════════════════════════════════════
        self.intent_patterns = {
            Intent.CODE_FIX: {
                "keywords": ["fix", "bug", "error", "broken", "crash", "issue", "problem", "failed"],
                "error_patterns": ["Error:", "Exception", "Traceback", "failed"],
                "priority": "high"
            },
            Intent.CODE_DEBUG: {
                "keywords": ["debug", "trace", "log", "investigate", "why", "what happened", "trace"],
                "error_patterns": ["Traceback", "stack trace", "breakpoint"],
                "priority": "high"
            },
            Intent.CODE_REVIEW: {
                "keywords": ["review", "audit", "check", "examine", "analyze", "quality"],
                "error_patterns": [],
                "priority": "medium"
            },
            Intent.CODE_OPTIMIZE: {
                "keywords": ["optimize", "fast", "performance", "slow", "lag", "speed up"],
                "error_patterns": ["timeout", "slow", "memory"],
                "priority": "medium"
            },
            Intent.CODE_REFACTOR: {
                "keywords": ["refactor", "clean up", "restructure", "improve", "simplify", "maintainability"],
                "error_patterns": [],
                "priority": "low"
            },
            Intent.GENERATE_CODE: {
                "keywords": ["write", "create", "generate", "build", "implement", "code", "function"],
                "error_patterns": [],
                "priority": "medium"
            },
            Intent.APP_BUILD: {
                "keywords": ["build", "create app", "develop", "make", "construct", "project"],
                "error_patterns": [],
                "priority": "medium"
            },
            Intent.MATH_COMPUTE: {
                "keywords": ["calculate", "compute", "solve", "math", "equation", "sum"],
                "error_patterns": [],
                "priority": "low"
            },
            Intent.WEB_SEARCH: {
                "keywords": ["search", "find", "lookup", "google", "query"],
                "error_patterns": [],
                "priority": "low"
            },
            Intent.WEATHER_QUERY: {
                "keywords": ["weather", "forecast", "temperature", "rain", "sunny"],
                "error_patterns": [],
                "priority": "low"
            },
            Intent.DATA_ANALYSIS: {
                "keywords": ["analyze", "data", "statistics", "report", "metrics", "graph"],
                "error_patterns": [],
                "priority": "medium"
            },
            Intent.TEST_WRITE: {
                "keywords": ["test", "unit test", "pytest", "testing", "test case"],
                "error_patterns": [],
                "priority": "medium"
            },
            Intent.DOC_GENERATE: {
                "keywords": ["document", "doc", "readme", "tutorial", "guide"],
                "error_patterns": [],
                "priority": "low"
            },
            Intent.VIDEO_GENERATE: {
                "keywords": ["video", "create video", "make video", "edit video"],
                "error_patterns": [],
                "priority": "MEDIUM"
            },
        
            Intent.PHOTO_GENERATE: {
                "keywords": ["photo", "create photo", "make photo", "edit photo"],
                "error_patterns": [],
                "priority": "MEDIUM"
            }
        }

        # Capability routing map
        self.capability_agents = {
            Intent.CODE_FIX: ["code_assistant", "debugger", "fixer"],
            Intent.CODE_DEBUG: ["content_generator", "generator"],
            Intent.CODE_DEBUG: ["code_assistant", "debugger"],
            Intent.CODE_REVIEW: ["code_assistant", "reviewer"],
            Intent.CODE_OPTIMIZE: ["code_assistant", "optimizer"],
            Intent.CODE_REFACTOR: ["code_assistant", "refactorer"],
            Intent.GENERATE_CODE: ["code_assistant", "fixer"],
            Intent.APP_BUILD: ["app_builder", "code_assistant"],
            Intent.MATH_COMPUTE: ["calculator"],
            Intent.WEB_SEARCH: ["web_agent", "search"],
            Intent.WEATHER_QUERY: ["weather_agent"],
            Intent.DATA_ANALYSIS: ["analytics", "data_processor"],
            Intent.TEST_WRITE: ["code_assistant", "tester"],
            Intent.DOC_GENERATE: ["documentation", "writer"],
            Intent.UNKNOWN: ["code_assistant", "chat"]  # fallback
        }

    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point for intent-aware planning.
        
        Args:
            task: {"prompt": str, "error_trace": str, "context": str, "files": dict}
        
        Returns:
            Plan with agents, strategy, confidence, etc.
        """
        prompt = str(task.get("prompt", "")).lower()
        error_trace = str(task.get("error_trace", "")).lower()
        context = task.get("context", "")
        files = task.get("files", {})

        logger.info(f"[Planner] Analyzing task: {prompt[:80]}")

        # 🔥 STEP 1: Perform intent analysis
        analysis = self._analyze_intent(prompt, error_trace, context, files)

        logger.info(f"[Planner] Intent: {analysis.intent.value} (confidence: {analysis.confidence:.2f})")
        logger.info(f"[Planner] Complexity: {analysis.complexity.value}, Priority: {analysis.priority}")
        logger.info(f"[Planner] Strategy: {analysis.strategy}")

        # 🔥 STEP 2: Check confidence threshold
        if analysis.confidence < self.confidence_threshold:
            logger.warning(f"[Planner] Low confidence ({analysis.confidence:.2f}), using fallback")
            agents = ["code_assistant", "chat"]
            strategy = "low_confidence_fallback"
        else:
            agents = analysis.agents_required
            strategy = analysis.strategy

        # 🔥 STEP 3: Try runtime capability matching
        if self.runtime and hasattr(self.runtime, 'capabilities'):
            try:
                matches = self.runtime.capabilities.match_agents(prompt)
                if matches:
                    best_match = sorted(matches, key=lambda m: m.get("score", 0), reverse=True)[0]
                    if best_match.get("score", 0) >= self.confidence_threshold:
                        logger.info(f"[Planner] Runtime capability match: {best_match['agent']}")
                        agents = [best_match["agent"]]
            except Exception as e:
                logger.debug(f"[Planner] Runtime capability matching failed: {e}")

        # 🔥 STEP 4: Build final plan
        plan = self._build_plan(
            analysis=analysis,
            agents=agents,
            strategy=strategy,
            task=task
        )

        # 🔥 FORCE BUILD IF LILY CONTEXT SAYS SO
        if task.get("context", {}).get("intent") == "build":
            logger.info("[Planner] Forced APP_BUILD from Lily")
    
            return self._build_plan(
                analysis=IntentAnalysis(
                    intent=Intent.APP_BUILD,
                    confidence=1.0,
                    complexity=Complexity.SIMPLE,
                    priority="high",
                    keywords_matched=["build"],
                    error_type="none",
                    languages_detected=["unknown"],
                    agents_required=["app_builder"],
                    strategy="llm_based",
                    reasoning="Forced by Lily intent"
                ),
                agents=["app_builder"],
                strategy="llm_based",
                task=task
          )

        logger.info(f"[Planner] Plan → agents: {agents}, strategy: {strategy}")
        return plan

    def _analyze_intent(self, prompt: str, error_trace: str, context: str, files: Dict) -> IntentAnalysis:
        """
        Comprehensive intent analysis.
        """
        # 1. Detect primary intent
        intent, intent_confidence, matched_keywords = self._detect_intent(prompt, error_trace)

        # 2. Classify error type
        error_type = self._classify_error(error_trace, prompt)

        # 3. Assess complexity
        complexity = self._assess_complexity(prompt, error_trace, len(files))

        # 4. Detect languages
        languages = self._detect_languages(prompt, error_trace, files, context)

        # 5. Determine priority
        priority = self._determine_priority(intent, error_type, complexity)

        # 6. Select strategy
        strategy = self._select_strategy(intent, error_type, complexity, languages)

        # 7. Determine required agents
        agents = self._determine_agents(intent, error_type, complexity)

        # 8. Build reasoning
        reasoning = self._build_reasoning(intent, error_type, complexity, languages)

        return IntentAnalysis(
            intent=intent,
            confidence=intent_confidence,
            complexity=complexity,
            priority=priority,
            keywords_matched=matched_keywords,
            error_type=error_type,
            languages_detected=languages,
            agents_required=agents,
            strategy=strategy,
            reasoning=reasoning
        )

    def _detect_intent(self, prompt: str, error_trace: str) -> Tuple[Intent, float, List[str]]:
        """
        Detect intent from prompt and error trace.
        
        Returns:
            (Intent, confidence_score, matched_keywords)
        """
        combined = f"{prompt} {error_trace}"
        scores = {}
        matched_keywords_map = {}

        # Score each intent
        for intent, pattern_info in self.intent_patterns.items():
            keywords = pattern_info.get("keywords", [])
            error_patterns = pattern_info.get("error_patterns", [])

            # Keyword matches
            keyword_matches = sum(1 for k in keywords if k in combined)
            error_pattern_matches = sum(1 for p in error_patterns if p in error_trace)

            total_matches = keyword_matches + (error_pattern_matches * 2)  # Weight error patterns higher
            max_possible = len(keywords) + (len(error_patterns) * 2)

            confidence = total_matches / max_possible if max_possible > 0 else 0
            scores[intent] = confidence

            # Track matched keywords
            matched = [k for k in keywords if k in combined]
            matched_keywords_map[intent] = matched

        # Find best intent
        if scores:
            best_intent = max(scores, key=scores.get)
            best_confidence = scores[best_intent]
            matched_keywords = matched_keywords_map[best_intent]

        # 🔥 BOOST SIMPLE BUILD COMMANDS
        if "build" in prompt and len(prompt.split()) <= 6:
            return Intent.APP_BUILD, 0.9, ["build"]

        else:
            best_intent = Intent.UNKNOWN
            best_confidence = 0.0
            matched_keywords = []

        logger.debug(f"[Planner] Intent detection: {best_intent.value} ({best_confidence:.2f})")
        return best_intent, best_confidence, matched_keywords

    def _classify_error(self, error_trace: str, prompt: str) -> str:
        """Classify type of error."""
        combined = f"{error_trace} {prompt}".lower()

        error_types = {
            "syntax": ["syntax", "indent", "unexpected", "colon", "quote"],
            "runtime": ["traceback", "error", "exception", "typeerror", "attributeerror"],
            "logic": ["wrong", "incorrect", "unexpected", "assertion"],
            "performance": ["slow", "timeout", "memory", "cpu"],
            "security": ["security", "vulnerability", "injection"],
            "network": ["connection", "timeout", "unreachable", "dns"],
            "database": ["database", "sql", "query", "transaction"],
            "none": ["no error", "working", "ok"]
        }

        for error_type, keywords in error_types.items():
            if any(k in combined for k in keywords):
                return error_type

        return "unknown"

    def _assess_complexity(self, prompt: str, error_trace: str, num_files: int) -> Complexity:
        """Assess task complexity."""
        score = 0

        # Prompt length factor
        score += len(prompt.split()) / 10

        # Error depth factor
        stack_lines = len(error_trace.split('\n'))
        score += stack_lines / 5

        # File count factor
        score += num_files

        # Keyword complexity
        complex_keywords = ["distributed", "concurrent", "async", "architecture", "microservice"]
        score += sum(1 for k in complex_keywords if k in prompt.lower()) * 5

        if score > 30:
            return Complexity.CRITICAL
        elif score > 20:
            return Complexity.COMPLEX
        elif score > 10:
            return Complexity.MODERATE
        elif score > 5:
            return Complexity.SIMPLE
        else:
            return Complexity.TRIVIAL

    def _detect_languages(self, prompt: str, error_trace: str, files: Dict, context: str) -> List[str]:
        """Detect programming languages."""
        languages = set()
        combined = f"{prompt} {error_trace} {str(files)} {str(context)}".lower()

        language_indicators = {
            "python": ["python", "import ", "def ", "py:", ".py"],
            "javascript": ["javascript", "function", "const ", "let ", ".js"],
            "typescript": ["typescript", "interface", "type ", ".ts"],
            "java": ["java", "class ", "public ", ".java"],
            "cpp": ["c++", "cpp", "#include", ".cpp"],
            "go": ["golang", "go:", "func ", ".go"],
            "rust": ["rust", "fn ", "let ", ".rs"],
            "ruby": ["ruby", "def ", "class ", ".rb"],
            "html": ["html", "div", "body", ".html"],
            "css": ["css", "style", "class", ".css"],
            "sql": ["sql", "select", "from", "table"],
            "json": ["json", "{", "}", ".json"],
        }

        for lang, indicators in language_indicators.items():
            if any(ind in combined for ind in indicators):
                languages.add(lang)

        return list(languages) if languages else ["unknown"]

    def _determine_priority(self, intent: Intent, error_type: str, complexity: Complexity) -> str:
        """Determine task priority."""
        base_priority = {
            Intent.CODE_FIX: "high",
            Intent.CODE_DEBUG: "high",
            Intent.CODE_OPTIMIZE: "medium",
            Intent.CODE_REFACTOR: "low",
            Intent.GENERATE_CODE: "medium",
            Intent.TEST_WRITE: "medium",
        }

        priority = base_priority.get(intent, "medium")

        # Adjust for error type
        if error_type == "security":
            return "critical"
        if error_type == "runtime":
            return "high"
        if error_type == "syntax":
            return "high"

        # Adjust for complexity
        if complexity == Complexity.CRITICAL:
            if priority != "critical":
                priority = "high"

        return priority

    def _select_strategy(self, intent: Intent, error_type: str, complexity: Complexity, languages: List[str]) -> str:
        """Select best execution strategy."""
        # Error type based
        if error_type == "syntax":
            return "pattern_based"
        if error_type == "runtime":
            return "llm_based"
        if error_type == "logic":
            return "test_driven"
        if error_type == "performance":
            return "optimization"
        if error_type == "security":
            return "security_audit"

        # Intent based
        strategies = {
            Intent.CODE_FIX: "llm_based",
            Intent.CODE_DEBUG: "debug_trace",
            Intent.CODE_REVIEW: "static_analysis",
            Intent.CODE_OPTIMIZE: "profiling",
            Intent.CODE_REFACTOR: "structural",
            Intent.TEST_WRITE: "test_generation",
            Intent.GENERATE_CODE: "llm_based",
        }

        return strategies.get(intent, "llm_based")

    def _determine_agents(self, intent: Intent, error_type: str, complexity: Complexity) -> List[str]:
        """Determine required agents."""
        base_agents = self.capability_agents.get(intent, ["code_assistant"])

        # Add complexity-aware agents
        if complexity == Complexity.CRITICAL:
            # Add reviewer for critical tasks
            if "reviewer" not in base_agents:
                base_agents.insert(0, "reviewer")

        # Add error-specific agents
        if error_type == "performance":
            if "profiler" not in base_agents:
                base_agents.insert(0, "profiler")

        if error_type == "security":
            if "security_auditor" not in base_agents:
                base_agents.insert(0, "security_auditor")

        return base_agents

    def _build_reasoning(self, intent: Intent, error_type: str, complexity: Complexity, languages: List[str]) -> str:
        """Build explanation for the plan."""
        parts = [
            f"Intent: {intent.value}",
            f"Error type: {error_type}",
            f"Complexity: {complexity.value}",
            f"Languages: {', '.join(languages)}"
        ]
        return " | ".join(parts)

    def _build_plan(self, analysis: IntentAnalysis, agents: List[str], strategy: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build final execution plan.
        
        Returns:
            Complete plan with all metadata
        """
        return {
            "type": "plan",
            "status": "success",
            "intent": analysis.intent.value,
            "agents": agents,
            "strategy": strategy,
            "confidence": analysis.confidence,
            "complexity": analysis.complexity.value,
            "priority": analysis.priority,
            "files_to_modify": list(task.get("files", {}).keys()) or ["main.py"],
            "error_type": analysis.error_type,
            "languages": analysis.languages_detected,
            "keywords_matched": analysis.keywords_matched,
            "execution_steps": self._generate_steps(strategy, analysis.intent),
            "reasoning": analysis.reasoning,
            "metadata": {
                "timestamp": self._get_timestamp(),
                "confidence_threshold": self.confidence_threshold
            }
        }

    def _generate_steps(self, strategy: str, intent: Intent) -> List[str]:
        """Generate execution steps based on strategy."""
        steps = {
            "pattern_based": ["detect_pattern", "apply_fix", "validate", "test"],
            "llm_based": ["analyze", "generate_fix", "validate", "test"],
            "test_driven": ["write_tests", "implement", "run_tests"],
            "optimization": ["profile", "identify_bottleneck", "optimize"],
            "debug_trace": ["trace", "log", "analyze", "debug"],
            "static_analysis": ["scan", "audit", "report"],
            "security_audit": ["audit", "identify_risks", "patch"],
        }
        return steps.get(strategy, ["analyze", "fix", "test"])

    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.utcnow().isoformat()