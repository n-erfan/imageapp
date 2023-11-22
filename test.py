import unittest
from app import app

class FlaskAppTest(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_index_page(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Image Gallery', response.data)

    # Add more test cases for your application

if __name__ == '__main__':
    unittest.main()

