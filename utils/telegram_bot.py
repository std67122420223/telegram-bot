import os
from telegram import Bot
from utils.logger import sys_logger

class TelegramNotificationEngine:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.bot = Bot(token=self.token) if self.token and self.chat_id else None

    async def send_signal_alert(self, symbol: str, signal_data: dict):
        """ส่งสัญญาณจัดรูปแบบด่วน ทรงพลัง และปลอดภัยตามรูปที่กำหนด"""
        if not self.bot:
            sys_logger.warning("สคริปต์ตรวจไม่พบตัวแปรสภาพแวดล้อมสำหรับแจ้งเตือน Telegram")
            return
        
        message = (
            f"🚨 {symbol} SIGNAL\n\n"
            f"ตามๆ : {signal_data['signal']}\n\n"
            f"จุดเข้า : {signal_data['entry']}\n"
            f"SL : {signal_data['sl']}\n"
            f"TP : {signal_data['tp']}\n\n"
            f"คะแนนซื้อ : {signal_data['buy_score']}\n"
            f"คะแนนขาย : {signal_data['sell_score']}"
        )
        try:
            await self.bot.send_message(chat_id=self.chat_id, text=message)
            sys_logger.info("แพ็กเกจสัญญาณ Siren ส่งผ่านไปทาง API สำเร็จ")
        except Exception as e:
            sys_logger.error(f"การเชื่อมโยงสัญญาณโทรศัพท์ขัดข้อง: {e}")

    async def send_status_update(self, status_type: str):
        if not self.bot: return
        msg_map = {
            "BREAKEVEN": "🔒 กันหน้าทุน",
            "LOSS": "🛑 ขาดทุน",
            "PROFIT": "💰 ปิดทำกำไรเรียบร้อยแล้ว (TP)"
        }
        msg = msg_map.get(status_type, f"ℹ️ อัปเดตข้อมูลพอร์ต: {status_type}")
        try:
            await self.bot.send_message(chat_id=self.chat_id, text=msg)
        except Exception as e:
            sys_logger.error(f"แจ้งสถานะอัปเดตล้มเหลว: {e}")