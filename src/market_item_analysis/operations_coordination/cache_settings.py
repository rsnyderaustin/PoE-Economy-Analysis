

class CacheSettings:

    def __init__(self,
                 load_raw_api_responses: bool,
                 load_listings: bool,
                 save_raw_api_responses: bool,
                 save_listings: bool):
        self.load_raw_api_responses = load_raw_api_responses
        self.load_listings = load_listings
        self.save_raw_api_responses = save_raw_api_responses
        self.save_listings = save_listings
