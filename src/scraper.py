"""
Web scraper for Otomoto.pl car listings.

This module provides functionality to scrape car listings from Otomoto.pl
based on various search criteria.
"""

import json
import time
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable

import requests
from bs4 import BeautifulSoup

# Simple in-memory cache for metadata
_metadata_cache = {}
CACHE_TTL = timedelta(hours=1)


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


def get_makes() -> List[Dict[str, str]]:
    """Fetch all available car makes from Otomoto."""
    url = "https://www.otomoto.pl/osobowe"
    return _extract_filter_data(url, 'filter_enum_make')


def get_models(make: str) -> List[Dict[str, str]]:
    """Fetch models for a given make from Otomoto."""
    url = f"https://www.otomoto.pl/osobowe/{make}"
    return _extract_filter_data(url, 'filter_enum_model')


def get_generations(make: str, model: str) -> List[Dict[str, str]]:
    """Fetch generations for a given make and model from Otomoto."""
    url = f"https://www.otomoto.pl/osobowe/{make}/{model}"
    return _extract_filter_data(url, 'filter_enum_generation')


def _extract_filter_data(url: str, filter_id: str) -> List[Dict[str, str]]:
    """Helper to extract filter data from NEXT_DATA in a page with caching."""
    # Check cache
    cache_key = f"{url}:{filter_id}"
    if cache_key in _metadata_cache:
        timestamp, data = _metadata_cache[cache_key]
        if datetime.now() - timestamp < CACHE_TTL:
            return data

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                     "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        script_tag = soup.find('script', id='__NEXT_DATA__')
        if not script_tag:
            return []
        
        data = json.loads(script_tag.string)
        urql_state = data.get('props', {}).get('pageProps', {}).get('urqlState', {})
        
        # Parse conditions for better matching if model-specific
        url_parts = url.split('/')
        make = url_parts[4] if len(url_parts) > 4 else None
        model = url_parts[5] if len(url_parts) > 5 else None
        
        all_values = {}
        
        for v in urql_state.values():
            if isinstance(v, dict) and 'data' in v:
                try:
                    inner_data = json.loads(v['data'])
                    found_filters = _find_filters_recursive(inner_data, filter_id)
                    for f in found_filters:
                        # Check conditions if present
                        if not _matches_conditions(f, make, model):
                            continue
                            
                        vals = _extract_values_from_filter(f)
                        for val in vals:
                            # Keep most generic or most complete name
                            all_values[val['id']] = val['name']
                except:
                    continue
        
        res = []
        if all_values:
            res = [{'id': k, 'name': v} for k, v in sorted(all_values.items(), key=lambda x: x[1])]
        
        # If not found in urqlState, try AlternativeLinks as fallback for models
        if not res and filter_id == 'filter_enum_model' and make:
            res = _extract_from_alternative_links(data, make_slug=make)

        # Cache results if successful
        if res:
            _metadata_cache[cache_key] = (datetime.now(), res)
            
        return res

    except Exception as e:
        print(f"Error extracting filter {filter_id} from {url}: {e}")
    
    return []


def _matches_conditions(filter_obj: Dict[str, Any], make: Optional[str], model: Optional[str]) -> bool:
    """Check if the filter object matches the given make and model conditions."""
    conditions = filter_obj.get('conditions', [])
    if not conditions:
        return True # Assume it's a global filter or correctly scoped if no conditions
        
    for cond in conditions:
        f_id = cond.get('filterId')
        val = cond.get('value')
        if f_id == 'filter_enum_make' and make and val != make:
            return False
        if f_id == 'filter_enum_model' and model and val != model:
            return False
    return True


def _find_filters_recursive(obj: Any, target_id: str) -> List[Dict[str, Any]]:
    """Recursively find all filter objects with a specific ID or filterId."""
    results = []
    if isinstance(obj, dict):
        # We look for AdvertSearchFilter (id) or OpenForInputFilterState (filterId)
        if obj.get('id') == target_id or obj.get('filterId') == target_id:
            results.append(obj)
        for v in obj.values():
            results.extend(_find_filters_recursive(v, target_id))
    elif isinstance(obj, list):
        for item in obj:
            results.extend(_find_filters_recursive(item, target_id))
    return results


def _extract_values_from_filter(filter_obj: Dict[str, Any]) -> List[Dict[str, str]]:
    """Extract label/value pairs from a filter object, including counter if present."""
    values = []
    raw_values = filter_obj.get('values', [])
    for val in raw_values:
        if not isinstance(val, dict):
            continue
            
        if val.get('__typename') == 'AdvertSearchFilterValue':
            name = val.get('name')
            counter = val.get('counter')
            if counter is not None:
                name = f"{name} ({counter})"
            values.append({
                'id': val.get('id'),
                'name': name
            })
        elif val.get('__typename') == 'AdvertSearchFilterValuesGroup':
            for gv in val.get('values', []):
                if isinstance(gv, dict):
                    name = gv.get('name')
                    counter = gv.get('counter')
                    if counter is not None:
                        name = f"{name} ({counter})"
                    values.append({
                        'id': gv.get('id'),
                        'name': name
                    })
    return values


def _extract_from_alternative_links(next_data: Dict[str, Any], make_slug: str) -> List[Dict[str, str]]:
    """Fallback extraction from AlternativeLinksBlock (often models) if urqlState fails."""
    import re
    try:
        # Search for AlternativeLinksBlock in props
        def find_alt_links(obj):
            if isinstance(obj, dict):
                if obj.get('__typename') == 'AlternativeLinksBlock' and (obj.get('name') == 'model-generations' or obj.get('name') == 'models'):
                    return obj
                for v in obj.values():
                    res = find_alt_links(v)
                    if res: return res
            elif isinstance(obj, list):
                for item in obj:
                    res = find_alt_links(item)
                    if res: return res
            return None

        alt_block = find_alt_links(next_data)
        if not alt_block:
            return []
            
        models = []
        # Pattern to extract model slug from URL: /osobowe/make/model-slug
        pattern = re.compile(rf"/osobowe/{make_slug}/([^/?#\s]+)")
        
        for link in alt_block.get('links', []):
            url = link.get('url', '')
            match = pattern.search(url)
            if match:
                model_slug = match.group(1)
                # Filter out regions or other things
                if any(region in model_slug for region in ['mazowieckie', 'slaskie', 'wielkopolskie']):
                    continue
                
                name = link.get('title', model_slug)
                # Cleanup name
                clean_name = name.replace(make_slug.capitalize(), '').strip()
                
                models.append({
                    'id': model_slug,
                    'name': clean_name if clean_name else model_slug
                })
        return models
    except:
        return []
