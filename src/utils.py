from prettytable import PrettyTable

import os
import re


def terminal_get_size() -> tuple:
    """Get terminal size"""
    size = os.get_terminal_size()
    return (size.columns, size.lines)


def terminal_run(command: str) -> None:
    """Run command in terminal."""
    if os.name == "nt":
        os.system(f"start cmd /c {command}")
    else:
        os.system(f"sh -c {command}")


def table_resize(
    table: PrettyTable, terminal_columns: int, columns_percent: dict
) -> None:
    """Resize table to fit terminal size"""
    # Account for borders and padding
    columns = terminal_columns
    columns -= len(table._field_names) + 1
    columns -= 2 * len(table._field_names) * table._padding_width

    # Set new min width
    table._min_width = dict(
        (name, int(columns * percent)) for name, percent in columns_percent.items()
    )
    table._max_width = table._min_width


def toml_interpolate(string: str, configs: list) -> str:
    """Interpolate TOML string with config variables."""
    interpolation_candidates = re.findall(r"\%(.+?)\%", string)

    for candidate in interpolation_candidates:
        path = candidate.split("/")

        for k in configs:
            value = k

            for key in path:
                if key in value:
                    value = value.get(key, None)
                else:
                    value = None
                    break

            if value:
                string = string.replace(f"%{candidate}%", value)
                break

    return string
