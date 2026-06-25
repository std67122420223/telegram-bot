import streamlit as st
import pandas as pd
import numpy as np

def run_dashboard():
    # กำหนดค่าเริ่มต้นของหน้าจอให้โหลดเบาที่สุด
    st.set_page_config(page_title="Trading Terminal", layout="wide")
    st.title("📊 Enterprise Automated Hub Dashboard")
    
    # ส่วน Sidebar ด้านข้างแสดงสถานะระบบ
    st.sidebar.markdown("### System Status: <font color='green'>ONLINE</font>", unsafe_allow_html=True)
    if st.sidebar.button("Emergency Global Kill Switch", type="primary"):
        st.sidebar.warning("SYSTEM HALTED BY USER")

    # ส่วนแสดงผลตัวเลขสำคัญ (Metrics) 4 ช่อง
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Account Balance", "$10,450.00", "+4.5%")
    col2.metric("Equity Growth", "$10,485.00", "+4.85%")
    col3.metric("Win-Rate Parameter", "64.2%", "Optimal")
    col4.metric("Active Drawdown", "0.22%", "Safe")

    # ส่วนแสดงผลกราฟพอร์ตโฟลิโอแบบ Native (โหลดเร็ว ไม่ค้าง)
    st.markdown("### Interactive Strategy Equity Curve")
    
    # จำลองข้อมูลกราฟการเติบโตของทุน
    np.random.seed(42)
    chart_data = pd.DataFrame(
        np.random.randn(50, 1).cumsum() + 10000, 
        columns=['Equity Value']
    )
    st.line_chart(chart_data)

if __name__ == '__main__':
    run_dashboard()