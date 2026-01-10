# Otomoto Price Analyzer

A Streamlit-based web application for analyzing car prices from Otomoto.pl.

## Features

- **Search by Make, Model, and Generation**: Select from a comprehensive list of car manufacturers and models
- **Advanced Filtering**: Filter by year, fuel type, transmission, drive type, first owner, and accident-free status
- **Price Analytics**: View average, median, min, and max prices
- **Interactive Charts**: 
  - Price distribution histogram
  - Price vs. Year scatter plot
  - Price vs. Mileage scatter plot
- **Raw Data Table**: View and export all scraped listings
- **Client-Side Filtering**: Instantly filter results without re-scraping
- **Max Pages Control**: Limit scraping to avoid long wait times

## Installation

```bash
pip install -r requirements.txt
```

## Running the App

### Option 1: Using the run script (Linux/Mac)
```bash
chmod +x run_app.sh
./run_app.sh
```

### Option 2: Manual start (Windows/Linux/Mac)
```bash
# Set PYTHONPATH to include backend directory
export PYTHONPATH="${PYTHONPATH}:backend"  # Linux/Mac
# OR
$env:PYTHONPATH="backend"  # Windows PowerShell

# Run Streamlit
streamlit run app.py --server.port 8501
```

The app will be available at: **http://localhost:8501**

## Project Structure

```
.
├── app.py                      # Main Streamlit application
├── backend/
│   ├── scraper.py             # Web scraping logic
│   ├── car_data.py            # Car makes, models, and generations data
│   └── main.py                # (Legacy) FastAPI backend - not used
├── requirements.txt           # Python dependencies
└── run_app.sh                # Startup script
```

## Usage

1. Open the app at http://localhost:8501
2. Select your desired car make and model from the sidebar
3. Adjust filters (year, fuel type, etc.)
4. Set "Max Pages to Scrape" (lower = faster)
5. Click "Analyze Prices"
6. View statistics, charts, and raw data
7. Adjust filters to see real-time updates without re-scraping

## Notes

- The app scrapes data from Otomoto.pl, a Polish car marketplace
- Fuel types and transmission types are mapped from English to Polish terms
- Client-side filtering allows instant updates after initial scraping
- The FastAPI backend (port 8000) has been deprecated in favor of the Streamlit app
