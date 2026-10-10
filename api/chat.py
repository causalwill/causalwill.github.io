import os
import json
import requests
from http.server import BaseHTTPRequestHandler

API_URL = "https://api.deepseek.com/chat/completions"

# 数字分身的人设：想让它知道什么，都写在这里
SYSTEM_PROMPT = """你是「周裔」的数字分身，替她和主页访客聊天。

【关于周裔】
- 她是一名女大学生，正在学习使用 AI，擅长内容表达、AI 应用和知识整理，喜欢把复杂问题讲成人话。
- 她最近在做两件事：搭建个人主页；把这学期的课程内容整理成自己的笔记。
- 她做事喜欢先做计划再一步步执行，过程中也会灵活调整。
- 兴趣是拍照、写作、听音乐。
- 联系方式：邮箱 1248536271@qq.com，其他联系方式不要透露。

【回答风格】
- 语气温柔、口语化，像朋友聊天，回答中适当加入表情。
- 只回答与周裔的近况、在整理的资料、学习难度、拍照写作等有关的问题，不要编造她的经历。
- 当问题超出回答范围时，原样使用这句话回答：
  "唔……这个问题好像超出我的回答范围了 😅 我只了解「周裔」的近况、在整理的资料、学习难度，还有拍照写作这些事～你可以点下面的快捷问题，或者换个方式问问看 🌿"
"""


class handler(BaseHTTPRequestHandler):
    """Vercel Python 云函数入口：文件放在 api/chat.py，即对应接口 /api/chat"""

    def _json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        # 浏览器跨域预检请求，直接放行
        self._json(200, {})

    def do_POST(self):
        # 1. 读取前端发来的对话内容
        try:
            length = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(length) or b"{}")
        except Exception:
            self._json(400, {"error": "bad request"})
            return

        # 2. 从环境变量取 Key（Key 在 Vercel 后台填写，不在代码里）
        key = os.environ.get("DEEPSEEK_API_KEY")
        if not key:
            self._json(500, {"error": "missing DEEPSEEK_API_KEY"})
            return

        # 3. 拼上人设 + 对话历史，转发给 DeepSeek
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages += payload.get("messages", [])

        try:
            r = requests.post(
                API_URL,
                headers={
                    "Authorization": "Bearer " + key,
                    "Content-Type": "application/json",
                },
                json={
                    "model": "deepseek-chat",
                    "messages": messages,
                    "temperature": 0.8,
                },
                timeout=60,
            )
            self._json(r.status_code, r.json())
        except Exception as e:
            self._json(500, {"error": str(e)})
