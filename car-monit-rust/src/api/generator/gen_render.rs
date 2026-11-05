// 来源: ruoyi-generator/src/main/java/com/ruoyi/generator/util/VelocityUtils.java
//       ruoyi-generator/.../service/GenTableServiceImpl.java#previewCode / setPkColumn
//       /dictionaryKeyToCamelCase
// 职责: 代码生成的模板上下文 + 渲染（替代 Java 的 Apache Velocity）。
//
// 模板文件从 Java 资源目录原样拷贝到 car-monit-rust/templates/**，
// 用 include_str! 内嵌，等价 Java 的 ClasspathResourceLoader。

use serde_json::{json, Map, Value};

use crate::service::velocity::{self, Ctx};

macro_rules! tpl {
    ($name:expr) => {
        (
            $name,
            include_str!(concat!(env!("CARGO_MANIFEST_DIR"), "/templates/", $name)),
        )
    };
}

/// (模板路径, 内容)；路径与 Java 的 getTemplateList 返回值一致。
pub const TEMPLATES: &[(&str, &str)] = &[
    tpl!("vm/java/domain.java.vm"),
    tpl!("vm/java/domain-bak.java.vm"),
    tpl!("vm/java/mapper.java.vm"),
    tpl!("vm/java/service.java.vm"),
    tpl!("vm/java/serviceImpl.java.vm"),
    tpl!("vm/java/controller.java.vm"),
    tpl!("vm/java/sub-domain.java.vm"),
    tpl!("vm/xml/mapper.xml.vm"),
    tpl!("vm/sql/sql.vm"),
    tpl!("vm/js/api.js.vm"),
    tpl!("vm/vue/index.vue.vm"),
    tpl!("vm/vue/index-form.vue.vm"),
    tpl!("vm/vue/index-tree.vue.vm"),
    tpl!("vmplus/java/domain.java.vm"),
    tpl!("vmplus/java/domain-bak.java.vm"),
    tpl!("vmplus/java/mapper.java.vm"),
    tpl!("vmplus/java/service.java.vm"),
    tpl!("vmplus/java/serviceImpl.java.vm"),
    tpl!("vmplus/java/controller.java.vm"),
    tpl!("vmplus/java/sub-domain.java.vm"),
    tpl!("vmplus/xml/mapper.xml.vm"),
    tpl!("vmplus/sql/sql.vm"),
    tpl!("vmplus/js/api.js.vm"),
    tpl!("vmplus/vue/index.vue.vm"),
    tpl!("vmplus/vue/index-form.vue.vm"),
    tpl!("vmplus/vue/index-tree.vue.vm"),
];

const DEFAULT_PARENT_MENU_ID: &str = "3";
/// Java: Constants.GENERATE_CODE_DICTIONARY_LIST_KEY_SUFFIX
const DICTIONARY_LIST_KEY_SUFFIX: &str = "DictList";

fn template_text(name: &str) -> Option<&'static str> {
    TEMPLATES
        .iter()
        .find(|(key, _)| *key == name)
        .map(|(_, text)| *text)
}

/// Java: VelocityUtils.getTemplateList
pub fn template_list(tpl_category: &str, is_mybatis_plus: bool) -> Vec<String> {
    let prefix = if is_mybatis_plus { "vmplus" } else { "vm" };
    let mut templates = vec![
        format!("{prefix}/java/domain.java.vm"),
        format!("{prefix}/java/mapper.java.vm"),
        format!("{prefix}/java/service.java.vm"),
        format!("{prefix}/java/serviceImpl.java.vm"),
        format!("{prefix}/java/controller.java.vm"),
        format!("{prefix}/xml/mapper.xml.vm"),
        format!("{prefix}/sql/sql.vm"),
        format!("{prefix}/js/api.js.vm"),
    ];
    match tpl_category {
        "crud" => {
            templates.push(format!("{prefix}/vue/index.vue.vm"));
            templates.push(format!("{prefix}/vue/index-form.vue.vm"));
        }
        "tree" => templates.push(format!("{prefix}/vue/index-tree.vue.vm")),
        "sub" => {
            templates.push(format!("{prefix}/vue/index.vue.vm"));
            templates.push(format!("{prefix}/java/sub-domain.java.vm"));
        }
        _ => {}
    }
    templates
}

