from .scrape_open_eper import EPERHandler # Assuming this module exists and is correctly implemented
from .api_config import load_ebay_env_config #
from ebaysdk.trading import Connection as Trading
from ebaysdk.finding import Connection as Finding
import logging
from typing import Optional, Dict, List

CONDITION_MAP = {
    '1000': 'New',
    '1500': 'New other (see details)',
    '1750': 'New with defects',
    '2000': 'Certified refurbished',
    '2500': 'Seller refurbished',
    '3000': 'Used',
    '4000': 'Very Good',
    '5000': 'Good',
    '6000': 'Acceptable',
    '7000': 'For parts or not working'
}

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
class EBAYHandler:
    """
    Handles interactions with the eBay API for listing items.
    It uses EPERHandler to fetch item details.
    """
    def __init__(self, dotenv_path: Optional[str] = None, api_config_override: Optional[Dict] = None):
        """
        Initializes the eBay API connections.

        Args:
            dotenv_path (Optional[str]): Path to the .env file containing API credentials.
                                         If None, default .env loading behavior is used.
            api_config_override (Optional[Dict]): A dictionary to override specific API_CONFIG values
                                                  after loading from .env.
        """
        # 1. Lade die Basiskonfiguration aus der .env Datei
        config = load_ebay_env_config(dotenv_path=dotenv_path) #

        # 2. Wende Overrides an, falls vorhanden
        if api_config_override:
            config.update(api_config_override) #

        # 3. Stelle sicher, dass alle benötigten Schlüssel vorhanden sind
        required_keys = ['appid', 'certid', 'devid', 'token'] #
        missing_or_placeholder_keys = [] #

        for key in required_keys:
            value = config.get(key) #
            # Überprüfe auf None, leere Strings oder typische Platzhalter-Strings
            if value is None or value == "" or (isinstance(value, str) and f'YOUR_EBAY_{key.upper()}' in value): #
                missing_or_placeholder_keys.append(key) #

        if missing_or_placeholder_keys:
            error_message = ( #
                f"eBay API configuration for the following keys is missing, empty, or using a placeholder: "
                f"{', '.join(missing_or_placeholder_keys)}. "
                "Please set them correctly in your .env file or via api_config_override."
            )
            logging.error(error_message) #
            raise ValueError(error_message) #

        # Speichere die finale Konfiguration
        self.config = config #
        logging.info(f"Finale eBay API Konfiguration: {self.config}") #

        # 4. Initialisiere die eBay API-Clients
        try:
            self.api_trading = Trading(config_file=None, **self.config) #
            self.api_finding = Finding(config_file=None, **self.config) #
            logging.info("eBay API connections initialized successfully.") #
        except Exception as e:
            logging.error(f"Failed to initialize eBay API connections: {e}") #
            raise

    def get_category_id(self, part_number: str, default_category_id: str = '185012') -> str:
        """
        Finds the eBay Category ID for a given part number using keywords.

        Args:
            part_number (str): The part number to search for.
            default_category_id (str): The category ID to return if no item is found.
                                       '185012' is "Sonstige" (Other) in Auto & Motorrad: Teile on eBay DE.

        Returns:
            str: The eBay Category ID.
        """
        try:
            # Splitting part_number into keywords can be refined based on part_number structure
            keywords = part_number # Ganze Teilenummer als Keyword kann besser sein
            response = self.api_finding.execute('findItemsByKeywords', {'keywords': keywords}) #

            if response.reply.ack == 'Success' and response.reply.searchResult._count != '0': #
                # Prüfe, ob searchResult und item existieren und nicht leer sind
                if hasattr(response.reply.searchResult, 'item') and response.reply.searchResult.item: #
                    category_id = response.reply.searchResult.item[0].primaryCategory.categoryId #
                    logging.info(f"Found category ID '{category_id}' for part number '{part_number}'.") #
                    return category_id #
                else:
                    logging.warning(f"Search result for part number '{part_number}' was successful but contained no items. Using default category: '{default_category_id}'.") #
                    return default_category_id #
            else:
                ack_status = response.reply.ack if hasattr(response.reply, 'ack') else 'N/A' #
                error_message = "" #
                if hasattr(response.reply, 'errorMessage') and response.reply.errorMessage and hasattr(response.reply.errorMessage, 'error') and response.reply.errorMessage.error: #
                     error_message = response.reply.errorMessage.error[0].message #


                logging.warning(f"No category found or error for part number '{part_number}'. Ack: {ack_status}. API Error: {error_message}. Using default: '{default_category_id}'.") #
                return default_category_id #
        except Exception as e:
            logging.error(f"Error getting category ID for '{part_number}': {e}") #
            return default_category_id #

    @staticmethod
    def get_shipping_profile_id_by_weight(weight_kg: float, default_profile_id: str) -> str:
        """
        Determines the eBay Shipping Profile ID based on item weight.
        This is a placeholder and needs your specific business logic.

        Args:
            weight_kg (float): The weight of the item in kilograms.
            default_profile_id (str): A default shipping profile ID if no specific rule matches.

        Returns:
            str: The Shipping Profile ID.
        """
        # Example placeholder logic:
        # You would replace this with your actual shipping profile IDs and weight tiers.
        # shipping_profiles = {
        #     'LIGHT_PACKAGE_PROFILE_ID': (0, 1.0),  # Profile ID for items up to 1.0 kg
        #     'MEDIUM_PACKAGE_PROFILE_ID': (1.0, 5.0), # Profile ID for items >1.0 kg up to 5.0 kg
        #     'HEAVY_PACKAGE_PROFILE_ID': (5.0, float('inf')) # Profile ID for items >5.0 kg
        # }
        # for profile_id, (min_weight, max_weight) in shipping_profiles.items():
        #     if min_weight < weight_kg <= max_weight:
        #         logging.info(f"Selected shipping profile '{profile_id}' for weight {weight_kg}kg.")
        #         return profile_id

        logging.info(f"Using default shipping profile '{default_profile_id}' for weight {weight_kg}kg (implement custom logic).") #
        return default_profile_id # Return a passed default or a fixed one

    def draft_item_payload(self,
                       part_number_str: str,
                       quantity: int,
                       condition_id: str,
                       shipping_profile_id_val: str,
                       payment_profile_id_val: str, # Hinzugefügt
                       return_profile_id_val: str,  # Hinzugefügt
                       sku: str,
                       item_location: str,
                       country_code: str,
                       currency_code: str,
                       dispatch_time_max: str,
                       vat_percent: float, # Geändert zu float für interne Logik, wird zu str für API
                       picture_urls: Optional[List[str]] = None, # Geändert zu picture_urls und List[str]
                       manufacturer_override: Optional[str] = None,
                       description_override: Optional[str] = None, # Geändert von description zu description_override
                       title_override: Optional[str] = None # Hinzugefügt für Titel-Override
                       ) -> dict:
        """
        Prepares the item dictionary (payload) for an eBay listing.
        (Args-Beschreibung wie in der Originaldatei)
        """
        if condition_id not in CONDITION_MAP:
            logging.warning(f"Condition ID '{condition_id}' not in known CONDITION_MAP. Using it directly.") #

        if picture_urls is None or not picture_urls:
            # Verwende einen Standard-Platzhalter, wenn keine Bilder bereitgestellt werden
            picture_urls = ['https://rs-syke.de/wp-content/uploads/2024/01/rs-syke.de_.webp'] #
            logging.info("No picture URLs provided, using default placeholder image.") #


        try:
            eper_item = EPERHandler(part_number_str) # Assuming EPERHandler raises an error if part not found
        except Exception as e:
            logging.error(f"Failed to initialize EPERHandler for part number {part_number_str}: {e}") #
            raise ValueError(f"EPERHandler could not be initialized for part number {part_number_str}. Error: {e}") #

        # KORRIGIERTER ZUGRIFF auf eper_item Daten
        title = title_override if title_override else eper_item["title"]
        description = description_override if description_override else eper_item["title_base_description"]
        final_price_str = eper_item["eper_price_str"] # oder eper_item["price"]
        part_number_specific = eper_item["part_number"]

        if not final_price_str:
            raise ValueError(f"EPER Price (eper_price_str) is missing for part number {part_number_str}.") #
        try:
            # Validierung, ob der Preis eine Zahl ist
            float(final_price_str) #
        except ValueError:
            raise ValueError(f"Invalid price format '{final_price_str}' for part number {part_number_str}. Must be a number.") #

        # KORRIGIERTER ZUGRIFF und Schlüsselname
        comparison_numbers_list = eper_item["comparison_numbers"]
        if not isinstance(comparison_numbers_list, list):
            comparison_numbers_list = [str(comparison_numbers_list)] if comparison_numbers_list else [] #

        comparison_numbers_str = ", ".join(filter(None, comparison_numbers_list)) # Filtert leere Strings heraus

        if manufacturer_override:
            manufacturer = manufacturer_override #
        else:
            manufacturer_override = 'Fiat' # Standardwert, falls kein Override

        if not all([title, description, final_price_str, part_number_specific]):
            missing_fields = [ #
                f for f, v in [("title",title), ("description",description), ("eper_price_str",final_price_str), ("part_number",part_number_specific)] if not v
            ]
            error_msg = f"Essential data missing from EPERHandler for part number '{part_number_str}'. Missing: {', '.join(missing_fields)}" #
            logging.error(error_msg) #
            raise ValueError(error_msg) #

        category_id = self.get_category_id(part_number_specific, default_category_id='185012') # Nutze spezifische Teilenummer für Kategorie

        new_item_payload = { #
            'Item': {
                'Title': title[:80], # eBay Titel-Limit ist 80 Zeichen
                'Description': description, #
                'PrimaryCategory': {'CategoryID': category_id}, #
                'StartPrice': final_price_str, #
                'Quantity': str(quantity), # Muss String sein
                'ListingType': 'FixedPriceItem', #
                'ListingDuration': 'GTC', #
                'Location': item_location, #
                'Country': country_code, #
                'Currency': currency_code, #
                'DispatchTimeMax': str(dispatch_time_max), # Muss String sein
                'ConditionID': condition_id, #
                'PictureDetails': {'PictureURL': picture_urls}, # Nimmt Liste von URLs
                'SellerProfiles': { #
                    'SellerShippingProfile': { #
                        'ShippingProfileID': str(shipping_profile_id_val) #
                    },
                    'SellerPaymentProfile': { # Hinzugefügt
                        'PaymentProfileID': str(payment_profile_id_val) #
                    },
                    'SellerReturnProfile': { # Hinzugefügt
                        'ReturnProfileID': str(return_profile_id_val) #
                    }
                },
                'ItemSpecifics': { #
                    'NameValueList': [ #
                        {'Name': 'Hersteller', 'Value': manufacturer}, #
                        {'Name': 'Herstellernummer', 'Value': part_number_specific}, #
                        # Nur hinzufügen, wenn Vergleichsnummern vorhanden sind
                        *([{'Name': 'OE/OEM Referenznummer(n)', 'Value': comparison_numbers_str}] if comparison_numbers_str else []) #
                    ]
                },
                'SKU': sku, #
            }
        }
        # Füge VATDetails nur hinzu, wenn vat_percent einen Wert hat und nicht 0 ist
        if vat_percent is not None and float(vat_percent) > 0: #
            new_item_payload['Item']['VATDetails'] = {'VATPercent': str(vat_percent)} #


        logging.info(f"Drafted payload for SKU '{sku}' (Part: {part_number_str}).") #
        return new_item_payload #

    def get_item(self, item_id: str) -> Optional[Dict]:
        """
        Retrieves an item's details from eBay using its ItemID.
        (Args-Beschreibung wie in der Originaldatei)
        """
        try:
            response = self.api_trading.execute('GetItem', {'ItemID': item_id, 'DetailLevel': 'ReturnAll'}) #
            if response.reply.Ack == 'Success': #
                logging.info(f"Successfully fetched item '{item_id}'.") #
                return response.dict().get('Item') # response.dict() ist oft nützlicher
            else:
                error_msg = "Unknown eBay error" #
                if hasattr(response.reply, 'Errors') and response.reply.Errors: #
                     error_msg = response.reply.Errors[0].LongMessage #
                logging.error(f"Error fetching item '{item_id}': {error_msg}") #
                return None #
        except Exception as e:
            logging.error(f"Exception fetching item '{item_id}': {e}") #
            return None #

    def create_item(self, item_payload: dict) -> Optional[str]:
        """
        Lists a new item on eBay.
        (Args-Beschreibung wie in der Originaldatei)
        """
        try:
            response = self.api_trading.execute('AddItem', item_payload) #
            # response.dict() für leichteren Zugriff und Logging
            response_data = response.dict() #
            logging.debug(f"AddItem API Response for SKU {item_payload.get('Item', {}).get('SKU', 'N/A')}: {response_data}") #

            if response.reply.Ack == 'Success' or response.reply.Ack == 'Warning': #
                item_id = response_data.get('ItemID') #
                logging.info(f"Item created successfully with ID: {item_id}. SKU: {item_payload.get('Item', {}).get('SKU', 'N/A')}") #
                if response.reply.Ack == 'Warning' and response_data.get('Errors'): #
                     for error in response_data.get('Errors'): #
                        logging.warning(f"eBay AddItem Warning: {error.get('SeverityCode')} - {error.get('ShortMessage')} - {error.get('LongMessage')}") #
                return item_id #
            else:
                logging.error(f"Error creating item. SKU: {item_payload.get('Item', {}).get('SKU', 'N/A')}.") #
                if response_data.get('Errors'): #
                    for error in response_data.get('Errors'): #
                        logging.error(f"eBay AddItem Error: {error.get('SeverityCode')} - {error.get('ShortMessage')} - {error.get('LongMessage')}") #
                return None #
        except Exception as e:
            logging.error(f"Exception creating item. SKU: {item_payload.get('Item', {}).get('SKU', 'N/A')}: {e}") #
            return None #

    def revise_item(self, item_id: str, revised_item_fields: dict) -> Optional[str]:
        """
        Revises an existing eBay listing.
        (Args-Beschreibung wie in der Originaldatei)
        """
        item_to_revise = {'ItemID': item_id} #
        item_to_revise.update(revised_item_fields) #

        try:
            response = self.api_trading.execute('ReviseFixedPriceItem', {'Item': item_to_revise}) # ReviseFixedPriceItem ist oft passender
            response_data = response.dict() #
            logging.debug(f"ReviseItem API Response for ItemID {item_id}: {response_data}") #

            if response.reply.Ack == 'Success' or response.reply.Ack == 'Warning': #
                logging.info(f"Item '{item_id}' revised successfully.") #
                if response.reply.Ack == 'Warning' and response_data.get('Errors'): #
                     for error in response_data.get('Errors'): #
                        logging.warning(f"eBay ReviseItem Warning: {error.get('SeverityCode')} - {error.get('ShortMessage')} - {error.get('LongMessage')}") #
                return item_id #
            else:
                logging.error(f"Error revising item '{item_id}'.") #
                if response_data.get('Errors'): #
                    for error in response_data.get('Errors'): #
                        logging.error(f"eBay ReviseItem Error: {error.get('SeverityCode')} - {error.get('ShortMessage')} - {error.get('LongMessage')}") #
                return None #
        except Exception as e:
            logging.error(f"Exception revising item '{item_id}': {e}") #
            return None #