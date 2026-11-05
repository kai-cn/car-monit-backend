// 来源: ruoyi-system/src/main/java/com/ruoyi/base/util/GpsUtil.java
// 职责: WGS84 与 GCJ-02 互转，以及 Java `Double.toString` / `BigDecimal.setScale(6, HALF_UP)` 的等价写法。
// 对应关系: gps84_To_Gcj02 -> gps84_to_gcj02；gcj02_To_Gps84 -> gcj02_to_gps84。

use rust_decimal::prelude::ToPrimitive;
use rust_decimal::{Decimal, RoundingStrategy};

/// Java: `GpsUtil.pi`（double 能表示的取值就是 3.141592653589793）。
const PI: f64 = 3.141592653589793;
const A: f64 = 6378245.0;
const EE: f64 = 0.00669342162296594323;

pub fn out_of_china(lat: f64, lon: f64) -> bool {
    lon < 72.004 || lon > 137.8347 || lat < 0.8293 || lat > 55.8271
}

fn transform_lat(x: f64, y: f64) -> f64 {
    let mut ret = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * (x.abs()).sqrt();
    ret += (20.0 * (6.0 * x * PI).sin() + 20.0 * (2.0 * x * PI).sin()) * 2.0 / 3.0;
    ret += (20.0 * (y * PI).sin() + 40.0 * (y / 3.0 * PI).sin()) * 2.0 / 3.0;
    ret += (160.0 * (y / 12.0 * PI).sin() + 320.0 * (y * PI / 30.0).sin()) * 2.0 / 3.0;
    ret
}

fn transform_lon(x: f64, y: f64) -> f64 {
    let mut ret = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * (x.abs()).sqrt();
    ret += (20.0 * (6.0 * x * PI).sin() + 20.0 * (2.0 * x * PI).sin()) * 2.0 / 3.0;
    ret += (20.0 * (x * PI).sin() + 40.0 * (x / 3.0 * PI).sin()) * 2.0 / 3.0;
    ret += (150.0 * (x / 12.0 * PI).sin() + 300.0 * (x / 30.0 * PI).sin()) * 2.0 / 3.0;
    ret
}

/// Java: `transform(lat, lon)` —— 返回 `[lat, lon]`。
fn transform(lat: f64, lon: f64) -> (f64, f64) {
    if out_of_china(lat, lon) {
        return (lat, lon);
    }
    let mut d_lat = transform_lat(lon - 105.0, lat - 35.0);
    let mut d_lon = transform_lon(lon - 105.0, lat - 35.0);
    let rad_lat = lat / 180.0 * PI;
    let mut magic = rad_lat.sin();
    magic = 1.0 - EE * magic * magic;
    let sqrt_magic = magic.sqrt();
    d_lat = (d_lat * 180.0) / ((A * (1.0 - EE)) / (magic * sqrt_magic) * PI);
    d_lon = (d_lon * 180.0) / (A / sqrt_magic * rad_lat.cos() * PI);
    (lat + d_lat, lon + d_lon)
}

/// Java: `gps84_To_Gcj02(lat, lon)` —— 返回 `[lat, lon]`。
pub fn gps84_to_gcj02(lat: f64, lon: f64) -> (f64, f64) {
    if out_of_china(lat, lon) {
        return (lat, lon);
    }
    let mut d_lat = transform_lat(lon - 105.0, lat - 35.0);
    let mut d_lon = transform_lon(lon - 105.0, lat - 35.0);
    let rad_lat = lat / 180.0 * PI;
    let mut magic = rad_lat.sin();
    magic = 1.0 - EE * magic * magic;
    let sqrt_magic = magic.sqrt();
    d_lat = (d_lat * 180.0) / ((A * (1.0 - EE)) / (magic * sqrt_magic) * PI);
    d_lon = (d_lon * 180.0) / (A / sqrt_magic * rad_lat.cos() * PI);
    (lat + d_lat, lon + d_lon)
}

/// Java: `gcj02_To_Gps84(lat, lon)` —— 返回 `[lat, lon]`（用对称差反推）。
pub fn gcj02_to_gps84(lat: f64, lon: f64) -> (f64, f64) {
    let gps = transform(lat, lon);
    (lat * 2.0 - gps.0, lon * 2.0 - gps.1)
}

