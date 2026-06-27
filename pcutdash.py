import streamlit as st
import pandas as pd
import plotly.express as px
import sys
from streamlit.web import cli as stcli

# --- UI CONFIGURATION ---
st.set_page_config(page_title="School Print Analysis Dashboard", layout="wide")

# Custom CSS targeting specific internal Streamlit wrapper labels and values
st.markdown("""
    <style>
    /* Scope primary widget labels and markdown headers for white visibility */
    div[data-testid="stWidgetLabel"] p, 
    div[data-testid="stMarkdownContainer"] p,
    .stSelectbox label p, 
    .stTextInput label p,
    .stFileUploader label p,
    div[data-baseweb="select"] div {
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }
    
    /* Headings, subheadings, and key performance numeric text */
    h1, h2, h3, h4, h5, h6, 
    [data-testid="stMetricLabel"], 
    [data-testid="stMetricValue"] {
        color: #FFFFFF !important;
        font-weight: 800 !important;
    }
    
    /* Tab label header text configuration */
    button[data-baseweb="tab"] p {
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }
    
    /* Retain clean contrast inside raw data tables */
    .stDataFrame div, table, td, th, [data-testid="stTable"] td {
        color: #000000 !important;
        font-weight: 500 !important;
    }
    
    .stButton>button, .stDownloadButton>button {
        border-radius: 20px;
        background-color: #1A5276 !important;
        color: white !important;
        padding: 10px 24px;
        font-weight: 700 !important;
        border: 1px solid #ffffff !important;
    }
    
    .metadata-box {
        background-color: #2C3E50;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #1A5276;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CORE LOGIC ---
def process_csv(df):
    processed = df.groupby(['Full Name', 'Username']).agg({
        'Color Pages': 'sum',
        'Grayscale Pages': 'sum',
        'Total Printed Pages': 'sum',
        'Duplex Pages': 'sum',
        'Simplex Pages': 'sum',
        'Cost': 'sum'
    }).reset_index()
    
    processed['Color_Ratio'] = (processed['Color Pages'] / processed['Total Printed Pages'] * 100).fillna(0).round(2)
    processed['Duplex_Ratio'] = (processed['Duplex Pages'] / processed['Total Printed Pages'] * 100).fillna(0).round(2)
    return processed

# --- MAIN DASHBOARD INTERFACE ---
def build_dashboard():
    st.title("🖨️ Monthly School Print & Copy Analysis")

    tab1, tab2 = st.tabs(["📥 Import", "📊 Analysis"])

    # 1. IMPORT SECTION
    with tab1:
        st.header("Import School Site CSVs")
        uploaded_files = st.file_uploader("Upload PaperCut CSV files", accept_multiple_files=True, type=['csv'])
        
        if uploaded_files:
            st.session_state['data_frames'] = {}
            st.session_state['first_lines'] = {}
            
            for file in uploaded_files:
                try:
                    first_line_bytes = file.readline()
                    first_line_str = first_line_bytes.decode('utf-8', errors='ignore').strip()
                except Exception:
                    first_line_str = "Unknown Header Reference"
                
                file.seek(0)
                df = pd.read_csv(file, skiprows=2) 
                
                school_name = file.name.split('.')[0]
                st.session_state['data_frames'][school_name] = df
                st.session_state['first_lines'][school_name] = first_line_str
                
            st.success(f"Successfully imported {len(uploaded_files)} school files.")

    # 2. ANALYSIS SECTION
    with tab2:
        st.header("Analysis Dashboard")
        if 'data_frames' in st.session_state and st.session_state['data_frames']:
            selected_school = st.selectbox("Select School to Visualize", options=list(st.session_state['data_frames'].keys()))
            
            if selected_school:
                # Display the source metadata matching the selected data file
                captured_first_line = st.session_state['first_lines'].get(selected_school, "N/A")
                st.markdown(
                    f"""
                    <div class="metadata-box">
                        <span style="color: #BDC3C7; font-size: 14px;">CSV Source Information:</span><br>
                        <code style="color: #E74C3C; font-size: 15px; font-weight: bold;">{captured_first_line}</code>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
                
                raw_data = st.session_state['data_frames'][selected_school]
                analysis_data = process_csv(raw_data)
                
                total_vol = analysis_data['Total Printed Pages'].sum()
                gray_vol = analysis_data['Grayscale Pages'].sum()
                color_vol = analysis_data['Color Pages'].sum()
                duplex_vol = analysis_data['Duplex Pages'].sum()
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Volume", f"{total_vol:,}")
                col2.metric("Grayscale Usage", f"{gray_vol:,}")
                col3.metric("Color Usage", f"{color_vol:,}")

                # Graph 1: Top 20 users by volume
                st.subheader("Top 20 High-Volume Users")
                top_20_vol = analysis_data.nlargest(20, 'Total Printed Pages')
                fig_users = px.bar(top_20_vol, x='Full Name', y='Total Printed Pages', color='Color Pages',
                                   title="Total Pages by Top Users (Color indicated by shade)",
                                   labels={'Total Printed Pages': 'Total Pages', 'Full Name': 'Staff Member'})
                fig_users.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_users, use_container_width=True)

                # Graph 2: Top 20 users by total cost
                st.subheader("Top 20 Highest Fiscal Impact Users")
                top_20_cost = analysis_data.nlargest(20, 'Cost')
                fig_cost = px.bar(top_20_cost, x='Cost', y='Full Name', orientation='h',
                                  title="Total Cost Accumulation per User ($)",
                                  color='Cost', color_continuous_scale='Reds',
                                  labels={'Cost': 'Total Cost ($)', 'Full Name': 'Staff Member'})
                fig_cost.update_layout(yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig_cost, use_container_width=True)

                st.subheader("Sustainability & Ratio Analysis")
                ratio_col1, ratio_col2 = st.columns(2)
                
                fig_ratio = px.pie(values=[gray_vol, color_vol], names=['Grayscale', 'Color'], title="Grayscale vs Color Ratio")
                ratio_col1.plotly_chart(fig_ratio, use_container_width=True)
                
                fig_duplex = px.pie(values=[duplex_vol, analysis_data['Simplex Pages'].sum()], 
                                    names=['Duplex', 'Simplex'], title="Duplex vs Simplex Usage")
                ratio_col2.plotly_chart(fig_duplex, use_container_width=True)
                
                st.subheader("Complete Staff Usage Data")
                st.dataframe(analysis_data, use_container_width=True)
        else:
            st.info("Please import school files first in the Import tab.")

# --- ENGINE EXECUTION MATRIX ---
if __name__ == '__main__':
    if st.runtime.exists():
        build_dashboard()
    else:
        sys.argv = ["streamlit", "run", sys.argv[0], "--global.developmentMode=false"]
        sys.exit(stcli.main())