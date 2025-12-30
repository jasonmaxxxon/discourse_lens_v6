#!/usr/bin/env python3
import datetime
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
VERSION_FILE = ROOT / "version.py"
CHANGELOG = ROOT / "CHANGELOG.md"


def read_version() -> str:
    ns = {}
    exec(VERSION_FILE.read_text(encoding="utf-8"), ns)
    return ns.get("version") or ns.get("__version__", "0.0.0")


def git_log(limit: int = 30) -> list[str]:
    try:
        output = subprocess.check_output(
            ["git", "log", f"-n{limit}", "--pretty=format:%s", "--no-merges"],
            cwd=ROOT,
        )
        lines = output.decode().splitlines()
        return [f"- {line}" for line in lines if line.strip()]
    except Exception as e:
        return [f"- (log unavailable: {e})"]


def write_changelog(version: str, entries: list[str]):
    today = datetime.date.today().isoformat()
    header = f"## v{version} ({today})"
    body = "\n".join(entries) if entries else "- No changes recorded."
    existing = ""
    if CHANGELOG.exists():
        existing = CHANGELOG.read_text(encoding="utf-8").strip()
    content = f"{header}\n{body}\n\n{existing}".strip() + "\n"
    CHANGELOG.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    ver = read_version()
    logs = git_log()
    write_changelog(ver, logs)
    print(f"Wrote CHANGELOG for v{ver}")
