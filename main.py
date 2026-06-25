import os
import time
import yaml
import ccxt
import pandas as pd
import requests

# โหลดไฟล์ตั้งค่า Config
def load_config():
    with open("config/config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# ฟังก์ชันส่งข้อความเข้า Telegram ดึงรหัสจาก Environment บน Cloud
def send_telegram_message(message):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        print("⚠️ [Error] ไม่พบข้อมูล TELEGRAM_BOT_TOKEN หรือ TELEGRAM_CHAT_ID ใน Environment")
        return
        
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"⚠️ ไม่สามารถส่งข้อความ Telegram ได้: {e}")

def main():
    print("🤖 [LIVE] บอทเริ่มเปิดระบบเฝ้ากราฟราคาทองคำจริงบน Cloud...")
    config = load_config()
    
    # เชื่อมต่อโบรกเกอร์ผ่าน CCXT (ใช้ Bybit เป็นหลักในการดึงราคาสปอต)
    exchange = ccxt.bybit()
    symbol = config['bot']['symbol']
    timeframe = config['bot']['timeframe']
    
    from strategy.smc_strategy import analyze_smc
    
    while True:
        try:
            # ดึงข้อมูลแท่งเทียนล่าสุด
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=50)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # วิเคราะห์กลยุทธ์
            buy_score, sell_score, current_price = analyze_smc(df)
            
            print(f"👀 [SCANNING] ราคาทองปัจจุบัน: {current_price:.2f} | คะแนน BUY: {buy_score}/8 | คะแนน SELL: {sell_score}/8")
            
            # ตรวจสอบเงื่อนไขสัญญาณ (คะแนนแตะ 8 เต็ม)
            if buy_score >= config['strategy']['score_threshold']:
                sl = current_price - (config['strategy']['sl_pips'] / 10)
                tp = current_price + (config['strategy']['tp_pips'] / 10)
                msg = f"🔔 *[SMC SIGNAL: BUY]*\n📈 ราคาทองคำ: {current_price:.2f}\n🎯 TP: {tp:.2f}\n🛑 SL: {sl:.2f}\n🔥 คะแนนความแม่นยำ: {buy_score}/8"
                send_telegram_message(msg)
                time.sleep(300) # พักระบบ 5 นาทีหลังส่งซิกแนล
                
            elif sell_score >= config['strategy']['score_threshold']:
                sl = current_price + (config['strategy']['sl_pips'] / 10)
                tp = current_price - (config['strategy']['tp_pips'] / 10)
                msg = f"🔔 *[SMC SIGNAL: SELL]*\n📉 ราคาทองคำ: {current_price:.2f}\n🎯 TP: {tp:.2f}\n🛑 SL: {sl:.2f}\n🔥 คะแนนความแม่นยำ: {sell_score}/8"
                send_telegram_message(msg)
                time.sleep(300)
                
        except Exception as e:
            print(f"⚠️ เกิดข้อผิดพลาดในระบบ: {e}")
            
        # หน่วงเวลาสแกนรอบถัดไปตามที่ตั้งไว้ใน Config (เช่น ทุก 60 วินาที)
        time.sleep(config['bot']['scan_interval_seconds'])

if __name__ == "__main__":
    main()