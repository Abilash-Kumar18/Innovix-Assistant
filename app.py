import streamlit as st
import json
import os
from datetime import datetime
from openai import OpenAI
from deep_translator import GoogleTranslator
from streamlit_folium import st_folium
import folium
import requests

# ================= CONFIG =================
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
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
    except Exception as e:
        return f"⚠️ Error: {e}"

def get_weather(lat, lon):
    try:
        api_key = st.secrets["OPENWEATHER_API_KEY"]
        url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={api_key}"
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

# ================= MOBILE-FRIENDLY STYLING =================
st.markdown("""
<style>
.big-button > button {
    padding: 15px 25px;
    font-size: 20px;
}
.big-input input {
    height: 50px;
    font-size: 18px;
}
</style>
""", unsafe_allow_html=True)

# ================= HOME PAGE =================
if page == "Home":
    st.title("🌾 കൃഷി സഖി – AI കർഷക സഹായി" if is_ml else "🌾 Krishi Sakhi – AI Farmer Assistant")
    st.image("https://cdn-icons-png.flaticon.com/512/2589/2589183.png", width=200)
    st.subheader("🌱 Welcome / സ്വാഗതം" if not is_ml else "🌱 സ്വാഗതം")
    st.write("Manage farm activities, get weather, ask questions, receive AI tips." if not is_ml else
             "ഫാർം പ്രവർത്തനങ്ങൾ നിയന്ത്രിക്കുക, കാലാവസ്ഥ അറിയുക, ചോദ്യങ്ങൾ ചോദിക്കുക, AI ഉപദേശങ്ങൾ ലഭിക്കുക.")
    st.markdown("---")

    st.subheader("🖼️ Features / സവിശേഷതകൾ" if is_ml else "🖼️ Features")
    static_tips = [
        {"title": "Irrigation" if not is_ml else "സിംചനം",
         "image": "https://cdn-icons-png.flaticon.com/512/2965/2965567.png",
         "desc": "Water crops early morning or late evening." if not is_ml else "രാവിലെ അല്ലെങ്കിൽ വൈകിട്ട് വിളകൾ വെള്ളം നൽകുക."},
        {"title": "Pest Control" if not is_ml else "പൊട്ടെൻ നിയന്ത്രണം",
         "image": "https://cdn-icons-png.flaticon.com/512/616/616408.png",
         "desc": "Use neem-based pesticides for safe control." if not is_ml else "സുരക്ഷിതമായി പൊട്ടെൻ നിയന്ത്രിക്കാൻ നീം പദാർത്ഥ പടികാരികൾ ഉപയോഗിക്കുക."},
        {"title": "Soil Health" if not is_ml else "മണ്ണിന്റെ ആരോഗ്യസംരക്ഷണം",
         "image": "https://cdn-icons-png.flaticon.com/512/616/616408.png",
         "desc": "Add organic compost to improve soil fertility." if not is_ml else "മണ്ണിന്റെ സസ്യധാരാവൃദ്ധിക്ക് ജൈവ വളം ചേർക്കുക."},
    ]
    for tip in static_tips:
        st.image(tip["image"], width=100)
        st.markdown(f"**{tip['title']}**")
        st.write(tip["desc"])

    st.markdown("---")
    st.subheader("🤖 AI Tips" if not is_ml else "🤖 AI ഉപദേശം")
    recent_activities = logs[-3:] if logs else []
    activities_text = "\n".join([f"- {act['activity']} on {act['time']}" for act in recent_activities]) if recent_activities else "No recent activities"
    ai_context = f"Farmer Profile: {profile}\nRecent Activities:\n{activities_text}\nProvide 2-3 simple tips in {'Malayalam' if is_ml else 'English'}."
    
    if st.button("Get AI Tips" if not is_ml else "AI ഉപദേശം ലഭിക്കുക", key="ai_tip_button", help="Click to get AI farming tips", use_container_width=True):
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert farming assistant providing concise tips."},
                    {"role": "user", "content": ai_context}
                ]
            )
            ai_tips_raw = response.choices[0].message.content
            ai_tips = [tip.strip("- ").strip() for tip in ai_tips_raw.split("\n") if tip.strip()]
            icon_map = {
                "water": "https://cdn-icons-png.flaticon.com/512/2965/2965567.png",
                "irrigation": "https://cdn-icons-png.flaticon.com/512/2965/2965567.png",
                "pest": "https://cdn-icons-png.flaticon.com/512/616/616408.png",
                "soil": "https://cdn-icons-png.flaticon.com/512/616/616408.png",
                "fertilizer": "https://cdn-icons-png.flaticon.com/512/616/616408.png",
            }
            for tip in ai_tips:
                matched_icon = next((icon_map[key] for key in icon_map if key in tip.lower()), None)
                cols_tip = st.columns([1, 5])
                with cols_tip[0]:
                    if matched_icon:
                        st.image(matched_icon, width=50)
                with cols_tip[1]:
                    st.write(tip)
        except Exception as e:
            st.error(f"⚠️ Error generating tips: {e}")

# ================= FARMER PROFILE =================
elif page == "Farmer Profile":
    st.header("👨‍🌾 Farmer Profile" if not is_ml else "👨‍🌾 കർഷക പ്രൊഫൈൽ")
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
    st.header("💬 Ask a Question" if not is_ml else "💬 ചോദ്യങ്ങൾ ചോദിക്കുക")
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    user_query = st.text_input("Type your question in Malayalam:" if is_ml else "Type your question:")
    if st.button("Get Answer" if not is_ml else "ഉത്തരമെടുക്കുക"):
        if not profile:
            st.warning("⚠️ Please fill in your profile first." if not is_ml else "⚠️ ദയവായി പ്രൊഫൈൽ ആദ്യം പൂരിപ്പിക്കുക.")
        elif user_query.strip() != "":
            answer = get_ai_response(user_query, profile, st.session_state.chat_history)
            st.session_state.chat_history.append({"q": user_query, "a": answer})
    for chat in reversed(st.session_state.chat_history):
        st.write(f"👨‍🌾: {chat['q']}")
        st.write(f"🤖: {chat['a']}")

# ================= ACTIVITY LOG =================
elif page == "Activity Log":
    st.header("📝 Activity Log" if not is_ml else "📝 പ്രവർത്തന രേഖ")
    activity = st.text_input("Log activity (e.g., sowing, irrigation, spraying):" if not is_ml else "പ്രവർത്തനം രേഖപ്പെടുത്തുക:")
    if st.button("Add Log" if not is_ml else "സേവ് ചെയ്യുക"):
        entry = {"activity": activity, "time": datetime.now().strftime("%Y-%m-%d %H:%M")}
        logs.append(entry)
        save_json(LOG_FILE, logs)
        st.success("✅ Activity logged!")
    if logs:
        st.subheader("Past Activities" if not is_ml else "മുൻ പ്രവർത്തനങ്ങൾ")
        for log in reversed(logs[-5:]):
            st.write(f"{log['time']} - {log['activity']}")

# ================= WEATHER & MAP =================
elif page == "Weather & Map":
    st.header("🌤️ Weather & Map" if not is_ml else "🌤️ കാലാവസ്ഥ & മാപ്പ്")
    st.write("Allow location to see weather and map." if not is_ml else "കാലാവസ്ഥയും മാപ്പും കാണാൻ സ്ഥലം അനുവദിക്കുക.")
    location = st.text_input("Enter your location coordinates as lat,lon (e.g., 10.85,76.27):" if is_ml else "സ്ഥലം ലാറ്റ്,ലോൺ നൽകുക (e.g., 10.85,76.27):")
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