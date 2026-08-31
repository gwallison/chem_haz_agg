import streamlit as st
import sys
from pathlib import Path
from datetime import datetime

# Bootstrap paths so local modules resolve correctly
APP_DIR = Path(__file__).parent
PROJECT_ROOT = APP_DIR.parent
sys.path.insert(0, str(APP_DIR))
sys.path.insert(0, str(PROJECT_ROOT))

from steps import STEPS, steps_by_id
from state import load_state, save_state, reset_state
from runner import run_step_streaming

st.set_page_config(page_title="ChemHaz Pipeline", page_icon="🧪", layout="wide")

# ── Constants ─────────────────────────────────────────────────────────────────

STATUS_ICON = {
    "pending": "⬜",
    "running": "🔄",
    "done": "✅",
    "failed": "❌",
    "skipped": "⏭️",
}

CATEGORY_BADGE = {
    "AUTO":         "🤖 AUTO",
    "MANUAL-FETCH": "👤 MANUAL",
    "HUMAN-LOOP":   "🔐 HUMAN-LOOP",
    "BLOCKED":      "🚫 BLOCKED",
}

# ── State ─────────────────────────────────────────────────────────────────────

state = load_state(STEPS)
sid_map = steps_by_id()

# ── Helpers ───────────────────────────────────────────────────────────────────

def deps_satisfied(step):
    return all(
        state["steps"].get(dep, {}).get("status") in ("done", "skipped")
        for dep in step.dependencies
    )

def blocking_dep_names(step):
    return [
        sid_map[d].name
        for d in step.dependencies
        if state["steps"].get(d, {}).get("status") not in ("done", "skipped")
        and d in sid_map
    ]

def run_step(step):
    """Execute an AUTO step, streaming output live, then update state."""
    ss = state["steps"][step.id]
    ss["status"] = "running"
    ss["started_at"] = datetime.now().isoformat()
    save_state(state)

    output_area = st.empty()
    lines = []
    return_code = 1  # default to failure until process reports otherwise

    extra_args = st.session_state.get("active_run_extra_args")
    for line, rc in run_step_streaming(step, extra_args=extra_args):
        lines.append(line.rstrip("\n"))
        output_area.code("\n".join(lines[-100:]), language=None)
        if rc is not None:
            return_code = rc

    ss["status"] = "done" if return_code == 0 else "failed"
    ss["completed_at"] = datetime.now().isoformat()
    ss["output"] = "\n".join(lines)
    save_state(state)
    st.session_state.active_run_id = None
    st.session_state.active_run_extra_args = None
    st.rerun()

def mark_step(step_id, status):
    ss = state["steps"][step_id]
    ss["status"] = status
    ss["completed_at"] = datetime.now().isoformat()
    save_state(state)
    st.rerun()

def reset_step(step_id):
    state["steps"][step_id] = {"status": "pending", "started_at": None, "completed_at": None}
    save_state(state)
    st.rerun()

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("🧪 ChemHaz Pipeline")

    total = len(STEPS)
    done_count = sum(1 for s in STEPS if state["steps"][s.id]["status"] in ("done", "skipped"))
    failed_count = sum(1 for s in STEPS if state["steps"][s.id]["status"] == "failed")

    st.metric("Progress", f"{done_count} / {total} steps")
    st.progress(done_count / total)
    if failed_count:
        st.error(f"{failed_count} step(s) failed")
    if state.get("created_at"):
        st.caption(f"Run started: {state['created_at'][:10]}")

    st.divider()
    if st.button("🔄 Start New Run", use_container_width=True):
        reset_state(STEPS)
        st.rerun()

    st.divider()
    st.subheader("By Stage")

    stages_ordered = list(dict.fromkeys(s.stage for s in STEPS))
    for stage in stages_ordered:
        stage_steps = [s for s in STEPS if s.stage == stage]
        n_done = sum(1 for s in stage_steps if state["steps"][s.id]["status"] in ("done", "skipped"))
        n_fail = sum(1 for s in stage_steps if state["steps"][s.id]["status"] == "failed")
        n_total = len(stage_steps)
        if n_done == n_total:
            icon = "✅"
        elif n_fail:
            icon = "❌"
        elif n_done > 0:
            icon = "🔄"
        else:
            icon = "⬜"
        st.write(f"{icon} **{stage}** {n_done}/{n_total}")

# ── Main content ──────────────────────────────────────────────────────────────

