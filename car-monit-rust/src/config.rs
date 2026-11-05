// 来源: ruoyi-admin/src/main/resources/application.yml
//       ruoyi-admin/src/main/resources/application-druid.yml
// 职责: 启动期配置加载，键名/默认值与 Java 保持一致。
// 对应关系: @ConfigurationProperties/@Value -> serde 反序列化；Spring relaxed binding -> APP_ + __。

use std::env;

use config::{Config, Environment, File, FileFormat};
use serde::Deserialize;

/// Java: application.yml + application-druid.yml 的合并默认值。
/// 嵌入为第一层配置源，保证磁盘文件缺省时仍与 Java 默认值一致。
pub const DEFAULT_YAML: &str = include_str!("../config/application.yaml");

#[derive(Debug, Clone, Deserialize)]
pub struct Settings {
    pub server: ServerSettings,
    pub ruoyi: RuoYiSettings,
    pub user: UserSettings,
    pub token: TokenSettings,
    pub database: DatabaseSettings,
    pub redis: RedisSettings,
    pub kafka: KafkaSettings,
    pub cdc: CdcSettings,
    pub elasticsearch: ElasticsearchSettings,
    pub oss: OssSettings,
    pub sms: SmsSettings,
    pub forest: ForestSettings,
    /// Java: hengda.appid / hengda.secret —— 恒达桩号转经纬度接口签名参数。
    pub hengda: HengdaSettings,
    /// Java: vehicleMonitor.baseUrl —— Forest 客户端的目标服务地址。
    #[serde(rename = "vehicleMonitor")]
    pub vehicle_monitor: VehicleMonitorSettings,
    pub monitor: MonitorSettings,
    pub xss: XssSettings,
    pub upload: UploadSettings,
    pub log: LogSettings,
    pub snapshot: SnapshotSettings,
    pub sharding: ShardingSettings,
    pub app: AppSettings,
    /// Java: `isLocalhost`（local 时实时轨迹任务只做落库、不判定驶出）。
    #[serde(default = "default_localhost")]
    pub is_localhost: String,
    /// Java: `tx-service-url` —— LonLatPathsUtils 走的腾讯 direction 服务。
    #[serde(rename = "tx-service-url", default)]
    pub tx_service_url: String,
    /// Java: `generator-code.mybatis-plus.enable`（决定代码生成取 vm 还是 vmplus 模板）。
    #[serde(rename = "generator-code", default)]
    pub generator_code: GeneratorCodeSettings,
}

#[derive(Debug, Clone, Deserialize, Default)]
pub struct GeneratorCodeSettings {
    #[serde(rename = "mybatis-plus", default)]
    pub mybatis_plus: GeneratorMybatisPlus,
}

#[derive(Debug, Clone, Deserialize, Default)]
pub struct GeneratorMybatisPlus {
    #[serde(default)]
    pub enable: bool,
}

fn default_localhost() -> String {
    "local".to_string()
}

#[derive(Debug, Clone, Deserialize)]
pub struct ServerSettings {
    pub port: u16,
}

#[derive(Debug, Clone, Deserialize)]
pub struct RuoYiSettings {
    pub name: String,
    pub version: String,
    pub profile: String,
    #[serde(rename = "addressEnabled")]
    pub address_enabled: bool,
    /// Java: ruoyi.captchaType（math | char）
    #[serde(rename = "captchaType")]
    pub captcha_type: String,
}

#[derive(Debug, Clone, Deserialize)]
pub struct UserSettings {
    pub password: PasswordSettings,
}

#[derive(Debug, Clone, Deserialize)]
pub struct PasswordSettings {
    #[serde(rename = "maxRetryCount")]
    pub max_retry_count: i32,
    #[serde(rename = "lockTime")]
    pub lock_time: i64,
}

#[derive(Debug, Clone, Deserialize)]
pub struct TokenSettings {
    pub header: String,
    pub secret: String,
    #[serde(rename = "expireTime")]
    pub expire_time: i64,
}

#[derive(Debug, Clone, Deserialize)]
pub struct DatabaseSettings {
    pub url: String,
    pub username: String,
    pub password: String,
    pub pool: PoolSettings,
}

