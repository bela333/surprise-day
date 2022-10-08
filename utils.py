import datetime
import random
import typing as t


# FIXME: Why not use datetime.date instead?
def normalize_datetime(t: datetime.datetime) -> datetime.datetime:
    """
    Normalize a datetime by removing the time.
    """
    return t.replace(hour=0, minute=0, second=0, microsecond=0)


def random_surprise_day(now: datetime.datetime) -> datetime.datetime:
    """Generate a random surprise day datetime."""

    now = normalize_datetime(now)

    start_date = now + datetime.timedelta(days=7)

    end_date = now.replace(year=now.year + 1)
    end_date = end_date - datetime.timedelta(days=1)

    t = random.random()

    surprise_day = normalize_datetime(
        datetime.datetime.fromtimestamp(start_date.timestamp() * t + end_date.timestamp() * (1 - t))
    )
    return surprise_day


def generate_random_days() -> t.Tuple[datetime.datetime, datetime.datetime]:
    now = normalize_datetime(datetime.datetime.now(datetime.timezone.utc))
    surprise_day = random_surprise_day(now)
    reset_day = now.replace(year=now.year + 1)
    return (surprise_day, reset_day)
