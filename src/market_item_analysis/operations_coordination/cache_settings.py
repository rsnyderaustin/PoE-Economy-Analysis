

class CacheSettings:

    def __init__(self,
                 load_from_file: bool,
                 pull_from_trade_api: bool,
                 save_to_file: bool,
                 save_every: int = 5):
        self.load_from_file = load_from_file
        self.pull_from_trade_api = pull_from_trade_api
        self.save_to_file = save_to_file
        self.save_every = save_every
