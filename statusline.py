#!/usr/bin/env python3
"""Claude Code status line: branch (+worktree) | model | effort | ctx%"""
import json
import os
import subprocess
import sys


def run_git(cwd: str, *args: str) -> str:
    try:
        r = subprocess.run(
            ["git", *args], cwd=cwd, capture_output=True, text=True, timeout=1
        )
        return r.stdout.strip() if r.returncode == 0 else ""
    except Exception:
        return ""


def read_effort(cwd: str) -> str:
    candidates = [
        os.path.join(cwd, ".claude", "settings.local.json"),
        os.path.join(cwd, ".claude", "settings.json"),
        os.path.expanduser("~/.claude/settings.local.json"),
        os.path.expanduser("~/.claude/settings.json"),
    ]
    for path in candidates:
        try:
            with open(path) as f:
                effort = json.load(f).get("effortLevel")
                if effort:
                    return effort
        except (OSError, json.JSONDecodeError):
            continue
    return ""


def main() -> None:
    data = json.load(sys.stdin)

    model = (data.get("model") or {}).get("display_name") or "?"

    ctx = data.get("context_window") or {}
    pct = ctx.get("used_percentage")
    ctx_str = f"{int(pct)}%" if pct is not None else "?"

    cwd = (
        (data.get("workspace") or {}).get("current_dir")
        or data.get("cwd")
        or os.getcwd()
    )

    branch = run_git(cwd, "branch", "--show-current")

    wt = data.get("worktree") or {}
    workspace_wt = (data.get("workspace") or {}).get("git_worktree")
    is_worktree = bool(wt) or bool(workspace_wt)
    if not is_worktree and branch:
        git_dir = run_git(cwd, "rev-parse", "--git-dir")
        is_worktree = "/worktrees/" in git_dir

    effort = read_effort(cwd)

    parts = []
    if branch:
        parts.append(f"{branch} (worktree)" if is_worktree else branch)
    elif is_worktree:
        parts.append("(worktree)")
    parts.append(model)
    if effort:
        parts.append(f"effort:{effort}")
    parts.append(f"ctx:{ctx_str}")

    print(" | ".join(parts), end="")


if __name__ == "__main__":
    main()
