import streamlit as st
import pandas as pd
from datetime import datetime, date
import io
from calculations import ARRCalculator
from visualizations import ARRVisualizer
from utils import validate_inputs, export_to_csv

# Configure page
st.set_page_config(
    page_title="SaaS Sheet",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    st.title("📊 SaaS Sheet - ARR Forecasting Tool")
    st.markdown("*Lightning-fast ARR forecasts for SaaS founders — no spreadsheets required*")
    st.markdown("Have feedback or suggestions? Need a more detailed financial model for your business? [Let me know!](https://linktr.ee/wchughe1)")
    
    # Initialize session state
    if 'calculator' not in st.session_state:
        st.session_state.calculator = ARRCalculator()
    if 'visualizer' not in st.session_state:
        st.session_state.visualizer = ARRVisualizer()
    
    # Sidebar for inputs
    st.sidebar.header("📊 SaaS Sheet")
    
    # Core assumptions
    st.sidebar.subheader("Key Assumptions ")
    current_arr = st.sidebar.number_input(
        "Expected Current Year End ARR ($)",
        min_value=0,
        value=1000,
        step=100,
        help="Expected ARR at the end of current year"
    )
    
    current_date = st.sidebar.date_input(
        "Current Date",
        value=date.today(),
        help="Reference date for calculations"
    )
    
    # Growth rates
    st.sidebar.subheader("ARR Growth Rates")
    growth_rates = {}
    growth_defaults = [100, 90, 80, 70, 60]
    for i in range(5):
        growth_rates[f'Y{i+1}'] = st.sidebar.number_input(
            f"Year {i+1} - ARR Growth Rate (%)",
            min_value=0,
            max_value=1000,
            value=growth_defaults[i],
            step=1,
            format="%d",
            help=f"Expected growth rate for year {i+1}"
        )
    
    # Retention rate
    st.sidebar.subheader("Gross Retention")
    gross_retention = st.sidebar.slider(
        "Gross Retention Rate (%)",
        min_value=50,
        max_value=100,
        value=90,
        step=1,
        help="Percentage of ARR retained from one year to the next (excluding impact from any new business)"
    )
    
    # New business vs existing split by year
    st.sidebar.subheader("Bookings Split - New Business vs Existing Customers")
    new_business_split = {}
    for i in range(5):
        new_business_split[f'Y{i+1}'] = st.sidebar.slider(
            f"Year {i+1} - New Business vs. Existing (%)",
            min_value=0,
            max_value=100,
            value=60,
            step=5,
            help=f"Percentage of bookings from new customer wins vs expansion with existing customers (i.e. upsell / cross-sell) for year {i+1}"
        )
    
    # Seasonality factors
    st.sidebar.subheader("Quarterly Seasonality")
    seasonality = {}
    seasonality['Q1'] = st.sidebar.number_input("Q1 (%)", min_value=0, max_value=100, value=20, step=1)
    seasonality['Q2'] = st.sidebar.number_input("Q2 (%)", min_value=0, max_value=100, value=25, step=1)
    seasonality['Q3'] = st.sidebar.number_input("Q3 (%)", min_value=0, max_value=100, value=25, step=1)
    seasonality['Q4'] = st.sidebar.number_input("Q4 (%)", min_value=0, max_value=100, value=30, step=1)
    
    # Validate seasonality
    total_seasonality = sum(seasonality.values())
    if total_seasonality != 100:
        st.sidebar.error(f"Seasonality factors must sum to 100%. Current total: {total_seasonality}%")
        return
    
    # Reset button
    if st.sidebar.button("Reset to Defaults"):
        st.rerun()
    
    # Compile assumptions
    assumptions = {
        'current_arr': current_arr,
        'current_date': current_date,
        'growth_rates': growth_rates,
        'gross_retention': gross_retention / 100,  # Convert to decimal
        'new_business_split': {k: v/100 for k, v in new_business_split.items()},  # Convert to decimal
        'seasonality': {k: v/100 for k, v in seasonality.items()}  # Convert to decimal
    }
    
    # Validate inputs
    validation_errors = validate_inputs(assumptions)
    if validation_errors:
        st.error("Please fix the following issues:")
        for error in validation_errors:
            st.error(f"• {error}")
        return
    
    # Calculate forecasts
    try:
        forecast_data = st.session_state.calculator.calculate_forecast(assumptions)
        
        # Main dashboard
        col1, col2, col3, col4 = st.columns(4)
        
        # Key metrics cards
        with col1:
            st.metric(
                "Current ARR",
                f"${current_arr:,.0f}",
                help="Starting ARR value"
            )
        
        with col2:
            year_5_arr = forecast_data['annual']['Ending ARR'].iloc[-1]
            st.metric(
                "Year 5 ARR",
                f"${year_5_arr:,.0f}",
                help="Projected ARR at end of year 5"
            )
        
        with col3:
            arr_cagr = st.session_state.calculator.calculate_cagr(current_arr, year_5_arr, 5)
            st.metric(
                "5-Year ARR CAGR",
                f"{arr_cagr:.1f}%",
                help="Compound Annual Growth Rate for ARR"
            )
        
        with col4:
            total_bookings = forecast_data['annual']['New Logo Bookings'].sum() + forecast_data['annual']['Expansion Bookings'].sum()
            bookings_cagr = st.session_state.calculator.calculate_bookings_cagr(forecast_data)
            st.metric(
                "5-Year Bookings CAGR",
                f"{bookings_cagr:.1f}%",
                help="Compound Annual Growth Rate for total bookings"
            )
        
        # Main visualizations
        st.header("ARR Forecast Dashboard")
        
        # Primary ARR chart
        arr_chart = st.session_state.visualizer.create_arr_chart(forecast_data)
        st.plotly_chart(arr_chart, use_container_width=True)
        
        # YoY Growth Rate chart
        growth_chart = st.session_state.visualizer.create_growth_rate_chart(forecast_data)
        st.plotly_chart(growth_chart, use_container_width=True)
        
        # Additional charts arranged vertically
        st.subheader("Annual ARR Waterfall")
        waterfall_chart = st.session_state.visualizer.create_waterfall_chart(forecast_data)
        st.plotly_chart(waterfall_chart, use_container_width=True)
        
        st.subheader("Quarterly Bookings Breakdown")
        bookings_chart = st.session_state.visualizer.create_bookings_chart(forecast_data)
        st.plotly_chart(bookings_chart, use_container_width=True)
        
        # Retention analytics
        st.subheader("Retention Analytics")
        retention_chart = st.session_state.visualizer.create_retention_chart(forecast_data)
        st.plotly_chart(retention_chart, use_container_width=True)
        
        # Summary metrics
        st.header("📋 Summary Metrics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("Revenue Metrics")
            avg_net_retention = forecast_data['quarterly']['Net Retention'].mean() * 100
            st.write(f"**Average Net Retention:** {avg_net_retention:.1f}%")
            st.write(f"**Total New Logo Bookings (5Y):** ${forecast_data['annual']['New Logo Bookings'].sum():,.0f}")
            st.write(f"**Total Expansion Bookings (5Y):** ${forecast_data['annual']['Expansion Bookings'].sum():,.0f}")
        
        with col2:
            st.subheader("Churn Analysis")
            total_churn = abs(forecast_data['annual']['Churn & Downsell'].sum())
            st.write(f"**Total ARR Lost to Churn (5Y):** ${total_churn:,.0f}")
            avg_gross_retention = forecast_data['quarterly']['Gross Retention'].mean() * 100
            st.write(f"**Average Gross Retention:** {avg_gross_retention:.1f}%")
        
        with col3:
            st.subheader("Growth Analysis")
            st.write(f"**Total ARR Growth (5Y):** ${year_5_arr - current_arr:,.0f}")
            growth_multiple = year_5_arr / current_arr
            st.write(f"**5-Year Growth Multiple:** {growth_multiple:.1f}x")
        
        # Export functionality
        st.header("📥 Export Data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # CSV export
            csv_data = export_to_csv(forecast_data, assumptions)
            st.download_button(
                label="Download Forecast CSV",
                data=csv_data,
                file_name=f"arr_forecast_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                help="Download complete forecast model with all calculations"
            )
        
        with col2:
            # Summary export
            summary_data = st.session_state.calculator.create_summary_export(forecast_data, assumptions)
            st.download_button(
                label="Download Executive Summary",
                data=summary_data,
                file_name=f"arr_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                help="Download key metrics and assumptions summary"
            )
        
        # Show detailed tables (expandable)
        with st.expander("📊 View Detailed Forecast Tables"):
            st.subheader("Annual Forecast")
            st.dataframe(forecast_data['annual'])
            
            st.subheader("Quarterly Forecast")
            st.dataframe(forecast_data['quarterly'])
    
    except Exception as e:
        st.error(f"An error occurred during calculations: {str(e)}")
        st.error("Please check your inputs and try again.")

if __name__ == "__main__":
    main()
