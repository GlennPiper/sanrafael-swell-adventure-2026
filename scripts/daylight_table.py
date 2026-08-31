"""Print the sunrise/sunset table for the trip dates and area.

Paste the output into ``trip_config.DAYLIGHT``. Kept as a separate script rather
than computed at build time so the shipped values are reviewable in the diff and
the build stays deterministic without a solar library.

Uses the NOAA solar position algorithm. Accurate to about a minute, which is
well inside the margin that matters for "can we finish this hike in daylight".

Usage:
    python scripts/daylight_table.py
"""
from __future__ import annotations
import datetime
import math
import pathlib
import sys

_SCRIPTS = pathlib.Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import trip_config as cfg  # noqa: E402

# Route mid-latitude and Pacific Daylight Time.
LAT = 46.3
LON = -121.6
TZ_OFFSET_HOURS = -7
TZ_LABEL = 'PDT'


def sun_times(lat: float, lon: float, date: datetime.date,
              tz_offset: float) -> tuple[str, str, int]:
    n = date.timetuple().tm_yday
    lat_r = math.radians(lat)
    g = 2 * math.pi / 365 * (n - 1)
    eqt = 229.18 * (0.000075 + 0.001868 * math.cos(g) - 0.032077 * math.sin(g)
                    - 0.014615 * math.cos(2 * g) - 0.040849 * math.sin(2 * g))
    decl = (0.006918 - 0.399912 * math.cos(g) + 0.070257 * math.sin(g)
            - 0.006758 * math.cos(2 * g) + 0.000907 * math.sin(2 * g)
            - 0.002697 * math.cos(3 * g) + 0.00148 * math.sin(3 * g))
    # 90.833 deg accounts for atmospheric refraction and the solar disc radius.
    cos_ha = (math.cos(math.radians(90.833)) / (math.cos(lat_r) * math.cos(decl))
              - math.tan(lat_r) * math.tan(decl))
    ha = math.degrees(math.acos(max(-1.0, min(1.0, cos_ha))))
    rise = 720 - 4 * (lon + ha) - eqt + tz_offset * 60
    set_ = 720 - 4 * (lon - ha) - eqt + tz_offset * 60

    def fmt(mins: float) -> str:
        h, m = int(mins // 60) % 24, int(round(mins % 60))
        if m == 60:
            h, m = (h + 1) % 24, 0
        return f'{h:02d}:{m:02d}'

    return fmt(rise), fmt(set_), int(round(set_ - rise))


def main() -> None:
    start = datetime.date.fromisoformat(cfg.TRIP_DATE_START)
    end = datetime.date.fromisoformat(cfg.TRIP_DATE_END)
    print(f'Daylight at {LAT}N, {abs(LON)}W in {TZ_LABEL}\n')
    print('DAYLIGHT = [')
    d = start
    while d <= end:
        rise, set_, dur = sun_times(LAT, LON, d, TZ_OFFSET_HOURS)
        print(f"    {{'date_iso': '{d.isoformat()}', 'sunrise': '{rise}', "
              f"'sunset': '{set_}', 'hours': '{dur // 60}h{dur % 60:02d}m'}},")
        d += datetime.timedelta(days=1)
    print(']')


if __name__ == '__main__':
    main()
