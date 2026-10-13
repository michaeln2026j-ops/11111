"""Real multi-station, multi-day GNSS positioning-error series from NOAA CORS (RTKLIB demo5).

Replaces the single 27-min vehicle RTK series (data_rtk.py) with a diverse set of REAL error series:
12 CORS station pairs (5-30 km baselines, mostly US Midwest/Plains agricultural regions plus CA/WA/MT)
x 8 days spread over the four seasons of 2024 and 2025, each processed in four receiver grades:

  rtk_fix   : dual-freq (L1+L2) GPS+GLONASS carrier-phase kinematic RTK, ambiguity resolution 'continuous'
              (no fix-and-hold, GLONASS AR off because base/rover receivers are often of different brands),
              ionosphere-weighted (pos1-ionoopt=est-stec: DD slant iono estimated with baseline-scaled
              constraints, RTKLIB default stats), every epoch output with its quality flag (Q=1 fix, 2 float).
              Without iono estimation ('brdc') RTKLIB fixes more often on the 20-30 km baselines but the
              fixed solutions carry the solar-maximum ionospheric scale bias (-0.7..-2.4 ppm along the
              baseline in tests, i.e. 2-6 cm), so the iono-weighted model is used, as in commercial RTK.
  rtk_float : same, ambiguity resolution off (float-only carrier-phase solution)
  dgps      : code-differential GNSS (RTKLIB pos1-posmode=dgps, L1+L2 codes)
  spp       : single point positioning of the rover alone (L1 C/A, broadcast Klobuchar iono, Saastamoinen)

Base = station A at its known coordinates, rover = station B processed *kinematically* (pos1-dynamics=off, so
every epoch's position is estimated independently; only the ambiguities are carried over), broadcast
ephemeris, 15 deg elevation mask, forward (real-time-like) filter, cold start at 00:00 GPST of each day.

Truth: IGS20/ITRF2020 ARP coordinates + velocities from NGS coord/coord_20/<ssss>_20.coord.txt, propagated
from epoch 2020.0 to the observation day (mid-day decimal year). Antenna deltas are forced to 0 so that both
the base input and the rover output refer to the ARP; receiver-antenna PCO/PCV from RTKLIB's igs14.atx.
Errors = (solution - truth) rotated to local north/east/up at the rover (metres).

Data rate: NOAA's public S3 mirror (noaa-cors-pds) only carries 30-s daily RINEX for the CORS network; 1-s
data exist only as hourly *proprietary raw* files (e.g. Trimble .T02) for ~40 stations under raw/, which
RTKLIB cannot decode, so all series are 30 s.

Output
  data/cors_errors.npz  keys 'rtk_fix','rtk_float','dgps','spp' -> object arrays of series dicts
                        {pair, rover, base, region, baseline_km, date, doy, dt_s, t, en, ee, eu, q, ns,
                         rover_ant, base_ant, rover_rcv, base_rcv, interval_s, ant_differs_from_coord};
                        'meta' -> dict (configs, station coordinates, days, antenna PCV lookup, problems).
                        t = seconds of day (GPST; gaps where a receiver has no data), en/ee/eu = error (m),
                        q = RTKLIB Q flag (1 fix, 2 float, 4 dgps [2 fallback epochs in the RTK grades],
                        5 single), ns = #satellites used. Each day starts cold, so the first minutes of every
                        RTK series are float convergence (decimetre errors); trim them if a warm receiver is
                        wanted. Load with load() below or np.load(path, allow_pickle=True)[grade].
  data/cors_summary.csv one row per grade x pair-day: n epochs, availability, fix rate, bias, sd, rms,
                        p50/p95/max horizontal error, lag-1 autocorrelation and 1/e correlation time, over the
                        whole day; the same stats on fixed epochs only (*_fixed) and *_warm columns that skip
                        the first WARM_S = 30 min after the daily cold start (the part core.gnss_bank uses).
                        The whole-day max_h and RTK correlation times are dominated by that convergence.
                        `python data_cors.py --stats-only` rebuilds the CSV and summary from the npz.
Intermediate files (downloads, rnx2rtkp configs and .pos outputs) go to $CORS_CACHE (/home/user/data/cors).

Notable heterogeneity (real, kept on purpose): LINH-SC00 has a 706 m base-rover height difference
(tropospheric DD residuals -> 19-46 % fix rate) and NLIB-IAMN is the longest baseline (28.8 km, 11-69 % fix);
the other pairs have median daily fix rates of 90-100 % (worst days 31 % MNCA-IANA, 70 % MNEY-MNSV, summer
2025). DGPS quality depends strongly on the CORS receivers' code tracking/smoothing: BAYR-MIBY (two Leica GR50)
sd_h ~6 cm with ~30 min correlation; most pairs sd_h 25-35 cm with 0.5-1 min correlation; MNBV-ECSD,
MNEY-MNSV, NEOM-IACB add slow code-multipath components (1/e time 20-50 min).

CAVEAT: these are errors of *static* geodetic-grade CORS antennas (choke-ring/geodetic antennas, good sky
view, low multipath) processed kinematically. They capture the real temporal structure of satellite
geometry, ionosphere/troposphere residuals, ambiguity convergence and fix/float transitions, but they
UNDERESTIMATE the errors of a receiver on a moving agricultural vehicle: vehicle antennas are smaller, sit
near metal roofs/implements (multipath), suffer canopy/tree-line masking, antenna tilt/vibration and
cycle slips under dynamics, and multipath decorrelates faster in motion (shorter correlation times than the
static sites' quasi-periodic sidereal multipath). Treat rtk_fix here as a lower bound on field RTK error.

Requirements (rebuild only): RTKLIB demo5 rnx2rtkp built from https://github.com/rtklibexplorer/RTKLIB
(app/consapp/rnx2rtkp/gcc; path via $RNX2RTKP), python package `hatanaka` (Hatanaka-compressed RINEX;
falls back to the 2.5x larger .o.gz files if it is missing). Download ~0.25 GB, runtime ~5-10 min on 3 CPUs.

Data: NOAA National Geodetic Survey CORS Network (NCN), https://geodesy.noaa.gov/CORS/ (AWS Open Data
noaa-cors-pds). Software: T. Takasu, RTKLIB; demo5 fork by T. Everett (rtklibexplorer).
"""
import argparse
import concurrent.futures as cf
import datetime as _dt
import gzip
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT_NPZ = os.path.join(ROOT, "data", "cors_errors.npz")
OUT_CSV = os.path.join(ROOT, "data", "cors_summary.csv")
CACHE = os.environ.get("CORS_CACHE", "/home/user/data/cors")
RTKLIB = os.environ.get("RTKLIB_DIR", "/home/user/RTKLIB")
RNX2RTKP = os.environ.get("RNX2RTKP", os.path.join(RTKLIB, "app/consapp/rnx2rtkp/gcc/rnx2rtkp"))
ATX = os.path.join(RTKLIB, "data/ant/igs14.atx")
S3 = "https://noaa-cors-pds.s3.amazonaws.com"

