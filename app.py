import streamlit as st
import json
import os
from datetime import datetime
import openai
from deep_translator import GoogleTranslator

# ========== CONFIG ==========
openai.api_key = st.secrets["OPENAI_API_KEY"]
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

def get_ai_response(query, profile, history, lang="ml"):
    translated = GoogleTranslator(source=lang, target="en").translate(query)
    context = f"Farmer Profile: {profile}\nConversation History: {history}\nFarmer asked: {translated}\nAnswer in simple {lang}."

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful farming assistant for Kerala farmers."},
                {"role": "user", "content": context}
            ]
        )
        reply = response.choices[0].message["content"]
        reply_ml = GoogleTranslator(source="en", target=lang).translate(reply)
        return reply_ml
    except Exception as e:
        return f"⚠️ Error: {e}"

# ========== STREAMLIT APP ==========
st.set_page_config(page_title="Krishi Sakhi - Farming Assistant", layout="wide")

# Language Toggle
lang = st.sidebar.radio("🌐 Language / ഭാഷ", ("English", "മലയാളം"))
is_ml = lang == "മലയാളം"

# ---- Title ----
st.title("🌾 കൃഷി സഖി – കർഷകരുടെ AI സഹായം" if is_ml else "🌾 Krishi Sakhi – AI-Powered Farming Assistant")

# Load saved data
profile = load_json(PROFILE_FILE, {})
logs = load_json(LOG_FILE, [])

# ---- Farmer Profile ----
st.header("👨‍🌾 കർഷകന്റെ വിവരങ്ങൾ" if is_ml else "👨‍🌾 Farmer Profile")
with st.form("profile_form"):
    name = st.text_input("പേര്" if is_ml else "Name", profile.get("name", ""))
    location = st.text_input("സ്ഥലം" if is_ml else "Location", profile.get("location", ""))
    
    crop = st.selectbox("പ്രധാന വിള" if is_ml else "Main Crop", ["Rice", "Coconut", "Banana", "Vegetables", "Rubber", "Other"])
    soil = st.selectbox("മണ്ണിന്റെ തരം" if is_ml else "Soil Type", ["Sandy", "Clay", "Loamy", "Laterite", "Alluvial"])
    land = st.text_input("ഭൂമിയുടെ വലുപ്പം (ഏക്കർ)" if is_ml else "Land Size (acres)", profile.get("land", ""))

    uploaded_image = st.file_uploader("ഫോട്ടോ അപ്ലോഡ് ചെയ്യുക" if is_ml else "Upload Farmer/Land Photo", type=["jpg", "png"])
    submitted = st.form_submit_button("സേവ് ചെയ്യുക" if is_ml else "Save Profile")
    if submitted:
        profile = {"name": name, "location": location, "crop": crop, "soil": soil, "land": land}
        save_json(PROFILE_FILE, profile)
        st.success("✅ സംരക്ഷിച്ചു!" if is_ml else "✅ Profile saved!")

if profile:
    st.subheader("📌 വിശദാംശങ്ങൾ" if is_ml else "📌 Farmer Details")
    st.json(profile)
    if uploaded_image:
        st.image(uploaded_image, caption="ഫോട്ടോ" if is_ml else "Farmer / Land Photo", use_column_width=True)

# ---- Chat Assistant ----
st.header("💬 ചോദ്യോത്തരങ്ങൾ (മലയാളം)" if is_ml else "💬 Chat Assistant (Malayalam)")
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

user_query = st.text_input("മലയാളത്തിൽ ചോദിക്കുക:" if is_ml else "Type your question in Malayalam:")
col1, col2 = st.columns([1,1])
with col1:
    if st.button("ഉത്തരം നേടുക" if is_ml else "Get Answer"):
        if not profile:
            st.warning("⚠️ ആദ്യം പ്രൊഫൈൽ പൂരിപ്പിക്കുക!" if is_ml else "⚠️ Please fill in your profile first.")
        elif user_query.strip() != "":
            answer = get_ai_response(user_query, profile, st.session_state.chat_history, lang="ml")
            st.session_state.chat_history.append({"q": user_query, "a": answer})
with col2:
    if st.button("ചാറ്റ് മായ്ക്കുക" if is_ml else "Reset Chat"):
        st.session_state.chat_history = []
        st.success("🗑️ മായ്ച്ചു!" if is_ml else "🗑️ Chat history cleared!")

st.markdown("### 🗨️ സംഭാഷണം" if is_ml else "### 🗨️ Conversation")
for chat in reversed(st.session_state.chat_history):
    st.markdown(f"<div style='background:#e0ffe0;padding:10px;border-radius:8px;margin:5px;'>👨‍🌾 <b>{'കർഷകൻ' if is_ml else 'Farmer'}:</b> {chat['q']}</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='background:#f0f0f0;padding:10px;border-radius:8px;margin:5px;'>🤖 <b>{'സഹായി' if is_ml else 'Assistant'}:</b> {chat['a']}</div>", unsafe_allow_html=True)

