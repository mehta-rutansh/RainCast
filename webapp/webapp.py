import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from geopy.geocoders import Nominatim

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------
st.set_page_config(
    page_title="Global Weather Dashboard",
    page_icon="🌤",
    layout="wide"
)

# ---------------------------------------------------
# MODERN UI (THEME ADAPTIVE + MOBILE FRIENDLY)
# ---------------------------------------------------
st.markdown("""
<style>

/* Main container spacing */
.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

/* Titles */
.main-title{
    font-size:42px;
    font-weight:800;
    letter-spacing: -1px;
}

/* City title */
.city-title{
    font-size:26px;
    font-weight:600;
    margin-top:10px;
}

/* Weather Cards */
.weather-card{
    background: rgba(255,255,255,0.06);
    backdrop-filter: blur(12px);
    padding:18px;
    border-radius:18px;
    text-align:center;
    border: 1px solid rgba(255,255,255,0.08);
    transition: 0.3s;
}

.weather-card:hover{
    transform: translateY(-5px);
}

/* Temperature */
.temp-big{
    font-size:34px;
    font-weight:700;
}

/* Plot rounding */
[data-testid="stPlotlyChart"]{
    border-radius:16px;
}

/* Mobile Optimization */
@media (max-width: 768px) {
    .main-title{
        font-size:28px;
    }
    .temp-big{
        font-size:26px;
    }
}

</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# TITLE
# ---------------------------------------------------
st.markdown('<div class="main-title">🌍 Global Weather Dashboard</div>', unsafe_allow_html=True)

city = st.text_input("🔍 Enter City Name", placeholder="e.g., Ahmedabad, London, New York")

# ---------------------------------------------------
# GET COORDINATES (VALIDATION ADDED)
# ---------------------------------------------------
def get_coordinates(city):
    geolocator = Nominatim(user_agent="weather_app")
    location = geolocator.geocode(city)

    if location is None:
        return None, None

    return location.latitude, location.longitude

# ---------------------------------------------------
# GET WEATHER DATA
# ---------------------------------------------------
def get_weather(lat, lon):

    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}"
        f"&longitude={lon}"
        "&current_weather=true"
        "&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,weathercode"
        "&timezone=auto"
    )

    response = requests.get(url)
    data = response.json()

    daily = pd.DataFrame({
        "date": data["daily"]["time"],
        "temp_max": data["daily"]["temperature_2m_max"],
        "temp_min": data["daily"]["temperature_2m_min"],
        "rain_prob": data["daily"]["precipitation_probability_max"],
        "weathercode": data["daily"]["weathercode"]
    })

    current = data["current_weather"]

    return current, daily.head(7)

# ---------------------------------------------------
# WEATHER INTERPRETER
# ---------------------------------------------------
def interpret_weather(code):

    if code == 0:
        return "☀ Clear"
    elif code in [1,2,3]:
        return "🌤 Partly Cloudy"
    elif code in [45,48]:
        return "🌫 Fog"
    elif code in [51,53,55,61,63,65,80,81,82]:
        return "🌧 Rain"
    elif code in [71,73,75]:
        return "❄ Snow"
    else:
        return "☁ Cloudy"

# ---------------------------------------------------
# MAIN LOGIC
# ---------------------------------------------------
if city:

    lat, lon = get_coordinates(city)

    # ❌ INVALID CITY HANDLING
    if lat is None:
        st.error("❌ Invalid city name. Please enter a real city (e.g., Ahmedabad, London).")
        st.stop()

    current, df = get_weather(lat, lon)

    st.markdown(f'<div class="city-title">📍 {city.title()}</div>', unsafe_allow_html=True)

# ---------------------------------------------------
# CURRENT WEATHER
# ---------------------------------------------------
    st.subheader("Current Weather")

    col1, col2, col3 = st.columns(3)

    col1.metric("🌡 Temperature", f"{current['temperature']} °C")
    col2.metric("💨 Wind Speed", f"{current['windspeed']} km/h")
    col3.metric("🧭 Wind Direction", f"{current['winddirection']}°")

    st.divider()

# ---------------------------------------------------
# 7 DAY FORECAST
# ---------------------------------------------------
    st.subheader("7 Day Forecast")

    cols = st.columns(7)

    for i in range(len(df)):

        condition = interpret_weather(df.loc[i, "weathercode"])

        with cols[i]:
            st.markdown(f"""
            <div class="weather-card">
            <div><b>{df.loc[i,"date"]}</b></div>
            <div class="temp-big">{df.loc[i,"temp_max"]}°C</div>
            <div>Min {df.loc[i,"temp_min"]}°C</div>
            <div>{condition}</div>
            <div>🌧 {df.loc[i,"rain_prob"]}%</div>
            </div>
            """, unsafe_allow_html=True)

    st.divider()

# ---------------------------------------------------
# TABS
# ---------------------------------------------------
    tabs = st.tabs([
        "📊 Forecast Dashboard",
        "🌡 Temperature Analysis",
        "📈 Data Insights (EDA)"
    ])

# ---------------------------------------------------
# TAB 1
# ---------------------------------------------------
    with tabs[0]:

        col1, col2 = st.columns(2)

        with col1:
            fig = px.line(df, x="date", y=["temp_max","temp_min"], markers=True,
                          title="Temperature Trend")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            rain_chart = px.bar(df, x="date", y="rain_prob",
                                color="rain_prob",
                                title="Rain Probability")
            st.plotly_chart(rain_chart, use_container_width=True)

# ---------------------------------------------------
# TAB 2
# ---------------------------------------------------
    with tabs[1]:

        df["temp_range"] = df["temp_max"] - df["temp_min"]

        col1, col2 = st.columns(2)

        with col1:
            range_chart = px.bar(df, x="date", y="temp_range",
                                 title="Daily Temperature Range")
            st.plotly_chart(range_chart, use_container_width=True)

        with col2:
            compare_chart = px.bar(df, x="date",
                                  y=["temp_max","temp_min"],
                                  barmode="group",
                                  title="Max vs Min Temperature")
            st.plotly_chart(compare_chart, use_container_width=True)

# ---------------------------------------------------
# TAB 3 (EDA)
# ---------------------------------------------------
    with tabs[2]:

        st.subheader("📊 Summary Metrics")

        col1, col2, col3 = st.columns(3)

        col1.metric("Avg Max Temp", f"{df['temp_max'].mean():.1f} °C")
        col2.metric("Avg Min Temp", f"{df['temp_min'].mean():.1f} °C")
        col3.metric("Avg Rain Chance", f"{df['rain_prob'].mean():.0f} %")

        st.divider()

        st.subheader("Temperature Distribution")

        hist = px.histogram(df, x="temp_max", nbins=7)
        st.plotly_chart(hist, use_container_width=True)

        st.subheader("Relationship: Temp vs Rain")

        scatter = px.scatter(df, x="temp_max", y="rain_prob",
                             size=df["temp_max"] - df["temp_min"])
        st.plotly_chart(scatter, use_container_width=True)

        st.subheader("🧠 Key Insights")

        if df["rain_prob"].mean() > 50:
            st.info("High chances of rain this week 🌧")
        else:
            st.success("Mostly dry weather expected ☀")

        if df["temp_max"].max() > 35:
            st.warning("High temperature alert 🔥 Stay hydrated")

# ---------------------------------------------------
# FOOTER
# ---------------------------------------------------
st.caption("Weather data provided by Open-Meteo")
