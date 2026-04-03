import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from geopy.geocoders import Nominatim

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------
st.set_page_config(
    page_title="Weather Intelligence Dashboard",
    layout="wide"
)

# ---------------------------------------------------
# TITLE
# ---------------------------------------------------
st.title("🌍 Weather Intelligence Dashboard")

city_input = st.text_input(
    "🔍 Enter City (or multiple cities separated by comma)",
    placeholder="Ahmedabad, London, New York"
)

# ---------------------------------------------------
# STRICT VALIDATION (FIXED PROPERLY)
# ---------------------------------------------------
def get_coordinates(city):
    geolocator = Nominatim(user_agent="weather_app")

    location = geolocator.geocode(
        city,
        addressdetails=True,
        exactly_one=True
    )

    if location is None:
        return None, None

    address = location.raw.get("address", {})

    # ✅ MUST be a real city-like entity
    valid_keys = ["city", "town", "village"]

    if not any(k in address for k in valid_keys):
        return None, None

    # ✅ Ensure strong match (IMPORTANT FIX)
    display_name = location.raw.get("display_name", "").lower()

    if city.lower() not in display_name:
        return None, None

    return location.latitude, location.longitude

# ---------------------------------------------------
# WEATHER DATA
# ---------------------------------------------------
def get_weather(lat, lon):
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}"
        f"&longitude={lon}"
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

    return df.head(7)

# ---------------------------------------------------
# MAIN LOGIC
# ---------------------------------------------------
if city_input:

    cities = [c.strip() for c in city_input.split(",")]

    valid_data = []
    invalid_cities = []

    for city in cities:
        lat, lon = get_coordinates(city)

        if lat is None:
            invalid_cities.append(city)
        else:
            df = get_weather(lat, lon)
            df["city"] = city.title()
            valid_data.append(df)

    # ❌ SHOW ERROR IF INVALID
    if invalid_cities:
        st.error(f"❌ Invalid city(s): {', '.join(invalid_cities)}")

    if not valid_data:
        st.stop()

    df_all = pd.concat(valid_data)

# ---------------------------------------------------
# TABS (CLEAN DASHBOARD STRUCTURE)
# ---------------------------------------------------
    tab1, tab2, tab3 = st.tabs([
        "📊 Forecast Dashboard",
        "📈 Data Insights (EDA)",
        "🌍 Multi-City Comparison"
    ])

# ---------------------------------------------------
# TAB 1 → FORECAST
# ---------------------------------------------------
    with tab1:

        st.subheader("Temperature Trend")

        fig = px.line(
            df_all,
            x="date",
            y="temp_max",
            color="city",
            markers=True,
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Rain Probability")

        rain = px.bar(
            df_all,
            x="date",
            y="rain_prob",
            color="city",
            barmode="group",
            height=400
        )

        st.plotly_chart(rain, use_container_width=True)

# ---------------------------------------------------
# TAB 2 → EDA
# ---------------------------------------------------
    with tab2:

        st.subheader("Summary Metrics")

        col1, col2, col3 = st.columns(3)

        col1.metric("Avg Max Temp", f"{df_all['temp_max'].mean():.1f} °C")
        col2.metric("Avg Min Temp", f"{df_all['temp_min'].mean():.1f} °C")
        col3.metric("Avg Rain", f"{df_all['rain_prob'].mean():.0f} %")

        st.divider()

        st.subheader("Temperature Distribution")

        hist = px.histogram(
            df_all,
            x="temp_max",
            color="city",
            height=350
        )

        st.plotly_chart(hist, use_container_width=True)

        st.subheader("Temp vs Rain Relationship")

        scatter = px.scatter(
            df_all,
            x="temp_max",
            y="rain_prob",
            color="city",
            size="rain_prob",
            height=350
        )

        st.plotly_chart(scatter, use_container_width=True)

# ---------------------------------------------------
# TAB 3 → MULTI CITY
# ---------------------------------------------------
    with tab3:

        st.subheader("City Comparison")

        compare = px.bar(
            df_all.groupby("city")[["temp_max","temp_min"]].mean().reset_index(),
            x="city",
            y=["temp_max","temp_min"],
            barmode="group",
            height=400
        )

        st.plotly_chart(compare, use_container_width=True)

        st.subheader("Rain Comparison")

        rain_cmp = px.bar(
            df_all.groupby("city")["rain_prob"].mean().reset_index(),
            x="city",
            y="rain_prob",
            height=400
        )

        st.plotly_chart(rain_cmp, use_container_width=True)
