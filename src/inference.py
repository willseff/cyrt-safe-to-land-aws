"""
Inference module for weather landing predictions.

Usage:
    from inference import predict_from_grib2

    grib2_bytes: bytes = ...   # raw GRIB2 data from retrieve_data
    probability: float = predict_from_grib2(grib2_bytes)
"""

import tempfile
from pathlib import Path
from typing import Optional

import numpy as np
import torch
import xarray as xr
from torch import nn


# ---------------------------------------------------------------------------
# Model definition
# ---------------------------------------------------------------------------
class WeatherLanding2DNet(nn.Module):
    def __init__(self, in_ch: int, base: int = 16):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(in_ch, base, 3, padding=1),
            nn.ReLU(),
            nn.Conv2d(base, base, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(base, base * 2, 3, padding=1),
            nn.ReLU(),
            nn.Conv2d(base * 2, base * 2, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
        )
        self.head = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Linear(base * 2, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """x: (B, C, H, W) -> logits: (B,)"""
        z = self.features(x)
        return self.head(z).squeeze(1)


# ---------------------------------------------------------------------------
# Cached model loading (lazy singleton)
# ---------------------------------------------------------------------------
_bundle: Optional[dict] = None
_model: Optional[WeatherLanding2DNet] = None


def _load_bundle() -> dict:
    """Load and cache the model bundle. Safe to call multiple times."""
    global _bundle
    if _bundle is None:
        bundle_path = Path(__file__).parent / "weather_landing_bundle.pth"
        _bundle = torch.load(str(bundle_path), weights_only=False)
    return _bundle


def get_model() -> WeatherLanding2DNet:
    """Return a cached, eval-mode model loaded from the bundle."""
    global _model
    if _model is None:
        bundle = _load_bundle()
        _model = WeatherLanding2DNet(in_ch=bundle["in_ch"], base=bundle["base"])
        _model.load_state_dict(bundle["state_dict"])
        _model.eval()
    return _model


# ---------------------------------------------------------------------------
# Normalization helpers
# ---------------------------------------------------------------------------
def _extract_and_normalize(local_path: str) -> np.ndarray:
    """
    Open a GRIB2 file, extract the four variables over the region of
    interest, normalize with the bundle's mu/sd, and return a (1, 4, H, W)
    numpy array ready for inference.
    """
    bundle = _load_bundle()

    # t2m (heightAboveGround, level=2)
    ds_t2m = xr.open_dataset(
        local_path,
        engine="cfgrib",
        filter_by_keys={"typeOfLevel": "heightAboveGround", "level": 2},
        backend_kwargs={"indexpath": ""},
    )
    # u10, v10, msl
    ds_other = xr.open_dataset(
        local_path,
        engine="cfgrib",
        backend_kwargs={"indexpath": ""},
        drop_variables=["t2m"],
    )

    # Spatial subset
    region = dict(latitude=slice(66, 59), longitude=slice(-101, -82))
    ds_t2m = ds_t2m.sel(**region)
    ds_other = ds_other.sel(**region)

    # Stack into (1, 4, H, W) channels-last -> channels-first
    t2m = ds_t2m["t2m"].values
    u10 = ds_other["u10"].values
    v10 = ds_other["v10"].values
    msl = ds_other["msl"].values
    X = np.stack([t2m, u10, v10, msl], axis=1)[np.newaxis, ...]   # (1, 4, H, W)
    X = np.transpose(X, (0, 2, 1, 3))                              # (1, H, C, W) -> now correct

    # Normalize
    mu = bundle["mu"]
    sd = bundle["sd"]
    Xn = (X - mu) / sd
    return Xn


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def predict_from_grib2(grib2_data: bytes) -> float:
    """
    Run inference on raw GRIB2 forecast data and return the landing
    probability (0.0 – 1.0).

    Args:
        grib2_data: Raw GRIB2 bytes (e.g. from ``retrieve_latest_forecast()``).

    Returns:
        Landing probability as a float.
    """
    model = get_model()

    with tempfile.TemporaryDirectory() as tdir:
        tmp_path = Path(tdir) / "forecast.grib2"
        tmp_path.write_bytes(grib2_data)

        Xn = _extract_and_normalize(str(tmp_path))
        Xn_tensor = torch.tensor(Xn, dtype=torch.float32)

        with torch.no_grad():
            logits = model(Xn_tensor)
            prob = torch.sigmoid(logits).item()

    return prob
