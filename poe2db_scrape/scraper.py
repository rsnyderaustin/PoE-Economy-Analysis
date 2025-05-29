import re
from enum import Enum

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup


class ItemUrls(Enum):
    ONE_HANDED_MACES = 'https://poe2db.tw/us/One_Hand_Maces#ModifiersCalc'


class Poe2DbScraper:

    @staticmethod
    def _determine_mod_types(mod_data):
        print(f"Row data: {mod_data.prettify()}\n---")
        spans = mod_data.find_all('span')
        mod_type_spans = [span for span in spans if any(['crafting' in cls for cls in span.get('class', '')])]
        mod_types = [span.get('data-tag') for span in mod_type_spans]
        return mod_types

    @staticmethod
    def _determine_mod_text(mod_data):
        texts = []
        values_ranges = []
        for i, child in enumerate(list(mod_data.children)):
            if i == 0:
                continue

            text = child.get_text(strip=True)
            texts.append(text)

            if child.name == 'span' and 'mod-value' in child.get('class', []):
                values_ranges.append(text)


    def _parse_table_mods(self, table):
        tbody = table.find('tbody')
        if not tbody:
            raise ValueError("No tbody found for this HTML table. Unexpected.")

        mod_tiers = tbody.find_all('tr')
        for mod_tier in mod_tiers:
            cells = mod_tier.find_all('td')
            mod_name = cells[0].get_text(strip=True)
            mod_ilvl = cells[1].get_text(strip=True)

            mod_data = cells[2]
            print(f"Row data: {mod_data.prettify()}\n---")
            weight = float(mod_data.find('span', class_='badge rounded-pill bg-danger').get_text(strip=True))
            mod_types = self._determine_mod_types(mod_data)
            sanitized_mod_text, mod_values = self._determine_mod_text(mod_data)

            values = mod_data.find_all('span', class_='mod-value')
            x=0

    def scrape(self):
        options = Options()
        options.add_argument("--headless")  # Run in headless mode
        options.add_argument("--disable-gpu")  # Optional: needed for some environments
        options.add_argument("--no-sandbox")  # Optional: good for Linux servers
        options.add_argument("--window-size=1920,1080")  # Optional: ensures consistent layout

        for e in ItemUrls:
            driver = webdriver.Chrome(options=options)
            driver.get(e.value)
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')

            tables = soup.find_all('table')

            for table in tables:
                self._parse_table_mods(table)

