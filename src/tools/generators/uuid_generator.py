from uuid import UUID
import uuid


def is_valid_uuid(target, version=4) -> bool:
    try:
        return str(UUID(target, version=version)) == target
    except ValueError:
        return False


def generate_uuid():
    return uuid.uuid4()
