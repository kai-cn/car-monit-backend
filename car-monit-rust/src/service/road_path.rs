// 来源: ruoyi-system/src/main/java/com/ruoyi/base/service/impl/RoadPathImpl.java
//       ruoyi-system/src/main/java/com/ruoyi/base/service/forest/RoadPathApi.java
//       ruoyi-system/src/main/java/com/ruoyi/base/util/LonLatPathsUtils.java
// 职责: 轨迹绘制用到的两个外部路径服务 —— 本地路网规划接口（Forest）与腾讯 direction 接口（RestTemplate）。
// 对应关系: getShortestRoadPath -> get_shortest_road_path；calcLonAndLatPaths -> calc_lon_and_lat_paths。
// 两者的失败语义都是「异常/非 0 status -> 返回 null」，由调用方回落到本地桩号绘制。

use md5::{Digest, Md5};
use serde_json::{json, Value};
use tracing::warn;

use crate::common::gps;
use crate::state::AppState;

/// Java: `@Post(url = "/api/routes/query")`。
const ROAD_PATH_PATH: &str = "/api/routes/query";

/// Java: `LonLatPathsUtils` 里的固定常量（key/secret/url）。
const TX_KEY: &str = "UVUBZ-6AY3V-FEGP2-UJSJP-SBJAJ-UTBT6";
const TX_SECRET: &str = "M9yNPgh8FLp33A0plztTK5sehD6gMqny";
const TX_PATH: &str = "/ws/direction/v1/driving/";

/// Java: RoadPathImpl.getShortestRoadPath —— 把每段的 routePoints 摊平成一个点数组。
/// 任何异常（连不上、success=false、segmentRoutes 为 null 的 NPE）都返回 null。
pub async fn get_shortest_road_path(state: &AppState, node_ids: &[String]) -> Option<String> {
    let base = state
        .settings
        .forest
        .variables
        .road_path_url
        .trim_end_matches('/')
        .to_string();
    if base.is_empty() {
        return None;
    }
    // Java: PathQueryRo（includeCoordinates/queryMode 是字符串 "TRUE"/"LENIENT"）。
    let body = json!({
        "nodeIds": node_ids,
        "pathType": "SHORTEST",
        "includeCoordinates": "TRUE",
        "queryMode": "LENIENT",
    });
    let response = state
        .http
        .post(format!("{base}{ROAD_PATH_PATH}"))
        .json(&body)
        .send()
        .await;
    let value = match response {
        Ok(response) if response.status().is_success() => match response.text().await {
            Ok(text) if !text.trim().is_empty() => {
                serde_json::from_str::<Value>(text.trim()).ok()?
            }
            _ => return None,
        },
        Ok(response) => {
            warn!(
                "【路网规划】{} 返回 HTTP {}",
                ROAD_PATH_PATH,
                response.status()
            );
            return None;
        }
        Err(err) => {
            warn!("【路网规划】{} 请求失败: {}", ROAD_PATH_PATH, err);
            return None;
        }
    };
    java_road_path_points(&value)
}

/// Java: RoadPathImpl 的解析部分（不发请求，便于单测）。
pub fn java_road_path_points(object: &Value) -> Option<String> {
    let success = object.get("success").and_then(Value::as_bool)?;
    if !success {
        warn!("【路网规划】接口调用结果success为false");
        return None;
    }
    let array = object.get("data")?.get("data")?.as_array()?;
    if array.is_empty() {
        return None;
    }
    let mut rtn: Vec<String> = Vec::new();
    for item in array {
        // Java: obj.to(ResData) 后 getSegmentRoutes() 为 null 会 NPE -> 整体返回 null。
        let routes = item.get("segmentRoutes")?.as_array()?;
        for route in routes {
            let points = route.get("routePoints")?.as_array()?;
            for point in points {
                rtn.push(java_point(point)?);
            }
        }
    }
    if rtn.is_empty() {
        return None;
    }
    Some(format!("[{}]", rtn.join(",")))
}

/// Java: `List<Double>` 经 fastjson2 toString —— 每个数按 Double.toString 写。
fn java_point(point: &Value) -> Option<String> {
    let items = point.as_array()?;
    let text: Vec<String> = items
        .iter()
        .map(|item| match item {
            Value::Number(number) => number
                .as_f64()
                .map(gps::java_double)
                .unwrap_or_else(|| number.to_string()),
            other => other.to_string(),
        })
        .collect();
    Some(format!("[{}]", text.join(",")))
}

