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