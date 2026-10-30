"""坐标系转换工具（GPS84 / GCJ02 / BD09）.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/util/GpsUtil.java

纯静态算法类，逐行照抄。Java 的 ``double[]`` 在这里用 ``tuple[float, float]``
表示，元素顺序与 Java 一致 —— ``[纬度, 经度]``（注意**不是**常见的 ``[经度, 纬度]``）。

``main`` 方法在 Java 里已被注释掉，因此不迁移。
"""

from __future__ import annotations

import math
from typing import Tuple

#: Java: ``public static double pi``
PI = 3.1415926535897932384626
#: Java: ``public static double x_pi``
X_PI = 3.14159265358979324 * 3000.0 / 180.0
#: Java: ``public static double a``
A = 6378245.0
#: Java: ``public static double ee``
EE = 0.00669342162296594323


def transform_lat(x: float, y: float) -> float:
    """Java: ``public static double transformLat(double x, double y)``."""
    ret = (
        -100.0
        + 2.0 * x
        + 3.0 * y
        + 0.2 * y * y
        + 0.1 * x * y
        + 0.2 * math.sqrt(abs(x))
    )
    ret += (20.0 * math.sin(6.0 * x * PI) + 20.0 * math.sin(2.0 * x * PI)) * 2.0 / 3.0
    ret += (20.0 * math.sin(y * PI) + 40.0 * math.sin(y / 3.0 * PI)) * 2.0 / 3.0
    ret += (160.0 * math.sin(y / 12.0 * PI) + 320 * math.sin(y * PI / 30.0)) * 2.0 / 3.0
    return ret


def transform_lon(x: float, y: float) -> float:
    """Java: ``public static double transformLon(double x, double y)``."""
    ret = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * math.sqrt(abs(x))
    ret += (20.0 * math.sin(6.0 * x * PI) + 20.0 * math.sin(2.0 * x * PI)) * 2.0 / 3.0
    ret += (20.0 * math.sin(x * PI) + 40.0 * math.sin(x / 3.0 * PI)) * 2.0 / 3.0
    ret += (150.0 * math.sin(x / 12.0 * PI) + 300.0 * math.sin(x / 30.0 * PI)) * 2.0 / 3.0
    return ret


def out_of_china(lat: float, lon: float) -> bool:
    """Java: ``public static boolean outOfChina(double lat, double lon)``."""
    if lon < 72.004 or lon > 137.8347:
        return True
    if lat < 0.8293 or lat > 55.8271:
        return True
    return False


def transform(lat: float, lon: float) -> Tuple[float, float]:
    """Java: ``public static double[] transform(double lat, double lon)``."""
    if out_of_china(lat, lon):
        return (lat, lon)
    d_lat = transform_lat(lon - 105.0, lat - 35.0)
    d_lon = transform_lon(lon - 105.0, lat - 35.0)
    rad_lat = lat / 180.0 * PI
    magic = math.sin(rad_lat)
    magic = 1 - EE * magic * magic
    sqrt_magic = math.sqrt(magic)
    d_lat = (d_lat * 180.0) / ((A * (1 - EE)) / (magic * sqrt_magic) * PI)
    d_lon = (d_lon * 180.0) / (A / sqrt_magic * math.cos(rad_lat) * PI)
    mg_lat = lat + d_lat
    mg_lon = lon + d_lon
    return (mg_lat, mg_lon)


# Java: public static double[] gps84_To_Gcj02(double lat, double lon)
def gps84_to_gcj02(lat: float, lon: float) -> Tuple[float, float]:
    """84 -> 火星坐标系 (GCJ-02)。"""
    if out_of_china(lat, lon):
        return (lat, lon)
    d_lat = transform_lat(lon - 105.0, lat - 35.0)
    d_lon = transform_lon(lon - 105.0, lat - 35.0)
    rad_lat = lat / 180.0 * PI
    magic = math.sin(rad_lat)
    magic = 1 - EE * magic * magic
    sqrt_magic = math.sqrt(magic)
    d_lat = (d_lat * 180.0) / ((A * (1 - EE)) / (magic * sqrt_magic) * PI)
    d_lon = (d_lon * 180.0) / (A / sqrt_magic * math.cos(rad_lat) * PI)
    mg_lat = lat + d_lat
    mg_lon = lon + d_lon
    return (mg_lat, mg_lon)


# Java: public static double[] gcj02_To_Gps84(double lat, double lon)
def gcj02_to_gps84(lat: float, lon: float) -> Tuple[float, float]:
    """火星坐标系 (GCJ-02) -> 84。"""
    gps = transform(lat, lon)
    lontitude = lon * 2 - gps[1]
    latitude = lat * 2 - gps[0]
    return (latitude, lontitude)


# Java: public static double[] gcj02_To_Bd09(double lat, double lon)
def gcj02_to_bd09(lat: float, lon: float) -> Tuple[float, float]:
    """火星坐标系 (GCJ-02) -> 百度坐标系 (BD-09)。"""
    x = lon
    y = lat
    z = math.sqrt(x * x + y * y) + 0.00002 * math.sin(y * X_PI)
    theta = math.atan2(y, x) + 0.000003 * math.cos(x * X_PI)
    temp_lon = z * math.cos(theta) + 0.0065
    temp_lat = z * math.sin(theta) + 0.006
    return (temp_lat, temp_lon)


# Java: public static double[] bd09_To_Gcj02(double lat, double lon)
def bd09_to_gcj02(lat: float, lon: float) -> Tuple[float, float]:
    """百度坐标系 (BD-09) -> 火星坐标系 (GCJ-02)。"""
    x = lon - 0.0065
    y = lat - 0.006
    z = math.sqrt(x * x + y * y) - 0.00002 * math.sin(y * X_PI)
    theta = math.atan2(y, x) - 0.000003 * math.cos(x * X_PI)
    temp_lon = z * math.cos(theta)
    temp_lat = z * math.sin(theta)
    return (temp_lat, temp_lon)


# Java: public static double[] gps84_To_bd09(double lat, double lon)
def gps84_to_bd09(lat: float, lon: float) -> Tuple[float, float]:
    """gps84 -> bd09。"""
    gcj02 = gps84_to_gcj02(lat, lon)
    return gcj02_to_bd09(gcj02[0], gcj02[1])


# Java: public static double[] bd09_To_gps84(double lat, double lon)
def bd09_to_gps84(lat: float, lon: float) -> Tuple[float, float]:
    """bd09 -> gps84（保留小数点后六位）。"""
    gcj02 = bd09_to_gcj02(lat, lon)
    gps84 = gcj02_to_gps84(gcj02[0], gcj02[1])
    return (retain6(gps84[0]), retain6(gps84[1]))


def retain6(num: float) -> float:
    """Java: ``public static double retain6(double num)`` —— ``String.format("%.6f")``."""
    return float(format(num, ".6f"))


__all__ = [
    "A",
    "EE",
    "PI",
    "X_PI",
    "bd09_to_gcj02",
    "bd09_to_gps84",
    "gcj02_to_bd09",
    "gcj02_to_gps84",
    "gps84_to_bd09",
    "gps84_to_gcj02",
    "out_of_china",
    "retain6",
    "transform",
    "transform_lat",
    "transform_lon",
]
