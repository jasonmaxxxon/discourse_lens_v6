#!/usr/bin/env python3
import subprocess
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
BUMP = ROOT / "tools" / "bump_version.py"
CHANGELOG = ROOT / "tools" / "gen_changelog.py"


def run(cmd: list[str]):
    subprocess.check_call(cmd, cwd=ROOT)


def main():
    # Stage everything first
    run(["git", "add", "-A"])

    # Bump version and regenerate changelog
    run([sys.executable, str(BUMP)])
    run([sys.executable, str(CHANGELOG)])

    # Stage generated files
    run(["git", "add", "-A"])

    # Commit if there is any change
    diff = subprocess.call(["git", "diff", "--cached", "--quiet"], cwd=ROOT)
    if diff == 0:
        print("No changes to commit.")
        return

    run(["git", "commit", "-m", "auto: updated files"])

    # Push
    try:
        run(["git", "push"])
    except subprocess.CalledProcessError as e:
        print(f"Push failed: {e}")


if __name__ == "__main__":
    main()
