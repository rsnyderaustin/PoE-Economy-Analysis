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
                       verification_func = None) -> Any:
    print("\n")
    done = False
    while not done:
        i = input(prompt)
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

        if valid_inputs:
            if i in valid_inputs:
                done = True
            else:
                print("Invalid input according to valid inputs")

    return i

