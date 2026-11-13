from __future__ import annotations
import json, os, shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE, DOCS = ROOT / "radar_charts", ROOT / "docs"
ASSETS, DATA = DOCS / "assets", DOCS / "data"
ROLE_ORDER = ["Top", "Jug", "Mid", "Bot", "Sup"]
ROLE_NAMES = {"Top":"上单","Jug":"打野","Mid":"中单","Bot":"ADC","Sup":"辅助"}
TOURNAMENT_NAMES = {
 "1353":"2026 LCK Split1 Group Stage","1354":"2026 LPL Split1 Group Stage",
 "1360":"2026 LCK Split1 Play-In","1372":"2026 LPL Split1 Playoffs",
 "1359":"2026 LCK Split1 Playoffs","1374":"2026 First-Stand Playoffs",
 "1375":"2026 First-Stand Group A","1376":"2026 First-Stand Group B",
 "1443":"2026 Worlds Knockout"
}
def main():
    tournament_id = os.environ.get("TOURNAMENT_ID", "1443")
    generated_at = datetime.now(timezone.utc).isoformat()
    ASSETS.mkdir(parents=True, exist_ok=True); DATA.mkdir(parents=True, exist_ok=True)
    for old in ASSETS.glob("*.png"): old.unlink()
    charts = []
    for role in ROLE_ORDER:
        matches = sorted(SOURCE.glob(f"*_{role}.png"), key=lambda p:p.stat().st_mtime, reverse=True)
        if not matches: continue
        source = matches[0]; target = ASSETS / f"{role.lower()}-radar.png"
        shutil.copy2(source, target)
        charts.append({"role":role,"roleName":ROLE_NAMES[role],"image":f"./assets/{target.name}","count":40,"generatedAt":generated_at,"filename":source.name})
    manifest = {"tournamentId":tournament_id,"tournamentName":TOURNAMENT_NAMES.get(tournament_id,f"Tournament {tournament_id}"),"generatedAt":generated_at,"recordsPerPosition":40,"charts":charts}
    (DATA / "charts.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Website manifest generated: {len(charts)} charts for tournament {tournament_id}")
if __name__ == "__main__": main()
