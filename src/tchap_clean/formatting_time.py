from datetime import datetime, timedelta


def convert_unix_time(time_as_int):
    """
    Convert time from timestamp (ie seconds) to standard date

    Args:
        time_as_int (int): nix time, with either 10 or 13 digits

    Returns:
        date (string) format ("%Y-%m-%d %H:%M")

    Example:
        >>> convert_unix_time(1760297400000)
        '2025-10-12 21:30'
        >>> convert_unix_time(1760297400)
        '2025-10-12 21:30'
    """
    time_as_int = int(time_as_int)

    if time_as_int >= 1e12:
        time_as_int = time_as_int / 1000

    time = datetime.fromtimestamp(time_as_int) + timedelta(hours=+2)
    return time.strftime("%Y-%m-%d %H:%M")