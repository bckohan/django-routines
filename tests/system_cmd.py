#!/usr/bin/env python
from tests import track_file
import json
import sys

if __name__ == "__main__":
    if not track_file.is_file():
        track_file.write_text(json.dumps({"invoked": [], "passed_options": []}))
    track = json.loads(track_file.read_text())
    track["invoked"].append(sys.argv[-1])
    track_file.write_text(json.dumps(track))
