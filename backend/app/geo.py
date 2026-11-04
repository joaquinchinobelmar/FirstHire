"""Local-first geography for the North East of England.

Distances are straight-line miles between town centres — good enough to keep
opportunities local (and keep graduates out of the "just move to London" trap).
"""

from math import asin, cos, radians, sin, sqrt

REGION = "North East England"

# Approximate town-centre coordinates (lat, lng)
TOWNS: dict[str, tuple[float, float]] = {
    "Newcastle upon Tyne": (54.9783, -1.6178),
    "Gateshead": (54.9527, -1.6034),
    "Sunderland": (54.9069, -1.3838),
    "Durham": (54.7761, -1.5733),
    "Middlesbrough": (54.5742, -1.2350),
    "North Shields": (55.0177, -1.4486),
    "South Shields": (54.9986, -1.4323),
    "Tynemouth": (55.0179, -1.4256),
    "Wallsend": (54.9910, -1.5340),
    "Whitley Bay": (55.0446, -1.4475),
    "Jarrow": (54.9803, -1.4847),
    "Washington": (54.9000, -1.5167),
    "Chester-le-Street": (54.8586, -1.5741),
    "Hexham": (54.9719, -2.1019),
    "Morpeth": (55.1683, -1.6880),
    "Cramlington": (55.0860, -1.5850),
    "Ashington": (55.1810, -1.5680),
    "Blaydon": (54.9646, -1.7126),
    "Consett": (54.8540, -1.8310),
    "Seaham": (54.8390, -1.3450),
    "Peterlee": (54.7600, -1.3360),
    "Hartlepool": (54.6863, -1.2129),
    "Stockton-on-Tees": (54.5705, -1.3290),
    "Darlington": (54.5236, -1.5595),
}


def town_names() -> list[str]:
    return sorted(TOWNS)


def miles_between(town_a: str, town_b: str) -> float | None:
    a, b = TOWNS.get(town_a), TOWNS.get(town_b)
    if not a or not b:
        return None
    lat1, lng1, lat2, lng2 = map(radians, (*a, *b))
    h = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lng2 - lng1) / 2) ** 2
    return round(2 * 3958.8 * asin(sqrt(h)), 1)


def is_in_region(town: str) -> bool:
    return town in TOWNS