/// Java: StringUtils.capitalize
pub fn capitalize(value: &str) -> String {
    let mut chars = value.chars();
    match chars.next() {
        Some(first) => first.to_uppercase().collect::<String>() + chars.as_str(),
        None => String::new(),
    }
}

/// Java: StringUtils.uncapitalize
pub fn uncapitalize(value: &str) -> String {
    let mut chars = value.chars();
    match chars.next() {
        Some(first) => first.to_lowercase().collect::<String>() + chars.as_str(),
        None => String::new(),
    }
}

/// Java: StringUtils.toCamelCase（下划线转驼峰，先小写）
pub fn to_camel_case(value: &str) -> String {
    if !value.contains('_') {
        return value.to_string();
    }
    let mut out = String::new();
    let mut upper_next = false;
    for ch in value.to_lowercase().chars() {
        if ch == '_' {
            upper_next = true;
            continue;
        }
        if upper_next {
            out.extend(ch.to_uppercase());
            upper_next = false;
        } else {
            out.push(ch);
        }
    }
    out
}

/// Java: VelocityUtils.getPackagePrefix
pub fn package_prefix(package_name: &str) -> String {
    match package_name.rfind('.') {
        Some(index) => package_name[..index].to_string(),
        None => String::new(),
    }
}

/// Java: String.hashCode（32 位溢出回绕）
fn java_hash_code(value: &str) -> i32 {
    let mut hash: i32 = 0;
    for ch in value.chars() {
        hash = hash.wrapping_mul(31).wrapping_add(ch as i32);
    }
    hash
}

/// Java: HashMap 的散列扰动 + 桶序，用于复刻 HashSet 的迭代顺序。
fn java_hash_set_order(items: &[String]) -> Vec<String> {
    let mut capacity = 16usize;
    let mut buckets: Vec<Vec<(i32, String)>> = vec![Vec::new(); capacity];
    let mut size = 0usize;
    let mut seen: Vec<String> = Vec::new();
    for item in items {
        if seen.iter().any(|exist| exist == item) {
            continue;
        }
        seen.push(item.clone());
        let hash = java_hash_code(item) ^ (java_hash_code(item) >> 16);
        let index = (hash as usize) & (capacity - 1);
        buckets[index].push((hash, item.clone()));
        size += 1;
        if size > capacity * 3 / 4 {
            capacity *= 2;
            let mut resized: Vec<Vec<(i32, String)>> = vec![Vec::new(); capacity];
            for bucket in buckets {
                for (hash, value) in bucket {
                    let index = (hash as usize) & (capacity - 1);
                    resized[index].push((hash, value));
                }
            }
            buckets = resized;
        }
    }
    buckets
        .into_iter()
        .flat_map(|bucket| bucket.into_iter().map(|(_, value)| value))
        .collect()
}

/// Java: GenTableServiceImpl.dictionaryKeyToCamelCase 的列加工。
pub fn columns_with_dictionary(columns: &[Value]) -> (Vec<Value>, Vec<Value>, Option<String>) {
    let mut out = Vec::new();
    let mut dictionary_list: Vec<Value> = Vec::new();
    for column in columns {
        let mut column = column.clone();
        let dict_type = column
            .get("dictType")
            .and_then(Value::as_str)
            .unwrap_or_default()
            .to_string();
        let converter = read_converter_exp(&column);
        let converter = match converter {
            Some(text) => Value::String(text),
            // Java: 备注为 null 时 readConverterExp() 返回 null，Velocity 原样打印引用文本。
            None => Value::Null,
        };
        if !dict_type.is_empty() {
            let camel = to_camel_case(&dict_type);
            if let Some(object) = column.as_object_mut() {
                object.insert(
                    "dictTypeCamelCase".to_string(),
                    Value::String(camel.clone()),
                );
                object.insert("readConverterExp".to_string(), converter);
            }
            dictionary_list.push(json!({
                "dictionaryKey": dict_type,
                "dictionaryKeyCamelCase": camel,
            }));
        } else if let Some(object) = column.as_object_mut() {
            object.insert("readConverterExp".to_string(), converter);
        }
        out.push(column);
    }
    let dictionary_info_string = if dictionary_list.is_empty() {
        None
    } else {
        Some(
            dictionary_list
                .iter()
                .filter_map(|item| item.get("dictionaryKey").and_then(Value::as_str))
                .collect::<Vec<_>>()
                .join(","),
        )
    };
    (out, dictionary_list, dictionary_info_string)
}

