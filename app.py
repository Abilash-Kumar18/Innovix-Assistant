import streamlit as st
import json
import os
from datetime import datetime
import requests
import folium
from streamlit_folium import st_folium
from deep_translator import GoogleTranslator

# ================= CONFIG =================
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]  # Add your Gemini key in Streamlit Secrets
GEMINI_API_URL = "https://gemini.googleapis.com/v1/chat/completions"
OPENWEATHER_API_KEY = st.secrets["OPENWEATHER_API_KEY"]

PROFILE_FILE = "farmer_profile.json"
LOG_FILE = "activity_logs.json"

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

    headers = {
        "Authorization": f"Bearer {GEMINI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gemini-1.5-flash",
        "messages": [
            {"role": "system", "content": "You are a helpful farming assistant for Kerala farmers."},
            {"role": "user", "content": context}
        ]
    }
    try:
        response = requests.post(GEMINI_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        reply = response.json()['choices'][0]['message']['content']
        reply_ml = GoogleTranslator(source="en", target="ml").translate(reply)
        return reply_ml
    except requests.exceptions.RequestException as e:
        return f"⚠️ Error: {e}"

def get_weather(lat, lon):
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={OPENWEATHER_API_KEY}"
        res = requests.get(url).json()
        temp = res['main']['temp']
        desc = res['weather'][0]['description']
        return f"{temp}°C, {desc}"
    except:
        return "Weather info unavailable"

# ================= APP LAYOUT =================
st.set_page_config(page_title="Krishi Sakhi", layout="wide")

lang_options = ["English", "മലയാളം"]
lang = st.sidebar.selectbox("Choose Language / ഭാഷ തിരഞ്ഞെടുക്കുക", lang_options)
is_ml = lang == "മലയാളം"

pages = ["Home", "Farmer Profile", "Chat Assistant", "Activity Log", "Weather & Map"]
page = st.sidebar.radio("Navigation", pages)

profile = load_json(PROFILE_FILE, {})
logs = load_json(LOG_FILE, [])

# ================= HOME PAGE =================
if page == "Home":
    st.title("🌾 കൃഷി സഖി – AI കർഷക സഹായി" if is_ml else "🌾 Krishi Sakhi – AI Farmer Assistant")
    st.image("https://cdn-icons-png.flaticon.com/512/2589/2589183.png", width=200)
    st.subheader("🌱 സ്വാഗതം" if is_ml else "🌱 Welcome")
    st.write(
        "ഫാർം പ്രവർത്തനങ്ങൾ നിയന്ത്രിക്കുക, കാലാവസ്ഥ അറിയുക, ചോദ്യങ്ങൾ ചോദിക്കുക, AI ഉപദേശങ്ങൾ ലഭിക്കുക." if is_ml else
        "Manage farm activities, get weather, ask questions, receive AI tips."
    )

    st.markdown("---")
    st.subheader("🖼️ സവിശേഷതകൾ" if is_ml else "🖼️ Features")
    static_tips = [
        {"title": "സിംചനം" if is_ml else "Irrigation",
         "image": "https://cdn-icons-png.flaticon.com/512/2965/2965567.png",
         "desc": "രാവിലെ അല്ലെങ്കിൽ വൈകിട്ട് വിളകൾ വെള്ളം നൽകുക." if is_ml else "Water crops early morning or late evening."},
        {"title": "പൊട്ടെൻ നിയന്ത്രണം" if is_ml else "Pest Control",
         "image": "https://cdn-icons-png.flaticon.com/512/616/616408.png",
         "desc": "സുരക്ഷിതമായി പൊട്ടെൻ നിയന്ത്രിക്കാൻ നീം പദാർത്ഥ പടികാരികൾ ഉപയോഗിക്കുക." if is_ml else "Use neem-based pesticides for safe control."},
        {"title": "മണ്ണിന്റെ ആരോഗ്യസംരക്ഷണം" if is_ml else "Soil Health",
         "image": "https://cdn-icons-png.flaticon.com/512/616/616408.png",
         "desc": "മണ്ണിന്റെ സസ്യധാരാവൃദ്ധിക്ക് ജൈവ വളം ചേർക്കുക." if is_ml else "Add organic compost to improve soil fertility."},
    ]
    for tip in static_tips:
        st.image(tip["image"], width=100)
        st.markdown(f"**{tip['title']}**")
        st.write(tip["desc"])

# ================= FARMER PROFILE =================
elif page == "Farmer Profile":
    st.header("👨‍🌾 കർഷക പ്രൊഫൈൽ" if is_ml else "👨‍🌾 Farmer Profile")
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

# ================= CHAT ASSISTANT =================
elif page == "Chat Assistant":
    st.header("💬 ചോദ്യങ്ങൾ ചോദിക്കുക" if is_ml else "💬 Ask a Question")
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    user_query = st.text_input("Type your question in Malayalam:" if is_ml else "Type your question:")
    if st.button("ഉത്തരമെടുക്കുക" if is_ml else "Get Answer"):
        if not profile:
            st.warning("⚠️ ദയവായി പ്രൊഫൈൽ ആദ്യം പൂരിപ്പിക്കുക." if is_ml else "⚠️ Please fill in your profile first.")
        elif user_query.strip() != "":
            answer = get_ai_response(user_query, profile, st.session_state.chat_history)
            st.session_state.chat_history.append({"q": user_query, "a": answer})
    for chat in reversed(st.session_state.chat_history):
        st.write(f"👨‍🌾: {chat['q']}")
        st.write(f"🤖: {chat['a']}")

# ================= ACTIVITY LOG =================
elif page == "Activity Log":
    st.header("📝 പ്രവർത്തന രേഖ" if is_ml else "📝 Activity Log")
    activity = st.text_input("പ്രവർത്തനം രേഖപ്പെടുത്തുക:" if is_ml else "Log activity:")
    if st.button("സേവ് ചെയ്യുക" if is_ml else "Add Log"):
        entry = {"activity": activity, "time": datetime.now().strftime("%Y-%m-%d %H:%M")}
        logs.append(entry)
        save_json(LOG_FILE, logs)
        st.success("✅ Activity logged!")
    if logs:
        st.subheader("മുൻ പ്രവർത്തനങ്ങൾ" if is_ml else "Past Activities")
        for log in reversed(logs[-5:]):
            st.write(f"{log['time']} - {log['activity']}")

# ================= WEATHER & MAP =================
elif page == "Weather & Map":
    st.header("🌤️ കാലാവസ്ഥ & മാപ്പ്" if is_ml else "🌤️ Weather & Map")
    location = st.text_input("സ്ഥലം ലാറ്റ്,ലോൺ നൽകുക (e.g., 10.85,76.27):" if is_ml else
                             "Enter your location coordinates as lat,lon (e.g., 10.85,76.27):")
    if location:
        try:
            lat, lon = map(float, location.split(","))
            weather = get_weather(lat, lon)
            st.info(f"Current weather: {weather}")
            m = folium.Map(location=[lat, lon], zoom_start=13)
            folium.Marker([lat, lon], tooltip="You are here").add_to(m)
            st_folium(m, width=350, height=350)
        except:
            st.error("Invalid coordinates format.")
