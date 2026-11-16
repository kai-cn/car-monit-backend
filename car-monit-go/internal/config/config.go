// JAVA 对照: ruoyi-admin/src/main/resources/application.yml + application-druid.yml
// 类/职责: 配置加载 — 对应 Spring 的 @ConfigurationProperties + @Value
// 对应 Go 文件: internal/config/config.go
// 关键映射: application.yml -> Viper(YAML) -> 结构体；@Profile -> 环境变量/--config
//
// DIFF: Java 用 Druid + P6Spy 数据源，Go 侧使用 database/sql 连接池（GORM）。
// DIFF: Java 的 lettuce pool 配置在 Go 中对应 go-redis 的 ConnPoolSize/MinIdleConns。
// DIFF: Spring 的 relaxed binding 由 Viper 的 mapstructure 弱匹配承担；环境变量前缀 CARMONIT_。
package config

import (
	"fmt"
	"os"
	"strconv"
	"strings"

	"github.com/spf13/viper"
)

// JAVA 对照: application.yml:1-12 (ruoyi.*)
type RuoYi struct {
	Name          string `mapstructure:"name"`
	Version       string `mapstructure:"version"`
	CopyrightYear int    `mapstructure:"copyrightYear"`
	Profile       string `mapstructure:"profile"`
	AddressEnable bool   `mapstructure:"addressEnabled"`
	CaptchaType   string `mapstructure:"captchaType"`
}

func (r RuoYi) ImportPath() string   { return r.Profile + "/import" }
func (r RuoYi) AvatarPath() string   { return r.Profile + "/avatar" }
func (r RuoYi) DownloadPath() string { return r.Profile + "/download/" }
func (r RuoYi) UploadPath() string   { return r.Profile + "/upload" }

// JAVA 对照: application.yml:15-33 (server.*)
type Server struct {
	Port        int    `mapstructure:"port"`
	ContextPath string `mapstructure:"context-path"`
	MaxThreads  int    `mapstructure:"max-threads"`
	MinSpare    int    `mapstructure:"min-spare"`
}

// JAVA 对照: application.yml:36-40 (logging.level)
// Level 使用 map[string]any：YAML 中 com.ruoyi 等键含点号，Viper 会解析成嵌套 map。
type Logging struct {
	Level map[string]any `mapstructure:"level"`
}

// JAVA 对照: application.yml:45-60 (monitor.*)
type Monitor struct {
	Enabled              bool   `mapstructure:"enabled"`
	SlowRequestThreshold int    `mapstructure:"slow-request-threshold"`
	SlowMethodThreshold  int    `mapstructure:"slow-method-threshold"`
	SlowSQLThreshold     int    `mapstructure:"slow-sql-threshold"`
	TraceIDHeader        string `mapstructure:"trace-id-header"`
	AlertWindowMS        int    `mapstructure:"alert-window-ms"`
	AlertMaxCount        int    `mapstructure:"alert-max-count"`
}

// JAVA 对照: application.yml:63-68 (user.password.*)
type UserCfg struct {
	MaxRetryCount int `mapstructure:"maxRetryCount"`
	LockTime      int `mapstructure:"lockTime"`
}

// JAVA 对照: application.yml:71-106 (spring.*)
type Spring struct {
	Profiles SpringProfiles `mapstructure:"profiles"`
	Redis    RedisCfg       `mapstructure:"redis"`
}

type SpringProfiles struct {
	Active string `mapstructure:"active"`
}

// JAVA 对照: application.yml:109-116 (token.*)
type Token struct {
	Header     string `mapstructure:"header"`
	Secret     string `mapstructure:"secret"`
	ExpireTime int    `mapstructure:"expireTime"`
}

// JAVA 对照: application.yml:457-490 (kafka.*)
type Kafka struct {
	BootstrapServers []string `mapstructure:"bootstrap-servers"`
	Topic            struct {
		SnapshotFlow    string `mapstructure:"snapshot-flow"`
		SnapshotFlowDLQ string `mapstructure:"snapshot-flow-dlq"`
	} `mapstructure:"topic"`
	Consumer struct {
		GroupID          string `mapstructure:"group-id"`
		AutoOffsetReset  string `mapstructure:"auto-offset-reset"`
		EnableAutoCommit bool   `mapstructure:"enable-auto-commit"`
		MaxPollRecords   int    `mapstructure:"max-poll-records"`
	} `mapstructure:"consumer"`
	Enabled bool `mapstructure:"enabled"`
}

