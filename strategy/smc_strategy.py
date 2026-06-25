import pandas as pd

def analyze_smc(df):
    """
    ฟังก์ชันวิเคราะห์กลยุทธ์ SMC (Smart Money Concepts) 
    คืนค่าคะแนนความน่าจะเป็นในการ BUY หรือ SELL (เต็ม 8 คะแนน)
    """
    if len(df) < 20:
        return 0, 0, 0.0
        
    buy_score = 0
    sell_score = 0
    current_price = float(df['close'].iloc[-1])
    
    # 1. เช็กแนวโน้มด้วยเส้น EMA (ตัวอย่างการคำนวณแบบง่าย)
    ema_fast = df['close'].ewm(span=9, adjust=False).mean().iloc[-1]
    ema_slow = df['close'].ewm(span=21, adjust=False).mean().iloc[-1]
    
    if ema_fast > ema_slow:
        buy_score += 2
    else:
        sell_score += 2
        
    # 2. จำลองการเช็ก Market Structure (CHoCH / BOS)
    # ในสคริปต์จริงส่วนนี้จะคำนวณจาก High/Low ล่าสุด
    highest_high = df['high'].iloc[-20:-1].max()
    lowest_low = df['low'].iloc[-20:-1].min()
    
    if current_price > highest_high:
        buy_score += 3  # ทะลุโครงสร้างขาขึ้น (BOS)
    elif current_price < lowest_low:
        sell_score += 3  # ทะลุโครงสร้างขาลง (BOS)
        
    # 3. จำลองการเช็ก Order Block & Fair Value Gap (FVG)
    # เพื่อความรวดเร็วและเสถียรบนระบบ Cloud ฟรี
    buy_score += 3
    sell_score += 3
    
    # จำกัดคะแนนไม่ให้เกิน 8
    buy_score = min(buy_score, 8)
    sell_score = min(sell_score, 8)
    
    return buy_score, sell_score, current_price