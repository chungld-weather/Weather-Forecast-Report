import streamlit as st
from app import get_base64_image

st.set_page_config(page_title="Test Windy", layout="wide")

windy_url = "https://embed.windy.com/embed2.html?lat=10.762&lon=106.660&zoom=5&level=surface&overlay=rain&product=ecmwf&menu=&message=&marker=1&calendar=now&pressure=&type=map&location=coordinates&detail=&metricWind=default&metricTemp=default&radarRange=-1"

logo_b64 = get_base64_image("Pictures/Logo.png")

if logo_b64:
    windy_html = f"""
    <div style="position: relative; width: 100%; height: 500px; background-color: red;">
        <iframe src="{windy_url}" width="100%" height="100%" frameborder="0" style="border:0; pointer-events: auto;"></iframe>
        <div style="position: absolute; top: 10px; left: 50%; transform: translateX(-50%); z-index: 99999; 
                    background-color: white; padding: 10px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    display: flex; justify-content: center; align-items: center; pointer-events: none;">
            <img src="data:image/png;base64,{logo_b64}" style="max-height: 120px; max-width: 400px; object-fit: contain;">
        </div>
    </div>
    """
    st.components.v1.html(windy_html, height=520, scrolling=False)
else:
    st.write("Logo could not be loaded")
