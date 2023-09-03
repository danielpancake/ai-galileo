import re


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
