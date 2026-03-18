"""
消息处理器
在此实现你的 Bot 业务逻辑：回显、AI 接入、指令解析等
"""

import json
import re
from typing import Optional

import httpx
from loguru import logger

from config import settings


class MessageHandler:
    """
    统一消息处理入口。
    你可以在 handle() 中扩展：
      - 对接 LLM（OpenAI / Claude / Gemini ...）
      - 指令路由（!帮助、!天气 ...）
      - 关键词触发
    """

    # ── 内置指令表 ────────────────────────────────
    COMMANDS = {
        "/帮助": "📖 支持以下指令：\n/帮助 - 显示帮助\n/ping - 连通测试\n/echo <内容> - 回显消息",
        "/ping": "🏓 Pong! Bot 在线运行中。",
    }

    async def handle(
        self,
        raw_content: str,
        source: str = "unknown",
        channel_user_id: Optional[str] = None,
    ) -> str:
        """
        处理一条消息，返回回复字符串。

        :param raw_content: 原始消息文本（可能含 @ 机器人的 mention）
        :param source: 消息来源标识（guild / c2c / group / direct）
        :return: 回复文本
        """
        content = self._clean(raw_content)
        logger.debug(f"[{source}] 处理消息: {content!r}")

        # 0. 链接类消息：走 iflow-agent 网关流式对话
        if self._is_link_like(content):
            if not channel_user_id:
                # 没有用户标识则无法保证稳定会话；仍尝试新会话
                channel_user_id = "unknown"
            message_for_iflow = self._message_for_iflow(content)
            logger.debug(f"[{source}] 处理url: {message_for_iflow!r}")
            return await self._handle_iflow_link(message_for_iflow, source, channel_user_id)

        # 1. 空消息
        if not content:
            return "你好！有什么可以帮你的吗？"

        # 2. 内置指令
        for cmd, reply in self.COMMANDS.items():
            if content.startswith(cmd):
                return reply

        # 3. /echo 指令
        if content.startswith("/echo "):
            return content[len("/echo "):]

        # 4. 默认回显（此处可替换为 LLM 调用）
        prefix = settings.REPLY_PREFIX
        return f"{prefix}收到你的消息：{content}\n\n（提示：可在 handlers/message_handler.py 中接入 LLM 或扩展逻辑）"

    # 单行内首个 http(s) URL（到空白为止；去掉常见尾部标点）
    _URL_IN_LINE = re.compile(r"https?://\S+", re.IGNORECASE)

    @classmethod
    def _is_link_like(cls, content: str) -> bool:
        """含 http(s) 即视为可走链接链路；多行分享类由 _message_for_iflow 取第二行链接。"""
        if not content:
            return False
        return ("http://" in content) or ("https://" in content)

    @classmethod
    def _extract_second_line_url(cls, content: str) -> Optional[str]:
        """
        从第二行提取链接。适用于：
        [分享]标题\\nhttps://...\\n…\\n完整链接\\n来自: ...
        按需求使用第二行上的 URL（可能为截断链接）。
        """
        lines = content.splitlines()
        if len(lines) < 2:
            return None
        second = lines[1].strip()
        m = cls._URL_IN_LINE.search(second)
        if not m:
            return None
        url = m.group(0).rstrip(").,;，。、]")
        return url or None

    @classmethod
    def _message_for_iflow(cls, content: str) -> str:
        """
        只发 URL：多行分享类取第二行链接；否则取全文里第一个 http(s) URL；都没有则回退原文。
        """
        url2 = cls._extract_second_line_url(content)
        if url2:
            return url2
        m = cls._URL_IN_LINE.search(content)
        if m:
            return m.group(0).rstrip(").,;，。、]")
        return content

    async def _handle_iflow_link(
        self,
        user_text: str,
        source: str,
        channel_user_id: str,
    ) -> str:
        """
        调用 iflow-agent：
        - POST /api/chat 返回 SSE
        - 拼接所有 assistant_chunk.text 作为最终回复
        """
        chat_url = settings.iflow_chat_url()

        payload = {
            "message": user_text,
            "channel": source if source else "web",
            "channel_user_id": channel_user_id,
        }
        # 不主动传 session_id：让 iflow-agent 按稳定会话策略处理。

        assistant_text_parts: list[str] = []
        last_event_type: str | None = None

        timeout = settings.iflow_http_timeout_seconds()
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                # 以流方式读取 SSE
                resp = await client.post(chat_url, json=payload, headers={"Accept": "text/event-stream"})
                resp.raise_for_status()

                async for raw_line in resp.aiter_lines():
                    if not raw_line:
                        continue
                    # SSE 只关心 data: 行；其余（例如 event:) 直接忽略
                    if not raw_line.startswith("data:"):
                        continue
                    data_str = raw_line[len("data:"):].strip()
                    if not data_str:
                        continue

                    try:
                        event = json.loads(data_str)
                    except Exception:
                        logger.warning("解析 SSE data 失败: %r", data_str)
                        continue

                    last_event_type = str(event.get("type") or "")
                    if last_event_type == "assistant_chunk":
                        text = event.get("text") or ""
                        if text:
                            assistant_text_parts.append(str(text))
                    elif last_event_type == "task_finish":
                        break
                    elif last_event_type == "error":
                        msg = event.get("message") or "iflow-agent error"
                        return f"链接请求处理中出现错误：{msg}"

        except httpx.TimeoutException:
            logger.exception("iflow-agent SSE 超时")
            return "链接请求处理中断（超时），请稍后再试。"
        except Exception:
            logger.exception("iflow-agent SSE 调用失败")
            return "链接请求处理中断（通信失败），请稍后再试。"

        final_text = "".join(assistant_text_parts).strip()
        if final_text:
            return final_text
        # 如果没有拿到 assistant_chunk，给一个可读兜底
        return "我已收到链接请求，但未能生成回复内容。请再发一次或更换链接。"

    # ─────────────────────────────────────────────

    @staticmethod
    def _clean(text: str) -> str:
        """去除 @机器人 的 mention 标签，清理首尾空白"""
        # QQ 频道的 mention 格式：<@!BOTID> 或 <@BOTID>
        text = re.sub(r"<@!?\d+>", "", text)
        return text.strip()
