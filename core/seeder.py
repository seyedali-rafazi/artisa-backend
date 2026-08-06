"""
Seeder — generates sample travel data for the next N days.

Called by the admin API endpoint.  All logic lives here so it can also be
imported and awaited from tests or management commands.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from itertools import permutations
from typing import Optional

from models.flight import City, Destination, Flight, FlightClass, PopularFlight
from models.transport import TransportRoute, TransportTrip, TransportType

# ── Cities ────────────────────────────────────────────────────────────────────
CITIES = [
    {"name": "تهران",     "code": "THR", "country": "ایران"},
    {"name": "مشهد",     "code": "MHD", "country": "ایران"},
    {"name": "اصفهان",   "code": "IFN", "country": "ایران"},
    {"name": "شیراز",    "code": "SYZ", "country": "ایران"},
    {"name": "کیش",      "code": "KIH", "country": "ایران"},
    {"name": "دبی",      "code": "DXB", "country": "امارات"},
    {"name": "استانبول", "code": "IST", "country": "ترکیه"},
]

# Codes that have no bus / train connectivity (international or island)
FLIGHT_ONLY_CODES = {"DXB", "IST", "KIH"}

# ── Airlines ──────────────────────────────────────────────────────────────────
AIRLINES = [
    {"name": "ماهان",         "code": "W5"},
    {"name": "ایران‌ایر",      "code": "IR"},
    {"name": "آتا",            "code": "I3"},
    {"name": "قشم‌ایر",        "code": "QB"},
    {"name": "زاگرس",          "code": "IZ"},
    {"name": "کاسپین",         "code": "CPN"},
]

BUS_COMPANIES   = ["ایران‌پیما", "تعاونی ۵", "رجا سفر", "سیروسفر", "ارس‌گشت"]
TRAIN_COMPANIES = ["راه‌آهن جمهوری اسلامی ایران", "رجا", "قطار سریع‌السیر"]

# ── Price & duration tables ───────────────────────────────────────────────────
# (origin_code, dest_code) → (min_price_toman, max_price_toman, duration_minutes)
FLIGHT_SPECS: dict[tuple, tuple] = {
    ("THR", "MHD"): (1_500_000,  3_500_000,  90),
    ("THR", "IFN"): (1_200_000,  2_800_000,  55),
    ("THR", "SYZ"): (1_400_000,  3_200_000,  80),
    ("THR", "KIH"): (1_800_000,  4_000_000, 100),
    ("THR", "DXB"): (3_500_000,  8_000_000, 130),
    ("THR", "IST"): (4_000_000,  9_500_000, 195),
    ("MHD", "IFN"): (1_300_000,  2_900_000,  80),
    ("MHD", "SYZ"): (1_600_000,  3_800_000,  95),
    ("MHD", "KIH"): (1_900_000,  4_200_000, 110),
    ("MHD", "DXB"): (3_800_000,  8_500_000, 150),
    ("MHD", "IST"): (4_500_000, 10_000_000, 210),
    ("IFN", "SYZ"): (1_100_000,  2_500_000,  55),
    ("IFN", "KIH"): (1_700_000,  3_800_000,  90),
    ("IFN", "DXB"): (3_000_000,  7_000_000, 120),
    ("SYZ", "KIH"): (1_500_000,  3_200_000,  75),
    ("SYZ", "DXB"): (3_200_000,  7_500_000, 115),
    ("KIH", "DXB"): (2_500_000,  5_500_000,  60),
    ("DXB", "IST"): (5_000_000, 12_000_000, 230),
}

BUS_SPECS: dict[tuple, tuple] = {
    ("تهران",   "مشهد"):   (250_000, 550_000, 780),
    ("تهران",   "اصفهان"): (120_000, 280_000, 240),
    ("تهران",   "شیراز"):  (200_000, 450_000, 540),
    ("مشهد",   "اصفهان"): (230_000, 500_000, 720),
    ("مشهد",   "شیراز"):  (280_000, 600_000, 900),
    ("اصفهان", "شیراز"):  (100_000, 250_000, 300),
}

TRAIN_SPECS: dict[tuple, tuple] = {
    ("تهران",   "مشهد"):   (200_000, 500_000, 510),
    ("تهران",   "اصفهان"): (100_000, 250_000, 360),
    ("تهران",   "شیراز"):  (180_000, 420_000, 600),
    ("مشهد",   "اصفهان"): (190_000, 440_000, 660),
    ("مشهد",   "شیراز"):  (220_000, 500_000, 780),
    ("اصفهان", "شیراز"):  ( 90_000, 220_000, 270),
}

FLIGHT_FEATURES = [
    ["WiFi", "وعده غذایی", "سرگرمی"],
    ["وعده غذایی", "بار مجاز ۲۰kg"],
    ["WiFi", "صندلی VIP"],
    ["بار مجاز ۱۵kg", "نوشیدنی"],
    ["WiFi", "وعده غذایی", "بار مجاز ۲۰kg", "سرگرمی"],
]
BUS_FEATURES   = [
    ["کولر", "WiFi", "سرویس بهداشتی"],
    ["کولر", "آب‌معدنی"],
    ["کولر", "WiFi"],
]
TRAIN_FEATURES = [
    ["کابین خصوصی", "رستوران"],
    ["واگن معمولی", "سرویس بهداشتی"],
    ["کوپه ۴ نفره"],
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _spec(table: dict, key: tuple) -> Optional[tuple]:
    """Return spec for a pair or its reverse; None if not present."""
    return table.get(key) or table.get((key[1], key[0]))


def _duration_str(minutes: int) -> str:
    return f"{minutes // 60}h {minutes % 60}m"


def _random_dep(base_date: datetime, hour_min: int = 5, hour_max: int = 22) -> datetime:
    hour   = random.randint(hour_min, hour_max)
    minute = random.choice([0, 15, 30, 45])
    return base_date.replace(hour=hour, minute=minute, second=0, microsecond=0)


# ── Public seeder functions ───────────────────────────────────────────────────

async def seed_cities() -> int:
    """Insert cities that don't exist yet. Returns number created."""
    created = 0
    for c in CITIES:
        if not await City.find_one(City.code == c["code"]):
            await City(code=c["code"], name=c["name"], country=c["country"]).insert()
            created += 1
    return created


