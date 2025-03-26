def truncate_string(field: str, max_len: int) -> str:
    """Обрезает строку до заданной длины и добавляет троеточие,
    если строка превышает максимальную длину"""
    return field[:max_len] + '...' if len(field) > max_len else field
