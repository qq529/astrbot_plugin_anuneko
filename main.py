import httpx
import json
import os
import time
import aiofiles
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger

BASE_URL = "https://anuneko.com/api/v1"
DATA_DIR = "data/anuneko_sessions.json"  # 会话存储文件

@register("anuneko", "YourName", "AnuNeko AI 对话插件，基于 anuneko.com API，支持分支决策", "1.0.0", "https://github.com/YourUsername/astrbot_plugin_anuneko.git")
class Main(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.x_token = ""
        # 兼容性处理：尝试不同的配置获取方式
        if hasattr(context, "config"):
             self.config = context.config.get("anuneko", {})
             self.x_token = self.config.get("x_token")
        else:
             logger.warning("Context object has no config attribute. Please check AstrBot version.")

        if not self.x_token:
            logger.warning("AnuNeko x-token 未配置，请在 WebUI 设置。")

        # 加载会话数据
        self.sessions = self.load_sessions()

    @filter.command("anu", aliases=["anuneko"])
    async def anu_handler(self, event: AstrMessageEvent):
        message_str = event.message_str.strip()
        parts = message_str.split(maxsplit=1)
        cmd = parts[0].lower() if parts else ""
        content = parts[1].strip() if len(parts) > 1 else ""
        
        # 尝试获取发送者ID，兼容不同版本
        if hasattr(event, "sender_id"):
            user_id = event.sender_id
        elif hasattr(event, "get_sender_id"):
            user_id = event.get_sender_id()
        else:
            user_id = "unknown_user"

        if cmd == "model" and content:
            await self.switch_model(user_id, content)
            yield event.plain_result(f"模型切换为 {content}")
            return

        # 如果不是特殊指令，将整个消息作为内容（修复原逻辑可能丢失第一个词的问题）
        if cmd != "model":
            content = message_str

        if not content:
             yield event.plain_result("请输入内容。")
             return

        # 获取或创建 chat_id
        chat_id = self.get_chat_id(user_id)

        # 发送消息
        try:
            response = await self.send_message(chat_id, content)
            
            # 处理响应
            # httpx response 使用 .text 获取文本内容
            full_response = response.text
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            yield event.plain_result(f"API 请求失败: {e}")
            return

        # 解析响应
        try:
            # 尝试解析 JSON
            data = json.loads(full_response)
            reply = data.get("reply", "未知响应")
            choices = data.get("choices", [])
            if choices:
                # 自动选择 0
                await self.select_choice(chat_id, 0)
                reply += "\n(自动选择分支 0 继续对话)"
        except json.JSONDecodeError:
            # 如果不是 JSON，直接返回原文
            reply = full_response or "响应解析失败"

        yield event.plain_result(reply)

        # 保存会话
        self.save_sessions()

    async def send_message(self, chat_id: str, content: str):
        url = f"{BASE_URL}/msg/{chat_id}/stream"
        headers = {
            "x-token": self.x_token,
            "Content-Type": "application/json" # 修正为 application/json
        }
        data = json.dumps({"contents": [content]})
        async with httpx.AsyncClient() as client:
            return await client.post(url, headers=headers, content=data, timeout=60)

    async def select_choice(self, chat_id: str, idx: int):
        url = f"{BASE_URL}/msg/select-choice"
        headers = {
            "x-token": self.x_token,
            "Content-Type": "application/json"
        }
        data = json.dumps({"msg_id": chat_id, "choice_idx": idx})
        async with httpx.AsyncClient() as client:
            await client.post(url, headers=headers, content=data)

    async def switch_model(self, user_id: str, model: str):
        chat_id = self.get_chat_id(user_id)
        url = f"{BASE_URL}/user/select_model"
        headers = {
            "x-token": self.x_token,
            "Content-Type": "application/json"
        }
        data = json.dumps({"chat_id": chat_id, "model": model})
        async with httpx.AsyncClient() as client:
            await client.post(url, headers=headers, content=data)

    def get_chat_id(self, user_id: str) -> str:
        if user_id not in self.sessions:
            # 使用 time.time() 替代 os.time()
            chat_id = f"{user_id}_{int(time.time())}"
            self.sessions[user_id] = {"chat_id": chat_id, "model": "Orange Cat"}
        return self.sessions[user_id]["chat_id"]

    def load_sessions(self) -> dict:
        if os.path.exists(DATA_DIR):
            try:
                with open(DATA_DIR, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_sessions(self):
        try:
            os.makedirs(os.path.dirname(DATA_DIR), exist_ok=True)
            with open(DATA_DIR, "w", encoding="utf-8") as f:
                json.dump(self.sessions, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存会话失败: {e}")
