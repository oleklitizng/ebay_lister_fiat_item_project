import dotenv
import os
from typing import Optional, Dict, List
import logging

def load_ebay_env_config(dotenv_path: Optional[str] = None) -> Dict:
    """
    Load eBay environment variables from a specified .env file or the default .env file.

    Args:
        dotenv_path (Optional[str]): Path to the .env file.
                                     If None, it defaults to looking for a .env
                                     file in the current directory or parent directories.
    Returns:
        dict: The API configuration dictionary for eBay.
    """
    if dotenv_path:
        logging.info(f"Lade eBay Umgebungsvariablen von: {dotenv_path}")
        dotenv.load_dotenv(dotenv_path=dotenv_path, override=True)
    else:
        logging.info("Lade eBay Umgebungsvariablen von Standard .env Datei (falls vorhanden).")
        dotenv.load_dotenv(override=True)

    config = {
        'api': os.getenv('EBAY_API_TYPE', 'trading'), # Standardwert, falls nicht in .env
        'siteid': os.getenv('EBAY_SITE_ID', '77'),  # eBay Germany als Standard
        'appid': os.getenv('EBAY_APP_ID'),
        'certid': os.getenv('EBAY_CERT_ID'),
        'devid': os.getenv('EBAY_DEV_ID'),
        'token': os.getenv('EBAY_TOKEN'),
        'sandbox': str(os.getenv('EBAY_SANDBOX', 'False')).lower() == 'true'
    }
    return config