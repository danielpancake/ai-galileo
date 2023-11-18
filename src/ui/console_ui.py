from prettytable import PrettyTable
from utils import table_resize, terminal_get_size

import os
import sys

if os.name == "nt":
    import msvcrt
else:
    from select import select

    import atexit
    import sys
    import termios


class ConsolePanel:
    def __init__(self):
        self.requires_redraw = False

    def update(self):
        pass

    def redraw(self):
        pass


class ConsoleUI:
    def __init__(self, panels: list):
        self.panels = panels

    def add_panel(self, panel: ConsolePanel):
        self.panels.append(panel)

    def update(self):
        for panel in self.panels:
            panel.update()

        # If any panel requires a redraw, redraw all panels
        if any([panel.requires_redraw for panel in self.panels]):
            self.clear()

            for panel in self.panels:
                panel.redraw()
                panel.requires_redraw = False

    @staticmethod
    def clear():
        print("\033[H\033[J", end="")


class ScheduleTable(ConsolePanel):
    def __init__(self):
        super().__init__()

        self.schedule = PrettyTable()
        self.schedule.padding_width = 0
        self.schedule.field_names = ["ID", "Theme", "Status", "Author", "Request time"]
        self.schedule.align["Theme"] = "l"

        self.columns_percent = {
            "ID": 0.1,
            "Theme": 0.6,
            "Status": 0.1,
            "Author": 0.1,
            "Request time": 0.1,
        }

        self.schedule.add_row(["", "Nothing to show", "", "", ""])

        self.__prev_terminal_cols = None

    def pull_data(self, data: list) -> None:
        self.schedule.clear_rows()
        self.schedule.add_rows(data)

        if len(data) == 0:
            self.schedule.add_row(["", "Nothing to show", "", "", ""])

        self.requires_redraw = True

    def update(self) -> None:
        if self.__prev_terminal_cols != terminal_get_size()[0]:
            self.requires_redraw = True

    def redraw(self):
        terminal_cols = terminal_get_size()[0]

        table_resize(self.schedule, terminal_cols, self.columns_percent)
        print(self.schedule)

        self.__prev_terminal_cols = terminal_cols


class InputLine(ConsolePanel):
    def __init__(
        self,
        prompt: str,
        enter_callback: callable = None,
        escape_callback: callable = None,
    ):
        super().__init__()
        self.prompt = prompt
        self.enter_callback = enter_callback
        self.escape_callback = escape_callback

        self.user_input = ""

    def update(self) -> None:
        char = None

        if os.name == "nt":
            if msvcrt.kbhit():
                char = msvcrt.getwch()
        else:
            dr, _, _ = select([sys.stdin], [], [], 0)
            if dr:
                char = sys.stdin.read(1)

        if char is None:
            return

        match char:
            # ESC
            case "\x1b":
                if self.escape_callback is not None:
                    self.escape_callback()
            # Backspace
            case "\x08":
                self.user_input = self.user_input[:-1]
                self.requires_redraw = True
            # Paste from clipboard
            case "\x16":
                pass
            # Enter
            case "\r":
                if self.enter_callback is not None:
                    self.enter_callback(self.user_input)
                self.user_input = ""
                self.requires_redraw = True
            case k:
                self.user_input += k
                self.requires_redraw = True

    def redraw(self):
        print(f"{self.prompt}{self.user_input}", end="")
        sys.stdout.flush()
