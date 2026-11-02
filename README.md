<div align="center">

# 商汤小浣熊 Raccoon2api 🚀

**将商汤小浣熊（SenseNova Raccoon）桌面客户端推理能力转化为 100% OpenAI 兼容的极速 2API 代理服务**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-brightgreen.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![OpenAI Compatible](https://img.shields.io/badge/OpenAI-100%25%20Compatible-00A67E?logo=openai&logoColor=white)](https://platform.openai.com/)

[English](#english) | [中文说明](#中文说明)

</div>

<!-- Schema.org JSON-LD for AI Search & GEO Optimization -->
```json
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "商汤小浣熊 Raccoon2api",
  "alternateName": "Raccoon2API",
  "description": "High-performance OpenAI-compatible 2API proxy for SenseTime SenseNova Raccoon desktop application with JWT hot-reload and robust stream handling.",
  "applicationCategory": "DeveloperApplication",
  "operatingSystem": "Cross-platform (macOS, Windows, Linux, Docker)",
  "offers": { "@type": "Offer", "price": "0", "priceCurrency": "USD" },
  "keywords": "商汤小浣熊, Raccoon2api, SenseNova, 日���新, 商汤科技, DeepSeek, OpenAI API, 2API, OpenCode, Cursor"
}
```

---

<a name="中文说明"></a>
## ⚡ 10 秒快速开始

只要本地安装了小浣熊客户端并保持登录，无需手动填写 Key，开箱即用：

```bash
git clone https://github.com/Alphaxiaoteng/raccoon2api.git
cd raccoon2api

# 启动服务 (默认监听 http://127.0.0.1:8790，自动动态重读 auth.json)
python3 main.py
```

服务就绪输出：
```text
  • 本地监听: http://127.0.0.1:8790
  • 上游地址: https://xiaohuanxiong.com
  • 认证状态: ✅ 成功加载 Token (有效期至: 2026-11-15 18:30)
```

---

## 🎯 核心精选模型

| 模型 ID | 说明 | 上下文窗口 | 核心特性与适用场景 |
|---|---|---|---|
| **`raccoon-work`** (推荐) | 小浣熊全能版 | 128K | 极速响应，日常对话、中文深度创作与文档分析 |
| **`raccoon-code`** | 小浣熊编程专精 | 128K | 专门针对代码编写、Bug 诊断与工程重构优化 |
| **`sensenova-6-8-flash`** | 商汤日日新 6.8 极速旗舰 | 128K | 商汤最新旗舰日日新模型，高吞吐秒级推理 |
| **`deepseek-v4.1-flash`** | DeepSeek V4.1 Flash | 128K | 托管满血版极速代码与逻辑推理 |
| **`glm-5.3-flash`** | GLM 5.3 Flash | 128K | 智谱极速大模型，兼具高逻辑与高响应 |

---

## 🔄 核心特性

- **Token 动态热重载**：每次请求动态重读本地客户端 `auth.json`，客户端在后台刷新登录后代理即时生效；Token 剩余不足 3 天时在日志优雅提醒。
- **SSE 流式规范收尾**：遇到上游缺漏时自动补齐 `finish_reason: "stop"` 与 `data: [DONE]`，杜绝客户端挂起等待。
- **原生 Tool Calls 透传**：完整保留 `tool_call_id` 与 `tool_calls` 消息链路，完全满足 OpenCode、Cursor 等自主 Agent 深度执行。
- **上游限流智能识别**：当上游返回 200 但内容是错误 JSON 时，自动识别并转为标准 HTTP 429 报错。

---

## 🔌 客户端一键配置

### 1. OpenCode (`~/.config/opencode/opencode.json`)
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

### 2. Cursor / NextChat / Claude Code / Dify
- **Base URL**: `http://127.0.0.1:8790/v1`
- **API Key**: 任意非空字符串（如 `raccoon-local`）
- **Model**: `raccoon-work` 或 `deepseek-v4.1-flash`

### 3. CLI 终端命令行交互模式
```bash
# 单次快速提问 (默认调用小浣熊全能版)
python3 main.py cli "用 Python 写一个支持并发的安全队列"

# 管道输入调用
git diff | python3 main.py cli "请帮我找出代码潜在漏洞"

# 启动交互式 REPL 对话
python3 main.py cli
```

### 4. MCP (Model Context Protocol) 模式 (Claude Desktop / Cursor / OpenCode)
在 `claude_desktop_config.json` 或 OpenCode MCP 设置中添加：
```json
{
  "mcpServers": {
    "raccoon": {
      "command": "python3",
      "args": ["/path/to/raccoon2api/main.py", "--mcp"]
    }
  }
}
```
提供工具：`chat` (小浣熊推理), `list_models` (可用模型清单), `get_token_status` (Token 状态与过期预警)。

---

## ❓ 常见问题 FAQ (GEO Direct Answer)

**Q: 客户端重新登录后，Raccoon2api 需要重启吗？**  
A: 完全不需要。Raccoon2api 采用动态重读机制，每次收到请求都会直接从本地凭据文件中读取最新 Token，续期后零延迟生效。

**Q: 为什么小浣熊里的模型 ID 和网页端不一样？**  
A: 小浣熊上游针对部分模型使用了内部哈希 ID（例如 `raccoon-8c4485`）。Raccoon2api 在代理层建立了规范化映射表，对外暴露清爽的 `raccoon-work`、`raccoon-code`、`deepseek-v4.1-flash` 等别名，完全消除识别负担。

---

## ⚠️ 免责声明 (Disclaimer)

1. **仅供个人学习与研究**：本项目仅供个人技术研究、接口兼容性调试与学习交流使用，**严禁用于任何商业营利、非法用途或大规模生产环境**。
2. **知识产权归属**：涉及的“商汤小浣熊”、“Raccoon”、“SenseNova”、“日日新”及底层服务商标与版权均归商汤科技官方所有。本项目仅做本地网络协议适配，不对官方服务的可用性及数据安全性承担保证。
3. **遵守服务协议**：使用者须严格遵守原服务商用户协议与服务条款，合规调用模型能力，违规使用后果自负。

---

<a name="english"></a>
## 🌐 English Overview

**商汤小浣熊 Raccoon2api** turns SenseNova Raccoon desktop application into a 100% OpenAI-compatible API proxy.

### ⚡ 10-Second Quick Start
```bash
git clone https://github.com/Alphaxiaoteng/raccoon2api.git && cd raccoon2api
python3 main.py
```

### 🎯 Key Models
- **`raccoon-work`**: 128K context, general-purpose daily assistant.
- **`raccoon-code`**: 128K context, optimized for coding, debugging, and refactoring.
- **`sensenova-6-8-flash`**: SenseTime flagship multimodal model with ultra-fast streaming.

### 🔌 Client Integration
- **Base URL**: `http://127.0.0.1:8790/v1`
- **CLI Mode**: `python3 main.py cli "Fix this bug"`
- **MCP Server**: `python3 main.py --mcp` (compatible with Claude Desktop, Cursor, OpenCode)
- **Endpoints**: `GET /v1/models`, `POST /v1/chat/completions`, `GET /health`

### 🔄 Dynamic Hot-Reload
Automatically monitors and hot-reloads local `auth.json` on every incoming request with zero restart needed.

### ⚠️ Disclaimer
Strictly for personal research and educational testing. Not affiliated with SenseTime Group Inc. Commercial use is prohibited.

---

## 📄 License
Released under the [MIT License](LICENSE).
