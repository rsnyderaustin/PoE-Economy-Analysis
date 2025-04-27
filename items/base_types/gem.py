
from items import Modifiable


class Gem(Modifiable):

    def __init__(self,
                 item_id: str,
                 name: str,
                 base_type: str,
                 quality: int):
        super(Modifiable).__init__(item_id=item_id,
                                   name=name,
                                   base_type=base_type,
                                   quality=quality)

