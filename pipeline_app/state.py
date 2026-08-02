import json
from pathlib import Path
from datetime import datetime

STATE_FILE = Path(__file__).parent / "pipeline_state.json"


def _fresh_step():
    return {"status": "pending", "started_at": None, "completed_at": None}


def load_state(steps):
    """Load persisted state, initialising any steps that are missing."""
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            state = json.load(f)
    else:
        state = {"created_at": None, "steps": {}}

    for step in steps:
        if step.id not in state["steps"]:
            state["steps"][step.id] = _fresh_step()

    return state


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def reset_state(steps):
    state = {
        "created_at": datetime.now().isoformat(),
        "steps": {step.id: _fresh_step() for step in steps},
    }
    save_state(state)
    return state