// JAVA 对照: application.yml:492-498 (elasticsearch.*)
type Elasticsearch struct {
	Host  string `mapstructure:"host"`
	Port  int    `mapstructure:"port"`
	Index struct {
		SnapshotFlow string `mapstructure:"snapshot-flow"`
	} `mapstructure:"index"`
	Enabled bool `mapstructure:"enabled"`
}

// JAVA 对照: application.yml:500-505 (idempotent.redis.*)
type Idempotent struct {
	Redis IdempotentRedis `mapstructure:"redis"`
}

type IdempotentRedis struct {
	Prefix     string `mapstructure:"prefix"`
	ExpireTime int    `mapstructure:"expire-time"`
}

// JAVA 对照: application.yml:507-513 (snapshot.flow.sharding.*)
type SnapshotSharding struct {
	Enabled       bool   `mapstructure:"enabled"`
	TablePrefix   string `mapstructure:"table-prefix"`
	ShardingField string `mapstructure:"sharding-field"`
	ShardingType  string `mapstructure:"sharding-type"`
}

type Snapshot struct {
	Flow SnapshotSharding `mapstructure:"flow"`
}

// Go 原生配置：替代 application-druid.yml 中的 JDBC/Druid 连接池。
type Database struct {
	Master DatabaseNode `mapstructure:"master"`
	Slave  DatabaseNode `mapstructure:"slave"`
	Pool   PoolCfg      `mapstructure:"pool"`
}

type DatabaseNode struct {
	Enabled  bool   `mapstructure:"enabled"`
	DSN      string `mapstructure:"dsn"`
	Host     string `mapstructure:"host"`
	Port     int    `mapstructure:"port"`
	Username string `mapstructure:"username"`
	Password string `mapstructure:"password"`
}

type PoolCfg struct {
	MaxOpenConns    int `mapstructure:"max-open-conns"`
	MaxIdleConns    int `mapstructure:"max-idle-conns"`
	ConnMaxLifetime int `mapstructure:"conn-max-lifetime-seconds"`
	ConnMaxIdleTime int `mapstructure:"conn-max-idle-time-seconds"`
	SlowSQLMillis   int `mapstructure:"slow-sql-millis"`
}

// JAVA 对照: application.yml:86-106 (spring.redis.*)
type RedisCfg struct {
	Host         string `mapstructure:"host"`
	Port         int    `mapstructure:"port"`
	Password     string `mapstructure:"password"`
	Database     int    `mapstructure:"database"`
	Timeout      string `mapstructure:"timeout"`
	MinIdleConns int    `mapstructure:"min-idle"`
	MaxIdleConns int    `mapstructure:"max-idle"`
	MaxActive    int    `mapstructure:"max-active"`
}

func (r RedisCfg) Addr() string { return fmt.Sprintf("%s:%d", r.Host, r.Port) }

// JAVA 对照: application.yml (oss / sms / forest / hengda / vehicleMonitor / roadPathUrl / isLocalhost)
type Oss struct {
	Endpoint   string `mapstructure:"endpoint"`
	AccessKey  string `mapstructure:"accessKey"`
	SecretKey  string `mapstructure:"secretKey"`
	BucketName string `mapstructure:"bucketName"`
}

type Hengda struct {
	AppID  string `mapstructure:"appid"`
	Secret string `mapstructure:"secret"`
}

type Forest struct {
	HendaURL string `mapstructure:"hendaUrl"`
	Timeout  int    `mapstructure:"timeout"`
}

type VehicleMonitor struct {
	BaseURL string `mapstructure:"baseUrl"`
}

type Xss struct {
	Enabled     bool   `mapstructure:"enabled"`
	Excludes    string `mapstructure:"excludes"`
	URLPatterns string `mapstructure:"urlPatterns"`
}

