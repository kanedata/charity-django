def scale(values: list[float | int | None]) -> int:
    max_value = max(abs(value or 0) for value in values)
    if max_value > 10_000_000:
        return 1_000_000
    if max_value > 10_000:
        return 1_000
    return 1


def scale_value(value: float | int | None, scale: int) -> float:
    if value is None:
        value = 0
    return value / float(scale)


def scale_value_format(
    value: float | int | None,
    scale: int,
    with_currency: bool = True,
    if_zero: str = "-",
):
    prefix = "£" if with_currency else ""
    suffix = ""
    if scale == 1_000_000:
        suffix = "m"
    elif scale == 1_000:
        suffix = "k"
    format_str = "{:,.1f}" if scale > 1 else "{:,.0f}"
    value = scale_value(value, scale)
    if value == 0 and if_zero:
        return if_zero
    return prefix + format_str.format(value) + suffix