# (base, rover, region). Baselines 5-29 km; chosen from the NGS ITRF2020 coordinate list (operational sites,
# computed velocities) and checked for data availability on all DAYS. Rejected candidates: KAR4-ILUC (IL;
# KAR4 RINEX antenna LEIAS11 differs from the coord_20 antenna record and fixed RTK showed a constant ~2 cm
# horizontal offset on every day, i.e. unreliable truth), P775-PRDU/INWL (IN; P775 absent from the S3
# archive, INWL-PRDU < 5 km), KS pairs (ICT*: data on <= 3 of 8 days), MC01-MC02 (CO; antennas replaced Sep 2024).
PAIRS = [
    ("ndfa", "morh", "ND/MN Red River Valley"),
    ("p539", "p602", "CA Cholame Valley"),
    ("mtei", "p051", "MT Yellowstone Valley"),
    ("ohsb", "ohmh", "OH Lake Erie plain"),
    ("linh", "sc00", "WA Kittitas Valley"),
    ("neom", "iacb", "NE/IA Missouri Valley"),
    ("bayr", "miby", "MI Saginaw Valley"),
    ("p268", "p271", "CA Sacramento Valley"),
    ("mnca", "iana", "MN/IA Driftless"),
    ("mney", "mnsv", "MN SE farmland"),
    ("mnbv", "ecsd", "SD/MN Big Sioux"),
    ("nlib", "iamn", "IA Cedar Valley"),
]
# one day per season in 2024 and 2025 (year, day-of-year); 2024-2025 is near solar maximum
DAYS = [(2024, 15), (2024, 106), (2024, 197), (2024, 289), (2025, 20), (2025, 110), (2025, 201), (2025, 294)]
GRADES = ("rtk_fix", "rtk_float", "dgps", "spp")
DT_NOM = 30.0
WARM_S = 1800.0  # *_warm stats skip the first 30 min after the daily cold start (= core.CONVERGE_S)
WGS_A, WGS_E2 = 6378137.0, 6.69437999014e-3

