import streamlit as st
import json
import os
from datetime import datetime
from deep_translator import GoogleTranslator
import requests
import geocoder
from streamlit_folium import st_folium
import folium
from openai import OpenAI
from openai.error import RateLimitError

# ================= CONFIG =================
st.set_page_config(page_title="Krishi Sakhi - AI Farmer Assistant", layout="wide")

PROFILE_FILE = "farmer_profile.json"
LOG_FILE = "activity_logs.json"
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
OPENWEATHER_API_KEY = st.secrets["OPENWEATHER_API_KEY"]

# ================= HELPER FUNCTIONS =================
def load_json(file, default):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_ai_response(query, profile, history):
    translated = GoogleTranslator(source="ml", target="en").translate(query)
    context = f"Farmer Profile: {profile}\nConversation History: {history}\nFarmer asked: {translated}\nAnswer in simple Malayalam."
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful farming assistant for Kerala farmers."},
                {"role": "user", "content": context}
            ]
        )
        reply = response.choices[0].message.content
        reply_ml = GoogleTranslator(source="en", target="ml").translate(reply)
        return reply_ml
    except RateLimitError:
        return "⚠️ API quota exceeded. Please try again later."
    except Exception as e:
        return f"⚠️ Error: {e}"

def get_weather(lat, lon):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
        data = requests.get(url).json()
        desc = data["weather"][0]["description"]
        temp = data["main"]["temp"]
        return f"{desc}, {temp}°C"
    except Exception:
        return "Weather data unavailable"

# ================= MAIN APP =================
st.title("🌾 Krishi Sakhi – AI-Powered Farming Assistant")

# Load saved data
profile = load_json(PROFILE_FILE, {})
logs = load_json(LOG_FILE, [])

# ---------------- Home Page ----------------
st.header("🏠 Home")
st.image("https://i.imgur.com/4NJqg2N.png", use_column_width=True)  # AI Farmer image placeholder

st.subheader("📍 Your Location & Weather")
user_location = geocoder.ip('me')
lat, lon = user_location.latlng if user_location.ok else (10.0, 76.0)  # Default Kerala coords
st.map([[lat, lon]])
st.write(f"Current weather: {get_weather(lat, lon)}")

# ---------------- Farmer Profile ----------------
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

# ---------------- Chat Assistant ----------------
st.header("💬 Ask a Question (Malayalam)")
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

user_query = st.text_input("Type your question in Malayalam:")
if st.button("Get Answer"):
    if not profile:
        st.warning("⚠️ Please fill in your profile first.")
    elif user_query.strip() != "":
        answer = get_ai_response(user_query, profile, st.session_state.chat_history)
        st.session_state.chat_history.append({"q": user_query, "a": answer})

for chat in reversed(st.session_state.chat_history):
    st.write(f"👨‍🌾: {chat['q']}")
    st.write(f"🤖: {chat['a']}")

# ---------------- Activity Log ----------------
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

# ---------------- Advisory ----------------
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

# ---------------- Interactive Map ----------------
st.header("🗺️ Farm Map")
m = folium.Map(location=[lat, lon], zoom_start=12)
st_folium(m, width=700, height=400)