# ebay_lister/__init__.py

"""
eBay Lister Package
===================

This package provides tools for listing items on eBay, including
fetching part details and a graphical user interface.
"""

# Import key classes and functions to make them accessible
# at the package level, e.g., from ebay_lister import EBAYHandler
from .api_config import load_ebay_env_config
from .ebay_item import EBAYHandler, CONDITION_MAP
from .scrape_open_eper import EPERHandler, CAR_BRANDS_DATA
from .gui import EbayListingApp
import logging

# __all__ defines the public API of the package when a user
# executes 'from ebay_lister import *'.
__all__ = [
    "load_ebay_env_config",  # From api_config.py
    "EBAYHandler",           # From ebay_item.py
    "CONDITION_MAP",         # From ebay_item.py
    "EPERHandler",           # From scrape_open_eper.py
    "CAR_BRANDS_DATA",       # From scrape_open_eper.py
    "EbayListingApp"         # From gui.py
]


logging.getLogger(__name__).addHandler(logging.NullHandler())
#This prevents "No handler found" warnings if the library user hasn't
# configured logging, but your application (gui.py) already sets up logging.