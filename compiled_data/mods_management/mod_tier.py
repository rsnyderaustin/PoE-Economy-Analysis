
from dataclasses import dataclass


@dataclass
class ModTier:
    base_type_id: int
    coe_mod_id: str
    ilvl: int
    values_range: tuple
    weighting: float
