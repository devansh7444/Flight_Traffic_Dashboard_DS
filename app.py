import streamlit as st
import pandas as pd
import altair as alt
import os

# --- Configuration ---
st.set_page_config(
    page_title="Air Traffic Analysis Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Define the data file path ---
DATA_FILE = "22070521076_CA1_EDA.csv"

# --- Data Loading and Preparation (Cached) ---
# Removed the problematic 'suppress_st_warning=True' argument
@st.cache_data 
def load_data(file_path):
    """Loads the data and performs initial cleaning and calculation."""
    
    if not os.path.exists(file_path):
         # This error message is essential for debugging file access in deployment
         st.error(f"FATAL ERROR: Data file not found at: {file_path}. Please ensure it is uploaded.")
         return pd.DataFrame()

    df = pd.read_csv(file_path)

    # 1. Calculate Total Freight and Create Route Column
    df['TOTAL FREIGHT'] = df['FREIGHT TO CITY 2'] + df['FREIGHT FROM CITY 2']
    df['Route'] = df['CITY 1'] + ' - ' + df['CITY 2']

    # 2. Robust Data Type Conversion for Passenger Columns
    int_cols = ['PASSENGERS TO CITY 2', 'PASSENGERS FROM CITY 2', 'TOTAL PASSENGERS']
    
    for col in int_cols:
         # Convert to numeric, coercing any bad/non-numeric values to NaN
         df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Convert to the nullable integer type ('Int64') for clean display
    df[int_cols] = df[int_cols].astype('Int64')
    
    return df

# --- Main App Execution ---
df = load_data(DATA_FILE)

if not df.empty:
    
    # --- Title and Summary Metrics ---
    st.title("✈️ Government Open Dataset: Air Traffic Analysis Dashboard")
    st.markdown("Interactive visual reports for air traffic route decision-making.")
    st.markdown("---")

    # Display Summary Metrics in Columns
    col1, col2, col3 = st.columns(3)

    total_passengers_sum = df['TOTAL PASSENGERS'].sum()
    total_freight_sum = df['TOTAL FREIGHT'].sum()
    total_routes = len(df)

    col1.metric("Total Passengers (Across all Routes)", f"{total_passengers_sum:,.0f}")
    col2.metric("Total Freight (Tons)", f"{total_freight_sum:,.1f}")
    col3.metric("Number of Unique Routes Analyzed", f"{total_routes:,}")

    st.markdown("---")

    # --- Dashboard Visualizations ---

    # 1. Top N Busiest Routes by Total Passengers
    st.header("1. Top N Busiest Air Routes by Total Passengers")
    st.write("Use the slider to focus on the busiest routes, aiding capacity planning.")

    # Filter out potential NaN passenger routes before sorting
    df_clean = df.dropna(subset=['TOTAL PASSENGERS'])
    top_n = st.slider("Select Top N Routes to Display:", 5, min(50, len(df_clean)), 20)
    top_routes_df = df_clean.sort_values(by='TOTAL PASSENGERS', ascending=False).head(top_n)

    chart1 = alt.Chart(top_routes_df).mark_bar().encode(
        x=alt.X('TOTAL PASSENGERS', title='Total Passengers', axis=alt.Axis(format='~s')),
        y=alt.Y('Route', sort='-x', title='Route'),
        tooltip=[
            alt.Tooltip('Route', title='City Pair'),
            alt.Tooltip('TOTAL PASSENGERS', title='Total Passengers', format=',')],
        color=alt.Color('TOTAL PASSENGERS', scale=alt.Scale(range='ramp'), legend=None)
    ).properties(
        height=500
    ).interactive() # Enables zoom and pan

    st.altair_chart(chart1, use_container_width=True)

    st.markdown("---")

    # 2. Passenger Traffic vs. Freight Traffic per Route (Interactive for Decision-Making)
    st.header("2. Passenger Traffic vs. Freight Traffic per Route")
    st.write("Use the slider to highlight high-volume passenger routes for strategic comparison with freight.")

    # Slider allows users to interactively set the threshold for 'High Volume'
    threshold = st.slider("Set Passenger Threshold for High Volume (in thousands):",
                          10, 500, 250, step=10) * 1000

    chart2 = alt.Chart(df).mark_circle(size=60).encode(
        x=alt.X('TOTAL PASSENGERS', title='Total Passengers', axis=alt.Axis(format='~s')),
        y=alt.Y('TOTAL FREIGHT', title='Total Freight (Tons)', axis=alt.Axis(format='~s')),
        tooltip=[
            alt.Tooltip('Route', title='City Pair'),
            alt.Tooltip('TOTAL PASSENGERS', title='Total Passengers', format=','),
            alt.Tooltip('TOTAL FREIGHT', title='Total Freight (Tons)', format=',.1f')
        ],
        color=alt.condition(
            alt.datum['TOTAL PASSENGERS'] >= threshold, # Conditional highlight
            alt.value('red'),
            alt.value('steelblue'),
            legend=alt.Legend(title='Passenger Volume',
                              labelExpr=f"datum.value == 'red' ? 'High Volume (≥ {threshold/1000:,.0f}k)' : 'Low Volume (< {threshold/1000:,.0f}k)'")
        )
    ).properties(
        height=400
    ).interactive() # Enables zoom and pan

    st.altair_chart(chart2, use_container_width=True)
    
    # Optional: Show the raw data in an expander
    with st.expander("View Raw Data"):
        st.dataframe(df)