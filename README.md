# Otomoto Price Analyzer

An advanced, modern web application designed to scrape and analyze used car prices from **Otomoto.pl** (Poland's largest automotive marketplace). This tool helps buyers and enthusiasts understand current market trends for specific vehicles.

![Dashboard Preview](https://via.placeholder.com/800x400?text=Otomoto+Analyzer+Dashboard)

## 🎯 Purpose

The primary goal of this application is to provide **transparent pricing insights** for used cars. It automates the process of collecting data and visualizing market trends, helping users answer questions like:
- "What is a fair price for a 2018 BMW 3 Series?"
- "How does mileage affect the price of a Kia Sportage?"
- "Is it worth paying extra for a younger model year?"

## 🚀 Features

### Core Capabilities
- **Real-Time Scraping**: Fetches live data directly from Otomoto.pl.
- **Smart Filtering**:
  - Filter by **Make, Model, Generation** (dynamic dropdowns).
  - refine by **Year, Fuel Type, Transmission, Drive Type**.
  - Exclusive filters for **First Owner** and **Accident Free** vehicles (parsed directly from listings).
- **Streaming Progress**: View real-time "Scraping page X..." updates during analysis.

### Analytics & Visualization
- **Price Statistics**: Instant calculation of Average, Median, Minimum, and Maximum prices.
- **Interactive Charts**:
  - **Price Distribution**: Histogram showing the most common price ranges.
  - **Price vs. Mileage**: Scatter plot to identify outliers and depreciation trends.
- **Raw Data Explorer**: A sortable table containing all scraped listings with links to original ads.

## 🛠️ Tech Stack

This project uses a modern, lightweight, and deployment-friendly stack:

| Component | Technology | Description |
|-----------|------------|-------------|
| **Backend** | **Python (Flask)** | Lightweight WSGI web application framework. |
| **Scraping** | **Requests + BS4** | Efficient HTML parsing and HTTP handling. |
| **Frontend** | **HTML5 + CSS3** | Custom dark-themed UI with Grid/Flexbox layouts. |
| **Scripting** | **Vanilla JavaScript** | Asynchronous fetching, DOM manipulation, stream handling. |
| **Charts** | **Chart.js** | Responsive, interactive data visualization. |
| **Data** | **Pandas** | (Backend) Data processing and cleaning. |

## 📦 Installation

1.  **Clone the repository** (if applicable) or download the source code.
2.  **Install Python dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## ▶️ How to Run

### Windows (PowerShell)
```powershell
# Set PYTHONPATH to include the current directory
$env:PYTHONPATH="."

# Run the application
python app.py
```

### Linux / macOS
```bash
# Make the run script executable
chmod +x run_app.sh

# Run the application
./run_app.sh
```

Once started, open your browser and navigate to:
👉 **[http://localhost:5000](http://localhost:5000)**

## 📂 Project Structure

```
Otomoto-Price-Analyzer/
├── app.py                 # Main Flask application entry point
├── run_app.sh             # Startup helper script (Linux/Mac)
├── src/                   # Core business logic
│   ├── scraper.py         # Advanced scraping logic with pagination handling
│   ├── car_data.py        # Database of Makes, Models, and Generations
│   └── utils.py           # Helper functions & Polish-English mapping
├── static/                # Frontend assets
│   ├── css/style.css      # Modern dark theme styling
│   └── js/script.js       # Application logic (fetching, sorting, charts)
├── templates/             # HTML Templates
│   └── index.html         # Main dashboard layout
└── requirements.txt       # Project dependencies
```

## 📝 Usage Guide

1.  **Select Vehicle**: Choose a Manufacturer (e.g., *BMW*) and Model (e.g., *Seria 3*) from the sidebar.
2.  **Refine Search**: Adjust the Year range and select a Generation if known.
3.  **Apply Filters**: (Optional) Select Fuel type, Transmission, or check "First Owner".
4.  **Set Limits**: Adjust "Max Pages to Scrape" (default: 20) to balance between speed and data volume.
5.  **Analyze**: Click **"Analyze Prices"** and watch the real-time progress.
6.  **Explore**: Use the charts to spot trends and sort the table to find specific deals.
