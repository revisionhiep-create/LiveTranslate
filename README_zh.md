# LiveTranslate (海外直播实时字幕翻译版)

<div align="center">

<img src="icon.ico" width="128" height="128" alt="LiveTranslate 图标" />

### 专为 Windows 观看海外直播、VTuber、动画打造的实时字幕翻译工具

**无需安装外部软件或购买 API 密钥，开箱即用，支持毫秒级流式字幕。**

[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011-0078d4?logo=windows)](https://github.com/revisionhiep-create/LiveTranslate)
[![Python](https://img.shields.io/badge/Python-3.10%20--%203.12-3776AB?logo=python)](https://github.com/revisionhiep-create/LiveTranslate)
[![CUDA](https://img.shields.io/badge/CUDA-12.6%20%7C%2012.8%20(RTX%2050xx)-76B900?logo=nvidia)](https://github.com/revisionhiep-create/LiveTranslate)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

[English](README.md) | [中文说明](README_zh.md)

</div>

---

## 🌟 本 Fork 分支特色

原本的 LiveTranslate 偏向于主播直播推流使用，而本 Fork 进行了全方位重新调优，**专门服务于在 Windows 上观看海外主播（如 YouTube/Twitch/TwitCasting 的日文 VTuber、游戏直播、动漫生肉等）的观众**。

### 主要改进与特性：
- 🚀 **开箱即用，零配置要求**：默认搭载针对动漫/日文游戏优化的 **Anime-Whisper**，以及直接运行的 **Qwen3.5-4B** 本地大语言模型。**首次启动完全无需配置 LM Studio 或填写 API 密钥**！
- ⚡ **无思考模式极速流式翻译**：Qwen 本地翻译模型强制启用 `enable_thinking=False`，彻底关闭多余的思维链推理，从第一个 token 开始直接输出翻译字幕，零延迟流式展现。
- 🖥️ **跨多显示器 DPI 缩放修复**：彻底解决了原版在多台不同分辨率/DPI 缩放比例的显示器之间拖拽时，界面错位、字体模糊或窗口被截断的 Bug。
- 💾 **完整的语言与状态持久化**：记住用户选择的源语言（如 `ja`）与目标语言（如 `en`），不再强制重置回中文；窗口坐标、置顶（`Top-most`）、鼠标穿透（`Click-through`）、自动滚动状态均会自动保存。
- 📺 **双字幕窗口与独立位置记忆**：除了主控制台历史窗口外，还提供专为贴在视频播放器下方设计的半透明单行/双行字幕条。按住鼠标中键即可拖动到任意位置，关闭后自动记忆坐标。
- 🐱 **单实例原生 GUI 启动器 (`LiveTranslate.exe`)**：任务栏独立精致萌系图标，无黑色控制台干扰。若环境未安装依赖，自动弹出友好安装向导一键配置，免去命令行困扰。
- 🏎️ **核心音频算法与性能提速**：音频双声道混音与重采样速度提升 8.9 倍，RMS 与 VAD 计算向量化加速，针对直播杂音优化的能量检测算法。

---

## ⚡ 快速开始 (Windows)

### 系统要求
- **系统**：Windows 10 / 11 (64位)
- **显卡**：NVIDIA GeForce RTX 系列（推荐 RTX 30/40/50 系列，显存 6GB 以上最佳）
- **音频**：任意系统播放声音（通过 WASAPI 环回内录捕获浏览器、Discord 或播放器声音）

### 一键安装

1. **克隆代码库**：
   ```bash
   git clone https://github.com/revisionhiep-create/LiveTranslate.git
   cd LiveTranslate
   ```

2. **双击运行 `LiveTranslate.exe`**（或执行 `install.bat`）：
   - 如果是首次运行，程序会自动检测虚拟环境，并询问是否开始自动安装。
   - 点击 **“是”** 即可全自动安装 Python 依赖及匹配当前显卡的 PyTorch CUDA 版本（包括 RTX 50 系列 Blackwell 显卡专属 CUDA 12.8）。

3. **首次启动自动下载模型**：
   - 首次启动向导会自动从 Hugging Face 下载 **Anime-Whisper** 与 **Qwen3.5-4B**。
   - 下载完成后立即自动打开字幕悬浮窗开始实时翻译！

---

## 🧠 翻译模式选择

### 1. 内置本地 Qwen3.5-4B（默认推荐 —— 无需第三方软件）
默认情况下，LiveTranslate 使用内置的本地 **Qwen3.5-4B** 并在本地 GPU 上运行：
- 完全离线运行，保护隐私，无网络调用开销。
- 自动禁用思考模式，逐字流式打字输出。
- 在 **设置 → 翻译** 选项卡中，保持勾选 **“使用内置 Qwen3.5-4B”** 即可。

---

### 2. 使用 LM Studio 本地模型服务（可选）

如果你喜欢使用 [LM Studio](https://lmstudio.ai/) 加载自定义的大语言模型（如 Llama 3、Mistral、Gemma 等）：

1. **在 LM Studio 中**：
   - 下载并加载你喜欢的翻译模型。
   - 点击左侧 **Developer / 本地服务器** 图标 (`<->`)。
   - 点击 **Start Server** 启动服务（默认端口为 `http://localhost:1234`）。
2. **在 LiveTranslate 中**：
   - 点击主界面右上角齿轮图标进入 **设置 → 翻译**。
   - **取消勾选** “使用内置 Qwen3.5-4B”。
   - 在模型配置中点击 **添加** 或 **编辑**：
     - **名称**：`LM Studio`
     - **API 地址 (API Base)**：`http://127.0.0.1:1234/v1`
     - **API 密钥 (API Key)**：`lm-studio`（可任意填写）
     - **模型**：输入 LM Studio 中加载的模型标识符。
   - 点击保存即可切换到 LM Studio。

---

### 3. 使用云端大模型 API（DeepSeek、OpenAI 等）

如需节省本地显存，也可以一键接入各大云端 API：

1. 进入 **设置 → 翻译**。
2. **取消勾选** “使用内置 Qwen3.5-4B”。
3. 点击 **添加** 或 **编辑**：
   - **DeepSeek**：
     - API 地址：`https://api.deepseek.com/v1`
     - API 密钥：`sk-your-deepseek-key`
     - 模型：`deepseek-chat`
   - **OpenAI**：
     - API 地址：`https://api.openai.com/v1`
     - API 密钥：`sk-your-openai-key`
     - 模型：`gpt-4o-mini`
4. 保存即可。

---

## 🎮 控制与操作手势

| 功能 | 操作说明 |
|------|----------|
| **移动主窗口** | 按住左上角拖拽条使用鼠标左键拖动。 |
| **独立字幕窗口 (`Sub`)** | 点击标题栏的 `Sub` 按钮开启/隐藏下方的精简悬浮字幕条。 |
| **拖动字幕条** | 在悬浮字幕文字上**点击并按住鼠标中键**，即可将其拖到 YouTube/Twitch 播放器画面下方任意位置，位置自动记忆保存。 |
| **窗口置顶 (`Top-most`)** | 勾选后窗口将始终悬浮在浏览器、视频播放器或游戏上方。 |
| **鼠标穿透 (`Click-through`)**| 勾选后鼠标点击可直接穿透字幕区域操作背后的网页或播放器。 |
| **自动滚动 (`Auto-scroll`)** | 勾选后字幕记录自动滚到最新一行。 |
| **源语言 / 目标语言切换** | 顶部下拉菜单快速切换语音识别源语言（默认日文 `ja`）与翻译目标语言（默认英文 `en`）。 |

---

## 🛠️ VAD 语音与静音检测预设

针对日文直播快速切分优化的预设参数：
- **VAD 模式**：`Energy-based`（能量基准检测，有效过滤直播背景 BGM 与杂音）。
- **能量阈值**：`25‰` (`0.025`)。
- **最短语音时长**：`0.40s`（准确捕获日文极短语气词与拟声词）。
- **最长语音时长**：`8.00s`。
- **静音切分时长**：`0.50s` (固定)。
- **音频设备**：自动对接 Windows 默认播放输出或虚拟调音台（如 VoiceMeeter、BEACN 等）。

可在 **设置 → AD / ASR** 中随时按个人需求微调。

---

## 📄 许可协议

- 基于 [LiveTranslate](https://github.com/TheDeathDragon/LiveTranslate) 开源架构衍生开发。
- 日语音频识别模型：[Anime-Whisper](https://huggingface.co/litagin/anime-whisper) (litagin)。
- 语音活动检测：[Silero VAD](https://github.com/snakers4/silero-vad)。
- 本地翻译大模型：[Qwen/Qwen3.5-4B](https://huggingface.co/Qwen/Qwen3.5-4B) (阿里 Qwen 团队)。
- 遵循 [MIT 许可协议](LICENSE) 开源。
