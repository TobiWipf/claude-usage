#!/usr/bin/env python3
"""Claude Code status line: branch (+worktree) | model | effort | ctx%

Theme selection: set CLAUDE_STATUSLINE_THEME to one of:
  default, mono, dracula, nord, solarized, vivid
Set NO_COLOR=1 to force plain output.
"""
import json
import os
import subprocess
import sys

RESET = "\033[0m"
BOLD = "\033[1m"


def _fg(r: int, g: int, b: int) -> str:
    return f"\033[38;2;{r};{g};{b}m"


def _fg256(n: int) -> str:
    return f"\033[38;5;{n}m"


THEMES = {
    "default": {
        "branch":   _fg256(110),
        "worktree": _fg256(214),
        "model":    _fg256(140),
        "effort":   _fg256(108),
        "label":    _fg256(244),
        "sep":      _fg256(240),
        "ctx_low":  _fg256(108),
        "ctx_med":  _fg256(214),
        "ctx_high": _fg256(203),
    },
    "mono": {k: "" for k in (
        "branch", "worktree", "model", "effort",
        "label", "sep", "ctx_low", "ctx_med", "ctx_high",
    )},
    "dracula": {
        "branch":   _fg(139, 233, 253),
        "worktree": _fg(255, 184, 108),
        "model":    _fg(189, 147, 249),
        "effort":   _fg(80, 250, 123),
        "label":    _fg(98, 114, 164),
        "sep":      _fg(68, 71, 90),
        "ctx_low":  _fg(80, 250, 123),
        "ctx_med":  _fg(241, 250, 140),
        "ctx_high": _fg(255, 85, 85),
    },
    "nord": {
        "branch":   _fg(136, 192, 208),
        "worktree": _fg(235, 203, 139),
        "model":    _fg(180, 142, 173),
        "effort":   _fg(163, 190, 140),
        "label":    _fg(76, 86, 106),
        "sep":      _fg(76, 86, 106),
        "ctx_low":  _fg(163, 190, 140),
        "ctx_med":  _fg(235, 203, 139),
        "ctx_high": _fg(191, 97, 106),
    },
    "solarized": {
        "branch":   _fg(38, 139, 210),
        "worktree": _fg(181, 137, 0),
        "model":    _fg(108, 113, 196),
        "effort":   _fg(133, 153, 0),
        "label":    _fg(147, 161, 161),
        "sep":      _fg(147, 161, 161),
        "ctx_low":  _fg(133, 153, 0),
        "ctx_med":  _fg(181, 137, 0),
        "ctx_high": _fg(220, 50, 47),
    },
    "vivid": {
        "branch":   _fg(0, 200, 255),
        "worktree": _fg(255, 165, 0),
        "model":    _fg(200, 100, 255),
        "effort":   _fg(0, 230, 120),
        "label":    _fg(150, 150, 150),
        "sep":      _fg(90, 90, 90),
        "ctx_low":  _fg(0, 230, 120),
        "ctx_med":  _fg(255, 200, 0),
        "ctx_high": _fg(255, 60, 60),
    },
}


def pick_theme() -> dict:
    if os.environ.get("NO_COLOR"):
        return THEMES["mono"]
    name = os.environ.get("CLAUDE_STATUSLINE_THEME", "default").lower()
    return THEMES.get(name, THEMES["default"])


def ctx_color(theme, pct):
    if pct is None:
        return theme["label"]
    if pct < 50:
        return theme["ctx_low"]
    if pct < 80:
        return theme["ctx_med"]
    return theme["ctx_high"]


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


def paint(color, text, bold=False):
    prefix = (BOLD if bold else "") + (color or "")
    return f"{prefix}{text}{RESET}" if prefix else text


def main() -> None:
    data = json.load(sys.stdin)
    theme = pick_theme()

    model = (data.get("model") or {}).get("display_name") or "?"

    ctx = data.get("context_window") or {}
    pct = ctx.get("used_percentage")
    pct_int = int(pct) if pct is not None else None
    pct_str = f"{pct_int}%" if pct_int is not None else "?"

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

    sep = f" {paint(theme['sep'], '|')} "
    parts = []
    if branch:
        seg = paint(theme["branch"], branch, bold=True)
        if is_worktree:
            seg += " " + paint(theme["worktree"], "(worktree)", bold=True)
        parts.append(seg)
    elif is_worktree:
        parts.append(paint(theme["worktree"], "(worktree)", bold=True))
    parts.append(paint(theme["model"], model, bold=True))
    if effort:
        parts.append(
            paint(theme["label"], "effort:")
            + paint(theme["effort"], effort, bold=True)
        )
    parts.append(
        paint(theme["label"], "ctx:")
        + paint(ctx_color(theme, pct_int), pct_str, bold=True)
    )

    print(sep.join(parts), end="")


if __name__ == "__main__":
    main()
