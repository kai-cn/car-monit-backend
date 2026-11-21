// JAVA 对照: com.baomidou.mybatisplus.core.toolkit.IdWorker
// 类/职责: 雪花 ID 生成器 —— 与 MyBatis-Plus IdWorker 的位宽一致（41 位毫秒 + 5 位机房 + 5 位机器 + 12 位序列）
// 对应 Go 文件: internal/idgen/idgen.go
//
// DIFF: MyBatis-Plus 的 IdWorker 从机器 MAC / 进程号推导 workerId；Go 侧改为显式配置
// （instance.worker-id / instance.datacenter-id 或 CARMONIT_WORKER_ID / CARMONIT_DATACENTER_ID），
// 未配置时按主机名哈希推导。多副本部署必须保证 (datacenterId, workerId) 组合唯一，
// 否则同一毫秒内会生成重复主键 —— 部署文档与启动日志都会显式提示。
package idgen

import (
	"fmt"
	"hash/fnv"
	"os"
	"strconv"
	"sync"
	"sync/atomic"
	"time"
)

const (
	// epoch 与 MyBatis-Plus / Twitter Snowflake 的起始纪元一致。
	epoch = int64(1288834974657)

	workerIDBits     = 5
	datacenterIDBits = 5
	sequenceBits     = 12

	maxWorkerID     = int64(-1 ^ (-1 << workerIDBits))     // 31
	maxDatacenterID = int64(-1 ^ (-1 << datacenterIDBits)) // 31
	sequenceMask    = int64(-1 ^ (-1 << sequenceBits))     // 4095

	workerIDShift     = sequenceBits                                   // 12
	datacenterIDShift = sequenceBits + workerIDBits                    // 17
	timestampShift    = sequenceBits + workerIDBits + datacenterIDBits // 22
)

// Generator 是单个 (datacenterID, workerID) 组合下的雪花生成器。
type Generator struct {
	mu sync.Mutex

	workerID     int64
	datacenterID int64

	lastMillis int64
	sequence   int64
}

// New 校验取值范围后构造生成器。
func New(workerID, datacenterID int64) (*Generator, error) {
	if workerID < 0 || workerID > maxWorkerID {
		return nil, fmt.Errorf("instance.worker-id 必须在 0~%d 之间，当前 %d", maxWorkerID, workerID)
	}
	if datacenterID < 0 || datacenterID > maxDatacenterID {
		return nil, fmt.Errorf("instance.datacenter-id 必须在 0~%d 之间，当前 %d", maxDatacenterID, datacenterID)
	}
	return &Generator{workerID: workerID, datacenterID: datacenterID, lastMillis: -1}, nil
}

// NextInt64 生成下一个雪花 ID。
func (g *Generator) NextInt64() int64 {
	g.mu.Lock()
	defer g.mu.Unlock()

	now := time.Now().UnixMilli()
	// 时钟回拨：沿用上一次时间戳，保证单实例内单调不降。
	if now < g.lastMillis {
		now = g.lastMillis
	}
	if now == g.lastMillis {
		g.sequence = (g.sequence + 1) & sequenceMask
		if g.sequence == 0 {
			for now <= g.lastMillis {
				now = time.Now().UnixMilli()
			}
		}
	} else {
		g.sequence = 0
	}
	g.lastMillis = now
	return ((now - epoch) << timestampShift) | (g.datacenterID << datacenterIDShift) |
		(g.workerID << workerIDShift) | g.sequence
}

// NextString 返回 19 位十进制字符串（对应 Java 的 String.valueOf(nextId())）。
func (g *Generator) NextString() string { return strconv.FormatInt(g.NextInt64(), 10) }

// IDs 返回当前生效的 (workerId, datacenterId)，便于启动日志输出。
func (g *Generator) IDs() (workerID, datacenterID int64) {
	return g.workerID, g.datacenterID
}

var defaultGen atomic.Pointer[Generator]

// Init 初始化进程级生成器。两个参数传 -1 表示按主机名自动推导 workerId（datacenterId 固定 0）。
//
// 返回值 source 说明取值来源（"config"/"env"/"hostname"），供启动日志与排障使用。
func Init(workerID, datacenterID int64) (source string, err error) {
	source = "config"
	if workerID < 0 {
		workerID = hostnameWorkerID()
		source = "hostname"
	}
	if datacenterID < 0 {
		datacenterID = 0
	}
	g, err := New(workerID, datacenterID)
	if err != nil {
		return "", err
	}
	defaultGen.Store(g)
	return source, nil
}

// NextInt64 使用进程级生成器；未显式 Init 时按主机名懒初始化，保证不会返回 0 或 panic。
func NextInt64() int64 { return current().NextInt64() }

// NextString 使用进程级生成器。
func NextString() string { return current().NextString() }

// IDs 返回进程级生成器当前的 (workerId, datacenterId)。
func IDs() (workerID, datacenterID int64) { return current().IDs() }

func current() *Generator {
	if g := defaultGen.Load(); g != nil {
		return g
	}
	// 未显式初始化（例如单测直接调用）时按主机名推导，避免 nil panic。
	if _, err := Init(-1, -1); err != nil {
		g, _ := New(0, 0)
		defaultGen.CompareAndSwap(nil, g)
	}
	return defaultGen.Load()
}

// hostnameWorkerID 用主机名哈希取低 5 位。K8s Pod 名/容器主机名通常唯一，
// 因此多副本在未显式配置时也能获得较大概率的唯一 workerId；但仍建议显式配置。
func hostnameWorkerID() int64 {
	host, err := os.Hostname()
	if err != nil || host == "" {
		return 0
	}
	h := fnv.New32a()
	_, _ = h.Write([]byte(host))
	return int64(h.Sum32() & uint32(maxWorkerID))
}
