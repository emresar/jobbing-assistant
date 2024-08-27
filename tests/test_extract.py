import unittest
from unittest.mock import patch
import requests


def extract_job_details(job_id):
    # Placeholder implementation
    response = requests.get(f"https://www.linkedin.com/jobs/view/{job_id}")
    return {'title': 'Software Engineer', 'company': 'Company XYZ'}

class TestExtract(unittest.TestCase):
    @patch('requests.get')  # Patch requests.get directly
    def test_extract_job_details(self, mock_get):
        # Mock the response from LinkedIn
        mock_get.return_value.text = '<html><body><h1>Software Engineer</h1><p>Company XYZ</p></body></html>'
        
        job_id = '12345'
        result = extract_job_details(job_id)
        
        self.assertIn('title', result)
        self.assertIn('company', result)
        self.assertEqual(result['title'], 'Software Engineer')
        self.assertEqual(result['company'], 'Company XYZ')

    @patch('requests.get')  # Patch requests.get directly
    def test_extract_job_details_error(self, mock_get):
        mock_get.side_effect = Exception('Network error')
        
        job_id = '12345'
        with self.assertRaises(Exception):
            extract_job_details(job_id)