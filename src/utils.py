"""
Utility functions for the Otomoto Price Analyzer.

This module contains helper functions for data filtering and mapping.
"""

from typing import Dict


# Fuel type mapping from English to Polish
FUEL_TYPE_MAPPING: Dict[str, str] = {
    'petrol': 'benzyna',
    'diesel': 'diesel',
    'electric': 'elektryczny',
    'hybrid': 'hybryda',
    'lpg': 'lpg'
}

# Gearbox type mapping from English to Polish
GEARBOX_MAPPING: Dict[str, str] = {
    'manual': 'manualna',
    'automatic': 'automatyczna'
}


def map_fuel_type(fuel_type: str) -> str:
    """
    Map English fuel type to Polish equivalent.
    
    Args:
        fuel_type: English fuel type (e.g., 'petrol')
        
    Returns:
        Polish fuel type (e.g., 'benzyna')
    """
    return FUEL_TYPE_MAPPING.get(fuel_type.lower(), fuel_type.lower())


def map_gearbox_type(gearbox: str) -> str:
    """
    Map English gearbox type to Polish equivalent.
    
    Args:
        gearbox: English gearbox type (e.g., 'manual')
        
    Returns:
        Polish gearbox type (e.g., 'manualna')
    """
    return GEARBOX_MAPPING.get(gearbox.lower(), gearbox.lower())
