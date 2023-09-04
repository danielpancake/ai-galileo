import os
import platform
import re


class StatusCodes:
    ADDED = "added"
    QUEUED = "queued"
    COMPLETED = "completed"
    FAILED = "failed"


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


def run_in_terminal(command: str):
    """Run command in terminal."""
    match platform.system():
        case "Windows":
            os.system(f"start cmd /c {command}")

        case "Linux":
            os.system(f"sh -c {command}")

        case _:
            raise NotImplementedError("Unsupported platform")
