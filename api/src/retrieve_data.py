import logging
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from ecmwf.opendata import Client


def snap_to_valid_step(run_hour: int, lead_h: int) -> int:
    """
    Snap a lead hour to the nearest valid forecast step for the given run hour.

    HRES rules:
      - 00/12 UTC: 0-144 by 3h, then 150-240 by 6h
      - 06/18 UTC: 0-90 by 3h
    """
    if run_hour in (0, 12):
        valid = list(range(0, 145, 3)) + list(range(150, 241, 6))
    else:
        valid = list(range(0, 91, 3))
    return max([s for s in valid if s <= lead_h] or [0])


def retrieve_latest_forecast() -> bytes:
    """
    Download the latest ECMWF HRES 0.25° forecast (2t, msl, 10u, 10v) for the
    current valid step, and return the raw GRIB2 data as bytes.

    Returns:
        bytes: Raw GRIB2 forecast data.

    Raises:
        RuntimeError: If the latest run cannot be determined or the download fails.
    """
    client = Client(source="ecmwf", model="ifs", resol="0p25")

    # Determine latest run and current valid step
    run_dt = client.latest(type="fc")
    if run_dt.tzinfo is None:
        run_dt = run_dt.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    lead = max(0, round((now - run_dt).total_seconds() / 3600))
    step = snap_to_valid_step(run_dt.hour, lead)
    logging.info("Latest run %s, lead=%d, chosen step=%d", run_dt, lead, step)

    # Download to a temp file and read into memory
    with tempfile.TemporaryDirectory() as tdir:
        tmp = Path(tdir) / "latest_now.grib2"
        client.retrieve(
            date=run_dt.date(),
            time=run_dt.hour,
            type="fc",
            step=step,
            param=["2t", "msl", "10u", "10v"],
            target=str(tmp),
        )
        logging.info("Downloaded forecast %s step %d -> %s", run_dt, step, tmp)
        data = tmp.read_bytes()

    logging.info("Retrieved %d bytes of forecast data", len(data))
    return data
