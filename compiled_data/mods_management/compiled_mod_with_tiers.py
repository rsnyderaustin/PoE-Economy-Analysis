
from dataclasses import dataclass

from .compiled_mod import CompiledMod
from external_apis import ModTier


@dataclass
class CompiledModWithTiers:
    """
    This class is literally only used as a package for when mods and tiers are needed in crafting simulation.
    Just a returnable.
    """
    compiled_mod: CompiledMod
    mod_tiers: list[ModTier]
