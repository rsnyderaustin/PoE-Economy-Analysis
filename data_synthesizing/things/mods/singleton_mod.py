

from .base_mod_class import Mod, generate_mod_id


class SingletonMod(Mod):

    def __init__(self,
                 atype: str,
                 mod_text: str,
                 mod_id: str = None):
        """
        As of now this is only applicable to Implicit mods and Enchant mods.
        :param atype: Attribute type (ie: DEX Body Armour)
        """
        mod_id = generate_mod_id(
            atype=atype,
            mod_ids=[mod_id] if mod_id else [],
            mod_text=mod_text
        )

        super().__init__(mod_id=mod_id)
        self.mod_text = mod_text

        self.atype = atype

    def __eq__(self, other):
        if not isinstance(other, SingletonMod):
            return False

        return self.mod_id == other.mod_id

    def __hash__(self):
        return hash(self.mod_id)
