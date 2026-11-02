// JAVA 对照: ruoyi-framework/.../FastJson2JsonRedisSerializer.java（JSONWriter.Feature.WriteClassName）
// JAVA 对照: ruoyi-framework/.../RedisConfig.java（valueSerializer = FastJson2(Object.class)）
// 类/职责: 与 Java 共用 Redis 时的值编码/解码兼容层
// 对应 Go 文件: internal/cache/fastjson.go
//
// Java 的 redisTemplate 用 FastJson2 且开启 WriteClassName，写出的值不是标准 JSON：
//  1. 对象带 "@type":"com.ruoyi..."（Java 反序列化时靠它还原具体类，缺失即 ClassCastException）；
//  2. java.lang.Long 字段写成 25367L；
//  3. java.util.Set 写成 Set[...]；
//  4. Map 字段带 "@type":"java.util.HashMap"；
//  5. null 字段一律不写（fastjson2 默认行为）。
//
// ToJava 负责写出这种格式（Go 独有的缓存键也顺带对齐），FromJava 负责读回 Java 写的值。
package cache

import (
	"bytes"
	"encoding/json"
	"fmt"
	"sort"
	"strconv"
	"strings"
)

const hashMapType = "java.util.HashMap"

// JavaOptions 描述一次编码需要的类型信息，字段名均为 JSON 键名。
type JavaOptions struct {
	// RootType 根对象（或根数组每个元素）的 @type，空则不写。
	RootType string
	// Longs Java 侧声明为包装类型 Long 的键，整数输出补 L。
	Longs map[string]bool
	// Sets Java 侧为 Set 的键，数组输出为 Set[...]。
	Sets map[string]bool
	// Maps Java 侧为 Map/HashMap 的字段：一定写成 {"@type":"java.util.HashMap"}，
	// 对象里没有这个键时也会补上 —— fastjson2 对空 HashMap 同样写类型标记，
	// 少了它会让「谁先回填缓存」改变另一端读到的字段集合。
	Maps map[string]bool
}

type emitCtx struct {
	opts   *JavaOptions
	key    string // 当前值在父对象里的键名
	atRoot bool   // 当前值是整份缓存值的根
	isElem bool   // 当前值是根数组的元素
}

// ToJava 按 FastJson2 WriteClassName 规则编码。
func ToJava(v any, o JavaOptions) ([]byte, error) {
	raw, err := json.Marshal(v)
	if err != nil {
		return nil, err
	}
	dec := json.NewDecoder(bytes.NewReader(raw))
	dec.UseNumber()
	var tree any
	if err := dec.Decode(&tree); err != nil {
		return nil, fmt.Errorf("cache: 待写入值不是合法 JSON: %w", err)
	}
	var buf bytes.Buffer
	emitValue(&buf, tree, emitCtx{opts: &o, atRoot: true})
	return buf.Bytes(), nil
}

func emitValue(buf *bytes.Buffer, v any, ctx emitCtx) {
	switch x := v.(type) {
	case map[string]any:
		emitObject(buf, x, ctx)
	case []any:
		if ctx.opts != nil && ctx.opts.Sets[ctx.key] {
			buf.WriteString("Set")
		}
		buf.WriteByte('[')
		for i, item := range x {
			if i > 0 {
				buf.WriteByte(',')
			}
			// 根数组的每个元素同样带 @type（Java 的 List<X> 就是这样写的）
			emitValue(buf, item, emitCtx{opts: ctx.opts, key: ctx.key, isElem: ctx.atRoot})
		}
		buf.WriteByte(']')
	case json.Number:
		buf.WriteString(x.String())
		if ctx.opts != nil && ctx.opts.Longs[ctx.key] && isInteger(x.String()) {
			buf.WriteByte('L')
		}
	case string:
		writeJSONString(buf, x)
	case bool:
		if x {
			buf.WriteString("true")
		} else {
			buf.WriteString("false")
		}
	case nil:
		buf.WriteString("null")
	default:
		raw, _ := json.Marshal(x)
		buf.Write(raw)
	}
}