// JAVA 对照: application.yml:144-146 (generator-code.mybatis-plus.enable)
// Go 侧决定代码生成器使用 vmplus/ 还是 vm/ 模板。
type GeneratorCode struct {
	MybatisPlus struct {
		Enable bool `mapstructure:"enable"`
	} `mapstructure:"mybatis-plus"`
}

// JAVA 对照: application.yml 全量顶层配置
type Config struct {
	RuoYi          RuoYi          `mapstructure:"ruoyi"`
	Server         Server         `mapstructure:"server"`
	Logging        Logging        `mapstructure:"logging"`
	Monitor        Monitor        `mapstructure:"monitor"`
	User           UserCfg        `mapstructure:"user"`
	Spring         Spring         `mapstructure:"spring"`
	Token          Token          `mapstructure:"token"`
	Kafka          Kafka          `mapstructure:"kafka"`
	Elasticsearch  Elasticsearch  `mapstructure:"elasticsearch"`
	Idempotent     Idempotent     `mapstructure:"idempotent"`
	Snapshot       Snapshot       `mapstructure:"snapshot"`
	Database       Database       `mapstructure:"database"`
	Redis          RedisCfg       `mapstructure:"redis"`
	Oss            Oss            `mapstructure:"oss"`
	Hengda         Hengda         `mapstructure:"hengda"`
	Forest         Forest         `mapstructure:"forest"`
	VehicleMonitor VehicleMonitor `mapstructure:"vehicleMonitor"`
	Xss            Xss            `mapstructure:"xss"`
	GeneratorCode  GeneratorCode  `mapstructure:"generator-code"`
	IsLocalhost    string         `mapstructure:"isLocalhost"`
	TxServiceURL   string         `mapstructure:"tx-service-url"`
	RoadPathURL    string         `mapstructure:"roadPathUrl"`
	ConfigFile     string         `mapstructure:"-"`
}

// LoadConfig 读取 YAML 并应用显式环境变量覆盖。
// JAVA 对照: Spring Boot 启动时 EnvironmentPostProcessor 加载 application.yml
func LoadConfig(path string) (*Config, error) {
	v := viper.New()
	v.SetConfigFile(path)
	v.SetConfigType("yaml")
	setDefaults(v)
	if err := v.ReadInConfig(); err != nil {
		return nil, fmt.Errorf("read config %s: %w", path, err)
	}
	var cfg Config
	if err := v.Unmarshal(&cfg); err != nil {
		return nil, fmt.Errorf("unmarshal config: %w", err)
	}
	applyEnvOverrides(&cfg)
	cfg.ConfigFile = path
	// JAVA 对照: application.yml 中 spring.redis 与顶层 token/user 同时存在；
	// Go 侧数据库与 Redis 使用独立顶层段，保持 Spring 段仅作兼容展示。
	if cfg.Database.Master.DSN == "" {
		cfg.Database.Master.DSN = buildDSN(cfg.Database.Master)
	}
	if err := validate(&cfg); err != nil {
		return nil, err
	}
	return &cfg, nil
}

