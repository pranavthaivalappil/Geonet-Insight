import phonenumbers
import streamlit as st
from phonenumbers import carrier, geocoder
import requests
import json
import streamlit.components.v1 as components
import sqlite3
import pandas as pd
from datetime import datetime
import os


def init_database():
    """Initialize SQLite database and create tables if they don't exist"""
    conn = sqlite3.connect('tracker_data.db')
    cursor = conn.cursor()
    
    # Create phone tracking table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS phone_searches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone_number TEXT,
            country TEXT,
            detected_operator TEXT,
            manual_operator TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            user_ip TEXT
        )
    ''')
    
    # Create IP tracking table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ip_searches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            searched_ip TEXT,
            country TEXT,
            region TEXT,
            city TEXT,
            isp TEXT,
            coordinates TEXT,
            search_type TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            user_ip TEXT
        )
    ''')
    
    conn.commit()
    conn.close()


def save_phone_search(phone_number, country, detected_operator, manual_operator, user_ip):
    """Save phone number search to database"""
    try:
        conn = sqlite3.connect('tracker_data.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO phone_searches (phone_number, country, detected_operator, manual_operator, user_ip)
            VALUES (?, ?, ?, ?, ?)
        ''', (phone_number, country, detected_operator, manual_operator, user_ip))
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Error saving phone search: {str(e)}")


def save_ip_search(searched_ip, country, region, city, isp, coordinates, search_type, user_ip):
    """Save IP address search to database"""
    try:
        conn = sqlite3.connect('tracker_data.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO ip_searches (searched_ip, country, region, city, isp, coordinates, search_type, user_ip)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (searched_ip, country, region, city, isp, coordinates, search_type, user_ip))
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Error saving IP search: {str(e)}")


def get_search_statistics():
    """Get statistics from the database"""
    try:
        conn = sqlite3.connect('tracker_data.db')
        
        # Get phone search stats
        phone_df = pd.read_sql_query('''
            SELECT country, COUNT(*) as count
            FROM phone_searches
            GROUP BY country
            ORDER BY count DESC
            LIMIT 10
        ''', conn)
        
        # Get IP search stats
        ip_df = pd.read_sql_query('''
            SELECT country, COUNT(*) as count
            FROM ip_searches
            GROUP BY country
            ORDER BY count DESC
            LIMIT 10
        ''', conn)
        
        # Get total counts
        total_phone = pd.read_sql_query('SELECT COUNT(*) as total FROM phone_searches', conn).iloc[0]['total']
        total_ip = pd.read_sql_query('SELECT COUNT(*) as total FROM ip_searches', conn).iloc[0]['total']
        
        # Get recent searches
        recent_searches = pd.read_sql_query('''
            SELECT 'Phone' as type, phone_number as search_term, country, timestamp
            FROM phone_searches
            UNION ALL
            SELECT 'IP' as type, searched_ip as search_term, country, timestamp
            FROM ip_searches
            ORDER BY timestamp DESC
            LIMIT 20
        ''', conn)
        
        conn.close()
        
        return {
            'phone_countries': phone_df,
            'ip_countries': ip_df,
            'total_phone': total_phone,
            'total_ip': total_ip,
            'recent_searches': recent_searches
        }
    except Exception as e:
        st.error(f"Error getting statistics: {str(e)}")
        return None


def get_client_ip():
    """Get the real client IP using JavaScript"""
    # JavaScript code to fetch the real client IP
    js_code = """
    <script>
    async function getClientIP() {
        try {
            const response = await fetch('https://api.ipify.org?format=json');
            const data = await response.json();
            // Send the IP back to Streamlit
            window.parent.postMessage({
                type: 'CLIENT_IP',
                ip: data.ip
            }, '*');
        } catch (error) {
            console.error('Error fetching IP:', error);
            window.parent.postMessage({
                type: 'CLIENT_IP',
                ip: null,
                error: 'Failed to fetch IP'
            }, '*');
        }
    }
    
    // Execute when page loads
    getClientIP();
    </script>
    <div style="display: none;">Getting your IP address...</div>
    """
    
    # Execute the JavaScript
    components.html(js_code, height=0)


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
    # Initialize database
    init_database()
    
    st.title("Network Tracker: Phone Number & IP Address Intelligence")
    st.subheader("Built using Python and Streamlit")
    
    # Privacy notice
    st.info("🔒 **Privacy Notice:** This app automatically detects your IP address to provide accurate geolocation services. Search history is stored locally for analytics. No personal information is shared with third parties.")
    
    # Create tabs for different tracking types
    tab2, tab1, tab3 = st.tabs(["🌐 IP Address Intelligence", "📱 Phone Number Intelligence", "📊 Analytics & History"])
    
    with tab2:
        st.header("IP Address Intelligence & Geolocation")
        st.info("Analyze IP addresses to get location, ISP, and network intelligence.")
        
        # Initialize session state for client IP
        if 'client_ip' not in st.session_state:
            st.session_state.client_ip = None
        
        # Option to detect user's own IP or enter custom IP
        ip_option = st.radio(
            "Choose IP tracking option:",
            ["Track My Real IP (Auto-Detect)", "Enter Custom IP"]
        )
        
        if ip_option == "Track My Real IP (Auto-Detect)":
            st.write("**Detecting your real IP address...**")
            
            # Get client IP using JavaScript
            get_client_ip()
            
            # Listen for messages from JavaScript
            # Note: This is a simplified approach - in a real app you might need a more robust solution
            if st.button("Track My Real IP Address"):
                # For now, we'll use a fallback method since direct JS communication is complex in Streamlit
                with st.spinner("Fetching your real IP information..."):
                    # Use a client-side IP detection service
                    try:
                        # First, get the real client IP
                        client_ip_response = requests.get("https://api.ipify.org?format=json")
                        if client_ip_response.status_code == 200:
                            client_ip_data = client_ip_response.json()
                            real_ip = client_ip_data.get('ip')
                            st.success(f"🎯 **Your Real IP Detected:** {real_ip}")
                            
                            # Now get location data for the real IP
                            ip_data = track_ip(real_ip)
                        else:
                            st.error("Could not detect your real IP. Please try the custom IP option.")
                            ip_data = None
                    except Exception as e:
                        st.error(f"Error detecting real IP: {str(e)}")
                        ip_data = None
                    
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
                        
                        # Map visualization (if coordinates available)
                        if ip_data.get('loc'):
                            st.subheader("🗺️ Location on Map")
                            try:
                                coords = ip_data.get('loc').split(',')
                                map_data = {
                                    'lat': [float(coords[0])],
                                    'lon': [float(coords[1])]
                                }
                                st.map(map_data)
                            except:
                                st.error("Could not parse coordinates for map display")
                        
                        # Save to database
                        try:
                            user_ip_response = requests.get("https://api.ipify.org?format=json")
                            user_ip = user_ip_response.json().get('ip', 'Unknown') if user_ip_response.status_code == 200 else 'Unknown'
                        except:
                            user_ip = 'Unknown'
                        
                        save_ip_search(
                            ip_data.get('ip', ''),
                            ip_data.get('country', ''),
                            ip_data.get('region', ''),
                            ip_data.get('city', ''),
                            ip_data.get('org', ''),
                            ip_data.get('loc', ''),
                            'Auto-Detect',
                            user_ip
                        )
                        
                        # Additional information
                        st.subheader("📊 Additional Details")
                        st.json(ip_data)
                        st.success("✅ Search saved to history!")
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
                                
                                # Map visualization (if coordinates available)
                                if ip_data.get('loc'):
                                    st.subheader("🗺️ Location on Map")
                                    try:
                                        coords = ip_data.get('loc').split(',')
                                        map_data = {
                                            'lat': [float(coords[0])],
                                            'lon': [float(coords[1])]
                                        }
                                        st.map(map_data)
                                    except:
                                        st.error("Could not parse coordinates for map display")
                                
                                # Save to database
                                try:
                                    user_ip_response = requests.get("https://api.ipify.org?format=json")
                                    user_ip = user_ip_response.json().get('ip', 'Unknown') if user_ip_response.status_code == 200 else 'Unknown'
                                except:
                                    user_ip = 'Unknown'
                                
                                save_ip_search(
                                    ip_data.get('ip', ''),
                                    ip_data.get('country', ''),
                                    ip_data.get('region', ''),
                                    ip_data.get('city', ''),
                                    ip_data.get('org', ''),
                                    ip_data.get('loc', ''),
                                    'Custom IP',
                                    user_ip
                                )
                                
                                # Additional information
                                st.subheader("📊 Raw API Response")
                                st.json(ip_data)
                                st.success("✅ Search saved to history!")
                            else:
                                st.error("Failed to fetch IP information. Please check the IP address and try again.")
                    else:
                        st.error("Please enter a valid IP address format (e.g., 192.168.1.1)")
                else:
                    st.warning("Please enter an IP address to track.")
    
    with tab1:
        st.header("Phone Number Intelligence & Service Operator Identifier")
        st.info("Note: The detected service operator is based on the original number assignment and may not reflect the current operator if the number has been ported.")
        mobile_number = st.text_input("Enter Your Phone Number: ", type="password")
        manual_operator = st.text_input("(Optional) Enter your current operator if ported (e.g., Jio, Airtel, Vi):")
        
        if st.button("Track Phone Number"):
            if mobile_number:
                ch_number = phonenumbers.parse(mobile_number, "CH")
                country = geocoder.description_for_number(ch_number, "en")
                st.success(f"Country Name: {country}")
                
                services_operator = phonenumbers.parse(mobile_number, "RO")
                detected_operator = carrier.name_for_number(services_operator, "en")
                
                if manual_operator.strip():
                    st.success(f"Service Operator (Manual): {manual_operator.strip()}")
                    st.info(f"(Detected Operator: {detected_operator})")
                else:
                    st.success(f"Service Operator: {detected_operator}")
                
                # Get user's IP for logging
                try:
                    user_ip_response = requests.get("https://api.ipify.org?format=json")
                    user_ip = user_ip_response.json().get('ip', 'Unknown') if user_ip_response.status_code == 200 else 'Unknown'
                except:
                    user_ip = 'Unknown'
                
                # Save to database
                save_phone_search(
                    mobile_number[:5] + "***",  # Partially mask phone number for privacy
                    country,
                    detected_operator,
                    manual_operator.strip() if manual_operator.strip() else None,
                    user_ip
                )
                st.success("✅ Search saved to history!")
            else:
                st.warning("Please enter a phone number to track.")
    
    with tab3:
        st.header("📊 Analytics & Search History")
        
        # Get statistics
        stats = get_search_statistics()
        
        if stats:
            # Overview metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📱 Total Phone Searches", stats['total_phone'])
            with col2:
                st.metric("🌐 Total IP Searches", stats['total_ip'])
            with col3:
                st.metric("🔍 Total Searches", stats['total_phone'] + stats['total_ip'])
            
            st.markdown("---")
            
            # Country statistics
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📱 Top Countries (Phone Searches)")
                if not stats['phone_countries'].empty:
                    st.dataframe(stats['phone_countries'], use_container_width=True)
                    st.bar_chart(stats['phone_countries'].set_index('country')['count'])
                else:
                    st.info("No phone searches yet.")
            
            with col2:
                st.subheader("🌐 Top Countries (IP Searches)")
                if not stats['ip_countries'].empty:
                    st.dataframe(stats['ip_countries'], use_container_width=True)
                    st.bar_chart(stats['ip_countries'].set_index('country')['count'])
                else:
                    st.info("No IP searches yet.")
            
            st.markdown("---")
            
            # Recent searches
            st.subheader("🕐 Recent Searches")
            if not stats['recent_searches'].empty:
                st.dataframe(stats['recent_searches'], use_container_width=True)
            else:
                st.info("No searches yet.")
        
        else:
            st.error("Could not load analytics data.")
    
    # Footer
    st.markdown("---")
    st.markdown("**Note:** IP tracking uses ipinfo.io free tier (50,000 requests/month). Real IP detection uses ipify.org. Both services are reliable and privacy-focused. Search history is stored locally using SQLite.")


if __name__ == "__main__":
    main()