/// Java: LonLatPathsUtils.calcLonAndLatPaths —— 返回 `[[lon,lat],...]` 字符串，失败返回 null。
/// 入参是 WGS84 的十进制字符串（Java 侧用 `Double.parseDouble` 解析，解析失败即异常 -> null）。
pub async fn calc_lon_and_lat_paths(
    state: &AppState,
    cur_lon: &str,
    cur_lat: &str,
    next_lon: &str,
    next_lat: &str,
    heading: &str,
    waypoints: &str,
) -> Option<String> {
    let base = state
        .settings
        .tx_service_url
        .trim_end_matches('/')
        .to_string();
    if base.is_empty() {
        return None;
    }
    // Java: gps84_To_Gcj02(lat, lon) 后 setScale(6, HALF_UP).doubleValue()，拼 "纬度,经度"。
    let from = gcj_from_to(cur_lon, cur_lat)?;
    let to = gcj_from_to(next_lon, next_lat)?;

    let mut sig_params: Vec<(&str, &str)> = vec![("from", from.as_str()), ("to", to.as_str())];
    if !heading.trim().is_empty() {
        sig_params.push(("heading", heading));
    }
    if !waypoints.trim().is_empty() {
        sig_params.push(("waypoints", waypoints));
    }
    let signature = tx_sig(TX_PATH, &sig_params, TX_KEY, TX_SECRET);

    // Java: getLngLat —— heading/waypoints 非空才带上，key/sig 始终带上。
    let mut url = format!("{base}{TX_PATH}?from={from}&to={to}");
    if !heading.trim().is_empty() {
        url.push_str(&format!("&heading={heading}"));
    }
    if !waypoints.trim().is_empty() {
        url.push_str(&format!("&waypoints={waypoints}"));
    }
    url.push_str(&format!("&key={TX_KEY}&sig={signature}"));

    let response = state.http.get(&url).send().await;
    let value = match response {
        Ok(response) if response.status().is_success() => match response.text().await {
            Ok(text) => serde_json::from_str::<Value>(text.trim()).ok()?,
            Err(_) => return None,
        },
        Ok(response) => {
            warn!("【腾讯路径】{} 返回 HTTP {}", TX_PATH, response.status());
            return None;
        }
        Err(err) => {
            warn!("【腾讯路径】请求失败: {err}");
            return None;
        }
    };
    tx_paths(&value)
}

/// Java: calcLonAndLatPaths 的解析部分（不发请求，便于单测）。
pub fn tx_paths(result: &Value) -> Option<String> {
    // Java: getIntValue("status")，非 0 直接 null（缺键按 0 处理，随后取 result 会 NPE -> null）。
    let status = result.get("status").and_then(Value::as_i64).unwrap_or(0);
    if status != 0 {
        return None;
    }
    let route = result
        .get("result")?
        .get("routes")?
        .as_array()?
        .first()?
        .clone();
    let polyline = route.get("polyline")?.as_array()?;
    let numbers: Vec<f64> = polyline
        .iter()
        .filter_map(|item| match item {
            Value::Number(number) => number.as_f64(),
            Value::String(text) => text.parse::<f64>().ok(),
            _ => None,
        })
        .collect();
    if numbers.len() != polyline.len() {
        return None;
    }
    let arr = gps::decode_polyline(&numbers)?;
    let mut rtn: Vec<String> = Vec::new();
    for pair in arr.chunks_exact(2) {
        // Java: gcj02_To_Gps84(lat, lon) -> [lat, lon]，各自六位四舍五入后交换成 [lon, lat]。
        let (lat, lon) = gps::gcj02_to_gps84(pair[0], pair[1]);
        let lon = gps::round6(lon);
        let lat = gps::round6(lat);
        rtn.push(format!(
            "[{},{}]",
            gps::java_double(lon),
            gps::java_double(lat)
        ));
    }
    if rtn.is_empty() {
        return None;
    }
    Some(format!("[{}]", rtn.join(",")))
}

/// Java: `BigDecimal.valueOf(gps[0]).setScale(6, HALF_UP).doubleValue()` 拼成的 "纬度,经度"。
fn gcj_from_to(lon: &str, lat: &str) -> Option<String> {
    let lon: f64 = lon.trim().parse().ok()?;
    let lat: f64 = lat.trim().parse().ok()?;
    let (lat, lon) = gps::gps84_to_gcj02(lat, lon);
    Some(format!(
        "{},{}",
        gps::java_double(gps::round6(lat)),
        gps::java_double(gps::round6(lon))
    ))
}

