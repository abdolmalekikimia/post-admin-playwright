"""Helper functions: date builders, mock data fixtures, Persian formatters."""
from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from typing import Any


def iso_now() -> str:
    """Current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def make_discrepancy_payload(
    barcodes: list[str] | None = None,
    total_count: int = 1,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """Generate a valid contract-compliant response for /api/admin/parcels/discrepancies."""
    if barcodes is None:
        barcodes = ["111122223333444455556677"]

    items = []
    for i, barcode in enumerate(barcodes):
        items.append({
            "parcelBarcode": barcode,
            "parcelCreatedAtUtc": iso_now(),
            "readings": [
                {
                    "readingId": f"read-{i + 1}",
                    "deviceId": f"DEV-00{i + 1}",
                    "exchangeCenterCode": "10001",
                    "edgeEventTimeUtc": iso_now(),
                    "coreReceiveTimeUtc": iso_now(),
                    "discrepancies": [
                        {
                            "type": "WeightDiscrepancy",
                            "registeredValue": "500g",
                            "measuredValue": "750g",
                            "recordedPriceRial": 250000,
                            "recalculatedPriceRial": 320000,
                            "postFetchedAtUtc": iso_now(),
                        },
                        {
                            "type": "BoxSizeDiscrepancy",
                            "registeredValue": "20x15x10",
                            "measuredValue": "25x20x15",
                            "recordedPriceRial": 250000,
                            "recalculatedPriceRial": 320000,
                            "postFetchedAtUtc": iso_now(),
                        },
                    ],
                }
            ],
        })

    return {
        "items": items,
        "page": page,
        "pageSize": page_size,
        "totalCount": total_count,
        "totalRecordedPriceRial": sum(d["recordedPriceRial"] for item in items for reading in item["readings"] for d in reading["discrepancies"]),
        "totalRecalculatedPriceRial": sum(d["recalculatedPriceRial"] for item in items for reading in item["readings"] for d in reading["discrepancies"]),
    }


def make_empty_discrepancy_payload() -> dict[str, Any]:
    """Generate an empty discrepancy response."""
    return {
        "items": [],
        "page": 1,
        "pageSize": 20,
        "totalCount": 0,
        "totalRecordedPriceRial": 0,
        "totalRecalculatedPriceRial": 0,
    }


def make_devices_payload(center_code: str = "10001") -> dict[str, Any]:
    """Device list including the fields validated by the admin frontend."""
    return {
        "items": [
            {
                "deviceId": f"DEV-00{i}", "deviceName": name,
                "logicalCode": f"QA-{i}", "deviceType": "Sorter",
                "exchangeCenterCode": center_code, "activationStatus": "Active",
                "createdAt": iso_now(), "rowVersion": "AAAAAAAB",
            }
            for i, name in enumerate(["دستگاه سورت ۱", "دستگاه سورت ۲"], 1)
        ],
        "page": 1, "pageSize": 50, "totalCount": 2,
    }


def make_postal_codes_payload() -> dict[str, Any]:
    """Generate a valid contract-compliant response for /api/admin/postal-codes (exchange centers).
    
    The API returns a paged collection with page, pageSize, and totalCount.
    The combobox uses `code` as the exchange center code and `name` for display.
    """
    return {
        "items": [
            {
                "code": "10001",
                "province": "تهران",
                "county": "تهران",
                "city": "تهران",
                "name": "مرکز مبادله تهران",
            },
            {
                "code": "10002",
                "province": "اصفهان",
                "county": "اصفهان",
                "city": "اصفهان",
                "name": "مرکز مبادله اصفهان",
            },
        ],
        "page": 1,
        "pageSize": 50,
        "totalCount": 2,
    }
