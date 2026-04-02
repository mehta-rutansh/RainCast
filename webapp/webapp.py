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
# MODERN STYLE
# ---------------------------------------------------
st.markdown("""
<style>

.stApp{
background-color:#f4f6fb;
font-family: "Segoe UI", sans-serif;
}

.main-title{
font-size:40px;
font-weight:700;
color:#1f2937;
}

.city-title{
font-size:26px;
font-weight:600;
margin-top:10px;
color:#374151;
}

.weather-card{
background:white;
padding:20px;
border-radius:14px;
text-align:center;
box-shadow:0px 4px 15px rgba(0,0,0,0.08);
}

.temp-big{
font-size:36px;
font-weight:700;
color:#2563eb;
}

.condition{
font-size:18px;
margin-top:5px;
color:#374151;
}

[data-testid="stPlotlyChart"]{
background:white;
padding:20px;
border-radius:18px;
box-shadow:0px 4px 18px rgba(0,0,0,0.08);
margin-bottom:20px;
}

</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# TITLE
# ---------------------------------------------------
st.markdown('<div class="main-title">🌍 Global Weather Forecast</div>', unsafe_allow_html=True)

city = st.text_input("Enter City Name", "London")

# ---------------------------------------------------
# GET COORDINATES
# ---------------------------------------------------
def get_coordinates(city):
    geolocator = Nominatim(user_agent="weather_app")
    location = geolocator.geocode(city)
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
# WEATHER CODE INTERPRETER
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
# MAIN APP
# ---------------------------------------------------
if city:

    lat, lon = get_coordinates(city)
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

            <div class="temp-big">
            {df.loc[i,"temp_max"]}°C
            </div>

            <div>
            Min {df.loc[i,"temp_min"]}°C
            </div>

            <div class="condition">
            {condition}
            </div>

            <div>
            🌧 Rain: {df.loc[i,"rain_prob"]}%
            </div>

            </div>
            """, unsafe_allow_html=True)

    st.divider()

# ---------------------------------------------------
# WEATHER ANALYTICS TABS
# ---------------------------------------------------

tabs = st.tabs([
"📊 Forecast Dashboard",
"🌡 Temperature Analysis"
])

# ---------------------------------------------------
# TAB 1 DASHBOARD
# ---------------------------------------------------
with tabs[0]:

    st.subheader("Forecast Overview")

    col1, col2 = st.columns(2)

    with col1:

        fig = px.line(
            df,
            x="date",
            y=["temp_max","temp_min"],
            markers=True,
            title="Temperature Trend"
        )

        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Temperature (°C)"
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:

        rain_chart = px.bar(
            df,
            x="date",
            y="rain_prob",
            color="rain_prob",
            color_continuous_scale="Blues",
            title="Rain Probability"
        )

        rain_chart.update_layout(
            xaxis_title="Date",
            yaxis_title="Rain Probability (%)"
        )

        st.plotly_chart(rain_chart, use_container_width=True)

# ---------------------------------------------------
# TAB 2 TEMPERATURE ANALYSIS
# ---------------------------------------------------
with tabs[1]:

    st.subheader("Temperature Insights")

    df["temp_range"] = df["temp_max"] - df["temp_min"]

    col1, col2 = st.columns(2)

    with col1:

        range_chart = px.bar(
            df,
            x="date",
            y="temp_range",
            color="temp_range",
            color_continuous_scale="Oranges",
            title="Daily Temperature Range"
        )

        st.plotly_chart(range_chart, use_container_width=True)

    with col2:

        compare_chart = px.bar(
            df,
            x="date",
            y=["temp_max","temp_min"],
            barmode="group",
            title="Max vs Min Temperature"
        )

        st.plotly_chart(compare_chart, use_container_width=True)

# ---------------------------------------------------
# FOOTER
# ---------------------------------------------------
st.caption("Weather data provided by Open-Meteo")