"""
Web scraper for Otomoto.pl car listings.

This module provides functionality to scrape car listings from Otomoto.pl
based on various search criteria.
"""

import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable

import requests
from bs4 import BeautifulSoup


def get_listings(
    make: str,
    model: str,
    year_from: int,
    year_to: int,
    fuel_type: Optional[str] = None,
    gearbox: Optional[str] = None,
    drive_type: Optional[str] = None,
    first_owner: bool = False,
    accident_free: bool = False,
    generation_slug: Optional[str] = None,
    max_pages: int = 100,
    progress_callback: Optional[Callable[[str], None]] = None
) -> List[Dict[str, Any]]:
    """
    Scrape car listings from Otomoto.pl.
    
    Args:
        make: Car manufacturer (e.g., 'bmw', 'audi')
        model: Car model (e.g., 'seria-3', 'a4')
        year_from: Minimum production year
        year_to: Maximum production year
        fuel_type: Fuel type filter (e.g., 'petrol', 'diesel')
        gearbox: Transmission type (e.g., 'manual', 'automatic')
        drive_type: Drive type (e.g., 'front-wheel-drive', '4x4')
        first_owner: Filter for first owner only
        accident_free: Filter for accident-free vehicles only
        generation_slug: Specific generation identifier
        max_pages: Maximum number of pages to scrape (default: 100)
        progress_callback: Optional callback function for progress updates
        
    Returns:
        List of dictionaries containing listing details
    """
    base_url = _build_url(make, model, year_from, generation_slug)
    params = _build_params(year_to, fuel_type, gearbox, drive_type, first_owner, accident_free)
    headers = _get_headers()
    
    all_listings = []
    page = 1
    
    while page <= max_pages:
        params['page'] = page
        
        if progress_callback:
            progress_callback(f"Scraping page {page}...")
        
        try:
            listings = _scrape_page(base_url, params, headers, year_from)
            
            if not listings:
                print(f"No listings found on page {page}. Stopping pagination.")
                break
            
            all_listings.extend(listings)
            print(f"Found {len(listings)} listings on page {page}")
            
            time.sleep(0.5)  # Be nice to the server
            page += 1
            
        except requests.RequestException as e:
            print(f"Error fetching page {page}: {e}")
            break
        except Exception as e:
            print(f"Unexpected error on page {page}: {e}")
            break
    
    return all_listings


def _build_url(make: str, model: str, year_from: int, generation_slug: Optional[str]) -> str:
    """Build the base URL for scraping."""
    if generation_slug:
        return f"https://www.otomoto.pl/osobowe/{make}/{model}/{generation_slug}/od-{year_from}"
    return f"https://www.otomoto.pl/osobowe/{make}/{model}/od-{year_from}"


def _build_params(
    year_to: int,
    fuel_type: Optional[str],
    gearbox: Optional[str],
    drive_type: Optional[str],
    first_owner: bool,
    accident_free: bool
) -> Dict[str, Any]:
    """Build query parameters for the request."""
    params = {"search[filter_float_year:to]": year_to}
    
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
    
    return params


def _get_headers() -> Dict[str, str]:
    """Get HTTP headers for requests."""
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                     "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }


def _scrape_page(
    base_url: str,
    params: Dict[str, Any],
    headers: Dict[str, str],
    year_from: int
) -> List[Dict[str, Any]]:
    """Scrape a single page of listings."""
    response = requests.get(base_url, params=params, headers=headers, timeout=30)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.content, 'html.parser')
    articles = soup.find_all('article', attrs={'data-id': True})
    
    if not articles:
        return []
    
    scrape_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    listings = []
    
    for article in articles:
        try:
            listing = _parse_listing(article, scrape_date, year_from)
            listings.append(listing)
        except Exception as e:
            print(f"Error parsing listing: {e}")
            continue
    
    return listings


def _parse_listing(article, scrape_date: str, year_from: int) -> Dict[str, Any]:
    """Parse a single listing article."""
    listing_id = article.get('data-id')
    
    # Title and link
    title_elem = article.find('h2').find('a')
    title = title_elem.get_text(strip=True)
    link = title_elem['href']
    
    # Price
    price_elem = article.find('h3')
    price_text = price_elem.get_text(strip=True) if price_elem else "N/A"
    price_val = _parse_price(price_text)
    
    # Year
    year_elem = article.find('dd', {'data-parameter': 'year'})
    listing_year = year_elem.get_text(strip=True) if year_elem else str(year_from)
    
    # Mileage
    mileage_elem = article.find('dd', {'data-parameter': 'mileage'})
    mileage_text = mileage_elem.get_text(strip=True) if mileage_elem else "N/A"
    mileage_val = _parse_mileage(mileage_text)
    
    # Fuel type
    fuel_elem = article.find('dd', {'data-parameter': 'fuel_type'})
    fuel = fuel_elem.get_text(strip=True) if fuel_elem else "N/A"
    
    # Gearbox
    gearbox_elem = article.find('dd', {'data-parameter': 'gearbox'})
    gearbox = gearbox_elem.get_text(strip=True) if gearbox_elem else "N/A"
    
    # Drive type
    drive_elem = article.find('dd', {'data-parameter': 'drive'})
    drive = drive_elem.get_text(strip=True) if drive_elem else "N/A"

    # Accident Free (Bezwypadkowy)
    accident_free_val = False
    # Check distinct parameters often used in list view
    if article.find('li', class_='parameter-feature-item', string='Bezwypadkowy'):
         accident_free_val = True
    # Also check data-parameter if available (sometimes different in list view)
    elif article.find('dd', {'data-parameter': 'no_accident'}):
         accident_free_val = True

    # First Owner (Pierwszy właściciel)
    first_owner_val = False
    if article.find('li', class_='parameter-feature-item', string='Pierwszy właściciel'):
         first_owner_val = True
    elif article.find('dd', {'data-parameter': 'original_owner'}):
         first_owner_val = True
    
    return {
        "id": listing_id,
        "scrape_date": scrape_date,
        "title": title,
        "price_text": price_text,
        "price": price_val,
        "year": listing_year,
        "mileage_text": mileage_text,
        "mileage": mileage_val,
        "fuel": fuel,
        "gearbox": gearbox,
        "drive": drive,
        "accident_free": accident_free_val,
        "first_owner": first_owner_val,
        "link": link
    }


def _parse_price(price_text: str) -> float:
    """Parse price text to float value."""
    try:
        return float(
            price_text.replace(' ', '')
                     .replace('PLN', '')
                     .replace('EUR', '')
                     .replace(',', '.')
        )
    except ValueError:
        return 0.0


def _parse_mileage(mileage_text: str) -> int:
    """Parse mileage text to integer value."""
    try:
        return int(mileage_text.replace(' ', '').replace('km', '').strip())
    except ValueError:
        return 0