/// Java: GenTableColumn.readConverterExp —— 取备注里全角括号内的内容转成 `1=正常,0=停用`；
/// 括号缺失或为空时返回备注本身，备注为 null 时返回 None（模板会原样打印引用）。
fn read_converter_exp(column: &Value) -> Option<String> {
    let comment = column.get("columnComment").and_then(Value::as_str)?;
    // Java: StringUtils.substringBetween(comment, "（", "）")
    let start = match comment.find('（') {
        Some(index) => index + '（'.len_utf8(),
        None => return Some(comment.to_string()),
    };
    let relative = match comment[start..].find('）') {
        Some(index) => index,
        None => return Some(comment.to_string()),
    };
    let remarks = &comment[start..start + relative];
    if remarks.is_empty() {
        return Some(comment.to_string());
    }
    let mut parts: Vec<String> = Vec::new();
    for value in remarks.split(' ') {
        if value.is_empty() {
            continue;
        }
        let head: String = value.chars().take(1).collect();
        let tail: String = value.chars().skip(1).collect();
        parts.push(format!("{head}={tail}"));
    }
    Some(parts.join(","))
}

/// Java: VelocityUtils.getImportList
pub fn import_list(columns: &[Value], has_sub_table: bool) -> Vec<String> {
    let mut items: Vec<String> = Vec::new();
    if has_sub_table {
        items.push("java.util.List".to_string());
    }
    for column in columns {
        if truthy_flag(column, "superColumn") {
            continue;
        }
        match column.get("javaType").and_then(Value::as_str) {
            Some("Date") => {
                items.push("java.util.Date".to_string());
                items.push("com.fasterxml.jackson.annotation.JsonFormat".to_string());
            }
            Some("BigDecimal") => items.push("java.math.BigDecimal".to_string()),
            _ => {}
        }
    }
    java_hash_set_order(&items)
}

fn truthy_flag(column: &Value, key: &str) -> bool {
    match column.get(key) {
        Some(Value::Bool(flag)) => *flag,
        Some(Value::String(text)) => text == "1" || text.eq_ignore_ascii_case("true"),
        Some(value) if !value.is_null() => true,
        _ => false,
    }
}

fn text_of(table: &Value, key: &str) -> String {
    table
        .get(key)
        .and_then(Value::as_str)
        .unwrap_or_default()
        .to_string()
}

