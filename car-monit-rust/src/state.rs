// 来源: Spring 容器装配（DataSource / RedisTemplate / TokenService）
// 职责: 进程级共享状态，等价于 Java 的单例 Bean 集合。
// 对应关系: DataSource -> MySqlPool；RedisTemplate -> RedisCache；TokenService -> JwtService。

use std::sync::Arc;
use std::time::Duration;

use sqlx::mysql::MySqlPoolOptions;
use sqlx::MySqlPool;

use crate::auth::jwt::JwtService;
use crate::common::snowflake::SnowflakeIdWorker;
use crate::config::Settings;
use crate::db::sharding::ShardingRouter;
use crate::db::RedisCache;
use crate::error::AppError;

#[derive(Clone)]
pub struct AppState {
    pub settings: Arc<Settings>,
    pub db: MySqlPool,
    pub redis: RedisCache,
    pub jwt: Arc<JwtService>,
    pub snowflake: Arc<SnowflakeIdWorker>,
    pub sharding: Arc<ShardingRouter>,
    /// Java: Forest 全局 HTTP 客户端（连接数/超时取自 forest.*）。
    pub http: reqwest::Client,
}

impl AppState {
    pub async fn connect(settings: Settings) -> anyhow::Result<Self> {
        let settings = Arc::new(settings);

        let (host, port, db) = settings.mysql_endpoint()?;
        let mut url = url::Url::parse(&format!("mysql://{host}:{port}/{db}"))?;
        url.set_username(&settings.database.username)
            .map_err(|_| anyhow::anyhow!("database.username 非法"))?;
        url.set_password(Some(&settings.database.password))
            .map_err(|_| anyhow::anyhow!("database.password 非法"))?;

        // Java: Druid/JDBC 用 URL 上的 `serverTimezone=GMT+8` 设置会话时区；
        // SQLx 默认写死 `+00:00`，会让 `timestamp(3)` 列（car_* 全表）读写差 8 小时。
        let mut connect_options: sqlx::mysql::MySqlConnectOptions = url.as_str().parse()?;
        if let Some(timezone) = settings.mysql_session_timezone() {
            connect_options = connect_options.timezone(timezone);
        }

        let pool = MySqlPoolOptions::new()
            .max_connections(settings.database.pool.max_active)
            .min_connections(settings.database.pool.min_idle)
            .acquire_timeout(Duration::from_millis(settings.database.pool.max_wait))
            .connect_with(connect_options)
            .await?;

        let redis = RedisCache::connect(&settings.redis_url()).await?;
        let jwt = Arc::new(JwtService::new(&settings.token.secret)?);
        // Java: IdWorkerConfig.snowflakeIdWorker() —— 单例 new SnowflakeIdWorker(0, 0)
        let snowflake = Arc::new(SnowflakeIdWorker::new(0, 0)?);
        let sharding = Arc::new(ShardingRouter::from_settings(&settings));

        // Java: Forest 通过 `forest.*` 配置连接池与超时；reqwest 侧做等价映射。
        let http = reqwest::Client::builder()
            .pool_max_idle_per_host(settings.forest.max_connections as usize)
            .connect_timeout(Duration::from_millis(settings.forest.connect_timeout))
            .timeout(Duration::from_millis(settings.forest.read_timeout))
            .build()?;

        Ok(Self {
            settings,
            db: pool,
            redis,
            jwt,
            snowflake,
            sharding,
            http,
        })
    }

    /// 单次探活，供 /health 使用。
    pub async fn check_health(&self) -> Result<(), AppError> {
        sqlx::query("select 1").execute(&self.db).await?;
        Ok(())
    }
}
