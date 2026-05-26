import streamlit as st
from PIL import Image
import random
import pandas as pd

st.set_page_config(page_title="Air Pollution Indicator")

st.title("🌍 Air Pollution Indicator")
st.write("Upload image and check air quality")

uploaded_file = st.file_uploader(
    "Upload Image",
    type=["jpg", "jpeg", "png"]
)

if uploaded_file is not None:

    img = Image.open(uploaded_file)

    st.image(
        img,
        caption="Uploaded Image",
        use_container_width=True
    )

    if st.button("Predict"):

        # Demo Prediction
        pollution = random.randint(1, 100)

        # Health Status
        if pollution <= 20:
            status = "🌿 Very Good"
            msg = "Air is Healthy"

        elif pollution <= 40:
            status = "✅ Good"
            msg = "Air quality is Healthy"

        elif pollution <= 60:
            status = "😐 Moderate"
            msg = "Air quality is Average"

        elif pollution <= 80:
            status = "⚠️ Unhealthy"
            msg = "Air quality is Unhealthy"

        else:
            status = "🚨 Very Unhealthy"
            msg = "Air quality is Dangerous"

        st.subheader("Prediction Result")

        st.metric(
            "Pollution Percentage",
            f"{pollution}%"
        )

        st.progress(pollution)

        st.subheader("Health Status")
        st.write(status)

        if pollution <= 40:
            st.success(msg)

        elif pollution <= 60:
            st.warning(msg)

        else:
            st.error(msg)

        st.subheader("Pollution Graph")

        chart = pd.DataFrame({
            "Level": [pollution]
        })

        st.bar_chart(chart)

        st.subheader("Air Quality Scale")

        st.write("""
🌿 Very Good → 0–20%

✅ Good → 21–40%

😐 Moderate → 41–60%

⚠️ Unhealthy → 61–80%

🚨 Very Unhealthy → 81–100%
""")

!pip install pandas plotly ipywidgets

import pandas as pd
import plotly.express as px
import ipywidgets as widgets
from IPython.display import display

data = pd.DataFrame({

'State':[
'Delhi',
'Maharashtra',
'Karnataka',
'Tamil Nadu',
'Gujarat',
'West Bengal',
'Rajasthan',
'Uttar Pradesh',
'Kerala',
'Punjab'
],

'AQI':[320,180,150,120,170,280,210,260,90,140],

'Temperature':[34,31,29,32,36,33,39,37,30,35],

'Lat':[
28.7041,
19.7515,
15.3173,
11.1271,
22.2587,
22.9868,
27.0238,
26.8467,
10.8505,
31.1471
],

'Lon':[
77.1025,
75.7139,
75.7139,
78.6569,
71.1924,
87.8550,
74.2179,
80.9462,
76.2711,
75.3412
]

})

data


state_dropdown = widgets.Dropdown(
    options=data["State"],
    description="State:"
)

output = widgets.Output()


def update_dashboard(change):

    output.clear_output()

    selected = state_dropdown.value

    row = data[data["State"] == selected]

    aqi = row["AQI"].values[0]
    temp = row["Temperature"].values[0]

    fig = px.scatter_geo(
        data,
        lat="Lat",
        lon="Lon",
        size="AQI",
        color="AQI",
        hover_name="State",
        scope="asia",

        title="India Air Pollution Dashboard",

        color_continuous_scale="Turbo",

        size_max=40
    )

    fig.update_geos(
        center=dict(lat=22, lon=79),
        projection_scale=4
    )

    with output:

        print("Selected State:", selected)
        print()

        print("🌫 AQI:", aqi)

        if aqi <= 100:
            print("Air Quality: Good")

        elif aqi <= 200:
            print("Air Quality: Moderate")

        elif aqi <= 300:
            print("Air Quality: Poor")

        else:
            print("Air Quality: Hazardous")

        print()

        print("🌡 Temperature:", temp, "°C")

        fig.show()


state_dropdown.observe(
    update_dashboard,
    names="value"
)

display(state_dropdown)

display(output)

update_dashboard(None)
