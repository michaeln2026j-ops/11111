"""Attach real terrain (Copernicus GLO-30 DEM, AWS open data) to each field.

For every field in data/fields.json we read a DEM window covering the field
(+60 m margin) directly from the public COG on S3 and store it on a local ENU
grid (metres, origin = field centroid). Output: data/dem/<id>.npz
Usage: python3 experiments/data_dem.py [--max-per-kind 250]
"""
import argparse
import json
import math
import os
from collections import defaultdict

import numpy as np
import rasterio
from rasterio.windows import from_bounds

ROOT = os.path.dirname(os.path.abspath(__file__))
URL = "https://copernicus-dem-30m.s3.amazonaws.com/{n}/{n}.tif"
R_EARTH = 6371000.0
os.environ.setdefault("CURL_CA_BUNDLE", "/root/.ccr/ca-bundle.crt")
if "HTTPS_PROXY" in os.environ:
    os.environ.setdefault("GDAL_HTTP_PROXY", os.environ["HTTPS_PROXY"])


def tile_name(lat, lon):
    ns, ew = ("N" if lat >= 0 else "S"), ("E" if lon >= 0 else "W")
    return f"Copernicus_DSM_COG_10_{ns}{abs(lat):02d}_00_{ew}{abs(lon):03d}_00_DEM"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-per-kind", type=int, default=250)
    args = ap.parse_args()
    fields = json.load(open(os.path.join(ROOT, "data", "fields.json")))
    rng = np.random.default_rng(0)
    keep = []
    for kind in ("paddy", "wheat"):
        idx = [i for i, f in enumerate(fields) if f["kind"] == kind]
        rng.shuffle(idx)
        keep += sorted(idx[: args.max_per_kind])
    by_tile = defaultdict(list)
    for i in keep:
        f = fields[i]
        by_tile[(math.floor(f["lat"]), math.floor(f["lon"]))].append(i)
    out_dir = os.path.join(ROOT, "data", "dem")
    os.makedirs(out_dir, exist_ok=True)
    done = 0
    for (la, lo), ids in sorted(by_tile.items()):
        n = tile_name(la, lo)
        try:
            ds = rasterio.open(URL.format(n=n))
        except Exception as exc:  # tile over sea / missing
            print("skip tile", n, exc)
            continue
        with ds:
            for i in ids:
                f = fields[i]
                poly = np.array(f["polygon_enu"])
                r = np.abs(poly).max() + 60.0
                dlat = math.degrees(r / R_EARTH)
                dlon = math.degrees(r / (R_EARTH * math.cos(math.radians(f["lat"]))))
                w = from_bounds(f["lon"] - dlon, f["lat"] - dlat, f["lon"] + dlon, f["lat"] + dlat, ds.transform)
                z = ds.read(1, window=w, boundless=True, fill_value=np.nan).astype(np.float32)
                t = ds.window_transform(w)
                ny, nx = z.shape
                lons = t.c + (np.arange(nx) + 0.5) * t.a
                lats = t.f + (np.arange(ny) + 0.5) * t.e
                xs = np.radians(lons - f["lon"]) * R_EARTH * math.cos(math.radians(f["lat"]))
                ys = np.radians(lats - f["lat"]) * R_EARTH
                np.savez_compressed(os.path.join(out_dir, f"{i}.npz"), z=z, xs=xs, ys=ys)
                done += 1
        print(f"tile {n}: {len(ids)} fields (total {done})", flush=True)


if __name__ == "__main__":
    main()
