#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter, PercentFormatter


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_INPUT = SCRIPT_DIR.parents[1] / "boxoffice_ukraine_2005_2025.xlsx"
DEFAULT_OUTPUT = SCRIPT_DIR / "generated_ukraine_en"

COLORS = {
    "ink": "#1F2937",
    "blue": "#2F5597",
    "light_blue": "#7EA6D8",
    "gold": "#C69214",
    "red": "#A33B3B",
    "green": "#3C7A57",
    "gray": "#7B8491",
    "light_gray": "#D9DEE7",
}

ARCHETYPE_COLORS = {
    "Superhero and comics": "#2F5597",
    "Science-fiction and posthuman hero": "#2C7F9E",
    "Fantasy hero and quest": "#7A5195",
    "Animated and family hero": "#4C9F70",
    "Action hero, spy, and criminal protagonist": "#D07A27",
    "Historical, military, and biographical hero": "#A33B3B",
    "Horror and survival hero": "#5A5A5A",
    "Comic and romantic hero": "#D95F9D",
    "Other and unclassified": "#B8C0CC",
}


# Rules are applied in order. They are title-level proxies, not a substitute
# for coding plots, protagonists, or audience reception.
ARCHETYPE_RULES: list[tuple[str, list[str]]] = [
    (
        "Superhero and comics",
        [
            r"avengers", r"spider[- ]?man", r"iron man", r"thor", r"captain america",
            r"captain marvel", r"guardians of the galaxy", r"black panther", r"doctor strange",
            r"ant[- ]?man", r"deadpool", r"x-men", r"wolverine", r"fantastic four",
            r"batman", r"dark knight", r"superman", r"justice league", r"wonder woman",
            r"aquaman", r"shazam", r"black adam", r"suicide squad", r"joker", r"venom",
            r"morbius", r"the flash", r"blue beetle", r"teenage mutant ninja turtles",
            r"black widow", r"shang-chi", r"eternals", r"logan(?:\s|$)", r"ghost rider",
            r"hancock", r"constantine", r"kick-ass", r"watchmen",
        ],
    ),
    (
        "Science-fiction and posthuman hero",
        [
            r"avatar", r"star wars", r"matrix", r"tron", r"interstellar", r"the martian",
            r"gravity(?:\s|$)", r"inception", r"prometheus", r"alien", r"elysium",
            r"after earth", r"real steel", r"battleship", r"alita", r"blade runner",
            r"arrival(?:\s|$)", r"edge of tomorrow", r"oblivion", r"ready player one",
            r"terminator", r"jurassic", r"godzilla", r"pacific rim", r"free guy",
            r"the creator", r"transformers", r"m3gan", r"dune",
        ],
    ),
    (
        "Animated and family hero",
        [
            r"shrek", r"madagascar", r"ice age", r"toy story", r"cars(?:\s|$|\d)",
            r"despicable me", r"minions", r"frozen", r"lion king", r"kung fu panda",
            r"puss in boots", r"how to train your dragon", r"hotel transylvania", r"sing(?:\s|$|\d)",
            r"secret life of pets", r"zootopia", r"moana", r"inside out", r"coco(?:\s|$)",
            r"finding dory", r"finding nemo", r"incredibles", r"boss baby", r"smurfs",
            r"rio(?:\s|$|\d)", r"trolls", r"croods", r"migration", r"elemental",
            r"super mario", r"sonic", r"garfield", r"mufasa", r"wish(?:\s|$)",
            r"ralph", r"monsters university", r"brave(?:\s|$)", r"lorax", r"tangled",
            r"megamind", r"rango", r"up(?:\s|$)", r"wall[- ]?e", r"bolt(?:\s|$)",
            r"bee movie", r"ratatouille", r"happy feet", r"open season", r"over the hedge",
            r"angry birds", r"wild robot", r"bad guys", r"mavka", r"soul(?:\s|$)",
            r"tom & jerry", r"raya and the last dragon", r"spies in disguise", r"grinch",
            r"addams family", r"stolen princess", r"paddington", r"three heroes",
            r"rise of the guardians", r"mulan(?:\s|$)", r"jungle book",
        ],
    ),
    (
        "Fantasy hero and quest",
        [
            r"harry potter", r"fantastic beasts", r"hobbit", r"lord of the rings",
            r"pirates of the caribbean", r"alice in wonderland", r"maleficent", r"oz the great",
            r"narnia", r"warcraft", r"hunger games", r"twilight", r"john carter",
            r"life of pi", r"prince of persia", r"clash of the titans", r"wrath of the titans",
            r"snow white", r"dracula", r"noah(?:\s|$)", r"exodus", r"mortal kombat",
            r"maze runner", r"divergent", r"ready player one", r"jumanji", r"wonka",
            r"little mermaid", r"beauty and the beast", r"aladdin", r"cinderella",
            r"mummy", r"witch", r"seventh son", r"hercules", r"gods of egypt",
            r"miss peregrine", r"dungeons & dragons", r"wicked", r"demon slayer",
            r"assassin's creed", r"valerian", r"national treasure", r"da vinci code",
            r"angels & demons", r"forbidden empire", r"last airbender", r"immortals",
        ],
    ),
    (
        "Historical, military, and biographical hero",
        [
            r"oppenheimer", r"stalingrad", r"admiral(?:\s|$)", r"vysotsky", r"napoleon",
            r"dunkirk", r"1917", r"hacksaw ridge", r"fury(?:\s|$)", r"darkest hour",
            r"bohemian rhapsody", r"elvis", r"rocketman", r"ford v ferrari", r"the imitation game",
            r"lincoln", r"the king's speech", r"the social network", r"american sniper",
            r"the revenant", r"first man", r"green book", r"once upon a time in hollywood",
            r"taras bulba", r"300(?:\s|:|$)", r"10,000 bc", r"great gatsby",
            r"killers of the flower moon", r"house of gucci",
        ],
    ),
    (
        "Horror and survival hero",
        [
            r"conjuring", r"annabelle", r"insidious", r"paranormal activity", r"the ring",
            r"ring two", r"it chapter", r"^it(?:\s|:|$)", r"saw(?:\s|$|\d)", r"scream",
            r"a quiet place", r"resident evil", r"final destination", r"purge", r"nun(?:\s|$)",
            r"exorc", r"sinister", r"smile(?:\s|$|\d)", r"alien", r"predator", r"zomb",
            r"world war z", r"i am legend", r"28 years later", r"five nights at freddy",
            r"nosferatu", r"black phone", r"invisible man", r"fantasy island",
        ],
    ),
    (
        "Action hero, spy, and criminal protagonist",
        [
            r"fast & furious", r"fast and furious", r"furious 7", r"fate of the furious", r"^f9:", r"^fast x$",
            r"hobbs & shaw", r"mission: impossible", r"mission impossible", r"john wick",
            r"james bond", r"casino royale", r"quantum of solace", r"skyfall", r"spectre",
            r"no time to die", r"bourne", r"taken", r"transport(er)?", r"expendables",
            r"die hard", r"terminator", r"transformers", r"pacific rim", r"godzilla",
            r"king kong", r"kong:", r"jurassic", r"indiana jones", r"uncharted",
            r"top gun", r"equalizer", r"gentlemen", r"ocean's", r"sherlock holmes",
            r"men in black", r"bad boys", r"be cool", r"sahara", r"shadowboxing",
            r"wrath of man", r"hitman's wife", r"king's man", r"fall guy", r"ballerina",
            r"nobody 2", r"black bag", r"wanted(?:\s|$)", r"death race", r"taxi 4",
        ],
    ),
    (
        "Comic and romantic hero",
        [
            r"love", r"valentine", r"wedding", r"bridget jones", r"sex and the city",
            r"hangover", r"american pie", r"meet the", r"hitch(?:\s|$)", r"congeniality",
            r"what men", r"crazy rich asians", r"ticket to paradise", r"proposal(?:\s|$)",
        ],
    ),
]


