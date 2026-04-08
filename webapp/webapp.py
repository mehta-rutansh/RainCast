import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from geopy.geocoders import Nominatim
import plotly.graph_objects as go

st.set_page_config(page_title="Weather Intelligence", layout="wide")

st.title("🌍 Weather Intelligence Dashboard")

city = st.text_input("🔍 Enter City", placeholder="Ahmedabad")

# ---------------------------------------------------
# STRICT FUNCTION (FOR USER INPUT)
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

    valid_keys = [
        "city", "town", "village",
        "municipality", "county", "state_district"
    ]

    if not any(k in address for k in valid_keys):
        return None, None, None

    if city.strip().lower() not in display_name:
        return None, None, None

    if location.raw.get("importance", 0) < 0.4:
        return None, None, None

    return location.latitude, location.longitude, address


# ---------------------------------------------------
# RELAXED FUNCTION (FOR NEARBY CITIES)
# ---------------------------------------------------
@st.cache_data
def get_coordinates_relaxed(city):
    geolocator = Nominatim(user_agent="weather_app")

    location = geolocator.geocode(city)

    if not location:
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
# NEARBY MAP (BASE)
# ---------------------------------------------------
nearby_map = {
    "ahmedabad": ["Surat", "Vadodara", "Rajkot"],
    "anand": ["Nadiad", "Vadodara", "Ahmedabad"],
    "vapi": ["Valsad", "Daman", "Navsari"],
    "navsari": ["Surat", "Valsad", "Vapi"]
}


# ---------------------------------------------------
# MAIN LOGIC
# ---------------------------------------------------
lat, lon, address = None, None, None
valid_city = False

if city:
    lat, lon, address = get_coordinates(city)

    if lat is None:
        st.error("❌ Invalid city. Showing fallback comparison.")
    else:
        valid_city = True
        current, df = get_weather(lat, lon)


# ---------------------------------------------------
# HOME PAGE
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

    if valid_city:

        st.subheader("Temperature Trend")

        fig = px.line(df, x="date", y=["temp_max", "temp_min"], height=350)
        st.plotly_chart(fig, use_container_width=True)

        df["temp_range"] = df["temp_max"] - df["temp_min"]

        range_chart = px.area(df, x="date", y="temp_range", height=300)
        st.plotly_chart(range_chart, use_container_width=True)

        combo = px.scatter(
            df,
            x="temp_max",
            y="rain_prob",
            size="temp_range",
            height=300
        )
        st.plotly_chart(combo, use_container_width=True)

    else:
        st.info("Enter a valid city to see analytics")


# ---------------------------------------------------
# EDA
# ---------------------------------------------------
with tab2:

    if valid_city:

        st.subheader("📊 Summary Statistics")
        st.dataframe(df.describe(), use_container_width=True)

        hottest_day = df.loc[df["temp_max"].idxmax()]
        coldest_day = df.loc[df["temp_min"].idxmin()]
        rainiest_day = df.loc[df["rain_prob"].idxmax()]

        col1, col2, col3 = st.columns(3)

        col1.success(f"Hottest: {hottest_day['date']} ({hottest_day['temp_max']}°C)")
        col2.info(f"Coldest: {coldest_day['date']} ({coldest_day['temp_min']}°C)")
        col3.warning(f"Rainiest: {rainiest_day['date']} ({rainiest_day['rain_prob']}%)")

        hist = px.histogram(df, x="temp_max", height=300)
        st.plotly_chart(hist, use_container_width=True)

        df["rolling_temp"] = df["temp_max"].rolling(3).mean()

        rolling = px.line(df, x="date", y=["temp_max", "rolling_temp"], height=300)
        st.plotly_chart(rolling, use_container_width=True)

    else:
        st.info("Enter a valid city to see EDA insights")


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
        cities_to_compare = ["Ahmedabad", "Surat", "Vadodara", "Rajkot"]

    for c in cities_to_compare:

        lat2, lon2 = get_coordinates_relaxed(c)

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
    st.subheader("🗺 Nearby Cities Map")

map_data = []

for c in cities_to_compare:

    lat2, lon2 = get_coordinates_relaxed(c)

    if lat2 is None:
        continue

    map_data.append({
        "city": c,
        "lat": lat2,
        "lon": lon2
    })

if map_data:

    map_df = pd.DataFrame(map_data)

    fig_map = px.scatter_mapbox(
        map_df,
        lat="lat",
        lon="lon",
        hover_name="city",
        zoom=6,
        height=400
    )

    fig_map.update_layout(
        mapbox_style="open-street-map",
        margin=dict(l=0, r=0, t=0, b=0)
    )

    st.plotly_chart(fig_map, use_container_width=True)

else:
    st.warning("Map data not available")

        if len(df_all["city"].unique()) < 2:
            st.warning("Limited nearby data available")

    else:
        st.warning("No comparison data available")