func emitObject(buf *bytes.Buffer, obj map[string]any, ctx emitCtx) {
	buf.WriteByte('{')
	written := 0
	if typeName := objectTypeName(ctx); typeName != "" {
		buf.WriteString(`"@type":`)
		writeJSONString(buf, typeName)
		written++
	}
	keys := make([]string, 0, len(obj))
	for k := range obj {
		if k != "@type" {
			keys = append(keys, k)
		}
	}
	sort.Strings(keys)
	for _, k := range keys {
		// fastjson2 默认不输出 null 成员
		if obj[k] == nil {
			continue
		}
		if written > 0 {
			buf.WriteByte(',')
		}
		writeJSONString(buf, k)
		buf.WriteByte(':')
		emitValue(buf, obj[k], emitCtx{opts: ctx.opts, key: k})
		written++
	}
	// Maps 声明的字段在嵌套对象里必须存在（Java 侧是初始化好的 new HashMap<>()）；
	// 根对象不补：LoginUser 自己就没有 params 字段。数组元素不算根，所以 sys_dict 的行会被补上。
	if ctx.opts != nil && !ctx.atRoot && !ctx.opts.Maps[ctx.key] {
		for _, k := range sortedKeys(ctx.opts.Maps) {
			if _, has := obj[k]; has {
				continue
			}
			if written > 0 {
				buf.WriteByte(',')
			}
			buf.WriteString(`"` + k + `":{"@type":"` + hashMapType + `"}`)
			written++
		}
	}
	buf.WriteByte('}')
}

func sortedKeys(set map[string]bool) []string {
	out := make([]string, 0, len(set))
	for k := range set {
		out = append(out, k)
	}
	sort.Strings(out)
	return out
}

func objectTypeName(ctx emitCtx) string {
	if ctx.opts == nil {
		return ""
	}
	if ctx.opts.Maps[ctx.key] {
		return hashMapType
	}
	if ctx.opts.RootType != "" && (ctx.atRoot || ctx.isElem) {
		return ctx.opts.RootType
	}
	return ""
}

func isInteger(s string) bool {
	if strings.ContainsAny(s, ".eE") {
		return false
	}
	_, err := strconv.ParseInt(s, 10, 64)
	return err == nil
}

func writeJSONString(buf *bytes.Buffer, s string) {
	raw, err := json.Marshal(s)
	if err != nil {
		buf.WriteString(`""`)
		return
	}
	buf.Write(raw)
}

// FromJava 把 Java 写的值还原成标准 JSON：去 Set[...] 前缀、去 Long 的 L 后缀。
//
// "@type" 成员**保留**：Go 的结构体解码本就忽略未知键，而 Java 把它读进
// BaseEntity.params（Map<String,Object>）后会原样带进 HTTP 响应
// （"params":{"@type":"java.util.HashMap"}），剥掉反而与 Java 不一致。
func FromJava(raw []byte) []byte {
	s := string(raw)
	var out bytes.Buffer
	out.Grow(len(s))
	for i := 0; i < len(s); {
		c := s[i]
		if c == '"' {
			j := skipString(s, i)
			out.WriteString(s[i:j])
			i = j
			continue
		}
		if end := typedCollectionEnd(s, i); end > i {
			out.WriteByte('[')
			i = end
			continue
		}
		if c == 'L' && out.Len() > 0 && isDigit(out.Bytes()[out.Len()-1]) {
			if j := skipSpace(s, i+1); j < len(s) && (s[j] == ',' || s[j] == '}' || s[j] == ']') {
				i = j
				continue
			}
		}
		out.WriteByte(c)
		i++
	}
	return out.Bytes()
}

// typedCollectionEnd 匹配 Java 的 Set[...] / LinkedHashSet[...] 这类字面量，
// 返回左方括号之后的下标；不匹配时返回 i。
func typedCollectionEnd(s string, i int) int {
	if i >= len(s) || !isIdentStart(s[i]) {
		return i
	}
	j := i
	for j < len(s) && (isIdentChar(s[j]) || s[j] == '.' || s[j] == '$') {
		j++
	}
	if j < len(s) && s[j] == '[' {
		return j + 1
	}
	return i
}

func skipString(s string, i int) int {
	i++ // 跳过左引号
	for i < len(s) {
		if s[i] == '\\' {
			i += 2
			continue
		}
		if s[i] == '"' {
			return i + 1
		}
		i++
	}
	return i
}

func skipSpace(s string, i int) int {
	for i < len(s) && (s[i] == ' ' || s[i] == '\t' || s[i] == '\r' || s[i] == '\n') {
		i++
	}
	return i
}

func isDigit(c byte) bool { return c >= '0' && c <= '9' }
func isIdentStart(c byte) bool {
	return c == '_' || (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z')
}
func isIdentChar(c byte) bool { return isIdentStart(c) || isDigit(c) }
