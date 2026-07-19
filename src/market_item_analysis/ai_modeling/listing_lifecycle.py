import itertools

import numpy as np
import pandas as pd

from src.market_item_analysis.listing.objects import Listing
from src.market_item_analysis.shared.enums.item_enums import EquipmentCategory


class ListingLifecycle:

    def __init__(self,
                 listing: Listing):
        self.listing = listing

        self.dropped_cols = []


