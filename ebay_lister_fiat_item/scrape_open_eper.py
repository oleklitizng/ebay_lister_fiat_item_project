import requests
from bs4 import BeautifulSoup
import logging
import re
import time
import cloudscraper
import random

# --- (CAR_BRANDS_DATA should be defined globally here) ---
CAR_BRANDS_DATA = {
    'LANCIA': ['LYBRA', 'DELTA', 'THESIS', 'DEDRA', 'Y', 'YPSILON', 'MUSA', 'PHEDRA', 'THEMA', 'KAPPA', 'ZETA', 'FLAVIA', 'FULVIA', 'FLAMINIA', 'AURELIA', 'APPIA', 'VOYAGER', 'PRISMA', 'BETA', 'GAMMA', 'STRATOS', 'RALLY 037', 'ARDEA'],
    'ALFA ROMEO': ['145', '146', '147', '155', '156', '159', '164', '166', '4C', '8C', 'ALFASUD', 'ALFETTA', 'ARNA', 'BRERA', 'GIULIA', 'GIULIETTA', 'GT', 'GTA', 'GTV', 'MITO', 'MONTREAL', 'SPIDER', 'SPRINT', 'STELVIO', 'SZ', 'RZ', '33', '75', '90', 'TONALE'],
    'FIAT': ['500', '500L', '500X', 'ALBEA', 'BARCHETTA', 'BRAVA', 'BRAVO', 'CINQUECENTO', 'COUPE', 'CROMA', 'DOBLO', 'DUCATO', "DUCATO'94", 'DUNA', 'FIORINO', 'FREEMONT', 'FULLBACK', 'GRANDE PUNTO', 'IDEA', 'LINEA', 'MAREA', 'MULTIPLA', 'PALIO', 'PANDA', 'PUNTO', 'QUBO', 'REGATA', 'RITMO', 'SCUDO', 'SEDICI', 'SEICENTO', 'SIENA', 'STILO', 'STRADA', 'TALENTO', 'TEMPRA', 'TIPO', 'ULYSSE', 'UNO'],
    'ABARTH': ['500', '595', '695', 'GRANDE PUNTO', 'PUNTO EVO', '124 SPIDER'],
    'MASERATI': ['GHIBLI', 'QUATTROPORTE', 'LEVANTE', 'GRANTURISMO', 'GRANCABRIO', 'MC20', 'GRECALE'],
    'FERRARI': ['458', '488', 'F8 TRIBUTO', 'SF90 STRADALE', 'ROMA', 'PORTOFINO', '812', 'CALIFORNIA', 'FF', 'GTC4LUSSO', 'LAFERRARI'],
    'IVECO': ['DAILY', 'EUROCARGO', 'STRALIS', 'TRAKKER', 'S-WAY', 'MASSIF']
}


