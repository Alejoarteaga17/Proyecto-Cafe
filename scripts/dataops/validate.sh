#!/usr/bin/env bash
set -euo pipefail

python3 -m compileall -q batch/src batch/glue streaming/streaming_src streaming/glue
python3 -m pytest -q batch/tests streaming/tests
python3 - <<'PY'
from html.parser import HTMLParser
from pathlib import Path

HTMLParser().feed(Path("frontend/index.html").read_text(encoding="utf-8"))
print("frontend/index.html: valid HTML")
PY
git diff --check
