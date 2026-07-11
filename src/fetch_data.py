import hashlib
import json
import ssl
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import truststore

from config import (
    BIKE_PARKING_URL,
    BIKE_RAW_PATH,
    NEIGHBORHOODS_RAW_PATH,
    RAW_DIR,
    SOURCE_MANIFEST_PATH,
    VULNERABILITY_GEOJSON_URL,
)

SSL_CONTEXT = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
USER_AGENT = "valencia-bike-equity-analysis/1.0"


def request_json(url: str, attempts: int = 3) -> dict:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    last_error: Exception | None = None

    for attempt in range(attempts):
        try:
            with urlopen(request, timeout=45, context=SSL_CONTEXT) as response:
                return json.loads(response.read().decode("utf-8"))
        except (URLError, TimeoutError, json.JSONDecodeError) as error:
            last_error = error
            if attempt < attempts - 1:
                time.sleep(2**attempt)

    raise RuntimeError(f"Could not download JSON after {attempts} attempts: {url}") from last_error


def write_json(payload: dict, path: Path) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch_bike_parking() -> dict:
    all_features = []
    offset = 0
    page_size = 2000

    while True:
        params = {
            "f": "json",
            "outFields": "*",
            "where": "1=1",
            "resultOffset": offset,
            "resultRecordCount": page_size,
            "orderByFields": "objectid",
        }
        page = request_json(f"{BIKE_PARKING_URL}?{urlencode(params)}")
        features = page.get("features", [])
        all_features.extend(features)

        if len(features) < page_size or not page.get("exceededTransferLimit", False):
            break
        offset += page_size

    payload = {
        "source": BIKE_PARKING_URL,
        "feature_count": len(all_features),
        "features": all_features,
    }
    write_json(payload, BIKE_RAW_PATH)
    return payload


def fetch_neighborhoods() -> dict:
    payload = request_json(VULNERABILITY_GEOJSON_URL)
    write_json(payload, NEIGHBORHOODS_RAW_PATH)
    return payload


def write_source_manifest(bike_count: int, neighborhood_count: int) -> None:
    manifest = {
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "sources": [
            {
                "name": "Aparcamientos de bicicleta",
                "url": BIKE_PARKING_URL,
                "records": bike_count,
                "file": BIKE_RAW_PATH.name,
                "sha256": sha256_file(BIKE_RAW_PATH),
            },
            {
                "name": "Vulnerabilidad por barrios",
                "url": VULNERABILITY_GEOJSON_URL,
                "records": neighborhood_count,
                "file": NEIGHBORHOODS_RAW_PATH.name,
                "sha256": sha256_file(NEIGHBORHOODS_RAW_PATH),
            },
        ],
    }
    write_json(manifest, SOURCE_MANIFEST_PATH)


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    bike_payload = fetch_bike_parking()
    neighborhoods_payload = fetch_neighborhoods()
    neighborhood_count = len(neighborhoods_payload.get("features", []))
    write_source_manifest(bike_payload["feature_count"], neighborhood_count)

    print(f"Downloaded {bike_payload['feature_count']} bike parking records")
    print(f"Downloaded {neighborhood_count} neighborhood polygons")


if __name__ == "__main__":
    main()
