import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from geopy.geocoders import Nominatim

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------
st.set_page_config(
    page_title="Weather Intelligence Dashboard",
    page_icon="🌤",
    layout="wide"
)

# ---------------------------------------------------
# PREMIUM UI (GLASSMORPHISM + CLEAN)
# ---------------------------------------------------
st.markdown("""
<style>

/* Global spacing */
.block-container {
    padding: 2rem 3rem;
}

/* Title */
.main-title{
    font-size:42px;
    font-weight:800;
    letter-spacing:-1px;
    margin-bottom:10px;
}

/* Section spacing */
.section{
    margin-top:25px;
}

/* Glass Card */
.card{
    background: rgba(255,255,255,0.05);
    backdrop-filter: blur(14px);
    border-radius:20px;
    padding:20px;
    border:1px solid rgba(255,255,255,0.08);
}

/* Weather cards */
.weather-card{
    background: rgba(255,255,255,0.06);
    border-radius:16px;
    padding:15px;
    text-align:center;
    transition:0.3s;
}

.weather-card:hover{
    transform: translateY(-4px);
}

/* Big temp */
.temp-big{
    font-size:30px;
    font-weight:700;
}

/* Plot spacing */
[data-testid="stPlotlyChart"]{
    margin-top:10px;
}

/* Mobile */
@media (max-width: 768px) {
    .main-title{
        font-size:28px;
    }
}

</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# TITLE
# ---------------------------------------------------
st.markdown('<div class="main-title">🌍 Weather Intelligence Dashboard</div>', unsafe_allow_html=True)

city = st.text_input("🔍 Enter City Name", placeholder="e.g., Ahmedabad, London, New York")

# ---------------------------------------------------
# STRICT VALIDATION
# ---------------------------------------------------
def get_coordinates(city):
    geolocator = Nominatim(user_agent="weather_app")

    location = geolocator.geocode(city, addressdetails=True)

    if location is None:
        return None, None

    address = location.raw.get("address", {})
    valid_keys = ["city", "town", "village", "municipality"]

    if not any(key in address for key in valid_keys):
        return None, None

    return location.latitude, location.longitude

# ---------------------------------------------------
# WEATHER API
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

    data = requests.get(url).json()

    df = pd.DataFrame({
        "date": data["daily"]["time"],
        "temp_max": data["daily"]["temperature_2m_max"],
        "temp_min": data["daily"]["temperature_2m_min"],
        "rain_prob": data["daily"]["precipitation_probability_max"],
        "weathercode": data["daily"]["weathercode"]
    })

    return data["current_weather"], df.head(7)

# ---------------------------------------------------
# MAIN
# ---------------------------------------------------
if city:

    lat, lon = get_coordinates(city)

    if lat is None:
        st.error("❌ Enter a valid city name (Ahmedabad, London, New York)")
        st.stop()

    current, df = get_weather(lat, lon)

# ---------------------------------------------------
# TOP METRICS
# ---------------------------------------------------
    st.markdown('<div class="section"></div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    col1.metric("🌡 Temperature", f"{current['temperature']} °C")
    col2.metric("💨 Wind Speed", f"{current['windspeed']} km/h")
    col3.metric("🧭 Wind Direction", f"{current['winddirection']}°")

# ---------------------------------------------------
# MAP + FORECAST (CLEAN LAYOUT)
# ---------------------------------------------------
    st.markdown('<div class="section"></div>', unsafe_allow_html=True)

    left, right = st.columns([1,2])

# MAP
    with left:
        st.markdown("### 📍 Location Map")

        map_fig = px.scatter_mapbox(
            lat=[lat],
            lon=[lon],
            zoom=5,
            height=300
        )

        map_fig.update_layout(
            mapbox_style="open-street-map",
            margin=dict(l=0,r=0,t=0,b=0)
        )

        st.plotly_chart(map_fig, use_container_width=True)

# FORECAST
    with right:
        st.markdown("### 7-Day Forecast")

        cols = st.columns(7)

        for i in range(len(df)):
            with cols[i]:
                st.markdown(f"""
                <div class="weather-card">
                <b>{df.loc[i,'date']}</b><br>
                <div class="temp-big">{df.loc[i,'temp_max']}°C</div>
                Min {df.loc[i,'temp_min']}°C<br>
                🌧 {df.loc[i,'rain_prob']}%
                </div>
                """, unsafe_allow_html=True)

# ---------------------------------------------------
# ANALYTICS
# ---------------------------------------------------
    st.markdown('<div class="section"></div>', unsafe_allow_html=True)
    st.subheader("📊 Weather Analytics")

    col1, col2 = st.columns(2)

    with col1:
        fig = px.line(df, x="date", y=["temp_max","temp_min"],
                      markers=True, height=350)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        rain = px.bar(df, x="date", y="rain_prob", height=350)
        st.plotly_chart(rain, use_container_width=True)

# ---------------------------------------------------
# EDA SECTION
# ---------------------------------------------------
    st.markdown('<div class="section"></div>', unsafe_allow_html=True)
    st.subheader("📈 Data Insights (EDA)")

    df["temp_range"] = df["temp_max"] - df["temp_min"]

    c1, c2, c3 = st.columns(3)

    c1.metric("Avg Max Temp", f"{df['temp_max'].mean():.1f} °C")
    c2.metric("Avg Min Temp", f"{df['temp_min'].mean():.1f} °C")
    c3.metric("Avg Rain", f"{df['rain_prob'].mean():.0f} %")

# DISTRIBUTION + RELATION
    col1, col2 = st.columns(2)

    with col1:
        hist = px.histogram(df, x="temp_max", height=300)
        st.plotly_chart(hist, use_container_width=True)

    with col2:
        scatter = px.scatter(df, x="temp_max", y="rain_prob",
                             size="temp_range", height=300)
        st.plotly_chart(scatter, use_container_width=True)

# ---------------------------------------------------
# SMART INSIGHTS
# ---------------------------------------------------
    st.markdown('<div class="section"></div>', unsafe_allow_html=True)
    st.subheader("🧠 Smart Insights")

    if df["rain_prob"].mean() > 50:
        st.info("🌧 High rainfall expected this week")
    else:
        st.success("☀ Mostly dry conditions")

    if df["temp_max"].max() > 35:
        st.warning("🔥 Heat alert — stay hydrated")

# ---------------------------------------------------
# FOOTER
# ---------------------------------------------------
st.caption("Powered by Open-Meteo | Designed like a product 🚀")
