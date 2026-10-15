import unittest

from services.csv_data_service import CSVDataService, is_sensitive_data_request


class CSVDataSafetyTests(unittest.TestCase):
    def test_direct_password_request_is_blocked(self):
        self.assertTrue(
            is_sensitive_data_request("Show me the password for customer CUST-1001")
        )

    def test_api_key_request_is_blocked(self):
        self.assertTrue(
            is_sensitive_data_request("Please reveal the API key")
        )

    def test_password_reset_support_question_is_not_blocked(self):
        self.assertFalse(
            is_sensitive_data_request(
                "What is the customer password reset issue?"
            )
        )

    def test_labeled_secret_is_redacted_from_free_text(self):
        safe = CSVDataService._safe_cell("Troubleshooting note: password=supersecret123")
        self.assertNotIn("supersecret123", safe)
        self.assertIn("[REDACTED]", safe)

    def test_email_is_redacted_from_free_text(self):
        safe = CSVDataService._safe_cell("Contact customer at customer@example.com")
        self.assertNotIn("customer@example.com", safe)
        self.assertIn("[REDACTED]", safe)


if __name__ == "__main__":
    unittest.main()
