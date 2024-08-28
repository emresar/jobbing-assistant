import unittest
from unittest.mock import patch


def get_company_info(company_name):
    # Placeholder implementation
    return f"Information about {company_name}"


class TestWikipedia(unittest.TestCase):
    def test_get_company_info(self):
        company_name = "Company XYZ"
        result = get_company_info(company_name)

        self.assertIsInstance(result, str)
        self.assertIn("Company XYZ", result)