PERIODS = [
    (2006, 2009, "2006–2009\nmarket formation"),
    (2010, 2013, "2010–2013\nmarket expansion"),
    (2014, 2016, "2014–2016\ncrisis and restructuring"),
    (2017, 2019, "2017–2019\npre-pandemic peak"),
    (2020, 2021, "2020–2021\npandemic"),
    (2022, 2025, "2022–2025\nfull-scale war"),
]


def configure_plotting() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10.5,
            "axes.titlesize": 13,
            "axes.titleweight": "bold",
            "axes.labelsize": 10.5,
            "axes.edgecolor": "#8A94A3",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.color": "#E4E8EF",
            "grid.linewidth": 0.8,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
        }
    )


def classify_title(title: str) -> str:
    normalized = str(title).casefold().replace("’", "'")
    for label, patterns in ARCHETYPE_RULES:
        if any(re.search(pattern, normalized) for pattern in patterns):
            return label
    return "Other and unclassified"


def period_label(year: int) -> str:
    for start, end, label in PERIODS:
        if start <= year <= end:
            return label.replace("\n", " ")
    return "2005 incomplete coverage"


def load_and_validate(path: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    movies = pd.read_excel(path, sheet_name="All Movies")
    years = pd.read_excel(path, sheet_name="Years")

    required_movie = {"Year", "Rank", "Release", "Gross", "Theaters", "Distributor", "Release URL"}
    required_year = {"Year", "Movies", "Calendar_Gross"}
    missing_movie = required_movie - set(movies.columns)
    missing_year = required_year - set(years.columns)
    if missing_movie or missing_year:
        raise ValueError(f"Missing required columns: movies={sorted(missing_movie)}, years={sorted(missing_year)}")

    movies["Year"] = pd.to_numeric(movies["Year"], errors="raise").astype(int)
    movies["Rank"] = pd.to_numeric(movies["Rank"], errors="raise").astype(int)
    movies["Gross"] = pd.to_numeric(movies["Gross"], errors="raise")
    movies["Theaters"] = pd.to_numeric(movies["Theaters"], errors="coerce")
    years["Year"] = pd.to_numeric(years["Year"], errors="raise").astype(int)
    years["Movies"] = pd.to_numeric(years["Movies"], errors="raise")
    years["Calendar_Gross"] = pd.to_numeric(years["Calendar_Gross"], errors="raise")

    recomputed = movies.groupby("Year", as_index=False)["Gross"].sum().rename(columns={"Gross": "Recomputed_Gross"})
    validation = years.merge(recomputed, on="Year", how="outer")
    validation["Gross_Difference"] = validation["Calendar_Gross"] - validation["Recomputed_Gross"]

    quality = {
        "rows": int(len(movies)),
        "years": [int(movies["Year"].min()), int(movies["Year"].max())],
        "missing_genre": int(movies["Genre"].isna().sum()) if "Genre" in movies else None,
        "missing_distributor": int(movies["Distributor"].isna().sum()),
        "missing_theaters": int(movies["Theaters"].isna().sum()),
        "duplicate_year_title_rows": int(movies.duplicated(["Year", "Release"]).sum()),
        "yearly_gross_reconciliation_max_abs_difference": float(validation["Gross_Difference"].abs().max()),
    }
    return movies, years.sort_values("Year"), quality


def build_metrics(movies: pd.DataFrame, years: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    yearly = years.copy()
    top_shares = []
    for year, group in movies.groupby("Year"):
        group = group.sort_values("Gross", ascending=False)
        total = group["Gross"].sum()
        row = {
            "Year": year,
            "Top1_Share": group.head(1)["Gross"].sum() / total,
            "Top5_Share": group.head(5)["Gross"].sum() / total,
            "Top10_Share": group.head(10)["Gross"].sum() / total,
            "Median_Gross": group["Gross"].median(),
            "Median_Theaters": group["Theaters"].median(),
            "Gross_per_Theater_Median": (group["Gross"] / group["Theaters"]).replace([np.inf, -np.inf], np.nan).median(),
        }
        top_shares.append(row)
    yearly = yearly.merge(pd.DataFrame(top_shares), on="Year", how="left")
    yearly["Gross_Index_2019"] = yearly["Calendar_Gross"] / yearly.loc[yearly["Year"].eq(2019), "Calendar_Gross"].iloc[0] * 100
    yearly["Movies_Index_2019"] = yearly["Movies"] / yearly.loc[yearly["Year"].eq(2019), "Movies"].iloc[0] * 100
    yearly["YoY_Gross"] = yearly["Calendar_Gross"].pct_change()
    yearly["Period"] = yearly["Year"].map(period_label)

    period = (
        yearly[yearly["Year"].ge(2006)]
        .groupby("Period", sort=False)
        .agg(
            Years=("Year", "count"),
            Mean_Annual_Gross=("Calendar_Gross", "mean"),
            Mean_Annual_Movies=("Movies", "mean"),
            Mean_Top10_Share=("Top10_Share", "mean"),
            Median_Gross=("Median_Gross", "median"),
            Median_Theaters=("Median_Theaters", "median"),
        )
        .reset_index()
    )

    top = movies.sort_values("Gross", ascending=False).head(30).copy()
    top["Archetype"] = top["Release"].map(classify_title)
    return yearly, period, top


def build_archetype_tables(movies: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    sample = movies[movies["Rank"].le(20)].copy()
    sample["Archetype"] = sample["Release"].map(classify_title)
    sample["Period"] = sample["Year"].map(period_label)

    year_arch = sample.pivot_table(index="Year", columns="Archetype", values="Gross", aggfunc="sum", fill_value=0)
    year_arch = year_arch.div(year_arch.sum(axis=1), axis=0)
    for col in ARCHETYPE_COLORS:
        if col not in year_arch:
            year_arch[col] = 0.0
    year_arch = year_arch[list(ARCHETYPE_COLORS)]

    period_arch = sample[sample["Year"].ge(2006)].pivot_table(
        index="Period", columns="Archetype", values="Gross", aggfunc="sum", fill_value=0
    )
    period_arch = period_arch.div(period_arch.sum(axis=1), axis=0)
    for col in ARCHETYPE_COLORS:
        if col not in period_arch:
            period_arch[col] = 0.0
    ordered_periods = [label.replace("\n", " ") for _, _, label in PERIODS]
    period_arch = period_arch.reindex(ordered_periods)[list(ARCHETYPE_COLORS)]
    return sample, year_arch, period_arch


def save_figure(fig: plt.Figure, output: Path, stem: str) -> None:
    fig.tight_layout()
    fig.savefig(output / f"{stem}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_market_dynamics(yearly: pd.DataFrame, output: Path) -> None:
    fig, ax1 = plt.subplots(figsize=(10.6, 5.8))
    x = yearly["Year"]
    ax1.plot(x, yearly["Calendar_Gross"] / 1e6, color=COLORS["blue"], marker="o", lw=2.3, label="Box-office revenue")
    ax1.fill_between(x, yearly["Calendar_Gross"] / 1e6, color=COLORS["light_blue"], alpha=0.18)
    ax1.set_ylabel("Box-office revenue (USD millions)")
    ax1.set_xlabel("Year")
    ax1.set_xticks(x)
    ax1.tick_params(axis="x", rotation=45)
    ax2 = ax1.twinx()
    ax2.plot(x, yearly["Movies"], color=COLORS["gold"], marker="s", lw=1.8, label="Number of releases")
    ax2.set_ylabel("Number of releases")
    ax2.grid(False)
    lines = ax1.get_lines() + ax2.get_lines()
    ax1.legend(lines, [line.get_label() for line in lines], loc="upper left", frameon=False, ncol=2)
    ax1.set_title("Ukrainian box-office dynamics in the 2005–2025 dataset")
    ax1.text(0.0, -0.22, "Note: 2005 contains only 10 records; coverage may be incomplete for 2022–2025. Values are nominal and are not adjusted for inflation.", transform=ax1.transAxes, fontsize=8.7, color=COLORS["gray"])
    save_figure(fig, output, "fig_01_market_dynamics")


def plot_market_index(yearly: pd.DataFrame, output: Path) -> None:
    df = yearly[yearly["Year"].ge(2006)]
    fig, ax = plt.subplots(figsize=(10.6, 5.4))
    ax.plot(df["Year"], df["Gross_Index_2019"], label="Box-office revenue", color=COLORS["blue"], lw=2.3, marker="o")
    ax.plot(df["Year"], df["Movies_Index_2019"], label="Number of releases", color=COLORS["gold"], lw=2.0, marker="s")
    ax.axhline(100, color=COLORS["gray"], lw=1, ls="--")
    ax.set_ylabel("Index, 2019 = 100")
    ax.set_xlabel("Year")
    ax.set_xticks(df["Year"])
    ax.tick_params(axis="x", rotation=45)
    ax.legend(frameon=False, ncol=2)
    ax.set_title("Market scale relative to the 2019 pre-pandemic peak")
    save_figure(fig, output, "fig_02_market_index_2019")


def plot_concentration(yearly: pd.DataFrame, output: Path) -> None:
    fig, ax = plt.subplots(figsize=(10.6, 5.4))
    df = yearly[yearly["Year"].ge(2006)]
    ax.plot(df["Year"], df["Top1_Share"], label="Top 1", color=COLORS["red"], marker="o", lw=1.8)
    ax.plot(df["Year"], df["Top5_Share"], label="Top 5", color=COLORS["gold"], marker="s", lw=1.8)
    ax.plot(df["Year"], df["Top10_Share"], label="Top 10", color=COLORS["blue"], marker="^", lw=2.2)
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax.set_ylim(0, max(0.9, df["Top10_Share"].max() * 1.08))
    ax.set_xticks(df["Year"])
    ax.tick_params(axis="x", rotation=45)
    ax.set_xlabel("Year")
    ax.set_ylabel("Share of annual box-office revenue")
    ax.legend(frameon=False, ncol=3)
    ax.set_title("Concentration of audience attention among the highest-grossing releases")
    save_figure(fig, output, "fig_03_concentration")


def plot_top_films(top: pd.DataFrame, output: Path) -> None:
    df = top.head(15).sort_values("Gross")
    labels = [f"{title} ({year})" for title, year in zip(df["Release"], df["Year"])]
    colors = [ARCHETYPE_COLORS[a] for a in df["Archetype"]]
    fig, ax = plt.subplots(figsize=(10.6, 7.1))
    ax.barh(labels, df["Gross"] / 1e6, color=colors)
    ax.set_xlabel("Box-office revenue in the relevant calendar year (USD millions)")
    ax.set_title("Highest-grossing entries in the dataset")
    ax.grid(axis="y", visible=False)
    for y, value in enumerate(df["Gross"] / 1e6):
        ax.text(value + 0.05, y, f"{value:.2f}", va="center", fontsize=8.5)
    save_figure(fig, output, "fig_04_top_films")


def plot_archetype_periods(period_arch: pd.DataFrame, output: Path) -> None:
    fig, ax = plt.subplots(figsize=(11.2, 6.5))
    x = np.arange(len(period_arch))
    bottom = np.zeros(len(period_arch))
    short_labels = [p.replace(" ", "\n", 1) for p in period_arch.index]
    for category in period_arch.columns:
        values = period_arch[category].to_numpy()
        ax.bar(x, values, bottom=bottom, label=category, color=ARCHETYPE_COLORS[category], width=0.72)
        bottom += values
    ax.set_xticks(x, short_labels)
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax.set_ylim(0, 1)
    ax.set_ylabel("Share of top-twenty revenue in the period")
    ax.set_title("Changes in narrative macrotypes within the most popular repertoire")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.18), frameon=False, ncol=2, fontsize=8.7)
    save_figure(fig, output, "fig_05_archetype_periods")


def plot_archetype_years(year_arch: pd.DataFrame, output: Path) -> None:
    df = year_arch[year_arch.index >= 2006]
    fig, ax = plt.subplots(figsize=(10.9, 6.1))
    ax.stackplot(
        df.index,
        *[df[c].to_numpy() for c in df.columns],
        labels=df.columns,
        colors=[ARCHETYPE_COLORS[c] for c in df.columns],
        alpha=0.95,
    )
    ax.set_xlim(df.index.min(), df.index.max())
    ax.set_ylim(0, 1)
    ax.set_xticks(df.index)
    ax.tick_params(axis="x", rotation=45)
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax.set_xlabel("Year")
    ax.set_ylabel("Share of top-twenty revenue")
    ax.set_title("Annual composition of narrative macrotypes in the top twenty")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.20), frameon=False, ncol=2, fontsize=8.5)
    save_figure(fig, output, "fig_06_archetype_years")


