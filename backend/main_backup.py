from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import car_data
import scraper
import history_manager

app = FastAPI(title="Otomoto Price Analyzer API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For dev, allow all. Check specifically for Next.js port in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchParams(BaseModel):
    make: str
    model: str
    year_from: int
    year_to: int
    fuel_type: Optional[str] = None
    gearbox: Optional[str] = None
    drive_type: Optional[str] = None
    first_owner: bool = False
    accident_free: bool = False
    generation_slug: Optional[str] = None
    max_pages: int = 100

@app.get("/")
def read_root():
    return {"message": "Otomoto Price Analyzer API is running"}

@app.get("/api/makes")
def get_makes():
    return sorted(list(car_data.models_dict.keys()))

@app.get("/api/models/{make}")
def get_models(make: str):
    if make not in car_data.models_dict:
        raise HTTPException(status_code=404, detail="Make not found")
    return sorted(car_data.models_dict[make])

@app.get("/api/generations/{make}/{model}")
def get_generations(make: str, model: str):
    if make in car_data.generations_dict and model in car_data.generations_dict[make]:
        return car_data.generations_dict[make][model]
    return {}

@app.post("/api/listings")
def search_listings(params: SearchParams):
    print(f"Searching for {params.make} {params.model}...")
    
    # Define a simple callback for server-side logging
    def progress_callback(msg):
        print(f"[Scraper] {msg}")

    try:
        listings = scraper.get_listings(
            make=params.make,
            model=params.model,
            year_from=params.year_from,
            year_to=params.year_to,
            fuel_type=params.fuel_type,
            gearbox=params.gearbox,
            drive_type=params.drive_type,
            first_owner=params.first_owner,
            accident_free=params.accident_free,
            generation_slug=params.generation_slug,
            max_pages=params.max_pages,
            progress_callback=progress_callback
        )
        
        # Save to history automatically
        if listings:
            history_manager.save_to_history(listings)
            
        return {"count": len(listings), "listings": listings}
        
    except Exception as e:
        print(f"Error scraping: {e}")
        raise HTTPException(status_code=500, detail=str(e))