COMMON_OPTS = """pos1-frequency     =l1+l2
pos1-soltype       =forward
pos1-elmask        =15
pos1-dynamics      =off
pos1-tidecorr      =0
pos1-ionoopt       =brdc
pos1-tropopt       =saas
pos1-sateph        =brdc
pos1-navsys        =5
pos2-gloarmode     =off
pos2-bdsarmode     =off
pos2-arthres       =3
pos2-slipthres     =0.05
pos2-maxage        =30
out-solformat      =xyz
out-outhead        =on
out-outopt         =on
out-timesys        =gpst
out-timeform       =tow
out-timendec       =1
out-solstatic      =all
out-outstat        =off
ant1-postype       =llh
ant1-anttype       ={rover_ant}
ant1-antdele       =0
ant1-antdeln       =0
ant1-antdelu       =0
ant2-postype       =xyz
ant2-pos1          ={bx:.4f}
ant2-pos2          ={by:.4f}
ant2-pos3          ={bz:.4f}
ant2-anttype       ={base_ant}
ant2-antdele       =0
ant2-antdeln       =0
ant2-antdelu       =0
file-rcvantfile    ={atx}
"""
GRADE_OPTS = {  # appended after COMMON_OPTS (later lines override earlier ones)
    "rtk_fix": "pos1-posmode       =kinematic\npos2-armode        =continuous\npos1-ionoopt       =est-stec\n",
    "rtk_float": "pos1-posmode       =kinematic\npos2-armode        =off\npos1-ionoopt       =est-stec\n",
    "dgps": "pos1-posmode       =dgps\npos2-armode        =off\n",
    "spp": "pos1-posmode       =single\npos1-frequency     =l1\npos2-armode        =off\n",
}


# ----------------------------------------------------------------------------------------------- download
def fetch(key, dest, retries=4):
    """Download S3 object `key` to `dest` (cached). Returns dest, or None if the object does not exist."""
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return dest
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    for k in range(retries):
        try:
            with urllib.request.urlopen(f"{S3}/{key}", timeout=120) as r:
                data = r.read()
            tmp = dest + ".part"
            with open(tmp, "wb") as f:
                f.write(data)
            os.replace(tmp, dest)
            return dest
        except urllib.error.HTTPError as e:
            if e.code in (403, 404):
                return None
            err = e
        except Exception as e:  # network hiccup
            err = e
        time.sleep(2 * (k + 1))
    raise RuntimeError(f"download failed: {key}: {err}")


def have_hatanaka():
    try:
        import hatanaka  # noqa: F401
        return True
    except ImportError:
        return False


def obs_key(sta, year, doy, hatanaka_ok):
    yy = year % 100
    ext = "d" if hatanaka_ok else "o"
    return f"rinex/{year}/{doy:03d}/{sta}/{sta}{doy:03d}0.{yy:02d}{ext}.gz"


def nav_keys(year, doy):
    yy = year % 100
    return [f"rinex/{year}/{doy:03d}/brdc{doy:03d}0.{yy:02d}{c}.gz" for c in "ng"]


def local(key):
    return os.path.join(CACHE, "s3", key)


def unpack(src, dst):
    """gz (+ Hatanaka) -> plain RINEX file."""
    if src.endswith("d.gz"):
        import hatanaka
        data = hatanaka.decompress(open(src, "rb").read())
    else:
        with gzip.open(src, "rb") as f:
            data = f.read()
    with open(dst, "wb") as f:
        f.write(data)
    return dst


