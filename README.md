
# eBay Lister Package

This package provides tools for listing automotive parts on eBay, including fetching part details from an online ePER catalog and a graphical user interface (GUI) for managing listings.

## Features

* **Fetch Part Details:** Automatically scrapes part information (description, price, weight, fitting cars, comparison numbers) from an online ePER catalog using a part number.
* **eBay API Integration:**
    * Connects to the eBay Trading and Finding APIs.
    * Retrieves eBay category IDs based on part numbers.
    * Creates new fixed-price listings on eBay.
    * Revises existing eBay listings.
    * Retrieves item details from eBay.
* **Graphical User Interface (GUI):**
    * User-friendly interface built with CustomTkinter to manage listing operations.
    * Supports creating new listings and revising existing ones.
    * Allows overriding automatically fetched title and description.
    * Provides input fields for all necessary eBay listing parameters (condition, quantity, SKU, shipping/payment/return profiles, item location, VAT, etc.).
    * Displays process logs and outputs directly in the GUI.
* **Configuration:**
    * Loads eBay API credentials and settings from a `.env` file.
* **Logging:** Comprehensive logging for both backend processes and GUI operations.

## Package Structure

The package is organized into the following main modules:

* `__init__.py`: Makes key classes and functions accessible at the package level.
* `api_config.py`: Handles loading of eBay API credentials and configuration from a `.env` file.
* `ebay_item.py`: Contains the `EBAYHandler` class, which manages all interactions with the eBay APIs (Trading and Finding). It uses `EPERHandler` to fetch item details and prepares payloads for creating or revising listings. It also defines a `CONDITION_MAP` for eBay item conditions.
* `scrape_open_eper.py`: Contains the `EPERHandler` class, responsible for scraping part details (like description, price, weight, fitting cars, comparison numbers) from the `eper.fiatforum.com` website. It includes `CAR_BRANDS_DATA` for mapping models.
* `gui.py`: Implements the `EbayListingApp` class, providing a CustomTkinter-based graphical user interface for the eBay listing functionalities.

## Setup and Configuration

1. **Dependencies:**

    Ensure you have the following Python libraries installed:

    * `customtkinter`
    * `python-dotenv`
    * `ebaysdk`
    * `requests`
    * `beautifulsoup4`
    * `cloudscraper`

    You can typically install them using pip:

    ```bash
    pip install customtkinter python-dotenv ebaysdk requests beautifulsoup4 cloudscraper
    ```

2. **eBay API Credentials (.env file):**

    This package requires eBay API credentials to function. Create a `.env` file in the root directory of your project (or specify its path). Add your eBay API keys and settings to this file. The `api_config.py` module will load these variables.

    Example `.env` file content:

    ```env
    EBAY_API_TYPE=trading
    EBAY_SITE_ID=77 # eBay Germany
    EBAY_APP_ID=YOUR_EBAY_APP_ID
    EBAY_CERT_ID=YOUR_EBAY_CERT_ID
    EBAY_DEV_ID=YOUR_EBAY_DEV_ID
    EBAY_TOKEN=YOUR_EBAY_TOKEN
    EBAY_SANDBOX=False # Set to True for Sandbox environment
    ```

    Replace `YOUR_EBAY_...` with your actual eBay Developer Program credentials.

## Usage

### Running the GUI Application

The primary way to use this package is through its graphical interface.

1. Ensure your `.env` file is correctly set up with your eBay API credentials.
2. Run the `gui.py` script (or the main function it provides if integrated into a larger application).

    ```python
    # If you have the package installed or in your PYTHONPATH
    from ebay_lister.gui import main_gui_app
    main_gui_app()

    # Or, if running directly from the directory containing gui.py
    # (assuming __main__ block in gui.py)
    # python path/to/ebay_lister/gui.py
    ```

    The `EbayListingApp` will launch, allowing you to:

    * Select an action: "New Listing" or "Revise Listing".
    * **For New Listings:**
        * Enter Part Number (OEM), Quantity, and SKU.
        * Provide eBay-specific details: Shipping Profile ID, Payment Profile ID, Return Profile ID, Item Location, Country Code, Currency Code, Dispatch Time Max, and VAT Percent.
        * Select the item's condition.
        * Optionally override the auto-fetched title and description.
    * **For Revising Listings:**
        * Enter the eBay Item ID.
        * Enter new Quantity, SKU, or override Title/Description as needed.
    * Click "Submit" to process the request.
    * View logs and results in the output text area.

### Using Package Components Programmatically

You can also use the individual components for more custom workflows.

**1. Loading eBay Configuration:**

```python
from ebay_lister.api_config import load_ebay_env_config

ebay_config = load_ebay_env_config()
# For a custom .env path:
# ebay_config = load_ebay_env_config(dotenv_path="/path/to/your/.env")
print(ebay_config)
```

**2. Fetching Part Details with EPERHandler:**

```python
from ebay_lister.scrape_open_eper import EPERHandler
import logging

logging.basicConfig(level=logging.INFO)

part_number = "YOUR_PART_NUMBER" # Replace with an actual part number
try:
    eper_handler = EPERHandler(part_number)
    part_details = eper_handler.data

    print(f"Part Number: {part_details.get('part_number')}")
    print(f"Title: {part_details.get('title')}")
    print(f"ePER Price: {part_details.get('eper_price_str')}")
    print(f"Weight (kg): {part_details.get('weight_kg')}")
    print(f"Fitting Cars: {part_details.get('fitting_cars')}")
    print(f"Comparison Numbers: {part_details.get('comparison_numbers')}")
except Exception as e:
    print(f"Error fetching part details for {part_number}: {e}")
```

**3. Interacting with eBay using EBAYHandler:**

```python
from ebay_lister.ebay_item import EBAYHandler, CONDITION_MAP
import logging

logging.basicConfig(level=logging.INFO)

try:
    ebay_handler = EBAYHandler()

    payload = ebay_handler.draft_item_payload(
        part_number_str="YOUR_PART_NUMBER",
        quantity=1,
        condition_id=CONDITION_MAP['New'],
        shipping_profile_id_val="YOUR_SHIPPING_PROFILE_ID",
        payment_profile_id_val="YOUR_PAYMENT_PROFILE_ID",
        return_profile_id_val="YOUR_RETURN_PROFILE_ID",
        sku="YOUR_SKU_A01_B02",
        item_location="Your City, Your State",
        country_code="DE",
        currency_code="EUR",
        dispatch_time_max="3",
        vat_percent=19.0
    )
    print("Drafted Payload:", payload)

except ValueError as ve:
    print(f"Configuration or input error: {ve}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
```

## Logging

The application uses the logging module.

* `EBAYHandler` and `EPERHandler` log their operations.
* The GUI (`EbayListingApp`) sets up file logging (`ebay_lister_gui.log`) and redirects stdout/logs to the GUI’s output textbox.

## Public API

Defined in `ebay_lister/__init__.py` via `__all__`:

```python
__all__ = [
    "load_ebay_env_config",
    "EBAYHandler",
    "CONDITION_MAP",
    "EPERHandler",
    "CAR_BRANDS_DATA",
    "EbayListingApp"
]
```

## Disclaimer

Web scraping (as done by `EPERHandler`) is prone to breakage if the target site changes.  
Always comply with eBay's API policies and third-party terms of service.  
This package is provided as-is — test thoroughly, especially with the production eBay environment.
