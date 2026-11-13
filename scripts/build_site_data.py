from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend" / "main.py"
DOCS = ROOT / "docs"
ASSETS = DOCS / "assets"
DATA = DOCS / "data"
TEMP = ROOT / "radar_charts" / "_catalog_tmp"

TOURNAMENTS = [
    {"id":"1353","name":"2026 LCK Cup Group Stage","group":"LCK"},
    {"id":"1354","name":"2026 LPL Split1 Group Stage","group":"LPL"},
    {"id":"1360","name":"2026 LCK Cup Play-In","group":"LCK"},
    {"id":"1372","name":"2026 LPL Split1 Playoffs","group":"LPL"},
    {"id":"1359","name":"2026 LCK Cup Playoffs","group":"LCK"},
    {"id":"1374","name":"2026 First-Stand Playoffs","group":"国际赛事"},
    {"id":"1375","name":"2026 First-Stand Group A","group":"国际赛事"},
    {"id":"1376","name":"2026 First-Stand Group B","group":"国际赛事"},
    {"id":"1392","name":"2026 LPL Split2 Group Ascend","group":"LPL"},
    {"id":"1393","name":"2026 LPL Split2 Group Nirvana","group":"LPL"},
    {"id":"1386","name":"2026 LCK Round 1–2","group":"LCK"},
    {"id":"1442","name":"2026 Worlds Swiss Stage","group":"国际赛事"},
    {"id":"1443","name":"2026 Worlds Knockout","group":"国际赛事"},
    {"id":"1444","name":"2026 Worlds Play-In","group":"国际赛事"},
]
ROLES = ["Top", "Jug", "Mid", "Bot", "Sup"]
ROLE_NAMES = {"Top":"上单","Jug":"打野","Mid":"中单","Bot":"ADC","Sup":"辅助"}

def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    DATA.mkdir(parents=True, exist_ok=True)
    TEMP.mkdir(parents=True, exist_ok=True)
    for old in ASSETS.glob("*.png"):
        old.unlink()

    generated_at = datetime.now(timezone.utc).isoformat()
    catalog = []
    total_ok = 0

    for tournament in TOURNAMENTS:
        event = {**tournament, "roles": {}}
        print(f"\n{'='*72}\n赛事：{tournament['name']} | ID={tournament['id']}\n{'='*72}", flush=True)
        for role in ROLES:
            work_dir = TEMP / f"{tournament['id']}_{role}"
            if work_dir.exists():
                shutil.rmtree(work_dir)
            work_dir.mkdir(parents=True)
            env = os.environ.copy()
            env["RADAR_CHARTS_DIR"] = str(work_dir)
            command = [sys.executable, str(BACKEND), "--tournament", tournament["id"], "--position", role]
            try:
                result = subprocess.run(command, cwd=ROOT, env=env, text=True, capture_output=True, timeout=50)
                output = (result.stdout or "") + (result.stderr or "")
                print(output[-3500:], flush=True)
                files = sorted(work_dir.glob("*.png"), key=lambda p: p.stat().st_mtime, reverse=True)
                if result.returncode == 0 and files:
                    target_name = f"{tournament['id']}-{role.lower()}-radar.png"
                    target = ASSETS / target_name
                    shutil.copy2(files[0], target)
                    match = re.search(r"该位置选手数量:\s*(\d+)", output)
                    count = int(match.group(1)) if match else None
                    event["roles"][role] = {
                        "available": True,
                        "image": f"./assets/{target_name}",
                        "count": count,
                        "label": ROLE_NAMES[role],
                    }
                    total_ok += 1
                    print(f"[OK] {tournament['id']} {role}: {count if count is not None else '图表已生成'} 名选手", flush=True)
                else:
                    event["roles"][role] = {"available": False, "image": None, "count": 0, "label": ROLE_NAMES[role]}
                    print(f"[NO DATA] {tournament['id']} {role}: 未生成图表", flush=True)
            except subprocess.TimeoutExpired:
                event["roles"][role] = {"available": False, "image": None, "count": 0, "label": ROLE_NAMES[role]}
                print(f"[TIMEOUT] {tournament['id']} {role}", flush=True)
            finally:
                shutil.rmtree(work_dir, ignore_errors=True)
        event["availableRoles"] = [r for r in ROLES if event["roles"][r]["available"]]
        catalog.append(event)

    manifest = {
        "generatedAt": generated_at,
        "tournamentCount": len(catalog),
        "roleCount": len(ROLES),
        "successfulCharts": total_ok,
        "tournaments": catalog,
    }
    (DATA / "catalog.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\nCATALOG COMPLETE: {total_ok}/{len(TOURNAMENTS)*len(ROLES)} charts generated.", flush=True)

if __name__ == "__main__":
    main()
