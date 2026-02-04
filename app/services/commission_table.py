COMMISSION_TABLE_IN_BASIC_VALUE = (
    (0, 4200, 3.0),
    (4200, 5000, 2.5),
    (5000, 8000, 2.0),
    (8000, 12000, 1.7),
    (12000, 16500, 1.3),
    (16500, None, 1.0),
)


def get_commission_percent(cost_in_basic_value):
    for start, end, percent in COMMISSION_TABLE_IN_BASIC_VALUE:
        if end is None and cost_in_basic_value >= start:
            return percent
        if end is not None and start <= cost_in_basic_value < end:
            return percent
    return COMMISSION_TABLE_IN_BASIC_VALUE[-1][2]
