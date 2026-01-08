from scraper import get_listings
import pandas as pd

print("Testing scraper...")
listings = get_listings("bmw", "seria-3", 2015)

if listings:
    print(f"Successfully scraped {len(listings)} listings.")
    print("First listing sample:")
    print(listings[0])
else:
    print("No listings found or error occurred.")
