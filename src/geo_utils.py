import math
from collections.abc import Iterable
from functools import cache

from pyproj import Transformer
from shapely.geometry import Point, shape
from shapely.geometry.base import BaseGeometry

EARTH_RADIUS_METERS = 6_371_000


@cache
def _utm_transformer(zone_number: int) -> Transformer:
    source_crs = "EPSG:25830" if zone_number == 30 else f"EPSG:326{zone_number:02d}"
    return Transformer.from_crs(source_crs, "EPSG:4326", always_xy=True)


def utm_to_latlon(easting: float, northing: float, zone_number: int = 30) -> tuple[float, float]:
    """Convert UTM coordinates to latitude and longitude.

    Valencia publishes this dataset in ETRS89 / UTM zone 30N (EPSG:25830).
    Other northern UTM zones fall back to their WGS84 EPSG definition.
    """
    lon, lat = _utm_transformer(zone_number).transform(easting, northing)
    return float(lat), float(lon)


def haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    lat1_rad, lon1_rad = math.radians(lat1), math.radians(lon1)
    lat2_rad, lon2_rad = math.radians(lat2), math.radians(lon2)
    d_lat = lat2_rad - lat1_rad
    d_lon = lon2_rad - lon1_rad
    a = math.sin(d_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(d_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return EARTH_RADIUS_METERS * c


def nearest_distance_meters(
    lat: float,
    lon: float,
    candidate_points: Iterable[tuple[float, float]],
) -> float:
    points = list(candidate_points)
    if not points:
        raise ValueError("candidate_points must contain at least one point")
    return min(haversine_meters(lat, lon, p_lat, p_lon) for p_lat, p_lon in points)


def shape_geometry(geometry: dict) -> BaseGeometry:
    result = shape(geometry)
    if result.is_empty:
        raise ValueError("Geometry is empty")
    if not result.is_valid:
        result = result.buffer(0)
    if result.is_empty:
        raise ValueError("Geometry could not be repaired")
    return result


def geometry_covers_point(geometry: BaseGeometry, lon: float, lat: float) -> bool:
    return bool(geometry.covers(Point(lon, lat)))


def point_in_geojson_geometry(lon: float, lat: float, geometry: dict) -> bool:
    return geometry_covers_point(shape_geometry(geometry), lon, lat)


def polygon_bbox(geometry: dict) -> tuple[float, float, float, float]:
    bounds = shape_geometry(geometry).bounds
    return tuple(float(value) for value in bounds)


def grid_points_in_geometry(
    geometry: dict,
    step_meters: int,
    center_lat: float,
) -> list[tuple[float, float]]:
    if step_meters <= 0:
        raise ValueError("step_meters must be positive")

    polygon = shape_geometry(geometry)
    min_lon, min_lat, max_lon, max_lat = polygon.bounds
    lat_step = step_meters / 111_320
    lon_step = step_meters / (111_320 * math.cos(math.radians(center_lat)))

    points: list[tuple[float, float]] = []
    lat = min_lat + lat_step / 2
    while lat <= max_lat:
        lon = min_lon + lon_step / 2
        while lon <= max_lon:
            if geometry_covers_point(polygon, lon, lat):
                points.append((lat, lon))
            lon += lon_step
        lat += lat_step

    if not points:
        representative = polygon.representative_point()
        points.append((float(representative.y), float(representative.x)))
    return points


def geometry_centroid_fallback(geometry: dict) -> tuple[float, float]:
    representative = shape_geometry(geometry).representative_point()
    return float(representative.x), float(representative.y)