# ------------------------------------------------------------------------------------------- coordinates
def read_coord(sta):
    """ARP ITRF2020 position (epoch 2020.0) and velocity from the NGS coord_20 file."""
    path = fetch(f"coord/coord_20/{sta}_20.coord.txt", os.path.join(CACHE, "coord_20", f"{sta}_20.coord.txt"))
    if path is None:
        raise RuntimeError(f"no coord_20 file for {sta}")
    txt = open(path).read()
    i0 = txt.index("Antenna Reference Point")
    i1 = txt.find("L1 Phase Center", i0)
    arp = txt[i0:i1 if i1 > 0 else None]
    pos_blk = arp[arp.index("ITRF2020 POSITION"):arp.index("ITRF2020 VELOCITY")]
    vel_blk = arp[arp.index("ITRF2020 VELOCITY"):]
    if "EPOCH 2020.0" not in pos_blk:
        raise RuntimeError(f"{sta}: unexpected reference epoch")
    g = lambda blk, k: float(re.search(r"\b" + k + r"\s*=\s*(-?[\d.]+)\s*m", blk).group(1))
    xyz = np.array([g(pos_blk, c) for c in ("X", "Y", "Z")])
    vel = np.array([g(vel_blk, c) for c in ("VX", "VY", "VZ")])
    m = re.search(r"Antenna Code\s*=\s*([^)]*)\)\s*was installed on\s*(\d{2}\w{3}\d{4})", txt.replace("|\n|", " "))
    ant, inst = (re.sub(r"\s+", " ", m.group(1)).strip(), m.group(2)) if m else ("", "")
    comp = re.search(r"(Computed|Published by the IGS) in ([\w.]+ \d{4}) using data through gpswk (\d+)", pos_blk)
    return dict(xyz2020=xyz, vel=vel, coord_ant=ant, ant_installed=inst,
                computed=f"{comp.group(1)} {comp.group(2)} (gpswk {comp.group(3)})" if comp else "")


def decyear(year, doy):
    ndays = 366 if (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)) else 365
    return year + (doy - 0.5) / ndays  # mid-day


def ecef2geo(x):
    lon = np.arctan2(x[1], x[0])
    p = np.hypot(x[0], x[1])
    lat = np.arctan2(x[2], p * (1 - WGS_E2))
    for _ in range(10):
        n = WGS_A / np.sqrt(1 - WGS_E2 * np.sin(lat) ** 2)
        h = p / np.cos(lat) - n
        lat = np.arctan2(x[2], p * (1 - WGS_E2 * n / (n + h)))
    return lat, lon, h


def enu_matrix(lat, lon):
    sl, cl, sp, cp = np.sin(lon), np.cos(lon), np.sin(lat), np.cos(lat)
    return np.array([[-sl, cl, 0.0], [-sp * cl, -sp * sl, cp], [cp * cl, cp * sl, sp]])  # rows: E, N, U


# ------------------------------------------------------------------------------------------ rinex / atx
def rinex_header(path):
    hdr = {}
    with open(path, "r", errors="replace") as f:
        for line in f:
            lab = line[60:].strip()
            if lab == "ANT # / TYPE":
                hdr["ant"] = line[20:40].rstrip()
            elif lab == "REC # / TYPE / VERS":
                hdr["rcv"] = line[20:40].strip()
            elif lab == "INTERVAL":
                hdr["interval"] = float(line[:10])
            elif lab == "END OF HEADER":
                break
    return hdr


_ATX_TYPES = None


def pcv_found(ant):
    """Mimic RTKLIB searchpcv(): antenna+radome first, then antenna name alone."""
    global _ATX_TYPES
    if _ATX_TYPES is None:
        _ATX_TYPES = [l[:20] for l in open(ATX, errors="replace")
                      if l[60:].startswith("TYPE / SERIAL NO") and not l[20:40].strip()]
    tok = ant.split()
    if not tok:
        return "none"
    if any(all(t in ty for t in tok[:2]) for ty in _ATX_TYPES):
        return "exact"
    if any(ty.startswith(tok[0]) for ty in _ATX_TYPES):
        return "no-radome"
    return "none"


# -------------------------------------------------------------------------------------------- processing
def read_pos(path):
    if not os.path.exists(path):
        return None
    try:
        d = np.loadtxt(path, comments="%", ndmin=2)
    except ValueError:
        return None
    return d if d.size else None


