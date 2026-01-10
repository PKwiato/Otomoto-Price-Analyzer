import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

import time

def get_listings(make, model, year_from, year_to, fuel_type=None, gearbox=None, drive_type=None, first_owner=False, accident_free=False, generation_slug=None, max_pages=100, progress_callback=None):
    """
    Scrapes OTOMOTO for car listings based on make, model, and year range.
    Returns a list of dictionaries with listing details.
    
    Args:
        max_pages: Safety limit for pages (default 100).
        progress_callback: Optional function to call with "Scraping page X..." message.
    """
    # URL construction
    if generation_slug:
        base_url = f"https://www.otomoto.pl/osobowe/{make}/{model}/{generation_slug}/od-{year_from}"
    else:
        base_url = f"https://www.otomoto.pl/osobowe/{make}/{model}/od-{year_from}"

    params = {
        "search[filter_float_year:to]": year_to
    }

    if fuel_type:
        params["search[filter_enum_fuel_type]"] = fuel_type
        
    if gearbox:
        params["search[filter_enum_gearbox]"] = gearbox
        
    if drive_type:
        params["search[filter_enum_drive]"] = drive_type

    if first_owner:
        params["search[filter_enum_original_owner]"] = "1"

    if accident_free:
        params["search[filter_enum_no_accident]"] = "1"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
    }

    all_listings = []
    page = 1
    
    while page <= max_pages:
        params['page'] = page
        msg = f"Scraping page {page}..."
        print(f"{msg} URL: {base_url}")
        
        if progress_callback:
            progress_callback(msg)
        
        try:
            response = requests.get(base_url, params=params, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find articles with data-id (listings)
            articles = soup.find_all('article', attrs={'data-id': True})
            
            print(f"DEBUG: Found {len(articles)} articles on page {page}")
            
            if not articles:
                print("DEBUG: No articles found. Stopping pagination.")
                break
            
            scrape_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            for article in articles:
                try:
                    # Listing ID
                    listing_id = article.get('data-id')

                    # Title and Link
                    title_elem = article.find('h2').find('a')
                    title = title_elem.get_text(strip=True)
                    link = title_elem['href']
                    
                    # Price
                    # Price is usually in h3, check for currency
                    price_elem = article.find('h3')
                    price_text = price_elem.get_text(strip=True) if price_elem else "N/A"
                    
                    # Metadata (Year, Mileage)
                    year_elem = article.find('dd', {'data-parameter': 'year'})
                    listing_year = year_elem.get_text(strip=True) if year_elem else str(year_from)
                    
                    mileage_elem = article.find('dd', {'data-parameter': 'mileage'})
                    mileage_text = mileage_elem.get_text(strip=True) if mileage_elem else "N/A"
                    
                    try:
                        mileage_val = int(mileage_text.replace(' ', '').replace('km', '').strip())
                    except ValueError:
                        mileage_val = 0
                    
                    fuel_elem = article.find('dd', {'data-parameter': 'fuel_type'})
                    fuel = fuel_elem.get_text(strip=True) if fuel_elem else "N/A"
                    
                    gearbox_elem = article.find('dd', {'data-parameter': 'gearbox'})
                    gearbox_val = gearbox_elem.get_text(strip=True) if gearbox_elem else "N/A"

                    # Parse price to number if possible
                    try:
                        # Remove spaces and currency (PLN/EUR)
                        price_val = float(price_text.replace(' ', '').replace('PLN', '').replace('EUR', '').replace(',', '.'))
                    except ValueError:
                        price_val = 0

                    all_listings.append({
                        "id": listing_id,
                        "scrape_date": scrape_date,
                        "title": title,
                        "price_text": price_text,
                        "price": price_val,
                        "year": listing_year,
                        "mileage_text": mileage_text,
                        "mileage": mileage_val,
                        "fuel": fuel,
                        "gearbox": gearbox_val,
                        "link": link
                    })
                    
                except Exception as item_err:
                    print(f"Error parsing item: {item_err}")
                    continue
            
            # Gentle nice-ness delay
            time.sleep(0.5)
            page += 1
            
        except Exception as e:
            print(f"Error fetching data on page {page}: {e}")
            break
            
    return all_listings
