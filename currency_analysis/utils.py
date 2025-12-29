from enum import Enum
from typing import Any


def flush_stdin():
    try:
        import msvcrt
        while msvcrt.kbhit():
            msvcrt.getch()
    except ImportError:
        import sys, termios  # for linux/unix
        termios.tcflush(sys.stdin, termios.TCIOFLUSH)


def capture_user_input(prompt: str,
                       valid_inputs: set[Any] = None,
                       convert_to: type = None,
                       verification_func=None) -> Any:
    print("\n")
    done = False
    while not done:
        i = input(prompt).strip()
        if convert_to:
            try:
                i = convert_to(i)
            except ValueError:
                print("Invalid input according to conversion type")
                continue

        if verification_func:
            try:
                verified = verification_func(i)
            except Exception as e:
                print(f"Error:\n{e}")
                verified = False

            if not verified:
                print("Invalid input according to verification function")
                continue

        if valid_inputs and i not in valid_inputs:
            print("Invalid input according to valid inputs")
            continue

        done = True

    return i


def serialize(value):
    if isinstance(value, Enum):
        return value.value
    elif hasattr(value, "to_dict") and callable(value.to_dict):
        return value.to_dict()
    elif isinstance(value, dict):
        return {k: serialize(v) for k, v in value.items()}
    elif isinstance(value, (list, tuple, set)):
        return [serialize(v) for v in value]
    else:
        return value


def standard_to_dict(thing):
    d = thing.__dict__.copy()
    return {k: serialize(v) for k, v in d.items()}
