"""
消息处理器
在此实现你的 Bot 业务逻辑：回显、AI 接入、指令解析等
"""

import re
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

    async def handle(self, raw_content: str, source: str = "unknown") -> str:
        """
        处理一条消息，返回回复字符串。

        :param raw_content: 原始消息文本（可能含 @ 机器人的 mention）
        :param source: 消息来源标识（guild / c2c / group / direct）
        :return: 回复文本
        """
        content = self._clean(raw_content)
        logger.debug(f"[{source}] 处理消息: {content!r}")

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

    # ─────────────────────────────────────────────

    @staticmethod
    def _clean(text: str) -> str:
        """去除 @机器人 的 mention 标签，清理首尾空白"""
        # QQ 频道的 mention 格式：<@!BOTID> 或 <@BOTID>
        text = re.sub(r"<@!?\d+>", "", text)
        return text.strip()
