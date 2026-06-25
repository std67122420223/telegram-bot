import pandas as pd
import numpy as np

class SmartMoneyConceptsStrategy:
    def __init__(self, config: dict):
        self.config = config['strategies']['smc_engine']

    def analyze_market_structure(self, df: pd.DataFrame) -> dict:
        """ระบบวิเคราะห์หาโครงสร้างราคาและแท่งเทียนกลับตัวที่มีความแม่นยำสูง (Win Rate เน้นย้ำ)"""
        signals = {"signal": "NEUTRAL", "entry": 0.0, "sl": 0.0, "tp": 0.0, "buy_score": 0, "sell_score": 0}
        if len(df) < 5: 
            return signals

        # ดึงราคาแท่งเทียนปัจจุบันและย้อนหลังมาวิเคราะห์โครงสร้าง
        current_close = df['close'].iloc[-1]
        current_high = df['high'].iloc[-1]
        current_low = df['low'].iloc[-1]
        
        prev_close = df['close'].iloc[-2]
        prev_high = df['high'].iloc[-2]
        prev_low = df['low'].iloc[-2]

        # 1. การคำนวณแนวโน้มหลัก (Trend Filter) ด้วยเส้นค่าเฉลี่ย
        ma_fast = df['close'].rolling(3).mean().iloc[-1]
        ma_slow = df['close'].rolling(5).mean().iloc[-1]
        
        is_bullish_trend = ma_fast > ma_slow
        is_bearish_trend = ma_fast < ma_slow

        # 2. ตัวกรองแท่งเทียนกลับตัวระดับองค์กร (SMC Liquidity Grab + Engulfing)
        buy_score = 0
        sell_score = 0

        # --- เงื่อนไขฝั่ง BUY (จุดกลับตัวเพื่อความแม่นยำสูง) ---
        if is_bullish_trend:
            buy_score += 3  # ได้คะแนนจากเทรนด์หลักขาขึ้น
        if current_close > prev_high:
            buy_score += 3  # เกิดการกลืนกินขาขึ้น (Bullish Engulfing) แท่งเทียนแข็งแรง ชนะราคาก่อนหน้า
        if current_low < prev_low and current_close > prev_close:
            buy_score += 2  # เกิด Liquidity Grab (ทิ้งไส้ล่างกวาด Stop loss แล้วดึงกลับทันที)
        
        # --- เงื่อนไขฝั่ง SELL (จุดกลับตัวเพื่อความแม่นยำสูง) ---
        if is_bearish_trend:
            sell_score += 3  # ได้คะแนนจากเทรนด์หลักขาลง
        if current_close < prev_low:
            sell_score += 3  # เกิดการกลืนกินขาลง (Bearish Engulfing) แท่งเทียนทุบแรง
        if current_high > prev_high and current_close < prev_close:
            sell_score += 2  # เกิด Liquidity Grab (สะบัดกินไส้บนก่อนทุบจริง)

        signals["buy_score"] = buy_score
        signals["sell_score"] = sell_score

        # 3. ตั้งค่าระยะปลอดภัยและ RR 1:2 (SL 700 จุด / TP 1500 จุด สำหรับราคาทองคำจริง)
        # หมายเหตุ: สำหรับทองคำ 700 จุด คือ $7 ดอลลาร์ และ 1500 จุด คือ $15 ดอลลาร์
        sl_distance = 7.0
        tp_distance = 15.0

        # บอทจะออกสัญญาณก็ต่อเมื่อคะแนนความแม่นยำเต็ม 8 คะแนนเท่านั้น (High Probability Setup)
        if buy_score >= 8:
            signals["signal"] = "BUY"
            signals["entry"] = round(current_close, 2)
            signals["sl"] = round(current_close - sl_distance, 2)
            signals["tp"] = round(current_close + tp_distance, 2)
            
        elif sell_score >= 8:
            signals["signal"] = "SELL"
            signals["entry"] = round(current_close, 2)
            signals["sl"] = round(current_close + sl_distance, 2)
            signals["tp"] = round(current_close - tp_distance, 2)

        return signals