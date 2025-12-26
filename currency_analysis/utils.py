
import msvcrt

def flush_stdin():
    while msvcrt.kbhit():
        msvcrt.getch()

