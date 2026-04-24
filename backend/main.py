"""
从 OP.GG 拉取赛事选手数据并生成分位置雷达图，图片保存到脚本同目录下的 radar_charts 文件夹。
"""

from __future__ import annotations

import argparse
import math
from datetime import datetime
from pathlib import Path

# Gradio/脚本运行时避免弹出 Matplotlib figure 窗口
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
from sklearn.preprocessing import MinMaxScaler

# 与项目根目录同级的 radar_charts 目录（会自动创建）
# backend/main.py -> backend -> project root -> radar_charts
RADAR_CHARTS_DIR = Path(__file__).resolve().parent.parent / "radar_charts"


def get_all_fields(data, prefix="", fields=None):
    if fields is None:
        fields = []
    if isinstance(data, dict):
        for key, value in data.items():
            new_prefix = f"{prefix}.{key}" if prefix else key
            if isinstance(value, (dict, list)):
                get_all_fields(value, new_prefix, fields)
            else:
                fields.append(new_prefix)
    elif isinstance(data, list) and data:
        get_all_fields(data[0], prefix, fields)
    return fields


def extract_data(items):
    rows = []
    for item in items:

        def extract_values(data, prefix="", result=None):
            if result is None:
                result = {}
            if isinstance(data, dict):
                for key, value in data.items():
                    new_prefix = f"{prefix}.{key}" if prefix else key
                    if isinstance(value, (dict, list)):
                        extract_values(value, new_prefix, result)
                    else:
                        result[new_prefix] = value
            elif isinstance(data, list) and data:
                extract_values(data[0], prefix, result)
            return result

        item_values = extract_values(item)
        rows.append(item_values)
    return rows


def generate_special_lol_players_radar_charts(
    tournamentId,
    Position,
    img_name,
    title,
    categories,
    save_dir: Path | str | None = None,
):
    """
    save_dir: 默认使用 RADAR_CHARTS_DIR；可传入自定义路径。
    """

    out_dir = Path(save_dir) if save_dir is not None else RADAR_CHARTS_DIR

    url = "https://esports.op.gg/matches/graphql/__query__ListPlayerStatisticsByTournament"
    headers = {
        "authority": "esports.op.gg",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "Apollo-Require-Preflight": "true",
        "Content-Type": "application/json",
        "Origin": "https://esports.op.gg",
        "Referer": "https://esports.op.gg/stats/player",
        "Sec-Ch-Ua": '"Not:A-Brand";v="99", "Microsoft Edge";v="145", "Chromium";v="145"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36 Edg/145.0.0.0",
    }

    query = """
    query PlayerStatisticsByTournament($tournamentId: ID!) {
      playerStatisticsByTournament(tournamentId: $tournamentId) {
        player {
          id
          nickName
          firstName
          lastName
        }
        team {
          acronym
        }
        position
        games
        wins
        loses
        winRate
        kda
        kills
        deaths
        assists
        firstBlood
        firstTower
        dpm
        dtpm
        gpm
        cspm
        dpgr
        wardsPlaced
        wardsKilled
      }
    }
    """

    variables = {"tournamentId": f"{tournamentId}"}

    payload = {"query": query, "variables": variables}
    result = None
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)

        if response.status_code == 200:
            result = response.json()

            if "errors" in result:
                print("API返回错误:", result["errors"])
            else:
                print("数据爬取成功")
                print(
                    "获取到的数据数量:",
                    len(result.get("data", {}).get("playerStatisticsByTournament", [])),
                )
        else:
            print(f"请求失败，状态码: {response.status_code}")
            print("响应内容:", response.text)

    except Exception as e:
        print(f"爬取过程中发生错误: {str(e)}")
        return

    if result is None or "data" not in result:
        print("无有效数据，终止绘图。")
        return

    json_data = result
    all_fields = []
    get_all_fields(
        json_data["data"]["playerStatisticsByTournament"], fields=all_fields
    )
    all_fields = list(set(all_fields))
    rows = extract_data(json_data["data"]["playerStatisticsByTournament"])

    df = pd.DataFrame(rows, columns=all_fields)

    df.columns = df.columns.str.strip().str.replace(" ", "_")
    df = df.rename(
        columns={
            "position": "Position",
            "winRate": "Winning_Rate",
            "kda": "KDA",
            "kills": "Kills",
            "deaths": "Deaths",
            "assists": "Assists",
            "firstBlood": "First_Blood",
            "firstTower": "First_Turret",
            "dpm": "DPM",
            "dtpm": "DTPM",
            "gpm": "GPM",
            "cspm": "CSPM",
            "dpgr": "DPGR",
            "wardsPlaced": "Vision_Score",
            "wardsKilled": "Denied_Vision_Score",
        }
    )
    df["Name"] = (
        df["team.acronym"].str.strip() + "." + df["player.nickName"].str.strip()
    )
    columns_to_drop = [
        "team.acronym",
        "player.lastName",
        "player.firstName",
        "wins",
        "loses",
        "player.nickName",
        "player.id",
        "games",
    ]
    df = df.drop(columns=columns_to_drop)
    desired_order = [
        "Name",
        "Position",
        "Winning_Rate",
        "KDA",
        "Kills",
        "Deaths",
        "Assists",
        "DPM",
        "DTPM",
        "GPM",
        "CSPM",
        "DPGR",
        "First_Blood",
        "First_Turret",
        "Vision_Score",
        "Denied_Vision_Score",
    ]
    df = df[desired_order]
    df["Position"] = df["Position"].str.capitalize()
    df["Position"] = df["Position"].replace("Jun", "Jug")
    df["Position"] = df["Position"].replace("Adc", "Bot")

    df = df[df["Position"] == f"{Position}"]
    df = df.reset_index(drop=True)

    if df.empty:
        print(f"该赛事没有位符为 {Position} 的选手数据，跳过绘图。")
        return

    N = len(categories)
    angles = [n / float(N) * 2 * math.pi for n in range(N)]
    angles += angles[:1]

    eps = 0.05
    scaler = MinMaxScaler(feature_range=(0, 1 - eps))
    df[categories] = scaler.fit_transform(df[categories])
    df[categories] += eps

    base_values = df[categories].mean().values.flatten().tolist()
    base_values += base_values[:1]

    num_players = len(df)
    rows_n = (num_players + 2) // 3
    cols = 3

    fig, axes = plt.subplots(
        nrows=rows_n,
        ncols=cols,
        figsize=(4 * cols, 4 * rows_n),
        subplot_kw=dict(polar=True),
        gridspec_kw={"hspace": 0.4},
    )

    if num_players == 1:
        axes = [axes]
    else:
        axes = axes.ravel()

    for i, ax in enumerate(axes[:num_players]):
        ax.plot(
            angles,
            base_values,
            linewidth=2,
            linestyle="--",
            color="blue",
            label="Average",
        )

        player = df.iloc[i]
        values = player[categories].values.flatten().tolist()
        values += values[:1]

        ax.plot(angles, values, linewidth=2, color="orange")
        ax.fill(angles, values, alpha=0.25, color="orange")

        ax.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
        ax.set_yticklabels(["0", "0.2", "0.4", "0.6", "0.8", "1.0"])
        ax.set_thetagrids(
            [math.degrees(angle) for angle in angles[:-1]],
            categories,
            fontsize=8,
        )
        ax.set_title(player["Name"], fontsize=10, y=1.1)
        ax.set_ylim(0, 1.0)
        ax.legend(loc="upper right", fontsize=6)

    for j in range(num_players, len(axes)):
        axes[j].axis("off")

    plt.suptitle(title, fontsize=16, y=1.01)
    plt.tight_layout()

    # Windows 文件名避免 : 及 | 等非法字符（| 在 Windows 路径中不可用）
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{current_time}__{img_name}.png"

    out_dir.mkdir(parents=True, exist_ok=True)
    file_path = out_dir / filename

    plt.savefig(file_path, dpi=300, bbox_inches="tight")
    print(f"已保存: {file_path}")
    plt.close()


