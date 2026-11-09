#!/usr/bin/env bash
set -euo pipefail

python3 -m compileall -q batch/src batch/glue streaming/streaming_src streaming/glue
python3 -m pytest -q batch/tests streaming/tests
python3 - <<'PY'
from html.parser import HTMLParser
from pathlib import Path

html = Path("frontend/index.html").read_text(encoding="utf-8")
HTMLParser().feed(html)
print("frontend/index.html: valid HTML")

PY
node - <<'JS'
const fs = require('fs');
const html = fs.readFileSync('frontend/index.html', 'utf8');
const match = html.match(/<script>([\s\S]*?)<\/script>/);
if (!match) throw new Error('frontend/index.html: inline JavaScript not found');
new Function(match[1]);
console.log('frontend/index.html: valid JavaScript');
JS
python3 - <<'PY'
from html.parser import HTMLParser
from pathlib import Path

class AccessibilityParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.references = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if "id" in attributes:
            self.ids.add(attributes["id"])
        for name in ("aria-labelledby", "aria-controls", "aria-describedby"):
            if name in attributes:
                self.references.extend(attributes[name].split())

parser = AccessibilityParser()
parser.feed(Path("frontend/index.html").read_text(encoding="utf-8"))
missing = sorted(set(parser.references) - parser.ids)
if missing:
    raise SystemExit(f"frontend/index.html: missing ARIA references: {missing}")
print("frontend/index.html: ARIA references valid")
PY
git diff --check
