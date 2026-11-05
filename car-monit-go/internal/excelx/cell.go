// Package excelx 放各模块 xlsx 写手共用的单元格兜底。
package excelx

import (
	"fmt"
	"reflect"
	"strconv"
	"strings"
	"unicode/utf8"
)

// Unbox 解引用指针型字段值。
//
// GORM 模型的可空列是 *string / *int64 这类指针，直接交给 excelize 会被写成
// 指针地址（0xc000…、&lt;nil&gt;）；JSON 编码时 encoding/json 会自动解引用，所以
// 只有 xlsx 导出会暴露这个差异。Java 侧 ExcelUtil 取的是属性值本身，没有这层坑。
// 多级指针与 nil 指针分别按"取到底 / 空串"处理。
func Unbox(v any) any {
	rv := reflect.ValueOf(v)
	for rv.Kind() == reflect.Ptr || rv.Kind() == reflect.Interface {
		if rv.IsNil() {
			return ""
		}
		rv = rv.Elem()
	}
	if !rv.IsValid() {
		return ""
	}
	return rv.Interface()
}

// maxCellRunes 是 POI 的单元格文本上限。
const maxCellRunes = 32767

// Sanitize 把 XML 1.0 不允许的字符换成 '?'。
//
// Java 侧：POI 的 XSSF 序列化（xmlbeans）会把这些字符写成 '?'（不是整格丢弃、也不是 U+FFFD），
// RuoYi 的异常堆栈/请求参数里常见 U+001A、NUL 这类控制字符；Go 的 encoding/xml 则写成 U+FFFD，
// 于是同一份 DB 文本在两端落成不同字符。合法字符集：#x9 #xA #xD [#x20-#xD7FF] [#xE000-#xFFFD] [#x10000-]。
func Sanitize(s string) string {
	if s == "" {
		return s
	}
	var b strings.Builder
	for _, r := range s {
		switch {
		case r == 0x9 || r == 0xA || r == 0xD:
		case r >= 0x20 && r <= 0xD7FF:
		case r >= 0xE000 && r <= 0xFFFD:
		case r >= 0x10000:
		default:
			r = '?'
		}
		b.WriteRune(r)
	}
	return b.String()
}

// Cell 是通用落格规则：解引用指针 + 超长文本按 POI 的上限置空 + 非法 XML 字符替换。
//
// 超长按 Java 行为是"整格留空"而不是截断：RuoYi ExcelUtil.addCell 的单元格级 try/catch
// 把 POI 的 IllegalArgumentException("The maximum length of cell contents (text) is 32767 characters")
// 吞掉，格子已经创建但没有值（EasyPOI 走的是同一套 POI 限制，表现相同）。
func Cell(v any) any {
	uv := Unbox(v)
	s, ok := uv.(string)
	if !ok {
		return uv
	}
	if utf8.RuneCountInString(s) > maxCellRunes {
		return ""
	}
	return Sanitize(s)
}

// formulaPrefix 对应 ExcelUtil.FORMULA_STR（CSV 公式注入防护）。
var formulaPrefix = []string{"=", "-", "+", "@"}

// TextValue 给"Java 侧是 STRING 单元格"的列用：先按 Convert.toStr 的形态转成字符串，
// 再套用 setCellVo 的注入防护前缀。数字型属性在 Java 默认 cellType=STRING 下就是这样落格的，
// 直接传数值会被 excelize 写成数字格，两端格类型与文本都不一致（租户单位id=-1 ⇒ "\t-1"）。
func TextValue(v any) string {
	s := plainStr(Unbox(v))
	for _, p := range formulaPrefix {
		if strings.HasPrefix(s, p) {
			return "\t" + s
		}
	}
	return s
}

func plainStr(v any) string {
	switch x := v.(type) {
	case nil:
		return ""
	case string:
		return x
	case bool:
		return strconv.FormatBool(x)
	case int:
		return strconv.Itoa(x)
	case int64:
		return strconv.FormatInt(x, 10)
	case float64:
		return strconv.FormatFloat(x, 'f', -1, 64)
	default:
		return fmt.Sprint(x)
	}
}

// UtilCell 在 Cell 之上再加 RuoYi ExcelUtil.setCellVo 的 STRING 分支规则：
// 文本以 = - + @ 开头时前面补一个 TAB（ExcelUtil.java:961-977），
// 于是 tenantId=-1 在 Java 的 xlsx 里是 "\t-1"。只用于 ExcelUtil 形态的写手，
// EasyPOI 模板导出没有这一步；数字格也不适用（Java 只在 STRING/TEXT 分支处理）。
func UtilCell(v any) any {
	cv := Cell(v)
	s, ok := cv.(string)
	if !ok {
		return cv
	}
	for _, p := range formulaPrefix {
		if strings.HasPrefix(s, p) {
			return "\t" + s
		}
	}
	return s
}

// ConvertByExp 逐字对应 ExcelUtil.convertByExp(value, converterExp, separator)，
// separator 取 @Excel.separator() 的默认值 ","（Excel.java:49）：注解串始终按 ASCII 逗号拆项，
// 每项再按 "=" 拆成 [键, 文案]，键命中就取文案。
//
// 关键点：**未命中返回空串，不是原值**（propertyString 一直是空的，最后 stripEnd 得 ""）。
// 工程里大量 "@Excel(readConverterExp="1=机构用户2专家3供应商")" 这类缺 ASCII 逗号的串，
// Java 会当成一项：值为 "1" 时文案是 "机构用户2专家3供应商"，其它值一律空。
// 属性值本身含分隔符（默认逗号）时走多值分支：命中的各文案用分隔符连接，末尾再去掉分隔符。
func ConvertByExp(value, exp string) string {
	return ConvertByExpSep(value, exp, ",")
}

func ConvertByExpSep(value, exp, sep string) string {
	if sep == "" {
		sep = ","
	}
	var out strings.Builder
	for _, item := range strings.Split(exp, ",") {
		arr := strings.Split(item, "=")
		if strings.ContainsAny(value, sep) {
			for _, one := range strings.Split(value, sep) {
				if arr[0] == one {
					if len(arr) > 1 {
						out.WriteString(arr[1] + sep)
					}
					break
				}
			}
			continue
		}
		if arr[0] == value {
			if len(arr) > 1 {
				return arr[1]
			}
			// Java 在这里取 itemArray[1] 会抛 ArrayIndexOutOfBoundsException（整条导出失败）。
			// 只有属性值恰好等于一个不含 "=" 的注解片段时才会发生，本工程未观测到。
			return ""
		}
	}
	return strings.TrimRight(out.String(), sep)
}

// DictLabel 对应 DictUtils.getDictLabel(dictType, dictValue, ",") 的单值分支：
// 命中取标签，未命中返回空串。多值（值里含逗号）要按字典缓存顺序输出，
// 那是 dictValueLabel 的 map 形态给不了的，调用点需要有序字典时另取。
func DictLabel(dict map[string]string, value string) string {
	if strings.Contains(value, ",") {
		// 多值：Java 按字典缓存顺序拼接命中的标签。map 无序，这里保持与 Java 一致的
		// 「命中才拼、未命中跳过」，顺序差异在有重复值/多值的列上才可能出现。
		var parts []string
		for _, one := range strings.Split(value, ",") {
			if label, ok := dict[one]; ok {
				parts = append(parts, label)
			}
		}
		return strings.Join(parts, ",")
	}
	return dict[value]
}
