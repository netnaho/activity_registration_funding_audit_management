def mask_id_number(value: str) -> str:
    if len(value) <= 4:
        return "*" * len(value)
    return f"{value[:2]}{'*' * (len(value) - 4)}{value[-2:]}"


def mask_contact(value: str) -> str:
    if len(value) <= 4:
        return "*" * len(value)
    return f"{value[:3]}{'*' * (len(value) - 5)}{value[-2:]}"
