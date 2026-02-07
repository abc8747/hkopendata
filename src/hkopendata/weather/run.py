from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from itertools import chain
from logging import getLogger
from pathlib import Path
from typing import Any, Generator, TypedDict

import httpx
import orjson
import polars as pl
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

import numpy as np

from .ocf import fetch_ocf
from .station import grid, stations

logger = getLogger(__name__)


async def ocf_download(path_base: Path) -> None:
    run_id = int(time.time())
    path_run = path_base / str(run_id)
    hourly_dir = path_run / "hourly"
    hourly_dir.mkdir(parents=True, exist_ok=True)
    # daily_dir = path_run / "daily"
    # daily_dir.mkdir(parents=True, exist_ok=True)

    async with httpx.AsyncClient() as client:
        stations_all = []
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=None,
        ) as progress:
            task = progress.add_task("processing station", total=None)

            for station in chain(grid(), stations()):
                progress.update(task, description=f"fetching station {station.id}")
                ocf = await fetch_ocf(client, station.id)

                pl.DataFrame(ocf["HourlyWeatherForecast"]).write_parquet(
                    hourly_dir / f"{station.id}.parquet"
                )
                # pl.DataFrame(ocf["DailyForecast"]).write_parquet(
                #     daily_dir / f"{station.id}.parquet"
                # )

                stations_all.append(
                    {
                        **asdict(station),
                        "lat": ocf["Latitude"],
                        "lng": ocf["Longitude"],
                        "last_modified": ocf["LastModified"],
                        "model_time": ocf["ModelTime"],
                    }
                )

        fp_out = path_run / "stations.json"
        with open(fp_out, "wb") as f:
            f.write(orjson.dumps(stations_all, option=orjson.OPT_INDENT_2))
        logger.info(f"wrote {len(stations_all)} stations to {fp_out}")


class Station(TypedDict):
    id: str
    backup: str | None
    urban: bool
    aws: bool
    grid: bool
    lat: float
    lng: float
    last_modified: int
    model_time: int


@dataclass
class Run:
    fp: Path

    def load_stations(self) -> list[Station]:
        with open(self.fp / "stations.json") as f:
            return orjson.loads(f.read())  # type: ignore


def ocf_runs(
    path_base: Path, *, sort_reverse: bool | None = True
) -> Generator[Run, None, None]:
    """:param sort_reverse: True for newest first, False for oldest first,
    None for no sorting"""
    if sort_reverse is None:
        paths = path_base.iterdir()
    else:
        paths = (p for p in sorted(path_base.iterdir(), reverse=sort_reverse))
    for run in paths:
        if run.is_dir() and run.name.isdigit():
            yield Run(fp=run)


def ocf_plot_hourly_wind(path_base: Path) -> None:
    import matplotlib.pyplot as plt

    plt.style.use("dark_background")

    HKO = (114.174637, 22.302219)
    DISTANCE_MAX = 1.2
    DISTANCE_MAX_STATION = 0.4
    try:
        base_dir = next(ocf_runs(path_base, sort_reverse=True))
    except StopIteration:
        return

    hourly_dir = base_dir.fp / "hourly"

    for station in base_dir.load_stations():
        time, wind_speed = (
            pl.scan_parquet(hourly_dir / f"{station['id']}.parquet")
            .select("ForecastHour", "ForecastWindSpeed")
            .collect()
        )
        distance = (
            (HKO[0] - station["lng"]) ** 2 + (HKO[1] - station["lat"]) ** 2
        ) ** 0.5
        if not station["grid"] and station["aws"]:
            plt.plot(
                time,
                wind_speed,
                label=station["id"],
                lw=(DISTANCE_MAX_STATION - distance) / DISTANCE_MAX_STATION * 3,
            )
            continue
        if station["grid"]:
            plt.plot(
                time,
                wind_speed,
                color="white",
                alpha=(DISTANCE_MAX - distance) / DISTANCE_MAX * 0.1,
            )

    plt.legend()
    plt.xticks(rotation=45)
    plt.show()
    plt.close()


def ocf_plot_grid_wind(path_base: Path) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.widgets import Slider
    from mpl_toolkits.basemap import Basemap

    plt.style.use("dark_background")
    try:
        base_dir = next(ocf_runs(path_base, sort_reverse=True))
    except StopIteration:
        return
    hourly_dir = base_dir.fp / "hourly"
    if not (sts := [s for s in base_dir.load_stations() if s["grid"]]):
        return
    df0 = pl.read_parquet(
        hourly_dir / f"{sts[0]['id']}.parquet", columns=["ForecastHour"]
    )
    hours = df0["ForecastHour"].to_list()
    if (T := len(hours)) == 0:
        return
    data = np.full((T, 15, 16), np.nan, dtype=float)
    for s in sts:
        idx = int(s["id"][1:]) - 1
        r, c = divmod(idx, 16)
        df = pl.read_parquet(
            hourly_dir / f"{s['id']}.parquet", columns=["ForecastWindSpeed"]
        ).with_columns(pl.col("ForecastWindSpeed").cast(pl.Float64))
        ws = df["ForecastWindSpeed"].to_numpy()
        n = min(T, ws.shape[0])
        if n:
            data[:n, r, c] = ws[:n]
    vmin = float(np.nanmin(data))
    vmax = float(np.nanmax(data))
    fig, ax = plt.subplots()
    lons = sorted({float(s["lng"]) for s in sts})
    lats = sorted({float(s["lat"]) for s in sts})
    dlon = (lons[1] - lons[0]) if len(lons) > 1 else 0.1
    dlat = (lats[1] - lats[0]) if len(lats) > 1 else 0.1
    xmin, xmax = lons[0] - dlon / 2, lons[-1] + dlon / 2
    ymin, ymax = lats[0] - dlat / 2, lats[-1] + dlat / 2
    im = ax.imshow(
        data[0],
        cmap="turbo",
        vmin=vmin,
        vmax=vmax,
        extent=(xmin, xmax, ymin, ymax),
        origin="upper",
    )
    m = Basemap(
        projection="cyl",
        llcrnrlon=xmin,
        urcrnrlon=xmax,
        llcrnrlat=ymin,
        urcrnrlat=ymax,
        resolution="h",
        ax=ax,
    )
    m.drawcoastlines(color="white", linewidth=0.5)
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    plt.colorbar(im, ax=ax)
    ax_slider = plt.axes((0.2, 0.02, 0.6, 0.03))
    slider = Slider(ax_slider, "t", 0, T - 1, valinit=0, valstep=1)
    slider.valtext.set_text(str(hours[0]))

    def update(val: Any) -> None:
        i = int(slider.val)
        im.set_data(data[i])
        slider.valtext.set_text(str(hours[i]))
        fig.canvas.draw_idle()

    slider.on_changed(update)
    plt.show()
    plt.close()