#[derive(Debug, Clone, Deserialize)]
pub struct PoolSettings {
    #[serde(rename = "initialSize")]
    pub initial_size: u32,
    #[serde(rename = "minIdle")]
    pub min_idle: u32,
    #[serde(rename = "maxActive")]
    pub max_active: u32,
    #[serde(rename = "maxWait")]
    pub max_wait: u64,
    #[serde(rename = "connectTimeout")]
    pub connect_timeout: u64,
    #[serde(rename = "socketTimeout")]
    pub socket_timeout: u64,
}

#[derive(Debug, Clone, Deserialize)]
pub struct RedisSettings {
    pub host: String,
    pub port: u16,
    pub database: i64,
    pub password: String,
    pub timeout: String,
}

#[derive(Debug, Clone, Deserialize)]
pub struct KafkaSettings {
    pub bootstrap_servers: String,
    pub topic: KafkaTopicSettings,
    pub consumer: KafkaConsumerSettings,
    pub producer: KafkaProducerSettings,
}

#[derive(Debug, Clone, Deserialize)]
pub struct KafkaTopicSettings {
    #[serde(rename = "snapshot-flow")]
    pub snapshot_flow: String,
    #[serde(rename = "snapshot-flow-dlq")]
    pub snapshot_flow_dlq: String,
}

#[derive(Debug, Clone, Deserialize)]
pub struct KafkaConsumerSettings {
    #[serde(rename = "group-id")]
    pub group_id: String,
    pub concurrency: u32,
    #[serde(rename = "auto-offset-reset")]
    pub auto_offset_reset: String,
    #[serde(rename = "max-poll-records")]
    pub max_poll_records: u32,
}

#[derive(Debug, Clone, Deserialize)]
pub struct KafkaProducerSettings {
    pub acks: String,
    pub retries: u32,
}

#[derive(Debug, Clone, Deserialize)]
pub struct CdcSettings {
    pub kafka: CdcKafkaSettings,
    #[serde(rename = "es_sync")]
    pub es_sync: CdcEsSyncSettings,
    pub retry: CdcRetrySettings,
}

#[derive(Debug, Clone, Deserialize)]
pub struct CdcKafkaSettings {
    #[serde(rename = "bootstrap-servers")]
    pub bootstrap_servers: String,
    pub topic: String,
    #[serde(rename = "group-id")]
    pub group_id: String,
    pub concurrency: u32,
}

#[derive(Debug, Clone, Deserialize)]
pub struct CdcEsSyncSettings {
    pub enabled: bool,
}

#[derive(Debug, Clone, Deserialize)]
pub struct CdcRetrySettings {
    #[serde(rename = "max-retries")]
    pub max_retries: u32,
}

#[derive(Debug, Clone, Deserialize)]
pub struct ElasticsearchSettings {
    pub host: String,
    pub port: u16,
    pub index: String,
    pub enabled: bool,
}

#[derive(Debug, Clone, Deserialize)]
pub struct OssSettings {
    pub enable: bool,
    pub info: bool,
    pub endpoint: String,
    pub access_key: String,
    pub secret_key: String,
    pub bucket_name: String,
    /// Java: `OssProperties.region` —— yml 里没配时为 null，AWS SDK v1 落到 us-east-1。
    #[serde(default = "default_oss_region")]
    pub region: String,
    /// Java: `OssProperties.pathStyleAccess`（默认 true，即 `/{bucket}/{key}` 形式）。
    #[serde(default = "default_true", rename = "path_style_access")]
    pub path_style_access: bool,
}

fn default_oss_region() -> String {
    "us-east-1".to_string()
}

fn default_true() -> bool {
    true
}

#[derive(Debug, Clone, Deserialize)]
pub struct SmsSettings {
    pub signature: String,
    pub template: SmsTemplateSettings,
}

#[derive(Debug, Clone, Deserialize)]
pub struct SmsTemplateSettings {
    pub login: String,
    pub register: String,
}

#[derive(Debug, Clone, Deserialize)]
pub struct ForestSettings {
    #[serde(rename = "max-connections")]
    pub max_connections: u32,
    #[serde(rename = "connect-timeout")]
    pub connect_timeout: u64,
    #[serde(rename = "read-timeout")]
    pub read_timeout: u64,
    #[serde(rename = "retry-count")]
    pub retry_count: u32,
    pub variables: ForestVariables,
}

