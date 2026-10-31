// JAVA 对照: com/ruoyi/common/core/redis/RedisCache.java
// JAVA 对照: ruoyi-framework/src/main/java/com/ruoyi/framework/config/RedisConfig.java
// 类/职责: Redis 缓存 — 对应 Spring RedisTemplate + FastJson2 序列化
// 对应 Go 文件: internal/cache/redis.go
//
// DIFF: Java 的 FastJson2 序列化带类型信息；Go 侧统一 JSON。若与 Java 进程共用 Redis，
// 登录态缓存不可互读（本项目迁移后 Java 进程下线，无需兼容）。
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
	return json.Unmarshal(b, dest) == nil
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
