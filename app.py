import streamlit as st
import json
import os
from datetime import datetime
import openai
from deep_translator import GoogleTranslator
from streamlit_folium import st_folium
import folium
import requests

# ========== CONFIG ==========
openai.api_key = st.secrets["OPENAI_API_KEY"]
weather_api_key = st.secrets["OPENWEATHER_API_KEY"]

PROFILE_FILE = "farmer_profile.json"
LOG_FILE = "activity_logs.json"

# ========== HELPER FUNCTIONS ==========
def load_json(file, default):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_weather(lat, lon, lang="en"):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={weather_api_key}&units=metric&lang={lang}"
    try:
        res = requests.get(url).json()
        if "main" in res:
            temp = res["main"]["temp"]
            desc = res["weather"][0]["description"]
            humidity = res["main"]["humidity"]
            return f"🌡️ {temp}°C | {desc.capitalize()} | 💧 Humidity: {humidity}%"
        else:
            return "⚠️ Weather data unavailable"
    except Exception as e:
        return f"⚠️ Error fetching weather: {e}"

# ========== STREAMLIT APP ==========
st.set_page_config(page_title="Krishi Sakhi - Farming Assistant", layout="wide")

# Language Toggle
lang = st.sidebar.radio("🌐 Language / ഭാഷ", ("English", "മലയാളം"))
is_ml = lang == "മലയാളം"
weather_lang = "ml" if is_ml else "en"

# ---- Title ----
st.title("🌾 കൃഷി സഖി – കർഷകരുടെ AI സഹായം" if is_ml else "🌾 Krishi Sakhi – AI-Powered Farming Assistant")

# Load saved data
profile = load_json(PROFILE_FILE, {})
logs = load_json(LOG_FILE, [])

# ---- Farmer Profile ----
st.header("👨‍🌾 കർഷകന്റെ വിവരങ്ങൾ" if is_ml else "👨‍🌾 Farmer Profile")
with st.form("profile_form"):
    name = st.text_input("പേര്" if is_ml else "Name", profile.get("name", ""))
    crop = st.selectbox("പ്രധാന വിള" if is_ml else "Main Crop", ["Rice", "Coconut", "Banana", "Vegetables", "Rubber", "Other"])
    soil = st.selectbox("മണ്ണിന്റെ തരം" if is_ml else "Soil Type", ["Sandy", "Clay", "Loamy", "Laterite", "Alluvial"])
    land = st.text_input("ഭൂമിയുടെ വലുപ്പം (ഏക്കർ)" if is_ml else "Land Size (acres)", profile.get("land", ""))

    submitted = st.form_submit_button("സേവ് ചെയ്യുക" if is_ml else "Save Profile")
    if submitted:
        profile = {"name": name, "crop": crop, "soil": soil, "land": land}
        save_json(PROFILE_FILE, profile)
        st.success("✅ സംരക്ഷിച്ചു!" if is_ml else "✅ Profile saved!")

if profile:
    st.subheader("📌 വിശദാംശങ്ങൾ" if is_ml else "📌 Farmer Details")
    st.json(profile)

# ---- Location Map ----
st.header("📍 സ്ഥലം / Location")
st.write("🗺️ നിങ്ങളുടെ സ്ഥലത്ത് ക്ലിക്ക് ചെയ്യുക" if is_ml else "🗺️ Click on the map to mark your farm location")

m = folium.Map(location=[10.85, 76.27], zoom_start=7)  # Kerala default center
if "location" in profile and "lat" in profile["location"]:
    folium.Marker(
        [profile["location"]["lat"], profile["location"]["lon"]],
        popup="Your Farm",
        icon=folium.Icon(color="green")
    ).add_to(m)

map_data = st_folium(m, height=400, width=700)

if map_data and map_data["last_clicked"]:
    lat, lon = map_data["last_clicked"]["lat"], map_data["last_clicked"]["lng"]
    profile["location"] = {"lat": lat, "lon": lon}
    save_json(PROFILE_FILE, profile)
    st.success(f"📍 Location saved: {lat:.4f}, {lon:.4f}")

if "location" in profile:
    st.map([{"lat": profile["location"]["lat"], "lon": profile["location"]["lon"]}])

    # ---- Weather Section ----
    st.header("🌦️ കാലാവസ്ഥ" if is_ml else "🌦️ Weather Update")
    weather_report = get_weather(profile["location"]["lat"], profile["location"]["lon"], lang=weather_lang)
    st.info(weather_report)
