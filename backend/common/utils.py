from datetime import datetime, time, timedelta
from decimal import Decimal
from uuid import uuid4

from django.utils import timezone


def generate_reference(prefix):
    return f"{prefix}-{uuid4().hex[:10].upper()}"


def normalize_optional_text(value):
    return value.strip() if isinstance(value, str) and value.strip() else None


def get_date_range(range_type, start=None, end=None):
    now = timezone.localtime()
    today = now.date()
    if range_type == "daily":
        start_date = today
        end_date = today
    elif range_type == "weekly":
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
    elif range_type == "monthly":
        start_date = today.replace(day=1)
        if start_date.month == 12:
            end_date = start_date.replace(year=start_date.year + 1, month=1) - timedelta(days=1)
        else:
            end_date = start_date.replace(month=start_date.month + 1) - timedelta(days=1)
    elif range_type == "annual":
        start_date = today.replace(month=1, day=1)
        end_date = today.replace(month=12, day=31)
    elif range_type == "custom" and start and end:
        start_date = start
        end_date = end
    else:
        raise ValueError("Unsupported report range.")

    start_dt = timezone.make_aware(datetime.combine(start_date, time.min))
    end_dt = timezone.make_aware(datetime.combine(end_date, time.max))
    return start_dt, end_dt


def quantize_money(value):
    return Decimal(value).quantize(Decimal("0.01"))
