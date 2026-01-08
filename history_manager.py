import pandas as pd
import os
from datetime import datetime

HISTORY_FILE = "history.csv"

def load_history():
    """
    Loads proper historical data from CSV.
    Returns an empty DataFrame if file doesn't exist.
    """
    if os.path.exists(HISTORY_FILE):
        try:
            return pd.read_csv(HISTORY_FILE)
        except Exception as e:
            print(f"Error loading history: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

def save_to_history(listings):
    """
    Appends new listings to the history CSV.
    """
    if not listings:
        return

    new_df = pd.DataFrame(listings)
    
    # Ensure ID is treated as string to avoid scientific notation issues if purely numeric
    if 'id' in new_df.columns:
        new_df['id'] = new_df['id'].astype(str)

    if os.path.exists(HISTORY_FILE):
        try:
            existing_df = pd.read_csv(HISTORY_FILE)
            if 'id' in existing_df.columns:
                existing_df['id'] = existing_df['id'].astype(str)
                
            # Combine and append
            # We want to keep historical record of price changes, so we append unique (id, scrape_date) tuples.
            # However, if we run it multiple times quickly, we might want to avoid exact duplicates.
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            
            # Remove exact duplicates (same ID, same scrape time)
            # Or better: duplicate rows entirely
            combined_df.drop_duplicates(inplace=True)
            
            combined_df.to_csv(HISTORY_FILE, index=False)
        except Exception as e:
            print(f"Error saving to history: {e}")
    else:
        new_df.to_csv(HISTORY_FILE, index=False)