/// Java: VelocityUtils.prepareContext
pub fn prepare_context(
    table: &Value,
    datetime: &str,
    columns: Vec<Value>,
    pk_column: Option<Value>,
    dictionary_list: Vec<Value>,
    dictionary_info_string: Option<String>,
    parent_menu_id: String,
) -> Map<String, Value> {
    let class_name = text_of(table, "className");
    let business_name = text_of(table, "businessName");
    let package_name = text_of(table, "packageName");
    let function_name = text_of(table, "functionName");
    let function_name = if function_name.is_empty() {
        "【请填写功能名称】".to_string()
    } else {
        function_name
    };
    let import_list = import_list(
        &columns,
        table.get("subTable").map(|v| !v.is_null()).unwrap_or(false),
    );
    let mut map = Map::new();
    map.insert("tplCategory".to_string(), json_of(table, "tplCategory"));
    map.insert("tableName".to_string(), json_of(table, "tableName"));
    map.insert("functionName".to_string(), Value::String(function_name));
    map.insert("ClassName".to_string(), Value::String(class_name.clone()));
    map.insert(
        "className".to_string(),
        Value::String(uncapitalize(&class_name)),
    );
    map.insert("moduleName".to_string(), json_of(table, "moduleName"));
    map.insert(
        "BusinessName".to_string(),
        Value::String(capitalize(&business_name)),
    );
    map.insert(
        "businessName".to_string(),
        Value::String(business_name.clone()),
    );
    map.insert(
        "basePackage".to_string(),
        Value::String(package_prefix(&package_name)),
    );
    map.insert("packageName".to_string(), Value::String(package_name));
    map.insert("author".to_string(), json_of(table, "functionAuthor"));
    map.insert("datetime".to_string(), Value::String(datetime.to_string()));
    map.insert("pkColumn".to_string(), pk_column.unwrap_or(Value::Null));
    map.insert(
        "importList".to_string(),
        Value::Array(import_list.into_iter().map(Value::String).collect()),
    );
    map.insert(
        "permissionPrefix".to_string(),
        Value::String(format!(
            "{}:{}",
            text_of(table, "moduleName"),
            business_name
        )),
    );
    map.insert("columns".to_string(), Value::Array(columns));
    map.insert("table".to_string(), table.clone());
    map.insert(
        "dictionaryListKeySuffix".to_string(),
        Value::String(DICTIONARY_LIST_KEY_SUFFIX.to_string()),
    );
    map.insert(
        "dictionaryInfoList".to_string(),
        Value::Array(dictionary_list),
    );
    map.insert(
        "dictionaryInfoString".to_string(),
        dictionary_info_string
            .map(Value::String)
            .unwrap_or(Value::Null),
    );
    for key in [
        "uploadInfo",
        "richTextInfo",
        "columnDialogInfo",
        "filterColumnList",
    ] {
        map.insert(key.to_string(), json_of(table, key));
    }
    map.insert("parentMenuId".to_string(), Value::String(parent_menu_id));
    map
}

fn json_of(table: &Value, key: &str) -> Value {
    table.get(key).cloned().unwrap_or(Value::Null)
}

/// Java: GenTableServiceImpl.setPkColumn
pub fn pk_column(columns: &[Value]) -> Option<Value> {
    for column in columns {
        if truthy_flag(column, "pk") {
            return Some(column.clone());
        }
    }
    columns.first().cloned()
}

/// Java: VelocityUtils.getParentMenuId（options 里没有则用默认「系统工具」=3）
pub fn parent_menu_id(options: Option<&Value>) -> String {
    let text = options.and_then(Value::as_str).unwrap_or_default();
    if let Ok(Value::Object(map)) = serde_json::from_str::<Value>(text) {
        if let Some(value) = map.get("parentMenuId") {
            return match value {
                Value::String(text) => text.clone(),
                other => other.to_string(),
            };
        }
    }
    DEFAULT_PARENT_MENU_ID.to_string()
}

/// Java: GenTableServiceImpl.FILTER_COLUMN_NAME_LIST
const FILTER_COLUMN_NAMES: &[&str] = &["sort", "epsId", "delFlag", "tenantId"];

/// Java: GenTableServiceImpl.initFilterColumnInfo
/// （去掉空 javaField、String 类型的 id、以及审计类保留字段）
pub fn filter_column_list(columns: &[Value]) -> Vec<Value> {
    columns
        .iter()
        .filter(|column| {
            let field = column
                .get("javaField")
                .and_then(Value::as_str)
                .unwrap_or_default();
            if field.is_empty() {
                return false;
            }
            let java_type = column
                .get("javaType")
                .and_then(Value::as_str)
                .unwrap_or_default();
            if field == "id" && java_type == "String" {
                return false;
            }
            !FILTER_COLUMN_NAMES.contains(&field)
        })
        .cloned()
        .collect()
}

