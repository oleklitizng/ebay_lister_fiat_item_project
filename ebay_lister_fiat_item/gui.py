import customtkinter as ctk
import threading
from tkinter import messagebox
import sys
import logging
from typing import Optional, Dict, List # For type hinting

# Import classes and constants from ebay_item.py
from .ebay_item import EBAYHandler, CONDITION_MAP #
from .scrape_open_eper import EPERHandler



# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler('ebay_lister_gui.log'),
                              logging.StreamHandler(sys.stdout)]) # Also log to stdout for visibility in GUI

class RedirectText:
    def __init__(self, text_widget: ctk.CTkTextbox):
        self.output = text_widget
        self.logger = logging.getLogger() # Get the root logger
        self.log_level = logging.INFO # Or whatever level you redirect

    def write(self, string: str):
        self.output.insert(ctk.END, string)
        self.output.see(ctk.END)
        # Optionally, also send to logger if it's not already happening
        # For instance, if some prints are not going through the logger
        # self.logger.log(self.log_level, string.strip())

    def flush(self):
        pass

class EbayListingApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("eBay Listing Manager Enhanced")
        self.geometry("800x900") # Increased size for new fields
        self.minsize(700, 750)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(8, weight=1) # Adjusted for new layout elements

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        try:
            # Initialize EBAYHandler
            # Ensure your .env file is set up as per ebay_item.py requirements
            # or provide api_config_override
            self.ebay_handler = EBAYHandler()
            logging.info("EBAYHandler initialized successfully.")
        except Exception as e:
            logging.error(f"Failed to initialize EBAYHandler: {e}", exc_info=True)
            messagebox.showerror("Initialization Error", f"Failed to initialize EBAYHandler: {e}\nPlease check your eBay API configuration and .env file.")
            self.destroy() # Close app if EBAYHandler fails
            return


        self.create_widgets()
        self.toggle_fields()

    def create_widgets(self):
        self.action_var = ctk.StringVar(value="new")
        self.create_header()
        self.create_action_frame()
        self.create_input_fields() # Basic item details
        self.create_ebay_details_frame() # eBay specific details like profiles, location etc.
        self.create_condition_menu()
        self.create_item_id_entry()
        self.create_override_fields() # Optional overrides for title/description
        self.create_output_text()
        self.create_button_frame()

    def create_header(self):
        header_frame = ctk.CTkFrame(self)
        header_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        ctk.CTkLabel(header_frame, text="eBay Auto Parts Lister (EBAYHandler Integrated)",
                    font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)

    def create_action_frame(self):
        action_frame = ctk.CTkFrame(self)
        action_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        action_frame.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkLabel(action_frame, text="Action Type:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        radio_frame = ctk.CTkFrame(action_frame, fg_color="transparent")
        radio_frame.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkRadioButton(radio_frame, text="New Listing", variable=self.action_var,
                         value="new", command=self.toggle_fields).pack(side="left", padx=10)
        ctk.CTkRadioButton(radio_frame, text="Revise Listing", variable=self.action_var,
                         value="revise", command=self.toggle_fields).pack(side="left", padx=10)

    def create_input_fields(self):
        input_frame = ctk.CTkFrame(self)
        input_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        input_frame.grid_columnconfigure(1, weight=1)

        fields = [
            ("part_number", "Part Number (OEM)", "Enter OEM part number"),
            ("quantity", "Quantity", "Enter available quantity"),
            ("sku", "SKU (Storage Location)", "Enter your SKU / storage reference") # Changed label for clarity
        ]
        for i, (attr, label, placeholder) in enumerate(fields):
            ctk.CTkLabel(input_frame, text=f"{label}:").grid(row=i, column=0, padx=10, pady=5, sticky="w")
            entry = ctk.CTkEntry(input_frame, placeholder_text=placeholder)
            entry.grid(row=i, column=1, padx=10, pady=5, sticky="ew")
            setattr(self, f"{attr}_entry", entry)

    def create_ebay_details_frame(self):
        self.ebay_details_frame = ctk.CTkFrame(self)
        self.ebay_details_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        self.ebay_details_frame.grid_columnconfigure(1, weight=1)

        # Fields required by draft_item_payload
        ebay_fields = [
            ("shipping_profile_id", "Shipping Profile ID", "Your Shipping Profile ID", "DEFAULT_SHIPPING_PROFILE_ID"), # Placeholder default
            ("payment_profile_id", "Payment Profile ID", "Your Payment Profile ID", "DEFAULT_PAYMENT_PROFILE_ID"),   # Placeholder default
            ("return_profile_id", "Return Profile ID", "Your Return Profile ID", "DEFAULT_RETURN_PROFILE_ID"),     # Placeholder default
            ("item_location", "Item Location", "e.g., City, State", "Syke, Niedersachsen"),
            ("country_code", "Country Code", "e.g., DE, US", "DE"),
            ("currency_code", "Currency Code", "e.g., EUR, USD", "EUR"),
            ("dispatch_time_max", "Dispatch Time Max (days)", "e.g., 3", "3"),
            ("vat_percent", "VAT Percent", "e.g., 19.0 (0 for none)", "19.0")
        ]
        for i, (attr, label, placeholder, default_value) in enumerate(ebay_fields):
            ctk.CTkLabel(self.ebay_details_frame, text=f"{label}:").grid(row=i, column=0, padx=10, pady=5, sticky="w")
            entry = ctk.CTkEntry(self.ebay_details_frame, placeholder_text=placeholder)
            entry.insert(0, default_value) # Pre-fill with default
            entry.grid(row=i, column=1, padx=10, pady=5, sticky="ew")
            setattr(self, f"{attr}_entry", entry)

    def create_condition_menu(self):
        self.condition_frame = ctk.CTkFrame(self)
        self.condition_frame.grid(row=4, column=0, padx=20, pady=10, sticky="ew")
        self.condition_frame.grid_columnconfigure(1, weight=1)
        self.condition_var = ctk.StringVar(value="1000") # Default to 'New'
        ctk.CTkLabel(self.condition_frame, text="Condition:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        condition_options = [(value, key) for key, value in CONDITION_MAP.items()] #
        self.condition_menu = ctk.CTkOptionMenu(
            self.condition_frame,
            variable=self.condition_var,
            values=[option[0] for option in condition_options], # Display names
            command=lambda selection: self.update_condition_id_from_selection(selection, condition_options)
        )
        self.condition_menu.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        # Set initial actual ID based on default selection
        self.update_condition_id_from_selection(CONDITION_MAP["1000"], condition_options)


    def create_item_id_entry(self):
        self.item_id_frame = ctk.CTkFrame(self)
        # Will be gridded by toggle_fields
        self.item_id_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(self.item_id_frame, text="eBay Item ID (for revise):").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.item_id_entry = ctk.CTkEntry(self.item_id_frame, placeholder_text="Enter eBay Item ID to revise")
        self.item_id_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

    def create_override_fields(self):
        self.override_frame = ctk.CTkFrame(self)
        # Will be gridded by toggle_fields
        self.override_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.override_frame, text="Title Override (Optional):").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.title_override_entry = ctk.CTkEntry(self.override_frame, placeholder_text="Leave blank to use EPER title")
        self.title_override_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(self.override_frame, text="Description Override (Optional):").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.description_override_entry = ctk.CTkTextbox(self.override_frame, height=60, wrap="word")
        self.description_override_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")


    def create_output_text(self):
        output_frame = ctk.CTkFrame(self)
        output_frame.grid(row=8, column=0, padx=20, pady=10, sticky="nsew") # Adjusted row
        output_frame.grid_columnconfigure(0, weight=1)
        output_frame.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(output_frame, text="Process Output:").grid(row=0, column=0, padx=10, pady=(10, 0), sticky="w")
        self.output_text = ctk.CTkTextbox(output_frame, height=200, wrap="word")
        self.output_text.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

    def create_button_frame(self):
        button_frame = ctk.CTkFrame(self)
        button_frame.grid(row=9, column=0, padx=20, pady=(10, 20), sticky="ew") # Adjusted row
        ctk.CTkButton(button_frame, text="Submit", command=self.submit,
                    fg_color="#2F7D31", hover_color="#235E23").pack(side="left", padx=10, pady=10, expand=True, fill="x")
        ctk.CTkButton(button_frame, text="Clear All", command=self.clear_all,
                    fg_color="#C62828", hover_color="#951F1F").pack(side="left", padx=10, pady=10, expand=True, fill="x")
        ctk.CTkButton(button_frame, text="Exit", command=self.quit_app,
                    fg_color="#555555", hover_color="#333333").pack(side="left", padx=10, pady=10, expand=True, fill="x")

    def toggle_fields(self):
        action = self.action_var.get()
        if action == "revise":
            self.item_id_frame.grid(row=5, column=0, padx=20, pady=10, sticky="ew") # Adjusted row
            self.override_frame.grid(row=6, column=0, padx=20, pady=10, sticky="ew") # Adjusted row
            self.condition_frame.grid_remove()
            self.ebay_details_frame.grid_remove() # Hide eBay details for revise, as we only update specific fields
        else: # new
            self.item_id_frame.grid_remove()
            self.override_frame.grid(row=6, column=0, padx=20, pady=10, sticky="ew") # Adjusted row
            self.condition_frame.grid(row=4, column=0, padx=20, pady=10, sticky="ew") # Adjusted row
            self.ebay_details_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")


    def update_condition_id_from_selection(self, selection_name: str, condition_options: list):
        """Updates self.condition_var to the ID based on the selected display name."""
        for name, id_val in condition_options:
            if name == selection_name:
                self.condition_var.set(id_val)
                return
        # Fallback if something goes wrong, though OptionMenu should prevent this
        if condition_options:
            self.condition_var.set(condition_options[0][1])


    def submit(self):
        input_data = self.get_input_data()
        if not self.validate_inputs(input_data):
            return

        self.clear_output()
        self.display_submitted_values(input_data)

        original_stdout = sys.stdout
        redirect_handler = RedirectText(self.output_text)
        sys.stdout = redirect_handler
        # Configure root logger to also use this handler for GUI output
        # This ensures logging messages also appear in the GUI textbox
        logging.getLogger().addHandler(logging.StreamHandler(redirect_handler))


        thread = threading.Thread(target=self.run_process, args=(input_data, original_stdout), daemon=True)
        thread.start()

    def get_input_data(self) -> dict:
        data = {
            "action": self.action_var.get(),
            "part_number": self.part_number_entry.get().strip(),
            "quantity": self.quantity_entry.get().strip(),
            "sku": self.sku_entry.get().strip(), #
            "title_override": self.title_override_entry.get().strip(),
            "description_override": self.description_override_entry.get("1.0", ctk.END).strip(),
        }
        if data["action"] == "new":
            data.update({
                "condition_id": self.condition_var.get(), # Already the ID
                "shipping_profile_id": self.shipping_profile_id_entry.get().strip(),
                "payment_profile_id": self.payment_profile_id_entry.get().strip(),
                "return_profile_id": self.return_profile_id_entry.get().strip(),
                "item_location": self.item_location_entry.get().strip(),
                "country_code": self.country_code_entry.get().strip(),
                "currency_code": self.currency_code_entry.get().strip(),
                "dispatch_time_max": self.dispatch_time_max_entry.get().strip(),
                "vat_percent": self.vat_percent_entry.get().strip(),
            })
        else: # revise
            data["item_id"] = self.item_id_entry.get().strip()
        return data

    def validate_inputs(self, data: dict) -> bool:
        if not data["part_number"]:
            messagebox.showerror("Error", "Part Number is required.")
            return False
        if not data["quantity"] or not data["quantity"].isdigit() or int(data["quantity"]) < 0:
            messagebox.showerror("Error", "Valid, non-negative Quantity is required.")
            return False
        if not data["sku"]:
            messagebox.showerror("Error", "SKU (Storage Location) is required.") #
            return False

        if data["action"] == "new":
            required_new_fields = ["shipping_profile_id", "payment_profile_id", "return_profile_id",
                                   "item_location", "country_code", "currency_code", "dispatch_time_max"]
            for field in required_new_fields:
                if not data[field]:
                    messagebox.showerror("Error", f"{field.replace('_', ' ').title()} is required for new listings.")
                    return False
            if data["vat_percent"]:
                try:
                    float(data["vat_percent"])
                except ValueError:
                    messagebox.showerror("Error", "VAT Percent must be a valid number.")
                    return False
        elif data["action"] == "revise":
            if not data["item_id"]:
                messagebox.showerror("Error", "eBay Item ID is required for revision.")
                return False
        return True

    def clear_output(self):
        self.output_text.delete("1.0", ctk.END)

    def clear_all(self):
        self.clear_output()
        self.part_number_entry.delete(0, ctk.END)
        self.quantity_entry.delete(0, ctk.END)
        self.sku_entry.delete(0, ctk.END) #
        self.item_id_entry.delete(0, ctk.END)
        self.title_override_entry.delete(0, ctk.END)
        self.description_override_entry.delete("1.0", ctk.END)

        # Clear new fields too
        if hasattr(self, 'shipping_profile_id_entry'): # Check if fields exist
            self.shipping_profile_id_entry.delete(0, ctk.END)
            self.payment_profile_id_entry.delete(0, ctk.END)
            self.return_profile_id_entry.delete(0, ctk.END)
            self.item_location_entry.delete(0, ctk.END)
            self.country_code_entry.delete(0, ctk.END)
            self.currency_code_entry.delete(0, ctk.END)
            self.dispatch_time_max_entry.delete(0, ctk.END)
            self.vat_percent_entry.delete(0, ctk.END)
            # Re-populate defaults for eBay details
            self.shipping_profile_id_entry.insert(0, "DEFAULT_SHIPPING_PROFILE_ID")
            self.payment_profile_id_entry.insert(0, "DEFAULT_PAYMENT_PROFILE_ID")
            self.return_profile_id_entry.insert(0, "DEFAULT_RETURN_PROFILE_ID")
            self.item_location_entry.insert(0, "Syke, Niedersachsen")
            self.country_code_entry.insert(0, "DE")
            self.currency_code_entry.insert(0, "EUR")
            self.dispatch_time_max_entry.insert(0, "3")
            self.vat_percent_entry.insert(0, "19.0")


    def display_submitted_values(self, data: dict):
        output = "Submitted values:\n"
        for key, value in data.items():
            if key == "condition_id" and data['action'] == 'new':
                output += f"Condition: {CONDITION_MAP.get(value, 'Unknown ID: '+str(value))} ({value})\n" #
            elif key == "description_override":
                 output += f"{key.replace('_', ' ').title()}: {'Provided (see below)' if value else 'Not provided'}\n"
                 if value: output += f"----\n{value}\n----\n"
            else:
                output += f"{key.replace('_', ' ').title()}: {value}\n"
        output += "\nProcessing... Please wait.\n\n"
        logging.info(output) # Use logging so it appears in the textbox via RedirectText


    def run_process(self, data: dict, original_stdout):
        try:
            logging.info(f"Starting process for action: {data['action']}")
            if data['action'] == 'new':
                self.process_new_listing(data)
            elif data['action'] == 'revise':
                self.process_revision(data)
            logging.info("\nProcess completed successfully!")
        except ValueError as e:
            logging.error(f"Validation or Business Logic Error: {e}", exc_info=True)
            messagebox.showerror("Error", str(e)) # Show detailed error from EBAYHandler/EPERHandler
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}", exc_info=True)
            messagebox.showerror("Unexpected Error", f"An unexpected error occurred: {e}")
        finally:
            sys.stdout = original_stdout # Restore original stdout
            # Remove the temporary handler from the root logger
            root_logger = logging.getLogger()
            for handler in root_logger.handlers:
                if isinstance(handler.stream, RedirectText): # type: ignore
                    root_logger.removeHandler(handler)
                    break


    def process_new_listing(self, data: dict):
        logging.info(f"Processing new listing for Part Number: {data['part_number']}")

        part_number_str = data['part_number']
        quantity = int(data['quantity'])
        condition_id = data['condition_id'] # This is already the ID
        sku = data['sku'] #

        # These are now collected from GUI
        shipping_profile_id_val = data['shipping_profile_id']
        payment_profile_id_val = data['payment_profile_id']
        return_profile_id_val = data['return_profile_id']
        item_location = data['item_location']
        country_code = data['country_code']
        currency_code = data['currency_code']
        dispatch_time_max = data['dispatch_time_max']
        vat_percent = float(data['vat_percent']) if data['vat_percent'] else 0.0

        title_override = data['title_override'] if data['title_override'] else None
        description_override = data['description_override'] if data['description_override'] else None

        # Get weight using EPERHandler to determine shipping profile if complex logic was needed
        # However, draft_item_payload does not use weight directly.
        # get_shipping_profile_id_by_weight IS a static method of EBAYHandler
        # So we can call it if we fetch weight. For now, we are taking shipping_profile_id from user input.
        # If you want to use get_shipping_profile_id_by_weight:
        # try:
        #     eper_item_for_weight = EPERHandler(part_number_str)
        #     weight_kg = eper_item_for_weight.get_item("weight_kg_float") # Assuming this method exists
        #     if weight_kg is None: raise ValueError("Could not fetch weight for part.")
        #     logging.info(f"Fetched weight: {weight_kg}kg for part {part_number_str}")
        #     # You'd need a default shipping profile ID for the call below
        #     shipping_profile_id_val = self.ebay_handler.get_shipping_profile_id_by_weight(weight_kg, data['shipping_profile_id'])
        #     logging.info(f"Determined Shipping Profile ID: {shipping_profile_id_val}")
        # except Exception as e:
        #     logging.error(f"Could not determine shipping profile from weight: {e}")
        #     # Fallback to user input or raise error
        #     # shipping_profile_id_val = data['shipping_profile_id'] (already set)


        logging.info("Preparing item payload...")
        payload = self.ebay_handler.draft_item_payload(
            part_number_str=part_number_str,
            quantity=quantity,
            condition_id=condition_id,
            shipping_profile_id_val=shipping_profile_id_val,
            payment_profile_id_val=payment_profile_id_val,
            return_profile_id_val=return_profile_id_val,
            sku=sku,
            item_location=item_location,
            country_code=country_code,
            currency_code=currency_code,
            dispatch_time_max=dispatch_time_max,
            vat_percent=vat_percent,
            # picture_urls will use default from ebay_item.py if None
            title_override=title_override,
            description_override=description_override
        )

        logging.info("Creating item on eBay...")
        item_id = self.ebay_handler.create_item(payload)

        if item_id:
            logging.info(f"Successfully created new listing with eBay Item ID: {item_id}")
            messagebox.showinfo("Success", f"New listing created!\nItem ID: {item_id}")
        else:
            logging.error("Failed to create new listing. Check logs for details.")
            # Error already logged by EBAYHandler, messagebox shown by run_process exception handling

    def process_revision(self, data: dict):
        logging.info(f"Processing revision for eBay Item ID: {data['item_id']}")
        item_id_to_revise = data['item_id']
        revised_fields = {}

        if data['quantity']:
            revised_fields['Quantity'] = str(data['quantity']) # Must be string for API

        # Check for overrides
        if data['title_override']:
            title = data['title_override'][:80] # Enforce 80 char limit
            revised_fields['Title'] = title
            logging.info(f"Revising Title to: {title}")

        if data['description_override']:
            revised_fields['Description'] = data['description_override']
            logging.info("Revising Description with provided override.")

        if data['sku']: # SKU can also be revised
             revised_fields['SKU'] = data['sku'] #

        # Add more revisable fields here if needed, e.g., StartPrice, ConditionID (if allowed)
        # revised_fields['StartPrice'] = new_price_str

        if not revised_fields:
            logging.warning("No fields were marked for revision beyond potentially SKU if it was changed.")
            messagebox.showwarning("Revision", "No changes specified for revision (except possibly SKU). If you only changed SKU, it will be updated.")
            # Still proceed if only SKU changed, as SKU is always passed in data

        if 'SKU' not in revised_fields and data['sku']: # if sku field exists and is filled
             # check if original SKU needs to be fetched to compare if it actually changed
             # For simplicity, we are allowing SKU to be "revised" even if it's the same
             # as it's part of the main input fields. If you want to be more precise,
             # you'd fetch the item, compare SKU, and only add to revised_fields if different.
             pass


        if not revised_fields and not data['sku']: # If SKU is also empty, then truly nothing to revise
             messagebox.showinfo("No Revision", "No information provided to revise.")
             return


        logging.info(f"Revising item with fields: {revised_fields}")
        result_item_id = self.ebay_handler.revise_item(item_id_to_revise, revised_fields)

        if result_item_id:
            logging.info(f"Successfully revised listing for Item ID: {result_item_id}")
            messagebox.showinfo("Success", f"Listing revised!\nItem ID: {result_item_id}")
        else:
            logging.error(f"Failed to revise listing for Item ID: {item_id_to_revise}. Check logs.")
            # Error already logged by EBAYHandler

    def quit_app(self):
        self.quit()
        self.destroy()

def main_gui_app():
    """Main function to launch the eBay Listing App."""
    app = EbayListingApp()
    if app.winfo_exists(): # Check if init was successful
        app.mainloop()

if __name__ == "__main__":
    main_gui_app()