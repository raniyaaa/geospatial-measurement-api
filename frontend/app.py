
import streamlit as st
import requests
import os

API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://127.0.0.1:8000"
)

st.set_page_config(
    page_title="Geospatial File Measurement",
    layout="wide"
)


st.title("Geospatial File Measurement")

st.markdown(
    """
    Upload a geospatial file to extract its features and calculate
    geometric measurements.

    **Supported formats:** KML and Shapefile ZIP

    **Measurements:**
    - Polygon: Area in square metres (m²)
    - LineString: Length in metres (m)
    - Point: No area or length calculation
    """
)


uploaded_file = st.file_uploader(
    "Choose a geospatial file",
    type=["kml", "zip"]
)
st.subheader("Upload a File")

if uploaded_file is not None:
    if st.button("Upload and Process"):
        st.session_state.pop("file_id", None)
        try:
            files = {
                "file": (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    uploaded_file.type
                )
            }

            with st.spinner("Uploading and processing file..."):
                response = requests.post(
                    f"{API_BASE_URL}/api/files/",
                    files=files,
                    timeout=120
                )

            if response.status_code == 200:
                result = response.json()
                file_id = result["id"]

                st.success("File uploaded and processed successfully!")
                st.write("File ID:", file_id)
                st.write("Filename:", result["filename"])

                st.session_state["file_id"] = file_id

            else:
                st.error(
                    f"Upload failed: {response.status_code} - "
                    f"{response.text}"
                )

        except requests.RequestException as error:
            st.error(f"Could not connect to the API: {error}")


# Display file details and measurements after a successful upload
if "file_id" in st.session_state:
    file_id = st.session_state["file_id"]

    st.divider()
    st.subheader("File Details")

    try:
        details_response = requests.get(
            f"{API_BASE_URL}/api/files/{file_id}",
            timeout=30
        )

        if details_response.status_code == 200:
            details = details_response.json()

            col1, col2, col3 = st.columns(3)

            col1.metric("File ID", details["id"])
            col2.metric("Feature Count", details["feature_count"] or 0)
            col3.metric("Status", details["status"].title())

            st.write("**Filename:**", details["filename"])
            st.write("**File Type:**", details["file_type"])
            st.write("**Source CRS:**", details["crs"] or "Not available")

        else:
            st.error(
                f"Could not retrieve file details: "
                f"{details_response.text}"
            )

        st.subheader("Measurements")

        measurements_response = requests.get(
            f"{API_BASE_URL}/api/files/{file_id}/measurements/",
            timeout=30
        )

        if measurements_response.status_code == 200:
            measurements = measurements_response.json()

            if measurements:
                display_measurements = []

                for measurement in measurements:
                    display_measurements.append({
                        "Feature Index": measurement["feature_index"],
                        "Geometry Type": measurement["geometry_type"],
                        "Area (m²)": (
                            f'{measurement["area"]:,.2f}'
                            if measurement["area"] is not None
                            else "—"
                        ),
                        "Length (m)": (
                            f'{measurement["length"]:,.2f}'
                            if measurement["length"] is not None
                            else "—"
                        )
                    })

                st.dataframe(
                    display_measurements,
                    use_container_width=True,
                    hide_index=True
                )

            else:
                st.info("No features were found in this file.")

        else:
            st.error(
                f"Could not retrieve measurements: "
                f"{measurements_response.text}"
            )

    except requests.RequestException as error:
        st.error(f"Could not connect to the API: {error}")
