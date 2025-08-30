import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

class ARRVisualizer:
    def __init__(self):
        self.color_scheme = {
            'primary': '#1f77b4',
            'success': '#2ca02c',
            'danger': '#d62728',
            'warning': '#ff7f0e',
            'info': '#17a2b8',
            'secondary': '#6c757d'
        }
    
    def create_arr_chart(self, forecast_data):
        """Create main ARR dashboard chart with quarterly bars"""
        
        quarterly_data = forecast_data['quarterly'].copy()
        
        # Create simple figure without secondary axis
        fig = go.Figure()
        
        # Add ARR bars
        fig.add_trace(
            go.Bar(
                x=quarterly_data['Date'],
                y=quarterly_data['Ending ARR'],
                name='Quarterly Ending ARR',
                marker_color=self.color_scheme['primary'],
                hovertemplate='<b>%{x}</b><br>Ending ARR: $%{y:,.0f}<extra></extra>'
            )
        )
        
        # Update layout
        fig.update_layout(
            title='5-Year ARR Forecast',
            xaxis_title='Date',
            yaxis_title='ARR ($)',
            height=400,
            showlegend=False,
            hovermode='x unified'
        )
        
        # Update y-axis
        fig.update_yaxes(
            tickformat='$,.0f',
            showgrid=True,
            gridcolor='lightgray'
        )
        
        return fig
    
    def create_growth_rate_chart(self, forecast_data):
        """Create separate YoY growth rate chart"""
        
        quarterly_data = forecast_data['quarterly'].copy()
        
        # Calculate quarterly growth rates
        quarterly_data['YoY_Growth'] = quarterly_data['Ending ARR'].pct_change(periods=4) * 100
        
        # Filter out first 4 quarters for YoY (they will be NaN)
        valid_yoy_data = quarterly_data[quarterly_data['YoY_Growth'].notna()]
        
        # Create figure
        fig = go.Figure()
        
        # Add growth rate line
        fig.add_trace(
            go.Scatter(
                x=valid_yoy_data['Date'],
                y=valid_yoy_data['YoY_Growth'],
                mode='lines+markers',
                name='YoY Growth Rate',
                line=dict(color=self.color_scheme['success'], width=3),
                marker=dict(size=8),
                hovertemplate='<b>%{x}</b><br>YoY Growth: %{y:.1f}%<extra></extra>'
            )
        )
        
        # Update layout
        fig.update_layout(
            title='Year-over-Year Growth Rate',
            xaxis_title='Date',
            yaxis_title='YoY Growth Rate (%)',
            height=300,
            showlegend=False,
            hovermode='x unified'
        )
        
        # Update y-axis
        fig.update_yaxes(
            tickformat='.1f',
            showgrid=True,
            gridcolor='lightgray'
        )
        
        return fig
    
    def create_waterfall_chart(self, forecast_data):
        """Create annual ARR waterfall chart"""
        
        annual_data = forecast_data['annual'].copy()
        
        # Prepare waterfall data (exclude year 0)
        waterfall_data = []
        cumulative = annual_data.loc[0, 'Ending ARR']  # Starting point
        
        # Starting position
        waterfall_data.append({
            'label': 'Year 0\nEnding ARR',
            'value': cumulative,
            'type': 'absolute',
            'color': self.color_scheme['secondary']
        })
        
        for year in range(1, 6):
            # New Logo
            new_logo = annual_data.loc[year, 'New Logo Bookings']
            waterfall_data.append({
                'label': f'Y{year}\nNew Logo',
                'value': new_logo,
                'type': 'relative',
                'color': self.color_scheme['success']
            })
            
            # Expansion
            expansion = annual_data.loc[year, 'Expansion Bookings']
            waterfall_data.append({
                'label': f'Y{year}\nExpansion',
                'value': expansion,
                'type': 'relative',
                'color': self.color_scheme['info']
            })
            
            # Churn
            churn = annual_data.loc[year, 'Churn & Downsell']
            waterfall_data.append({
                'label': f'Y{year}\nChurn',
                'value': churn,
                'type': 'relative',
                'color': self.color_scheme['danger']
            })
            
            # Ending ARR
            ending_arr = annual_data.loc[year, 'Ending ARR']
            waterfall_data.append({
                'label': f'Y{year}\nEnding ARR',
                'value': ending_arr,
                'type': 'absolute',
                'color': self.color_scheme['primary']
            })
        
        # Create waterfall chart
        fig = go.Figure()
        
        # Calculate positions for waterfall
        x_labels = [item['label'] for item in waterfall_data]
        y_values = []
        base_values = []
        colors = []
        
        cumulative = 0
        for item in waterfall_data:
            if item['type'] == 'absolute':
                y_values.append(item['value'])
                base_values.append(0)
                cumulative = item['value']
            else:  # relative
                y_values.append(abs(item['value']))
                if item['value'] >= 0:
                    base_values.append(cumulative)
                    cumulative += item['value']
                else:
                    cumulative += item['value']
                    base_values.append(cumulative)
            
            colors.append(item['color'])
        
        # Add bars
        fig.add_trace(go.Bar(
            x=x_labels,
            y=y_values,
            base=base_values,
            marker_color=colors,
            text=[f'${val:,.0f}' for val in y_values],
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>Value: $%{y:,.0f}<extra></extra>'
        ))
        
        # Update layout
        fig.update_layout(
            title='Annual ARR Waterfall Analysis',
            xaxis_title='Components',
            yaxis_title='ARR ($)',
            yaxis_tickformat='$,.0f',
            height=500,
            showlegend=False
        )
        
        return fig
    
    def create_bookings_chart(self, forecast_data):
        """Create quarterly bookings breakdown chart"""
        
        quarterly_data = forecast_data['quarterly'].copy()
        
        fig = go.Figure()
        
        # New Logo bookings (bottom stack)
        fig.add_trace(go.Bar(
            x=quarterly_data['Date'],
            y=quarterly_data['New Logo Bookings'],
            name='New Logo Bookings',
            marker_color=self.color_scheme['success'],
            hovertemplate='<b>%{x}</b><br>New Logo: $%{y:,.0f}<extra></extra>'
        ))
        
        # Expansion bookings (top stack)
        fig.add_trace(go.Bar(
            x=quarterly_data['Date'],
            y=quarterly_data['Expansion Bookings'],
            name='Expansion Bookings',
            marker_color=self.color_scheme['info'],
            hovertemplate='<b>%{x}</b><br>Expansion: $%{y:,.0f}<extra></extra>'
        ))
        
        # Update layout
        fig.update_layout(
            title='Quarterly Bookings Breakdown',
            xaxis_title='Date',
            yaxis_title='Bookings ($)',
            yaxis_tickformat='$,.0f',
            barmode='stack',
            height=400,
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig
    
    def create_retention_chart(self, forecast_data):
        """Create retention analytics chart"""
        
        quarterly_data = forecast_data['quarterly'].copy()
        
        fig = go.Figure()
        
        # Gross retention line
        fig.add_trace(go.Scatter(
            x=quarterly_data['Date'],
            y=quarterly_data['Gross Retention'] * 100,
            mode='lines+markers',
            name='Gross Retention Rate',
            line=dict(color=self.color_scheme['warning'], width=3),
            marker=dict(size=6),
            hovertemplate='<b>%{x}</b><br>Gross Retention: %{y:.1f}%<extra></extra>'
        ))
        
        # Net retention line
        fig.add_trace(go.Scatter(
            x=quarterly_data['Date'],
            y=quarterly_data['Net Retention'] * 100,
            mode='lines+markers',
            name='Net Retention Rate',
            line=dict(color=self.color_scheme['primary'], width=3),
            marker=dict(size=6),
            hovertemplate='<b>%{x}</b><br>Net Retention: %{y:.1f}%<extra></extra>'
        ))
        
        # Add benchmark lines
        fig.add_hline(
            y=90, 
            line_dash="dash", 
            line_color="gray",
            annotation_text="90% Benchmark"
        )
        
        fig.add_hline(
            y=110, 
            line_dash="dash", 
            line_color="gray",
            annotation_text="110% Benchmark"
        )
        
        # Update layout
        fig.update_layout(
            title='Retention Rate Analysis',
            xaxis_title='Date',
            yaxis_title='Retention Rate (%)',
            yaxis_tickformat='.1f',
            height=400,
            hovermode='x unified',
            yaxis_range=[80, 140],
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig
