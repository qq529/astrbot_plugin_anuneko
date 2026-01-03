# astrbot_plugin_anuneko

AnuNeko AI 对话插件，基于 [anuneko.com](https://anuneko.com) API 开发，支持多模型切换与分支对话决策。

## 安装

1.  将本项目克隆到 AstrBot 的 `data/plugins/` 目录下：
    ```bash
    git clone https://github.com/YourUsername/astrbot_plugin_anuneko.git astrbot_plugin_anuneko
    ```
2.  安装依赖：
    ```bash
    pip install -r requirements.txt
    ```
3.  重启 AstrBot。

## 配置

在 AstrBot WebUI 的插件配置页面找到 `AnuNeko`，填入从 [anuneko.com](https://anuneko.com) 获取的 `x-token`。

## 指令

| 指令 | 说明 | 示例 |
| --- | --- | --- |
| `/anu [内容]` | 与 AI 进行对话 | `/anu 你好` |
| `/anu model [模型名称]` | 切换当前会话的模型 | `/anu model Orange Cat` |

## 特性

- **自动分支选择**：当 API 返回多个分支选项时，插件会自动选择默认分支（index 0）并继续对话。
- **会话持久化**：用户的 `chat_id` 会保存在本地 `data/anuneko_sessions.json` 中，重启不丢失。