def process_pair_day(base, rover, region, year, doy, coords, hat):
    date = _dt.date(year, 1, 1) + _dt.timedelta(doy - 1)
    tag = f"{base}-{rover}_{year}{doy:03d}"
    work = os.path.join(CACHE, "pos", f"{base}-{rover}", f"{year}{doy:03d}")
    os.makedirs(work, exist_ok=True)
    src = {s: fetch(obs_key(s, year, doy, hat), local(obs_key(s, year, doy, hat))) for s in (base, rover)}
    navs = [fetch(k, local(k)) for k in nav_keys(year, doy)]
    if any(v is None for v in src.values()) or navs[0] is None:
        return tag, None, f"missing data: {[s for s, v in src.items() if v is None]}"
    tmp = os.path.join(CACHE, "tmp", tag)
    os.makedirs(tmp, exist_ok=True)
    try:
        yy = year % 100
        obs = {s: unpack(src[s], os.path.join(tmp, f"{s}{doy:03d}0.{yy:02d}o")) for s in src}
        nav = [unpack(n, os.path.join(tmp, os.path.basename(n)[:-3])) for n in navs if n]
        hdr = {s: rinex_header(obs[s]) for s in obs}
        ty = decyear(year, doy)
        xb = coords[base]["xyz2020"] + coords[base]["vel"] * (ty - 2020.0)
        xr = coords[rover]["xyz2020"] + coords[rover]["vel"] * (ty - 2020.0)
        lat, lon, _ = ecef2geo(xr)
        R = enu_matrix(lat, lon)
        out = {}
        for g in GRADES:
            conf = os.path.join(work, f"{g}.conf")
            with open(conf, "w") as f:
                f.write(COMMON_OPTS.format(rover_ant=hdr[rover].get("ant", ""), base_ant=hdr[base].get("ant", ""),
                                           bx=xb[0], by=xb[1], bz=xb[2], atx=ATX) + GRADE_OPTS[g])
            pos = os.path.join(work, f"{g}.pos")
            files = [obs[rover]] + ([] if g == "spp" else [obs[base]]) + nav
            subprocess.run([RNX2RTKP, "-x", "0", "-k", conf, "-o", pos] + files,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False, timeout=1800)
            d = read_pos(pos)
            if d is None or len(d) < 10:
                out[g] = None
                continue
            tow = d[:, 1]
            t = tow - np.floor(tow[0] / 86400.0) * 86400.0  # seconds of the GPST day
            e = (d[:, 2:5] - xr) @ R.T  # E, N, U
            out[g] = dict(pair=f"{base.upper()}-{rover.upper()}", rover=rover.upper(), base=base.upper(),
                          region=region, baseline_km=float(np.linalg.norm(xr - xb) / 1e3),
                          date=date.isoformat(), doy=doy, dt_s=DT_NOM, t=t.astype(np.float64),
                          en=e[:, 1].astype(np.float32), ee=e[:, 0].astype(np.float32),
                          eu=e[:, 2].astype(np.float32), q=d[:, 5].astype(np.int8), ns=d[:, 6].astype(np.int8),
                          rover_ant=hdr[rover].get("ant", ""), base_ant=hdr[base].get("ant", ""),
                          rover_rcv=hdr[rover].get("rcv", ""), base_rcv=hdr[base].get("rcv", ""),
                          interval_s=hdr[rover].get("interval", np.nan),
                          ant_differs_from_coord=[st.upper() for st in (base, rover)
                                                  if " ".join(hdr[st].get("ant", "").split()) != coords[st]["coord_ant"]])
        return tag, out, ""
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ------------------------------------------------------------------------------------------------ stats
def acf_gappy(x, valid, nlag):
    """Autocorrelation of a gappy, regularly gridded series (pairs where both samples exist)."""
    n = len(x)
    m = valid.astype(float)
    x0 = np.where(valid, x - x[valid].mean(), 0.0)
    nfft = 1 << int(np.ceil(np.log2(2 * n)))
    fx, fm = np.fft.rfft(x0, nfft), np.fft.rfft(m, nfft)
    num = np.fft.irfft(fx * np.conj(fx), nfft)[:nlag]
    cnt = np.round(np.fft.irfft(fm * np.conj(fm), nfft)[:nlag])
    with np.errstate(invalid="ignore", divide="ignore"):
        cov = np.where(cnt > 20, num / np.maximum(cnt, 1), np.nan)
    return cov  # autocovariance (not normalised)


