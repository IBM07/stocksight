import streamlit as st
import requests
import pandas as pd

# --- Page Configuration ---
st.set_page_config(
    page_title="Stock Data Intelligence",
    page_icon="🚀",
    layout="wide"
)

# --- API Base URL ---
API_URL = "https://stocksight-imzd.onrender.com/"

# --- Helper Function to Fetch Data ---
@st.cache_data(ttl=600) # Cache data for 10 minutes
def get_api_data(endpoint):
    try:
        response = requests.get(f"{API_URL}/{endpoint}")
        response.raise_for_status() # Raise an exception for bad responses
        return response.json()
    except requests.exceptions.ConnectionError:
        return {"error": "ConnectionError", "detail": "Failed to connect to the API. Is it running?"}
    except Exception as e:
        return {"error": str(e)}

# --- Sidebar ---
st.sidebar.title("JarNox Intelligence")
page = st.sidebar.radio("Navigate", ["Stock Analyzer", "Stock Comparator"])

company_data = get_api_data("companies")

if "error" in company_data:
    st.error(company_data["detail"])
else:
    # Create a mapping of company names to symbols
    company_map = {company['name']: company['symbol'] for company in company_data}
    
    # --- Main Page: Stock Analyzer ---
    if page == "Stock Analyzer":
        st.title("Stock Analyzer")
        
        selected_name = st.sidebar.selectbox("Select a Company", options=company_map.keys())
        selected_symbol = company_map[selected_name]

        if selected_symbol:
            # --- Load Data ---
            data = get_api_data(f"data/{selected_symbol}")
            summary = get_api_data(f"summary/{selected_symbol}")
            
            if "error" in data or "error" in summary:
                st.error("Failed to fetch data for the selected symbol.")
            else:
                # --- Display Metrics ---
                st.header(f"{selected_name} ({selected_symbol})")
                col1, col2, col3 = st.columns(3)
                col1.metric("52-Week High", f"₹{summary['52_week_high']:.2f}")
                col2.metric("52-Week Low", f"₹{summary['52_week_low']:.2f}")
                col3.metric("52-Week Avg. Close", f"₹{summary['52_week_avg_close']:.2f}")

                # --- Create DataFrame ---
                df = pd.DataFrame(data)
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                
                # --- Display Charts ---
                st.subheader("Closing Price (Last 30 Days)")
                st.line_chart(df['close'])
                
                st.subheader("Volatility (30-Day)")
                st.line_chart(df['volatility_30d'])

                st.subheader("Raw Data (Last 30 Days)")
                st.dataframe(df)

    # --- Comparison Page ---
    elif page == "Stock Comparator":
        st.title("Stock Comparator")
        
        col1, col2 = st.columns(2)
        name1 = col1.selectbox("Select Company 1", options=company_map.keys(), index=0)
        name2 = col2.selectbox("Select Company 2", options=company_map.keys(), index=1)
        
        symbol1 = company_map[name1]
        symbol2 = company_map[name2]

        if st.button("Compare"):
            compare_data = get_api_data(f"compare?symbol1={symbol1}&symbol2={symbol2}")
            
            if "error" in compare_data:
                st.error("Failed to fetch comparison data.")
            else:
                st.header(f"Comparing {name1} vs. {name2}")

                # --- Process data for charting ---
                try:
                    # --- CORRECTED CODE ---
                    df1 = pd.DataFrame(compare_data[symbol1])
                    df2 = pd.DataFrame(compare_data[symbol2])
                    
                    df1['date'] = pd.to_datetime(df1['dates'])
                    df1.set_index('date', inplace=True)
                    
                    df2['date'] = pd.to_datetime(df2['dates'])
                    df2.set_index('date', inplace=True)

                    # --- Combine and rename columns ---
                    chart_df = pd.concat([df1['closes'], df2['closes']], axis=1)
                    chart_df.columns = [name1, name2]
                    
                    st.subheader("Closing Prices (Last 90 Days)")
                    st.line_chart(chart_df)
                except Exception as e:
                    st.error(f"Error processing data for charting: {e}")
                    st.json(compare_data)
