from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

import gradio as gr


BASE_DIR = Path(__file__).resolve().parent  # frontend/
PROJECT_ROOT = BASE_DIR.parent  # lol_radar_charts/

RADAR_CHARTS_DIR = (PROJECT_ROOT / "radar_charts").resolve()
MAIN_PY = (PROJECT_ROOT / "backend" / "main.py").resolve()

DEFAULT_POSITIONS = ["Top", "Jug", "Mid", "Bot", "Sup"]


def _latest_png_path() -> Path | None:
    if not RADAR_CHARTS_DIR.exists():
        return None
    pngs = list(RADAR_CHARTS_DIR.glob("*.png"))
    if not pngs:
        return None
    return max(pngs, key=lambda p: p.stat().st_mtime)


def _generate(tournament_id: str, position: str) -> tuple[str | None, str]:
    tournament_id = (tournament_id or "").strip()
    position = (position or "").strip()

    if not tournament_id:
        return None, "请输入 tournament_id"
    if not position:
        return None, "请输入 position（Top / Jug / Mid / Bot / Sup）"

    if not MAIN_PY.exists():
        return None, f"未找到 backend/main.py：{MAIN_PY}"

    RADAR_CHARTS_DIR.mkdir(parents=True, exist_ok=True)

    latest_before_mtime = 0.0
    for p in RADAR_CHARTS_DIR.glob("*.png"):
        try:
            latest_before_mtime = max(latest_before_mtime, p.stat().st_mtime)
        except OSError:
            pass

    start_ts = time.time()
    try:
        proc = subprocess.run(
            [
                sys.executable,
                str(MAIN_PY),
                "-t",
                tournament_id,
                "-p",
                position,
            ],
            cwd=str(MAIN_PY.parent),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=300,
        )
    except subprocess.TimeoutExpired:
        return None, "main.py 执行超时（300 秒）"
    except Exception as e:
        return None, f"运行失败：{e}"

    elapsed = time.time() - start_ts

    if proc.returncode != 0:
        msg = "main.py 失败"
        if proc.stdout or proc.stderr:
            msg += "\n" + "stdout/stderr（尾部）:\n"
            msg += (proc.stdout or "")[-2000:]
            msg += "\n"
            msg += (proc.stderr or "")[-2000:]
        msg += f"\n耗时：{elapsed:.1f}s"
        return None, msg

    candidates: list[Path] = []
    for p in RADAR_CHARTS_DIR.glob("*.png"):
        try:
            if p.stat().st_mtime > (latest_before_mtime + 0.01):
                candidates.append(p)
        except OSError:
            pass

    if not candidates:
        # 可能是 position 不合法或请求失败
        latest = _latest_png_path()
        hint = f"（未发现新 PNG。最新一张：{latest.name if latest else 'None'}）"
        msg = "未生成新图片（可能 position 不合法或请求失败）。" + hint
        msg += "\nstdout/stderr（尾部）:\n"
        msg += (proc.stdout or "")[-2000:]
        msg += "\n"
        msg += (proc.stderr or "")[-2000:]
        msg += f"\n耗时：{elapsed:.1f}s"
        return None, msg

    latest = max(candidates, key=lambda p: p.stat().st_mtime)
    status = f"生成成功：{latest.name}\n耗时：{elapsed:.1f}s"
    return str(latest), status


def build_demo() -> gr.Blocks:
    with gr.Blocks(title="LOL Radar Charts") as demo:
        gr.Markdown("# LOL_Radar_charts 雷达图生成")
        gr.Markdown(
            "输入 `tournament_id` 和 `position` 后，点击“生成”，会调用 `backend/main.py` "
            "抓取数据并生成最新一张 PNG。"
        )

        with gr.Row():
            with gr.Column(scale=1):
                tournament_id = gr.Textbox(
                    label="tournament_id",
                    placeholder="例如：1374",
                )
                position = gr.Dropdown(
                    label="position",
                    choices=DEFAULT_POSITIONS,
                    value="Top",
                    multiselect=False,
                )
                run_btn = gr.Button("生成")
                status = gr.Textbox(label="状态", interactive=False)

            with gr.Column(scale=1):
                image = gr.Image(label="雷达图", type="filepath")

        run_btn.click(
            fn=_generate,
            inputs=[tournament_id, position],
            outputs=[image, status],
        )

    # 不同版本 Gradio 的 queue 参数不完全一致，这里用兼容写法。
    demo.queue()
    return demo


def main() -> None:
    parser = argparse.ArgumentParser(description="Gradio 前端：生成 OP.GG 雷达图 PNG")
    parser.add_argument("--server-name", default="127.0.0.1")
    parser.add_argument("--server-port", type=int, default=8000)
    args = parser.parse_args()

    demo = build_demo()
    demo.launch(
        server_name=args.server_name,
        server_port=args.server_port,
        share=False,
        prevent_thread_lock=True,
    )

    # 让 CLI 不立即退出
    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()