async def seed_popular_routes() -> dict:
    """Seed PopularFlight and TransportRoute records (once). Returns counts."""
    flight_count = transport_count = 0

    if await PopularFlight.find_all().count() == 0:
        rows = [
            ("تهران",   "مشهد",     "THR", "MHD", "از ۱,۵۰۰,۰۰۰ تومان", 1),
            ("تهران",   "دبی",      "THR", "DXB", "از ۳,۵۰۰,۰۰۰ تومان", 2),
            ("تهران",   "استانبول", "THR", "IST", "از ۴,۰۰۰,۰۰۰ تومان", 3),
            ("مشهد",   "تهران",    "MHD", "THR", "از ۱,۵۰۰,۰۰۰ تومان", 4),
            ("اصفهان", "تهران",    "IFN", "THR", "از ۱,۲۰۰,۰۰۰ تومان", 5),
            ("شیراز",  "دبی",      "SYZ", "DXB", "از ۳,۲۰۰,۰۰۰ تومان", 6),
        ]
        for fc, tc, fcode, tcode, price, order in rows:
            await PopularFlight(
                from_city=fc, to_city=tc,
                from_code=fcode, to_code=tcode,
                price=price, order=order,
            ).insert()
            flight_count += 1

    if await TransportRoute.find_all().count() == 0:
        rows = [
            (TransportType.BUS,   "تهران",   "مشهد",   "از ۲۵۰,۰۰۰ تومان", 1),
            (TransportType.BUS,   "تهران",   "اصفهان", "از ۱۲۰,۰۰۰ تومان", 2),
            (TransportType.BUS,   "تهران",   "شیراز",  "از ۲۰۰,۰۰۰ تومان", 3),
            (TransportType.TRAIN, "تهران",   "مشهد",   "از ۲۰۰,۰۰۰ تومان", 4),
            (TransportType.TRAIN, "تهران",   "اصفهان", "از ۱۰۰,۰۰۰ تومان", 5),
            (TransportType.TRAIN, "مشهد",   "تهران",  "از ۲۰۰,۰۰۰ تومان", 6),
        ]
        for ttype, fc, tc, price, order in rows:
            await TransportRoute(
                transport_type=ttype, from_city=fc, to_city=tc,
                price=price, order=order,
            ).insert()
            transport_count += 1

    return {"popular_flights": flight_count, "popular_routes": transport_count}


async def seed_flights(days: int = 7, trips_per_pair: int = 3) -> int:
    """Generate Flight documents for the next `days` days. Returns count created."""
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    codes  = [c["code"] for c in CITIES]
    count  = 0

    for day_offset in range(days):
        base = today + timedelta(days=day_offset)

        for origin, dest in permutations(codes, 2):
            spec = _spec(FLIGHT_SPECS, (origin, dest))
            min_p, max_p, dur = spec if spec else (2_000_000, 6_000_000, 150)

            for _ in range(trips_per_pair):
                airline = random.choice(AIRLINES)
                fn      = f"{airline['code']}{random.randint(100, 999)}"

                # Skip if same flight number on same route same day already exists
                exists = await Flight.find_one(
                    Flight.flight_number == fn,
                    Flight.origin == origin,
                    Flight.destination == dest,
                    Flight.departure_time >= base,
                    Flight.departure_time < base + timedelta(days=1),
                )
                if exists:
                    continue

                dep = _random_dep(base)
                arr = dep + timedelta(minutes=dur + random.randint(-5, 10))

                await Flight(
                    airline=airline["name"],
                    flight_number=fn,
                    origin=origin,
                    destination=dest,
                    departure_time=dep,
                    arrival_time=arr,
                    duration=_duration_str(dur),
                    price=random.randint(min_p, max_p),
                    available_seats=random.randint(10, 180),
                    stops=random.choices([0, 1], weights=[80, 20])[0],
                    flight_class=random.choice(list(FlightClass)),
                    features=random.choice(FLIGHT_FEATURES),
                    is_active=True,
                ).insert()
                count += 1

    return count


