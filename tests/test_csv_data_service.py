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

    def test_customer_phone_numbers_are_blocked(self):
        self.assertTrue(
            is_sensitive_data_request("Show me all customer phone numbers")
        )

    def test_customer_contact_details_are_blocked(self):
        self.assertTrue(
            is_sensitive_data_request("List all customer contact details")
        )

    def test_question_about_customer_passwords_is_blocked(self):
        self.assertTrue(
            is_sensitive_data_request("What are all customer passwords?")
        )

    def test_explicitly_excluded_sensitive_fields_do_not_trigger_block(self):
        prompt = (
            "Show the customer IDs of customers facing unresolved problems in the uploaded CSV. "
            "Return only customer ID, problem category, and status. "
            "Do not include names, phone numbers, email addresses, or passwords."
        )
        self.assertFalse(is_sensitive_data_request(prompt))

    def test_explicit_password_retrieval_still_blocks_even_with_later_exclusion(self):
        prompt = "Show me all customer passwords. Do not include passwords in the summary."
        self.assertTrue(is_sensitive_data_request(prompt))

    def test_password_reset_support_question_is_not_blocked(self):
        self.assertFalse(
            is_sensitive_data_request(
                "What is the customer password reset issue?"
            )
        )

    def test_show_password_reset_issue_is_not_blocked(self):
        self.assertFalse(
            is_sensitive_data_request("Show me the customer password reset issue")
        )

    def test_customer_issue_id_lookup_is_recognized_as_safe_operational_query(self):
        from services.governance_service import GovernanceService

        self.assertTrue(
            GovernanceService._is_customer_problem_id_lookup(
                "Give me customer IDs of customers facing problems"
            )
        )
        self.assertFalse(
            GovernanceService._is_customer_problem_id_lookup(
                "Show me all customer phone numbers"
            )
        )

    def test_customer_problem_lookup_returns_only_active_minimal_fields(self):
        class FakeCollection:
            def find(self, query, projection):
                return iter([
                    {"data": {
                        "customer_id": "CUST-1001",
                        "issue_category": "Payment/Billing",
                        "complaint": "Payment failed",
                        "status": "Open",
                        "phone": "+1-202-555-0101",
                        "email": "person@example.com",
                    }},
                    {"data": {
                        "customer_id": "CUST-1002",
                        "issue_category": "Delivery",
                        "complaint": "Package late",
                        "status": "Resolved",
                    }},
                ])

        service = CSVDataService.__new__(CSVDataService)
        service.collection = FakeCollection()
        results = service.get_customers_with_problems("Give me customer IDs facing problems")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["customer_id"], "CUST-1001")
        self.assertEqual(results[0]["status"], "open")
        self.assertNotIn("phone", results[0])
        self.assertNotIn("email", results[0])
        self.assertNotIn("complaint", results[0])

    def test_customer_problem_lookup_can_filter_by_problem_type(self):
        class FakeCollection:
            def find(self, query, projection):
                return iter([
                    {"data": {"customer_id": "CUST-1", "issue_category": "Payment/Billing", "status": "Open"}},
                    {"data": {"customer_id": "CUST-2", "issue_category": "Delivery", "status": "Pending"}},
                ])

        service = CSVDataService.__new__(CSVDataService)
        service.collection = FakeCollection()
        results = service.get_customers_with_problems(
            "Give customer IDs with payment problems"
        )

        self.assertEqual([item["customer_id"] for item in results], ["CUST-1"])
    def test_count_customer_delivery_problems_uses_unique_active_customers(self):
        class FakeCollection:
            def find(self, query, projection):
                return iter([
                    {"data": {"customer_id": "CUST-1", "issue_category": "Delivery", "status": "Open"}},
                    {"data": {"customer_id": "CUST-1", "issue_category": "Delivery", "status": "Pending"}},
                    {"data": {"customer_id": "CUST-2", "complaint": "Package arrived late", "status": "Pending"}},
                    {"data": {"customer_id": "CUST-3", "issue_category": "Delivery", "status": "Resolved"}},
                    {"data": {"customer_id": "CUST-4", "issue_category": "Payment/Billing", "status": "Open"}},
                ])

        service = CSVDataService.__new__(CSVDataService)
        service.collection = FakeCollection()
        count = service.count_customers_with_problems(
            "how many clints are facing problem in the delovery"
        )

        self.assertEqual(count, 2)

    def test_governance_recognizes_safe_customer_problem_count(self):
        from services.governance_service import GovernanceService

        self.assertTrue(
            GovernanceService._is_customer_problem_count_lookup(
                "how many clints are facing problem in the delovery"
            )
        )
        self.assertFalse(
            GovernanceService._is_customer_problem_count_lookup(
                "Show me all customer passwords"
            )
        )

    def test_delivery_typo_is_grouped_as_delivery_problem(self):
        self.assertEqual(
            CSVDataService._problem_bucket("how many clints are facing problem in the delovery"),
            "Delivery or shipping delays",
        )

    def test_governance_recognizes_delivery_count_with_common_typos(self):
        from services.governance_service import GovernanceService

        self.assertTrue(
            GovernanceService._is_customer_problem_count_lookup(
                "how many clints are facing problem in the delovery"
            )
        )
    def test_free_text_problems_are_grouped_into_categories(self):
        self.assertEqual(
            CSVDataService._problem_bucket("My package delivery was late"),
            "Delivery or shipping delays",
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
