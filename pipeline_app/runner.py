import subprocess


def run_step_streaming(step, extra_args=None):
    """
    Run a step's command as a subprocess.
    Yields (line: str, returncode: int | None) tuples.
    returncode is None for every line except the final sentinel.
    """
    cmd = step.resolved_cmd()
    if cmd and extra_args:
        cmd = cmd + list(extra_args)
    if not cmd:
        yield ("[No command defined for this step]\n", 1)
        return

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=step.resolved_cwd(),
            env=step.resolved_env(),
            encoding="utf-8",
            errors="replace",
        )
        for line in iter(process.stdout.readline, ""):
            yield (line, None)
        process.wait()
        yield (f"\n[Process exited with code {process.returncode}]\n", process.returncode)
    except FileNotFoundError as e:
        yield (f"[Error — executable not found: {e}]\n", 1)
    except Exception as e:
        yield (f"[Unexpected error: {e}]\n", 1)
