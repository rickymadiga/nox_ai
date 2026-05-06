# forge/agents/coder.py

import os
import json
import re
import asyncio
import sqlite3
from datetime import datetime
from typing import Any, Dict, Optional, List

from groq import AsyncGroq
from pydantic import BaseModel

from ..core.agent import Agent
from ..core.message import Message


# ────────────────────────────────────────────────
# Structured schema
# ────────────────────────────────────────────────

class GeneratedProject(BaseModel):
    files: Dict[str, str]


class Coder(Agent):

    MODEL = "llama-3.3-70b-versatile"

    # 🔥 HARD LIMIT CONFIG (increased slightly for memory)
    MAX_INPUT_TOKENS = 7000
    MAX_OUTPUT_TOKENS = 4000

    def __init__(self, name: str, bus: Any, context: dict):
        super().__init__(name=name, bus=bus, context=context)

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found")

        self.client = AsyncGroq(api_key=api_key)

        # 🔥 LONG-TERM MEMORY SETUP
        self.memory_db = "forge/memory/coder_memory.db"
        os.makedirs(os.path.dirname(self.memory_db), exist_ok=True)
        self._init_memory_db()

        # Short-term in-session cache (optional for now)
        self.recent_memories: List[Dict] = []

    def _init_memory_db(self):
        """Create SQLite table for experiences if it doesn't exist."""
        conn = sqlite3.connect(self.memory_db)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS experiences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                user_id TEXT,
                task TEXT,
                plan TEXT,
                template TEXT,
                files_json TEXT,
                outcome TEXT,           -- success | partial | failed
                feedback TEXT,
                lessons TEXT
            )
        """)
        conn.commit()
        conn.close()

    def register(self) -> None:
        print("[Coder] Subscribing → PLAN_CREATED")
        self.bus.subscribe("PLAN_CREATED", self.handle)
        # TODO: Later subscribe to TEST_RESULTS / USER_FEEDBACK for deeper learning

    # ────────────────────────────────────────────────
    # MEMORY HELPERS
    # ────────────────────────────────────────────────
    def _save_experience(self, user_id: str, task: str, plan: str, template: Optional[str],
                         files: Dict[str, str], outcome: str = "generated",
                         feedback: str = "", lessons: str = ""):
        """Persist the build + outcome to long-term memory."""
        try:
            conn = sqlite3.connect(self.memory_db)
            conn.execute("""
                INSERT INTO experiences 
                (timestamp, user_id, task, plan, template, files_json, outcome, feedback, lessons)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                user_id,
                task[:800],
                plan[:1500],
                template or "cli",
                json.dumps(files, ensure_ascii=False),
                outcome,
                feedback[:1000],
                lessons[:1000]
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[Coder] Failed to save experience: {e}")

    def _load_relevant_memories(self, task: str, template: Optional[str], limit: int = 6) -> List[Dict]:
        """Simple relevance retrieval (task keywords + template)."""
        try:
            conn = sqlite3.connect(self.memory_db)
            cursor = conn.execute("""
                SELECT task, plan, template, outcome, lessons 
                FROM experiences 
                WHERE (task LIKE ? OR template = ?)
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (f"%{task[:60]}%", template, limit))
            
            memories = []
            for row in cursor.fetchall():
                memories.append({
                    "past_task": row[0],
                    "past_plan": row[1],
                    "template": row[2],
                    "outcome": row[3],
                    "lessons": row[4] or "No lessons recorded"
                })
            conn.close()
            return memories
        except Exception as e:
            print(f"[Coder] Memory load failed: {e}")
            return []

    def _format_memories_for_prompt(self, memories: List[Dict]) -> str:
        if not memories:
            return "No previous experiences yet. This is the first build."

        parts = ["=== CODER PAST EXPERIENCES (LEARN FROM THESE) ==="]
        for i, m in enumerate(memories, 1):
            parts.append(f"""
Example {i}:
Task: {m['past_task']}
Template: {m.get('template', 'cli')}
Outcome: {m['outcome']}
Lessons learned: {m['lessons']}
""")
        return "\n".join(parts)

    # ────────────────────────────────────────────────
    # PROMPTS
    # ────────────────────────────────────────────────
    def _system_prompt(self, memories_text: str = "") -> str:
        base = """
You are an expert Python developer that improves with every project.

You have access to your past coding experiences. Study the lessons and patterns from previous builds to:
- Avoid repeating mistakes
- Apply proven patterns and your user's preferred style
- Make this new project cleaner, more robust, and more aligned with past successes

Return ONLY valid JSON object with no extra text:

{
  "files": {
    "main.py": "complete runnable code",
    "requirements.txt": "all dependencies, one per line"
  }
}

Strict rules:
- Always include both main.py and requirements.txt
- Code must be minimal but fully working
- Follow best practices shown in successful past builds
- Apply every relevant lesson from the experiences provided
"""
        if memories_text:
            base += f"\n\n{memories_text}\n\nApply the lessons above to make this the best version yet."
        return base

    def _build_prompt(self, task: str, plan: str, template: Optional[str], memories_text: str) -> str:
        template_hint = ""
        if template == "streamlit":
            template_hint = """
- MUST use Streamlit
- MUST include st.button or interactive elements
- MUST display results clearly with st.write / st.success etc.
"""
        elif template == "fastapi":
            template_hint = """
- MUST use FastAPI
- MUST include at least one GET/POST endpoint
- MUST be runnable with uvicorn
"""
        else:
            template_hint = """
- Must be a clean CLI Python script
- Use argparse or click if needed
- Include if __name__ == "__main__"
"""

        return f"""
PAST EXPERIENCES TO LEARN FROM:
{memories_text}

TASK:
{task}

PLAN:
{plan}

REQUIREMENTS:
{template_hint}

Generate a minimal, clean, and fully working Python project based on the task and plan.
Return ONLY the JSON object. No explanations.
"""

    # ────────────────────────────────────────────────
    # SAFE TRUNCATION
    # ────────────────────────────────────────────────
    def _truncate(self, text: str, max_tokens: int = 7000) -> str:
        max_chars = max_tokens * 4
        return text[:max_chars]

    # ────────────────────────────────────────────────
    async def handle(self, message: Message) -> None:
        if message.message_type != "PLAN_CREATED":
            return

        payload = message.payload or {}
        task: str = payload.get("task", "").strip()
        plan_steps: List[str] = payload.get("plan", [])
        template: Optional[str] = payload.get("template")
        user_id = payload.get("user_id", "default_user")
        fix_attempts = payload.get("fix_attempts", 0)

        print(f"[Coder] Generating project → {task}")

        if not task:
            await self._publish_error("Empty task", {})
            return

        plan_text = "\n".join(f"- {p}" for p in plan_steps[:20])

        # 🔥 LOAD RELEVANT MEMORIES
        memories = self._load_relevant_memories(task, template)
        memories_text = self._format_memories_for_prompt(memories)

        prompt = self._build_prompt(task, plan_text, template, memories_text)
        prompt = self._truncate(prompt, self.MAX_INPUT_TOKENS)

        files: Dict[str, str] = {}
        raw = ""
        outcome = "failed"

        try:
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=self.MODEL,
                    messages=[
                        {"role": "system", "content": self._system_prompt(memories_text)},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.15,
                    max_tokens=self.MAX_OUTPUT_TOKENS,
                    response_format={"type": "json_object"},
                ),
                timeout=90,
            )

            raw = response.choices[0].message.content.strip()
            files = await self._parse_and_validate(raw, task, prompt, template)
            outcome = "success" if len(files) >= 2 else "partial"

        except Exception as e:
            print(f"[Coder] ERROR: {e}")
            try:
                print("[Coder] Retrying with smaller prompt...")
                smaller_prompt = self._truncate(prompt, 3500)
                response = await self.client.chat.completions.create(
                    model=self.MODEL,
                    messages=[
                        {"role": "system", "content": self._system_prompt(memories_text)},
                        {"role": "user", "content": smaller_prompt},
                    ],
                    temperature=0.1,
                    max_tokens=2000,
                    response_format={"type": "json_object"},
                )
                raw = response.choices[0].message.content.strip()
                files = await self._parse_and_validate(raw, task, smaller_prompt, template)
                outcome = "success" if len(files) >= 2 else "partial"
            except Exception as retry_err:
                print(f"[Coder] Retry failed: {retry_err}")
                files = self.parse_file_blocks(raw) or self._fallback_error_files(task, str(e))
                outcome = "failed"

        # 🔥 SAVE EXPERIENCE (this is how the agent "learns" over time)
        self._save_experience(
            user_id=user_id,
            task=task,
            plan=plan_text,
            template=template,
            files=files,
            outcome=outcome,
            lessons=""  # TODO: fill this with reflection once you add feedback loop
        )

        await self.bus.publish(
            Message(
                sender=self.name,
                recipient="tester",
                message_type="CODE_GENERATED",
                payload={
                    "files": files,
                    "task": task,
                    "template": template,
                    "user_id": user_id,
                    "fix_attempts": fix_attempts,
                },
            )
        )

        print(f"[Coder] Sent CODE_GENERATED ({len(files)} files) | Experience saved to memory")

    # ────────────────────────────────────────────────
    # EXISTING HELPERS (unchanged except minor cleanups)
    # ────────────────────────────────────────────────
    def parse_file_blocks(self, text: str) -> Dict[str, str]:
        files: Dict[str, str] = {}
        current_file = None
        buffer: List[str] = []

        for line in text.splitlines():
            if line.startswith("FILE:"):
                if current_file and buffer:
                    files[current_file] = "\n".join(buffer).strip()
                current_file = line.replace("FILE:", "").strip()
                buffer = []
            elif current_file:
                buffer.append(line)

        if current_file and buffer:
            files[current_file] = "\n".join(buffer).strip()

        return files

    def _extract_json(self, text: str) -> str:
        start = text.find("{")
        end = text.rfind("}")
        return text[start:end + 1] if start != -1 and end != -1 else "{}"

    def _repair_llm_json(self, text: str) -> str:
        text = re.sub(r"```json|```", "", text, flags=re.IGNORECASE)
        text = self._extract_json(text)
        text = re.sub(r",\s*([}\]])", r"\1", text)
        return text

    async def _parse_and_validate(self, raw: str, task: str, prompt: str, template: Optional[str]) -> Dict[str, str]:
        try:
            cleaned = self._repair_llm_json(raw)
            data = json.loads(cleaned)
            validated = GeneratedProject.model_validate(data)
            files = validated.files

            if "requirements.txt" not in files:
                if template == "streamlit":
                    files["requirements.txt"] = "streamlit\n"
                elif template == "fastapi":
                    files["requirements.txt"] = "fastapi\nuvicorn\n"
                else:
                    files["requirements.txt"] = ""

            return files

        except Exception as e:
            print(f"[Coder] JSON parse failed: {e}")
            return self.parse_file_blocks(raw) or self._fallback_error_files(task, str(e))

    def _fallback_error_files(self, task: str, reason: str) -> Dict[str, str]:
        return {
            "main.py": f'''
import streamlit as st

st.title("Build Failed ⚠️")

st.error("Task: {task}")
st.error("Reason: {reason[:300]}")

if st.button("Retry"):
    st.rerun()
''',
            "requirements.txt": "streamlit\n"
        }

    async def _publish_error(self, reason: str, payload: Dict):
        await self.bus.publish(
            Message(
                sender=self.name,
                recipient="tester",
                message_type="CODE_GENERATED",
                payload={
                    **payload,
                    "files": self._fallback_error_files("error", reason),
                },
            )
        )