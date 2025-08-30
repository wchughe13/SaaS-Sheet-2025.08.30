import streamlit as st
import pandas as pd
import numpy as np
from visualizations import ARRVisualizer

# Page configuration
st.set_page_config(
    page_title="ARR Forecast Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_sample_data():
    """Load sample forecast data - replace with your actual data loading logic"""
    
    # Sample quarterly data (5 years = 20 quarters)
    quarters = pd.date_range(start='2024-01-01', periods=20, freq='Q')
    
    # Sample data - replace with your actual forecasting logic
    np.random.seed(42)
    base_arr = 1000000
    growth_rate = 0.15
    
    quarterly_data = []
    for i, quarter in enumerate(quarters):
        arr = base_arr * (1 + growth_rate) ** (i / 4)
        new_logo = arr * 0.3 * (1 + np.random.normal(0, 0.1))
        expansion = arr * 0.2 * (1 + np.random.normal(0, 0.1))
        churn = -arr * 0.05 * (1 + np.random.normal(0, 0.1))
        
        quarterly_data.append({
            'Date': quarter,
            'Ending ARR': arr,
            'New Logo Bookings': new_logo,
            'Expansion Bookings': expansion,
            'Churn & Downsell': churn,
            'Gross Retention': 0.95 + np.random.normal(0, 0.02),
            'Net Retention': 1.10 + np.random.normal(0, 0.05)
        })
    
    quarterly_df = pd.DataFrame(quarterly_data)
    
    # Sample annual data
    annual_data = []
    for year in range(6):
        if year == 0:
            annual_data.append({
                'Year': year,
                'Ending ARR': base_arr,
                'New Logo Bookings': 0,
                'Expansion Bookings': 0,
                'Churn & Downsell': 0
            })
        else:
            year_quarters = quarterly_df[quarterly_df['Date'].dt.year == 2024 + year - 1]
            annual_data.append({
                'Year': year,
                'Ending ARR': year_quarters['Ending ARR'].iloc[-1] if len(year_quarters) > 0 else base_arr * (1 + growth_rate) ** year,
                'New Logo Bookings': year_quarters['New Logo Bookings'].sum() if len(year_quarters) > 0 else base_arr * 0.3,
                'Expansion Bookings': year_quarters['Expansion Bookings'].sum() if len(year_quarters) > 0 else base_arr * 0.2,
                'Churn & Downsell': year_quarters['Churn & Downsell'].sum() if len(year_quarters) > 0 else -base_arr * 0.05
            })
    
    annual_df = pd.DataFrame(annual_data)
    
    return {
        'quarterly': quarterly_df,
        'annual': annual_df
    }

def main():
    """Main Streamlit application"""
    
    # Header
    st.markdown('<h1 class="main-header">📊 ARR Forecast Dashboard</h1>', unsafe_allow_html=True)
    
    # Load data
    try:
        forecast_data = load_sample_data()
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        st.stop()
    
    # Initialize visualizer
    visualizer = ARRVisualizer()
    
    # Sidebar controls
    st.sidebar.header("Dashboard Controls")
    
    # Chart selection
    chart_type = st.sidebar.selectbox(
        "Select Chart Type",
        ["ARR Forecast", "Growth Rate", "Waterfall Analysis", "Bookings Breakdown", "Retention Analysis", "All Charts"]
    )
    
    # Display selected chart(s)
    if chart_type == "ARR Forecast" or chart_type == "All Charts":
        st.subheader("📈 5-Year ARR Forecast")
        arr_chart = visualizer.create_arr_chart(forecast_data)
        st.plotly_chart(arr_chart, use_container_width=True)
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            current_arr = forecast_data['quarterly']['Ending ARR'].iloc[-1]
            st.metric("Current ARR", f"${current_arr:,.0f}")
        
        with col2:
            final_arr = forecast_data['quarterly']['Ending ARR'].iloc[-1]
            initial_arr = forecast_data['quarterly']['Ending ARR'].iloc[0]
            total_growth = ((final_arr - initial_arr) / initial_arr) * 100
            st.metric("Total Growth", f"{total_growth:.1f}%")
        
        with col3:
            quarterly_growth = forecast_data['quarterly']['Ending ARR'].pct_change().iloc[-1] * 100
            st.metric("QoQ Growth", f"{quarterly_growth:.1f}%")
        
        with col4:
            yoy_growth = forecast_data['quarterly']['Ending ARR'].pct_change(periods=4).iloc[-1] * 100
            st.metric("YoY Growth", f"{yoy_growth:.1f}%")
    
    if chart_type == "Growth Rate" or chart_type == "All Charts":
        st.subheader("📊 Year-over-Year Growth Rate")
        growth_chart = visualizer.create_growth_rate_chart(forecast_data)
        st.plotly_chart(growth_chart, use_container_width=True)
    
    if chart_type == "Waterfall Analysis" or chart_type == "All Charts":
        st.subheader("🌊 Annual ARR Waterfall Analysis")
        waterfall_chart = visualizer.create_waterfall_chart(forecast_data)
        st.plotly_chart(waterfall_chart, use_container_width=True)
    
    if chart_type == "Bookings Breakdown" or chart_type == "All Charts":
        st.subheader("💰 Quarterly Bookings Breakdown")
        bookings_chart = visualizer.create_bookings_chart(forecast_data)
        st.plotly_chart(bookings_chart, use_container_width=True)
    
    if chart_type == "Retention Analysis" or chart_type == "All Charts":
        st.subheader("🔄 Retention Rate Analysis")
        retention_chart = visualizer.create_retention_chart(forecast_data)
        st.plotly_chart(retention_chart, use_container_width=True)
    
    # Footer
    st.markdown("---")
    st.markdown("**Note**: This dashboard uses sample data. Replace the `load_sample_data()` function with your actual data loading logic.")

if __name__ == "__main__":
    main()