def plot_distributors(movies: pd.DataFrame, output: Path) -> pd.DataFrame:
    dist = (
        movies.dropna(subset=["Distributor"])
        .groupby("Distributor", as_index=False)
        .agg(Releases=("Release", "size"), Gross=("Gross", "sum"))
        .sort_values("Gross", ascending=False)
    )
    total_known = dist["Gross"].sum()
    dist["Known_Distributor_Gross_Share"] = dist["Gross"] / total_known
    df = dist.head(10).sort_values("Gross")
    fig, ax = plt.subplots(figsize=(10.6, 6.2))
    ax.barh(df["Distributor"], df["Gross"] / 1e6, color=COLORS["blue"])
    ax.set_xlabel("Total box-office revenue (USD millions)")
    ax.set_title("Leading distributors by box-office revenue in the dataset")
    ax.grid(axis="y", visible=False)
    save_figure(fig, output, "fig_07_distributors")
    return dist


def plot_release_scale(yearly: pd.DataFrame, output: Path) -> None:
    df = yearly[yearly["Year"].ge(2006)]
    fig, ax1 = plt.subplots(figsize=(10.6, 5.4))
    ax1.plot(df["Year"], df["Median_Theaters"], color=COLORS["blue"], marker="o", lw=2.2, label="Median number of theatres")
    ax1.set_ylabel("Theatres, median")
    ax1.set_xlabel("Year")
    ax1.set_xticks(df["Year"])
    ax1.tick_params(axis="x", rotation=45)
    ax2 = ax1.twinx()
    ax2.plot(df["Year"], df["Gross_per_Theater_Median"], color=COLORS["gold"], marker="s", lw=1.8, label="Median revenue per theatre")
    ax2.set_ylabel("Revenue per theatre (USD)")
    ax2.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:,.0f}"))
    ax2.grid(False)
    lines = ax1.get_lines() + ax2.get_lines()
    ax1.legend(lines, [line.get_label() for line in lines], frameon=False, ncol=2, loc="upper left")
    ax1.set_title("Scale of theatrical distribution and indicative revenue intensity")
    save_figure(fig, output, "fig_08_release_scale")


