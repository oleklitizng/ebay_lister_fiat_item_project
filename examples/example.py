# ebay_lister_fiat_item_project/example/example.py

import os
import logging
from ebay_lister_fiat_item import ( #
    EPERHandler,
    EBAYHandler,
    load_ebay_env_config,
    EbayListingApp,
    # CONDITION_MAP wird benötigt, um die Zustands-ID in Text umzuwandeln
)
# Da CONDITION_MAP in ebay_item.py definiert ist und ebay_item.py __init__.py des Pakets nicht standardmäßig exportiert,
# müssen wir es entweder in __init__.py exportieren oder direkt aus dem Modul importieren.
# Angenommen, es ist in __init__.py exportiert oder wir importieren es so:
try:
    from ebay_lister_fiat_item import CONDITION_MAP
except ImportError:
    # Fallback, falls es nicht im __init__.py des Pakets ist, versuchen wir den direkten Modulimport
    # Dies hängt davon ab, wie Ihr Paket 'ebay_lister_fiat_item' strukturiert ist.
    # Wenn ebay_item.py direkt unter ebay_lister_fiat_item liegt:
    try:
        from ebay_lister_fiat_item.ebay_item import CONDITION_MAP
    except ImportError:
        logging.error("CONDITION_MAP konnte nicht importiert werden. Bitte stellen Sie sicher, dass es verfügbar ist.")
        CONDITION_MAP = {"1000": "Neu (Platzhalter)"} # Minimaler Fallback


# Configure basic logging for the example
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def generate_html_description(eper_item_data, condition_text, quantity_for_description, template_path="ebay_listing_template.html"): #
    """
    Generiert eine HTML-Beschreibung basierend auf EPER-Daten und einer Vorlage.
    """
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
    except FileNotFoundError:
        logging.error(f"HTML-Vorlagendatei nicht gefunden unter: {template_path}")
        return "Fehler: HTML-Vorlage nicht gefunden."

    # Daten für die Vorlage vorbereiten
    title = eper_item_data.get('title', 'Kein Titel verfügbar') #
    part_number = eper_item_data.get('part_number', 'Nicht spezifiziert') #
    weight = eper_item_data.get('weight_kg', 'Nicht spezifiziert') #
    price = eper_item_data.get('eper_price_str', 'Auf Anfrage') #
    
    compatible_vehicles_list = eper_item_data.get('fitting_cars', []) #
    compatible_vehicles_str = ", ".join(compatible_vehicles_list) if compatible_vehicles_list else "Bitte Teilenummer prüfen oder anfragen." #
    
    comparable_numbers_list = eper_item_data.get('comparison_numbers', []) #
    comparable_numbers_str = ", ".join(comparable_numbers_list) if comparable_numbers_list else "Keine Vergleichsnummern verfügbar." #

    # Platzhalter in der Vorlage ersetzen
    description_html = template_content.format(
        title=title,
        part_number=part_number,
        condition=condition_text, #
        weight=weight,
        quantity=quantity_for_description, #
        price=price,
        compatible_vehicles=compatible_vehicles_str,
        comparable_numbers=comparable_numbers_str
        # Der Hersteller ist in der Vorlage hartcodiert als "Fiat"
    )
    return description_html

def demonstrate_eper_handler_and_html_description(): #
    """Demonstriert das Abrufen von Daten mit EPERHandler und das Generieren einer HTML-Beschreibung."""
    logging.info("--- Demonstrating EPERHandler and HTML Description Generation ---")
    part_number_to_test = "55210268"  # Beispiel Fiat/Alfa Teilenummer
    generated_html_description = None

    try:
        eper_item = EPERHandler(part_number_to_test)
        eper_data = eper_item.data # Zugriff auf das data Attribut, das ein Dictionary ist

        logging.info(f"Data for part number {eper_data.get('part_number')}:") #
        logging.info(f"  Title: {eper_data.get('title')}") #
        logging.info(f"  Price (ePER EUR): {eper_data.get('eper_price_str')}") #
        logging.info(f"  Weight (kg): {eper_data.get('weight_kg')}") #
        logging.info(f"  Fitting Cars (sample): {eper_data.get('fitting_cars', [])[:3]}") #
        logging.info(f"  Comparison Numbers (sample): {eper_data.get('comparison_numbers', [])[:5]}") #
        logging.info("\n  Full EPER Base Description (title_base_description):") #
        for line in eper_data.get('title_base_description', '').split('\n'): #
            logging.info(f"    {line}") #

        # Beispielwerte für die Beschreibung, die nicht direkt von EPER kommen
        # In einer echten Anwendung würden diese aus der GUI oder anderen Quellen stammen
        condition_id_for_listing = "1000"  # Beispiel: "Neu"
        condition_text_for_description = CONDITION_MAP.get(condition_id_for_listing, "Zustand nicht spezifiziert")
        quantity_for_description = "1 Stück (wie im Angebot angegeben)" # Platzhaltertext für die Menge in der Beschreibung

        # HTML-Beschreibung generieren
        # Stellen Sie sicher, dass 'ebay_listing_template.html' im selben Ordner wie dieses Skript ist
        # oder passen Sie den Pfad an.
        template_file_path = os.path.join(os.path.dirname(__file__), "ebay_listing_template.html") #
        generated_html_description = generate_html_description(eper_data, condition_text_for_description, quantity_for_description, template_file_path) #

        if "Fehler:" not in generated_html_description:
            logging.info("\n--- Generierte HTML Beschreibung (Auszug) ---")
            logging.info(generated_html_description[:500] + "...") # Zeigt die ersten 500 Zeichen
            # Hier würde die 'generated_html_description' als 'description_override'
            # für EBAYHandler.draft_item_payload verwendet werden.
            # z.B. payload = ebay_handler.draft_item_payload(..., description_override=generated_html_description)
        else:
            logging.warning("\nHTML Beschreibung konnte nicht generiert werden.")


    except Exception as e:
        logging.error(f"Error during EPERHandler demonstration for {part_number_to_test}: {e}", exc_info=True)
    logging.info("-" * 30 + "\n")
    return generated_html_description # Gibt die Beschreibung für eine eventuelle weitere Verwendung zurück


