// JAVA 对照: com/ruoyi/common/core/domain/AjaxResult.java:14
// 类/职责: AjaxResult 继承 HashMap<String,Object>，Jackson 按 HashMap 桶序输出键
// 对应 Go 文件: internal/web/javamap.go
//
// DIFF: Go 的 map 序列化按字典序，无法表达 Java HashMap 的桶序。
// 这里实现 JavaMap：按 Java 8 HashMap（capacity=16 起步、hash 扰动）桶序序列化，
// 保证 {"msg":...,"code":...,"data":...} 与 Java 侧字节顺序一致。
//
// 退役计划（Java 下线后）：本文件只为“双端逐字节对拍”存在，前端并不依赖键序。
// Java 服务退役后应删除本文件，把 AjaxResult 改为普通 struct（code/msg/data 字段序固定）。
package web

import (
	"bytes"
	"encoding/json"
	"sort"
)

type kv struct {
	key   string
	value any
	order int
}

// JavaMap 模拟 Java HashMap 的序列化顺序。
type JavaMap struct {
	entries []kv
	index   map[string]int
}

func NewJavaMap() *JavaMap {
	return &JavaMap{index: make(map[string]int)}
}

// Put 对应 HashMap.put；重复键只更新值，不改变插入位置。
func (m *JavaMap) Put(key string, value any) *JavaMap {
	if i, ok := m.index[key]; ok {
		m.entries[i].value = value
		return m
	}
	m.index[key] = len(m.entries)
	m.entries = append(m.entries, kv{key: key, value: value, order: len(m.entries)})
	return m
}

func (m *JavaMap) Get(key string) (any, bool) {
	if i, ok := m.index[key]; ok {
		return m.entries[i].value, true
	}
	return nil, false
}

func (m *JavaMap) Remove(key string) {
	i, ok := m.index[key]
	if !ok {
		return
	}
	m.entries = append(m.entries[:i], m.entries[i+1:]...)
	delete(m.index, key)
	for j := range m.entries {
		m.index[m.entries[j].key] = j
	}
}

func (m *JavaMap) Len() int { return len(m.entries) }

// MarshalJSON 按 Java HashMap 桶序输出。桶内保持插入顺序（JDK8 链表尾插）。
func (m *JavaMap) MarshalJSON() ([]byte, error) {
	cap := javaCapacity(len(m.entries))
	ordered := make([]kv, len(m.entries))
	copy(ordered, m.entries)
	sort.SliceStable(ordered, func(i, j int) bool {
		return javaBucket(ordered[i].key, cap) < javaBucket(ordered[j].key, cap)
	})

	var buf bytes.Buffer
	buf.WriteByte('{')
	for i, e := range ordered {
		if i > 0 {
			buf.WriteByte(',')
		}
		k, _ := json.Marshal(e.key)
		buf.Write(k)
		buf.WriteByte(':')
		v, err := json.Marshal(e.value)
		if err != nil {
			return nil, err
		}
		buf.Write(v)
	}
	buf.WriteByte('}')
	return buf.Bytes(), nil
}

// javaCapacity 复刻 HashMap 的容量扩张：默认 16，负载因子 0.75。
func javaCapacity(n int) int {
	cap := 16
	for n > cap*3/4 {
		cap <<= 1
	}
	return cap
}

func javaBucket(key string, capacity int) int {
	return int(spread(javaHash(key)) & int32(capacity-1))
}

func javaHash(s string) int32 {
	var h int32
	for _, r := range s {
		// Java 使用 UTF-16 code unit；BMP 字符与 rune 一致。
		if r > 0xFFFF {
			r -= 0x10000
			hi := 0xD800 + (r >> 10)
			lo := 0xDC00 + (r & 0x3FF)
			h = 31*h + hi
			h = 31*h + lo
			continue
		}
		h = 31*h + r
	}
	return h
}

func spread(h int32) int32 {
	return h ^ int32(uint32(h)>>16)
}
