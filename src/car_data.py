"""
Data for Otomoto Price Analyzer
"""

# Common Models dictionary (Make -> List of Models)
# Now used primarily to list available makes. 
# Models and Generations are scraped dynamically.
models_dict = {
    "audi": [],
    "bmw": [],
    "citroen": [],
    "ford": [],
    "honda": [],
    "hyundai": [],
    "kia": [],
    "mazda": [],
    "mercedes-benz": [],
    "nissan": [],
    "opel": [],
    "peugeot": [],
    "renault": [],
    "seat": [],
    "skoda": [],
    "toyota": [],
    "volkswagen": [],
    "volvo": [],
}

# Generations data (Make -> Model -> {Display Name: Slug})
# Now primarily handled dynamically.
generations_dict = {}
