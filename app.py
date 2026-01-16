"""
Otomoto Price Analyzer - Flask Application.

This module serves the web application, handling API requests for scraping
and providing data to the frontend.
"""

from flask import Flask, render_template, jsonify, request
import pandas as pd
from typing import Dict, Any, List

from src.scraper import get_listings
from src import car_data

app = Flask(__name__)

@app.route('/')
def index():
    """Render the main dashboard page."""
    return render_template('index.html')

@app.route('/api/config')
def get_config():
    """Return configuration data (makes) for the frontend."""
    makes = sorted(list(car_data.models_dict.keys()))
    return jsonify({
        'makes': makes
    })

@app.route('/api/models/<make>')
def get_models_for_make(make):
    """Fetch models for a specific make dynamically."""
    from src.scraper import get_models
    models = get_models(make)
    return jsonify(models)

@app.route('/api/generations/<make>/<model>')
def get_generations_for_model(make, model):
    """Fetch generations for a specific model dynamically."""
    from src.scraper import get_generations
    generations = get_generations(make, model)
    return jsonify(generations)

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """
    Trigger the scraping process based on usage params.
    Returns a streamed response (NDJSON) with progress updates and final data.
    """
    data = request.json
    
    make = data.get('make')
    model = data.get('model')
    year_from = int(data.get('year_from', 2015))
    year_to = int(data.get('year_to', 2024))
    generation = data.get('generation')
    max_pages = int(data.get('max_pages', 20))

    # Additional filters
    fuel_type = data.get('fuel_type')
    gearbox = data.get('gearbox')
    drive_type = data.get('drive_type')
    first_owner = data.get('first_owner', False)
    accident_free = data.get('accident_free', False)

    if not make or not model:
        return jsonify({'error': 'Make and Model are required'}), 400

    def generate():
        import json
        
        # Progress callback to yield updates
        def progress_callback(message):
            # We yield a JSON string followed by a newline
            yield json.dumps({"type": "progress", "message": message}) + "\n"

        try:
            listings = get_listings(
                make=make,
                model=model,
                year_from=year_from,
                year_to=year_to,
                fuel_type=fuel_type,
                gearbox=gearbox,
                drive_type=drive_type,
                first_owner=first_owner,
                accident_free=accident_free,
                generation_slug=generation,
                max_pages=max_pages,
                progress_callback=progress_callback 
            )

            # Final data
            yield json.dumps({
                "type": "complete", 
                "data": {
                    'count': len(listings),
                    'listings': listings
                }
            }) + "\n"

        except Exception as e:
            yield json.dumps({"type": "error", "message": str(e)}) + "\n"

    from flask import Response, stream_with_context
    return Response(stream_with_context(generate()), mimetype='application/x-ndjson')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
