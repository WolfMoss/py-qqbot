"""
QQ Bot 主程序入口
基于腾讯官方 qq-botpy SDK，使用 AppID + AppSecret 鉴权方式
参考：https://github.com/HKUDS/nanobot 的 QQ 频道接入方式
"""

import asyncio
import botpy
from botpy.message import Message, GroupMessage, DirectMessage
from botpy import BotAPI
from loguru import logger

from config import settings
from message_handler import MessageHandler


class QQBot(botpy.Client):
    """QQ Bot 主客户端"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message_handler = MessageHandler()

    async def on_ready(self):
        """Bot 启动就绪事件"""
        logger.info(f"✅ Bot [{self.robot.name}] 已启动，AppID: {self.robot.id}")

    # ──────────────────────────────────────────────
    # 频道消息事件
    # ──────────────────────────────────────────────

    async def on_at_message_create(self, message: Message):
        """频道内被 @ 时触发"""
        logger.info(f"[频道@消息] 来自 {message.author.username}: {message.content}")
        reply = await self.message_handler.handle(message.content, source="guild")
        await message.reply(content=reply)

    async def on_public_message_create(self, message: Message):
        """频道内公开消息（需开通权限）"""
        logger.info(f"[频道消息] 来自 {message.author.username}: {message.content}")
        reply = await self.message_handler.handle(message.content, source="guild_public")
        await message.reply(content=reply)

    # ──────────────────────────────────────────────
    # 单聊（好友私信）事件
    # ──────────────────────────────────────────────

    async def on_c2c_message_create(self, message: GroupMessage):
        """QQ 单聊（好友消息）"""
        logger.info(f"[单聊消息] 来自 {message.author.user_openid}: {message.content}")
        reply = await self.message_handler.handle(
            message.content,
            source="c2c",
            channel_user_id=str(message.author.user_openid),
        )
        await message.reply(content=reply)

    # ──────────────────────────────────────────────
    # 群聊事件
    # ──────────────────────────────────────────────

    async def on_group_at_message_create(self, message: GroupMessage):
        """QQ 群聊中被 @ 时触发"""
        logger.info(f"[群聊@消息] 群组 {message.group_openid}, 用户 {message.author.member_openid}: {message.content}")
        reply = await self.message_handler.handle(
            message.content,
            source="group",
            channel_user_id=str(message.author.member_openid),
        )
        await message.reply(content=reply)

    # ──────────────────────────────────────────────
    # 频道私信事件
    # ──────────────────────────────────────────────

    async def on_direct_message_create(self, message: DirectMessage):
        """频道私信消息"""
        logger.info(f"[频道私信] 来自 {message.author.username}: {message.content}")
        # direct 目前没有明确定义“固定会话用户”的字段映射，这里先保持旧逻辑（不触发 iflow 链接会话）
        reply = await self.message_handler.handle(message.content, source="direct")
        await self.api.post_dms(
            guild_id=message.guild_id,
            content=reply,
            msg_id=message.id,
        )


def main():
    logger.info("🚀 正在启动 QQ Bot...")
    logger.info(f"   AppID  : {settings.APP_ID}")
    logger.info(f"   沙盒模式: {settings.SANDBOX}")

    intents = botpy.Intents(
        public_guild_messages=True,    # 频道 @ 消息
        direct_message=True,           # 频道私信
        guild_messages=True,           # 全量频道消息（需申请）
        c2c_messages=True,             # 单聊消息
        group_at_messages=True,        # 群聊 @ 消息
    )

    client = QQBot(intents=intents, is_sandbox=settings.SANDBOX)
    client.run(appid=settings.APP_ID, secret=settings.APP_SECRET)


if __name__ == "__main__":
    main()
