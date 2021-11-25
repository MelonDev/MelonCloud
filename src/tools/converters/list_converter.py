def list_to_set_original(data):
    return set(data) if data is not None else None


def list_to_set(data):
    return str(set(data)).replace("'", "") if data is not None else None
