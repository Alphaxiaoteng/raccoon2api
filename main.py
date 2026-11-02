#!/usr/bin/env python3
"""
商汤小浣熊 Raccoon2api 🚀
将商汤小浣熊（SenseNova Raccoon）桌面客户端推理能力转化为 100% 兼容 OpenAI 格式的高性能 2API 代理服务。

【免责声明 / Disclaimer】
  1. 本项目仅供个人学习、技术研究与接口兼容性测试使用，严禁用于商业用途、非法用途或生产环境。
  2. 相关商标及底层服务版权均归商汤科技官方所有。
  3. 使用者须严格遵守原服务商用户协议与服务条款，违规使用后果自负。

功能特性:
  - 100% OpenAI 接口规范 (GET /v1/models, POST /v1/chat/completions)
  - 自动探测并重读小浣熊桌面端 JWT Token，带 JWT 到期预警机制
  - 优雅收敛上游内部哈希模型 ID 为友好别名 (raccoon-work, raccoon-code, deepseek-v4.1-flash 等)
  - 完美支持真流式 SSE (Server-Sent Events) 输出与规范 finish_reason 收尾
  - 支持原生 Function Calling (Tool Calls) 工具调用透传与多模态
  - 上游 429 限流智能侦测与标准化错误回显
  - 纯 Python 3 标准库实现，零外部依赖，开箱即用
"""

import os
import ssl
import sys
import json
import time
import base64
import urllib.request
import urllib.error
from urllib.parse import urlparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# ==================== 默认配置与环境变量加载 ====================

DEFAULT_PORT = 8790
DEFAULT_UPSTREAM = "https://xiaohuanxiong.com"
CHAT_PATH = "/api/web/llm/v2/chat/completions"
CATALOG_PATH = "/api/web/llm/v2/model_catalog"

SSL_CTX = ssl.create_default_context()

def load_dotenv():
    """纯标准库轻量加载当前目录下的 .env 文件"""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(env_path):
        return
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip("'").strip('"')
                if k and k not in os.environ:
                    os.environ[k] = v
    except Exception as e:
        sys.stderr.write(f"[WARN] 加载 .env 失败: {e}\n")

load_dotenv()

PORT = int(os.environ.get("PORT") or os.environ.get("RACCOON_PORT") or DEFAULT_PORT)
UPSTREAM_BASE = (os.environ.get("RACCOON_UPSTREAM_URL") or DEFAULT_UPSTREAM).rstrip("/")

# 默认客户端 auth.json 本地路径探测 (macOS / Windows / Linux)
DEFAULT_AUTH_PATHS = [
    os.path.expanduser("~/Library/Application Support/office-raccoon/agent/config/auth.json"),
    os.path.expandvars(r"%APPDATA%\office-raccoon\agent\config\auth.json"),
    os.path.expanduser("~/.config/office-raccoon/agent/config/auth.json")
]

# 友好名称到小浣熊内部真实模型 ID 的映射表
MODEL_ALIAS = {
    # 商汤小浣熊自研核心
    "raccoon-work": "raccoon-8c4485",
    "raccoon-code": "raccoon-19b265",
    "raccoon-lite": "raccoon-405a1c",
    # 第三方顶级模型托管
    "deepseek-v4.1-flash": "sn-deepseek-v4-1-flash-1017",
    "deepseek-v4.1": "sn-deepseek-v4-1-flash-1017",
    "glm-5.3": "sn-glm-5-3",
    "glm-5.3-flash": "sn-glm-5-3-flash",
    "kimi-k3": "sn-kimi-k3",
    "sensenova-6-8-flash": "sn-sensenova-6-8-flash"
}

# 对外暴露的核心推荐模型定义
CORE_MODELS = [
    {
        "id": "raccoon-work",
        "object": "model",
        "owned_by": "sensenova",
        "display_name": "Raccoon Work (商汤小浣熊全能版)",
        "context_window": 131072
    },
    {
        "id": "raccoon-code",
        "object": "model",
        "owned_by": "sensenova",
        "display_name": "Raccoon Code (商汤小浣熊编程专精)",
        "context_window": 131072
    },
    {
        "id": "deepseek-v4.1-flash",
        "object": "model",
        "owned_by": "deepseek",
        "display_name": "DeepSeek V4.1 Flash (托管极速版)",
        "context_window": 131072
    },
    {
        "id": "glm-5.3-flash",
        "object": "model",
        "owned_by": "zhipu",
        "display_name": "GLM 5.3 Flash (智谱极速版)",
        "context_window": 131072
    },
    {
        "id": "sensenova-6-8-flash",
        "object": "model",
        "owned_by": "sensenova",
        "display_name": "SenseNova 6.8 Flash (商汤日日新 6.8 旗舰极速)",
        "context_window": 131072
    }
]

# ==================== 认证与 Token 管理引擎 ====================

_LAST_EXP_WARN = [0.0]

def jwt_exp(token):
    """解析 JWT payload 里的 exp（unix 秒），解析失败返回 None"""
    if not token or "." not in token:
        return None
    try:
        parts = token.split(".")
        if len(parts) < 2:
            return None
        p = parts[1]
        p += "=" * (-len(p) % 4)
        data = json.loads(base64.urlsafe_b64decode(p).decode("utf-8"))
        return data.get("exp")
    except Exception:
        return None

