import streamlit as st
import pandas as pd
from scraper import get_listings

st.set_page_config(page_title="Otomoto Price Analyzer", layout="wide")

st.title("🚗 Otomoto Price Analyzer")
st.markdown("Analyze car prices from Otomoto.pl based on Make, Model, and Year.")

import car_data

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
    
    # 8. First Owner Checkbox
    first_owner = st.checkbox("First Owner Only")
    
    st.markdown("---")
    st.info("ℹ️ The scraper will retrieve all available listings. This may take a while depending on the number of results.")

    analyze_btn = st.button("Analyze Prices")

import history_manager
import plotly.express as px

# Main Content with Tabs
tab1, tab2 = st.tabs(["Current Analysis", "Historical Trends"])

with tab1:
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
                                  generation_slug=generation_slug,
                                  progress_callback=update_progress)
            
            # Clear progress message when done
            status_text.empty()
            
            if listings:
                # Save to history
                history_manager.save_to_history(listings)
                st.success(f"Found {len(listings)} listings! Data saved to history.")
                df = pd.DataFrame(listings)
                
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
                
                # Visualization
                # import plotly.express as px # Moved to top
                
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
                
            else:
                st.warning("No listings found or error in scraping. Please check your inputs or try again later.")



with tab2:
    st.header("Historical Price Trends")
    
    # Load history
    history_df = history_manager.load_history()
    
    if not history_df.empty:
        # Filter (optional, simplified for now to show all data relevant to current view or just text)
        st.markdown(f"**Total Records in History:** {len(history_df)}")
        
        # Ensure scrape_date is datetime
        if "scrape_date" in history_df.columns:
            history_df["scrape_date"] = pd.to_datetime(history_df["scrape_date"])
        
        # Show raw history
        with st.expander("View Full History Log"):
            st.dataframe(history_df.sort_values(by="scrape_date", ascending=False))
            
        # Group by date and calculate average price
        if "scrape_date" in history_df.columns and "price" in history_df.columns:
            daily_stats = history_df.groupby(history_df["scrape_date"].dt.date)["price"].mean().reset_index()
            daily_stats.columns = ["Date", "Average Price"]
            
            st.subheader("Average Price Over Time")
            fig_trend = px.line(daily_stats, x="Date", y="Average Price", markers=True, 
                                title="Average Listing Price Trend")
            st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("No historical data available yet. Run a search to save data.")

