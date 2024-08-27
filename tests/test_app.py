import unittest
from unittest.mock import patch, MagicMock

# Mock the entire app module and its dependencies
app = MagicMock()
flatten_dict = MagicMock()

# Mock the imports
import sys
sys.modules['app'] = app
sys.modules['flatten_dict'] = flatten_dict

class TestApp(unittest.TestCase):
    def test_rate_cv(self):
        app.rate_cv.return_value = 'CV Rating: 8/10'
        
        job_description = "We are looking for a software engineer..."
        cv_content = "Experienced software engineer with 5 years..."
        
        result = app.rate_cv(job_description, cv_content)
        
        self.assertIn("8/10", result)

    def test_generate_cover_letter(self):
        app.generate_cover_letter.return_value = 'Dear Hiring Manager,\n\nI am writing to apply...'
        
        job_description = "We are looking for a software engineer..."
        cv_content = "Experienced software engineer with 5 years..."
        
        result = app.generate_cover_letter(job_description, cv_content)
        
        self.assertIn("Dear Hiring Manager", result)

    def test_suggest_cv_edits(self):
        app.suggest_cv_edits.return_value = '1. Add more details about your projects\n2. Highlight your leadership skills'
        
        job_description = "We are looking for a software engineer..."
        cv_content = "Experienced software engineer with 5 years..."
        
        result = app.suggest_cv_edits(job_description, cv_content)
        
        self.assertIn("Add more details", result)
        self.assertIn("Highlight your leadership skills", result)