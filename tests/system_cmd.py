#!/usr/bin/env python
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from tests import track_file
import json


if __name__ == "__main__":
    if not track_file.is_file():
        track_file.write_text(
            json.dumps({"invoked": [], "passed_options": []}, indent=4)
        )
    track = json.loads(track_file.read_text())
    track["invoked"].append(sys.argv[-1])
    track_file.write_text(json.dumps(track, indent=4))
    if len(sys.argv) > 1:
        print(sys.argv[-1])