def plot_crisis_comparison(yearly: pd.DataFrame, output: Path) -> None:
    selected = yearly[yearly["Year"].isin([2013, 2015, 2019, 2020, 2022, 2024, 2025])].copy()
    fig, ax = plt.subplots(figsize=(10.6, 5.4))
    bars = ax.bar(selected["Year"].astype(str), selected["Calendar_Gross"] / 1e6, color=[COLORS["blue"] if y in (2013, 2019) else COLORS["red"] for y in selected["Year"]])
    ax.set_ylabel("Box-office revenue (USD millions)")
    ax.set_xlabel("Year")
    ax.set_title("Contrast between peak and crisis years")
    ax.grid(axis="x", visible=False)
    for bar, movies in zip(bars, selected["Movies"]):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1.2, f"{int(movies)} releases", ha="center", fontsize=8.5)
    save_figure(fig, output, "fig_09_crisis_comparison")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Source XLSX file")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Directory for figures and tables")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    configure_plotting()
    movies, years, quality = load_and_validate(args.input)
    yearly, period, top = build_metrics(movies, years)
    sample, year_arch, period_arch = build_archetype_tables(movies)

    plot_market_dynamics(yearly, args.output)
    plot_market_index(yearly, args.output)
    plot_concentration(yearly, args.output)
    plot_top_films(top, args.output)
    plot_archetype_periods(period_arch, args.output)
    plot_archetype_years(year_arch, args.output)
    distributors = plot_distributors(movies, args.output)
    plot_release_scale(yearly, args.output)
    plot_crisis_comparison(yearly, args.output)

    yearly.to_csv(args.output / "table_yearly_metrics.csv", index=False, encoding="utf-8-sig")
    period.to_csv(args.output / "table_period_metrics.csv", index=False, encoding="utf-8-sig")
    top.to_csv(args.output / "table_top_30_films.csv", index=False, encoding="utf-8-sig")
    sample.to_csv(args.output / "table_top20_title_coding.csv", index=False, encoding="utf-8-sig")
    year_arch.to_csv(args.output / "table_archetype_shares_by_year.csv", encoding="utf-8-sig")
    period_arch.to_csv(args.output / "table_archetype_shares_by_period.csv", encoding="utf-8-sig")
    distributors.to_csv(args.output / "table_distributors.csv", index=False, encoding="utf-8-sig")
    (args.output / "data_quality.json").write_text(json.dumps(quality, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({"input": str(args.input), "output": str(args.output), "quality": quality}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
