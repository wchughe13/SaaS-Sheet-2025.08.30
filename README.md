# ARR Forecast Dashboard

A Streamlit application for visualizing ARR (Annual Recurring Revenue) forecasts and analytics.

## Files Structure

```
├── streamlit_app.py      # Main Streamlit application
├── visualizations.py     # Chart visualization classes
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Local Development

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   streamlit run streamlit_app.py
   ```

## Deployment to Streamlit Cloud

1. Push these files to a GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repository
4. Set the main file path to `streamlit_app.py`
5. Deploy!

## Customization

- Replace the sample data in `load_sample_data()` function with your actual data
- Modify chart styling in the `ARRVisualizer` class
- Add more interactive controls in the sidebar

## Dependencies

- streamlit>=1.28.0
- plotly>=5.17.0
- pandas>=2.0.0
- numpy>=1.24.0
