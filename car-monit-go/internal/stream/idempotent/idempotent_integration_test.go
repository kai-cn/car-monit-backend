// 类/职责: Kafka 幂等键的 Redis 集成测试（需真实 Redis，默认跳过）
// 运行方式: $env:CARMONIT_TEST_REDIS="1"; go test -run TestIdempotentWithRedis ./internal/stream/idempotent
package idempotent

import (
	"context"
	"fmt"
	"os"
	"testing"
	"time"

	"github.com/redis/go-redis/v9"
)

func TestIdempotentWithRedis(t *testing.T) {
	if os.Getenv("CARMONIT_TEST_REDIS") == "" {
		t.Skip("未设置 CARMONIT_TEST_REDIS=1，跳过真实 Redis 集成测试")
	}
	addr := os.Getenv("CARMONIT_TEST_REDIS_ADDR")
	if addr == "" {
		addr = "127.0.0.1:6379"
	}
	rdb := redis.NewClient(&redis.Options{Addr: addr, DB: 15})
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if err := rdb.Ping(ctx).Err(); err != nil {
		t.Skipf("Redis 不可用（%s）: %v", addr, err)
	}
	defer func() { _ = rdb.Close() }()

	util := New(rdb, "test:snapshot:idempotent_", 60)
	key := fmt.Sprintf("big-%d", time.Now().UnixNano())
	defer util.Remove(context.Background(), key)

	if !util.CheckAndSet(ctx, key) {
		t.Fatal("首次 CheckAndSet 应为 true")
	}
	if util.CheckAndSet(ctx, key) {
		t.Fatal("重复 CheckAndSet 应为 false")
	}
	if !util.IsProcessed(ctx, key) {
		t.Fatal("IsProcessed 应为 true")
	}
	util.Remove(ctx, key)
	if util.IsProcessed(ctx, key) {
		t.Fatal("Remove 后 IsProcessed 应为 false")
	}
}
