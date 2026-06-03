import os
import logging
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CommandHandler

# 基础配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 全局数据存储
global_data = {
    "last_price": "连接中...",
    "owner_id": 8178986441,
    "authorized_operators": set(),
    "settings": {"language": "cn"}
}

# 1. 接收 MT5 价格的 Web 服务器
class MT5DataReceiver(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        try:
            data = json.loads(post_data)
            if "price" in data:
                global_data["last_price"] = str(data["price"])
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"status":"ok"}')
        except Exception:
            self.send_error(400)

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), MT5DataReceiver)
    server.serve_forever()

# 2. Telegram 指令逻辑
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    
    # 权限检查
    if user_id != global_data["owner_id"] and user_id not in global_data["authorized_operators"]:
        return

    # 报价与分析
    if "查看" in text or "price" in text.lower():
        await update.message.reply_text(f"💰 实时报价: {global_data['last_price']}\n📊 分析: 建议操作请参考实时趋势。")
    
    # 设置语言
    elif text.startswith("/lang "):
        lang = text.split(" ")[1]
        global_data["settings"]["language"] = lang
        await update.message.reply_text(f"Language set to {lang}")

    # 管理操作人
    elif text.startswith("/add "):
        new_op = int(text.split(" ")[1])
        global_data["authorized_operators"].add(new_op)
        await update.message.reply_text(f"已授权操作人: {new_op}")
        
    elif text.startswith("/remove "):
        rem_op = int(text.split(" ")[1])
        if rem_op in global_data["authorized_operators"]:
            global_data["authorized_operators"].remove(rem_op)
            await update.message.reply_text(f"已移除操作人: {rem_op}")

def main():
    # 启动价格接收后台
    threading.Thread(target=run_server, daemon=True).start()
    
    # 启动 Telegram Bot
    app = Application.builder().token(os.environ.get("TELEGRAM_BOT_TOKEN")).build()
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
