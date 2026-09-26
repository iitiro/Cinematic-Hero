#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont


# SETTINGS
BASE_DIR = Path(__file__).resolve().parent
SOURCE_FILE = Path("/boxoffice_world_1977_2025.xlsx")
FIG_DIR = BASE_DIR / "figures"
TABLE_DIR = BASE_DIR / "tables"

COLORS = {
    "blue": "#1F4E79",
    "light_blue": "#6BAED6",
    "orange": "#D97706",
    "green": "#2E7D5B",
    "red": "#A63D40",
    "purple": "#6B4C9A",
    "gray": "#6B7280",
    "light_gray": "#D9E2F3",
}

WIDTH = 1800
HEIGHT = 1050
FONT_REGULAR = "/System/Library/Fonts/Supplemental/Arial.ttf"
FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"

PERIODS = [
    (1977, 1989, "1977–1989"),
    (1990, 2000, "1990–2000"),
    (2001, 2008, "2001–2008"),
    (2009, 2015, "2009–2015"),
    (2016, 2019, "2016–2019"),
    (2020, 2021, "2020–2021"),
    (2022, 2025, "2022–2025"),
]


# Dictionary-based coding of serial narrative worlds in the top twenty.
# This provides a reproducible lower-bound estimate of seriality rather than an exhaustive franchise register.
SERIES_RULES = {
    "Comic-book superhero": [
        r"superman", r"batman", r"spider[- ]man", r"avengers", r"iron man",
        r"captain america", r"thor", r"guardians of the galaxy", r"black panther",
        r"wonder woman", r"aquaman", r"deadpool", r"x-men", r"wolverine",
        r"venom", r"ant-man", r"doctor strange", r"fantastic four", r"justice league",
        r"suicide squad", r"shang-chi", r"eternals", r"black widow", r"joker",
        r"hancock", r"incredibles", r"teenage mutant ninja turtles", r"blade\b",
        r"hellboy", r"green lantern", r"daredevil", r"catwoman", r"watchmen",
        r"thunderbolts", r"birds of prey", r"megamind",
    ],
    "Fantasy saga": [
        r"star wars", r"harry potter", r"lord of the rings", r"hobbit", r"avatar",
        r"jurassic", r"matrix", r"twilight", r"hunger games", r"chronicles of narnia",
        r"pirates of the caribbean", r"dune", r"planet of the apes", r"terminator",
        r"back to the future", r"star trek", r"alien\b", r"predator", r"godzilla",
        r"\bkong\b", r"fantastic beasts", r"independence day", r"men in black",
        r"maze runner", r"divergent", r"ne zha", r"demon slayer", r"wicked",
        r"warcraft", r"the mummy", r"clash of the titans", r"tron", r"transformers",
        r"the wandering earth", r"jumanji", r"ghostbusters", r"the meg\b|meg 2",
    ],
    "Action and service hero": [
        r"mission: impossible", r"fast & furious", r"fast and furious", r"furious [0-9]",
        r"\bf9:", r"john wick", r"die hard", r"rocky", r"rambo", r"bourne",
        r"indiana jones", r"top gun", r"bad boys", r"karate kid", r"police academy",
        r"lethal weapon", r"rush hour", r"ocean's", r"expendables", r"national treasure",
        r"taken [0-9]?", r"jack reacher", r"charlie's angels", r"xxx:", r"creed",
        r"the equalizer", r"detective chinatown", r"red cliff", r"wolf warrior",
        r"operation red sea", r"the battle at lake changjin", r"water gate bridge",
        r"the eight hundred", r"my people, my (country|homeland)", r"the expendables",
        # James Bond films whose titles do not include the protagonist's name.
        r"the spy who loved me", r"moonraker", r"for your eyes only", r"octopussy",
        r"a view to a kill", r"the living daylights", r"licence to kill", r"goldeneye",
        r"tomorrow never dies", r"the world is not enough", r"die another day",
        r"casino royale", r"quantum of solace", r"skyfall", r"spectre", r"no time to die",
    ],
    "Animated and family hero": [
        r"toy story", r"shrek", r"ice age", r"despicable me", r"minions",
        r"finding nemo", r"finding dory", r"\bcars\b", r"kung fu panda", r"madagascar",
        r"how to train your dragon", r"frozen", r"the lion king", r"\baladdin\b",
        r"moana", r"inside out", r"zootopia", r"super mario", r"sonic the hedgehog",
        r"pok[eé]mon", r"puss in boots", r"hotel transylvania", r"secret life of pets",
        r"croods", r"\bsing [0-9]?", r"monsters, inc", r"monsters university",
        r"\bcoco\b", r"ratatouille", r"\btangled\b", r"\bencanto\b", r"\belemental\b",
        r"lilo & stitch", r"minecraft movie", r"chicken run", r"boss baby", r"smurfs",
        r"dragon [0-9]", r"the first slam dunk", r"the bad guys", r"the grinch",
        r"the little mermaid", r"mufasa", r"the lego movie", r"peter rabbit",
    ],
    "Other serial narrative world": [
        r"home alone", r"hangover", r"fifty shades", r"mamma mia", r"meet the parents",
        r"little fockers", r"bridget jones", r"night at the museum", r"sherlock holmes",
        r"the conjuring", r"a quiet place", r"it: chapter", r"scream [0-9]?", r"saw [ivx0-9]?",
        r"scary movie", r"final destination", r"hotel transylvania", r"legally blonde",
        r"american pie", r"sister act", r"beverly hills cop", r"crocodile dundee",
        r"look who's talking", r"father of the bride", r"ace ventura", r"addams family",
        r"beetlejuice", r"the karate kid", r"planet of the apes", r"the godfather part",
    ],
}


