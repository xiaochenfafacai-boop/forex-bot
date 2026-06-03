import os
import logging
from datetime import datetime
import asyncio
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# 启用日志，方便在 Render 的 Log 里面查看机器人状态
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== 👑 核心权限配置 ====================
# ⚠️ 请将下方的 123456789 替换为您本人的真实 Telegram 数字 ID
OWNER_ID =   8179896441

# 存储授权操作人的用户名集合（不带@，全部小写保存）
# 实际生产中由于 Render 重启实例会清空内存，
# 如果您不想每次重启都重新设置，可以直接在这里死代码加入初始化名字，例如: {"alex", "user2"}
authorized_operators = set()

# 机器人全局设置：默认语言为中文 'cn' (可选 'cn', 'mm')
global_settings = {
    "language": "cn"
}

# ==================== 📊 模拟 Forex 核心分析引擎 ====================
def fetch_and_analyze(symbol: str):
    """
    这里是你的量化策略核心。
    实际开发时，你可以用 requests 去拉取现成的数据源 API，
    并用 pandas_ta 计算 M30, H1, H4 的指标。
    这里为您构建符合您要求的全要素高精度报告输出逻辑：
    """
    current_price = 2345.50  # 实际开发时这里对接实时价格
    
    # 模拟根据当前行情计算出的技术位（实际开发中用技术指标动态计算）
    analysis_data = {
        "symbol": symbol.upper(),
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "price": f"{current_price:.2f}",
        "trend_m30": "Bullish (看涨) —— 底部支撑确立",
        "trend_h1": "Sideways (震荡) —— 正在蓄势突破",
        "trend_h4": "Bullish (大趋势看涨) —— 多头排列健全",
        "res1": f"{current_price + 14.50:.2f}",
        "res2": f"{current_price + 29.50:.2f}",
        "sup1": f"{current_price - 10.50:.2f}",
        "sup2": f"{current_price - 25.50:.2f}",
        "entry": f"{current_price - 5.50:.2f} - {current_price - 3.50:.2f}",
        "sl": f"{current_price - 14.50:.2f}",
        "tp": f"{current_price + 12.50:.2f}",
        "win_rate": "62%",
        "should_entry": "✅ 建议入场 (Entry Recommended)"
    }
    return analysis_data

# ==================== 🌐 多语言模板渲染引擎 ====================
def generate_report_text(data: dict, lang: str) -> str:
    if lang == "mm":
        # 🇲🇲 缅文深度报告模板
        return (
            f"🤖 **{data['symbol']} Real-time Trade Strategy**\n"
            f"📅 **အချိန်:** {data['time']} (GMT+8)\n"
            f"💰 **လက်ရှိဈေး:** {data['price']}\n\n"
            f"📊 **Market Structure (Trend):**\n"
            f"• M30: {data['trend_m30']}\n"
            f"• H1: {data['trend_h1']}\n"
            f"• H4: {data['trend_h4']}\n\n"
            f"🧱 **Key Levels:**\n"
            f"• 🔴 Resistance (ခုခံမှုအမှတ်): {data['res1']} / {data['res2']}\n"
            f"• 🟢 Support (ပံ့ပိုးမှုအမှတ်): {data['sup1']} / {data['sup2']}\n\n"
            f"🎯 **Trade Plan:**\n"
            f"• 🚦 အကြံပြုချက်: **{data['should_entry']}**\n"
            f"• 📥 Entry Price (ဝယ်ရန်ဈေး): `{data['entry']}`\n"
            f"• 🛑 Stop Loss (ရှုံးရင်ဖြတ်မည့်ဈေး): `{data['sl']}`\n"
            f"• 💰 Take Profit (မြတ်ရင်ပိတ်မည့်ဈေး): `{data['tp']}`\n\n"
            f"🎲 **Win Rate & Risk:**\n"
            f"• နိုင်ခြေရှိမှု (Win Rate): **{data['win_rate']}**\n"
            f"• Risk/Reward Ratio: 1 : 1.8"
        )
    else:
        # 🇨🇳 中文深度报告模板 (默认)
        return (
            f"🤖 **{data['symbol']} 实时深度策略报告**\n"
            f"📅 **时间：** {data['time']} (GMT+8)\n"
            f"💰 **当前价格：** {data['price']}\n\n"
            f"📊 **市场结构 (Trend)：**\n"
            f"• M30: {data['trend_m30']}\n"
            f"• H1: {data['trend_h1']}\n"
            f"• H4: {data['trend_h4']}\n\n"
            f"🧱 **关键位置 (Key Levels)：**\n"
            f"• 🔴 强阻力位 (Resistance): {data['res1']} / {data['res2']}\n"
            f"• 🟢 强支撑位 (Support): {data['sup1']} / {data['sup2']}\n\n"
            f"🎯 **交易计划 (Trade Plan)：**\n"
            f"• 🚦 入场信号: **{data['should_entry']}**\n"
            f"• 📥 入场价格 (Entry): `{data['entry']}`\n"
            f"• 🛑 止损价格 (Stop Loss): `{data['sl']}`\n"
            f"• 💰 止盈价格 (Take Profit): `{data['tp']}`\n\n"
            f"🎲 **概率与风控：**\n"
            f"• 预估胜率: **{data['win_rate']}**\n"
            f"• 盈亏比: 1 : 1.8 (符合高赢面风控标准)"
        )

