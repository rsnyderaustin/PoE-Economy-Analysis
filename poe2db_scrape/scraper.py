import time

from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .mods_management import AtypeModsManager, Poe2DbModsManager
from poe2db_scrape.mods_management import Poe2DbMod
from shared import shared_utils
from shared.enums.item_enums import AType
from shared.logging import LogsHandler, LogFile


api_log = LogsHandler().fetch_log(LogFile.EXTERNAL_APIS)

_atype_paths = {
    AType.ONE_HANDED_MACE: 'https://poe2db.tw/us/One_Hand_Maces#ModifiersCalc',
    AType.SCEPTRE: 'https://poe2db.tw/us/Sceptres#ModifiersCalc',
    AType.SPEAR: 'https://poe2db.tw/us/Spears#ModifiersCalc',
    AType.BOW: 'https://poe2db.tw/us/Bows#ModifiersCalc',
    AType.STAFF: 'https://poe2db.tw/us/Staves#ModifiersCalc',
    AType.TWO_HANDED_MACE: 'https://poe2db.tw/us/Two_Hand_Maces#ModifiersCalc',
    AType.QUARTERSTAFF: 'https://poe2db.tw/us/Quarterstaves#ModifiersCalc',
    AType.CROSSBOW: 'https://poe2db.tw/us/Crossbows#ModifiersCalc',
    AType.AMULET: 'https://poe2db.tw/us/Amulets#ModifiersCalc',
    AType.WAND: 'https://poe2db.tw/us/Wands#ModifiersCalc',

    AType.HELMET_INT: 'https://poe2db.tw/us/Helmets_int#ModifiersCalc',
    AType.HELMET_STR: 'https://poe2db.tw/us/Helmets_str#ModifiersCalc',
    AType.HELMET_DEX: 'https://poe2db.tw/us/Helmets_dex#ModifiersCalc',
    AType.HELMET_STR_DEX: 'https://poe2db.tw/us/Helmets_str_dex#ModifiersCalc',
    AType.HELMET_STR_INT: 'https://poe2db.tw/us/Helmets_str_int#ModifiersCalc',
    AType.HELMET_DEX_INT: 'https://poe2db.tw/us/Helmets_dex_int#ModifiersCalc',

    AType.GLOVE_INT: 'https://poe2db.tw/us/Gloves_int#ModifiersCalc',
    AType.GLOVE_STR: 'https://poe2db.tw/us/Gloves_str#ModifiersCalc',
    AType.GLOVE_DEX: 'https://poe2db.tw/us/Gloves_dex#ModifiersCalc',
    AType.GLOVE_STR_DEX: 'https://poe2db.tw/us/Gloves_str_dex#ModifiersCalc',
    AType.GLOVE_STR_INT: 'https://poe2db.tw/us/Gloves_str_int#ModifiersCalc',
    AType.GLOVE_DEX_INT: 'https://poe2db.tw/us/Gloves_dex_int#ModifiersCalc',

    AType.BOOT_INT: 'https://poe2db.tw/us/Boots_int#ModifiersCalc',
    AType.BOOT_STR: 'https://poe2db.tw/us/Boots_str#ModifiersCalc',
    AType.BOOT_DEX: 'https://poe2db.tw/us/Boots_dex#ModifiersCalc',
    AType.BOOT_STR_DEX: 'https://poe2db.tw/us/Boots_str_dex#ModifiersCalc',
    AType.BOOT_STR_INT: 'https://poe2db.tw/us/Boots_str_int#ModifiersCalc',
    AType.BOOT_DEX_INT: 'https://poe2db.tw/us/Boots_dex_int#ModifiersCalc',

    AType.BODY_ARMOUR_STR: 'https://poe2db.tw/us/Body_Armours_str#ModifiersCalc',
    AType.BODY_ARMOUR_DEX: 'https://poe2db.tw/us/Body_Armours_dex#ModifiersCalc',
    AType.BODY_ARMOUR_INT: 'https://poe2db.tw/us/Body_Armours_int#ModifiersCalc',
    AType.BODY_ARMOUR_STR_DEX: 'https://poe2db.tw/us/Body_Armours_str_dex#ModifiersCalc',
    AType.BODY_ARMOUR_STR_INT: 'https://poe2db.tw/us/Body_Armours_str_int#ModifiersCalc',
    AType.BODY_ARMOUR_DEX_INT: 'https://poe2db.tw/us/Body_Armours_dex_int#ModifiersCalc',
    AType.BODY_ARMOUR_STR_DEX_INT: 'https://poe2db.tw/us/Body_Armours_str_dex_int#ModifiersCalc',

    AType.SHIELD_STR: 'https://poe2db.tw/us/Shields_str#ModifiersCalc',
    AType.BUCKLER: 'https://poe2db.tw/us/Shields_dex#ModifiersCalc',
    AType.SHIELD_STR_DEX: 'https://poe2db.tw/us/Shields_str_dex#ModifiersCalc',
    AType.SHIELD_STR_INT: 'https://poe2db.tw/us/Shields_str_int#ModifiersCalc',

    AType.FOCUS: 'https://poe2db.tw/us/Foci#ModifiersCalc',
    AType.QUIVER: 'https://poe2db.tw/us/Quivers#ModifiersCalc',

    AType.LIFE_FLASK: 'https://poe2db.tw/us/Life_Flasks#ModifiersCalc',
    AType.MANA_FLASK: 'https://poe2db.tw/us/Mana_Flasks#ModifiersCalc',

    AType.RUBY: 'poe2db.tw/us/Ruby#ModifiersCalc',
    AType.EMERALD: 'https://poe2db.tw/us/Emerald#ModifiersCalc',
    AType.SAPPHIRE: 'https://poe2db.tw/us/Sapphire#ModifiersCalc',

    AType.RING: 'https://poe2db.tw/us/Rings#ModifiersCalc',
    AType.BELT: 'https://poe2db.tw/us/Belts#ModifiersCalc'
}