def period_label(year: int) -> str:
    for start, end, label in PERIODS:
        if start <= year <= end:
            return label
    raise ValueError(year)


def classify_series(title: str) -> str:
    lowered = title.lower()
    for category, patterns in SERIES_RULES.items():
        if any(re.search(pattern, lowered) for pattern in patterns):
            return category
    return "Outside the serial-world dictionary"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REGULAR, size)


def hex_color(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def text_center(draw: ImageDraw.ImageDraw, xy: tuple[float, float], text: str, fnt: ImageFont.FreeTypeFont, fill=(0, 0, 0)) -> None:
    box = draw.textbbox((0, 0), text, font=fnt)
    draw.text((xy[0] - (box[2] - box[0]) / 2, xy[1] - (box[3] - box[1]) / 2), text, font=fnt, fill=fill)


def chart_area(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], y_ticks: list[float], y_labels: list[str], x_years: list[int] | None = None) -> None:
    left, top, right, bottom = box
    draw.line((left, top, left, bottom), fill=(55, 65, 81), width=2)
    draw.line((left, bottom, right, bottom), fill=(55, 65, 81), width=2)
    for value, label in zip(y_ticks, y_labels):
        y = bottom - value * (bottom - top)
        draw.line((left, y, right, y), fill=(220, 225, 232), width=2)
        draw.text((left - 20, y), label, font=font(25), fill=(70, 70, 70), anchor="rm")
    if x_years:
        first, last = min(x_years), max(x_years)
        ticks = list(range(((first + 4) // 5) * 5, last + 1, 5))
        if first not in ticks:
            ticks.insert(0, first)
        if last not in ticks:
            ticks.append(last)
        for year in ticks:
            x = left + (year - first) / (last - first) * (right - left)
            draw.line((x, bottom, x, bottom + 9), fill=(55, 65, 81), width=2)
            draw.text((x, bottom + 18), str(year), font=font(24), fill=(70, 70, 70), anchor="ma")


def line_points(years: np.ndarray, values: np.ndarray, box: tuple[int, int, int, int], ymin: float, ymax: float) -> list[tuple[float, float]]:
    left, top, right, bottom = box
    first, last = float(years.min()), float(years.max())
    pts = []
    for year, value in zip(years, values):
        x = left + (float(year) - first) / (last - first) * (right - left)
        y = bottom - (float(value) - ymin) / (ymax - ymin) * (bottom - top)
        pts.append((x, y))
    return pts


def save_image(img: Image.Image, filename: str) -> None:
    img.save(FIG_DIR / filename, dpi=(220, 220))


def compute_metrics(movies: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    ordered = movies.sort_values(["Year", "Rank"]).copy()
    annual_rows = []
    for year, group in ordered.groupby("Year", sort=True):
        gross = group["Worldwide"].sum()
        shares = group["Worldwide"] / gross
        foreign_known = group["Foreign"].notna()
        annual_rows.append({
            "Year": year,
            "Number of records": len(group),
            "Total worldwide box-office revenue": gross,
            "Share of the highest-grossing film": group.nsmallest(1, "Rank")["Worldwide"].sum() / gross,
            "Share of the top ten": group.nsmallest(10, "Rank")["Worldwide"].sum() / gross,
            "Share of the top twenty": group.nsmallest(20, "Rank")["Worldwide"].sum() / gross,
            "Herfindahl index": float((shares ** 2).sum()),
            "Effective number of equally sized films": float(1 / (shares ** 2).sum()),
            "Share of records with international revenue": float(foreign_known.mean()),
            "Share of international box-office revenue": float(group["Foreign"].fillna(0).sum() / gross),
            "Share of revenue with known international revenue": float(group.loc[foreign_known, "Worldwide"].sum() / gross),
        })
    annual = pd.DataFrame(annual_rows)
    base_gross = annual.loc[annual["Year"] == 2019, "Total worldwide box-office revenue"].iloc[0]
    annual["Total revenue index, 2019 = 100"] = annual["Total worldwide box-office revenue"] / base_gross * 100

    top20 = ordered[ordered["Rank"] <= 20].copy()
    top20["Serial-world category"] = top20["Release Group"].map(classify_series)
    top20["Period"] = top20["Year"].map(period_label)
    top20["Serial narrative world"] = top20["Serial-world category"] != "Outside the serial-world dictionary"

    series_annual = []
    for year, group in top20.groupby("Year", sort=True):
        total = group["Worldwide"].sum()
        series_annual.append({
            "Year": year,
            "Serial-world share of top-twenty revenue": group.loc[group["Serial narrative world"], "Worldwide"].sum() / total,
            "Share of serial titles in the top twenty": group["Serial narrative world"].mean(),
        })
    annual = annual.merge(pd.DataFrame(series_annual), on="Year", how="left")
    annual["Five-year mean seriality"] = annual["Serial-world share of top-twenty revenue"].rolling(5, center=True, min_periods=1).mean()

    period_rows = []
    for start, end, label in PERIODS:
        a = annual[annual["Year"].between(start, end)]
        t = top20[top20["Year"].between(start, end)]
        foreign_years = a[a["Year"] >= 2000]
        total_top20 = t["Worldwide"].sum()
        row = {
            "Period": label,
            "Number of years": len(a),
            "Mean share of the highest-grossing film": a["Share of the highest-grossing film"].mean(),
            "Mean share of the top ten": a["Share of the top ten"].mean(),
            "Mean share of the top twenty": a["Share of the top twenty"].mean(),
            "Mean share of international revenue": foreign_years["Share of international box-office revenue"].mean() if len(foreign_years) >= 2 else np.nan,
            "Serial-world share of top-twenty revenue": t.loc[t["Serial narrative world"], "Worldwide"].sum() / total_top20,
        }
        for category in list(SERIES_RULES) + ["Outside the serial-world dictionary"]:
            row[category] = t.loc[t["Serial-world category"] == category, "Worldwide"].sum() / total_top20
        period_rows.append(row)
    periods = pd.DataFrame(period_rows)
    return annual, periods, top20


def make_figures(annual: pd.DataFrame, periods: pd.DataFrame) -> None:
    # Figure 1. Two aligned panels.
    img = Image.new("RGB", (WIDTH, 1500), "white")
    draw = ImageDraw.Draw(img)
    text_center(draw, (WIDTH / 2, 55), "Dataset coverage and changes in total box-office revenue", font(42, True))
    boxes = [(190, 150, 1710, 690), (190, 860, 1710, 1400)]
    years = annual["Year"].to_numpy()
    chart_area(draw, boxes[0], [0, .25, .5, .75, 1], ["0", "50", "100", "150", "200"], years.tolist())
    pts = line_points(years, annual["Number of records"].to_numpy(), boxes[0], 0, 200)
    draw.line(pts, fill=hex_color(COLORS["blue"]), width=7, joint="curve")
    text_center(draw, (WIDTH / 2, 112), "Completeness of the annual ranking", font(31, True))
    draw.text((32, 410), "Number of\nrecords", font=font(28), fill=(55, 55, 55), anchor="lm", spacing=6)
    maximum = max(120, annual["Total revenue index, 2019 = 100"].max() * 1.05)
    tick_values = np.linspace(0, maximum, 5)
    chart_area(draw, boxes[1], list(np.linspace(0, 1, 5)), [f"{v:.0f}" for v in tick_values], years.tolist())
    pts = line_points(years, annual["Total revenue index, 2019 = 100"].to_numpy(), boxes[1], 0, maximum)
    draw.line(pts, fill=hex_color(COLORS["orange"]), width=7, joint="curve")
    text_center(draw, (WIDTH / 2, 815), "Nominal worldwide box-office revenue relative to 2019", font(31, True))
    draw.text((32, 1110), "Index", font=font(28), fill=(55, 55, 55), anchor="lm")
    save_image(img, "01_dataset_coverage_and_revenue.png")

    # Figure 2. Concentration.
    img = Image.new("RGB", (WIDTH, HEIGHT), "white")
    draw = ImageDraw.Draw(img)
    text_center(draw, (WIDTH / 2, 55), "Share of leading entries in annual worldwide box-office revenue", font(40, True))
    box = (190, 170, 1710, 890)
    chart_area(draw, box, [0, .2, .4, .6, .8, 1], ["0 %", "20 %", "40 %", "60 %", "80 %", "100 %"], years.tolist())
    series = [
        ("Highest-grossing film", "Share of the highest-grossing film", COLORS["orange"]),
        ("Top ten", "Share of the top ten", COLORS["blue"]),
        ("Top twenty", "Share of the top twenty", COLORS["green"]),
    ]
    for i, (label, column, color) in enumerate(series):
        pts = line_points(years, annual[column].to_numpy(), box, 0, 1)
        draw.line(pts, fill=hex_color(color), width=6, joint="curve")
        lx = 310 + i * 440
        draw.line((lx, 115, lx + 62, 115), fill=hex_color(color), width=7)
        draw.text((lx + 78, 115), label, font=font(27), fill=(35, 35, 35), anchor="lm")
    save_image(img, "02_box_office_concentration.png")

    # Figure 3. International revenue during the period with stable coverage.
    stable = annual[annual["Year"] >= 2000]
    sy = stable["Year"].to_numpy()
    img = Image.new("RGB", (WIDTH, HEIGHT), "white")
    draw = ImageDraw.Draw(img)
    text_center(draw, (WIDTH / 2, 55), "International share of worldwide box-office revenue, 2000–2025", font(39, True))
    box = (190, 170, 1710, 890)
    chart_area(draw, box, [0, .2, .4, .6, .8, 1], ["40 %", "50 %", "60 %", "70 %", "80 %", "90 %"], sy.tolist())
    pts = line_points(sy, stable["Share of international box-office revenue"].to_numpy(), box, .4, .9)
    draw.line(pts, fill=hex_color(COLORS["purple"]), width=7, joint="curve")
    for x, y in pts:
        draw.ellipse((x - 6, y - 6, x + 6, y + 6), fill=hex_color(COLORS["purple"]))
    save_image(img, "03_international_revenue_share.png")

    # Figure 4. Seriality.
    img = Image.new("RGB", (WIDTH, HEIGHT), "white")
    draw = ImageDraw.Draw(img)
    text_center(draw, (WIDTH / 2, 55), "Serial narrative worlds in top-twenty box-office revenue", font(40, True))
    box = (190, 170, 1710, 890)
    chart_area(draw, box, [0, .2, .4, .6, .8, 1], ["0 %", "20 %", "40 %", "60 %", "80 %", "100 %"], years.tolist())
    pts1 = line_points(years, annual["Serial-world share of top-twenty revenue"].to_numpy(), box, 0, 1)
    pts2 = line_points(years, annual["Five-year mean seriality"].to_numpy(), box, 0, 1)
    draw.line(pts1, fill=hex_color(COLORS["light_blue"]), width=4, joint="curve")
    draw.line(pts2, fill=hex_color(COLORS["blue"]), width=8, joint="curve")
    draw.line((510, 115, 570, 115), fill=hex_color(COLORS["light_blue"]), width=5)
    draw.text((585, 115), "Annual value", font=font(27), fill=(35, 35, 35), anchor="lm")
    draw.line((990, 115, 1050, 115), fill=hex_color(COLORS["blue"]), width=8)
    draw.text((1065, 115), "Five-year mean", font=font(27), fill=(35, 35, 35), anchor="lm")
    save_image(img, "04_serial_narrative_worlds.png")

    categories = [
        "Comic-book superhero",
        "Fantasy saga",
        "Action and service hero",
        "Animated and family hero",
        "Other serial narrative world",
        "Outside the serial-world dictionary",
    ]
    palette = [COLORS["red"], COLORS["purple"], COLORS["orange"], COLORS["green"], COLORS["gray"], "#D9D9D9"]
    img = Image.new("RGB", (2000, 1220), "white")
    draw = ImageDraw.Draw(img)
    text_center(draw, (1000, 55), "Composition of top-twenty revenue by type of serial narrative world", font(40, True))
    box = (170, 180, 1430, 1010)
    chart_area(draw, box, [0, .2, .4, .6, .8, 1], ["0 %", "20 %", "40 %", "60 %", "80 %", "100 %"])
    n = len(periods)
    gap = 35
    bar_width = (box[2] - box[0] - gap * (n + 1)) / n
    for i, row in periods.iterrows():
        x0 = box[0] + gap + i * (bar_width + gap)
        bottom_value = 0.0
        for category, color in zip(categories, palette):
            value = float(row[category])
            y1 = box[3] - bottom_value * (box[3] - box[1])
            y0 = box[3] - (bottom_value + value) * (box[3] - box[1])
            draw.rectangle((x0, y0, x0 + bar_width, y1), fill=hex_color(color))
            bottom_value += value
        draw.text((x0 + bar_width / 2, box[3] + 24), row["Period"], font=font(23), fill=(55, 55, 55), anchor="ma")
    legend_x, legend_y = 1500, 220
    for i, (category, color) in enumerate(zip(categories, palette)):
        y = legend_y + i * 92
        draw.rectangle((legend_x, y, legend_x + 42, y + 42), fill=hex_color(color))
        draw.multiline_text((legend_x + 62, y - 2), category, font=font(25), fill=(35, 35, 35), spacing=4)
    save_image(img, "05_serial_world_composition.png")


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    movies = pd.read_excel(SOURCE_FILE, sheet_name="All Movies")
    annual, periods, top20 = compute_metrics(movies)
    annual.to_csv(TABLE_DIR / "richni_pokaznyky.csv", index=False, encoding="utf-8-sig")
    periods.to_csv(TABLE_DIR / "pokaznyky_za_periodamy.csv", index=False, encoding="utf-8-sig")
    top20.to_csv(TABLE_DIR / "koduvannia_providnoi_dvadtsiatky.csv", index=False, encoding="utf-8-sig")
    make_figures(annual, periods)
    print("Created figures:")
    for path in sorted(FIG_DIR.glob("*.png")):
        print(path)
    print("\nPeriod indicators:")
    print(periods.to_string(index=False))


if __name__ == "__main__":
    main()
