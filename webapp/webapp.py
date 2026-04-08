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

    # ✅ VALID CITY TYPES (FIXED INDENTATION)
    valid_keys = [
        "city",
        "town",
        "village",
        "municipality",
        "county",
        "state_district"
    ]

    if not any(k in address for k in valid_keys):
        return None, None, None

    # ✅ STRICT MATCH
    city_clean = city.strip().lower()

    if city_clean not in display_name:
        return None, None, None

    # ✅ RELAXED IMPORTANCE (for Indian cities)
    if location.raw.get("importance", 0) < 0.4:
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
# ---------------------------------------------------
# MAIN
# ---------------------------------------------------

lat, lon, address = None, None, None
valid_city = False

if city:

    lat, lon, address = get_coordinates(city)

    if lat is None:
        st.error("❌ Invalid city. Showing default comparison instead.")
        valid_city = False
    else:
        valid_city = True
        current, df = get_weather(lat, lon)

# ---------------------------------------------------
# HOME PAGE (ONLY IF VALID)
# ---------------------------------------------------

if valid_city:

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
# TABS (ALWAYS SHOW)
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

        st.subheader("Temperature Trend")

        fig = px.line(df, x="date", y=["temp_max","temp_min"], height=350)
        st.plotly_chart(fig, use_container_width=True)

        df["temp_range"] = df["temp_max"] - df["temp_min"]

        st.subheader("Daily Temperature Variation")

        range_chart = px.area(df, x="date", y="temp_range", height=300)
        st.plotly_chart(range_chart, use_container_width=True)

        st.subheader("Rain vs Temperature Pattern")

        combo = px.scatter(
            df,
            x="temp_max",
            y="rain_prob",
            size="temp_range",
            height=300
        )
        st.plotly_chart(combo, use_container_width=True)

    # ---------------------------------------------------
    # EDA
    # ---------------------------------------------------
    with tab2:

        st.subheader("📊 Summary Statistics")
        st.dataframe(df.describe(), use_container_width=True)

        st.subheader("🔥 Weather Extremes")

        hottest_day = df.loc[df["temp_max"].idxmax()]
        coldest_day = df.loc[df["temp_min"].idxmin()]
        rainiest_day = df.loc[df["rain_prob"].idxmax()]

        col1, col2, col3 = st.columns(3)

        col1.success(f"Hottest: {hottest_day['date']} ({hottest_day['temp_max']}°C)")
        col2.info(f"Coldest: {coldest_day['date']} ({coldest_day['temp_min']}°C)")
        col3.warning(f"Rainiest: {rainiest_day['date']} ({rainiest_day['rain_prob']}%)")

        st.subheader("Temperature Distribution")
        hist = px.histogram(df, x="temp_max", height=300)
        st.plotly_chart(hist, use_container_width=True)

        st.subheader("Rolling Trend")
        df["rolling_temp"] = df["temp_max"].rolling(3).mean()

        rolling = px.line(df, x="date", y=["temp_max","rolling_temp"], height=300)
        st.plotly_chart(rolling, use_container_width=True)

    # ---------------------------------------------------
    # NEARBY COMPARISON
    # ---------------------------------------------------
    with tab3:

        st.subheader("🌍 Nearby Cities Comparison")

        data_list = []

        if valid_city:
            base_city = city.title()
            cities_to_compare = [base_city]

            city_key = address.get("city", "").lower() if address else ""

            if city_key in nearby_map:
                cities_to_compare += nearby_map[city_key]

        else:
            # 🔥 fallback cities (when invalid input)
            cities_to_compare = ["Ahmedabad", "Surat", "Vadodara", "Rajkot"]

        for c in cities_to_compare:

            lat2, lon2, _ = get_coordinates(c)

            if lat2 is None:
                continue

            _, d = get_weather(lat2, lon2)
            d["city"] = c
            data_list.append(d)

        if data_list:
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
            st.warning("No comparison data available")