class _ATypeHtmlParser:

    def __init__(self, atype: AType, soup: BeautifulSoup):
        self.atype = atype
        self.soup = soup

        self._affix_types = self._determine_mod_affix_types()

    @staticmethod
    def _parse_mod_text(mod_data):
        print(f"Parsing mod data:\n{mod_data.prettify()}")
        texts = []
        values_ranges = []
        children = list(mod_data.children)[2:]  # Only items after the first 2 contain mod text
        for child in children:
            # "float-end" spans are the tiers, ilvl, weights, etc of affix table mods
            if child.name == 'span' and 'float-end' in child.get('class', []):
                continue

            text = child.get_text(strip=True)
            if not text:
                continue

            texts.append(text)

            if child.name == 'span' and 'mod-value' in child.get('class', []):
                values = shared_utils.extract_values_from_text(text)
                values_ranges.extend(values)

        texts = ' '.join(texts)
        texts = texts.replace('# %', '#%').replace('(#-#)', '# to #')
        texts = shared_utils.sanitize_mod_text(texts)
        print(f"Mod data parsed into:\n{texts}")
        return texts, values_ranges

    def _determine_mod_affix_types(self) -> dict:
        affix_types = dict()
        affix_tables = self.soup.find_all('div', class_='col-lg-6')
        for affix_table in affix_tables:
            affix_type = affix_table.find(text=True, recursive=True)
            affix_type = shared_utils.sanitize_text(affix_type)

            mod_table = affix_table.find('div', class_='identifynormal')
            for mod in mod_table.find_all('div', class_='explicitMod'):
                mod_text, _ = self._parse_mod_text(mod)
                affix_types[mod_text] = affix_type

        return affix_types

    @staticmethod
    def _determine_mod_types(mod_data):
        print(f"Row data: {mod_data.prettify()}\n---")
        spans = mod_data.find_all('span')
        mod_type_spans = [span for span in spans if any(['crafting' in cls for cls in span.get('class', '')])]
        mod_types = [span.get('data-tag') for span in mod_type_spans]
        return mod_types

    def parse_table_mods(self, table) -> set[Poe2DbMod]:
        mods_dict = dict()

        tbody = table.find('tbody')
        if not tbody:
            raise ValueError("No tbody found for this HTML table. Unexpected.")

        print("Finding mod tiers.")
        mod_tiers = tbody.find_all('tr')
        for i, mod_tier in enumerate(mod_tiers):
            print(f"Iterating through mod tier {i}")
            cells = mod_tier.find_all('td')
            tier_name = cells[0].get_text(strip=True)
            mod_ilvl = cells[1].get_text(strip=True)

            mod_data = cells[2]
            weight = float(mod_data.find('span', class_='badge rounded-pill bg-danger').get_text(strip=True))

            print("Determining mod types.")
            mod_types = self._determine_mod_types(mod_data)

            print("Parsing mod text")
            mod_text, mod_values = self._parse_mod_text(mod_data)

            mod_text = shared_utils.sanitize_mod_text(mod_text)
            affix_type = self._affix_types[mod_text]

            values = mod_data.find_all('span', class_='mod-value')

            mod_id = Poe2DbMod.create_mod_id(atype=self.atype, mod_text=mod_text, affix_type=affix_type)
            if mod_id not in mods_dict:
                mod = Poe2DbMod(
                    atype=self.atype,
                    affix_type=affix_type,
                    mod_text=mod_text,
                    mod_types=mod_types
                )
                mods_dict[mod.mod_id] = mod
            mod = mods_dict[mod_id]

            mod.add_tier(ilvl=mod_ilvl,
                         tier_name=tier_name,
                         value_ranges=values,
                         weighting=weight)

        return set(mods_dict.values())

class Poe2DbScraper:
    _instance = None
    _initialized = False

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(Poe2DbScraper, cls).__new__(cls)

        return cls._instance

    def __init__(self):
        cls = self.__class__
        if cls._initialized:
            return
        cls._initialized = True

        options = Options()
        options.add_argument("--headless")  # Run in headless mode
        options.add_argument("--disable-gpu")  # Optional: needed for some environments
        options.add_argument("--no-sandbox")  # Optional: good for Linux servers
        options.add_argument("--window-size=1920,1080")  # Optional: ensures consistent layout
        self.driver = webdriver.Chrome(options=options)

        self._atypes_managers = {
            atype: AtypeModsManager(atype=atype)
            for atype in _atype_paths.keys()
        }

    def scrape(self) -> Poe2DbModsManager:
        for atype, url in _atype_paths.items():
            mods_manager = self._atypes_managers[atype]
            self.driver.get(url)
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')

            parser = _ATypeHtmlParser(atype=atype, soup=soup)

            tables = soup.find_all('table')

            for table in tables:
                mods = parser.parse_table_mods(table)
                for mod in mods:
                    mods_manager.add_mod(mod)

        poe2db_mods_manager = Poe2DbModsManager(atype_managers=list(self._atypes_managers.values()))
        return poe2db_mods_manager

