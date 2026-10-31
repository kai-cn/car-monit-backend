// JAVA 对照: ruoyi-common/src/main/java/com/ruoyi/common/utils/IdempotentUtil.java:10-100
// 类/职责: 基于 Redis SETNX 的分布式幂等控制（Kafka 重复消费防护）
// 对应 Go 文件: internal/stream/idempotent/idempotent.go
//
// DIFF: Spring @Value 注入 prefix/expire-time；Go 由调用方传入（通常取 config.Idempotent.Redis）。
package idempotent

import (
	"context"
	"time"

	"github.com/redis/go-redis/v9"
)

type Util struct {
	rdb    *redis.Client
	prefix string
	ttl    time.Duration
}

func New(rdb *redis.Client, prefix string, expireSeconds int) *Util {
	if expireSeconds <= 0 {
		expireSeconds = 86400
	}
	return &Util{rdb: rdb, prefix: prefix, ttl: time.Duration(expireSeconds) * time.Second}
}

// CheckAndSet 对应 IdempotentUtil.checkAndSet：SETNX 成功表示“未处理，可继续”。
func (u *Util) CheckAndSet(ctx context.Context, key string) bool {
	ok, err := u.rdb.SetNX(ctx, u.prefix+key, "1", u.ttl).Result()
	return err == nil && ok
}

// IsProcessed 对应 IdempotentUtil.isProcessed。
func (u *Util) IsProcessed(ctx context.Context, key string) bool {
	n, err := u.rdb.Exists(ctx, u.prefix+key).Result()
	return err == nil && n > 0
}

// Remove 对应 IdempotentUtil.remove（处理失败时回滚标记）。
func (u *Util) Remove(ctx context.Context, key string) {
	u.rdb.Del(ctx, u.prefix+key)
}
