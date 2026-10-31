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
