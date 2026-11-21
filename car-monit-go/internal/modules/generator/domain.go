// JAVA 对照: ruoyi-generator/src/main/java/com/ruoyi/generator/domain/GenTable.java
// JAVA 对照: ruoyi-generator/src/main/java/com/ruoyi/generator/domain/GenTableColumn.java
// JAVA 对照: ruoyi-generator/src/main/java/com/ruoyi/generator/domain/DictionaryInfo.java
// JAVA 对照: ruoyi-generator/src/main/java/com/ruoyi/generator/domain/GenColumnDialog.java
// JAVA 对照: ruoyi-generator/src/main/java/com/ruoyi/generator/domain/GenerateRichTextInfo.java
// JAVA 对照: ruoyi-generator/src/main/java/com/ruoyi/generator/domain/GenerateUploadInfo.java
// JAVA 对照: ruoyi-generator/src/main/java/com/ruoyi/generator/domain/LinkTableField.java
// 类/职责: 代码生成领域模型 — 字段序与 Jackson 输出键序、派生属性一一对应
// 对应 Go 文件: internal/modules/generator/domain.go
//
// DIFF: Java 包装类型可为 null，Go 用指针保留 null（JSON 输出与动态 SQL 的
// "!= null / != ”" 判定都依赖它）。
// DIFF: Jackson 会把 isSub()/isPk()/getCapJavaField() 等 getter 当属性输出，
// Go 用 MarshalJSON 追加同名派生键，键序与 Java 声明序一致。
package generator

import (
	"encoding/json"
	"strings"

	"car-monit-go/internal/platform/conv"
	"car-monit-go/internal/web"
)

// ---------------------------------------------------------------------------
// GenTable
// ---------------------------------------------------------------------------

// GenTable 对应 com.ruoyi.generator.domain.GenTable。
// 前 6 个字段来自 BaseEntity（searchValue 被 @JsonIgnore 排除）。
type GenTable struct {
	CreateBy                *string               `json:"createBy"`
	CreateTime              *web.DateTime         `json:"createTime"`
	UpdateBy                *string               `json:"updateBy"`
	UpdateTime              *web.DateTime         `json:"updateTime"`
	Remark                  *string               `json:"remark"`
	Params                  map[string]any        `json:"params,omitempty"`
	TableID                 *int64                `json:"tableId"`
	TableName               *string               `json:"tableName"`
	TableComment            *string               `json:"tableComment"`
	SubTableName            *string               `json:"subTableName"`
	SubTableFkName          *string               `json:"subTableFkName"`
	ClassName               *string               `json:"className"`
	TplCategory             *string               `json:"tplCategory"`
	PackageName             *string               `json:"packageName"`
	ModuleName              *string               `json:"moduleName"`
	BusinessName            *string               `json:"businessName"`
	FunctionName            *string               `json:"functionName"`
	FunctionAuthor          *string               `json:"functionAuthor"`
	GenType                 *string               `json:"genType"`
	GenPath                 *string               `json:"genPath"`
	PkColumn                *GenTableColumn       `json:"pkColumn"`
	SubTable                *GenTable             `json:"subTable"`
	Columns                 []*GenTableColumn     `json:"columns"`
	DictionaryInfoList      []*DictionaryInfo     `json:"dictionaryInfoList"`
	DictionaryInfoString    *string               `json:"dictionaryInfoString"`
	Options                 *string               `json:"options"`
	TreeCode                *string               `json:"treeCode"`
	TreeParentCode          *string               `json:"treeParentCode"`
	TreeName                *string               `json:"treeName"`
	ParentMenuID            *string               `json:"parentMenuId"`
	ParentMenuName          *string               `json:"parentMenuName"`
	DictionaryListKeySuffix *string               `json:"dictionaryListKeySuffix"`
	UploadInfo              *GenerateUploadInfo   `json:"uploadInfo"`
	RichTextInfo            *GenerateRichTextInfo `json:"richTextInfo"`
	ColumnDialogInfo        *GenColumnDialog      `json:"columnDialogInfo"`
	FilterColumnList        []*GenTableColumn     `json:"filterColumnList"`
}

func (t GenTable) MarshalJSON() ([]byte, error) {
	type plain GenTable
	v := plain(t)
	return json.Marshal(struct {
		*plain
		Sub  bool `json:"sub"`
		Tree bool `json:"tree"`
		Crud bool `json:"crud"`
	}{
		plain: &v,
		Sub:   t.IsSub(),
		Tree:  t.IsTree(),
		Crud:  t.IsCrud(),
	})
}

// IsSub 对应 Java GenTable.isSub()。
func (t *GenTable) IsSub() bool { return strVal(t.TplCategory) == tplSub }