#[derive(Debug, Clone, Deserialize)]
pub struct ForestVariables {
    pub henda_url: String,
    /// Java: `#{roadPathUrl}` —— 本地路网规划服务（RoadPathApi 的 @BaseRequest）。
    #[serde(default)]
    pub road_path_url: String,
}

#[derive(Debug, Clone, Deserialize)]
pub struct HengdaSettings {
    pub appid: String,
    pub secret: String,
}

#[derive(Debug, Clone, Deserialize)]
pub struct VehicleMonitorSettings {
    /// Java: `#{vehicleMonitor.baseUrl}`。
    #[serde(rename = "baseUrl")]
    pub base_url: String,
}

#[derive(Debug, Clone, Deserialize)]
pub struct MonitorSettings {
    #[serde(rename = "slow-request-threshold")]
    pub slow_request_threshold: u64,
    #[serde(rename = "slow-method-threshold")]
    pub slow_method_threshold: u64,
    #[serde(rename = "slow-sql-threshold")]
    pub slow_sql_threshold: u64,
    #[serde(rename = "trace-header")]
    pub trace_header: String,
    pub enabled: bool,
}

#[derive(Debug, Clone, Deserialize)]
pub struct XssSettings {
    pub enabled: bool,
    #[serde(rename = "url-patterns")]
    pub url_patterns: String,
    pub excludes: String,
}

#[derive(Debug, Clone, Deserialize)]
pub struct UploadSettings {
    #[serde(rename = "max-file-size")]
    pub max_file_size: String,
    #[serde(rename = "max-request-size")]
    pub max_request_size: String,
}

#[derive(Debug, Clone, Deserialize)]
pub struct LogSettings {
    pub dir: String,
    #[serde(rename = "max-history")]
    pub max_history: u32,
    #[serde(rename = "max-file-size")]
    pub max_file_size: String,
}

#[derive(Debug, Clone, Deserialize)]
pub struct SnapshotSettings {
    pub flow: SnapshotFlowSettings,
}

#[derive(Debug, Clone, Deserialize)]
pub struct SnapshotFlowSettings {
    pub sharding: SnapshotShardingSettings,
}

#[derive(Debug, Clone, Deserialize)]
pub struct SnapshotShardingSettings {
    pub enabled: bool,
    #[serde(rename = "table-prefix")]
    pub table_prefix: String,
    #[serde(rename = "sharding-field")]
    pub sharding_field: String,
    #[serde(rename = "sharding-type")]
    pub sharding_type: String,
}

#[derive(Debug, Clone, Deserialize)]
pub struct ShardingSettings {
    pub enabled: bool,
}

#[derive(Debug, Clone, Deserialize)]
pub struct AppSettings {
    #[serde(rename = "health-endpoint-enabled")]
    pub health_endpoint_enabled: bool,
    #[serde(rename = "scheduler-enabled")]
    pub scheduler_enabled: bool,
    #[serde(rename = "scheduled-annotations-enabled")]
    pub scheduled_annotations_enabled: bool,
    #[serde(rename = "kafka-enabled")]
    pub kafka_enabled: bool,
    #[serde(rename = "elasticsearch-enabled")]
    pub elasticsearch_enabled: bool,
    #[serde(rename = "oss-enabled")]
    pub oss_enabled: bool,
    #[serde(rename = "banner-enabled")]
    pub banner_enabled: bool,
}

impl Settings {
    /// Java: Spring Boot 启动期加载 application.yml + application-{profile}.yml + 环境变量。
    pub fn load() -> anyhow::Result<Self> {
        let profile = env::var("APP_PROFILE").unwrap_or_else(|_| "default".to_string());
        let builder = Config::builder()
            // 先加载内嵌默认值，再让磁盘文件/profile/环境变量逐层覆盖。
            .add_source(File::from_str(DEFAULT_YAML, FileFormat::Yaml))
            .add_source(File::with_name("config/application").required(false))
            .add_source(File::with_name(&format!("config/application-{profile}")).required(false))
            .add_source(
                Environment::with_prefix("APP")
                    .prefix_separator("_")
                    .separator("__")
                    .try_parsing(true),
            );
        let settings: Settings = builder.build()?.try_deserialize()?;
        Ok(settings)
    }

