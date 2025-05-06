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

        self.current_account_limits = dict()
        self.current_ip_limits = dict()

        self.request_counter = 0

    @staticmethod
    def _fetch_limits_and_state(response_headers: dict):
        if 'X-Rate-Limit-Account' in response_headers:
            account_limit = response_headers['X-Rate-Limit-Account']
        else:
            account_limit = '100:5:60'

        if 'x-rate-limit-account-state' in response_headers:
            account_state = response_headers['x-rate-limit-account-state']
        else:
            account_state = '0:5:60'

        if 'X-Rate-Limit-Ip' in response_headers:
            ip_limit = response_headers['X-Rate-Limit-Ip']
        else:
            ip_limit = '8:10:60,15:60:120,60:300:1800'

        if 'x-rate-limit-ip-state' in response_headers:
            ip_state = response_headers['x-rate-limit-ip-state']
        else:
            ip_state = '5:10:0,30:60:0,100:300:0'

        account_limits = _parse_rate_string(account_limit)
        account_state = _parse_rate_string(account_state)

        ip_limits = _parse_rate_string(ip_limit)
        ip_state = _parse_rate_string(ip_state)

        return account_limits, account_state, ip_limits, ip_state

    def set_limits(self, func_name: str, response_headers: dict):
        print(response_headers)
        account_limits, account_state, ip_limits, ip_state = self._fetch_limits_and_state(response_headers)

        self.current_account_limits[func_name] = account_limits
        self.current_ip_limits[func_name] = ip_limits

        if func_name in self.request_deques:
            logging.error(f"set_limits called for func_name {func_name}, which already exists in the dict.")

        self.request_deques[func_name] = []

        for limit, state in list(zip([*account_limits, *ip_limits], [*account_state, *ip_state])):
            max_requests = limit[0]
            seconds_interval = limit[1]
            current_requests = state[0]
            self.request_deques[func_name].append(
                Deque(
                    maximum_requests=max_requests - 1, # We lower the max requests by 1 to stay conservative
                    seconds_interval=seconds_interval,
                    current_requests=current_requests
                )
            )

    def _check_if_limits_have_changed(self, func_name: str, response_headers: dict):
        account_limits, account_state, ip_limits, ip_state = self._fetch_limits_and_state(response_headers)

        if account_limits != self.current_account_limits[func_name]:
            return True

        if ip_limits != self.current_ip_limits[func_name]:
            return True

    def _wait_if_needed(self, func_name: str):
        now = time.time()

        can_request = all(
            [
                request_deque.is_ready(now)
                for request_deque in self.request_deques[func_name]
            ]
        )

        if not can_request:
            logging.info("Waiting to send next request...")

        while not can_request:
            sleep_time = 0.25
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
            response.raise_for_status()

            self.set_limits(response_headers=response.headers,
                            func_name=func_name)

            now = time.time()
            self._register_requests(now=now,
                                    func_name=func_name)
            return response

        self._wait_if_needed(func_name=func_name)

        now = time.time()
        response = request_func(*args, **kwargs)

        # ip_state = _parse_rate_string(response.headers['x-rate-limit-ip-state'])
        # account_state = _parse_rate_string(response.headers['x-rate-limit-account-state'])

        if self.request_counter % 5 == 0 and self._check_if_limits_have_changed(func_name=func_name,
                                                                                response_headers=response.headers):
            logging.info(f"Limits have changed for func '{func_name}'. Resetting limits.")
            self.set_limits(func_name=func_name,
                            response_headers=response.headers)

        self._register_requests(now=now,
                                func_name=func_name)
        return response
