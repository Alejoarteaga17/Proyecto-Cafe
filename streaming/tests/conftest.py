import sys
from pathlib import Path


STREAMING_ROOT = Path(__file__).resolve().parents[1]
if str(STREAMING_ROOT) not in sys.path:
    sys.path.insert(0, str(STREAMING_ROOT))
