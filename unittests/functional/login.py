import unittest
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

class Login(unittest.TestCase):
    def setUp(self):
        self.driver = webdriver.Firefox()

    def test_login(self):
        driver = self.driver
        driver.get('https://localhost:8000')
        self.assertIn('FencingTournamentTool', driver.title)

    def tearDown(self):
        self.driver.close()

if __name__ == "__main__":
    unittest.main()
