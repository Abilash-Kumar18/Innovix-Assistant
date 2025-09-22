import streamlit as st
import json
import os
from datetime import datetime
import requests
import folium
from streamlit_folium import st_folium
import geocoder
from deep_translator import GoogleTranslator
from openai import OpenAI   # ✅ New OpenAI SDK

# -------------------------
# CONFIG
# -------------------------
st.set_page_config(page_title="Krishi Sakhi - AI Farming Assistant", layout="wide")

PROFILE_FILE = "farmer_profile.json"
LOG_FILE = "activity_logs.json"

# OpenAI client
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# -------------------------
# HELPER FUNCTIONS
# -------------------------
def load_json(file, default):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_weather(lat, lon):
    api_key = st.secrets.get("OPENWEATHER_API_KEY", "")
    if not api_key:
        return None
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric&lang=ml"
    try:
        r = requests.get(url)
        return r.json()
    except:
        return None

def ai_advice(query):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are Krishi Sakhi, a helpful AI farming assistant for Kerala farmers."},
                {"role": "user", "content": query}
            ],
            max_tokens=200
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ Error: {e}"

# -------------------------
# LOAD DATA
# -------------------------
profile = load_json(PROFILE_FILE, {})
logs = load_json(LOG_FILE, [])

# -------------------------
# HOME PAGE
# -------------------------
st.title("🌾 Krishi Sakhi – AI-Powered Farming Assistant")

st.image("https://i.imgur.com/yzYwO0M.png", use_container_width=True)  # Banner image

st.markdown("Welcome to **Krishi Sakhi**, an AI-powered farming assistant to help Kerala farmers with crop management, weather updates, and smart advice.")

# -------------------------
# LOCATION & WEATHER
# -------------------------
st.header("📍 Location & Weather")

g = geocoder.ip("me")
lat, lon = g.latlng if g.latlng else (10.8505, 76.2711)  # Default Kerala

m = folium.Map(location=[lat, lon], zoom_start=10)
folium.Marker([lat, lon], tooltip="Your Location").add_to(m)
st_folium(m, width=700, height=400)

weather = get_weather(lat, lon)
if weather:
    st.subheader("🌤️ Weather")
    st.write(f"**{weather['weather'][0]['description']}**")
    st.write(f"🌡️ Temperature: {weather['main']['temp']} °C")
    st.write(f"💧 Humidity: {weather['main']['humidity']} %")
    st.write(f"🌬️ Wind: {weather['wind']['speed']} m/s")

# -------------------------
# FARMER PROFILE
# -------------------------
st.header("👨‍🌾 Farmer Profile")
with st.form("profile_form"):
    name = st.text_input("Name", profile.get("name", ""))
    location = st.text_input("Location", profile.get("location", ""))
    crop = st.text_input("Main Crop", profile.get("crop", ""))
    soil = st.text_input("Soil Type", profile.get("soil", ""))
    land = st.text_input("Land Size (acres)", profile.get("land", ""))

    submitted = st.form_submit_button("Save Profile")
    if submitted:
        profile = {"name": name, "location": location, "crop": crop, "soil": soil, "land": land}
        save_json(PROFILE_FILE, profile)
        st.success("✅ Profile saved!")

if profile:
    st.json(profile)

# -------------------------
# CHAT ASSISTANT
# -------------------------
st.header("💬 Ask a Question (Malayalam / English)")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

user_query = st.text_input("Type your question:")
if st.button("Get Answer"):
    if not profile:
        st.warning("⚠️ Please fill in your profile first.")
    elif user_query.strip() != "":
        translated = GoogleTranslator(source="ml", target="en").translate(user_query)
        answer = ai_advice(translated)
        reply_ml = GoogleTranslator(source="en", target="ml").translate(answer)
        st.session_state.chat_history.append({"q": user_query, "a": reply_ml})

for chat in reversed(st.session_state.chat_history):
    st.write(f"👨‍🌾: {chat['q']}")
    st.write(f"🤖: {chat['a']}")

# -------------------------
# ACTIVITY LOG
# -------------------------
st.header("📝 Activity Log")
activity = st.text_input("Log activity (e.g., sowing, irrigation, spraying):")
if st.button("Add Log"):
    entry = {"activity": activity, "time": datetime.now().strftime("%Y-%m-%d %H:%M")}
    logs.append(entry)
    save_json(LOG_FILE, logs)
    st.success("✅ Activity logged!")

if logs:
    st.subheader("Past Activities")
    for log in reversed(logs[-5:]):
        st.write(f"{log['time']} - {log['activity']}")

# -------------------------
# ADVISORY
# -------------------------
st.header("📢 Advisory")
if logs:
    last_activity = logs[-1]["activity"].lower()
    if "irrigation" in last_activity:
        st.info("🌧️ Rain expected tomorrow – avoid irrigation.")
    elif "pest" in last_activity or "spray" in last_activity:
        st.info("🐛 Inspect your crop – pest alert nearby. Consider neem-based solution.")
    else:
        st.info("✅ Keep monitoring your crop regularly.")
else:
    st.write("No activities logged yet.")