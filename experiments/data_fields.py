"""Extract real field polygons from harvester GNSS trajectories.

Source: Field-road trajectory dataset (github.com/wefwrffa/Field-road-trajectory-dataset),
derived from China's agricultural machinery operation big data system
(Wu et al., Comput. Electron. Agric. 205:107594, 2023).

For each trajectory, field-labelled points are projected to a local ENU frame,
clustered with DBSCAN into individual fields, and each field is represented by
its convex hull plus the dominant operating direction (mode of the recorded
headings, folded to [0, 180)). Output: experiments/data/fields.json
"""
import glob
import json
import os

import numpy as np
import pandas as pd
from shapely.geometry import MultiPoint
from sklearn.cluster import DBSCAN

ROOT = os.path.dirname(os.path.abspath(__file__))
SOURCES = {
    "paddy": ("/home/user/wefwrffa/field-road-trajectory-dataset/paddy_*/*.xlsx", 20.0),
    "wheat": ("/home/user/data/wheat/*/*.xlsx", 12.0),
}
R_EARTH = 6371000.0


def enu(lon, lat, lon0, lat0):
    x = np.radians(lon - lon0) * R_EARTH * np.cos(np.radians(lat0))
    y = np.radians(lat - lat0) * R_EARTH
    return x, y


def dominant_direction(headings_deg):
    """Mode of axial (mod-180) heading, in degrees clockwise from north."""
    h = np.mod(headings_deg, 180.0)
    hist, edges = np.histogram(h, bins=36, range=(0, 180))
    k = np.argmax(hist)
    sel = (h >= edges[k]) & (h < edges[k + 1])
    return float(np.median(h[sel])), float(hist[k] / max(len(h), 1))


def extract(kind):
    pat, eps = SOURCES[kind]
    fields = []
    for f in sorted(glob.glob(pat)):
        d = pd.read_excel(f)
        labcol = "标签" if "标签" in d.columns else "标记"
        lon = pd.to_numeric(d["经度"], errors="coerce").to_numpy(float)
        lat = pd.to_numeric(d["纬度"], errors="coerce").to_numpy(float)
        hd = pd.to_numeric(d["方向"], errors="coerce").to_numpy(float)
        lab = pd.to_numeric(d[labcol], errors="coerce").fillna(0).to_numpy(int)
        m = (lab == 1) & np.isfinite(lon) & np.isfinite(lat)
        if m.sum() < 30:
            continue
        lon0, lat0 = np.median(lon[m]), np.median(lat[m])
        x, y = enu(lon[m], lat[m], lon0, lat0)
        cl = DBSCAN(eps=eps, min_samples=15).fit_predict(np.c_[x, y])
        for c in set(cl) - {-1}:
            s = cl == c
            hull = MultiPoint(list(zip(x[s], y[s]))).convex_hull
            if hull.geom_type != "Polygon":
                continue
            area = hull.area
            if not (2000.0 <= area <= 200000.0):  # 0.2 ha .. 20 ha
                continue
            direc, conc = dominant_direction(hd[m][s])
            if conc < 0.08:  # no clear operating direction
                continue
            cx, cy = hull.centroid.x, hull.centroid.y
            clon = lon0 + np.degrees(cx / (R_EARTH * np.cos(np.radians(lat0))))
            clat = lat0 + np.degrees(cy / R_EARTH)
            poly = [(px - cx, py - cy) for px, py in hull.exterior.coords]
            fields.append(dict(kind=kind, source=os.path.basename(f), lon=clon, lat=clat,
                               area_m2=area, heading_deg=direc, n_points=int(s.sum()),
                               polygon_enu=poly))
    return fields


def main():
    out = []
    for kind in SOURCES:
        fs = extract(kind)
        print(kind, len(fs), "fields; area ha median",
              np.round(np.median([f["area_m2"] for f in fs]) / 1e4, 2))
        out += fs
    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
    with open(os.path.join(ROOT, "data", "fields.json"), "w") as fh:
        json.dump(out, fh)


if __name__ == "__main__":
    main()
