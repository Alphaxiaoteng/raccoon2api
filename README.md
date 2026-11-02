<div align="center">

# 商汤小浣熊 Raccoon2api 🚀

**将商汤小浣熊（SenseNova Raccoon）桌面客户端推理能力转化为 100% 兼容 OpenAI 格式的高性能 2API 代理服务**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-brightgreen.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![OpenAI Compatible](https://img.shields.io/badge/OpenAI-100%25%20Compatible-00A67E?logo=openai&logoColor=white)](https://platform.openai.com/)

[English](#english) | [中文说明](#中文说明)

</div>

---

## ⚠️ 免责声明 (Disclaimer)

1. **个人学习与研究使用**：本项目仅供个人技术研究、接口兼容性调试与学习交流使用，**严禁用于任何商业营利、非法用途或大规模生产环境**。
2. **版权与商标归属**：本项目涉及的���商汤小浣熊”、“Raccoon”、“SenseNova”、“日日新”及底层服务商标与版权均归其官方所有（商汤科技 SenseTime）。本项目仅作为本地格式桥接适配中间件，不对官方客户端的稳定性、可用性及数据安全性作任何明示或暗示的保证。
3. **服务条款遵从**：使用者在调用相关接口与服务时，必须严格遵守原服务商的用户协议与服务条款（Terms of Service）。若因使用者自身的不当调用或超额请求引发账号风控、限制或法律责任，均由使用者本人独立承担，本项目作者概不负责。

---

<a name="中文说明"></a>
## 💡 为什么需要 商汤小浣熊 Raccoon2api？

**商汤小浣熊（Raccoon）** 是商汤科技推出的一款优秀的桌面智能生产力助手，集成了商汤**日日新（SenseNova 6.8）**多模态大模型及 DeepSeek、GLM 等业界顶尖模型。然而其原生客户端仅供桌面交互使用，外部开源生态（如 **OpenCode、Cursor、Claude Code、NextChat、LibreChat、Continue、Dify**）无法直接对接。

**Raccoon2api** 提供了原生级的转换桥梁：
- 🔄 **自动凭据同步与过期预警**：每次请求动态重读小浣熊桌面端登录 Token，客户端续期后立即生效；当 Token 剩余不足 3 天时日志自动提醒。
- 🎯 **模型名称规范化映射**：收敛上游内部随机哈希 ID（如 `raccoon-8c4485`）为清晰易读的别名（如 `raccoon-work`、`deepseek-v4.1-flash`）。
- 🌊 **工业级流式 SSE 规范收尾**：完整支持 Server-Sent Events，自动补齐缺失的 `finish_reason` 与 `data: [DONE]`，避免客户端 hang 死悬挂。
- 🛠️ **原�� Tool Calls 工具调用支持**：严格保留 `tool_call_id` 与 `tool_calls` 消息链路，完全满足 OpenCode、Cursor 等自主 Agent 深度执行。
- ⚡ **零外部依赖**：基于 Python 3 原生标准库开发，无任何重量级框架依赖，开箱即用。

---

## 🎯 核心精选模型

| 模型 ID | 说明 | 上下文窗口 | 特性与适用场景 |
|---|---|---|---|
| **`raccoon-work`** (推荐) | 商汤小浣熊全能版 | 128K | 极速全能，擅长日常对话、中文创作与文档分析 |
| **`raccoon-code`** | 商汤小浣熊编程专精 | 128K | 代码生成、Bug 修复与工程重构特化版 |
| **`sensenova-6-8-flash`** | 商汤日日新 6.8 旗舰极速 | 128K | 商汤最新旗舰日日新模型，推理速度极快 |
| **`deepseek-v4.1-flash`** | DeepSeek V4.1 Flash | 128K | 托管满血版极速代码与逻辑推理 |
| **`glm-5.3-flash`** | GLM 5.3 Flash | 128K | 智谱极速大模型，兼具高逻辑与高响应 |

---

## ⚡ 快速开始

### 方式 1：本地直接运行 (推荐)

只要本地安装了小浣熊客户端并保持登录，即可直接免密启动：

```bash
# 1. 克隆代码仓库
git clone https://github.com/Alphaxiaoteng/raccoon2api.git
cd raccoon2api

# 2. 启动服务（默认监听 http://127.0.0.1:8790）
python3 main.py
```

服务启动后自动输出：
```text
=================================================================
  🚀 商汤小浣熊 Raccoon2api
=================================================================
  • 本地监听: http://127.0.0.1:8790
  • 上游地址: https://xiaohuanxiong.com
  • 认证状态: ✅ 成功加载 Token (有效期至: 2026-11-15 18:30)
-----------------------------------------------------------------
```

### 方式 2：macOS 后台守护服务 (LaunchAgent)

创建 `~/Library/LaunchAgents/com.user.raccoon2api.plist`：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.raccoon2api</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/path/to/raccoon2api/main.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

加载守护进程：
```bash
launchctl load ~/Library/LaunchAgents/com.user.raccoon2api.plist
```

---

## 🛠️ 客户端接入指南

### 1. OpenCode

在你的 `~/.config/opencode/opencode.json` 中添加 Provider：

```json
{
  "provider": {
    "raccoon": {
      "name": "商汤小浣熊 (SenseNova)",
      "npm": "@ai-sdk/openai-compatible",
      "options": {
        "apiKey": "raccoon-local",
        "baseURL": "http://127.0.0.1:8790/v1"
      },
      "models": {
        "raccoon-work": {
          "id": "raccoon-work",
          "name": "Raccoon Work (小浣熊全能)",
          "attachment": true,
          "reasoning": true,
          "tool_call": true,
          "limit": { "context": 131072, "output": 8192 },
          "modalities": { "input": ["text"], "output": ["text"] }
        },
        "deepseek-v4.1-flash": {
          "id": "deepseek-v4.1-flash",
          "name": "DeepSeek V4.1 Flash (小浣熊)",
          "attachment": true,
          "reasoning": true,
          "tool_call": true,
          "limit": { "context": 131072, "output": 8192 },
          "modalities": { "input": ["text"], "output": ["text"] }
        }
      }
    }
  }
}
```

### 2. Cursor / NextChat / LibreChat / Continue

- **API Base URL**: `http://127.0.0.1:8790/v1`
- **API Key**: 任意非空字符串（如 `raccoon-local`）
- **Model Name**: `raccoon-work` 或 `deepseek-v4.1-flash`

---

## 🧪 接口调用示例

```bash
curl -N http://127.0.0.1:8790/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer raccoon-local" \
  -d '{
    "model": "raccoon-work",
    "messages": [{"role": "user", "content": "你好，请用一句话介绍你自己"}],
    "stream": true
  }'
```

---

<a name="english"></a>
## 🌐 English Overview

**商汤小浣熊 Raccoon2api** turns SenseNova Raccoon desktop application into a 100% OpenAI-compatible API proxy.

### ⚠️ Disclaimer

1. **Personal & Educational Use Only**: This project is strictly intended for personal learning, interface compatibility testing, and research purposes. **Any commercial use, illegal activities, or production deployments are strictly prohibited.**
2. **Trademarks & Copyrights**: All trademarks, brand names, and copyrights (including "Raccoon", "SenseNova", and "SenseTime") belong to their respective owners (SenseTime Group Inc.). This tool acts solely as a local protocol bridge/adapter and is not officially affiliated with or endorsed by SenseTime.
3. **Compliance with Terms of Service**: Users must strictly comply with the Terms of Service of the respective platforms. The authors assume no liability for any account suspensions, disputes, or damages resulting from the use of this project.

### Highlights
- **Zero Heavy Dependencies**: Pure Python 3 standard library.
- **Dynamic Token Hot-Reload**: Auto-reloads `auth.json` on every request with JWT expiry alarms.
- **Stream Robustness**: Auto-detects and polyfills missing `finish_reason` and `[DONE]` tokens.
- **Native Tool Calls**: Fully compliant with Agent workflows (OpenCode, Cursor).

---

## 📄 License

本项目基于 [MIT 许可证](LICENSE) 开源。欢迎 Star 🌟 与 PR 贡献！
