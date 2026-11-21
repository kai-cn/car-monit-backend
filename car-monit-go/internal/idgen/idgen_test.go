package idgen

import (
	"strconv"
	"sync"
	"testing"
)

func TestNewRejectsOutOfRange(t *testing.T) {
	cases := []struct{ worker, datacenter int64 }{
		{-1, 0}, {32, 0}, {0, -1}, {0, 32},
	}
	for _, c := range cases {
		if _, err := New(c.worker, c.datacenter); err == nil {
			t.Fatalf("New(%d,%d) 应报错", c.worker, c.datacenter)
		}
	}
	if _, err := New(0, 0); err != nil {
		t.Fatalf("New(0,0) 不应报错: %v", err)
	}
}

// 不同 (datacenterId, workerId) 在同一毫秒内必须生成不同 ID —— 这是多副本不碰撞的核心保证。
func TestDifferentWorkersDoNotCollide(t *testing.T) {
	a, err := New(1, 0)
	if err != nil {
		t.Fatal(err)
	}
	b, err := New(2, 0)
	if err != nil {
		t.Fatal(err)
	}
	seen := make(map[int64]string, 2000)
	for i := 0; i < 1000; i++ {
		ida, idb := a.NextInt64(), b.NextInt64()
		if ida == idb {
			t.Fatalf("第 %d 次生成碰撞: %d", i, ida)
		}
		for _, id := range []int64{ida, idb} {
			if prev, ok := seen[id]; ok {
				t.Fatalf("重复 ID %d（来源 %s 与当前）", id, prev)
			}
			seen[id] = "gen"
		}
	}
}

// 单实例并发调用不重复，且保持 19 位十进制字符串。
func TestNextStringConcurrentUnique(t *testing.T) {
	g, err := New(3, 4)
	if err != nil {
		t.Fatal(err)
	}
	const workers, perWorker = 8, 500
	ch := make(chan string, workers*perWorker)
	var wg sync.WaitGroup
	for i := 0; i < workers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for j := 0; j < perWorker; j++ {
				ch <- g.NextString()
			}
		}()
	}
	wg.Wait()
	close(ch)

	seen := make(map[string]struct{}, workers*perWorker)
	for id := range ch {
		if len(id) != 19 {
			t.Fatalf("ID 长度应为 19，实际 %d: %s", len(id), id)
		}
		if _, err := strconv.ParseInt(id, 10, 64); err != nil {
			t.Fatalf("ID 不是十进制整数: %s", id)
		}
		if _, ok := seen[id]; ok {
			t.Fatalf("并发下生成重复 ID: %s", id)
		}
		seen[id] = struct{}{}
	}
}

func TestInitWithAutoWorker(t *testing.T) {
	source, err := Init(-1, -1)
	if err != nil {
		t.Fatalf("Init(-1,-1) 失败: %v", err)
	}
	if source != "hostname" {
		t.Fatalf("自动推导时 source 应为 hostname，实际 %s", source)
	}
	w, d := IDs()
	if w < 0 || w > maxWorkerID || d < 0 || d > maxDatacenterID {
		t.Fatalf("自动推导的实例标识越界: worker=%d datacenter=%d", w, d)
	}
	if NextInt64() <= 0 {
		t.Fatal("NextInt64 应返回正数")
	}
}
