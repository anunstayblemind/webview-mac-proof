"""Print the result files in full, then exit non-zero if any required check missed or a file is absent."""
import json
import os
import sys

bad = 0
for path in sys.argv[1:]:
    print("=" * 20, path)
    if not os.path.exists(path):
        print("MISSING: this run wrote no result file")
        bad += 1
        continue
    with open(path, encoding="utf-8") as f:
        text = f.read()
    print(text)
    d = json.loads(text)
    if d.get("misses"):
        bad += 1
    p = d.get("page") or {}
    print(f"SUMMARY {path}: misses={d.get('misses')} frames={p.get('rafFrames')} "
          f"gap_avg_ms={p.get('frameGapAvgMs')} gap_worst_ms={p.get('frameGapWorstMs')} font={p.get('fontCheck')} "
          f"audio_running={d.get('audio_running')} audio={p.get('audio')} blur={p.get('backdropFilter')} "
          f"webgl={p.get('webgl')} renderer={d.get('renderer')} os={d.get('platform')} {d.get('machine')}")
sys.exit(1 if bad else 0)
