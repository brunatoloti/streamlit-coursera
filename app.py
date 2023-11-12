import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import pydeck as pdk
import plotly.express as px

DATA_URL = "./data/Motor_Vehicle_Collisions_-_Crashes.csv"

st.title("Motor Vehicle Collisions in New York City")
st.markdown("This application is a Streamlit dashboard that can be used"
            " to analyze motor vehicle collisions in NYC")

@st.cache_data(persist=True)
def load_data(nrows):
    data = pd.read_csv(DATA_URL, 
                       nrows=nrows,
                       parse_dates=[['CRASH_DATE', 'CRASH_TIME']])
    data.dropna(subset=['LATITUDE', 'LONGITUDE'], inplace=True)
    lowercase = lambda x: str(x).lower()
    data.rename(lowercase, axis='columns', inplace=True)
    data.rename(columns={'crash_date_crash_time': 'date/time'}, inplace=True)
    return data

data = load_data(100000)
original_data = data.copy()

st.header("Where are the most people injured in NYC?")
injured_people = st.slider("Number of persons injured in vehicle collisions", 
                           min_value=0, 
                           max_value=int(data['injured_persons'].max()))
st.map(data.query("injured_persons >= @injured_people")[["latitude", "longitude"]].dropna(how="any"))

st.header("How many collisions occur during a given time of day?")
hour = st.time_input("Hour to look at", datetime.min, step=3600).hour
data = data[data['date/time'].dt.hour == hour]

st.markdown("Vehicle collisions between %i:00 and %i:00" % (hour, (hour + 1) % 24))

midpoint = (np.median(data['latitude']), np.median(data['longitude']))
st.write(pdk.Deck(
    map_style="mapbox://styles/mapbox/light-v9",
    initial_view_state={
        "latitude": midpoint[0],
        "longitude": midpoint[1],
        "zoom": 11,
        "pitch": 50,
    },
    layers=[
        pdk.Layer(
            "HexagonLayer",
            data=data[['date/time', 'latitude', 'longitude']],
            get_position=['longitude', 'latitude'],
            radius=100,
            extruded=True,
            pickable=True,
            elevation_scale=4,
            elevation_range=[0, 1000]
        ),
    ],
))

st.subheader("Breakdown by minute between %i:00 and %i:00" % (hour, (hour + 1) % 24))
filtered_data = data[
    (data["date/time"].dt.hour >= hour) & (data["date/time"].dt.hour < (hour + 1))
]
hist = np.histogram(filtered_data["date/time"].dt.minute, bins=60, range=(0,60))[0]
chart_data = pd.DataFrame({'minute': range(60), 'crashes': hist})
fig = px.bar(chart_data, x='minute', y='crashes', hover_data=['minute', 'crashes'], height=400)
st.write(fig)

st.header("Top 5 dangerous streets by affected type")
select_type_people = st.selectbox("Affected type of people", ["Pedestrians", "Cyclists", "Motorists"])

if select_type_people == "Pedestrians":
    st.write(original_data.query("injured_pedestrians >= 1")[["on_street_name", "injured_pedestrians"]].groupby("on_street_name").sum().reset_index().sort_values(by="injured_pedestrians", ascending=False).dropna(how="any")[:5].reset_index(drop=True))
elif select_type_people == "Cyclists":
    st.write(original_data.query("injured_cyclists >= 1")[["on_street_name", "injured_cyclists"]].groupby("on_street_name").sum().reset_index().sort_values(by="injured_cyclists", ascending=False).dropna(how="any")[:5].reset_index(drop=True))
else:
    st.write(original_data.query("injured_motorists >= 1")[["on_street_name", "injured_motorists"]].groupby("on_street_name").sum().reset_index().sort_values(by="injured_motorists", ascending=False).dropna(how="any")[:5].reset_index(drop=True))


if st.checkbox("Show Raw Data", False):
    st.subheader("Raw Data")
    st.write(data)