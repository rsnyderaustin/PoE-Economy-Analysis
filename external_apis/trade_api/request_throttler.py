import logging
import time

from collections import deque


def _parse_rate_string(rate_limit_str):
    limits = []

    # Split by comma to separate each limit rule
    for limit in rate_limit_str.split(','):
        # Split each limit rule by colon
        parts = limit.split(':')

        # Extract the first and second numbers
        first_number = int(parts[0])
        second_number = int(parts[1])
        third_number = int(parts[2])

        # Append the pair to the list
        limits.append((first_number, second_number, third_number))

    return limits


class Deque:

    def __init__(self, maximum_requests: int, seconds_interval: int, current_requests: int):
        """

        :param maximum_requests:
        :param seconds_interval:
        :param current_requests: The number of requests that have been made within the seconds_interval -
            often requests will have been made from this IP outside of this program instance. So we need to take that into account.
        """
        self.maximum_requests = maximum_requests
        self.seconds_interval = seconds_interval

        self.requests = deque()

        now = time.time()
        for _ in list(range(current_requests)):
            self.register_request(now=now)

    def remove_expired_timestamps(self, now):
        while self.requests and (now - self.requests[0]) > self.seconds_interval:
            self.requests.popleft()

    def register_request(self, now):
        self.requests.append(now)

    def is_ready(self, now):
        self.remove_expired_timestamps(now=now)
        num_requests_in_queue = len(self.requests)
        return num_requests_in_queue < self.maximum_requests


class RequestThrottler:

    def __init__(self):
        """
        {
            func.__name__: [deques]
        }
        """
        self.request_deques = dict()

    def set_limits(self, func_name: str, response_headers: dict):
        account_limit = response_headers['X-Rate-Limit-Account']
        account_state = response_headers['x-rate-limit-account-state']

        ip_limit = response_headers['X-Rate-Limit-Ip']
        ip_state = response_headers['x-rate-limit-ip-state']

        account_limits = _parse_rate_string(account_limit)
        account_state = _parse_rate_string(account_state)

        ip_limits = _parse_rate_string(ip_limit)
        ip_state = _parse_rate_string(ip_state)

        if func_name in self.request_deques:
            logging.error(f"set_limits called for func_name {func_name}, which already exists in the dict.")

        self.request_deques[func_name] = []

        for limit, state in list(zip([*account_limits, *ip_limits], [*account_state, *ip_state])):
            max_requests = limit[0]
            seconds_interval = limit[1]
            current_requests = state[0]
            logging.info(f"For function '{func_name}' setting limit of maximum {max_requests} requests within {seconds_interval} seconds."
                         f"\n\tCurrently at {current_requests} requests in the last {seconds_interval} seconds..")
            self.request_deques[func_name].append(
                Deque(
                    maximum_requests=max_requests - 1, # We lower the max requests by 1 to stay conservative
                    seconds_interval=seconds_interval,
                    current_requests=current_requests
                )
            )

    def _wait_if_needed(self, func_name: str):
        now = time.time()

        can_request = all(
            [
                request_deque.is_ready(now)
                for request_deque in self.request_deques[func_name]
            ]
        )

        while not can_request:
            sleep_time = 0.25
            logging.info(f"Waiting {sleep_time} seconds to send another request for function '{func_name}'.")
            time.sleep(sleep_time)
            now = time.time()

            can_request = all(
                [
                    request_deque.is_ready(now)
                    for request_deque in self.request_deques[func_name]
                ]
            )

    def _register_requests(self, func_name: str, now):
        for request_deque in self.request_deques[func_name]:
            request_deque.register_request(now=now)

    def send_request(self, request_func, *args, **kwargs):
        func_name = request_func.__name__
        if func_name not in self.request_deques:
            response = request_func(*args, **kwargs)

            self.set_limits(response_headers=response.headers,
                            func_name=func_name)

            now = time.time()
            self._register_requests(now=now,
                                    func_name=func_name)
            return response

        self._wait_if_needed(func_name=func_name)

        logging.info(f"Sending '{request_func}' request.")
        now = time.time()
        response = request_func(*args, **kwargs)

        ip_state = _parse_rate_string(response.headers['x-rate-limit-ip-state'])
        account_state = _parse_rate_string(response.headers['x-rate-limit-account-state'])
        logging.info(f"After '{func_name}' request limit states:")

        for state in ip_state:
            logging.info(f"\n\tIP state: {state[0]} hits in the last {state[1]} seconds.")

        for state in account_state:
            logging.info(f"\n\tAccount state: {state[0]} hits in the last {state[1]} seconds.")

        self._register_requests(now=now,
                                func_name=func_name)
        return response
