import phonenumbers
import streamlit as st
from phonenumbers import carrier, geocoder
import requests
import json


def main():
    st.title("Phone Number Location Tracker & Service Operator Identifier")
    st.subheader("Build usihg Python and Streamlit")
    st.info("Note: The detected service operator is based on the original number assignment and may not reflect the current operator if the number has been ported.")
    mobile_number = st.text_input("Enter Your Phone Number: ", type="password")
    manual_operator = st.text_input("(Optional) Enter your current operator if ported (e.g., Jio, Airtel, Vi):")
    if st.button("Track"):
        ch_number = phonenumbers.parse(mobile_number, "CH")
        st.success(
            "Country Name:  {}".format(geocoder.description_for_number(ch_number, "en"))
        )
        services_operator = phonenumbers.parse(mobile_number, "RO")
        detected_operator = carrier.name_for_number(services_operator, "en")
        if manual_operator.strip():
            st.success(f"Service Operator (Manual): {manual_operator.strip()}")
            st.info(f"(Detected Operator: {detected_operator})")
        else:
            st.success(f"Service Operator: {detected_operator}")


if __name__ == "__main__":
    main()