fn html_type_is(column: &Value, expected: &str) -> bool {
    column.get("htmlType").and_then(Value::as_str) == Some(expected)
}

fn java_fields(columns: &[Value]) -> String {
    columns
        .iter()
        .filter_map(|column| column.get("javaField").and_then(Value::as_str))
        .collect::<Vec<_>>()
        .join(",")
}

/// Java: initUploadInfo（没有上传列时只有 uploadCount=0，其余属性为 null）
pub fn upload_info(columns: &[Value]) -> Option<Value> {
    if columns.is_empty() {
        return None;
    }
    let uploads: Vec<Value> = columns
        .iter()
        .filter(|column| html_type_is(column, "fileUpload"))
        .cloned()
        .collect();
    if uploads.is_empty() {
        return Some(json!({ "uploadCount": 0 }));
    }
    Some(json!({
        "uploadCount": uploads.len(),
        "uploadColumn": uploads.clone(),
        "uploadFiledNames": java_fields(&uploads),
    }))
}

/// Java: initRichTextInfo
pub fn rich_text_info(columns: &[Value]) -> Option<Value> {
    if columns.is_empty() {
        return None;
    }
    let editors: Vec<Value> = columns
        .iter()
        .filter(|column| html_type_is(column, "editor"))
        .cloned()
        .collect();
    if editors.is_empty() {
        return Some(json!({ "richTextCount": 0 }));
    }
    Some(json!({ "richTextCount": editors.len(), "columnList": editors }))
}

/// Java: GenTableServiceImpl.previewCode —— 渲染该表需要的全部模板。
pub async fn render_preview(
    pool: &sqlx::MySqlPool,
    table: &Value,
    raw_columns: &[Value],
    datetime: &str,
    is_mybatis_plus: bool,
) -> Result<Map<String, Value>, String> {
    let mut data = Map::new();
    for (name, text) in
        render_templates(pool, table, raw_columns, datetime, is_mybatis_plus).await?
    {
        data.insert(name, Value::String(text));
    }
    Ok(data)
}

/// 逐模板渲染，按 Java `getTemplateList` 的顺序返回 (模板名, 内容)。
/// previewCode 用它拼 LinkedHashMap，generatorCode 用它拼 zip 条目。
pub async fn render_templates(
    pool: &sqlx::MySqlPool,
    table: &Value,
    raw_columns: &[Value],
    datetime: &str,
    is_mybatis_plus: bool,
) -> Result<Vec<(String, String)>, String> {
    let (mut columns, dictionary_list, dictionary_info_string) =
        columns_with_dictionary(raw_columns);
    // Java: dictionaryKeyToCamelCase 之后才跑 initLinkTableInfo，
    // 所以关联列（含 dialog 列表里的同一批实例）已经带上 dictTypeCamelCase。
    let dialog_info = crate::api::generator::gen_link::link_table_info(pool, &mut columns).await?;
    let pk = pk_column(&columns);
    let mut context_table = table.clone();
    if let Some(object) = context_table.as_object_mut() {
        // Java: previewCode 在 prepareContext 之前先跑这几步加工，结果都挂在 table 上。
        object.insert("columns".to_string(), Value::Array(columns.clone()));
        object.insert("pkColumn".to_string(), pk.clone().unwrap_or(Value::Null));
        object.insert(
            "filterColumnList".to_string(),
            Value::Array(filter_column_list(&columns)),
        );
        object.insert(
            "uploadInfo".to_string(),
            upload_info(&columns).unwrap_or(Value::Null),
        );
        object.insert(
            "richTextInfo".to_string(),
            rich_text_info(&columns).unwrap_or(Value::Null),
        );
        object.insert("columnDialogInfo".to_string(), dialog_info);
    }
    let root = prepare_context(
        &context_table,
        datetime,
        columns.clone(),
        pk,
        dictionary_list,
        dictionary_info_string,
        parent_menu_id(table.get("options")),
    );
    let mut data = Vec::new();
    for name in template_list(&text_of(table, "tplCategory"), is_mybatis_plus) {
        let Some(text) = template_text(&name) else {
            return Err(format!("缺少模板 {name}"));
        };
        // 每个模板用独立的上下文副本：#set 只影响本次渲染（与 Java 每次 merge 新建子上下文一致）。
        let mut ctx = Ctx::with_root(root.clone());
        let rendered = velocity::render(text, &mut ctx).map_err(|err| format!("{name}: {err}"))?;
        data.push((name, rendered));
    }
    Ok(data)
}

