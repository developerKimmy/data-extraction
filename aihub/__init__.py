"""sys.path에 data_extraction/ 추가."""
import sys
from pathlib import Path

_PARENT = str(Path(__file__).resolve().parent.parent)  # data_extraction/
if _PARENT not in sys.path:
    sys.path.insert(0, _PARENT)