def demonstrate_ebay_handler_init(generated_description_html=None): #
    """Demonstriert die Initialisierung von EBAYHandler."""
    logging.info("--- Demonstrating EBAYHandler Initialization ---")
    logging.info("This part demonstrates initializing EBAYHandler.")
    logging.info("For full functionality, ensure your .env file is set up with eBay API credentials.") #

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) #
    dotenv_path = os.path.join(project_root, ".env") #

    if not os.path.exists(dotenv_path): #
        logging.warning(f".env file not found at {dotenv_path}. EBAYHandler might fail or use defaults.") #
        logging.warning("Please create a .env file with your eBay API keys for full testing.") #
        if not os.path.exists(dotenv_path): #
            with open(dotenv_path, "w") as f: #
                f.write("EBAY_APP_ID=YOUR_APP_ID_HERE\n") #
                f.write("EBAY_CERT_ID=YOUR_CERT_ID_HERE\n") #
                f.write("EBAY_DEV_ID=YOUR_DEV_ID_HERE\n") #
                f.write("EBAY_TOKEN=YOUR_EBAY_TOKEN_HERE\n") #
                f.write("EBAY_SANDBOX=True\n") #
            logging.info(f"Created a placeholder .env file at {dotenv_path}. Please fill it with real credentials.") #


    try:
        ebay_handler = EBAYHandler(dotenv_path=dotenv_path) #
        logging.info("EBAYHandler initialized successfully using .env configuration.") #
        logging.info(f"eBay API configured for site ID: {ebay_handler.config.get('siteid')}") #
        logging.info(f"Sandbox mode: {ebay_handler.config.get('sandbox')}") #

        if generated_description_html and "Fehler:" not in generated_description_html:
            logging.info("\nDie zuvor generierte HTML-Beschreibung könnte nun für das Erstellen eines Payloads verwendet werden.")
            # Beispielhafter Aufruf (auskommentiert, da dies ein Listing erstellen würde):
            # try:
            #     logging.info("Versuche, einen Payload mit der HTML-Beschreibung zu entwerfen...")
            #     # Diese Werte müssten korrekt aus der GUI oder einer anderen Quelle stammen
            #     payload = ebay_handler.draft_item_payload(
            #         part_number_str="55210268", # Die ursprüngliche Teilenummer oder die spezifische aus EPER
            #         quantity=1,
            #         condition_id="1000", # z.B. "Neu"
            #         shipping_profile_id_val="DEINE_VERSANDPROFIL_ID",
            #         payment_profile_id_val="DEINE_ZAHLUNGSPROFIL_ID",
            #         return_profile_id_val="DEINE_RUECKGABEPROFIL_ID",
            #         sku="DEIN_SKU_55210268",
            #         item_location="Dein Standort",
            #         country_code="DE",
            #         currency_code="EUR",
            #         dispatch_time_max="3",
            #         vat_percent=19.0,
            #         description_override=generated_description_html, # HIER WIRD ES VERWENDET
            #         # picture_urls, manufacturer_override, title_override optional
            #     )
            #     logging.info("Payload-Entwurf erfolgreich (hypothetisch). Payload-Auszug:")
            #     logging.info(f"  Titel: {payload.get('Item', {}).get('Title')}")
            #     logging.info(f"  Beschreibungslänge: {len(payload.get('Item', {}).get('Description', ''))}")
            # except Exception as draft_error:
            #     logging.error(f"Fehler beim Entwerfen des Payloads: {draft_error}", exc_info=True)


    except ValueError as ve:
        logging.error(f"Initialization ValueError for EBAYHandler: {ve}") #
        logging.error("This usually means API keys are missing or are placeholders in your .env file.") #
    except Exception as e:
        logging.error(f"Error during EBAYHandler initialization: {e}", exc_info=True) #
    logging.info("-" * 30 + "\n") #


def launch_gui_example(): #
    """Shows how to launch the GUI application.""" #
    logging.info("--- Launching GUI (Example) ---") #
    logging.info("If you run this, the GUI application will start.") #
    logging.info("Close the GUI to continue with other examples if any.") #
    try:
        app = EbayListingApp() #
        if app.winfo_exists(): #
             app.mainloop() #
    except Exception as e:
        logging.error(f"Could not launch GUI: {e}", exc_info=True) #
        logging.info("GUI launch might fail in environments without a display (e.g., some CI servers).") #
    logging.info("-" * 30 + "\n") #

if __name__ == "__main__":
    logging.info("Starting eBay Lister Package Examples...") #

    # 1. Demonstrate EPERHandler and generate HTML description
    html_desc = demonstrate_eper_handler_and_html_description() #

    # 2. Demonstrate EBAYHandler Initialization (kann die generierte Beschreibung verwenden)
    demonstrate_ebay_handler_init(html_desc) #

    # 3. Show how to launch the GUI (optional, comment out if not needed)
    # response = input("Do you want to launch the GUI example? (yes/no): ").strip().lower()
    # if response == 'yes':
    #    launch_gui_example()
    # else:
    #    logging.info("Skipping GUI launch example.")

    logging.info("eBay Lister Package Examples Finished.") #
    logging.info("To run the GUI independently (if package installed): 'ebay-lister-gui'") #