/// Java: `BigDecimal.valueOf(d).setScale(6, RoundingMode.HALF_UP).doubleValue()`。
/// 先按 `Double.toString` 的最短十进制表示建 BigDecimal，再六位四舍五入，最后回到 double。
pub fn round6(value: f64) -> f64 {
    java_double(value)
        .parse::<Decimal>()
        .or_else(|_| Decimal::from_f64_retain(value).ok_or(()))
        .unwrap_or_default()
        // Java 的 HALF_UP 是「远离零」，rust_decimal 的 round_dp 默认是银行家舍入。
        .round_dp_with_strategy(6, RoundingStrategy::MidpointAwayFromZero)
        .to_f64()
        .unwrap_or(value)
}

/// Java: 腾讯 polyline 的增量解码 —— `arr[0/1]` 取原值，其余 `arr[i-2] + value/1e6`。
/// 空数组/奇数长度在 Java 里是越界异常（`getDoubleValue(1)`、`arr[i+1]`），
/// 会被 `calcLonAndLatPaths` 的 catch 吞掉，这里同样返回 None。
pub fn decode_polyline(polyline: &[f64]) -> Option<Vec<f64>> {
    if polyline.len() < 2 || polyline.len() % 2 != 0 {
        return None;
    }
    let mut arr = vec![0.0f64; polyline.len()];
    arr[0] = polyline[0];
    arr[1] = polyline[1];
    for i in 2..polyline.len() {
        arr[i] = arr[i - 2] + polyline[i] / 1000000.0;
    }
    Some(arr)
}

/// Java: `Double.toString`。坐标取值范围（72~137 / 0.8~55）不会触发 Java 的科学计数法分支
/// （<1e-3 或 >=1e7），所以只需补上 Rust 省略的 `.0`。
pub fn java_double(value: f64) -> String {
    if value.is_nan() {
        return "NaN".to_string();
    }
    if value.is_infinite() {
        return if value > 0.0 { "Infinity" } else { "-Infinity" }.to_string();
    }
    let text = format!("{value}");
    if !text.contains('.') && !text.contains('e') {
        return format!("{text}.0");
    }
    text
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn java_double_keeps_the_trailing_zero_of_integers() {
        assert_eq!(java_double(27.0), "27.0");
        assert_eq!(java_double(113.893778), "113.893778");
        assert_eq!(java_double(-0.5), "-0.5");
    }

    #[test]
    fn round6_matches_bigdecimal_half_up() {
        assert_eq!(java_double(round6(113.8937784)), "113.893778");
        assert_eq!(java_double(round6(113.8937785)), "113.893779");
        assert_eq!(java_double(round6(27.0)), "27.0");
    }

    #[test]
    fn gcj02_conversion_is_a_small_offset_inside_china() {
        let (lat, lon) = gps84_to_gcj02(27.026869, 113.8937927);
        assert!((lat - 27.026905).abs() < 0.01, "lat={lat}");
        assert!((lon - 113.893778).abs() < 0.01, "lon={lon}");
    }

    #[test]
    fn points_outside_china_are_returned_unchanged() {
        let (lat, lon) = gps84_to_gcj02(48.0, 200.0);
        assert_eq!((lat, lon), (48.0, 200.0));
        assert!(out_of_china(27.0, 72.0));
    }

    /// 腾讯 direction 返回的是增量编码，Java 用 `arr[i-2] + value/1e6` 还原。
    #[test]
    fn decode_polyline_accumulates_every_two_columns() {
        // 增量单位是 1e-6：1737 -> +0.001737。
        let polyline = [113.893778_f64, 27.026905, 1737.0, 893.0];
        let arr = decode_polyline(&polyline).unwrap();
        assert_eq!(java_double(arr[2]), "113.895515");
        assert_eq!(java_double(arr[3]), "27.027798");
        assert!(decode_polyline(&[1.0, 2.0, 3.0]).is_none());
        assert!(decode_polyline(&[]).is_none());
    }
}
