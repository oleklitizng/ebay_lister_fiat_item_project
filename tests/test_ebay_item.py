# ebay_lister_fiat_item_project/tests/test_ebay_item.py

import unittest
from unittest.mock import patch, MagicMock, mock_open
from ebay_lister_fiat_item.ebay_item import EBAYHandler, CONDITION_MAP #
from ebay_lister_fiat_item.api_config import load_ebay_env_config #

# If EPERHandler is in scrape_open_eper.py at the same level as ebay_item.py inside the package
from ebay_lister_fiat_item.scrape_open_eper import EPERHandler #

class MockEbaySDKResponse:
    def __init__(self, ack='Success', data=None, errors=None, reply_dict=None):
        self.ack = ack
        self.reply = MagicMock()
        self.reply.ack = ack
        self.reply.Ack = ack # Some SDK versions use capitalized Ack

        if data:
            for key, value in data.items():
                setattr(self.reply, key, value)

        if errors:
            self.reply.Errors = errors
        else:
            self.reply.Errors = []

        # For findItemsByKeywords response structure
        if reply_dict and 'searchResult' in reply_dict:
            self.reply.searchResult = MagicMock()
            self.reply.searchResult._count = reply_dict['searchResult'].get('_count', '0')
            self.reply.searchResult.item = []
            for item_data in reply_dict['searchResult'].get('item', []):
                mock_item = MagicMock()
                mock_item.primaryCategory.categoryId = item_data['primaryCategory']['categoryId']
                self.reply.searchResult.item.append(mock_item)
        
        if reply_dict and 'Item' in reply_dict : # For GetItem
             self.reply.Item = reply_dict['Item']


        self._reply_dict = reply_dict if reply_dict else {}
        if data:
            self._reply_dict.update(data)


    def dict(self):
        # Ensure ItemID, SKU, Errors are present if they were part of the mock setup
        base_dict = {}
        if hasattr(self.reply, 'ItemID'):
            base_dict['ItemID'] = self.reply.ItemID
        if hasattr(self.reply, 'SKU') and hasattr(self.reply.SKU, 'value'): # Assuming SKU might be an object
            base_dict['SKU'] = self.reply.SKU.value
        elif hasattr(self.reply, 'SKU'):
             base_dict['SKU'] = self.reply.SKU

        if hasattr(self.reply, 'Errors') and self.reply.Errors:
            base_dict['Errors'] = []
            for err in self.reply.Errors:
                error_detail = {}
                if hasattr(err, 'SeverityCode'): error_detail['SeverityCode'] = err.SeverityCode
                if hasattr(err, 'ShortMessage'): error_detail['ShortMessage'] = err.ShortMessage
                if hasattr(err, 'LongMessage'): error_detail['LongMessage'] = err.LongMessage
                base_dict['Errors'].append(error_detail)
        
        if hasattr(self.reply, 'Item'): # For GetItem
            base_dict['Item'] = self.reply.Item


        base_dict.update(self._reply_dict)
        return base_dict