# ---- Activity Log ----
st.header("📝 പ്രവർത്തനങ്ങൾ" if is_ml else "📝 Activity Log")
activity = st.selectbox("പ്രവർത്തനം തിരഞ്ഞെടുക്കുക" if is_ml else "Select Activity", ["Irrigation", "Sowing", "Fertilizer", "Pesticide Spray", "Harvest", "Other"])
custom_activity = st.text_input("സ്വന്തം പ്രവർത്തനം നൽകുക" if is_ml else "Or enter custom activity:")
if st.button("ചേർക്കുക" if is_ml else "Add Log"):
    act = custom_activity if custom_activity else activity
    entry = {"activity": act, "time": datetime.now().strftime("%Y-%m-%d %H:%M")}
    logs.append(entry)
    save_json(LOG_FILE, logs)
    st.success("✅ ചേർത്തു!" if is_ml else "✅ Activity logged!")

if logs:
    st.subheader("📌 അടുത്തിടെയുള്ള പ്രവർത്തനങ്ങൾ" if is_ml else "📌 Recent Activities")
    for log in reversed(logs[-5:]):
        st.markdown(f"🕒 **{log['time']}** — {log['activity']}")

# ---- Advisory ----
st.header("📢 ഉപദേശം" if is_ml else "📢 Smart Advisory")
if logs:
    last_activity = logs[-1]["activity"].lower()
    if "irrigation" in last_activity:
        st.image("https://cdn-icons-png.flaticon.com/512/1163/1163624.png", width=70)
        st.info("🌧️ നാളെ മഴ പ്രതീക്ഷിക്കുന്നു – ഇന്ന് വെള്ളം കൊടുക്കേണ്ട." if is_ml else "🌧️ Rain expected tomorrow – avoid irrigation.")
    elif "pest" in last_activity or "spray" in last_activity:
        st.image("https://cdn-icons-png.flaticon.com/512/616/616408.png", width=70)
        st.info("🐛 കീട ബാധ ശ്രദ്ധിക്കുക – വേണമെങ്കിൽ വേപ്പ്നീർ സ്പ്രേ ചെയ്യുക." if is_ml else "🐛 Inspect your crop – pest alert nearby. Use neem spray.")
    elif "harvest" in last_activity:
        st.image("https://cdn-icons-png.flaticon.com/512/765/765514.png", width=70)
        st.success("🌾 കൊയ്ത്തിന് നല്ല സമയം. സംഭരണത്തിനുള്ള ഒരുക്കം വേണം." if is_ml else "🌾 Good time for harvesting. Ensure storage is ready.")
    else:
        st.image("https://cdn-icons-png.flaticon.com/512/3069/3069172.png", width=70)
        st.info("✅ വിള നിരന്തരം പരിശോധിക്കുക." if is_ml else "✅ Keep monitoring your crop regularly.")
else:
    st.write("പ്രവർത്തനങ്ങൾ ചേർത്തിട്ടില്ല." if is_ml else "No activities logged yet.")

# ---- Weather ----
st.header("🌦️ കാലാവസ്ഥ" if is_ml else "🌦️ Weather Forecast")
st.image("https://cdn-icons-png.flaticon.com/512/869/869869.png", width=80)
if is_ml:
    st.info("📍 സ്ഥലം: കേരളം\n🌤️ നാളെ: 30°C, ചെറിയ മഴ\n💧 ഈർപ്പം: 78%")
else:
    st.info("📍 Location: Kerala\n🌤️ Tomorrow: 30°C, Light Rain\n💧 Humidity: 78%")

# ---- About ----
st.header("ℹ️ ആപ്പ് വിവരങ്ങൾ" if is_ml else "ℹ️ About This App")
if is_ml:
    st.write("""
കൃഷി സഖി ഒരു **AI അടിസ്ഥാനത്തിലുള്ള കാർഷിക സഹായി** ആണു.  

🔹 **Python + Streamlit** ഉപയോഗിച്ച് വികസിപ്പിച്ചു  
🔹 **OpenAI GPT** കാർഷിക ഉപദേശം നൽകുന്നു  
🔹 **മലയാളം ചോദ്യങ്ങൾ** പിന്തുണയ്ക്കുന്നു  
🔹 **പ്രവർത്തനങ്ങൾ, കാലാവസ്ഥ, ഉപദേശങ്ങൾ** ലഭ്യമാക്കുന്നു  
""")
else:
    st.write("""
Krishi Sakhi is an **AI-powered farming assistant** built for Kerala farmers.  

🔹 Built with **Python + Streamlit**  
🔹 Uses **OpenAI GPT** for advisory  
🔹 Supports **Malayalam queries**  
🔹 Tracks **logs, weather, and smart advice**  
""")