def corr_stats(s):
    """lag-1 autocorrelation and 1/e correlation time of the horizontal error vector."""
    dt = s["dt_s"]
    k = np.round((s["t"] - s["t"][0]) / dt).astype(int)
    n = k[-1] + 1
    nlag = max(2, n // 2)
    cov = 0.0
    for c in ("en", "ee"):
        x = np.zeros(n)
        v = np.zeros(n, bool)
        x[k] = s[c]
        v[k] = True
        cov = cov + acf_gappy(x, v, nlag)
    r = cov / cov[0]
    rho1 = float(r[1])
    below = np.where(r < np.exp(-1))[0]
    if len(below) == 0:
        tau = np.nan
    else:
        j = below[0]
        r0, r1 = r[j - 1], r[j]
        frac = (r0 - np.exp(-1)) / (r0 - r1) if np.isfinite(r0) and r0 != r1 else 0.0
        tau = float((j - 1 + frac) * dt)
    return rho1, tau


def series_stats(g, s):
    en, ee = s["en"].astype(float), s["ee"].astype(float)
    h = np.hypot(en, ee)
    q = s["q"]
    rho1, tau = corr_stats(s)
    row = dict(grade=g, pair=s["pair"], base=s["base"], rover=s["rover"], region=s["region"],
               baseline_km=round(s["baseline_km"], 2), date=s["date"], n_epochs=len(h),
               availability=len(h) / (86400.0 / s["dt_s"]), fix_rate=float(np.mean(q == 1)),
               mean_ns=float(np.mean(s["ns"])), bias_n=en.mean(), bias_e=ee.mean(),
               sd_n=en.std(), sd_e=ee.std(), sd_h=float(np.sqrt(en.var() + ee.var())),
               rms_h=float(np.sqrt(np.mean(h ** 2))), p50_h=float(np.median(h)), p95_h=float(np.percentile(h, 95)),
               max_h=float(h.max()), rho1=rho1, tau_e_s=tau)
    fx = q == 1
    row["p95_h_fixed"] = float(np.percentile(h[fx], 95)) if fx.sum() > 10 else np.nan
    row["sd_h_fixed"] = float(np.sqrt(en[fx].var() + ee[fx].var())) if fx.sum() > 10 else np.nan
    row["bias_h_fixed"] = float(np.hypot(en[fx].mean(), ee[fx].mean())) if fx.sum() > 10 else np.nan
    wk = s["t"] >= s["t"][0] + WARM_S  # warm receiver: skip the daily cold-start convergence
    row["n_warm"] = int(wk.sum())
    if wk.sum() > 40:
        rho1w, tauw = corr_stats(dict(dt_s=s["dt_s"], t=s["t"][wk], en=s["en"][wk], ee=s["ee"][wk]))
        hw = h[wk]
        row.update(fix_rate_warm=float(np.mean(q[wk] == 1)),
                   sd_h_warm=float(np.sqrt(en[wk].var() + ee[wk].var())), p95_h_warm=float(np.percentile(hw, 95)),
                   max_h_warm=float(hw.max()), rho1_warm=rho1w, tau_e_s_warm=tauw)
    else:
        row.update({c: np.nan for c in ("fix_rate_warm", "sd_h_warm", "p95_h_warm", "max_h_warm", "rho1_warm",
                                        "tau_e_s_warm")})
    return row


def load(path=OUT_NPZ):
    """{grade: [series dict, ...]} from cors_errors.npz."""
    z = np.load(path, allow_pickle=True)
    return {g: list(z[g]) for g in GRADES}


# ------------------------------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--max-jobs", type=int, default=0, help="debug: limit number of pair-days")
    ap.add_argument("--stats-only", action="store_true",
                    help="rebuild cors_summary.csv and the printed summary from the existing cors_errors.npz")
    args = ap.parse_args()
    if args.stats_only:
        meta = np.load(OUT_NPZ, allow_pickle=True)["meta"].item()
        series = load()
        df = pd.DataFrame([series_stats(g, s) for g in GRADES for s in series[g]])
        df.to_csv(OUT_CSV, index=False, float_format="%.5g")
        print(f"rebuilt {OUT_CSV} from {OUT_NPZ}")
        summarize(df, series, meta["problems"], {tuple(k.split(":", 1)): v for k, v in meta["antenna_pcv"].items()})
        return
    if not os.access(RNX2RTKP, os.X_OK):
        sys.exit(f"rnx2rtkp not found at {RNX2RTKP}; build RTKLIB demo5 (app/consapp/rnx2rtkp/gcc)")
    hat = have_hatanaka()
    t0 = time.time()
    stations = sorted({s for b, r, _ in PAIRS for s in (b, r)})
    coords = {s: read_coord(s) for s in stations}
    jobs = [(b, r, reg, y, d) for (b, r, reg) in PAIRS for (y, d) in DAYS]
    if args.max_jobs:
        jobs = jobs[:args.max_jobs]
    # downloads first (I/O bound, more threads), then processing (CPU bound)
    keys = sorted({obs_key(s, y, d, hat) for b, r, _, y, d in jobs for s in (b, r)} |
                  {k for *_, y, d in jobs for k in nav_keys(y, d)})
    with cf.ThreadPoolExecutor(8) as ex:
        got = list(ex.map(lambda k: fetch(k, local(k)), keys))
    nbytes = sum(os.path.getsize(p) for p in got if p)
    print(f"{len(keys)} files ({sum(p is None for p in got)} missing), {nbytes / 1e6:.0f} MB cached, "
          f"hatanaka={hat}, {time.time() - t0:.0f}s")
    series = {g: [] for g in GRADES}
    problems = []
    with cf.ThreadPoolExecutor(args.workers) as ex:
        futs = [ex.submit(process_pair_day, *j, coords, hat) for j in jobs]
        for fu in cf.as_completed(futs):
            tag, out, msg = fu.result()
            if out is None:
                problems.append(f"{tag}: {msg}")
                continue
            for g in GRADES:
                if out[g] is None:
                    problems.append(f"{tag}: no {g} solution")
                else:
                    series[g].append(out[g])
    for g in GRADES:
        series[g].sort(key=lambda s: (s["pair"], s["date"]))
    rows = [series_stats(g, s) for g in GRADES for s in series[g]]
    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False, float_format="%.5g")
    st_meta = {}
    for s in stations:
        c = coords[s]
        st_meta[s.upper()] = dict(xyz2020=c["xyz2020"].tolist(), vel_m_per_yr=c["vel"].tolist(),
                                  coord_antenna=c["coord_ant"], antenna_installed=c["ant_installed"],
                                  coord_computed=c["computed"])
    ants = {}
    for g in GRADES:
        for s in series[g]:
            for who in ("rover", "base"):
                ants[(s[who], s[who + "_ant"])] = pcv_found(s[who + "_ant"])
    meta = dict(source="NOAA NGS CORS via s3://noaa-cors-pds (30-s daily RINEX 2.11, brdc nav)",
                truth="NGS coord_20 IGS20/ITRF2020 ARP + velocity propagated to mid-day; antenna deltas 0",
                software=f"RTKLIB demo5 rnx2rtkp ({RNX2RTKP})", antex=ATX,
                pairs=[dict(base=b.upper(), rover=r.upper(), region=reg) for b, r, reg in PAIRS],
                days=[f"{y}-{d:03d}" for y, d in DAYS], grades=list(GRADES), stations=st_meta,
                antenna_pcv={f"{k[0]}:{k[1]}": v for k, v in sorted(ants.items())},
                conf_common=COMMON_OPTS, conf_grade=GRADE_OPTS, problems=problems,
                fields=dict(t="s of GPST day", en="north error m", ee="east error m", eu="up error m",
                            q="1 fix,2 float,4 dgps,5 single", ns="satellites used"))
    obj = {g: np.empty(len(series[g]), dtype=object) for g in GRADES}
    for g in GRADES:
        obj[g][:] = series[g]
    np.savez_compressed(OUT_NPZ, meta=np.array(meta, dtype=object), **obj)
    print(f"processed {len(jobs)} pair-days in {time.time() - t0:.0f}s -> {OUT_NPZ} "
          f"({os.path.getsize(OUT_NPZ) / 1e6:.1f} MB), {OUT_CSV}")
    summarize(df, series, problems, ants)


