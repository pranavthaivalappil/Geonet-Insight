import phonenumbers
import streamlit as st
from phonenumbers import carrier, geocoder
import requests
import json


def track_ip(ip_address):
    """Track IP address and return geolocation and ISP information"""
    try:
        # Using ipapi.co for IP tracking (free tier: 1000 requests/day)
        response = requests.get(f"https://ipapi.co/{ip_address}/json/")
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            return None
    except Exception as e:
        st.error(f"Error fetching IP data: {str(e)}")
        return None


def main():
    st.title("Network Tracker: Phone Number & IP Address Intelligence")
    st.subheader("Built using Python and Streamlit")
    
    # Create tabs for different tracking types
    tab1, tab2 = st.tabs(["📱 Phone Number Tracker", "🌐 IP Address Tracker"])
    
    with tab1:
        st.header("Phone Number Location Tracker & Service Operator Identifier")
        st.info("Note: The detected service operator is based on the original number assignment and may not reflect the current operator if the number has been ported.")
        mobile_number = st.text_input("Enter Your Phone Number: ", type="password")
        manual_operator = st.text_input("(Optional) Enter your current operator if ported (e.g., Jio, Airtel, Vi):")
        
        if st.button("Track Phone Number"):
            if mobile_number:
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
            else:
                st.warning("Please enter a phone number to track.")
    
    with tab2:
        st.header("IP Address Tracker & Geolocation")
        st.info("Track IP addresses to get location, ISP, and security information.")
        st.write("IP tracking functionality coming soon...")


if __name__ == "__main__":
    main()
