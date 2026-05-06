
import time

def run_pipeline(prompt):
    state = {
        "agents": {},
        "files": {},
        "logs": []
    }

    # 🧠 PLANNER
    state["agents"]["🧠 Planner"] = "working"
    yield state
    time.sleep(1)

    plan = f"Plan for: {prompt}"
    state["logs"].append("[Planner] Plan created")
    state["agents"]["🧠 Planner"] = "done"
    yield state

    # 🏗 BUILDER
    state["agents"]["🏗 Builder"] = "working"
    yield state
    time.sleep(1)

    state["files"]["app.py"] = "# generated app code"
    state["files"]["requirements.txt"] = "fastapi\nuvicorn"

    state["logs"].append("[Builder] Files generated")
    state["agents"]["🏗 Builder"] = "done"
    yield state

    # 🧪 TESTER
    state["agents"]["🧪 Tester"] = "working"
    yield state
    time.sleep(1)

    state["logs"].append("[Tester] No errors found")
    state["agents"]["🧪 Tester"] = "done"
    yield state

    # 🔧 FIXER
    state["agents"]["🔧 Fixer"] = "working"
    yield state
    time.sleep(1)

    state["logs"].append("[Fixer] Nothing to fix")
    state["agents"]["🔧 Fixer"] = "done"
    yield state

    return state