def summarize(df, series, problems, ants):
    hdr = (f"{'grade':10s} {'n':>3s} {'epochs':>7s} {'fix%':>6s} {'sd_h':>8s} {'p95_h':>8s} {'max_h':>8s} "
           f"{'pool95':>8s} {'poolmax':>8s} {'rho1':>6s} {'tau1/e':>8s}")
    for title, sfx, t_min in (("whole day, incl. cold-start convergence", "", 0.0),
                              (f"warm: first {WARM_S / 60:.0f} min after the daily cold start skipped", "_warm", WARM_S)):
        print(f"\nPer-grade summary, {title} (medians over pair-days [m]; pooled = all epochs of all pair-days)")
        print(hdr)
        for g in GRADES:
            d = df[df.grade == g]
            if d.empty:
                continue
            h = np.concatenate([np.hypot(s["en"], s["ee"])[s["t"] >= s["t"][0] + t_min] for s in series[g]])
            n = int(d.n_epochs.sum() if not sfx else d.n_warm.sum())
            fix = f"{100 * d['fix_rate' + sfx].median():6.1f}" if g == "rtk_fix" else f"{'-':>6s}"
            print(f"{g:10s} {len(d):3d} {n:7d} {fix} {d['sd_h' + sfx].median():8.4f} {d['p95_h' + sfx].median():8.4f} "
                  f"{d['max_h' + sfx].median():8.3f} {np.percentile(h, 95):8.4f} {h.max():8.3f} "
                  f"{d['rho1' + sfx].median():6.3f} {d['tau_e_s' + sfx].median():7.0f}s")
    d = df[df.grade == "rtk_fix"]
    if not d.empty:
        allq = np.concatenate([s["q"] for s in series["rtk_fix"]])
        hf = np.concatenate([np.hypot(s["en"], s["ee"])[s["q"] == 1] for s in series["rtk_fix"]])
        bias = np.hypot(d.bias_n, d.bias_e)  # all epochs
        warmq = np.concatenate([s["q"][s["t"] >= s["t"][0] + WARM_S] for s in series["rtk_fix"]])
        print(f"\nrtk_fix: pooled fix rate {100 * np.mean(allq == 1):.1f}% (warm {100 * np.mean(warmq == 1):.1f}%; "
              f"pair-day range {100 * d.fix_rate.min():.0f}-{100 * d.fix_rate.max():.0f}%); FIXED epochs only: "
              f"median sd_h {100 * d.sd_h_fixed.median():.2f} cm, pooled p50/p95 {100 * np.median(hf):.2f}/"
              f"{100 * np.percentile(hf, 95):.2f} cm, |daily mean error| median {100 * d.bias_h_fixed.median():.2f} cm "
              f"(max {100 * d.bias_h_fixed.max():.2f} cm; all epochs: median {100 * bias.median():.2f}, "
              f"max {100 * bias.max():.2f} cm)")
        print("  typical RTK spec ~1-2 cm (8 mm + 1 ppm horizontal): "
              + ("consistent" if np.percentile(hf, 95) < 0.03 else "fixed epochs exceed it")
              + "; float/convergence epochs add the decimetre tail.")
        by = d.groupby(pd.cut(d.baseline_km, [0, 10, 20, 30]), observed=True)
        print("  by baseline: " + ", ".join(f"{k}: fix {100 * v.fix_rate.median():.0f}%, p95 "
                                            f"{100 * v.p95_h.median():.1f} cm" for k, v in by))
        print("\nper pair (rtk_fix, medians over days): fixed-epoch daily bias is a truth-consistency check")
        pp = d.groupby("pair", sort=False).agg(base_km=("baseline_km", "first"), days=("date", "size"),
                                                fix=("fix_rate", "median"), fix_min=("fix_rate", "min"),
                                                p95_cm=("p95_h", "median"), p95_fixed_cm=("p95_h_fixed", "median"),
                                                bias_fixed_cm=("bias_h_fixed", "median"), tau_s=("tau_e_s", "median"))
        for c in ("p95_cm", "p95_fixed_cm", "bias_fixed_cm"):
            pp[c] *= 100
        print(pp.sort_values("base_km").round(3).to_string())
    diff = sorted({(s["pair"], s["date"], tuple(s["ant_differs_from_coord"])) for s in series["rtk_fix"]
                   if s["ant_differs_from_coord"]})
    if diff:
        print("RINEX antenna differs from the coord_20 'current antenna' record (equipment change; ARP truth kept):",
              *[f"{a} {b}: {', '.join(c)}" for a, b, c in diff], sep="\n  ")
    nopcv = [k for k, v in ants.items() if v != "exact"]
    if nopcv:
        print("antennas without exact igs14.atx entry:", nopcv)
    if problems:
        print("problems:", *problems, sep="\n  ")


if __name__ == "__main__":
    main()
