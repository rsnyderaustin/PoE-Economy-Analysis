import logging

import rapidfuzz

import file_management
from file_management import FileKey
from instances_and_definitions import ItemMod, ModClass
from poecd_api.poecd_data import PoecdDataManager
from shared import shared_utils
from . import utils


class PoecdDataInjecter:

    def __init__(self):
        self.files_manager = file_management.FilesManager()
        self.mod_matches_file = self.files_manager.file_data[FileKey.MOD_MATCHES]

        self.mod_transformations = {
            '# additional': 'an additional',
            'an additional': '# additional',
            'reduced': 'increased',
            'increased': 'reduced'
        }

        self._coe_mod_parts_to_remove = {
            '#% increased Waystones found in Area',
            '#% reduced Waystones found in Area'
        }

        self._poecd_data = PoecdDataManager()

    def inject_poecd_data_into_mod(self, item_mod: ItemMod):
        # Implicit mods don't have weights, and we don't have weights for corruption enchantments yet
        # Both also probably have mod types, but they don't matter since they can't even be rolled with essences
        if item_mod.mod_class in [ModClass.IMPLICIT, ModClass.ENCHANT]:
            return

        poecd_mod_id = self._match_mod(item_mod)
        if not poecd_mod_id:
            logging.info(f"Parent mod:")
            shared_utils.log_dict(item_mod.__dict__)
            logging.info(f"Sub Mods:")
            for sub_mod in item_mod.sub_mods:
                shared_utils.log_dict(sub_mod.__dict__)
            raise RuntimeError(f"Could not find matching Poecd mod for Trade API mod. See above")

        atype_manager = self._poecd_data.fetch_atype_manager(item_mod.atype)
        poecd_mod = atype_manager.fetch_mod(mod_id=poecd_mod_id)

        item_mod.weighting = poecd_mod.fetch_weighting(ilvl=str(item_mod.mod_ilvl))
        item_mod.mod_types = poecd_mod.mod_types

    def _attempt_match(self,
                       item_mod: ItemMod,
                       atype_manager,
                       min_score: float,
                       attempt_to_transform: bool = False) -> str | None:

        if item_mod.is_hybrid:
            hybrid_scores_tracker = utils.MatchScoreTracker()

            number_of_parts = len(item_mod.sub_mods)

            # So this whole block works by matching individual PoE Trade hybrid mod (SubMod) texts to the possible
            # hybrid mod texts of the corresponding AType (data sourced from Poecd). After we've found the best matches
            # for each hybrid mod text, we just determine which Poecd hybrid mod is the most fititng
            for sub_mod in item_mod.sub_mods:
                mod_to_parent_dict = (atype_manager.hybrid_parts_to_parent_affixed_dict[item_mod.affix_type]
                                      if item_mod.affix_type else atype_manager.hybrid_parts_to_parent_dict)
                hybrid_mod_texts = list(mod_to_parent_dict.keys())

                if attempt_to_transform:
                    sub_mod_text = utils.transform_text(sub_mod.sanitized_mod_text,
                                                        transform_dict=self.mod_transformations)[0]
                else:
                    sub_mod_text = sub_mod.sanitized_mod_text
                matches = rapidfuzz.process.extract(sub_mod_text,
                                                    hybrid_mod_texts,
                                                    score_cutoff=min_score)

                for match, score, idx in matches:
                    poecd_mod_ids = mod_to_parent_dict[match]

                    # The number of parts in the Mod text has to line up with the number of parts in the Poecd mod
                    poecd_mod_ids = {
                        mod_id
                        for mod_id in poecd_mod_ids
                        if atype_manager.num_hybrid_parts_dict[mod_id] == number_of_parts
                    }

                    if not poecd_mod_ids:
                        continue

                    hybrid_scores_tracker.score_round(sub_mod_id=sub_mod.mod_id,
                                                      poecd_mod_ids=poecd_mod_ids,
                                                      score=score)

            poecd_mod_id_match = hybrid_scores_tracker.determine_winner()
            return poecd_mod_id_match

        if not item_mod.is_hybrid:
            if item_mod.affix_type:
                poecd_mod_texts = list(atype_manager.mods_affixed_dict[item_mod.affix_type].keys())
            else:
                poecd_mod_texts = list(atype_manager.mods_dict.keys())

            if attempt_to_transform:
                mod_text = utils.transform_text(item_mod.sub_mods[0].sanitized_mod_text,
                                                transform_dict=self.mod_transformations)[0]
            else:
                mod_text = item_mod.sub_mods[0].sanitized_mod_text

            result = rapidfuzz.process.extractOne(mod_text,
                                                  poecd_mod_texts,
                                                  score_cutoff=min_score)
            if result:
                match, score, idx = result

                mod = atype_manager.mods_affixed_dict[item_mod.affix_type][match]
                return mod.mod_id
            else:
                return None

    def _match_mod(self, item_mod: ItemMod, force_match: bool = False) -> str | None:
        """

        :param item_mod:
        :return: The matching Poecd Mod ID.
        """

        atype_manager = self._poecd_data.atype_data_managers[item_mod.atype]

        if item_mod.mod_id in self.mod_matches_file and not force_match:
            return self.mod_matches_file[item_mod.mod_id]

        coe_mod_id_match = self._attempt_match(item_mod=item_mod,
                                               atype_manager=atype_manager,
                                               min_score=95.0)
        if coe_mod_id_match:
            self.mod_matches_file[item_mod.mod_id] = coe_mod_id_match
            return coe_mod_id_match

        coe_mod_id_match = self._attempt_match(item_mod=item_mod,
                                               atype_manager=atype_manager,
                                               min_score=95.0,
                                               attempt_to_transform=True)
        if coe_mod_id_match:
            self.mod_matches_file[item_mod.mod_id] = coe_mod_id_match
            return coe_mod_id_match

        coe_mod_id_match = self._attempt_match(item_mod=item_mod,
                                               atype_manager=atype_manager,
                                               min_score=90.0)
        if coe_mod_id_match:
            self.mod_matches_file[item_mod.mod_id] = coe_mod_id_match
            return coe_mod_id_match

        coe_mod_id_match = self._attempt_match(item_mod=item_mod,
                                               atype_manager=atype_manager,
                                               min_score=90.0,
                                               attempt_to_transform=True)
        if coe_mod_id_match:
            self.mod_matches_file[item_mod.mod_id] = coe_mod_id_match
            return coe_mod_id_match

