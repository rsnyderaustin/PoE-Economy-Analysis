

class Result:
    pass


class Ok(Result):
    def __init__(self, value):
        self.value = value


class Err(Result):
    def __init__(self, error):
        self.error = error