st.title("ChemHaz Data Pipeline")
st.caption("Work through each step in order. AUTO steps run directly; MANUAL steps show instructions.")
st.divider()

stages_ordered = list(dict.fromkeys(s.stage for s in STEPS))

for stage in stages_ordered:
    st.header(stage)

    for step in [s for s in STEPS if s.stage == stage]:
        ss = state["steps"][step.id]
        status = ss["status"]
        icon = STATUS_ICON.get(status, "⬜")
        badge = CATEGORY_BADGE.get(step.category, step.category)
        satisfied = deps_satisfied(step)

        # Auto-expand the first pending/failed step that's ready to action
        is_active = status in ("pending", "failed") and satisfied

        with st.expander(f"{icon} **{step.name}** — {badge}", expanded=is_active):
            st.caption(step.description)

            # Dependency warning
            if not satisfied:
                blockers = blocking_dep_names(step)
                st.warning(f"Waiting on: {', '.join(blockers)}")

            # Instructions
            if step.category in ("MANUAL-FETCH", "HUMAN-LOOP") and step.instructions:
                st.markdown(step.instructions)
            if step.url:
                st.link_button(f"🔗 Open source", step.url)

            if step.category == "BLOCKED":
                st.error("This step is blocked — see pipeline tracker for details.")

            st.divider()

            # Status + action buttons
            col_status, col_btn = st.columns([2, 1])

            with col_status:
                if status == "done":
                    st.success("✅ Complete")
                    if ss.get("completed_at"):
                        st.caption(f"Completed: {ss['completed_at'][:16].replace('T', ' ')}")
                elif status == "failed":
                    st.error("❌ Failed")
                    if ss.get("completed_at"):
                        st.caption(f"Failed at: {ss['completed_at'][:16].replace('T', ' ')}")
                elif status == "skipped":
                    st.info("⏭️ Skipped")
                elif status == "running":
                    st.info("🔄 Running…")
                else:
                    if not satisfied:
                        st.caption("Blocked by unfinished dependencies.")
                    else:
                        st.caption("Ready.")

            with col_btn:
                if status in ("done", "skipped", "failed"):
                    if st.button("↩ Reset", key=f"reset_{step.id}"):
                        reset_step(step.id)

                elif status == "pending" and satisfied:
                    if step.id == "run-build-site":
                        if st.button("▶ Run (new chemicals only)", key=f"run_{step.id}_new", type="primary"):
                            st.session_state.active_run_id = step.id
                            st.session_state.active_run_extra_args = ["--new-only"]
                            st.rerun()
                        st.caption("Regenerates tier SVGs and pages only for chemicals that don't have one yet.")
                        st.warning("Regenerating ALL tier SVGs takes a long time — only needed if the image structure itself changed.")
                        if st.button("⚠ Regenerate ALL (slow)", key=f"run_{step.id}_all"):
                            st.session_state.active_run_id = step.id
                            st.session_state.active_run_extra_args = None
                            st.rerun()
                        if st.button("⏭ Skip", key=f"skip_{step.id}"):
                            mark_step(step.id, "skipped")
                    elif step.category == "AUTO":
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button("▶ Run", key=f"run_{step.id}", type="primary"):
                                st.session_state.active_run_id = step.id
                                st.session_state.active_run_extra_args = None
                                st.rerun()
                        with c2:
                            if st.button("⏭ Skip", key=f"skip_{step.id}"):
                                mark_step(step.id, "skipped")

                    elif step.category in ("MANUAL-FETCH", "HUMAN-LOOP"):
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button("✅ Done", key=f"done_{step.id}", type="primary"):
                                mark_step(step.id, "done")
                        with c2:
                            if st.button("⏭ Skip", key=f"skip_{step.id}"):
                                mark_step(step.id, "skipped")

                # Retry button for failed AUTO steps
                if status == "failed" and step.category == "AUTO" and satisfied:
                    if st.button("▶ Retry", key=f"retry_{step.id}", type="primary"):
                        st.session_state.active_run_id = step.id
                        st.rerun()

            # Persisted output from the last run, so it doesn't vanish on rerun.
            if ss.get("output"):
                with st.expander("Output", expanded=(status == "failed")):
                    st.code(ss["output"], language=None)

            # Run at full expander width, not squeezed into the narrow button column.
            if st.session_state.get("active_run_id") == step.id:
                run_step(step)

    st.divider()
