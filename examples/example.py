# ebay_lister_fiat_item_project/example/example.py
# (Diese Version basiert auf der zweiten von Ihnen hochgeladenen Datei, 
# die noch die .get_item()-Aufrufe enthielt)

import os
import logging
from ebay_lister_fiat_item import (
    EPERHandler,
    EBAYHandler,
    load_ebay_env_config,
    EbayListingApp
    # CONDITION_MAP Import wird hier nicht direkt benötigt,
    # da diese Version keine HTML-Beschreibung mit Zustandstext generiert.
)

# Configure basic logging for the example
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def demonstrate_eper_handler():
    """Demonstriert das Abrufen von Daten mit EPERHandler."""
    logging.info("--- Demonstrating EPERHandler ---")
    part_number_to_test = "98446492" # Beispiel Fiat/Alfa Teilenummer
    # part_number_to_test = "7796374" # Anderes Beispiel
    try:
        eper_item_handler = EPERHandler(part_number_to_test) # eper_item_handler ist eine Instanz von EPERHandler

        # Korrekter Zugriff auf die Daten über das .data Attribut oder __getitem__
        # Option 1: Zugriff über das .data Attribut (Dictionary)
        # eper_data = eper_item_handler.data
        # logging.info(f"Data for part number {eper_data.get('part_number')}:")
        # logging.info(f"  Title: {eper_data.get('title')}")
        # ... und so weiter

        # Option 2: Zugriff über die __getitem__-Methode (Dictionary-ähnlich)
        # Dies ist prägnanter und nutzt die Magie von __getitem__ in EPERHandler.
        logging.info(f"Data for part number {eper_item_handler['part_number']}:")
        logging.info(f"  Title: {eper_item_handler['title']}")
        logging.info(f"  Price (ePER EUR): {eper_item_handler['eper_price_str']}") # oder eper_item_handler['price']
        logging.info(f"  Weight (kg): {eper_item_handler['weight_kg']}")
        
        fitting_cars = eper_item_handler['fitting_cars']
        logging.info(f"  Fitting Cars (sample): {fitting_cars[:3] if fitting_cars else 'N/A'}")
        
        comparison_numbers = eper_item_handler['comparison_numbers']
        logging.info(f"  Comparison Numbers (sample): {comparison_numbers[:5] if comparison_numbers else 'N/A'}")
        
        logging.info("\n  Full Description (title_base_description):")
        title_base_desc = eper_item_handler['title_base_description']
        if title_base_desc:
            for line in title_base_desc.split('\n'):
                logging.info(f"    {line}")
        else:
            logging.info("    N/A")


    except Exception as e:
        logging.error(f"Error during EPERHandler demonstration for {part_number_to_test}: {e}", exc_info=True)
    logging.info("-" * 30 + "\n")


def demonstrate_ebay_handler_init():
    """Demonstriert die Initialisierung von EBAYHandler."""
    logging.info("--- Demonstrating EBAYHandler Initialization ---")
    logging.info("This part demonstrates initializing EBAYHandler.")
    logging.info("For full functionality, ensure your .env file is set up with eBay API credentials.")

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dotenv_path = os.path.join(project_root, ".env")

    if not os.path.exists(dotenv_path):
        logging.warning(f".env file not found at {dotenv_path}. EBAYHandler might fail or use defaults.")
        logging.warning("Please create a .env file with your eBay API keys for full testing.")
        if not os.path.exists(dotenv_path):
            with open(dotenv_path, "w") as f:
                f.write("EBAY_APP_ID=YOUR_APP_ID_HERE\n")
                f.write("EBAY_CERT_ID=YOUR_CERT_ID_HERE\n")
                f.write("EBAY_DEV_ID=YOUR_DEV_ID_HERE\n")
                f.write("EBAY_TOKEN=YOUR_EBAY_TOKEN_HERE\n")
                f.write("EBAY_SANDBOX=True\n")
            logging.info(f"Created a placeholder .env file at {dotenv_path}. Please fill it with real credentials.")


    try:
        ebay_handler = EBAYHandler(dotenv_path=dotenv_path)
        logging.info("EBAYHandler initialized successfully using .env configuration.")
        logging.info(f"eBay API configured for site ID: {ebay_handler.config.get('siteid')}")
        logging.info(f"Sandbox mode: {ebay_handler.config.get('sandbox')}")

    except ValueError as ve:
        logging.error(f"Initialization ValueError for EBAYHandler: {ve}")
        logging.error("This usually means API keys are missing or are placeholders in your .env file.")
    except Exception as e:
        logging.error(f"Error during EBAYHandler initialization: {e}", exc_info=True)
    logging.info("-" * 30 + "\n")


def launch_gui_example():
    """Shows how to launch the GUI application."""
    logging.info("--- Launching GUI (Example) ---")
    logging.info("If you run this, the GUI application will start.")
    logging.info("Close the GUI to continue with other examples if any.")
    try:
        app = EbayListingApp()
        if app.winfo_exists():
             app.mainloop()
    except Exception as e:
        logging.error(f"Could not launch GUI: {e}", exc_info=True)
        logging.info("GUI launch might fail in environments without a display (e.g., some CI servers).")
    logging.info("-" * 30 + "\n")

if __name__ == "__main__":
    logging.info("Starting eBay Lister Package Examples...")

    # 1. Demonstrate EPERHandler
    demonstrate_eper_handler()

    # 2. Demonstrate EBAYHandler Initialization
    demonstrate_ebay_handler_init()

    # 3. Show how to launch the GUI (optional, comment out if not needed)
    # response = input("Do you want to launch the GUI example? (yes/no): ").strip().lower()
    # if response == 'yes':
    #    launch_gui_example()
    # else:
    #    logging.info("Skipping GUI launch example.")

    logging.info("eBay Lister Package Examples Finished.")
    logging.info("To run the GUI independently (if package installed): 'ebay-lister-gui'")