// IsTree 对应 Java GenTable.isTree()。
func (t *GenTable) IsTree() bool { return strVal(t.TplCategory) == tplTree }

// IsCrud 对应 Java GenTable.isCrud()。
func (t *GenTable) IsCrud() bool { return strVal(t.TplCategory) == tplCrud }

// IsSuperColumn 对应 Java GenTable.isSuperColumn(String javaField)。
func (t *GenTable) IsSuperColumn(javaField any) bool {
	name := toJavaString(javaField)
	if t.IsTree() {
		return inStringIgnoreCase(name, append(append([]string{}, treeEntityColumns...), baseEntityColumns...)...)
	}
	return inStringIgnoreCase(name, baseEntityColumns...)
}

// VelocityProperty 暴露 Jackson/velocity 可见的派生属性。
func (t *GenTable) VelocityProperty(name string) (any, bool) {
	switch name {
	case "sub":
		return t.IsSub(), true
	case "tree":
		return t.IsTree(), true
	case "crud":
		return t.IsCrud(), true
	}
	return nil, false
}

// VelocityCall 供模板 $table.isSuperColumn(...) 使用。
func (t *GenTable) VelocityCall(name string, args []any) (any, bool) {
	if name == "isSuperColumn" && len(args) == 1 {
		return t.IsSuperColumn(args[0]), true
	}
	return nil, false
}

// ---------------------------------------------------------------------------
// GenTableColumn
// ---------------------------------------------------------------------------

// GenTableColumn 对应 com.ruoyi.generator.domain.GenTableColumn（字段序 = Java 声明序）。
type GenTableColumn struct {
	CreateBy                *string           `json:"createBy"`
	CreateTime              *web.DateTime     `json:"createTime"`
	UpdateBy                *string           `json:"updateBy"`
	UpdateTime              *web.DateTime     `json:"updateTime"`
	Remark                  *string           `json:"remark"`
	Params                  map[string]any    `json:"params,omitempty"`
	ColumnID                *int64            `json:"columnId"`
	TableID                 *int64            `json:"tableId"`
	ColumnName              *string           `json:"columnName"`
	ColumnComment           *string           `json:"columnComment"`
	ColumnType              *string           `json:"columnType"`
	JavaType                *string           `json:"javaType"`
	JavaField               *string           `json:"javaField"`
	IsPk                    *string           `json:"isPk"`
	IsIncrement             *string           `json:"isIncrement"`
	IsRequired              *string           `json:"isRequired"`
	IsInsert                *string           `json:"isInsert"`
	IsEdit                  *string           `json:"isEdit"`
	IsList                  *string           `json:"isList"`
	IsQuery                 *string           `json:"isQuery"`
	QueryType               *string           `json:"queryType"`
	HtmlType                *string           `json:"htmlType"`
	DictType                *string           `json:"dictType"`
	DictTypeCamelCase       *string           `json:"dictTypeCamelCase"`
	Sort                    *int64            `json:"sort"`
	GenerateLinkTableFlag   *string           `json:"generateLinkTableFlag"`
	LinkTableID             *int64            `json:"linkTableId"`
	LinkTable               *GenTable         `json:"linkTable"`
	SingleSelection         *string           `json:"singleSelection"`
	MultipleSelections      *string           `json:"multipleSelections"`
	DialogSearchColumnIDs   *string           `json:"dialogSearchColumnIds"`
	DialogListColumnIDs     *string           `json:"dialogListColumnIds"`
	DialogSearchColumnList  []*GenTableColumn `json:"dialogSearchColumnList"`
	DialogShowColumnList    []*GenTableColumn `json:"dialogShowColumnList"`
	DialogSearchColumnNames *string           `json:"dialogSearchColumnNames"`
	DialogListColumnNames   *string           `json:"dialogListColumnNames"`
	FieldMapString          *string           `json:"fieldMapString"`
	TableFieldList          []*LinkTableField `json:"tableFieldList"`
	CustomFieldList         []*LinkTableField `json:"customFieldList"`
	MajorLinkFieldInfo      *LinkTableField   `json:"majorLinkFieldInfo"`
}