class EPERHandler:
    """
    Ruft Teiledetails von der ePER-Website (eper.fiatforum.com) für eine gegebene Teilenummer ab.
    Die gesammelten Daten werden im Attribut 'self.data' als Dictionary gespeichert.

    Die Struktur von 'self.data' ist wie folgt:
    {
        'part_number': str,             # Die ursprünglich angefragte Teilenummer
        'eper_price_str': str | None,   # Der Preis aus ePER als String (z.B. "123.45") oder None
        'weight_kg': str,               # Das Gewicht in Kilogramm als String (z.B. "0.5")
        'fitting_cars': list[str],      # Eine Liste von passenden Fahrzeugmodellen (z.B. ["FIAT 500", "LANCIA YPSILON"])
        'comparison_numbers': list[str],# Eine Liste von Vergleichsnummern (ursprüngliche, vorherige und Ersatzteile)
        'title': str,                   # Der generierte Produkttitel (max. 80 Zeichen)
        'title_base_description': str   # Eine mehrzeilige, formatierte Zusammenfassung aller wichtigen gefundenen Daten.
    }
    """
    def __init__(self, part_number):
        self.car_brands = CAR_BRANDS_DATA
        self.data = self.get_part_details(part_number)

    def __getitem__(self, key):
        """Ermöglicht den Zugriff auf Datenfelder wie bei einem Dictionary."""
        if key == "price":
            return self.data.get("eper_price_str")
        return self.data.get(key)

    def _fetch_soup(self, part_number):
        """Fetches and parses HTML content from ePER for a given part number."""
        url = f"https://eper.fiatforum.com/Part/SearchPartByPartNumber?language=en&PartNumber={part_number}"
        scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})
        time.sleep(random.uniform(1, 3)) # Keep reasonable delay

        try:
            response = scraper.get(url)
            response.raise_for_status()
            if not response.text.strip():
                logging.warning(f"Received empty response from ePER for part number: {part_number}")
                return None
            return BeautifulSoup(response.text, 'html.parser')
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching ePER data for {part_number}: {e}")
            return None
        except ValueError as e: # Handles potential JSON decoding errors if response is not HTML
            logging.error(f"Error decoding ePER response (possibly empty or not HTML) for {part_number}: {e}")
            return None

    def _extract_title_from_soup(self, soup):
        if not soup: return ""
        table = soup.find('table', class_='table-sm')
        if table and len(table.find_all('tr')) >= 2:
            rows = table.find_all('tr')
            value_1 = rows[0].find_all('td')[1].text.strip() if len(rows[0].find_all('td')) > 1 else ""
            value_2 = rows[1].find_all('td')[1].text.strip()[6:] if len(rows[1].find_all('td')) > 1 else "" # Remove "Code: "
            return f"{value_1}, {value_2}".strip(", ")
        return ""

    def _extract_weight_from_soup(self, soup):
        if not soup: return '0'
        table_sm = soup.find('table', class_='table-sm')
        if table_sm:
            all_rows = table_sm.find_all('tr')
            if len(all_rows) > 2:
                cells_in_third_row = all_rows[2].find_all('td')
                if len(cells_in_third_row) > 1:
                    try:
                        weight_grams = float(cells_in_third_row[1].text.strip())
                        return str(weight_grams / 1000)  # Convert to kg
                    except ValueError:
                        logging.warning(f"Could not parse weight from ePER: '{cells_in_third_row[1].text.strip()}'")
        return '0'

    def _extract_eper_price_str_from_soup(self, soup):
        if not soup: return None
        div_prices_tab_pane = soup.find('div', id='prices-tab-pane')
        if div_prices_tab_pane:
            germany_tr = div_prices_tab_pane.find('td', string='Germany')
            if germany_tr and germany_tr.find_next_sibling('td'):
                price_text = germany_tr.find_next_sibling('td').text.strip()
                price_cleaned = re.sub(r'[EUR\s]', '', price_text).replace(',', '.') # Normalize price string
                try:
                    float(price_cleaned) # Validate if it's a number
                    return price_cleaned
                except ValueError:
                    logging.warning(f"Could not parse ePER price: {price_text} (cleaned: {price_cleaned})")
        return None

    @staticmethod
    def _normalize_car_name(name):
        if not isinstance(name, str): return ""
        name = name.upper()
        special_names = {'N.DELTA': 'DELTA', "DUCATO'94": 'DUCATO', "PUNTO BZ": "PUNTO", "PUNTO TB.DS": "PUNTO"}
        for special, normal in special_names.items():
            name = name.replace(special, normal)
        return name

    def _extract_fitting_cars_from_soup(self, soup):
        if not soup: return []
        div_drawings_tab_pane = soup.find('div', id='drawings-tab-pane')
        fitting_cars = []
        if div_drawings_tab_pane:
            tr_elements = div_drawings_tab_pane.find_all('tr')
            extracted_texts = [tr.find('td').get_text(strip=True) for tr in tr_elements if tr.find('td')]
            for text in extracted_texts:
                normalized_text = self._normalize_car_name(text)
                found_brand_model = False
                for brand, models in self.car_brands.items():
                    if brand in normalized_text: # Check if brand is in the text first
                        for model in models:
                            # Ensure model is a whole word or significant part
                            if re.search(r'\b' + re.escape(model) + r'\b', normalized_text) or model in normalized_text:
                                fitting_cars.append(f"{brand} {model}")
                                found_brand_model = True
                                break
                        if found_brand_model: break
                if not found_brand_model: # Fallback: check if model name is present as a word
                    for brand, models in self.car_brands.items():
                        for model in models:
                            if model in normalized_text.split(): # Simpler check if model name is one of the words
                                 fitting_cars.append(f"{brand} {model}")
                                 break
        return list(dict.fromkeys(fitting_cars)) # Remove duplicates

    def _extract_comparison_numbers_from_soup(self, soup, tab_id):
        if not soup: return []
        div_element = soup.find('div', id=tab_id)
        if not div_element: return []
        tr_elements = div_element.find_all('tr')
        return [
            tr.find_all('td')[2].text.strip()
            for tr in tr_elements
            if len(tr.find_all('td')) >= 3 and tr.find_all('td')[2] and tr.find_all('td')[2].text.strip()
        ]

    def get_part_details(self, part_number):
        logging.info(f"Fetching ePER data for primary part number: {part_number}...")
        primary_soup = self._fetch_soup(part_number)

        # Initial values if primary soup fails
        initial_title_base = f"OEM {part_number}"
        initial_eper_price_str = None
        initial_weight_kg = '0'
        initial_fitting_cars = []
        initial_comparison_numbers = [part_number]

        if not primary_soup:
            logging.warning(f"Could not fetch initial ePER data for {part_number}. Proceeding with limited info.")
            # Construct the comprehensive summary even with limited data
            summary_lines_fallback = [
                f"Bezeichnung: {initial_title_base}",
                f"Teilenummer: {part_number}",
                f"Preis (EUR): Nicht verfügbar",
                f"Gewicht: Nicht verfügbar",
                f"Passende Fahrzeuge: Keine Daten",
                f"Vergleichsnummern: {len(initial_comparison_numbers)} (nur angefragte Nummer)"
            ]
            comprehensive_summary_fallback = "\n".join(summary_lines_fallback)
            return {
                'part_number': part_number, 'eper_price_str': initial_eper_price_str, 'weight_kg': initial_weight_kg,
                'fitting_cars': initial_fitting_cars, 'comparison_numbers': initial_comparison_numbers,
                'title_base_description': comprehensive_summary_fallback,
                'title': initial_title_base # Fallback title
            }

        # final_title_base will store the actual part description from ePER
        final_title_base = self._extract_title_from_soup(primary_soup)
        final_eper_price_str = self._extract_eper_price_str_from_soup(primary_soup)
        final_weight_kg = self._extract_weight_from_soup(primary_soup)
        
        fitting_cars_from_primary = self._extract_fitting_cars_from_soup(primary_soup)
        all_fitting_cars = set(fitting_cars_from_primary)

        pre_comp_nums_of_primary = self._extract_comparison_numbers_from_soup(primary_soup, 'previous-tab-pane')
        initial_post_comp_nums_of_primary = self._extract_comparison_numbers_from_soup(primary_soup, 'replacements-tab-pane')

        parts_to_process_queue = list(dict.fromkeys(initial_post_comp_nums_of_primary))
        processed_parts_for_data_aggregation = {part_number}
        all_eventual_replacement_part_numbers = set(initial_post_comp_nums_of_primary)

        current_queue_index = 0
        while current_queue_index < len(parts_to_process_queue):
            comp_num_to_investigate = parts_to_process_queue[current_queue_index]
            current_queue_index += 1

            if comp_num_to_investigate in processed_parts_for_data_aggregation:
                continue

            logging.info(f"Processing replacement part: {comp_num_to_investigate} for data & its own replacements...")
            comp_soup = self._fetch_soup(comp_num_to_investigate)
            processed_parts_for_data_aggregation.add(comp_num_to_investigate)
            all_eventual_replacement_part_numbers.add(comp_num_to_investigate)

            if comp_soup:
                all_fitting_cars.update(self._extract_fitting_cars_from_soup(comp_soup))
                if not final_eper_price_str:
                    price_from_comp = self._extract_eper_price_str_from_soup(comp_soup)
                    if price_from_comp:
                        final_eper_price_str = price_from_comp
                        logging.info(f"Using price from replacement {comp_num_to_investigate}: {final_eper_price_str}")
                if final_weight_kg == '0' or not final_weight_kg:
                    weight_from_comp = self._extract_weight_from_soup(comp_soup)
                    if weight_from_comp and weight_from_comp != '0':
                        final_weight_kg = weight_from_comp
                        logging.info(f"Using weight from replacement {comp_num_to_investigate}: {final_weight_kg}")
                if not final_title_base: # If primary title was empty, try to get from replacement
                    title_from_comp = self._extract_title_from_soup(comp_soup)
                    if title_from_comp:
                        final_title_base = title_from_comp
                        logging.info(f"Using title base from replacement {comp_num_to_investigate}: '{title_from_comp}'")
                
                further_replacements = self._extract_comparison_numbers_from_soup(comp_soup, 'replacements-tab-pane')
                for further_rep_num in further_replacements:
                    all_eventual_replacement_part_numbers.add(further_rep_num)
                    if further_rep_num not in processed_parts_for_data_aggregation and \
                       further_rep_num not in parts_to_process_queue:
                        parts_to_process_queue.append(further_rep_num)
        
        final_output_comparison_numbers = list(dict.fromkeys(
            [part_number] + pre_comp_nums_of_primary + list(all_eventual_replacement_part_numbers)
        ))
        
        needs_price_check = not final_eper_price_str
        needs_weight_check = (final_weight_kg == '0' or not final_weight_kg)
        needs_title_check = not final_title_base # Check if ePER description is still missing

        if needs_price_check or needs_weight_check or needs_title_check:
            for comp_num in pre_comp_nums_of_primary:
                if comp_num == part_number or comp_num in processed_parts_for_data_aggregation:
                    continue
                if not (needs_price_check or needs_weight_check or needs_title_check): # Re-check if all filled
                    break
                
                logging.info(f"Processing previous part {comp_num} for still missing data...")
                comp_soup = self._fetch_soup(comp_num)
                if comp_soup:
                    if needs_price_check and not final_eper_price_str:
                        price_from_comp = self._extract_eper_price_str_from_soup(comp_soup)
                        if price_from_comp:
                            final_eper_price_str = price_from_comp
                            logging.info(f"Using price from previous part {comp_num}: {final_eper_price_str}")
                            needs_price_check = False
                    if needs_weight_check and (final_weight_kg == '0' or not final_weight_kg):
                        weight_from_comp = self._extract_weight_from_soup(comp_soup)
                        if weight_from_comp and weight_from_comp != '0':
                            final_weight_kg = weight_from_comp
                            logging.info(f"Using weight from previous part {comp_num}: {final_weight_kg}")
                            needs_weight_check = False
                    if needs_title_check and not final_title_base:
                        title_from_comp = self._extract_title_from_soup(comp_soup)
                        if title_from_comp:
                            final_title_base = title_from_comp
                            logging.info(f"Using title base from previous part {comp_num}: '{title_from_comp}'")
                            needs_title_check = False
        
        final_fitting_cars_list = list(all_fitting_cars)

        # Construct the short title for eBay etc.
        title_cars_suffix = ""
        if final_fitting_cars_list:
            non_nuovo_cars = [car for car in final_fitting_cars_list if car.upper() != 'NUOVO']
            cars_for_title_suffix = non_nuovo_cars if non_nuovo_cars else final_fitting_cars_list
            if cars_for_title_suffix:
                title_cars_suffix = cars_for_title_suffix[0]
                if len(cars_for_title_suffix) > 1:
                    title_cars_suffix += f" {cars_for_title_suffix[1]}"
        
        title_components = []
        # Use the actual ePER description for the short title if available
        actual_eper_description = final_title_base if final_title_base else f"OEM {part_number}"
        if final_title_base: # Use the ePER name if available
             title_components.append(final_title_base)
        title_components.append(f"OEM {part_number}")
        if title_cars_suffix:
            title_components.append(title_cars_suffix)
        
        final_title_str = " ".join(title_components).strip().replace("  ", " ")
        if len(final_title_str) > 80:
            final_title_str = final_title_str[:77].strip() + "..."

        # --- Construct the comprehensive summary for 'title_base_description' ---
        summary_lines = []
        
        # Use the collected ePER description or a default if it's still empty
        eper_desc_for_summary = final_title_base if final_title_base else "Nicht spezifiziert"
        summary_lines.append(f"Bezeichnung (ePER): {eper_desc_for_summary}")
        summary_lines.append(f"Teilenummer (Anfrage): {part_number}")
        summary_lines.append(f"Preis (EUR): {final_eper_price_str if final_eper_price_str else 'Nicht verfügbar'}")
        
        weight_display = 'Nicht verfügbar'
        if final_weight_kg and final_weight_kg != '0': # Ensure weight is valid and not '0'
            weight_display = f"{final_weight_kg} kg"
        summary_lines.append(f"Gewicht: {weight_display}")

        if final_fitting_cars_list:
            car_summary = f"{len(final_fitting_cars_list)} Modell(e)"
            if len(final_fitting_cars_list) > 0:
                car_examples = ", ".join(final_fitting_cars_list[:3]) # Show up to 3 examples
                car_summary += f" (z.B. {car_examples}{'...' if len(final_fitting_cars_list) > 3 else ''})"
            summary_lines.append(f"Passende Fahrzeuge: {car_summary}")
        else:
            summary_lines.append("Passende Fahrzeuge: Keine Daten")

        if final_output_comparison_numbers:
            comp_summary_count = len(final_output_comparison_numbers)
            # Filter out the original part_number for display of examples, if it's in the list
            actual_comps_examples = [cn for cn in final_output_comparison_numbers if cn != part_number][:3]
            
            comp_display_text = f"{comp_summary_count} Nummer(n) gefunden"
            if actual_comps_examples:
                comp_display_text += f" (inkl. {', '.join(actual_comps_examples)}{'...' if len(final_output_comparison_numbers) > 3 and len(actual_comps_examples) == 3 else ''})"
            elif comp_summary_count == 1 and final_output_comparison_numbers[0] == part_number:
                comp_display_text = f"1 (nur angefragte Nummer)"
            summary_lines.append(f"Vergleichs-/Ersatznummern: {comp_display_text}")
        else:
            summary_lines.append("Vergleichs-/Ersatznummern: Keine Daten")

        comprehensive_summary_str = "\n".join(summary_lines)

        return {
            'part_number': part_number,
            'eper_price_str': final_eper_price_str,
            'weight_kg': final_weight_kg,
            'fitting_cars': final_fitting_cars_list,
            'comparison_numbers': final_output_comparison_numbers,
            'title': final_title_str, # Der kurze Titel (z.B. für eBay)
            'title_base_description': comprehensive_summary_str # Die ausführliche Zusammenfassung
        }

# Example usage:
# Configure logging if you want to see the info messages
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# handler = EPERHandler("7796374") # Example part number
# print("--- Handler Data ---")
# for key, value in handler.data.items():
#    if key == 'title_base_description':
#        print(f"\n{key}:\n{value}\n")
#    else:
#        print(f"{key}: {value}")

# handler_2 = EPERHandler("98446492") # Example part number with 2nd order replacements
# print("\n\n--- Handler_2 Data ---")
# for key, value in handler_2.data.items():
#    if key == 'title_base_description':
#        print(f"\n{key}:\n{value}\n")
#    else:
#        print(f"{key}: {value}")