TOURNAMENT_MAPPING = {
    "1353": "2026 LCK Split1 Group Stage",
    "1354": "2026 LPL Split1 Group Stage",
    "1360": "2026 LCK Split1 Play-In",
    "1372": "2026 LPL Split1 Playoffs",
    "1359": "2026 LCK Split1 Playoffs",
    "1374": "2026 First-Stand Playoffs",
    "1375": "2026 First-Stand Group A",
    "1376": "2026 First-Stand Group B",
}

CATEGORIES_MAPPING = {
    "Top": ["KDA", "GPM", "DPM", "DPGR", "First_Turret"],
    "Jug": ["KDA", "GPM", "DTPM", "DPGR", "First_Blood", "First_Turret"],
    "Mid": ["KDA", "GPM", "DPM", "DPGR", "CSPM"],
    "Bot": ["KDA", "GPM", "DPM", "DPGR", "CSPM"],
    "Sup": [
        "KDA",
        "Assists",
        "First_Blood",
        "Vision_Score",
        "Denied_Vision_Score",
    ],
}


def _normalize_position(raw: str) -> str | None:
    s = raw.strip()
    if not s:
        return None
    key = s[:1].upper() + s[1:].lower() if len(s) > 1 else s.upper()
    key = {"Jun": "Jug", "Jungle": "Jug", "Adc": "Bot", "Bot": "Bot"}.get(
        key, key
    )
    if key in CATEGORIES_MAPPING:
        return key
    return None


def main():
    parser = argparse.ArgumentParser(
        description="拉取 OP.GG 赛事数据并生成分位置雷达图（图片在 radar_charts 目录）。",
    )
    parser.add_argument(
        "-t",
        "--tournament",
        metavar="ID",
        help="赛事 ID，例如 1374；可省略，运行时再输入",
    )
    parser.add_argument(
        "-p",
        "--position",
        metavar="POS",
        help="位置：Top / Jug / Mid / Bot / Sup；可省略，运行时再输入",
    )
    args = parser.parse_args()

    tournament_id = (args.tournament or "").strip()
    if not tournament_id:
        tournament_id = input("请输入 tournament_id: ").strip()

    if tournament_id not in TOURNAMENT_MAPPING:
        known = ", ".join(sorted(TOURNAMENT_MAPPING))
        print(f"未知的 tournament_id: {tournament_id!r}。已知 ID: {known}")
        return

    position_raw = (args.position or "").strip()
    if not position_raw:
        position_raw = input("请输入 position (Top/Jug/Mid/Bot/Sup): ")
    position = _normalize_position(position_raw)
    if position is None:
        print(
            f"无效 position: {position_raw!r}。请使用: {', '.join(CATEGORIES_MAPPING)}"
        )
        return

    now = datetime.now()
    img_name = (
        f"{now.strftime('%Y-%m-%d_%H-%M-%S')}_{TOURNAMENT_MAPPING[tournament_id]}_{position}"
    )
    chart_title = f"{TOURNAMENT_MAPPING[tournament_id]} {position} Radar Chart"
    radar_categories = CATEGORIES_MAPPING[position]

    generate_special_lol_players_radar_charts(
        tournamentId=tournament_id,
        Position=position,
        img_name=img_name,
        title=chart_title,
        categories=radar_categories,
    )


if __name__ == "__main__":
    main()
