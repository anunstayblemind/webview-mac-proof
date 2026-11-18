"""Print the result files in full. Exit non-zero if a REQUIRED file (the built app, name contains "app") missed a
check or is absent. Runs from source are printed and summarised but do not decide the job: the app is what ships."""
import json
import os
import sys

bad = 0
for path in sys.argv[1:]:
    print("=" * 20, path)
    required = "app" in os.path.basename(path)
    if not os.path.exists(path):
        print("MISSING: this run wrote no result file")
        bad += required
        continue
    with open(path, encoding="utf-8") as f:
        text = f.read()
    print(text)
    d = json.loads(text)
    if d.get("misses"):
        bad += required
    p = d.get("page") or {}
    origin = (p.get("timeOriginMs") - d["t0_epoch_ms"]) / 1000 if p.get("timeOriginMs") and d.get("t0_epoch_ms") else None
    print(f"TIMING {path}: variant={d.get('variant')} create_s={d.get('create_s')} start_called_s={d.get('start_called_s')} "
          f"shown_s={d.get('shown_s')} navigation_began_s={origin} loaded_s={d.get('loaded_s')} "
          f"getfqdn={d.get('getfqdn_calls')} requests={d.get('requests')} nav={p.get('nav')} resources={p.get('resources')}")
    print(f"SUMMARY {path}: misses={d.get('misses')} frames={p.get('rafFrames')} "
          f"gap_avg_ms={p.get('frameGapAvgMs')} gap_worst_ms={p.get('frameGapWorstMs')} font={p.get('fontCheck')} "
          f"audio_running={d.get('audio_running')} audio={p.get('audio')} blur={p.get('backdropFilter')} "
          f"webgl={p.get('webgl')} renderer={d.get('renderer')} shown_s={d.get('shown_s')} loaded_s={d.get('loaded_s')} "
          f"total_s={d.get('seconds_to_result')} required={required} os={d.get('platform')} {d.get('machine')}")
sys.exit(1 if bad else 0)