func setDefaults(v *viper.Viper) {
	v.SetDefault("ruoyi.name", "系统")
	v.SetDefault("ruoyi.version", "3.8.7")
	v.SetDefault("ruoyi.copyrightYear", 2024)
	v.SetDefault("ruoyi.profile", "D:/ruoyi/uploadPath")
	v.SetDefault("ruoyi.captchaType", "math")
	v.SetDefault("server.port", 9989)
	v.SetDefault("server.context-path", "/")
	v.SetDefault("user.password.maxRetryCount", 5)
	v.SetDefault("user.password.lockTime", 10)
	v.SetDefault("token.header", "Authorization")
	// 生产通过 CARMONIT_TOKEN_SECRET 注入；不再内置默认密钥
	v.SetDefault("token.secret", "")
	v.SetDefault("token.expireTime", 120)
	v.SetDefault("user.password.maxRetryCount", 5)
	v.SetDefault("monitor.trace-id-header", "X-Trace-Id")
	v.SetDefault("monitor.slow-request-threshold", 3000)
	v.SetDefault("monitor.slow-sql-threshold", 1000)
	v.SetDefault("database.pool.max-open-conns", 200)
	v.SetDefault("database.pool.max-idle-conns", 10)
	v.SetDefault("database.pool.conn-max-lifetime-seconds", 900)
	v.SetDefault("database.pool.conn-max-idle-time-seconds", 300)
	v.SetDefault("database.pool.slow-sql-millis", 1000)
	v.SetDefault("redis.host", "127.0.0.1")
	v.SetDefault("redis.port", 6379)
	v.SetDefault("redis.database", 0)
	v.SetDefault("redis.timeout", "10s")
	v.SetDefault("redis.max-active", 8)
	v.SetDefault("redis.max-idle", 8)
	v.SetDefault("kafka.bootstrap-servers", []string{"127.0.0.1:9092"})
	v.SetDefault("kafka.topic.snapshot-flow", "ods-rt-szdn-snapshot-flow")
	v.SetDefault("kafka.topic.snapshot-flow-dlq", "ods-rt-szdn-snapshot-flow-dlq")
	v.SetDefault("kafka.consumer.group-id", "snapshot-flow-consumer-group")
	v.SetDefault("kafka.consumer.max-poll-records", 500)
	v.SetDefault("kafka.enabled", false)
	v.SetDefault("elasticsearch.host", "127.0.0.1")
	v.SetDefault("elasticsearch.port", 9200)
	v.SetDefault("elasticsearch.index.snapshot-flow", "snapshot-flow")
	v.SetDefault("elasticsearch.enabled", false)
	v.SetDefault("idempotent.redis.prefix", "snapshot:flow:idempotent_")
	v.SetDefault("idempotent.redis.expire-time", 86400)
	v.SetDefault("snapshot.flow.sharding.enabled", true)
	v.SetDefault("snapshot.flow.sharding.table-prefix", "ods_rt_szdn_snapshot_flow_")
	v.SetDefault("snapshot.flow.sharding.sharding-field", "snapshottime")
	v.SetDefault("snapshot.flow.sharding.sharding-type", "month")
	v.SetDefault("generator-code.mybatis-plus.enable", false)
}

// applyEnvOverrides 提供与 Spring Boot 等价的少量关键环境变量覆盖。
func applyEnvOverrides(c *Config) {
	if v := os.Getenv("CARMONIT_SERVER_PORT"); v != "" {
		if n, err := strconv.Atoi(v); err == nil {
			c.Server.Port = n
		}
	}
	if v := os.Getenv("CARMONIT_DATABASE_DSN"); v != "" {
		c.Database.Master.DSN = v
	}
	if v := os.Getenv("CARMONIT_REDIS_ADDR"); v != "" {
		host, port, ok := strings.Cut(v, ":")
		if ok {
			c.Redis.Host = host
			if n, err := strconv.Atoi(port); err == nil {
				c.Redis.Port = n
			}
		}
	}
	if v := os.Getenv("CARMONIT_REDIS_PASSWORD"); v != "" {
		c.Redis.Password = v
	}
	if v := os.Getenv("CARMONIT_TOKEN_SECRET"); v != "" {
		c.Token.Secret = v
	}
	if v := os.Getenv("CARMONIT_KAFKA_BOOTSTRAP_SERVERS"); v != "" {
		c.Kafka.BootstrapServers = strings.Split(v, ",")
	}
}

func buildDSN(n DatabaseNode) string {
	if n.Username == "" {
		return ""
	}
	host := n.Host
	if host == "" {
		host = "127.0.0.1"
	}
	port := n.Port
	if port == 0 {
		port = 3306
	}
	return fmt.Sprintf("%s:%s@tcp(%s:%d)/carmonitdb?charset=utf8mb4&parseTime=True&loc=Local&multiStatements=true",
		n.Username, n.Password, host, port)
}

func validate(c *Config) error {
	if c.Server.Port <= 0 || c.Server.Port > 65535 {
		return fmt.Errorf("server.port 非法: %d", c.Server.Port)
	}
	if c.Database.Master.DSN == "" {
		return fmt.Errorf("database.master.dsn 不能为空")
	}
	if c.Token.Secret == "" {
		return fmt.Errorf("token.secret 不能为空")
	}
	if c.Token.ExpireTime <= 0 {
		c.Token.ExpireTime = 120
	}
	return nil
}