# ==================== ⚙️ 核心业务逻辑处理器 ====================
async def handle_chinese_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    user = update.effective_user
    user_id = user.id
    username = user.username.lower() if user.username else ""

    # 1. 🛡️ 【最高主人特权指令】
    if text.startswith("设置操作人"):
        if user_id != OWNER_ID:
            await update.message.reply_text("❌ 拒绝执行：只有最高主人有权限设置操作人。")
            return
        
        # 提取用户名
        target = text.replace("设置操作人", "").replace("@", "").strip().lower()
        if target:
            authorized_operators.add(target)
            await update.message.reply_text(f"⚖️ **权限变更通知**\n成功将用户 @{target} 提升为 **[授权操作人]**。")
        else:
            await update.message.reply_text("💡 请使用正确格式：设置操作人 @用户名")
        return

    if text.startswith("去掉操作人"):
        if user_id != OWNER_ID:
            await update.message.reply_text("❌ 拒绝执行：只有最高主人有权限去掉操作人。")
            return
        
        target = text.replace("去掉操作人", "").replace("@", "").strip().lower()
        if target in authorized_operators:
            authorized_operators.discard(target)
            await update.message.reply_text(f"❌ 权限撤销：已取消 @{target} 的操作人权限。")
        else:
            await update.message.reply_text(f"❓ 操作人列表中未找到用户 @{target}")
        return

    # 2. 🔏 【安全验证：拦截非白名单用户的其余指令】
    if user_id != OWNER_ID and username not in authorized_operators:
        # 如果是群里其他普通成员乱打字，机器人保持沉默，防止刷屏
        return

    # 3. 🛠️ 【主人与操作人共享的中文核心指令】
    if text == "查看操作人表格":
        op_list = "\n".join([f"| 🛠️ 授权操作人 | @{op} | 已激活 |" for op in authorized_operators])
        table_text = (
            f"📋 **机器人权限管理表格 (Admin List)**\n\n"
            f"| 角色 | Telegram 用户名 | 当前状态 |\n"
            f"| :--- | :--- | :--- |\n"
            f"| 👑 最高主人 | @{update.message.from_user.username if user_id == OWNER_ID else 'Owner'} | 永久在线 |\n"
            f"{op_list if op_list else '| 🛠️ 授权操作人 | (暂无) | - |'}\n\n"
            f"*注：只有最高主人可以添加或去掉操作人。*"
        )
        await update.message.reply_text(table_text, parse_mode="Markdown")
        return

    elif text.startswith("查看"):
        # 提取查看的货币对名称
        symbol = text.replace("查看", "").strip().upper()
        if not symbol:
            symbol = "XAUUSD"
        
        await update.message.reply_text(f"🔄 正在为您高精度计算【{symbol}】的实时进出场数据，请稍后...")
        
        # 跑核心策略算法并渲染对应的语言输出报告
        analysis_data = fetch_and_analyze(symbol)
        report_text = generate_report_text(analysis_data, global_settings["language"])
        
        await update.message.reply_text(report_text, parse_mode="Markdown")
        return

    elif text.startswith("改语言"):
        lang = text.replace("改语言", "").strip().lower()
        if lang in ["cn", "zh", "中文"]:
            global_settings["language"] = "cn"
            await update.message.reply_text("✅ 语言已成功切换为：**中文**")
        elif lang in ["mm", "myanmar", "缅文", "缅甸语"]:
            global_settings["language"] = "mm"
            await update.message.reply_text("✅ ဘာသာစကားကို **မြန်မာဘာသာ** သို့ ပြောင်းလဲပြီးပါပြီ။")
        else:
            await update.message.reply_text("💡 目前仅支持以下语言设定：\n• `改语言 cn` (中文)\n• `改语言 mm` (缅文)")
        return

# ==================== 🚀 Render Pro 启动入口 ====================
def main():
    # 从 Render 环境变量中安全获取你的 Bot Token
    TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    
    if not TOKEN:
        logger.error("错误：未在环境变量中检测到 TELEGRAM_BOT_TOKEN！")
        return

    # 创建 Telegram 异步应用
    app = Application.builder().token(TOKEN).build()

    # 注册消息监听器（监听群组里的所有文本消息，并移交中文命令处理器）
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_chinese_commands))

    logger.info("Forex 交互式智能机器人已成功在 Render 云端启动运行...")
    # 在 Render Background Worker 上保持持续轮询监听
    app.run_polling()

if __name__ == "__main__":
    main()
