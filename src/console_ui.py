from prettytable import PrettyTable

import os
import sys
import time

if os.name == "nt":
    import msvcrt
else:
    from select import select

    import atexit
    import sys
    import termios


def resize_table(
    table: PrettyTable, terminal_columns: int, columns_percent: dict
) -> None:
    # Account for borders and padding
    columns = terminal_columns
    columns -= len(table._field_names) + 1
    columns -= 2 * len(table._field_names) * table._padding_width

    # Set new min width
    table._min_width = dict(
        (name, int(columns * percent)) for name, percent in columns_percent.items()
    )


class GalileoConsole:
    def __init__(self) -> None:
        self.__prev_terminal_size = None
        self.__prev_user_input = ""
        self.__user_input = ""

        self.schedule = PrettyTable()
        self.schedule.padding_width = 0
        self.schedule.field_names = ["#", "Theme", "Status", "Request time"]
        self.columns_percent = {
            "#": 0.05,
            "Theme": 0.5,
            "Status": 0.2,
            "Request time": 0.25,
        }

        self.schedule.add_row(["-1", "Nothing to show", "", ""])
        self.__has_entries = False

    def __update_table(self) -> None:
        curr_terminal_size = self.get_terminal_size()

        # Resize table, clear and reprint
        resize_table(self.schedule, curr_terminal_size[0], self.columns_percent)
        self.clear()

        print(self.schedule)
        print(f"Add new theme: {self.__user_input}", end="")

        # Flush stdout
        sys.stdout.flush()

        self.__prev_terminal_size = curr_terminal_size
        self.__prev_user_input = self.__user_input

    def __update_user_input(self) -> None:
        char = None

        if os.name == "nt":
            if msvcrt.kbhit():
                char = msvcrt.getwch()
        else:
            dr, _, _ = select([sys.stdin], [], [], 0)
            if dr:
                char = sys.stdin.read(1)

        if char is None:
            return "continue"

        match char:
            # ESC
            case "\x1b":
                return "exit"
            # Backspace
            case "\x08":
                self.__user_input = self.__user_input[:-1]
            # Paste from clipboard
            case "\x16":
                pass
            # Enter
            case "\r":
                if self.__user_input != "":
                    self.add_to_schedule(self.__user_input)
                self.__user_input = ""
            case k:
                self.__user_input += k

        return "continue"

    def update(self) -> str:
        terminal_size_changed = self.get_terminal_size() != self.__prev_terminal_size
        user_input_changed = self.__user_input != self.__prev_user_input

        if terminal_size_changed or user_input_changed:
            self.__update_table()

        return self.__update_user_input()

    def add_to_schedule(self, theme: str) -> None:
        # Remove "Nothing to show" placeholder
        if not self.__has_entries:
            self.schedule.del_row(-1)
            self.__has_entries = True

        # Add new row
        n = len(self.schedule._rows) + 1
        t = time.strftime("%H:%M:%S", time.localtime())

        self.schedule.add_row([n, theme, "Scheduled", t])

    @staticmethod
    def clear() -> None:
        if os.name == "nt":
            os.system("cls")
        else:
            os.system("clear")

    @staticmethod
    def get_terminal_size() -> tuple:
        size = os.get_terminal_size()
        return (size.columns, size.lines)
