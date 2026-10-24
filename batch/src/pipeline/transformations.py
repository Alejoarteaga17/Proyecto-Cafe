"""Pure transformations shared by local tests and AWS Glue jobs."""

from collections import defaultdict
from copy import deepcopy

from src.common.coffee_batch_validator import BatchValidationError, validate_row


class TransformationResult:
    def __init__(self, valid_rows, rejected_rows, duplicate_rows):
        self.valid_rows = valid_rows
        self.rejected_rows = rejected_rows
        self.duplicate_rows = duplicate_rows


def bronze_to_silver(rows):
    """Validate, normalize and deduplicate historical Bronze rows."""
    valid_rows = []
    rejected_rows = []
    duplicate_rows = []
    seen = set()

    for row_number, row in enumerate(rows, start=2):
        try:
            normalized = validate_row(row, row_number)
        except BatchValidationError as error:
            rejected_rows.append({
                "row_number": row_number,
                "record": deepcopy(row),
                "errors": error.errors,
            })
            continue

        duplicate_key = tuple(sorted(normalized.items()))
        if duplicate_key in seen:
            duplicate_rows.append({
                "row_number": row_number,
                "record": normalized,
                "reason": "duplicate_record",
            })
            continue
        seen.add(duplicate_key)
        valid_rows.append(normalized)

    return TransformationResult(valid_rows, rejected_rows, duplicate_rows)


def silver_to_gold(rows):
    """Prepare documented analytical summaries from Silver historical rows."""
    groups = defaultdict(list)
    for row in rows:
        groups[(row["Location"], row["YEAR"], row["MM"])].append(row)

    summaries = []
    for (location, year, month), group in sorted(groups.items()):
        summaries.append({
            "Location": location,
            "YEAR": year,
            "MM": month,
            "record_count": len(group),
            "avg_temp_max": _average(group, "Temp_Max"),
            "avg_temp_min": _average(group, "Temp_Min"),
            "avg_humidity": _average(group, "Humidity"),
            "total_precipitation_mm": round(
                sum(row["Precipitation_mm"] for row in group), 6),
            "avg_solar_radiation": _average(group, "Solar_Radiation"),
            "avg_close_usd_60kg": _average(group, "Close_USD_60kg"),
        })
    return summaries


def _average(rows, field):
    return round(sum(row[field] for row in rows) / len(rows), 6)