/// Java: VelocityUtils.getFileName —— zip 条目名 / 落盘相对路径。
pub fn file_name(template: &str, table: &Value) -> Result<String, String> {
    let package_name = text_of(table, "packageName");
    let module_name = text_of(table, "moduleName");
    let class_name = text_of(table, "className");
    let business_name = text_of(table, "businessName");
    // Java: PROJECT_PATH = "main/java"，MYBATIS_PATH = "main/resources/mapper"
    let java_path = format!("main/java/{}", package_name.replace('.', "/"));
    let mybatis_path = format!("main/resources/mapper/{module_name}");

    let mut name = String::new();
    if template.contains("domain.java.vm") {
        name = format!("{java_path}/domain/{class_name}.java");
    }
    if template.contains("sub-domain.java.vm") && text_of(table, "tplCategory") == "sub" {
        // Java: genTable.getSubTable().getClassName()；subTable 为空时 Java 直接 NPE -> 500
        let sub_class = table
            .get("subTable")
            .and_then(|value| value.get("className"))
            .and_then(Value::as_str)
            .filter(|value| !value.is_empty())
            .ok_or_else(|| format!("子表信息缺失，无法生成 {template}"))?;
        name = format!("{java_path}/domain/{sub_class}.java");
    } else if template.contains("mapper.java.vm") {
        name = format!("{java_path}/mapper/{class_name}Mapper.java");
    } else if template.contains("service.java.vm") {
        name = format!("{java_path}/service/I{class_name}Service.java");
    } else if template.contains("serviceImpl.java.vm") {
        name = format!("{java_path}/service/impl/{class_name}ServiceImpl.java");
    } else if template.contains("controller.java.vm") {
        name = format!("{java_path}/controller/{class_name}Controller.java");
    } else if template.contains("mapper.xml.vm") {
        name = format!("{mybatis_path}/{class_name}Mapper.xml");
    } else if template.contains("sql.vm") {
        name = format!("{business_name}Menu.sql");
    } else if template.contains("api.js.vm") {
        name = format!("vue/api/{module_name}/{business_name}.js");
    } else if template.contains("index.vue.vm") {
        name = format!("vue/views/{module_name}/{business_name}/index.vue");
    } else if template.contains("index-form.vue.vm") {
        name = format!("vue/views/{module_name}/{business_name}/index-form.vue");
    } else if template.contains("index-tree.vue.vm") {
        name = format!("vue/views/{module_name}/{business_name}/index.vue");
    }
    Ok(name)
}

/// Java: GenTableServiceImpl.getGenPath（user.dir 取进程工作目录，File.separator 用本机分隔符）。
pub fn gen_path(table: &Value, template: &str) -> Result<std::path::PathBuf, String> {
    let name = file_name(template, table)?;
    let gen_path = text_of(table, "genPath");
    let joined = if gen_path == "/" {
        let cwd = std::env::current_dir()
            .map_err(|err| err.to_string())?
            .to_string_lossy()
            .to_string();
        format!(
            "{cwd}{}src{}{name}",
            std::path::MAIN_SEPARATOR_STR,
            std::path::MAIN_SEPARATOR_STR
        )
    } else {
        format!("{gen_path}{}{name}", std::path::MAIN_SEPARATOR)
    };
    // Java 的 Windows 路径里混着 '/' 与 '\'，File 会自行归一，这里保持原样交给 OS。
    Ok(std::path::PathBuf::from(joined))
}
