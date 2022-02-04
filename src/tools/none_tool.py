def isNone(value):
    return value is None


def NotNone(value):
    return value is not None


def ifNone(value, none):
    return value if value is not None else none


def ifNotNone(value, none):
    return value if value is None else none