async def seed_transport(days: int = 7, trips_per_pair: int = 3) -> dict:
    """Generate bus and train TransportTrip documents. Returns counts."""
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    domestic = [c["name"] for c in CITIES if c["code"] not in FLIGHT_ONLY_CODES]
    bus_count = train_count = 0

    for day_offset in range(days):
        base = today + timedelta(days=day_offset)

        for origin, dest in permutations(domestic, 2):
            # ── Bus ──────────────────────────────────────────────────────────
            spec = _spec(BUS_SPECS, (origin, dest))
            if spec:
                min_p, max_p, dur = spec
                for _ in range(trips_per_pair):
                    company = random.choice(BUS_COMPANIES)
                    tn      = f"BUS{random.randint(100, 999)}"

                    exists = await TransportTrip.find_one(
                        TransportTrip.transport_type == TransportType.BUS,
                        TransportTrip.trip_number == tn,
                        TransportTrip.origin == origin,
                        TransportTrip.destination == dest,
                        TransportTrip.departure_time >= base,
                        TransportTrip.departure_time < base + timedelta(days=1),
                    )
                    if exists:
                        continue

                    dep = _random_dep(base, 6, 23)
                    arr = dep + timedelta(minutes=dur)
                    await TransportTrip(
                        transport_type=TransportType.BUS,
                        company=company,
                        trip_number=tn,
                        origin=origin,
                        destination=dest,
                        departure_time=dep,
                        arrival_time=arr,
                        duration=_duration_str(dur),
                        price=random.randint(min_p, max_p),
                        available_seats=random.randint(10, 44),
                        features=random.choice(BUS_FEATURES),
                        is_active=True,
                    ).insert()
                    bus_count += 1

            # ── Train ─────────────────────────────────────────────────────────
            spec = _spec(TRAIN_SPECS, (origin, dest))
            if spec:
                min_p, max_p, dur = spec
                for _ in range(trips_per_pair):
                    company = random.choice(TRAIN_COMPANIES)
                    tn      = f"TRN{random.randint(100, 999)}"

                    exists = await TransportTrip.find_one(
                        TransportTrip.transport_type == TransportType.TRAIN,
                        TransportTrip.trip_number == tn,
                        TransportTrip.origin == origin,
                        TransportTrip.destination == dest,
                        TransportTrip.departure_time >= base,
                        TransportTrip.departure_time < base + timedelta(days=1),
                    )
                    if exists:
                        continue

                    dep = _random_dep(base, 6, 22)
                    arr = dep + timedelta(minutes=dur)
                    await TransportTrip(
                        transport_type=TransportType.TRAIN,
                        company=company,
                        trip_number=tn,
                        origin=origin,
                        destination=dest,
                        departure_time=dep,
                        arrival_time=arr,
                        duration=_duration_str(dur),
                        price=random.randint(min_p, max_p),
                        available_seats=random.randint(10, 200),
                        features=random.choice(TRAIN_FEATURES),
                        is_active=True,
                    ).insert()
                    train_count += 1

    return {"bus": bus_count, "train": train_count}


async def clean_future_data(days: int = 7) -> dict:
    """Delete all flights/trips departing within the next `days` days."""
    today  = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    cutoff = today + timedelta(days=days)
    r1 = await Flight.find(
        Flight.departure_time >= today,
        Flight.departure_time < cutoff,
    ).delete()
    r2 = await TransportTrip.find(
        TransportTrip.departure_time >= today,
        TransportTrip.departure_time < cutoff,
    ).delete()
    return {
        "deleted_flights": r1.deleted_count,
        "deleted_transport_trips": r2.deleted_count,
    }


async def run_full_seed(days: int = 7, trips_per_pair: int = 3, clean: bool = False) -> dict:
    """
    Top-level function — called by the API endpoint.
    Returns a summary dict of everything that was created.
    """
    result: dict = {}

    if clean:
        result["cleaned"] = await clean_future_data(days)

    result["cities_created"]   = await seed_cities()
    result["popular"]          = await seed_popular_routes()
    result["flights_created"]  = await seed_flights(days, trips_per_pair)
    result["transport_created"] = await seed_transport(days, trips_per_pair)
    result["days_covered"]     = days
    result["trips_per_pair"]   = trips_per_pair
    return result

# Made with Bob