class TestEBAYHandler(unittest.TestCase):

    @patch('ebay_lister_fiat_item.ebay_item.Trading') #
    @patch('ebay_lister_fiat_item.ebay_item.Finding') #
    @patch('ebay_lister_fiat_item.ebay_item.load_ebay_env_config') #
    def setUp(self, mock_load_env, mock_finding_conn, mock_trading_conn):
        # Mock environment configuration
        self.mock_config = {
            'api': 'trading',
            'siteid': '77',
            'appid': 'TEST_APP_ID',
            'certid': 'TEST_CERT_ID',
            'devid': 'TEST_DEV_ID',
            'token': 'TEST_TOKEN',
            'sandbox': False
        }
        mock_load_env.return_value = self.mock_config

        # Mock eBay SDK connections
        self.mock_trading_api = MagicMock()
        self.mock_finding_api = MagicMock()
        mock_trading_conn.return_value = self.mock_trading_api
        mock_finding_conn.return_value = self.mock_finding_api

        self.handler = EBAYHandler() #

    def test_initialization_success(self):
        self.assertIsNotNone(self.handler.api_trading)
        self.assertIsNotNone(self.handler.api_finding)
        self.assertEqual(self.handler.config['appid'], 'TEST_APP_ID')

    @patch('ebay_lister_fiat_item.ebay_item.load_ebay_env_config') #
    def test_initialization_missing_keys(self, mock_load_env):
        mock_load_env.return_value = {'appid': None, 'certid': 'some_cert'} # Missing devid, token
        with self.assertRaisesRegex(ValueError, "eBay API configuration for the following keys is missing"):
            EBAYHandler() #

    @patch('ebay_lister_fiat_item.ebay_item.Finding') #
    @patch('ebay_lister_fiat_item.ebay_item.load_ebay_env_config') #
    def test_get_category_id_found(self, mock_load_env, mock_finding_conn):
        mock_load_env.return_value = self.mock_config
        mock_api_finding = MagicMock()
        mock_finding_conn.return_value = mock_api_finding

        mock_response_data = {
            'searchResult': {
                '_count': '1',
                'item': [{'primaryCategory': {'categoryId': '12345'}}]
            }
        }
        mock_api_finding.execute.return_value = MockEbaySDKResponse(reply_dict=mock_response_data)
        
        handler = EBAYHandler() #
        category_id = handler.get_category_id("TEST_PART_NO") #
        self.assertEqual(category_id, "12345")
        mock_api_finding.execute.assert_called_once_with('findItemsByKeywords', {'keywords': 'TEST_PART_NO'})

    @patch('ebay_lister_fiat_item.ebay_item.Finding') #
    @patch('ebay_lister_fiat_item.ebay_item.load_ebay_env_config') #
    def test_get_category_id_not_found_uses_default(self, mock_load_env, mock_finding_conn):
        mock_load_env.return_value = self.mock_config
        mock_api_finding = MagicMock()
        mock_finding_conn.return_value = mock_api_finding

        mock_response_data = {'searchResult': {'_count': '0', 'item': []}}
        mock_api_finding.execute.return_value = MockEbaySDKResponse(reply_dict=mock_response_data)

        handler = EBAYHandler() #
        category_id = handler.get_category_id("TEST_PART_NO", default_category_id="999") #
        self.assertEqual(category_id, "999")

    @patch('ebay_lister_fiat_item.ebay_item.Finding') #
    @patch('ebay_lister_fiat_item.ebay_item.load_ebay_env_config') #
    def test_get_category_id_api_error_uses_default(self, mock_load_env, mock_finding_conn):
        mock_load_env.return_value = self.mock_config
        mock_api_finding = MagicMock()
        mock_finding_conn.return_value = mock_api_finding
        
        mock_api_finding.execute.return_value = MockEbaySDKResponse(ack='Failure')

        handler = EBAYHandler() #
        category_id = handler.get_category_id("TEST_PART_NO", default_category_id="777") #
        self.assertEqual(category_id, "777")

    def test_get_shipping_profile_id_by_weight(self):
        # Current implementation is a placeholder returning default
        profile_id = EBAYHandler.get_shipping_profile_id_by_weight(2.5, "DEFAULT_PROFILE") #
        self.assertEqual(profile_id, "DEFAULT_PROFILE")

    @patch('ebay_lister_fiat_item.ebay_item.EPERHandler') #
    @patch.object(EBAYHandler, 'get_category_id') #
    def test_draft_item_payload_success(self, mock_get_category_id, mock_eper_handler_cls):
        # Mock EPERHandler instance and its get_item method
        mock_eper_item = MagicMock()
        mock_eper_item.get_item.side_effect = lambda key: {
            "title": "Test EPER Title",
            "title_base_description": "Test EPER Description",
            "eper_price_str": "99.99",
            "part_number": "ACTUAL_PART_NO",
            "final_output_comparison_numbers": ["COMP1", "COMP2"],
            "manufacturer_name": "Test Manufacturer"
        }.get(key)
        mock_eper_handler_cls.return_value = mock_eper_item
        mock_get_category_id.return_value = "12345"

        payload = self.handler.draft_item_payload( #
            part_number_str="QUERY_PART_NO",
            quantity=2,
            condition_id="1000",
            shipping_profile_id_val="SHIP_ID",
            payment_profile_id_val="PAY_ID", #
            return_profile_id_val="RET_ID", #
            sku="TEST_SKU",
            item_location="Test Location", #
            country_code="DE", #
            currency_code="EUR", #
            dispatch_time_max="3", #
            vat_percent=19.0, #
            picture_urls=["http://example.com/pic1.jpg"], #
            title_override="Overridden Title" #
        )

        self.assertEqual(payload['Item']['Title'], "Overridden Title") #
        self.assertEqual(payload['Item']['StartPrice'], "99.99") #
        self.assertEqual(payload['Item']['Quantity'], "2") #
        self.assertEqual(payload['Item']['ConditionID'], "1000") #
        self.assertEqual(payload['Item']['SKU'], "TEST_SKU") #
        self.assertEqual(payload['Item']['PrimaryCategory']['CategoryID'], "12345") #
        self.assertEqual(payload['Item']['PictureDetails']['PictureURL'], ["http://example.com/pic1.jpg"]) #
        self.assertTrue(any(spec['Name'] == 'Herstellernummer' and spec['Value'] == 'ACTUAL_PART_NO' for spec in payload['Item']['ItemSpecifics']['NameValueList'])) #
        self.assertTrue(any(spec['Name'] == 'OE/OEM Referenznummer(n)' and spec['Value'] == 'COMP1, COMP2' for spec in payload['Item']['ItemSpecifics']['NameValueList'])) #
        self.assertIn('VATDetails', payload['Item']) #
        self.assertEqual(payload['Item']['VATDetails']['VATPercent'], "19.0") #
        mock_eper_handler_cls.assert_called_once_with("QUERY_PART_NO")
        mock_get_category_id.assert_called_once_with("ACTUAL_PART_NO", default_category_id='185012')

    @patch('ebay_lister_fiat_item.ebay_item.EPERHandler') #
    def test_draft_item_payload_eper_fail(self, mock_eper_handler_cls):
        mock_eper_handler_cls.side_effect = ValueError("EPER lookup failed")
        with self.assertRaisesRegex(ValueError, "EPERHandler could not be initialized"):
            self.handler.draft_item_payload(part_number_str="FAIL_PART", quantity=1, condition_id="1000", #
                                        shipping_profile_id_val="s", payment_profile_id_val="p", #
                                        return_profile_id_val="r", sku="s", item_location="l", #
                                        country_code="C", currency_code="C", dispatch_time_max="1", vat_percent=0) #

    def test_get_item_success(self):
        mock_response_item_data = {'Title': 'Test Item', 'ItemID': '112233'}
        self.mock_trading_api.execute.return_value = MockEbaySDKResponse(
            reply_dict={'Item': mock_response_item_data}
        )
        item_data = self.handler.get_item("112233") #
        self.assertEqual(item_data['Title'], 'Test Item')
        self.mock_trading_api.execute.assert_called_once_with('GetItem', {'ItemID': '112233', 'DetailLevel': 'ReturnAll'})

    def test_get_item_failure(self):
        self.mock_trading_api.execute.return_value = MockEbaySDKResponse(ack='Failure', errors=[MagicMock(LongMessage='Error occurred')])
        item_data = self.handler.get_item("112233") #
        self.assertIsNone(item_data)

    def test_create_item_success(self):
        self.mock_trading_api.execute.return_value = MockEbaySDKResponse(data={'ItemID': 'NEW_ITEM_ID'})
        item_payload = {'Item': {'Title': 'Test New Item', 'SKU': 'NEW_SKU'}} #
        item_id = self.handler.create_item(item_payload) #
        self.assertEqual(item_id, 'NEW_ITEM_ID')
        self.mock_trading_api.execute.assert_called_once_with('AddItem', item_payload)

    def test_create_item_failure(self):
        self.mock_trading_api.execute.return_value = MockEbaySDKResponse(ack='Failure', errors=[MagicMock(SeverityCode='Error', ShortMessage='Bad call', LongMessage='Item creation failed')])
        item_payload = {'Item': {'Title': 'Test New Item', 'SKU': 'NEW_SKU'}} #
        item_id = self.handler.create_item(item_payload) #
        self.assertIsNone(item_id)

    def test_revise_item_success(self):
        self.mock_trading_api.execute.return_value = MockEbaySDKResponse(data={'ItemID': 'REV_ITEM_ID'})
        revised_fields = {'Item': {'ItemID': 'REV_ITEM_ID', 'StartPrice': '10.00'}} #
        item_id = self.handler.revise_item("REV_ITEM_ID", {'StartPrice': '10.00'}) #
        self.assertEqual(item_id, "REV_ITEM_ID")
        self.mock_trading_api.execute.assert_called_once_with('ReviseFixedPriceItem', revised_fields)

    def test_revise_item_failure(self):
        self.mock_trading_api.execute.return_value = MockEbaySDKResponse(ack='Failure', errors=[MagicMock(SeverityCode='Error', ShortMessage='Bad call', LongMessage='Item revision failed')])
        item_id = self.handler.revise_item("REV_ITEM_ID", {'StartPrice': '10.00'}) #
        self.assertIsNone(item_id)

if __name__ == '__main__':
    unittest.main()