func (c GenTableColumn) MarshalJSON() ([]byte, error) {
	type plain GenTableColumn
	v := plain(c)
	if v.GenerateLinkTableFlag == nil || *v.GenerateLinkTableFlag == "" {
		flag := "0"
		v.GenerateLinkTableFlag = &flag
	}
	var capJavaField any
	if c.JavaField != nil {
		capJavaField = capitalize(*c.JavaField)
	}
	return json.Marshal(struct {
		*plain
		CapJavaField any  `json:"capJavaField"`
		Pk           bool `json:"pk"`
		Increment    bool `json:"increment"`
		Required     bool `json:"required"`
		Insert       bool `json:"insert"`
		Edit         bool `json:"edit"`
		List         bool `json:"list"`
		Query        bool `json:"query"`
		SuperColumn  bool `json:"superColumn"`
		UsableColumn bool `json:"usableColumn"`
	}{
		plain:        &v,
		CapJavaField: capJavaField,
		Pk:           c.IsPrimaryKey(),
		Increment:    c.Increment(),
		Required:     c.Required(),
		Insert:       c.Insert(),
		Edit:         c.Edit(),
		List:         c.List(),
		Query:        c.Query(),
		SuperColumn:  c.IsSuperColumn(),
		UsableColumn: c.IsUsableColumn(),
	})
}

func isOne(v *string) bool { return v != nil && *v == "1" }

// IsPrimaryKey 对应 Java GenTableColumn.isPk()。
func (c *GenTableColumn) IsPrimaryKey() bool { return isOne(c.IsPk) }

// DIFF: Java 的 isIncrement()/isRequired()/... 与同名字段在 Go 里不能共存，
// 方法去掉 Is 前缀；JSON 里的派生键名保持不变（increment/required/...）。
func (c *GenTableColumn) Increment() bool { return isOne(c.IsIncrement) }
func (c *GenTableColumn) Required() bool  { return isOne(c.IsRequired) }
func (c *GenTableColumn) Insert() bool    { return isOne(c.IsInsert) }
func (c *GenTableColumn) Edit() bool      { return isOne(c.IsEdit) }
func (c *GenTableColumn) List() bool      { return isOne(c.IsList) }
func (c *GenTableColumn) Query() bool     { return isOne(c.IsQuery) }

// IsSuperColumn 对应 Java GenTableColumn.isSuperColumn()。
func (c *GenTableColumn) IsSuperColumn() bool {
	return inStringIgnoreCase(strVal(c.JavaField),
		"createBy", "createTime", "updateBy", "updateTime", "remark",
		"parentName", "parentId", "orderNum", "ancestors")
}

// IsUsableColumn 对应 Java GenTableColumn.isUsableColumn()。
func (c *GenTableColumn) IsUsableColumn() bool {
	return inStringIgnoreCase(strVal(c.JavaField), "parentId", "orderNum", "remark")
}

// ReadConverterExp 对应 Java GenTableColumn.readConverterExp()。
func (c *GenTableColumn) ReadConverterExp() *string {
	remarks := substringBetween(strVal(c.ColumnComment), "（", "）")
	if remarks == nil || strings.TrimSpace(*remarks) == "" {
		return c.ColumnComment
	}
	var b strings.Builder
	for _, value := range javaSplitSpace(*remarks) {
		if value == "" {
			continue
		}
		b.WriteString(value[:1])
		b.WriteString("=")
		b.WriteString(value[1:])
		b.WriteString(",")
	}
	text := b.String()
	if text == "" {
		return c.ColumnComment
	}
	out := text[:len(text)-1]
	return &out
}

// VelocityProperty 暴露 Jackson/velocity 可见的派生属性。
func (c *GenTableColumn) VelocityProperty(name string) (any, bool) {
	switch name {
	case "capJavaField":
		if c.JavaField == nil {
			return nil, true
		}
		return capitalize(*c.JavaField), true
	case "pk":
		return c.IsPrimaryKey(), true
	case "increment":
		return c.Increment(), true
	case "required":
		return c.Required(), true
	case "insert":
		return c.Insert(), true
	case "edit":
		return c.Edit(), true
	case "list":
		return c.List(), true
	case "query":
		return c.Query(), true
	case "superColumn":
		return c.IsSuperColumn(), true
	case "usableColumn":
		return c.IsUsableColumn(), true
	case "generateLinkTableFlag":
		if c.GenerateLinkTableFlag == nil || *c.GenerateLinkTableFlag == "" {
			return "0", true
		}
		return *c.GenerateLinkTableFlag, true
	}
	return nil, false
}

// VelocityCall 供模板调用 $column.readConverterExp() / isSuperColumn() / isUsableColumn()。
func (c *GenTableColumn) VelocityCall(name string, args []any) (any, bool) {
	switch name {
	case "readConverterExp":
		return c.ReadConverterExp(), true
	case "isSuperColumn":
		return c.IsSuperColumn(), true
	case "isUsableColumn":
		return c.IsUsableColumn(), true
	}
	return nil, false
}

// ---------------------------------------------------------------------------
// 附属领域对象
// ---------------------------------------------------------------------------

// DictionaryInfo 对应 com.ruoyi.generator.domain.DictionaryInfo。
type DictionaryInfo struct {
	DictionaryKey          *string `json:"dictionaryKey"`
	DictionaryKeyCamelCase *string `json:"dictionaryKeyCamelCase"`
}

