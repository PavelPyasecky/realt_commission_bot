def redis_text(value):
    if value is None:
        return None
    if isinstance(value, (bytes, bytearray)):
        return value.decode()
    return str(value)


def redis_float(value):
    text = redis_text(value)
    if text is None:
        return None
    return float(text)