/// Java: LonLatPathsUtils.sig —— 按参数名字典序拼 `url?k=v&...` 再拼 secret 做 MD5（小写）。
/// 注意 Java 的分隔符是无条件追加的：值为空串时该项整条不写，但仍留下一个 `&`。
fn tx_sig(path: &str, params: &[(&str, &str)], key: &str, secret: &str) -> String {
    let mut entries: Vec<(&str, &str)> = params.to_vec();
    entries.push(("key", key));
    entries.sort_by(|left, right| left.0.cmp(right.0));
    let mut text = format!("{path}?");
    for (index, (name, value)) in entries.iter().enumerate() {
        let value = value.trim();
        if !value.is_empty() {
            text.push_str(name);
            text.push('=');
            text.push_str(value);
        }
        if index + 1 < entries.len() {
            text.push('&');
        }
    }
    text.push_str(secret);
    let mut hasher = Md5::new();
    hasher.update(text.as_bytes());
    hasher
        .finalize()
        .iter()
        .map(|byte| format!("{byte:02x}"))
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn road_path_points_flatten_every_segment() {
        let value = json!({
            "success": true,
            "data": {"data": [{
                "segmentRoutes": [
                    {"routePoints": [[113.8937927, 27.026869], [113.9, 27.1]]},
                    {"routePoints": [[118.3399669, 28.8140856]]}
                ]
            }]}
        });
        assert_eq!(
            java_road_path_points(&value).unwrap(),
            "[[113.8937927,27.026869],[113.9,27.1],[118.3399669,28.8140856]]"
        );
    }

    #[test]
    fn road_path_failure_shapes_all_become_null() {
        assert_eq!(java_road_path_points(&json!({"success": false})), None);
        assert_eq!(java_road_path_points(&json!({})), None);
        assert_eq!(java_road_path_points(&json!({"success": true})), None);
        // Java: segmentRoutes 为 null 时 for-each 抛 NPE，整个方法返回 null。
        assert_eq!(
            java_road_path_points(&json!({"success": true, "data": {"data": [{}]}})),
            None
        );
        assert_eq!(
            java_road_path_points(
                &json!({"success": true, "data": {"data": [{"segmentRoutes": []}]}})
            ),
            None
        );
    }

    #[test]
    fn whole_numbers_keep_the_java_decimal_point() {
        let value = json!({
            "success": true,
            "data": {"data": [{"segmentRoutes": [{"routePoints": [[113.0, 27.0]]}]}]}
        });
        assert_eq!(java_road_path_points(&value).unwrap(), "[[113.0,27.0]]");
    }

    #[test]
    fn tencent_status_non_zero_is_null() {
        assert_eq!(tx_paths(&json!({"status": 1, "message": "x"})), None);
        assert_eq!(tx_paths(&json!({"status": 0})), None);
    }

    #[test]
    fn tencent_polyline_is_decoded_and_converted_back() {
        // 两点：起点绝对值 + 一段增量，解码后各自 gcj02 -> wgs84、六位取整、经纬互换。
        let value = json!({
            "status": 0,
            "result": {"routes": [{"distance": 10, "polyline": [27.026905, 113.893778, 1000.0, 1000.0]}]}
        });
        let paths = tx_paths(&value).unwrap();
        assert!(paths.starts_with("[["), "{paths}");
        assert_eq!(paths.matches(",[").count(), 1, "{paths}");
        // 奇数长度的 polyline 在 Java 里越界 -> null。
        assert!(tx_paths(
            &json!({"status": 0, "result": {"routes": [{"polyline": [27.0, 113.0, 1.0]}]}})
        )
        .is_none());
    }

    #[test]
    fn tencent_sig_sorts_param_names() {
        let sig = tx_sig(
            TX_PATH,
            &[("from", "27.0,113.0"), ("to", "28.0,118.0")],
            TX_KEY,
            TX_SECRET,
        );
        assert_eq!(sig.len(), 32);
        assert!(sig.chars().all(|c| c.is_ascii_hexdigit()));
        // 与顺序无关：签名按参数名字典序拼接（from < key < to）。
        let reordered = tx_sig(
            TX_PATH,
            &[("to", "28.0,118.0"), ("from", "27.0,113.0")],
            TX_KEY,
            TX_SECRET,
        );
        assert_eq!(sig, reordered);
        // 多一个 waypoints 就是另一份签名。
        let with_waypoints = tx_sig(
            TX_PATH,
            &[
                ("from", "27.0,113.0"),
                ("to", "28.0,118.0"),
                ("waypoints", "27.5,115.5"),
            ],
            TX_KEY,
            TX_SECRET,
        );
        assert_ne!(sig, with_waypoints);
    }

    #[test]
    fn blank_value_leaves_an_empty_slot_like_java() {
        let sig = tx_sig(TX_PATH, &[("from", " "), ("to", "1,2")], "k", "s");
        // Java 排序后拼 "/ws/direction/v1/driving/?&key=k&to=1,2" + secret：
        // 值为空的项整条不写，但分隔符照样留下一个 `&`。
        let mut hasher = Md5::new();
        hasher.update(format!("{TX_PATH}?&key=k&to=1,2s").as_bytes());
        let expect: String = hasher
            .finalize()
            .iter()
            .map(|byte| format!("{byte:02x}"))
            .collect();
        assert_eq!(sig, expect);
    }
}
