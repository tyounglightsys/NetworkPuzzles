"""Print an Android versionCode derived from network_puzzles.__version__.

Layout: MMmmppSS (major, minor, patch, stage), e.g. 0.1.0rc1 -> 10051.
Stage digits: alpha 10-29, beta 30-49, rc 50-89, final 99,
so every pre-release sorts below its final release.
"""

import re
import sys
from pathlib import Path

from packaging.version import Version

VERSION_FILE = Path(__file__).resolve().parents[1] / "src/network_puzzles/__init__.py"
STAGE_BASE = {"a": 10, "b": 30, "rc": 50}
STAGE_MAX = {"a": 29, "b": 49, "rc": 89}


def version_code(version_str: str) -> int:
    v = Version(version_str)  # normalizes "0.1.0-rc.1" -> 0.1.0rc1
    if v.dev is not None or v.post is not None or v.local is not None:
        sys.exit(f"Unsupported version for Android release: {v}")
    major, minor, patch = (list(v.release) + [0, 0, 0])[:3]
    if minor > 99 or patch > 99:
        sys.exit(f"minor/patch must be <= 99: {v}")
    if v.pre is None:
        stage = 99
    else:
        kind, num = v.pre
        stage = STAGE_BASE[kind] + num
        if stage > STAGE_MAX[kind]:
            sys.exit(f"Pre-release number too large: {v}")
    return major * 1_000_000 + minor * 10_000 + patch * 100 + stage


if __name__ == "__main__":
    if len(sys.argv) > 1:
        version = sys.argv[1]
    else:
        text = VERSION_FILE.read_text(encoding="utf-8")
        version = re.search(r"""__version__\s*=\s*["']([^"']+)["']""", text).group(1)
    print(version_code(version))