    /// Java: `spring.datasource.druid.master.url` 是 `jdbc:mysql://...`；
    /// SQLx 只接受 `mysql://...`，这里剥离前缀与 JDBC 专用参数。
    pub fn mysql_endpoint(&self) -> anyhow::Result<(String, u16, String)> {
        let raw = self
            .database
            .url
            .strip_prefix("jdbc:mysql://")
            .unwrap_or(&self.database.url);
        let no_query = raw.split('?').next().unwrap_or(raw);
        let (host_port, db) = no_query
            .split_once('/')
            .ok_or_else(|| anyhow::anyhow!("database.url 缺少库名: {}", self.database.url))?;
        let (host, port) = match host_port.rsplit_once(':') {
            Some((h, p)) => (h.to_string(), p.parse::<u16>()?),
            None => (host_port.to_string(), 3306),
        };
        Ok((host, port, db.to_string()))
    }

    /// Java: JDBC 的 `serverTimezone` 决定驱动 `SET time_zone`，MySQL 的 `TIMESTAMP`
    /// 列按该时区读写；SQLx 默认强制 `+00:00`，不覆盖就会与 Java 差 8 小时
    /// （`car_*` 表的 `create_time` 全是 `timestamp(3)`）。
    /// 无法识别的写法（如 `Asia/Shanghai`）返回 `None`，沿用服务端默认时区。
    pub fn mysql_session_timezone(&self) -> Option<String> {
        jdbc_timezone(&self.database.url)
    }

    pub fn redis_url(&self) -> String {
        if self.redis.password.is_empty() {
            format!(
                "redis://{}:{}/{}",
                self.redis.host, self.redis.port, self.redis.database
            )
        } else {
            format!(
                "redis://:{}@{}:{}/{}",
                self.redis.password, self.redis.host, self.redis.port, self.redis.database
            )
        }
    }
}

/// 解析 JDBC URL 的 `serverTimezone`，转成 MySQL `SET time_zone` 接受的偏移量写法。
fn jdbc_timezone(url: &str) -> Option<String> {
    let query = url.split_once('?')?.1;
    let raw = query
        .split('&')
        .find_map(|pair| pair.strip_prefix("serverTimezone="))?;
    let text = raw.replace("%2B", "+").replace("%2b", "+");
    let upper = text.trim().to_ascii_uppercase();
    if upper == "UTC" || upper == "GMT" {
        return Some("+00:00".to_string());
    }
    let offset = upper.strip_prefix("GMT").unwrap_or(&upper);
    let (sign, digits) = offset.split_at(1);
    if sign != "+" && sign != "-" {
        return None;
    }
    let mut parts = digits.split(':');
    let hour: i32 = parts.next()?.parse().ok()?;
    let minute = parts.next().unwrap_or("0").parse::<i32>().ok()?;
    if parts.next().is_some() || !(0..15).contains(&hour) || !(0..60).contains(&minute) {
        return None;
    }
    Some(format!("{sign}{hour:02}:{minute:02}"))
}

#[cfg(test)]
mod tests {
    use super::jdbc_timezone;

    #[test]
    fn server_timezone_param_becomes_mysql_offset() {
        let cases = [
            (
                "jdbc:mysql://h:3307/d?a=1&serverTimezone=GMT%2B8",
                Some("+08:00"),
            ),
            ("jdbc:mysql://h:3307/d?serverTimezone=GMT+8", Some("+08:00")),
            (
                "jdbc:mysql://h:3307/d?serverTimezone=GMT+8:30",
                Some("+08:30"),
            ),
            ("jdbc:mysql://h:3307/d?serverTimezone=GMT-3", Some("-03:00")),
            (
                "jdbc:mysql://h:3307/d?serverTimezone=+08:00",
                Some("+08:00"),
            ),
            ("jdbc:mysql://h:3307/d?serverTimezone=UTC", Some("+00:00")),
            ("jdbc:mysql://h:3307/d?serverTimezone=GMT", Some("+00:00")),
            // 具名时区需要 mysql 的时区表，交给服务端默认。
            ("jdbc:mysql://h:3307/d?serverTimezone=Asia/Shanghai", None),
            ("jdbc:mysql://h:3307/d?serverTimezone=GMT+16", None),
            ("jdbc:mysql://h:3307/d", None),
        ];
        for (url, expected) in cases {
            assert_eq!(jdbc_timezone(url).as_deref(), expected, "{url}");
        }
    }
}
