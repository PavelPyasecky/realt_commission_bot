from decimal import Decimal, ROUND_HALF_UP


def round_half_up(value, digits=2):
    quant = Decimal("1") if digits == 0 else Decimal("1." + ("0" * digits))
    return Decimal(str(value)).quantize(quant, rounding=ROUND_HALF_UP)


def round_number(value, digits=2):
    rounded = round_half_up(value, digits=digits)
    if rounded == rounded.to_integral_value():
        return str(int(rounded))
    return f"{rounded:.{digits}f}"


def round_fixed(value, digits=2):
    rounded = round_half_up(value, digits=digits)
    return f"{rounded:.{digits}f}"