// GenColumnDialog 对应 com.ruoyi.generator.domain.GenColumnDialog。
type GenColumnDialog struct {
	DialogNumber       *int64            `json:"dialogNumber"`
	CheckboxNumber     *int64            `json:"checkboxNumber"`
	RadioNumber        *int64            `json:"radioNumber"`
	DialogColumnList   []*GenTableColumn `json:"dialogColumnList"`
	CheckBoxColumnList []*GenTableColumn `json:"checkBoxColumnList"`
	RadioColumnList    []*GenTableColumn `json:"radioColumnList"`
	TableFieldList     []*LinkTableField `json:"tableFieldList"`
	CustomFieldList    []*LinkTableField `json:"customFieldList"`
	FieldList          []*LinkTableField `json:"fieldList"`
}

// GenerateRichTextInfo 对应 com.ruoyi.generator.domain.GenerateRichTextInfo。
type GenerateRichTextInfo struct {
	RichTextCount *int64            `json:"richTextCount"`
	ColumnList    []*GenTableColumn `json:"columnList"`
}

// GenerateUploadInfo 对应 com.ruoyi.generator.domain.GenerateUploadInfo。
// 字段名 uploadFiledNames 是 Java 原文笔误，保留。
type GenerateUploadInfo struct {
	UploadCount      *int64            `json:"uploadCount"`
	UploadColumn     []*GenTableColumn `json:"uploadColumn"`
	UploadFiledNames *string           `json:"uploadFiledNames"`
}

// LinkTableField 对应 com.ruoyi.generator.domain.LinkTableField。
type LinkTableField struct {
	FieldType          *string         `json:"fieldType"`
	CurrentTableFileID *int64          `json:"currentTableFileId"`
	LinkTableFieldID   *int64          `json:"linkTableFieldId"`
	CustomFieldName    *string         `json:"customFieldName"`
	CustomFileComment  *string         `json:"customFileComment"`
	TableFileAlias     *string         `json:"tableFileAlias"`
	TableFileInfo      *GenTableColumn `json:"tableFileInfo"`
	LinkTableFieldInfo *GenTableColumn `json:"linkTableFieldInfo"`
}

func (f LinkTableField) MarshalJSON() ([]byte, error) {
	type plain LinkTableField
	v := plain(f)
	if v.CustomFileComment == nil || *v.CustomFileComment == "" {
		empty := ""
		v.CustomFileComment = &empty
	}
	return json.Marshal(&v)
}

// VelocityProperty 复刻 getCustomFileComment() 的空串兜底。
func (f *LinkTableField) VelocityProperty(name string) (any, bool) {
	if name == "customFileComment" {
		if f.CustomFileComment == nil || *f.CustomFileComment == "" {
			return "", true
		}
		return *f.CustomFileComment, true
	}
	return nil, false
}

// ---------------------------------------------------------------------------
// Java HashSet 迭代顺序（getImportList 的 import 行顺序）
// ---------------------------------------------------------------------------

// javaHashSet 复刻 java.util.HashSet<String> 的迭代顺序（容量 16、链表、桶序）。
type javaHashSet struct {
	items []string
}

func newJavaHashSet() *javaHashSet { return &javaHashSet{} }

func (s *javaHashSet) Add(value string) {
	for _, item := range s.items {
		if item == value {
			return
		}
	}
	s.items = append(s.items, value)
}

func (s *javaHashSet) Contains(value string) bool {
	for _, item := range s.items {
		if item == value {
			return true
		}
	}
	return false
}

func (s *javaHashSet) Size() int { return len(s.items) }

func (s *javaHashSet) ToList() []string {
	buckets := map[int][]string{}
	for _, item := range s.items {
		idx := int(spread(javaHash(item)) & 15)
		buckets[idx] = append(buckets[idx], item)
	}
	out := make([]string, 0, len(s.items))
	for i := 0; i < 16; i++ {
		out = append(out, buckets[i]...)
	}
	return out
}

// javaHash 对应 Java String.hashCode（UTF-16 code unit，有符号 32 位）。
func javaHash(s string) int32 {
	var h int32
	for _, r := range s {
		if r > 0xFFFF {
			r -= 0x10000
			h = h*31 + (0xD800 + (r >> 10))
			h = h*31 + (0xDC00 + (r & 0x3FF))
			continue
		}
		h = h*31 + r
	}
	return h
}

func spread(h int32) int32 { return h ^ int32(uint32(h)>>16) }

// ---------------------------------------------------------------------------
// 小工具
// ---------------------------------------------------------------------------

func strVal(p *string) string {
	if p == nil {
		return ""
	}
	return *p
}

func strPtr(v string) *string { return conv.Str(v) }
