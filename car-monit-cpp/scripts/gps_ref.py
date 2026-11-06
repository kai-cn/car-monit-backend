#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用 Python 独立实现一遍 GpsUtil 的公式，产出 tests/trail_geo_test.cpp 的对拍常量。

为什么这么麻烦：C++ 侧自己算自己验等于没验。这里的 Python 实现是**照着公开算法另写一份**
（不是从 C++ 翻译过来的），两边同时对不上就说明有一边抄错了 —— 最容易抄错的是
返回值顺序（gps84_To_Gcj02 返回 [lat, lon]，而 Geometry.paths 要的是 [lon, lat]）。

用法：python scripts/gps_ref.py > /tmp/gpsvec.txt   然后把数组贴进 trail_geo_test.cpp
"""
import math

pi = 3.1415926535897932384626
a = 6378245.0
ee = 0.00669342162296594323


def out_of_china(lat, lon):
    return not (72.004 <= lon <= 137.8347 and 0.8293 <= lat <= 55.8271)


def _t_lat(x, y):
    r = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * math.sqrt(abs(x))
    r += (20.0 * math.sin(6.0 * x * pi) + 20.0 * math.sin(2.0 * x * pi)) * 2.0 / 3.0
    r += (20.0 * math.sin(y * pi) + 40.0 * math.sin(y / 3.0 * pi)) * 2.0 / 3.0
    r += (160.0 * math.sin(y / 12.0 * pi) + 320 * math.sin(y * pi / 30.0)) * 2.0 / 3.0
    return r


def _t_lon(x, y):
    r = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * math.sqrt(abs(x))
    r += (20.0 * math.sin(6.0 * x * pi) + 20.0 * math.sin(2.0 * x * pi)) * 2.0 / 3.0
    r += (20.0 * math.sin(x * pi) + 40.0 * math.sin(x / 3.0 * pi)) * 2.0 / 3.0
    r += (150.0 * math.sin(x / 12.0 * pi) + 300.0 * math.sin(x / 30.0 * pi)) * 2.0 / 3.0
    return r


def transform(lat, lon):
    if out_of_china(lat, lon):
        return (lat, lon)
    d_lat = _t_lat(lon - 105.0, lat - 35.0)
    d_lon = _t_lon(lon - 105.0, lat - 35.0)
    rad_lat = lat / 180.0 * pi
    magic = math.sin(rad_lat)
    magic = 1 - ee * magic * magic
    sqrt_magic = math.sqrt(magic)
    d_lat = (d_lat * 180.0) / ((a * (1 - ee)) / (magic * sqrt_magic) * pi)
    d_lon = (d_lon * 180.0) / (a / sqrt_magic * math.cos(rad_lat) * pi)
    return (lat + d_lat, lon + d_lon)


def gcj02_to_wgs84(lat, lon):
    t = transform(lat, lon)
    return (lat * 2 - t[0], lon * 2 - t[1])


PTS = [(29.262412098, 117.758344803), (39.983455, 116.326612), (22.5431, 114.0579),
       (0.0, 0.0), (48.0, 10.0), (26.701453255, 116.038089826)]

print("// 由 scripts/gps_ref.py（Python 独立实现的同一套公式）产出，不是本工程自己的输出。")
print("// 每行 {原始 lat, 原始 lon, gcj lat, gcj lon, gcj->wgs84 反算 lat, 反算 lon}")
print("static const double kGpsRef[][6] = {")
for lat, lon in PTS:
    g = transform(lat, lon)
    r = gcj02_to_wgs84(g[0], g[1])
    print("    {%.17g, %.17g, %.17g, %.17g, %.17g, %.17g}," % (lat, lon, g[0], g[1], r[0], r[1]))
print("};")
