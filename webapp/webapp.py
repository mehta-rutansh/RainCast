import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from geopy.geocoders import Nominatim

st.set_page_config(page_title="Weather Intelligence", layout="wide")

st.title("🌍 Weather Intelligence Dashboard")

city = st.text_input("🔍 Enter City", placeholder="Ahmedabad")

# ---------------------------------------------------
# STRICT VALIDATION (FINAL FIX)
# ---------------------------------------------------
def get_coordinates(city):
    geolocator = Nominatim(user_agent="weather_app")

    location = geolocator.geocode(
        city,
        addressdetails=True,
        exactly_one=True
    )

    if not location:
        return None, None, None

    address = location.raw.get("address", {})
    display_name = location.raw.get("display_name", "").lower()

    # ✅ Only accept real cities
    if not any(k in address for k in ["city", "town"]):
        return None, None, None

    # ✅ STRICT MATCH (THIS FIXES xyz)
    city_clean = city.strip().lower()

    if city_clean not in display_name:
        return None, None, None

    # ✅ Reject weak matches (low importance places)
    if location.raw.get("importance", 0) < 0.5:
        return None, None, None

    return location.latitude, location.longitude, address

# ---------------------------------------------------
# WEATHER API
# ---------------------------------------------------
def get_weather(lat, lon):
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}"
        f"&longitude={lon}"
        "&current_weather=true"
        "&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max"
        "&timezone=auto"
    )

    data = requests.get(url).json()

    df = pd.DataFrame({
        "date": data["daily"]["time"],
        "temp_max": data["daily"]["temperature_2m_max"],
        "temp_min": data["daily"]["temperature_2m_min"],
        "rain_prob": data["daily"]["precipitation_probability_max"]
    })

    return data["current_weather"], df.head(7)

# ---------------------------------------------------
# NEARBY CITIES (STATIC INTELLIGENCE)
# ---------------------------------------------------
nearby_map = {
    "ahmedabad": ["Surat", "Vadodara", "Rajkot"],
    "london": ["Manchester", "Birmingham", "Leeds"],
    "new york": ["Boston", "Philadelphia", "Newark"]
}

# ---------------------------------------------------
# MAIN
# ---------------------------------------------------
if city:

    lat, lon, address = get_coordinates(city)

    if lat is None:
        st.error("❌ Enter a valid city name (No random text allowed)")
        st.stop()

    current, df = get_weather(lat, lon)

# ---------------------------------------------------
# HOME PAGE (CURRENT + FORECAST)
# ---------------------------------------------------
    st.subheader(f"📍 {city.title()}")

    c1, c2, c3 = st.columns(3)
    c1.metric("🌡 Temp", f"{current['temperature']} °C")
    c2.metric("💨 Wind", f"{current['windspeed']} km/h")
    c3.metric("🧭 Direction", f"{current['winddirection']}°")

    st.divider()

    st.subheader("7-Day Forecast")

    cols = st.columns(7)

    for i in range(len(df)):
        with cols[i]:
            st.metric(
                df.loc[i, "date"],
                f"{df.loc[i, 'temp_max']}°C",
                f"Rain {df.loc[i, 'rain_prob']}%"
            )

# ---------------------------------------------------
# TABS
# ---------------------------------------------------
    tab1, tab2, tab3 = st.tabs([
        "📊 Analytics",
        "📈 EDA",
        "🌍 Nearby Comparison"
    ])

# ---------------------------------------------------
# ANALYTICS
# ---------------------------------------------------
    with tab1:

        fig = px.line(df, x="date", y=["temp_max","temp_min"], height=350)
        st.plotly_chart(fig, use_container_width=True)

        rain = px.bar(df, x="date", y="rain_prob", height=350)
        st.plotly_chart(rain, use_container_width=True)

# ---------------------------------------------------
# EDA
# ---------------------------------------------------
    with tab2:

        df["temp_range"] = df["temp_max"] - df["temp_min"]

        st.metric("Avg Temp", f"{df['temp_max'].mean():.1f} °C")

        hist = px.histogram(df, x="temp_max", height=300)
        st.plotly_chart(hist, use_container_width=True)

        scatter = px.scatter(df, x="temp_max", y="rain_prob", height=300)
        st.plotly_chart(scatter, use_container_width=True)

# ---------------------------------------------------
# NEARBY COMPARISON
# ---------------------------------------------------
    with tab3:

        city_key = city.lower()

        if city_key in nearby_map:

            all_cities = [city.title()] + nearby_map[city_key]

            data_list = []

            for c in all_cities:
                lat, lon, _ = get_coordinates(c)
                _, d = get_weather(lat, lon)
                d["city"] = c
                data_list.append(d)

            df_all = pd.concat(data_list)

            compare = px.line(
                df_all,
                x="date",
                y="temp_max",
                color="city",
                height=400
            )

            st.plotly_chart(compare, use_container_width=True)

        else:
            st.info("Nearby comparison not available for this city yet")
