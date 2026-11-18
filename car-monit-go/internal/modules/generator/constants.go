// JAVA 对照: ruoyi-common/src/main/java/com/ruoyi/common/constant/GenConstants.java:10-116
// 类/职责: 代码生成常量 — 模板类型 / 树字段键 / 列类型分组 / HTML 控件 / 查询方式
// 对应 Go 文件: internal/modules/generator/constants.go
package generator

const (
	tplCrud = "crud"
	tplTree = "tree"
	tplSub  = "sub"

	treeCode       = "treeCode"
	treeParentCode = "treeParentCode"
	treeName       = "treeName"
	parentMenuID   = "parentMenuId"
	parentMenuName = "parentMenuName"

	htmlInput       = "input"
	htmlTextarea    = "textarea"
	htmlSelect      = "select"
	htmlRadio       = "radio"
	htmlCheckbox    = "checkbox"
	htmlDatetime    = "datetime"
	htmlImageUpload = "imageUpload"
	htmlFileUpload  = "fileUpload"
	htmlEditor      = "editor"

	typeString     = "String"
	typeInteger    = "Integer"
	typeLong       = "Long"
	typeDouble     = "Double"
	typeBigDecimal = "BigDecimal"
	typeDate       = "Date"

	queryLike  = "LIKE"
	queryEQ    = "EQ"
	queryNE    = "NE"
	queryGT    = "GT"
	queryLT    = "LT"
	queryRange = "BETWEEN"

	require = "1"

	// JAVA 对照: Constants.GENERATE_CODE_DICTIONARY_LIST_KEY_SUFFIX
	generateCodeDictionaryListKeySuffix = "DictList"
	// JAVA 对照: Constants.COLUMN_PRIMARY_KEY / STRING_CLASS_KEY
	columnPrimaryKey = "id"
	stringClassKey   = "String"

	linkTableFieldTypeTable       = "10"
	linkTableFieldTypeCustomField = "20"
)

// JAVA 对照: GenConstants.COLUMNTYPE_STR
var columnTypeStr = []string{"char", "varchar", "nvarchar", "varchar2"}

// JAVA 对照: GenConstants.COLUMNTYPE_TEXT
var columnTypeText = []string{"tinytext", "text", "mediumtext", "longtext"}

// JAVA 对照: GenConstants.COLUMNTYPE_TIME
var columnTypeTime = []string{"datetime", "time", "date", "timestamp"}

// JAVA 对照: GenConstants.COLUMNTYPE_NUMBER
var columnTypeNumber = []string{
	"tinyint", "smallint", "mediumint", "int", "number", "integer",
	"bit", "bigint", "float", "double", "decimal",
}

// JAVA 对照: GenConstants.COLUMNNAME_NOT_EDIT
var columnNameNotEdit = []string{"id", "create_by", "create_time", "del_flag"}

// JAVA 对照: GenConstants.COLUMNNAME_NOT_LIST
var columnNameNotList = []string{
	"id", "create_by", "create_time", "del_flag", "update_by", "update_time",
}

// JAVA 对照: GenConstants.COLUMNNAME_NOT_QUERY
var columnNameNotQuery = []string{
	"id", "create_by", "create_time", "del_flag", "update_by", "update_time", "remark",
}

// JAVA 对照: GenConstants.BASE_ENTITY
var baseEntityColumns = []string{"createBy", "createTime", "updateBy", "updateTime", "remark"}

// JAVA 对照: GenConstants.TREE_ENTITY
var treeEntityColumns = []string{"parentName", "parentId", "orderNum", "ancestors", "children"}

// JAVA 对照: GenTableServiceImpl.FILTER_COLUMN_NAME_LIST（static 块按序 add）
var filterColumnNameList = []string{"sort", "epsId", "delFlag", "tenantId"}

// JAVA 对照: VelocityUtils.PROJECT_PATH / MYBATIS_PATH / DEFAULT_PARENT_MENU_ID / DEFAULT_FUNCTION_NAME
const (
	projectPath         = "main/java"
	mybatisPath         = "main/resources/mapper"
	defaultParentMenuID = "3"
	defaultFunctionName = "【请填写功能名称】"
)
