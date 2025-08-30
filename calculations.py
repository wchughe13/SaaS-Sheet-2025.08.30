import pandas as pd
import numpy as np
import io
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class ARRCalculator:
    def __init__(self):
        self.quarterly_data = None
        self.annual_data = None
    
    def calculate_forecast(self, assumptions):
        """Main calculation engine for ARR forecasting"""
        
        # Extract assumptions
        current_arr = assumptions['current_arr']
        current_date = assumptions['current_date']
        growth_rates = assumptions['growth_rates']
        gross_retention = assumptions['gross_retention']
        new_business_split = assumptions['new_business_split']
        seasonality = assumptions['seasonality']
        
        # Create date structure (5 years, quarterly)
        dates = self._create_date_structure(current_date)
        
        # Calculate annual targets first
        annual_data = self._calculate_annual_forecast(
            current_arr, growth_rates, gross_retention, new_business_split
        )
        
        # Calculate quarterly breakdown
        quarterly_data = self._calculate_quarterly_forecast(
            annual_data, seasonality, gross_retention
        )
        
        # Add dates to quarterly data
        quarterly_data['Date'] = dates
        quarterly_data['Year'] = quarterly_data['Date'].dt.year
        quarterly_data['Quarter'] = quarterly_data['Date'].dt.quarter
        
        # Store for later use
        self.annual_data = annual_data
        self.quarterly_data = quarterly_data
        
        return {
            'annual': annual_data,
            'quarterly': quarterly_data,
            'assumptions': assumptions
        }
    
    def _create_date_structure(self, current_date):
        """Create quarterly date structure for 5 years"""
        dates = []
        base_year = current_date.year + 1  # Start from next year after current date
        
        for year in range(5):  # 5 years of forecast
            forecast_year = base_year + year
            for quarter in range(1, 5):
                if quarter == 1:
                    date = datetime(forecast_year, 3, 31)
                elif quarter == 2:
                    date = datetime(forecast_year, 6, 30)
                elif quarter == 3:
                    date = datetime(forecast_year, 9, 30)
                else:  # quarter == 4
                    date = datetime(forecast_year, 12, 31)
                dates.append(date)
        
        return pd.to_datetime(dates)
    
    def _calculate_annual_forecast(self, current_arr, growth_rates, gross_retention, new_business_split):
        """Calculate annual ARR waterfall components"""
        
        annual_data = pd.DataFrame(index=range(6))  # Year 0 through Year 5
        annual_data.index.name = 'Year'
        
        # Initialize columns with float dtype
        annual_data['Beginning ARR'] = 0.0
        annual_data['New Logo Bookings'] = 0.0
        annual_data['Expansion Bookings'] = 0.0
        annual_data['Churn & Downsell'] = 0.0
        annual_data['Ending ARR'] = 0.0
        annual_data.loc[0, 'Beginning ARR'] = float(current_arr)
        
        for year in range(1, 6):
            # Beginning ARR is previous year's ending ARR
            annual_data.loc[year, 'Beginning ARR'] = annual_data.loc[year-1, 'Ending ARR'] if year > 1 else current_arr
            
            # Calculate total bookings needed for growth
            target_growth_rate = growth_rates[f'Y{year}'] / 100
            beginning_arr = annual_data.loc[year, 'Beginning ARR']
            target_ending_arr = beginning_arr * (1 + target_growth_rate)
            
            # Calculate churn first (based on beginning ARR)
            churn_amount = beginning_arr * (1 - gross_retention)
            annual_data.loc[year, 'Churn & Downsell'] = -churn_amount
            
            # Calculate total bookings needed
            total_bookings_needed = target_ending_arr - beginning_arr + churn_amount
            
            # Split between new logo and expansion (year-specific)
            year_business_split = new_business_split[f'Y{year}']
            new_logo_bookings = total_bookings_needed * year_business_split
            expansion_bookings = total_bookings_needed * (1 - year_business_split)
            
            annual_data.loc[year, 'New Logo Bookings'] = new_logo_bookings
            annual_data.loc[year, 'Expansion Bookings'] = expansion_bookings
            
            # Calculate ending ARR
            ending_arr = (beginning_arr + new_logo_bookings + expansion_bookings - churn_amount)
            annual_data.loc[year, 'Ending ARR'] = ending_arr
        
        # Year 0 only has ending ARR
        annual_data.loc[0, 'New Logo Bookings'] = 0
        annual_data.loc[0, 'Expansion Bookings'] = 0
        annual_data.loc[0, 'Churn & Downsell'] = 0
        annual_data.loc[0, 'Ending ARR'] = current_arr
        
        # Calculate check column (should be 0 for all years)
        annual_data['Check'] = (
            annual_data['Beginning ARR'] + 
            annual_data['New Logo Bookings'] + 
            annual_data['Expansion Bookings'] + 
            annual_data['Churn & Downsell'] - 
            annual_data['Ending ARR']
        )
        
        # Calculate retention metrics
        annual_data['Gross Retention'] = gross_retention
        annual_data['Net Retention'] = np.where(
            annual_data['Beginning ARR'] > 0,
            (annual_data['Beginning ARR'] + annual_data['Expansion Bookings'] + annual_data['Churn & Downsell']) / annual_data['Beginning ARR'],
            np.nan
        )
        
        return annual_data
    
    def _calculate_quarterly_forecast(self, annual_data, seasonality, gross_retention):
        """Break down annual forecast into quarterly components"""
        
        quarterly_data = pd.DataFrame()
        
        # Convert seasonality to list for easier indexing
        seasonal_factors = [
            seasonality['Q1'], seasonality['Q2'], 
            seasonality['Q3'], seasonality['Q4']
        ]
        
        for year in range(1, 6):  # Years 1-5
            annual_new_logo = annual_data.loc[year, 'New Logo Bookings']
            annual_expansion = annual_data.loc[year, 'Expansion Bookings']
            
            for quarter in range(4):  # Q1-Q4
                quarterly_idx = (year - 1) * 4 + quarter
                
                # Apply seasonality to bookings
                quarterly_new_logo = annual_new_logo * seasonal_factors[quarter]
                quarterly_expansion = annual_expansion * seasonal_factors[quarter]
                quarterly_churn = annual_data.loc[year, 'Churn & Downsell'] / 4  # Even distribution
                
                # Calculate beginning ARR for quarter
                if quarterly_idx == 0:
                    # First quarter of first year
                    beginning_arr = annual_data.loc[0, 'Ending ARR']
                else:
                    # Previous quarter's ending ARR
                    beginning_arr = quarterly_data.loc[quarterly_idx - 1, 'Ending ARR']
                
                # Calculate ending ARR
                ending_arr = beginning_arr + quarterly_new_logo + quarterly_expansion + quarterly_churn
                
                # Store quarterly data
                quarterly_data.loc[quarterly_idx, 'Beginning ARR'] = beginning_arr
                quarterly_data.loc[quarterly_idx, 'New Logo Bookings'] = quarterly_new_logo
                quarterly_data.loc[quarterly_idx, 'Expansion Bookings'] = quarterly_expansion
                quarterly_data.loc[quarterly_idx, 'Churn & Downsell'] = quarterly_churn
                quarterly_data.loc[quarterly_idx, 'Ending ARR'] = ending_arr
                
                # Calculate retention metrics
                quarterly_data.loc[quarterly_idx, 'Gross Retention'] = gross_retention
                if beginning_arr > 0:
                    net_retention = (beginning_arr + quarterly_expansion + quarterly_churn) / beginning_arr
                    quarterly_data.loc[quarterly_idx, 'Net Retention'] = net_retention
                else:
                    quarterly_data.loc[quarterly_idx, 'Net Retention'] = np.nan
        
        # Calculate check column
        quarterly_data['Check'] = (
            quarterly_data['Beginning ARR'] + 
            quarterly_data['New Logo Bookings'] + 
            quarterly_data['Expansion Bookings'] + 
            quarterly_data['Churn & Downsell'] - 
            quarterly_data['Ending ARR']
        )
        
        return quarterly_data
    
    def calculate_cagr(self, start_value, end_value, years):
        """Calculate Compound Annual Growth Rate"""
        if start_value <= 0 or end_value <= 0 or years <= 0:
            return 0
        return ((end_value / start_value) ** (1/years) - 1) * 100
    
    def calculate_bookings_cagr(self, forecast_data):
        """Calculate CAGR for total bookings (New Logo + Expansion)"""
        annual_data = forecast_data['annual']
        
        # Year 1 total bookings
        year_1_bookings = annual_data.loc[1, 'New Logo Bookings'] + annual_data.loc[1, 'Expansion Bookings']
        
        # Year 5 total bookings
        year_5_bookings = annual_data.loc[5, 'New Logo Bookings'] + annual_data.loc[5, 'Expansion Bookings']
        
        return self.calculate_cagr(year_1_bookings, year_5_bookings, 4)  # 4 years from Y1 to Y5
    
    def create_summary_export(self, forecast_data, assumptions):
        """Create executive summary for export"""
        
        summary_data = []
        
        # Key metrics
        current_arr = assumptions['current_arr']
        year_5_arr = forecast_data['annual']['Ending ARR'].iloc[-1]
        arr_cagr = self.calculate_cagr(current_arr, year_5_arr, 5)
        bookings_cagr = self.calculate_bookings_cagr(forecast_data)
        
        summary_data.extend([
            ['Metric', 'Value'],
            ['Current ARR', f'${current_arr:,.0f}'],
            ['Year 5 ARR', f'${year_5_arr:,.0f}'],
            ['5-Year ARR CAGR', f'{arr_cagr:.1f}%'],
            ['5-Year Bookings CAGR', f'{bookings_cagr:.1f}%'],
            ['', ''],
            ['Assumptions', ''],
            ['Gross Retention Rate', f'{assumptions["gross_retention"]*100:.0f}%'],
            ['', ''],
            ['New Business Split by Year', ''],
        ])
        
        # Add year-specific business splits
        for year, split in assumptions['new_business_split'].items():
            summary_data.append([f'{year} New Business Split', f'{split*100:.0f}%'])
        
        summary_data.extend([
            ['', ''],
            ['Seasonality Factors', ''],
            ['Q1 Seasonality', f'{assumptions["seasonality"]["Q1"]*100:.0f}%'],
            ['Q2 Seasonality', f'{assumptions["seasonality"]["Q2"]*100:.0f}%'],
            ['Q3 Seasonality', f'{assumptions["seasonality"]["Q3"]*100:.0f}%'],
            ['Q4 Seasonality', f'{assumptions["seasonality"]["Q4"]*100:.0f}%'],
        ])
        
        # Convert to CSV string
        output = io.StringIO()
        for row in summary_data:
            output.write(','.join(str(cell) for cell in row) + '\n')
        
        return output.getvalue()
