# LOL_Radar_charts

从 OP.GG esports 的 GraphQL 拉取赛事选手统计数据，并生成分位置（`Top / Jug / Mid / Bot / Sup`）雷达图 PNG。

## 工作原理

- `backend/main.py`：调用 OP.GG GraphQL，清洗数据并生成雷达图
- `frontend/gradio_app.py`：提供本地 Gradio 页面；提交后会运行 `main.py`，并展示“最新生成”的 PNG

## 特性

- 支持位置：`Top`, `Jug`, `Mid`, `Bot`, `Sup`
- 输出目录自动创建：`radar_charts/`
- 本地 Web UI：`http://127.0.0.1:8000/`

## 环境准备

1. 安装依赖（本项目依赖在 `lol_radar_charts/requirements.txt`）：

```powershell
cd "c:\Users\mujing\Desktop\mj\lol_radar_charts"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r .\requirements.txt
```

## 运行

启动 Gradio 前端：

```powershell
cd "c:\Users\mujing\Desktop\mj\lol_radar_charts"
python .\frontend\gradio_app.py
```

浏览器打开：

- `http://127.0.0.1:8000/`

## 使用方法

在页面中填写：

- `tournament_id`：赛事 ID（字符串）
- `position`：位置（`Top / Jug / Mid / Bot / Sup`）

提交后会调用后端生成图片，并在页面上展示最新生成的 PNG。

## 已知 tournament_id

后端内置了部分赛事映射（`backend/main.py` 中的 `TOURNAMENT_MAPPING`）：

- `1353`：`2026 LCK Split1 Group Stage`
- `1354`：`2026 LPL Split1 Group Stage`
- `1360`：`2026 LCK Split1 Play-In`
- `1359`：`2026 LCK Split1 Playoffs`
- `1372`：`2026 LPL Split1 Playoffs`
- `1374`：`2026 First-Stand Playoffs`
- `1375`：`2026 First-Stand Group A`
- `1376`：`2026 First-Stand Group B`

## 输出目录

PNG 会保存到：

- `radar_charts/`

文件名格式（后端自动生成时间戳）：

- `YYYY-MM-DD_HH-MM-SS__{img_name}.png`

## 项目结构

以 `lol_radar_charts/` 为根：

- `backend/`：实际可运行的后端脚本 `main.py`（抓取与绘图）
- `frontend/gradio_app.py`：本地 Gradio UI（推荐）
- `radar_charts/`：输出目录（PNG）
- `etc/`：参考材料/原始探索代码（如 `rebirth.ipynb`、`radar.txt` 等）
- `requirements.txt`：Python 依赖清单

## 排错

- 服务器页面显示 `main.py` 错误时：通常需要检查控制台输出，或确认 `tournament_id` 是否在内置映射中
- OP.GG GraphQL 请求失败时：可能是网络问题、接口变更或被拦截（后端会在 stdout/stderr 中打印错误信息）

## 许可证

本项目采用 `MIT` 许可证，详见根目录 `LICENSE`。
