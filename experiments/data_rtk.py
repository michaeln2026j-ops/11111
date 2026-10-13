"""Real RTK positioning-error series from the i2Nav awesome-gins-datasets.

RTK fixes (GNSS_RTK.pos) are compared against the navigation-grade ground
truth (i300/truth.nav, IMU centre) after applying the documented GNSS antenna
lever arm for the HGuide-i300 (FRD: -0.075, 0.46, -0.218 m). The horizontal
error is projected onto the vehicle's lateral (cross-track) and longitudinal
axes using the true yaw. Output: data/rtk_error.npz (t, lat_err, lon_err).

Citation: Tang, Zhang, Niu et al., IEEE Sensors J. 2022 (i2Nav, Wuhan Univ.).
"""
import os

import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = "/home/user/data/i2nav"
LEVER_FRD = np.array([-0.075, 0.46, -0.218])
R_EARTH = 6378137.0


def main():
    pos = np.loadtxt(os.path.join(SRC, "GNSS_RTK.pos"))
    nav = np.loadtxt(os.path.join(SRC, "i300", "truth.nav"))
    t_nav = nav[:, 1]
    keep = (pos[:, 0] >= t_nav[0]) & (pos[:, 0] <= t_nav[-1])
    pos = pos[keep]
    t = pos[:, 0]
    interp = lambda c: np.interp(t, t_nav, nav[:, c])
    lat_t, lon_t = interp(2), interp(3)
    roll, pitch = np.radians(interp(8)), np.radians(interp(9))
    yaw = np.unwrap(np.radians(nav[:, 10]))
    yaw = np.interp(t, t_nav, yaw)
    # body (FRD) -> NED rotation, ZYX Euler
    cr, sr, cp, sp, cy, sy = np.cos(roll), np.sin(roll), np.cos(pitch), np.sin(pitch), np.cos(yaw), np.sin(yaw)
    lx, ly, lz = LEVER_FRD
    dn = cy * cp * lx + (cy * sp * sr - sy * cr) * ly + (cy * sp * cr + sy * sr) * lz
    de = sy * cp * lx + (sy * sp * sr + cy * cr) * ly + (sy * sp * cr - cy * sr) * lz
    lat0 = np.radians(lat_t.mean())
    n_true = np.radians(lat_t) * R_EARTH + dn
    e_true = np.radians(lon_t) * R_EARTH * np.cos(lat0) + de
    n_rtk = np.radians(pos[:, 1]) * R_EARTH
    e_rtk = np.radians(pos[:, 2]) * R_EARTH * np.cos(lat0)
    en, ee = n_rtk - n_true, e_rtk - e_true
    lon_err = en * cy + ee * sy  # along heading
    lat_err = -en * sy + ee * cy  # to the right
    np.savez(os.path.join(ROOT, "data", "rtk_error.npz"), t=t - t[0], lat_err=lat_err, lon_err=lon_err)
    dt = np.median(np.diff(t))
    print(f"{len(t)} RTK epochs, dt={dt:.2f}s, duration {t[-1]-t[0]:.0f}s")
    for name, v in [("lateral", lat_err), ("longitudinal", lon_err)]:
        print(f"{name}: mean={v.mean()*100:.2f} cm  std={v.std()*100:.2f} cm  "
              f"p95|.|={np.percentile(np.abs(v),95)*100:.2f} cm")
    ac = np.correlate(lat_err - lat_err.mean(), lat_err - lat_err.mean(), "full")[len(t) - 1:]
    ac /= ac[0]
    print("lateral autocorr time (1/e):", float(np.argmax(ac < np.exp(-1)) * dt), "s")


if __name__ == "__main__":
    main()
