import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup, NavigableString

from . import mods_management
from .mods_management import AtypeModsManager, Poe2DbModsManager
from poe2db_scrape.mods_management import Poe2DbMod
from shared import shared_utils
from shared.enums.item_enums import AType, ModAffixType
from shared.logging import LogsHandler, LogFile

api_log = LogsHandler().fetch_log(LogFile.EXTERNAL_APIS)

_atype_paths = {
    AType.ONE_HANDED_MACE: 'https://poe2db.tw/us/One_Hand_Maces#ModifiersCalc'
                           """,
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

    AType.RUBY: 'https://poe2db.tw/us/Ruby#ModifiersCalc',
    AType.EMERALD: 'https://poe2db.tw/us/Emerald#ModifiersCalc',
    AType.SAPPHIRE: 'https://poe2db.tw/us/Sapphire#ModifiersCalc',

    AType.RING: 'https://poe2db.tw/us/Rings#ModifiersCalc',
    AType.BELT: 'https://poe2db.tw/us/Belts#ModifiersCalc'"""
}


class _Poe2DbHtmlParser:

    def __init__(self, url: str):
        options = Options()
        options.add_argument("--headless")  # Run in headless mode
        options.add_argument("--disable-gpu")  # Optional: needed for some environments
        options.add_argument("--no-sandbox")  # Optional: good for Linux servers
        options.add_argument("--window-size=1920,1080")  # Optional: ensures consistent layout

        self.driver = webdriver.Chrome(options=options)
        time.sleep(0.5)
        self.driver.get(url)
        print(f"Successfully loaded {url} driver.")

        html = self.driver.page_source
        self.soup = BeautifulSoup(html, 'html.parser')

    def fetch_affix_mods(self, affix_type: ModAffixType):
        divs = self.soup.find_all('div', class_='col-lg-6')
        for div in divs:
            # The h5 element's text tells us what the table title is
            h5 = div.find('h5', class_='identify-title')
            if not h5:
                continue
            table_title = shared_utils.sanitize_text(h5.get_text(strip=True))

            if table_title == affix_type.value:
                table_mods = div.find_all('div', class_='explicitMod')
                return table_mods

    @staticmethod
    def fetch_mod_types(table_mod):
        spans = table_mod.find_all('span', )
        mod_type_spans = [span for span in spans if any(['crafting' in cls for cls in span.get('class', '')])]
        mod_types = [span.get('data-tag') for span in mod_type_spans]
        return mod_types

    def fetch_mod_pop_out_tiers(self, table_mod):
        pop_out_target = table_mod.get('data-bs-target')
        pop_out_target = pop_out_target[1:]  # Remove the '#' at the start of the target

        pop_out_table = self.soup.find('div', id=pop_out_target)

        return pop_out_table.find_all('tr')

    @staticmethod
    def parse_mod_text(mod) -> tuple[str, list]:
        text_list = []
        values_ranges = []

        valid_children = []
        for child in mod.contents:
            if not child:
                continue

            if isinstance(child, NavigableString) and child.strip():
                valid_children.append(child.get_text())

            if child.name != 'span':
                continue
            elif 'mod-value' in child.get('class', []) or 'KeywordPopups' in child.get('class', []):
                valid_children.append(child.get_text())

        for text in valid_children:
            values = shared_utils.extract_values_from_text(text)
            if values:
                value = values[0]  # Because each child is an individual piece of the overall string, only one index is ever returned here
                values_ranges.append(value)

                # +(3-5) to strength -> +# to strength
                if isinstance(value, tuple):
                    text = '#'

            text_list.append(text)

        mod_text = ' '.join(text_list)
        mod_text = shared_utils.sanitize_mod_text(mod_text).replace('n_p', 'np')

        return mod_text, values_ranges

    @staticmethod
    def fetch_mod_tier_weight(mod_tier) -> int:
        weight_pill = mod_tier.find('span', class_='rounded-pill')
        return weight_pill.get_text()


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

        self._atypes_managers = {
            atype: AtypeModsManager(atype=atype)
            for atype in _atype_paths.keys()
        }

        self._parsers = {
            atype: _Poe2DbHtmlParser(url=url)
            for atype, url in _atype_paths.items()
        }

    def _scrape_mods(self, atype: AType, affix_type: ModAffixType):
        parser = self._parsers[atype]
        mods_manager = self._atypes_managers[atype]

        prefix_mods = parser.fetch_affix_mods(affix_type=affix_type)
        for mod in prefix_mods:
            mod_tiers = parser.fetch_mod_pop_out_tiers(mod)
            mod_types = parser.fetch_mod_types(mod)

            for mod_tier in mod_tiers:
                cells = mod_tier.find_all('td')
                tier_name = shared_utils.sanitize_text(cells[0].get_text())
                mod_ilvl = int(cells[1].get_text(strip=True))
                mod_tier_weight = int(parser.fetch_mod_tier_weight(mod_tier))
                mod_text, value_ranges = parser.parse_mod_text(cells[2])

                mod_id = mods_management.create_mod_id(atype=atype,
                                                       affix_type=affix_type,
                                                       mod_text=mod_text)
                mod = mods_manager.fetch_mod(mod_id)

                if not mod:
                    mod = Poe2DbMod(
                        atype=atype,
                        affix_type=affix_type,
                        mod_text=mod_text,
                        mod_types=mod_types
                    )
                    mods_manager.add_mod(mod)

                mod.add_tier(ilvl=mod_ilvl,
                             tier_name=tier_name,
                             value_ranges=value_ranges,
                             weighting=mod_tier_weight
                             )

    def scrape(self) -> Poe2DbModsManager:
        for atype, url in _atype_paths.items():
            self._scrape_mods(atype=atype, affix_type=ModAffixType.PREFIX)
            self._scrape_mods(atype=atype, affix_type=ModAffixType.SUFFIX)

        poe2db_mods_manager = Poe2DbModsManager(atype_managers=list(self._atypes_managers.values()))
        return poe2db_mods_manager
