import streamlit as st
import pandas as pd

from src.scraper import get_listings
from src import car_data
from src.utils import map_fuel_type, map_gearbox_type

st.set_page_config(page_title="Otomoto Price Analyzer", layout="wide")

st.title("🚗 Otomoto Price Analyzer")
st.markdown("Analyze car prices from Otomoto.pl based on Make, Model, and Year.")

# Sidebar - Filter Options
with st.sidebar:
    st.header("Search Parameters")
    
    # 1. Make
    make_options = sorted(list(car_data.models_dict.keys()))
    make = st.selectbox("Make", make_options, index=make_options.index("bmw") if "bmw" in make_options else 0)
    
    # 2. Model
    if make in car_data.models_dict:
        model_options = sorted(car_data.models_dict[make])
        # Default to 'seria-3' for BMW or first item
        default_index = 0
        if make == "bmw" and "seria-3" in model_options:
            default_index = model_options.index("seria-3")
        elif make == "audi" and "a4" in model_options:
            default_index = model_options.index("a4")
            
        model = st.selectbox("Model", model_options, index=default_index)
    else:
        # Fallback if make not in dict (shouldn't happen with selectbox sourced from dict keys)
        model = st.text_input("Model", "seria-3")

    # 3. Generation (Dynamic)
    generation_slug = None
    if make in car_data.generations_dict and model in car_data.generations_dict[make]:
        gen_options = car_data.generations_dict[make][model]
        gen_choice = st.selectbox("Generation", list(gen_options.keys()))
        generation_slug = gen_options[gen_choice]

    # 4. Year Range
    current_year = 2024
    year_range = st.slider("Production Year", 1990, current_year, (2015, current_year))
    year_from = year_range[0]
    year_to = year_range[1]
    
    st.markdown("---")
    st.subheader("Additional Filters")

    # 5. Fuel Type
    fuel_options = {
        "Any": None,
        "Petrol": "petrol",
        "Diesel": "diesel",
        "Electric": "electric",
        "Hybrid": "hybrid", 
        "LPG": "lpg"
    }
    fuel_choice = st.selectbox("Fuel Type", list(fuel_options.keys()))
    selected_fuel = fuel_options[fuel_choice]
    
    # 6. Transmission
    gearbox_options = {
        "Any": None,
        "Manual": "manual",
        "Automatic": "automatic"
    }
    gearbox_choice = st.selectbox("Transmission", list(gearbox_options.keys()))
    selected_gearbox = gearbox_options[gearbox_choice]
    
    # 7. Drive Type
    drive_options = {
        "Any": None,
        "FWD (Front Wheel)": "front-wheel-drive",
        "RWD (Rear Wheel)": "rear-wheel-drive",
        "AWD / 4x4": "4x4"
    }
    drive_choice = st.selectbox("Drive Type", list(drive_options.keys()))
    selected_drive = drive_options[drive_choice]
    
    # 8. Additional Checks
    col_check1, col_check2 = st.columns(2)
    with col_check1:
        first_owner = st.checkbox("First Owner")
    with col_check2:
        accident_free = st.checkbox("Accident Free")
    
    st.markdown("---")
    
    # 9. Max Pages Control
    max_pages = st.number_input(
        "Max Pages to Scrape",
        min_value=1,
        max_value=500,
        value=100,
        step=1,
        help="Limit the number of pages to scrape. Lower values = faster results."
    )
    
    st.info("ℹ️ The scraper will retrieve all available listings. This may take a while depending on the number of results.")

    analyze_btn = st.button("Analyze Prices")

import plotly.express as px

# Main Content
if analyze_btn:
    # Create a status container for progress updates
    status_text = st.empty()
    
    def update_progress(message):
        status_text.text(f"⏳ {message}")

    with st.spinner(f"Starting scrape for {make.upper()} {model} ({year_from}-{year_to})..."):
        listings = get_listings(make, model, year_from, year_to, 
                                fuel_type=selected_fuel,
                                gearbox=selected_gearbox,
                                drive_type=selected_drive,
                                first_owner=first_owner,
                                accident_free=accident_free,
                                generation_slug=generation_slug,
                                max_pages=max_pages,
                                progress_callback=update_progress)
        
        # Clear progress message when done
        status_text.empty()
        
        if listings:
            df = pd.DataFrame(listings)
            # Convert year to int for filtering
            try:
                df['year'] = df['year'].astype(int)
            except:
                pass
                
            # Store in session state
            st.session_state['listings_df'] = df
            st.session_state['scrape_info'] = f"Scraped {len(listings)} listings for {make} {model}"
            st.success(f"Found {len(listings)} listings!")
        else:
            st.warning("No listings found or error in scraping. Please check your inputs or try again later.")

# DISPLAY LOGIC (Run if data exists in session state)
if 'listings_df' in st.session_state:
    df = st.session_state['listings_df']
    
    # Apply Year Filter
    if 'year' in df.columns:
        df = df[(df['year'] >= year_from) & (df['year'] <= year_to)]
    
    # Filter by Fuel Type
    if selected_fuel:
        search_term = map_fuel_type(selected_fuel)
        df = df[df['fuel'].str.lower().str.contains(search_term, na=False)]
        
    # Filter by Transmission
    if selected_gearbox:
        search_term = map_gearbox_type(selected_gearbox)
        df = df[df['gearbox'].str.lower().str.contains(search_term, na=False)]
        
    # Filter by First Owner
    if first_owner and 'first_owner' in df.columns:
        df = df[df['first_owner'] == True]
        
    # Filter by Accident Free
    if accident_free and 'accident_free' in df.columns:
        df = df[df['accident_free'] == True]

    st.info(f"{st.session_state.get('scrape_info', '')}. Showing {len(df)} listings matching current filters.")

    if not df.empty:
        # Basic Statistics
        avg_price = df['price'].mean()
        median_price = df['price'].median()
        min_price = df['price'].min()
        max_price = df['price'].max()
        
        # metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Average Price", f"{avg_price:,.0f} PLN")
        col2.metric("Median Price", f"{median_price:,.0f} PLN")
        col3.metric("Lowest Price", f"{min_price:,.0f} PLN")
        col4.metric("Highest Price", f"{max_price:,.0f} PLN")
        
        st.markdown("---")

        # Data Table
        with st.expander("View Raw Data"):
            st.dataframe(df)
        
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.subheader("Price Distribution")
            fig_hist = px.histogram(df, x="price", nbins=20, title="Price Histogram", labels={'price': 'Price (PLN)'})
            st.plotly_chart(fig_hist, use_container_width=True)
        
        with col_chart2:
            st.subheader("Price vs. Mileage")
            # Filter out valid mileage for plot
            df_plot = df[df['mileage'] > 0]
            fig_scatter = px.scatter(df_plot, x="mileage", y="price", hover_data=['title', 'year'], 
                                     title="Price vs Mileage", labels={'mileage': 'Mileage (km)', 'price': 'Price (PLN)'})
            st.plotly_chart(fig_scatter, use_container_width=True)
        
        st.subheader("Price vs. Year of Production")
        fig_year = px.scatter(df, x="year", y="price", hover_data=['title', 'mileage'],
                              title="Price vs Year", labels={'year': 'Year', 'price': 'Price (PLN)'})
        st.plotly_chart(fig_year, use_container_width=True)
    else:
        st.warning("No listings match the current filters.")

