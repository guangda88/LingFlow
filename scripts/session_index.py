#!/usr/bin/env python3
"""Scan all Crush CLI session JSONL files and generate a browsable index.

Usage:
    python scripts/session_index.py              # Full index, sorted by date
    python scripts/session_index.py --recent 10  # Last 10 sessions
    python scripts/session_index.py --project LingFlow  # Filter by project
    python scripts/session_index.py --json       # Output as JSON
"""

import argparse
import json
from datetime import datetime
from pathlib import Path


SESSIONS_ROOT = Path.home() / ".claude" / "projects"


def extract_project_name(dir_name: str) -> str:
    """Convert '-home-ai-LingFlow' to 'LingFlow'."""
    parts = dir_name.lstrip("-").split("-")
    # Skip 'home', 'ai' prefix
    if len(parts) > 2 and parts[0] == "home" and parts[1] == "ai":
        return "-".join(parts[2:])
    return dir_name


def parse_session(jsonl_path: Path, project_dir: str) -> dict | None:
    """Parse a session JSONL file and extract metadata."""
    try:
        stat = jsonl_path.stat()
        first_user_msg = ""
        msg_count = 0
        model = ""

        with open(jsonl_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    msg = json.loads(line)
                except json.JSONDecodeError:
                    continue

                msg_count += 1
                role = msg.get("role", "")

                if role == "user" and not first_user_msg:
                    content = msg.get("content", "")
                    if isinstance(content, list):
                        text_parts = [
                            p.get("text", "") for p in content if isinstance(p, dict) and p.get("type") == "text"
                        ]
                        first_user_msg = " ".join(text_parts)[:200]
                    elif isinstance(content, str):
                        first_user_msg = content[:200]

                if role == "assistant" and not model:
                    model = msg.get("model", "")

        if msg_count == 0:
            return None

        created = datetime.fromtimestamp(stat.st_ctime)
        modified = datetime.fromtimestamp(stat.st_mtime)

        return {
            "project": extract_project_name(project_dir),
            "project_dir": project_dir,
            "file": str(jsonl_path),
            "session_id": jsonl_path.stem,
            "created": created.isoformat(),
            "modified": modified.isoformat(),
            "size_kb": round(stat.st_size / 1024, 1),
            "messages": msg_count,
            "first_user_msg": first_user_msg[:120].replace("\n", " "),
            "model": model,
        }
    except Exception:
        return None


def scan_all_sessions() -> list[dict]:
    """Scan all projects for session files."""
    sessions = []

    if not SESSIONS_ROOT.exists():
        return sessions

    for project_dir in sorted(SESSIONS_ROOT.iterdir()):
        if not project_dir.is_dir():
            continue

        for jsonl_file in sorted(project_dir.glob("*.jsonl")):
            session = parse_session(jsonl_file, project_dir.name)
            if session:
                sessions.append(session)

    sessions.sort(key=lambda s: s["modified"], reverse=True)
    return sessions


def print_table(sessions: list[dict]):
    """Print sessions as a formatted table."""
    if not sessions:
        print("No sessions found.")
        return

    print(f"{'Date':<12} {'Project':<25} {'Size':>8} {'Msgs':>6}  {'First Message'}")
    print("-" * 120)

    for s in sessions:
        date = s["modified"][:10]
        project = s["project"][:24]
        size = f"{s['size_kb']}KB" if s["size_kb"] < 1024 else f"{s['size_kb']/1024:.1f}MB"
        print(f"{date:<12} {project:<25} {size:>8} {s['messages']:>6}  {s['first_user_msg'][:60]}")


def main():
    parser = argparse.ArgumentParser(description="Crush CLI Session Index")
    parser.add_argument("--recent", type=int, help="Show last N sessions")
    parser.add_argument("--project", type=str, help="Filter by project name")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--min-size", type=int, help="Minimum size in KB")
    args = parser.parse_args()

    sessions = scan_all_sessions()

    if args.project:
        sessions = [s for s in sessions if args.project.lower() in s["project"].lower()]
    if args.min_size:
        sessions = [s for s in sessions if s["size_kb"] >= args.min_size]
    if args.recent:
        sessions = sessions[: args.recent]

    if args.json:
        print(json.dumps(sessions, indent=2, ensure_ascii=False))
    else:
        print(f"\n=== Crush CLI Session Index ({len(sessions)} sessions) ===\n")
        print_table(sessions)
        print(f"\nTotal: {len(sessions)} sessions in {SESSIONS_ROOT}")


if __name__ == "__main__":
    main()