def _warn_if_expiring(token, threshold=3 * 86400, interval=6 * 3600):
    """当 Token 剩余有效期不足 3 天时在终端提示刷新"""
    now = time.time()
    if now - _LAST_EXP_WARN[0] < interval:
        return
    try:
        exp = jwt_exp(token)
        if not exp:
            return
        remain = exp - now
        if remain < threshold:
            sys.stderr.write(
                "[WARN] 小浣熊 JWT 将于 %s 过期 (剩余 %.1f 天)，请打开小浣熊桌面端刷新登录。\n"
                % (time.strftime("%Y-%m-%d %H:%M", time.localtime(exp)), remain / 86400)
            )
            _LAST_EXP_WARN[0] = now
    except Exception:
        pass

def get_access_token(request_header_token=None):
    """多级自适应加载小浣熊 access_token：
       1. 请求头 Authorization 显式传入有效 JWT
       2. 环境变量 RACCOON_ACCESS_TOKEN
       3. 本地客户端 auth.json 文件动态读取
    """
    if request_header_token and len(request_header_token) > 20 and request_header_token != "raccoon-local":
        return request_header_token

    env_token = os.environ.get("RACCOON_ACCESS_TOKEN") or os.environ.get("RACCOON_TOKEN")
    if env_token:
        _warn_if_expiring(env_token)
        return env_token

    custom_path = os.environ.get("RACCOON_AUTH_FILE")
    candidate_paths = [custom_path] if custom_path else DEFAULT_AUTH_PATHS

    for p in candidate_paths:
        if p and os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    tok = data.get("access_token")
                    if tok:
                        _warn_if_expiring(tok)
                        return tok
            except Exception:
                pass

    return None

def resolve_model(name):
    """将友好名称解析为内部模型 ID"""
    if not name:
        return "raccoon-8c4485"
    clean = str(name).strip()
    if "/" in clean:
        clean = clean.split("/")[-1]
    return MODEL_ALIAS.get(clean.lower(), clean)

def pick_first_message(messages):
    """兼容处理：小浣熊上游某些模型对 system role 支持不一，统一折叠前置。
       严格保留 tool_call_id 与 tool_calls 字段以支持闭环工具调用。"""
    out = []
    system_parts = []
    for m in messages or []:
        role = m.get("role", "user")
        content = m.get("content")
        if role == "system":
            if isinstance(content, str):
                system_parts.append(content)
            continue
        nm = {"role": role, "content": content}
        if role == "tool" and m.get("tool_call_id"):
            nm["tool_call_id"] = m["tool_call_id"]
        if role == "assistant" and m.get("tool_calls"):
            nm["tool_calls"] = m["tool_calls"]
        out.append(nm)
    if system_parts and out:
        first = out[0]
        if isinstance(first.get("content"), str):
            first["content"] = "\n\n".join(system_parts) + "\n\n" + first["content"]
    return out

# ==================== 请求处理类 ====================

class RaccoonProxyHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        sys.stderr.write(f"[{timestamp}] {fmt % args}\n")

    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, HEAD")
        self.send_header("Access-Control-Allow-Headers", "*")

    def _json_response(self, data, status_code=200):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status_code)
        self._send_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self._send_cors_headers()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        # 健康探针端点
        if path in ("", "/health", "/ping"):
            token = get_access_token()
            exp = jwt_exp(token) if token else None
            exp_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(exp)) if exp else None
            return self._json_response({
                "status": "healthy",
                "service": "商汤小浣熊 Raccoon2api",
                "version": "1.0.0",
                "port": PORT,
                "authenticated": bool(token),
                "jwt_expires_at": exp_str,
                "models": [m["id"] for m in CORE_MODELS]
            }, 200)

        # 模型列表端点
        if path in ("/v1/models", "/models"):
            models_data = [
                {
                    "id": alias,
                    "object": "model",
                    "created": int(time.time()),
                    "owned_by": "sensenova",
                    "permission": [],
                    "root": alias,
                    "parent": None
                }
                for alias in MODEL_ALIAS.keys()
            ]
            return self._json_response({"object": "list", "data": models_data}, 200)

        self._json_response({
            "error": {
                "message": f"Endpoint {path} not found. Use /v1/models or /v1/chat/completions.",
                "type": "invalid_request_error"
            }
        }, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if not (path.endswith("/chat/completions") or path.endswith("/completions")):
            return self._json_response({
                "error": {
                    "message": f"Endpoint not found: {path}",
                    "type": "invalid_request_error"
                }
            }, 404)

        # 获取 Token
        auth_header = self.headers.get("Authorization", "")
        req_token = auth_header.replace("Bearer ", "").strip() if auth_header else None
        token = get_access_token(req_token)

        if not token:
            return self._json_response({
                "error": {
                    "message": "未检测到商汤小浣熊凭证。请在小浣熊桌面客户端中保持登录，或配置 RACCOON_ACCESS_TOKEN 环境变量。",
                    "type": "authentication_error",
                    "code": "missing_token"
                }
            }, 401)

        length = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        except Exception as e:
            return self._json_response({"error": {"message": f"Bad JSON: {str(e)}"}}, 400)

        want_stream = bool(body.get("stream", False))
        raw_model = body.get("model", "raccoon-work")
        target_model = resolve_model(raw_model)

        payload = {
            "model": target_model,
            "messages": pick_first_message(body.get("messages")),
            "stream": want_stream
        }

        # 参数透传
        for k in ("temperature", "top_p", "max_tokens", "max_completion_tokens",
                  "frequency_penalty", "presence_penalty", "stop", "tools", "tool_choice"):
            if k in body and body[k] is not None:
                payload[k] = body[k]

        upstream_url = f"{UPSTREAM_BASE}{CHAT_PATH}"
        upstream_req = urllib.request.Request(
            upstream_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "User-Agent": "raccoon-desktop",
                "Accept": "text/event-stream" if want_stream else "application/json"
            },
            method="POST"
        )

        try:
            resp = urllib.request.urlopen(upstream_req, timeout=300, context=SSL_CTX)

            if want_stream:
                try:
                    first_line = resp.readline()
                except Exception:
                    first_line = b""
                fl = first_line.decode(errors="replace").strip()

                # 上游限流识别
                if fl.startswith('{"error"') or "rate_limit" in fl:
                    try:
                        resp.close()
                    except Exception:
                        pass
                    code = 429 if "rate_limit" in fl else 502
                    return self._json_response({
                        "error": {
                            "message": f"小浣熊上游限流或报错: {fl[:300]}",
                            "type": "upstream_rate_limit" if code == 429 else "upstream_error",
                            "code": code
                        }
                    }, code)

                self.send_response(200)
                self._send_cors_headers()
                self.send_header("Content-Type", "text/event-stream; charset=utf-8")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Connection", "close")
                self.send_header("X-Accel-Buffering", "no")
                self.end_headers()

                def safe_write(data):
                    try:
                        self.wfile.write(data)
                        self.wfile.flush()
                        return True
                    except Exception:
                        return False

                if not safe_write(first_line if first_line else b""):
                    return

                saw_finish = False
                saw_done = False
                for raw_line in resp:
                    if not safe_write(raw_line):
                        break
                    line = raw_line.decode(errors="replace").strip()
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            saw_done = True
                            continue
                        try:
                            j = json.loads(data)
                            for ch in j.get("choices") or []:
                                if ch.get("finish_reason"):
                                    saw_finish = True
                        except Exception:
                            pass

                try:
                    resp.close()
                except Exception:
                    pass

                # 规范收尾补齐
                if not saw_finish:
                    fallback_chunk = {
                        "id": "chatcmpl-raccoon-tail",
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": raw_model,
                        "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]
                    }
                    safe_write(("data: " + json.dumps(fallback_chunk) + "\n\n").encode("utf-8"))

                if not saw_done:
                    safe_write(b"data: [DONE]\n\n")
                return

            # 非流式处理
            resp_body = resp.read().decode("utf-8")
            try:
                parsed = json.loads(resp_body)
                return self._json_response(parsed, 200)
            except Exception:
                self.send_response(200)
                self._send_cors_headers()
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(resp_body.encode("utf-8"))

        except urllib.error.HTTPError as e:
            err_msg = e.read().decode("utf-8", "replace")
            code = 429 if e.code == 429 or "rate_limit" in err_msg else 502
            try:
                err_json = json.loads(err_msg)
                return self._json_response(err_json, code)
            except Exception:
                return self._json_response({"error": {"message": f"HTTP {e.code}: {err_msg[:300]}"}}, code)
        except Exception as e:
            return self._json_response({"error": {"message": str(e)}}, 502)

# ==================== 主入口与服务启动 ====================

def main():
    token = get_access_token()
    exp = jwt_exp(token) if token else None
    exp_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(exp)) if exp else "未知"

    print("=" * 65)
    print("  🚀 商汤小浣熊 Raccoon2api")
    print("=" * 65)
    print(f"  • 本地监听: http://127.0.0.1:{PORT}")
    print(f"  • 上游地址: {UPSTREAM_BASE}")
    print(f"  • 认证状态: {'✅ 成功加载 Token (有效期至: ' + exp_str + ')' if token else '⚠️ 未检测到 Token (需打开小浣熊客户端或配置环境变量)'}")
    print("-" * 65)
    print("  核心推荐模型:")
    for m in CORE_MODELS:
        print(f"    - {m['id']:22s} -> {m['display_name']}")
    print("-" * 65)
    print("  端点指南:")
    print(f"    GET  http://127.0.0.1:{PORT}/v1/models")
    print(f"    POST http://127.0.0.1:{PORT}/v1/chat/completions")
    print(f"    GET  http://127.0.0.1:{PORT}/health")
    print("=" * 65)

    server = ThreadingHTTPServer(("0.0.0.0", PORT), RaccoonProxyHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[INFO] 服务已平稳停止。")
        server.server_close()

if __name__ == "__main__":
    main()
