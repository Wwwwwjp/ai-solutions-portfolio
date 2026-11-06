"""Generate deterministic, entirely fictional enterprise activity data."""

from __future__ import annotations

import csv
from datetime import date, timedelta
from pathlib import Path
import random


SEED = 20261106
OUTPUT_DIR = Path(__file__).resolve().parent / "data"
COMPANY_COUNT = 42
AS_OF = date(2025, 6, 30)

SECTORS = [
    "advanced_manufacturing",
    "biotechnology",
    "enterprise_software",
    "new_energy",
    "advanced_materials",
]
PROVINCES = ["Jiangsu", "Shanghai", "Zhejiang", "Guangdong", "Anhui"]
NAME_ROOTS = [
    "Northstar",
    "BluePeak",
    "Helio",
    "Aster",
    "Kinetic",
    "Lattice",
    "Orchid",
    "Cobalt",
    "Morrow",
    "Vector",
    "Sable",
    "Harbor",
    "Summit",
    "Fusion",
]
NAME_SUFFIXES = ["Systems", "Materials", "Robotics", "Labs", "Dynamics"]


def random_date(rng: random.Random, start: date, end: date) -> date:
    return start + timedelta(days=rng.randrange((end - start).days + 1))


def company_rows(rng: random.Random) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    names: set[str] = set()
    for index in range(COMPANY_COUNT):
        root = NAME_ROOTS[index % len(NAME_ROOTS)]
        suffix = NAME_SUFFIXES[(index // len(NAME_ROOTS)) % len(NAME_SUFFIXES)]
        name = f"{root} {suffix}"
        serial = 2
        while name in names:
            name = f"{root} {suffix} {serial}"
            serial += 1
        names.add(name)

        founded = random_date(rng, date(2004, 1, 1), date(2022, 12, 31))
        employees = max(8, int(rng.lognormvariate(4.8, 0.8)))
        capital = round(rng.uniform(5, 700), 2)
        rd_ratio = round(rng.uniform(0.02, 0.42), 4)
        revenue = round(rng.uniform(20, 3_500), 2)
        rows.append(
            {
                "company_id": f"SYN-{index + 1:03d}",
                "company_name": name,
                "sector": SECTORS[index % len(SECTORS)],
                "province": PROVINCES[index % len(PROVINCES)],
                "founded_at": founded.isoformat(),
                "employees": str(employees),
                "registered_capital_million_cny": (
                    "" if rng.random() < 0.10 else f"{capital:.2f}"
                ),
                "rd_staff_ratio": (
                    "" if rng.random() < 0.08 else f"{rd_ratio:.4f}"
                ),
                "revenue_million_cny": (
                    "" if rng.random() < 0.05 else f"{revenue:.2f}"
                ),
            }
        )
    return rows


def event_date(rng: random.Random) -> str:
    return random_date(rng, date(2017, 1, 1), date(2025, 12, 31)).isoformat()


def event_counts(rng: random.Random, companies: list[dict[str, str]]) -> list[dict[str, str]]:
    patents: list[dict[str, str]] = []
    trademarks: list[dict[str, str]] = []
    software: list[dict[str, str]] = []
    platforms: list[dict[str, str]] = []
    programs: list[dict[str, str]] = []
    financings: list[dict[str, str]] = []
    talent: list[dict[str, str]] = []

    for index, company in enumerate(companies):
        company_id = company["company_id"]
        if index in {6, 17, 29, 38}:
            continue

        propensity = rng.uniform(0.25, 1.0)
        for _ in range(
            min(35, max(0, int(rng.expovariate(1 / 10) * propensity)))
        ):
            event = date.fromisoformat(event_date(rng))
            patent_type = rng.choices(
                ["invention", "utility_model", "design"],
                weights=[0.50, 0.38, 0.12],
            )[0]
            if event > AS_OF:
                status = "pending"
            elif rng.random() < 0.68:
                status = "active"
            elif rng.random() < 0.55:
                status = "pending"
            else:
                status = "expired"
            patents.append(
                {
                    "company_id": company_id,
                    "event_date": event.isoformat(),
                    "patent_type": patent_type,
                    "status": status,
                }
            )

        for _ in range(max(0, int(rng.expovariate(1 / 6) * propensity))):
            event = date.fromisoformat(event_date(rng))
            trademarks.append(
                {
                    "company_id": company_id,
                    "event_date": event.isoformat(),
                    "status": "active" if rng.random() < 0.72 else "expired",
                }
            )

        for _ in range(max(0, int(rng.expovariate(1 / 5) * propensity))):
            software.append(
                {
                    "company_id": company_id,
                    "event_date": event_date(rng),
                }
            )

        for _ in range(max(0, int(rng.expovariate(1 / 2.2) * propensity))):
            platforms.append(
                {
                    "company_id": company_id,
                    "event_date": event_date(rng),
                    "platform_type": rng.choice(
                        [
                            "technology_center",
                            "industrial_design_center",
                            "research_center",
                        ]
                    ),
                    "level": rng.choices(
                        ["national", "provincial", "municipal"],
                        weights=[0.20, 0.48, 0.32],
                    )[0],
                }
            )

        for _ in range(max(0, int(rng.expovariate(1 / 2.8) * propensity))):
            award = round(rng.uniform(0.1, 18), 2)
            programs.append(
                {
                    "company_id": company_id,
                    "event_date": event_date(rng),
                    "program_type": rng.choice(
                        [
                            "innovation_grant",
                            "digital_transformation",
                            "equipment_upgrade",
                        ]
                    ),
                    "level": rng.choices(
                        ["national", "provincial", "municipal", "district"],
                        weights=[0.12, 0.38, 0.35, 0.15],
                    )[0],
                    "award_amount_million_cny": (
                        "" if rng.random() < 0.05 else f"{award:.2f}"
                    ),
                }
            )

        for _ in range(max(0, int(rng.expovariate(1 / 1.8) * propensity))):
            amount = round(rng.uniform(1, 320), 2)
            financings.append(
                {
                    "company_id": company_id,
                    "event_date": event_date(rng),
                    "round_type": rng.choices(
                        [
                            "seed",
                            "series_a",
                            "series_b",
                            "series_c_or_later",
                            "strategic",
                        ],
                        weights=[0.24, 0.32, 0.20, 0.08, 0.16],
                    )[0],
                    "amount_million_cny": (
                        "" if rng.random() < 0.05 else f"{amount:.2f}"
                    ),
                    "investor_id": f"INV-{rng.randrange(1, 18):02d}",
                }
            )

        for _ in range(max(0, int(rng.expovariate(1 / 2.0) * propensity))):
            talent.append(
                {
                    "company_id": company_id,
                    "event_date": event_date(rng),
                    "talent_type": rng.choice(
                        ["innovation_leader", "technical_expert", "postdoctoral"]
                    ),
                    "level": rng.choices(
                        ["national", "provincial", "municipal"],
                        weights=[0.14, 0.36, 0.50],
                    )[0],
                }
            )

    return [
        ("patents", patents),
        ("trademarks", trademarks),
        ("software_copyrights", software),
        ("platforms", platforms),
        ("programs", programs),
        ("financings", financings),
        ("talent", talent),
    ]


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        raise RuntimeError(f"generator produced no rows for {path.name}")
    fieldnames = list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    rng = random.Random(SEED)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    companies = company_rows(rng)
    write_csv(OUTPUT_DIR / "companies.csv", companies)
    for name, rows in event_counts(rng, companies):
        write_csv(OUTPUT_DIR / f"{name}.csv", rows)

    train_ids = [row["company_id"] for row in companies[:30]]
    (OUTPUT_DIR / "train_company_ids.txt").write_text(
        "\n".join(train_ids) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
