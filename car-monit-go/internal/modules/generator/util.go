// JAVA 对照: com/ruoyi/common/utils/StringUtils.java（继承 org.apache.commons.lang3.StringUtils）
// JAVA 对照: org.apache.commons.lang3.StringUtils（capitalize / uncapitalize / substringBetween / split）
// 类/职责: Java 字符串语义工具（驼峰转换 / 忽略大小写包含 / Java 版 trim、split）
// 对应 Go 文件: internal/modules/generator/util.go
//
// DIFF: Java 的 String.length()/substring() 以 UTF-16 code unit 计数；这里按 rune 处理。
// 生成器模板里出现的非 ASCII 文本（中文列注释）都在 BMP 内，两种计数一致。
package generator

import (
	"fmt"
	"reflect"
	"regexp"
	"strconv"
	"strings"
)

// capitalize 对应 org.apache.commons.lang3.StringUtils.capitalize：
// 首字符大写，其余不变；空串返回空串。
func capitalize(s string) string {
	if s == "" {
		return s
	}
	runes := []rune(s)
	runes[0] = []rune(strings.ToUpper(string(runes[0])))[0]
	return string(runes)
}

// uncapitalize 对应 org.apache.commons.lang3.StringUtils.uncapitalize。
func uncapitalize(s string) string {
	if s == "" {
		return s
	}
	runes := []rune(s)
	runes[0] = []rune(strings.ToLower(string(runes[0])))[0]
	return string(runes)
}

// inStringIgnoreCase 对应 com.ruoyi.common.utils.StringUtils.inStringIgnoreCase：
// 候选值先 trim 再与 str 做 equalsIgnoreCase（str 本身不 trim）。
func inStringIgnoreCase(str string, candidates ...string) bool {
	for _, candidate := range candidates {
		if strings.EqualFold(str, strings.TrimSpace(candidate)) {
			return true
		}
	}
	return false
}

// toCamelCase 对应 RuoYi StringUtils.toCamelCase：
// 无下划线原样返回；否则整体小写并把下划线后的字符转大写（下划线丢弃）。
func toCamelCase(s string) string {
	if !strings.Contains(s, "_") {
		return s
	}
	s = strings.ToLower(s)
	var b strings.Builder
	upper := false
	for _, r := range s {
		if r == '_' {
			upper = true
			continue
		}
		if upper {
			b.WriteString(strings.ToUpper(string(r)))
			upper = false
			continue
		}
		b.WriteRune(r)
	}
	return b.String()
}

// convertToCamelCase 对应 RuoYi StringUtils.convertToCamelCase：
// 无下划线仅首字母大写；有下划线按 "_" 切分（丢弃空段），每段首字母大写、其余小写。
func convertToCamelCase(name string) string {
	if name == "" {
		return ""
	}
	if !strings.Contains(name, "_") {
		return strings.ToUpper(name[:1]) + name[1:]
	}
	var b strings.Builder
	for _, part := range splitJava(name, "_") {
		if part == "" {
			continue
		}
		b.WriteString(strings.ToUpper(part[:1]))
		b.WriteString(strings.ToLower(part[1:]))
	}
	return b.String()
}

// javaTrim 对应 Java String.trim：去掉首尾 <= U+0020 的字符（不是 Unicode 空白）。
func javaTrim(s string) string {
	return strings.TrimFunc(s, func(r rune) bool { return r <= ' ' })
}

// splitJava 复刻 Java String.split(regex)（limit=0）：保留中间空串、丢弃尾部空串。
func splitJava(s, sep string) []string {
	if !strings.Contains(s, sep) {
		return []string{s}
	}
	parts := strings.Split(s, sep)
	for len(parts) > 0 && parts[len(parts)-1] == "" {
		parts = parts[:len(parts)-1]
	}
	return parts
}

// splitJavaComma 对应 StringUtils.split(s, ",")：input 为 nil 时返回 nil。
func splitJavaComma(s *string) []string {
	if s == nil {
		return nil
	}
	return splitJava(*s, ",")
}

// javaSplitSpace 对应 GenTableColumn.readConverterExp 里的 remarks.split(" ")：
// 只按空格切分（不是任意空白），尾部空串丢弃。
func javaSplitSpace(s string) []string { return splitJava(s, " ") }

// substringBetween 对应 commons-lang3 StringUtils.substringBetween(str, open, close)：
// 取第一对 open/close 之间的内容；找不到返回 nil。
func substringBetween(s, open, close string) *string {
	start := strings.Index(s, open)
	if start == -1 {
		return nil
	}
	start += len(open)
	end := strings.Index(s[start:], close)
	if end == -1 {
		return nil
	}
	out := s[start : start+end]
	return &out
}

// replaceTextJava 对应 GenUtils.replaceText：
// RegExUtils.replaceAll(text, "(?:表|若依)", "")。
func replaceTextJava(text string) string {
	text = strings.ReplaceAll(text, "表", "")
	return strings.ReplaceAll(text, "若依", "")
}

// replaceFirstJava 对应 Java String.replaceFirst(regex, "")：
// 只替换第一处匹配（GenUtils.replaceFirst 先 startsWith 判定，命中位置在 0）。
func replaceFirstJava(text, pattern string) string {
	re, err := regexp.Compile(pattern)
	if err != nil {
		return strings.Replace(text, pattern, "", 1)
	}
	loc := re.FindStringIndex(text)
	if loc == nil {
		return text
	}
	return text[:loc[0]] + text[loc[1]:]
}

// toJavaString 对应 Java String.valueOf(Object)：null -> ""（拼接语境）、
// Boolean -> true/false、集合 -> [a, b]。
func toJavaString(value any) string {
	if value == nil || isUndefined(value) {
		return ""
	}
	switch v := value.(type) {
	case string:
		return v
	case *string:
		if v == nil {
			return ""
		}
		return *v
	case bool:
		if v {
			return "true"
		}
		return "false"
	case int:
		return strconv.Itoa(v)
	case int64:
		return strconv.FormatInt(v, 10)
	case int32:
		return strconv.FormatInt(int64(v), 10)
	case float64:
		return formatJavaDouble(v)
	case []string:
		return "[" + strings.Join(v, ", ") + "]"
	case []*GenTableColumn:
		parts := make([]string, 0, len(v))
		for _, item := range v {
			parts = append(parts, toJavaString(item))
		}
		return "[" + strings.Join(parts, ", ") + "]"
	}
	rv := reflect.ValueOf(value)
	if rv.Kind() == reflect.Slice || rv.Kind() == reflect.Array {
		parts := make([]string, 0, rv.Len())
		for i := 0; i < rv.Len(); i++ {
			parts = append(parts, toJavaString(rv.Index(i).Interface()))
		}
		return "[" + strings.Join(parts, ", ") + "]"
	}
	return fmt.Sprint(value)
}

func formatJavaDouble(v float64) string {
	s := strconv.FormatFloat(v, 'g', -1, 64)
	if !strings.ContainsAny(s, ".eE") {
		s += ".0"
	}
	return s
}

// intValue 把模板里的数值统一成 int64（布尔与字符串不算数值）。
func intValue(value any) (int64, bool) {
	switch v := value.(type) {
	case int:
		return int64(v), true
	case int32:
		return int64(v), true
	case int64:
		return v, true
	case float64:
		if v == float64(int64(v)) {
			return int64(v), true
		}
	}
	return 0, false
}
