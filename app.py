import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
import geocoder
from deep_translator import GoogleTranslator
import openai

# -------------------------
# SETUP
# -------------------------
st.set_page_config(page_title="Krishi Sakhi - AI Farming Assistant", layout="wide")

# Load API key from Streamlit secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]

# -------------------------
# TRANSLATION FUNCTION
# -------------------------
def translate_text(text, target_lang="ml"):
    try:
        return GoogleTranslator(source="auto", target=target_lang).translate(text)
    except:
        return text

# -------------------------
# WEATHER FUNCTION
# -------------------------
def get_weather(city):
    api_key = st.secrets.get("OPENWEATHER_API_KEY")
    if not api_key:
        return {"error": "Missing OpenWeather API key in secrets."}

    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    response = requests.get(url).json()
    if response.get("cod") != 200:
        return {"error": response.get("message", "Unable to fetch weather.")}
    
    return {
        "city": response["name"],
        "temperature": response["main"]["temp"],
        "description": response["weather"][0]["description"]
    }

# -------------------------
# AI FARMING ADVISOR
# -------------------------
def ai_advice(query):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are Krishi Sakhi, an AI farming assistant."},
                {"role": "user", "content": query}
            ],
            max_tokens=200
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠️ Error: {e}"

# -------------------------
# SIDEBAR
# -------------------------
st.sidebar.title("🌱 Krishi Sakhi Assistant")
page = st.sidebar.radio("Navigate", ["🏠 Home", "☁️ Weather", "🗺️ Map", "🤖 Chat Assistant", "📒 Activity Log"])

language = st.sidebar.selectbox("🌍 Select Language", ["English", "മലയാളം"])

# -------------------------
# HOME PAGE
# -------------------------
if page == "🏠 Home":
    st.title("🌾 Krishi Sakhi - AI Farming Assistant")
    st.image("https://img.freepik.com/premium-photo/smart-indian-farmer-using-laptop-field_75648-598.jpg", use_column_width=True)
    st.markdown("""
    Welcome to **Krishi Sakhi**, your AI-powered assistant for smart farming.
    
    ✅ Get real-time weather updates  
    ✅ Interactive farm location maps  
    ✅ Chat with AI for farming advice  
    ✅ Maintain an activity log  
    """)
    if language == "മലയാളം":
        st.markdown(translate_text("Welcome to Krishi Sakhi. Your AI-powered assistant for smart farming.", "ml"))

# -------------------------
# WEATHER PAGE
# -------------------------
elif page == "☁️ Weather":
    st.title("☁️ Weather Forecast")
    city = st.text_input("Enter your city", "Kochi")
    if st.button("Get Weather"):
        weather = get_weather(city)
        if "error" in weather:
            st.error(weather["error"])
        else:
            st.success(f"🌡️ {weather['temperature']}°C, {weather['description'].capitalize()} in {weather['city']}")

# -------------------------
# MAP PAGE
# -------------------------
elif page == "🗺️ Map":
    st.title("🗺️ Farm Location Map")
    g = geocoder.ip("me")
    lat, lon = g.latlng if g.ok else (10.0, 76.0)  # Default Kerala
    
    m = folium.Map(location=[lat, lon], zoom_start=10)
    folium.Marker([lat, lon], tooltip="Your Location").add_to(m)
    st_folium(m, width=700, height=500)

# -------------------------
# CHAT ASSISTANT
# -------------------------
elif page == "🤖 Chat Assistant":
    st.title("🤖 AI Farming Assistant")
    user_input = st.text_area("Ask your farming question:")
    if st.button("Get Advice"):
        response = ai_advice(user_input)
        if language == "മലയാളം":
            response = translate_text(response, "ml")
        st.write(response)

# -------------------------
# ACTIVITY LOG
# -------------------------
elif page == "📒 Activity Log":
    st.title("📒 Farmer's Activity Log")
    activity = st.text_input("Log your farming activity:")
    if "log" not in st.session_state:
        st.session_state["log"] = []
    if st.button("Save Activity"):
        st.session_state["log"].append(activity)
        st.success("Activity saved!")
    st.write("### Your Past Activities")
    st.write(st.session_state["log"])