import os
import logging
import requests
import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes, JobQueue

# 基础配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 全局数据
global_data = {
    "last_price": "正在获取中...",
    "owner_id": 8178986441,
    "authorized_operators": set()
}

# 获取实时黄金价格的函数 (无需 MT5)
def get_gold_price():
    try:
        # 使用公共的 API 获取金价 (例如使用 Yahoo Finance 或类似的公开源)
        # 这里以一个示例接口为例，你可以搜索 "gold price api" 替换为你需要的源
        response = requests.get("https://api.metals.live/v1/spot/gold")
        data = response.json()
        price = data[0]['price']
        return f"{price:.2f}"
    except Exception as e:
        logger.error(f"获取金价失败: {e}")
        return "获取失败"

# 定时任务：每分钟自动更新一次价格
async def update_price_job(context: ContextTypes.DEFAULT_TYPE):
    global_data["last_price"] = get_gold_price()

# Telegram 处理逻辑
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    
    # 权限检查
    if user_id != global_data["owner_id"] and user_id not in global_data["authorized_operators"]:
        return

    if "查看" in text:
        await update.message.reply_text(f"💰 **当前实时金价:** {global_data['last_price']}\n📊 分析: 建议操作请关注趋势。")

def main():
    # 使用 ApplicationBuilder 显式启用 JobQueue
    app = Application.builder().token(os.environ.get("TELEGRAM_BOT_TOKEN")).build()
    
    # 手动添加 JobQueue (如果上面的 build 没有自动创建的话)
    job_queue = app.job_queue
    
    # 添加定时任务 (每60秒运行一次)
    job_queue.run_repeating(update_price_job, interval=60, first=1)
    
    # 添加处理器
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    
    # 启动
    app.run_polling()

if __name__ == "__main__":
    main()
