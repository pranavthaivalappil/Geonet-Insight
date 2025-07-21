import phonenumbers
import streamlit as st
from phonenumbers import carrier, geocoder
import requests
import json

def track_ip(ip_address):
    """Track IP address and return geolocation and ISP information using ipinfo.io"""
    try:
        # Use ipinfo.io (no API key required, generous free tier: 50,000 requests/month)
        url = f"https://ipinfo.io/{ip_address or ''}/json"
        response = requests.get(url)
        st.write("API status code:", response.status_code)
        st.write("API raw response:", response.text)
        if response.status_code == 200:
            data = response.json()
            # ipinfo.io doesn't have a status field like ip-api, so we check if we got useful data
            if data.get('ip'):
                return data
            else:
                st.error("API returned empty or invalid data")
                return None
        else:
            st.error(f"HTTP error: {response.status_code}")
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
        
        # Option to detect user's own IP or enter custom IP
        ip_option = st.radio(
            "Choose IP tracking option:",
            ["Track My IP", "Enter Custom IP"]
        )
        
        if ip_option == "Track My IP":
            if st.button("Track My IP Address"):
                with st.spinner("Fetching your IP information..."):
                    ip_data = track_ip("")  # Empty string gets user's own IP
                    if ip_data:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.subheader("📍 Location Information")
                            st.write(f"**IP Address:** {ip_data.get('ip', 'N/A')}")
                            st.write(f"**Country:** {ip_data.get('country', 'N/A')}")
                            st.write(f"**Region:** {ip_data.get('region', 'N/A')}")
                            st.write(f"**City:** {ip_data.get('city', 'N/A')}")
                            st.write(f"**Postal Code:** {ip_data.get('postal', 'N/A')}")
                            st.write(f"**Timezone:** {ip_data.get('timezone', 'N/A')}")
                        
                        with col2:
                            st.subheader("🌐 Network Information")
                            st.write(f"**ISP:** {ip_data.get('org', 'N/A')}")
                            st.write(f"**ASN:** {ip_data.get('asn', 'N/A')}")
                            st.write(f"**Coordinates:** {ip_data.get('loc', 'N/A')}")
                            
                            # Security indicators (not available in ip-api, so skip)
                            # if ip_data.get('in_eu'):
                            #     st.write("🇪🇺 **Located in EU**")
                        
                        # Additional information
                        st.subheader("📊 Additional Details")
                        st.json(ip_data)
                    else:
                        st.error("Failed to fetch IP information. Please try again.")
        
        else:  # Enter Custom IP
            custom_ip = st.text_input("Enter IP Address to Track:", placeholder="e.g., 8.8.8.8")
            
            if st.button("Track IP Address"):
                if custom_ip:
                    # Basic IP validation
                    import re
                    ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
                    if re.match(ip_pattern, custom_ip):
                        with st.spinner(f"Tracking IP: {custom_ip}..."):
                            ip_data = track_ip(custom_ip)
                            if ip_data:
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.subheader("📍 Location Information")
                                    st.write(f"**IP Address:** {ip_data.get('ip', 'N/A')}")
                                    st.write(f"**Country:** {ip_data.get('country', 'N/A')}")
                                    st.write(f"**Region:** {ip_data.get('region', 'N/A')}")
                                    st.write(f"**City:** {ip_data.get('city', 'N/A')}")
                                    st.write(f"**Postal Code:** {ip_data.get('postal', 'N/A')}")
                                    st.write(f"**Timezone:** {ip_data.get('timezone', 'N/A')}")
                                
                                with col2:
                                    st.subheader("🌐 Network Information")
                                    st.write(f"**ISP:** {ip_data.get('org', 'N/A')}")
                                    st.write(f"**ASN:** {ip_data.get('asn', 'N/A')}")
                                    st.write(f"**Coordinates:** {ip_data.get('loc', 'N/A')}")
                                    # Security indicators (not available in ip-api, so skip)
                                    # if ip_data.get('in_eu'):
                                    #     st.write("🇪🇺 **Located in EU**")
                                
                                # Map visualization (if coordinates available)
                                if ip_data.get('loc'):
                                    st.subheader("🗺️ Location on Map")
                                    map_data = {
                                        'lat': [float(ip_data.get('loc').split(',')[0])],
                                        'lon': [float(ip_data.get('loc').split(',')[1])]
                                    }
                                    st.map(map_data)
                                
                                # Additional information
                                st.subheader("📊 Raw API Response")
                                st.json(ip_data)
                            else:
                                st.error("Failed to fetch IP information. Please check the IP address and try again.")
                    else:
                        st.error("Please enter a valid IP address format (e.g., 192.168.1.1)")
                else:
                    st.warning("Please enter an IP address to track.")
    
    # Footer
    st.markdown("---")
    st.markdown("**Note:** IP tracking uses ipinfo.io free tier (50,000 requests/month, generous for most use cases). For production use, consider their paid plan.")


if __name__ == "__main__":
    main()
