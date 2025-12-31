

class CacheSettings:

    def __init__(self,
                 load_raw_responses_from_file: bool,
                 save_raw_responses_to_file: bool,
                 load_listings_from_file: bool,
                 save_listings_to_file: bool,
                 pull_from_trade_api: bool,
                 pull_time_minutes: int = None,
                 save_every: int = 5):
        self.load_raw_responses_from_file = load_raw_responses_from_file
        self.save_raw_responses_to_file = save_raw_responses_to_file

        self.load_listings_from_file = load_listings_from_file
        self.save_listings_to_file = save_listings_to_file

        self.pull_from_trade_api = pull_from_trade_api
        self.pull_time_minutes = pull_time_minutes
        self.save_every = save_every

        self.validate()

    def validate(self):
        if self.pull_from_trade_api and not self.pull_time_minutes:
            raise ValueError(f"Must specify pull_time_minutes if pull_from_trade_api is flagged")
