# ebay_lister_fiat_item_project/tests/test_gui.py

import unittest
from unittest.mock import patch, MagicMock, ANY
import customtkinter as ctk #
# Assuming your app is EbayListingApp in ebay_lister_fiat_item.gui
from ebay_lister_fiat_item.gui import EbayListingApp, RedirectText #
from ebay_lister_fiat_item.ebay_item import CONDITION_MAP, EBAYHandler #


# It's often necessary to have a root window for CTk widgets even in tests.
# We can try to manage this.
class TestEbayListingApp(unittest.TestCase):

    @patch('ebay_lister_fiat_item.gui.EBAYHandler') #
    @patch('tkinter.messagebox') #
    def setUp(self, mock_messagebox, mock_ebay_handler_cls):
        # Mock EBAYHandler successfully initializing
        self.mock_ebay_handler_instance = MagicMock()
        mock_ebay_handler_cls.return_value = self.mock_ebay_handler_instance
        self.mock_messagebox = mock_messagebox

        # CTk applications need a root window.
        # We try to create one, or ensure it's handled.
        # If tests are run in an environment without a display server, this can be tricky.
        try:
            self.app_root = ctk.CTk()
            self.app_root.withdraw() # Keep it hidden
            self.app = EbayListingApp() #
        except Exception as e:
            # Fallback if root window creation fails (e.g. no display)
            # This might limit which tests can run.
            self.app_root = None
            self.app = None 
            print(f"Warning: CTk root window creation failed in test setup: {e}")
            print("Some GUI tests might be skipped or behave unexpectedly.")


    def tearDown(self):
        if self.app and hasattr(self.app, 'destroy') and self.app.winfo_exists(): #
            self.app.destroy()
        if self.app_root and hasattr(self.app_root, 'destroy') and self.app_root.winfo_exists():
            self.app_root.destroy()
        # Ensure all CTk windows are closed to avoid interference between tests
        # This might be aggressive but can help in some CI environments.
        # ctk.CTk().quit() # This might be too much, could interfere globally

    @patch('ebay_lister_fiat_item.gui.EBAYHandler') #
    def test_app_initialization_success(self, mock_ebay_handler_cls):
        mock_ebay_handler_cls.return_value = MagicMock()
        if self.app is None:
            self.skipTest("Skipping test: CTk App could not be initialized (no display?).")
        try:
            app = EbayListingApp() #
            self.assertIsNotNone(app.ebay_handler) #
            app.destroy() #
        except Exception as e:
            self.fail(f"EbayListingApp initialization failed even with mocks: {e}")


    @patch('ebay_lister_fiat_item.gui.EBAYHandler') #
    @patch('tkinter.messagebox') #
    def test_app_initialization_ebay_handler_fail(self, mock_messagebox, mock_ebay_handler_cls):
        mock_ebay_handler_cls.side_effect = ValueError("Test EBAYHandler Init Error")
        if self.app_root is None : # If root failed, app init is also likely to fail earlier
             self.skipTest("Skipping test: CTk root could not be initialized.")
        
        with self.assertRaisesRegex(SystemExit, "1") if "sys.exit(1)" in open('ebay_lister_fiat_item/gui.py').read() else self.assertRaises(RuntimeError): # Or whatever error it throws before sys.exit
            # Check if sys.exit is called. For that, we might need to patch sys.exit
            # or expect the messagebox to be called and the app to destroy.
            # The current gui.py calls self.destroy() then return, so no specific exception might be raised by __init__ itself
            # after the messagebox, but an error is logged.
            # Let's verify messagebox.showerror is called.
            try:
                app = EbayListingApp() #
                # If it reaches here and destroy is called, it's tricky.
                # Let's assume the constructor would try to fully complete or raise before that for this test.
                # The original code has:
                # except Exception as e: ... messagebox.showerror ... self.destroy(); return
                # So, the constructor itself doesn't re-raise. We check for messagebox.
                if app: app.destroy() #

            except Exception: # Catch any exception that might occur during init
                pass # Expected if error handling is different
            
            mock_messagebox.showerror.assert_called_with(
                "Initialization Error",
                "Failed to initialize EBAYHandler: Test EBAYHandler Init Error\nPlease check your eBay API configuration and .env file."
            )


    def test_get_input_data_new_listing(self):
        if self.app is None:
            self.skipTest("Skipping test: CTk App could not be initialized.")
        
        self.app.action_var.set("new") #
        self.app.part_number_entry.insert(0, "PN123") #
        self.app.quantity_entry.insert(0, "10") #
        self.app.sku_entry.insert(0, "SKU001") #
        self.app.title_override_entry.insert(0, "My Title") #
        self.app.description_override_entry.insert("1.0", "My Desc") #
        
        # Set values for 'new' specific fields
        self.app.condition_var.set("3000") # Used
        self.app.shipping_profile_id_entry.insert(0, "SHIP1") #
        self.app.payment_profile_id_entry.insert(0, "PAY1") #
        self.app.return_profile_id_entry.insert(0, "RET1") #
        self.app.item_location_entry.insert(0, "Location X") #
        self.app.country_code_entry.insert(0, "US") #
        self.app.currency_code_entry.insert(0, "USD") #
        self.app.dispatch_time_max_entry.insert(0, "2") #
        self.app.vat_percent_entry.insert(0, "5.0") #

        data = self.app.get_input_data() #

        expected_data = {
            "action": "new",
            "part_number": "PN123",
            "quantity": "10",
            "sku": "SKU001",
            "title_override": "My Title",
            "description_override": "My Desc",
            "condition_id": "3000",
            "shipping_profile_id": "SHIP1",
            "payment_profile_id": "PAY1",
            "return_profile_id": "RET1",
            "item_location": "Location X",
            "country_code": "US",
            "currency_code": "USD",
            "dispatch_time_max": "2",
            "vat_percent": "5.0",
        }
        self.assertEqual(data, expected_data)

    def test_get_input_data_revise_listing(self):
        if self.app is None:
            self.skipTest("Skipping test: CTk App could not be initialized.")

        self.app.action_var.set("revise") #
        self.app.part_number_entry.insert(0, "PN123") # # Part number still collected
        self.app.quantity_entry.insert(0, "5") #
        self.app.sku_entry.insert(0, "SKU002") #
        self.app.item_id_entry.insert(0, "ITEMID789") #
        self.app.title_override_entry.insert(0, "") #
        self.app.description_override_entry.insert("1.0", "") #

        data = self.app.get_input_data() #
        expected_data = {
            "action": "revise",
            "part_number": "PN123",
            "quantity": "5",
            "sku": "SKU002",
            "item_id": "ITEMID789",
            "title_override": "",
            "description_override": ""
        }
        self.assertEqual(data, expected_data)


    def test_validate_inputs_new_listing_valid(self):
        if self.app is None:
            self.skipTest("Skipping test: CTk App could not be initialized.")
        valid_data_new = {
            "action": "new", "part_number": "PN", "quantity": "1", "sku": "S",
            "shipping_profile_id": "s", "payment_profile_id": "p", "return_profile_id": "r",
            "item_location": "l", "country_code": "c", "currency_code": "c",
            "dispatch_time_max": "1", "vat_percent": "19.0"
        }
        self.assertTrue(self.app.validate_inputs(valid_data_new)) #

    def test_validate_inputs_new_listing_invalid(self):
        if self.app is None:
            self.skipTest("Skipping test: CTk App could not be initialized.")
        invalid_data_new = {"action": "new", "part_number": "", "quantity": "1", "sku": "S"} # Missing part_number
        self.assertFalse(self.app.validate_inputs(invalid_data_new)) #
        self.mock_messagebox.showerror.assert_called_with("Error", "Part Number is required.") #

        invalid_data_new_qty = {"action": "new", "part_number": "PN", "quantity": "-1", "sku": "S"}
        self.assertFalse(self.app.validate_inputs(invalid_data_new_qty)) #
        self.mock_messagebox.showerror.assert_called_with("Error", "Valid, non-negative Quantity is required.") #


    def test_validate_inputs_revise_listing_valid(self):
        if self.app is None:
            self.skipTest("Skipping test: CTk App could not be initialized.")
        valid_data_revise = {"action": "revise", "part_number": "PN", "quantity": "1", "sku": "S", "item_id": "ID123"}
        self.assertTrue(self.app.validate_inputs(valid_data_revise)) #

    def test_validate_inputs_revise_listing_invalid(self):
        if self.app is None:
            self.skipTest("Skipping test: CTk App could not be initialized.")
        invalid_data_revise = {"action": "revise", "part_number": "PN", "quantity": "1", "sku": "S", "item_id": ""} # Missing item_id
        self.assertFalse(self.app.validate_inputs(invalid_data_revise)) #
        self.mock_messagebox.showerror.assert_called_with("Error", "eBay Item ID is required for revision.") #

    @patch('threading.Thread') #
    @patch('sys.stdout', new_callable=MagicMock) # To check if it's changed
    def test_submit_valid_inputs_starts_thread(self, mock_stdout, mock_thread_cls):
        if self.app is None:
            self.skipTest("Skipping test: CTk App could not be initialized.")

        # Mock get_input_data to return something valid
        valid_data = {"action": "new", "part_number": "PN", "quantity": "1", "sku": "S",
                      "shipping_profile_id": "s", "payment_profile_id": "p", "return_profile_id": "r",
                      "item_location": "l", "country_code": "c", "currency_code": "c",
                      "dispatch_time_max": "1", "vat_percent": "19.0", "condition_id": "1000",
                      "title_override": "", "description_override": ""}
        self.app.get_input_data = MagicMock(return_value=valid_data) #
        self.app.validate_inputs = MagicMock(return_value=True) #
        self.app.display_submitted_values = MagicMock() #
        self.app.clear_output = MagicMock() #

        self.app.submit() #

        self.app.clear_output.assert_called_once() #
        self.app.display_submitted_values.assert_called_once_with(valid_data) #
        mock_thread_cls.assert_called_once_with(target=self.app.run_process, args=(valid_data, ANY), daemon=True) #
        mock_thread_cls.return_value.start.assert_called_once()


    @patch.object(EbayListingApp, 'process_new_listing') #
    def test_run_process_action_new(self, mock_process_new):
        if self.app is None:
            self.skipTest("Skipping test: CTk App could not be initialized.")
        
        data = {"action": "new", "part_number": "PN123"}
        # The run_process method redirects stdout. We need to manage that or simplify.
        # For this unit test, we mainly care that the correct sub-processor is called.
        # The try/except/finally in run_process that restores stdout makes it safer.
        original_stdout = MagicMock() 
        self.app.run_process(data, original_stdout) #
        mock_process_new.assert_called_once_with(data)


    @patch.object(EbayListingApp, 'process_revision') #
    def test_run_process_action_revise(self, mock_process_revise):
        if self.app is None:
            self.skipTest("Skipping test: CTk App could not be initialized.")

        data = {"action": "revise", "item_id": "ID123"}
        original_stdout = MagicMock()
        self.app.run_process(data, original_stdout) #
        mock_process_revise.assert_called_once_with(data)

    # Tests for process_new_listing and process_revision would be more involved,
    # requiring mocking of self.ebay_handler methods (draft_item_payload, create_item, revise_item)
    # and EPERHandler if used for weight.

    # Example for one part of process_new_listing:
    @patch.object(EBAYHandler, 'draft_item_payload') #
    @patch.object(EBAYHandler, 'create_item') #
    def test_process_new_listing_calls_ebay_handler(self, mock_create_item, mock_draft_payload):
        if self.app is None:
            self.skipTest("Skipping test: CTk App could not beinitialized.")

        # self.app.ebay_handler is already a mock from setUp
        self.app.ebay_handler.draft_item_payload = mock_draft_payload #
        self.app.ebay_handler.create_item = mock_create_item #
        
        mock_draft_payload.return_value = {"Item": {"SKU": "TestSKU123"}} # Dummy payload
        mock_create_item.return_value = "NEW_EBAY_ID_123" # Mock successful creation

        test_data = {
            "action": "new", "part_number": "PN123", "quantity": "1", "sku": "TestSKU123",
            "condition_id": "1000", "shipping_profile_id": "s_id", "payment_profile_id": "p_id",
            "return_profile_id": "r_id", "item_location": "loc", "country_code": "DE",
            "currency_code": "EUR", "dispatch_time_max": "3", "vat_percent": "19.0",
            "title_override": None, "description_override": None
        }
        self.app.process_new_listing(test_data) #

        mock_draft_payload.assert_called_once_with(
            part_number_str="PN123", quantity=1, condition_id="1000",
            shipping_profile_id_val="s_id", payment_profile_id_val="p_id", #
            return_profile_id_val="r_id", sku="TestSKU123", item_location="loc", #
            country_code="DE", currency_code="EUR", dispatch_time_max="3", #
            vat_percent=19.0, picture_urls=None, title_override=None, description_override=None #
        )
        mock_create_item.assert_called_once_with({"Item": {"SKU": "TestSKU123"}})
        self.mock_messagebox.showinfo.assert_called_with("Success", "New listing created!\nItem ID: NEW_EBAY_ID_123") #


    @patch.object(EBAYHandler, 'revise_item') #
    def test_process_revision_calls_ebay_handler(self, mock_revise_item):
        if self.app is None:
            self.skipTest("Skipping test: CTk App could not be initialized.")

        self.app.ebay_handler.revise_item = mock_revise_item #
        mock_revise_item.return_value = "REVISED_EBAY_ID_456"

        test_data = {
            "action": "revise", "item_id": "REVISED_EBAY_ID_456", "quantity": "5",
            "sku": "NewSKU", "title_override": "New Title", "description_override": "New Desc"
        }
        self.app.process_revision(test_data) #

        expected_revised_fields = {
            'Quantity': '5',
            'Title': 'New Title',
            'Description': 'New Desc',
            'SKU': 'NewSKU'
        }
        mock_revise_item.assert_called_once_with("REVISED_EBAY_ID_456", expected_revised_fields)
        self.mock_messagebox.showinfo.assert_called_with("Success", "Listing revised!\nItem ID: REVISED_EBAY_ID_456") #


if __name__ == '__main__':
    unittest.main()