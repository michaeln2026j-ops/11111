#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Passive run logger for the feed car (ROS Kinetic, Python 2.7). Subscribes only, never publishes:
it cannot affect route_follow, the chassis or the safety layer.

Every traversal of the route is written to ~/ce_logs/<route>/run_<start time>_<k>.csv with columns
    t, s, e, x, y, yaw, v, scan_d
s   arc length along the taught route (m)
e   signed lateral error of the measured point from the route (m, left of travel positive)
v   speed from /odom (m/s)
scan_d  minimum laser range in a side sector (m): the distance to the trough / wall measured directly by
        the lidar, independent of the localisation (set _side_deg to the trough side, NaN when unused)
Incomplete runs (logger started mid-route, run interrupted) are written with suffix _partial.

    python ~/ce_logger.py _route:=feed_full
    python ~/ce_logger.py _route:=feed_full _off_x:=0.8 _off_y:=0.0 _side_deg:=-90 _side_win_deg:=5
Stop with Ctrl-C (the current run is saved as partial unless it covered the whole route).
"""
from __future__ import division, print_function

import math
import os
import sys
import time

import rospy
import tf
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ce_core import RunRecorder, load_route  # noqa: E402


class Logger(object):
    def __init__(self):
        name = rospy.get_param("~route")
        route_dir = os.path.expanduser(rospy.get_param("~route_dir", "~/routes"))
        self.route = load_route(os.path.join(route_dir, name + ".yaml"))
        self.out = os.path.join(os.path.expanduser(rospy.get_param("~out_dir", "~/ce_logs")), name)
        if not os.path.isdir(self.out):
            os.makedirs(self.out)
        self.map_frame = rospy.get_param("~map_frame", "map")
        self.base_frame = rospy.get_param("~base_frame", "base_link")
        self.rate = rospy.get_param("~rate", 20.0)
        self.side = rospy.get_param("~side_deg", None)
        self.side_win = math.radians(rospy.get_param("~side_win_deg", 5.0))
        self.v, self.scan_d = float("nan"), float("nan")
        self.t0 = time.strftime("%Y%m%d_%H%M%S")
        self.rec = RunRecorder(self.route, self.write, win=int(rospy.get_param("~win", 40)),
                               offset=(rospy.get_param("~off_x", 0.0), rospy.get_param("~off_y", 0.0)))
        rospy.Subscriber("/odom", Odometry, self.on_odom, queue_size=5)
        if self.side is not None:
            rospy.Subscriber(rospy.get_param("~scan_topic", "/scan"), LaserScan, self.on_scan, queue_size=2)
        self.tfl = tf.TransformListener()
        rospy.loginfo("ce_logger: route %s, %d segments, length %.1f m, %s; writing to %s",
                      name, self.route.n_seg, self.route.length, "closed loop" if self.route.closed else "open",
                      self.out)

    def on_odom(self, m):
        self.v = m.twist.twist.linear.x

    def on_scan(self, m):
        a = math.radians(self.side)
        best = float("inf")
        for k, r in enumerate(m.ranges):
            ang = m.angle_min + k * m.angle_increment
            if abs(math.atan2(math.sin(ang - a), math.cos(ang - a))) <= self.side_win and \
                    m.range_min < r < m.range_max and not math.isnan(r):
                best = min(best, r)
        self.scan_d = best if best < float("inf") else float("nan")

    def write(self, k, rows, complete):
        fn = os.path.join(self.out, "run_%s_%03d%s.csv" % (self.t0, k, "" if complete else "_partial"))
        with open(fn, "w") as f:
            f.write("t,s,e,x,y,yaw,v,scan_d\n")
            for r in rows:
                f.write(",".join("%.4f" % v for v in r) + "\n")
        emax = max(abs(r[2]) for r in rows)
        rospy.loginfo("ce_logger: run %d %s, %d samples, max |e| %.3f m -> %s", k,
                      "complete" if complete else "PARTIAL", len(rows), emax, os.path.basename(fn))

    def spin(self):
        r = rospy.Rate(self.rate)
        last = None
        while not rospy.is_shutdown():
            try:
                stamp = self.tfl.getLatestCommonTime(self.map_frame, self.base_frame)
                if stamp != last:
                    (x, y, _), q = self.tfl.lookupTransform(self.map_frame, self.base_frame, stamp)
                    yaw = tf.transformations.euler_from_quaternion(q)[2]
                    self.rec.feed(stamp.to_sec(), x, y, yaw, self.v, self.scan_d)
                    last = stamp
            except (tf.Exception, tf.LookupException, tf.ConnectivityException, tf.ExtrapolationException):
                pass
            try:
                r.sleep()
            except rospy.ROSInterruptException:
                break
        self.rec.finish()
        if self.rec.n_lost:
            rospy.logwarn("ce_logger: %d samples needed a global re-match (pose jumps)", self.rec.n_lost)


if __name__ == "__main__":
    rospy.init_node("ce_logger")
    Logger().spin()
