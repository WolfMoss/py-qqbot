# QQ Bot

基于腾讯官方 [qq-botpy](https://github.com/tencent-connect/botpy) SDK 构建的 QQ 机器人，支持：

- ✅ QQ 频道 @ 消息
- ✅ QQ 频道私信
- ✅ QQ 单聊（好友消息）
- ✅ QQ 群聊 @ 消息
- ✅ 内置指令系统（可扩展）
- ✅ 可对接任意 LLM（OpenAI / Claude / Gemini ...）

接入方式参考：[HKUDS/nanobot](https://github.com/HKUDS/nanobot)

---

## 快速开始

### 1. 安装依赖

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. 配置凭据

```bash
cp .env.example .env
# 编辑 .env，填入你的 AppID 和 AppSecret
```

`.env` 文件内容示例：
```env
QQ_APP_ID=1903565953
QQ_APP_SECRET=XAlLsLl6MYjqvwvq
QQ_SANDBOX=true
```

> ⚠️ **安全提示**：`.env` 已加入 `.gitignore`，请勿将真实凭据提交到公开仓库。

### 3. 启动 Bot

```bash
python bot.py
```

---

## 项目结构

```
qq-bot/
├── bot.py                  # 主入口，Bot 客户端与事件监听
├── config.py               # 配置管理（从环境变量 / .env 读取）
├── handlers/
│   └── message_handler.py  # 消息处理逻辑（在此扩展业务）
├── requirements.txt
├── .env.example            # 配置模板
└── .gitignore
```

---

## 扩展：对接 LLM

编辑 `handlers/message_handler.py` 中的 `handle()` 方法，将默认回显替换为 LLM 调用：

```python
# 示例：对接 OpenAI
import openai

async def handle(self, raw_content: str, source: str = "unknown") -> str:
    content = self._clean(raw_content)
    response = await openai.ChatCompletion.acreate(
        model="gpt-4o",
        messages=[{"role": "user", "content": content}]
    )
    return response.choices[0].message.content
```

---

## 内置指令

| 指令 | 说明 |
|------|------|
| `/帮助` | 显示帮助信息 |
| `/ping` | 连通测试 |
| `/echo <内容>` | 回显消息 |

---

## 参考资料

- [QQ 机器人官方文档](https://bot.q.qq.com/wiki/)
- [qq-botpy SDK](https://github.com/tencent-connect/botpy)
- [HKUDS/nanobot](https://github.com/HKUDS/nanobot)
