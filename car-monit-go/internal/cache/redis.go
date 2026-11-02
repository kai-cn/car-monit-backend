// JAVA 对照: com/ruoyi/common/core/redis/RedisCache.java
// JAVA 对照: ruoyi-framework/src/main/java/com/ruoyi/framework/config/RedisConfig.java
// 类/职责: Redis 缓存 — 对应 Spring RedisTemplate + FastJson2 序列化
// 对应 Go 文件: internal/cache/redis.go
//
// 迁移完成后 Go 是唯一常驻写入方，但比对阶段两端会同时挂在同一个 Redis 上，
// 因此共享键（login_tokens:*、car_list、sys_dict:* 等）一律用 fastjson.go 的兼容格式读写：
// Go 写的值 Java 的 getCacheObject/getCacheList 能直接反序列化，Java 写的值 Go 也读得回来。
package cache

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/redis/go-redis/v9"

	"car-monit-go/internal/config"
)

type Cache struct {
	rdb *redis.Client
}

func New(cfg *config.Config) (*Cache, error) {
	timeout, err := time.ParseDuration(cfg.Redis.Timeout)
	if err != nil {
		timeout = 10 * time.Second
	}
	rdb := redis.NewClient(&redis.Options{
		Addr:         cfg.Redis.Addr(),
		Password:     cfg.Redis.Password,
		DB:           cfg.Redis.Database,
		DialTimeout:  timeout,
		ReadTimeout:  timeout,
		WriteTimeout: timeout,
		PoolSize:     orDefault(cfg.Redis.MaxActive, 8),
		MinIdleConns: cfg.Redis.MinIdleConns,
	})
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if err := rdb.Ping(ctx).Err(); err != nil {
		return nil, fmt.Errorf("Redis 连接失败: %w", err)
	}
	return &Cache{rdb: rdb}, nil
}

func (c *Cache) Client() *redis.Client { return c.rdb }

func (c *Cache) Get(ctx context.Context, key string, dest any) bool {
	b, err := c.rdb.Get(ctx, key).Bytes()
	if err != nil {
		return false
	}
	return json.Unmarshal(FromJava(b), dest) == nil
}

func (c *Cache) GetString(ctx context.Context, key string) (string, bool) {
	s, err := c.rdb.Get(ctx, key).Result()
	if err != nil {
		return "", false
	}
	return s, true
}

func (c *Cache) Set(ctx context.Context, key string, value any, ttl time.Duration) error {
	b, err := json.Marshal(value)
	if err != nil {
		return err
	}
	return c.rdb.Set(ctx, key, b, ttl).Err()
}

func (c *Cache) SetString(ctx context.Context, key, value string, ttl time.Duration) error {
	return c.rdb.Set(ctx, key, value, ttl).Err()
}

// SetJava 以 FastJson2 WriteClassName 格式写入 —— 与 Java 共用的键必须走这里，
// 否则 Java 的 getCacheObject 反序列化出来是 JSONObject，强转业务类型即 ClassCastException。
func (c *Cache) SetJava(ctx context.Context, key string, value any, ttl time.Duration, o JavaOptions) error {
	b, err := ToJava(value, o)
	if err != nil {
		return err
	}
	return c.rdb.Set(ctx, key, b, ttl).Err()
}

// ListJava 对应 RedisCache#getCacheList：LRANGE 全量，逐个还原 FastJson2 文本。
// 键不存在或类型不是 List（section_list 由 Java 的定时任务写入，Go 只读）时返回 ok=false，
// 调用方回源查库。
func (c *Cache) ListJava(ctx context.Context, key string) ([]string, bool) {
	values, err := c.rdb.LRange(ctx, key, 0, -1).Result()
	if err != nil || len(values) == 0 {
		return nil, false
	}
	out := make([]string, 0, len(values))
	for _, raw := range values {
		out = append(out, string(FromJava([]byte(raw))))
	}
	return out, true
}

// SetJavaString 对应 setCacheObject(key, String)：FastJson2 会把字符串本身再包一层引号，
// Java 侧 getCacheObject 反序列化后才得到 String。
func (c *Cache) SetJavaString(ctx context.Context, key, value string, ttl time.Duration) error {
	b, err := json.Marshal(value)
	if err != nil {
		return err
	}
	return c.rdb.Set(ctx, key, b, ttl).Err()
}

// GetStringJava 读回 Java 写的字符串值（脱掉外层引号）；老 Go 写的裸文本原样返回。
func (c *Cache) GetStringJava(ctx context.Context, key string) (string, bool) {
	s, ok := c.GetString(ctx, key)
	if !ok {
		return "", false
	}
	var unquoted string
	if err := json.Unmarshal([]byte(s), &unquoted); err == nil {
		return unquoted, true
	}
	return s, true
}

func (c *Cache) Delete(ctx context.Context, keys ...string) {
	if len(keys) == 0 {
		return
	}
	c.rdb.Del(ctx, keys...)
}

func (c *Cache) HasKey(ctx context.Context, key string) bool {
	n, err := c.rdb.Exists(ctx, key).Result()
	return err == nil && n > 0
}

func (c *Cache) Keys(ctx context.Context, pattern string) []string {
	keys, err := c.rdb.Keys(ctx, pattern).Result()
	if err != nil {
		return nil
	}
	return keys
}

// Incr 自增并设置过期时间，对应 SysPasswordService 的密码重试计数。
func (c *Cache) Incr(ctx context.Context, key string, ttl time.Duration) (int64, error) {
	n, err := c.rdb.Incr(ctx, key).Result()
	if err != nil {
		return 0, err
	}
	if ttl > 0 {
		c.rdb.Expire(ctx, key, ttl)
	}
	return n, nil
}

// GetInt 读取整数计数，不存在时返回 0。
func (c *Cache) GetInt(ctx context.Context, key string) int {
	n, err := c.rdb.Get(ctx, key).Int()
	if err != nil {
		return 0
	}
	return n
}

func (c *Cache) Close() error { return c.rdb.Close() }

func orDefault(v, def int) int {
	if v > 0 {
		return v
	}
	return def
}
