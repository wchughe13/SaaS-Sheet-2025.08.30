import pandas as pd
import io
from datetime import datetime

def validate_inputs(assumptions):
    """Validate user inputs and return list of errors"""
    errors = []
    
    # Validate current ARR
    if assumptions['current_arr'] <= 0:
        errors.append("Current ARR must be greater than 0")
    
    # Validate growth rates
    for year, rate in assumptions['growth_rates'].items():
        if rate < 0:
            errors.append(f"{year} growth rate cannot be negative")
        if rate > 1000:  # Reasonable upper bound
            errors.append(f"{year} growth rate seems unreasonably high (>{rate}%)")
    
    # Validate gross retention
    if not (0 <= assumptions['gross_retention'] <= 1):
        errors.append("Gross retention rate must be between 0% and 100%")
    
    # Validate business split for each year
    for year, split in assumptions['new_business_split'].items():
        if not (0 <= split <= 1):
            errors.append(f"{year} new business split must be between 0% and 100%")
    
    # Validate seasonality
    total_seasonality = sum(assumptions['seasonality'].values())
    if abs(total_seasonality - 1.0) > 0.001:  # Allow for small floating point errors
        errors.append(f"Seasonality factors must sum to 100% (currently {total_seasonality*100:.1f}%)")
    
    # Validate individual seasonality factors
    for quarter, factor in assumptions['seasonality'].items():
        if not (0 <= factor <= 1):
            errors.append(f"{quarter} seasonality factor must be between 0% and 100%")
    
    return errors

def export_to_csv(forecast_data, assumptions):
    """Export complete forecast model to CSV format"""
    
    output = io.StringIO()
    
    # Write header information
    output.write("ARR Forecasting Tool - Export\n")
    output.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    output.write("\n")
    
    # Write assumptions
    output.write("ASSUMPTIONS\n")
    output.write(f"Current ARR,${assumptions['current_arr']:,.0f}\n")
    output.write(f"Current Date,{assumptions['current_date']}\n")
    output.write(f"Gross Retention Rate,{assumptions['gross_retention']*100:.0f}%\n")
    
    output.write("\nNew Business Split by Year\n")
    for year, split in assumptions['new_business_split'].items():
        output.write(f"{year},{split*100:.0f}%\n")
    
    output.write("\nGrowth Rates\n")
    for year, rate in assumptions['growth_rates'].items():
        output.write(f"{year},{rate}%\n")
    
    output.write("\nSeasonality Factors\n")
    for quarter, factor in assumptions['seasonality'].items():
        output.write(f"{quarter},{factor*100:.0f}%\n")
    
    output.write("\n")
    
    # Write annual forecast
    output.write("ANNUAL FORECAST\n")
    annual_df = forecast_data['annual'].copy()
    
    # Format currency columns
    currency_cols = ['Beginning ARR', 'New Logo Bookings', 'Expansion Bookings', 
                    'Churn & Downsell', 'Ending ARR']
    for col in currency_cols:
        if col in annual_df.columns:
            annual_df[col] = annual_df[col].apply(lambda x: f'${x:,.0f}')
    
    # Format percentage columns
    pct_cols = ['Gross Retention', 'Net Retention']
    for col in pct_cols:
        if col in annual_df.columns:
            annual_df[col] = annual_df[col].apply(lambda x: f'{x*100:.1f}%' if pd.notna(x) else '')
    
    output.write(annual_df.to_csv(index_label='Year'))
    output.write("\n")
    
    # Write quarterly forecast
    output.write("QUARTERLY FORECAST\n")
    quarterly_df = forecast_data['quarterly'].copy()
    
    # Format currency columns
    for col in currency_cols:
        if col in quarterly_df.columns:
            quarterly_df[col] = quarterly_df[col].apply(lambda x: f'${x:,.0f}')
    
    # Format percentage columns
    for col in pct_cols:
        if col in quarterly_df.columns:
            quarterly_df[col] = quarterly_df[col].apply(lambda x: f'{x*100:.1f}%' if pd.notna(x) else '')
    
    # Format date column
    if 'Date' in quarterly_df.columns:
        quarterly_df['Date'] = quarterly_df['Date'].dt.strftime('%Y-%m-%d')
    
    output.write(quarterly_df.to_csv(index=False))
    
    return output.getvalue()

def format_currency(value):
    """Format value as currency string"""
    if pd.isna(value):
        return ""
    return f"${value:,.0f}"

def format_percentage(value):
    """Format value as percentage string"""
    if pd.isna(value):
        return ""
    return f"{value*100:.1f}%"

def calculate_summary_metrics(forecast_data):
    """Calculate key summary metrics from forecast data"""
    
    annual_data = forecast_data['annual']
    quarterly_data = forecast_data['quarterly']
    
    metrics = {}
    
    # Revenue metrics
    metrics['total_new_logo'] = annual_data['New Logo Bookings'].sum()
    metrics['total_expansion'] = annual_data['Expansion Bookings'].sum()
    metrics['total_churn'] = abs(annual_data['Churn & Downsell'].sum())
    metrics['total_bookings'] = metrics['total_new_logo'] + metrics['total_expansion']
    
    # Retention metrics
    metrics['avg_gross_retention'] = quarterly_data['Gross Retention'].mean()
    metrics['avg_net_retention'] = quarterly_data['Net Retention'].mean()
    
    # Growth metrics
    starting_arr = annual_data.loc[0, 'Ending ARR']
    ending_arr = annual_data.loc[5, 'Ending ARR']
    metrics['total_growth'] = ending_arr - starting_arr
    metrics['growth_multiple'] = ending_arr / starting_arr if starting_arr > 0 else 0
    
    return metrics

def create_scenario_comparison(base_forecast, optimistic_assumptions, pessimistic_assumptions):
    """Create scenario comparison with optimistic and pessimistic cases"""
    # This function could be used for advanced scenario planning
    # Implementation would involve running calculations with different assumption sets
    pass

def validate_calculation_integrity(forecast_data):
    """Validate that all calculations are mathematically consistent"""
    
    errors = []
    
    # Check annual data integrity
    annual_data = forecast_data['annual']
    for year in range(1, 6):
        beginning = annual_data.loc[year, 'Beginning ARR']
        new_logo = annual_data.loc[year, 'New Logo Bookings']
        expansion = annual_data.loc[year, 'Expansion Bookings']
        churn = annual_data.loc[year, 'Churn & Downsell']
        ending = annual_data.loc[year, 'Ending ARR']
        
        calculated_ending = beginning + new_logo + expansion + churn
        
        if abs(calculated_ending - ending) > 0.01:  # Allow for small rounding errors
            errors.append(f"Year {year}: ARR calculation doesn't balance")
    
    # Check quarterly data integrity
    quarterly_data = forecast_data['quarterly']
    for idx in quarterly_data.index:
        beginning = quarterly_data.loc[idx, 'Beginning ARR']
        new_logo = quarterly_data.loc[idx, 'New Logo Bookings']
        expansion = quarterly_data.loc[idx, 'Expansion Bookings']
        churn = quarterly_data.loc[idx, 'Churn & Downsell']
        ending = quarterly_data.loc[idx, 'Ending ARR']
        
        calculated_ending = beginning + new_logo + expansion + churn
        
        if abs(calculated_ending - ending) > 0.01:
            errors.append(f"Quarter {idx}: ARR calculation doesn't balance")
    
    return errors
