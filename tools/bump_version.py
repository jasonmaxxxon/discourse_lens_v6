#!/usr/bin/env python3
import pathlib
import re

VERSION_FILE = pathlib.Path(__file__).resolve().parent.parent / "version.py"
VERSION_PATTERN = re.compile(r'^__?version__?\s*=\s*["\'](\d+)\.(\d+)\.(\d+)["\']\s*$')


def read_version() -> tuple[int, int, int]:
    content = VERSION_FILE.read_text(encoding="utf-8").splitlines()
    for line in content:
        m = VERSION_PATTERN.match(line.strip())
        if m:
            return tuple(int(x) for x in m.groups())
    raise ValueError("Version string not found in version.py")


def write_version(major: int, minor: int, patch: int) -> str:
    new_version = f"{major}.{minor}.{patch}"
    VERSION_FILE.write_text(
        f'version = "{new_version}"\n__version__ = "{new_version}"\n',
        encoding="utf-8",
    )
    return new_version


def bump_patch() -> str:
    major, minor, patch = read_version()
    patch += 1
    return write_version(major, minor, patch)


if __name__ == "__main__":
    new_ver = bump_patch()
    print(new_ver)
