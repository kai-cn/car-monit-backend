// 来源: ruoyi-generator/src/main/java/com/ruoyi/generator/service/GenTableServiceImpl.java
//       #initLinkTableInfo / #initDialogQueryShowData / #initTableFieldInfo / #initLinkTableFieldInfo
// 职责: 代码生成上下文里「关联表（Dialog）」的回查，产出模板用的 columnDialogInfo。
//
// Java 侧这些对象之间是**共享引用**：dialogColumnList 里的列与 table.columns 是同一批实例，
// LinkTableField 同时挂在 column.tableFieldList 与 columnDialogInfo.fieldList 上，
// initTableFieldInfo/initLinkTableFieldInfo 再原地补 tableFileInfo/linkTableFieldInfo。
// 这里按同样的顺序改数据、最后才克隆进 dialog，保证 JSON 与模板输出和 Java 一致。

use std::collections::HashMap;

use serde_json::{json, Map, Value};
use sqlx::{MySql, MySqlPool, QueryBuilder};

use crate::api::generator::{gen, gen_render};

/// Java: LinkTableFiledTypeEnum（字符串码，不是数字）
const FIELD_TYPE_TABLE: &str = "10";
const FIELD_TYPE_CUSTOM: &str = "20";

/// Java: LinkTableField 的 Jackson 键顺序（@Data 声明顺序）
const LINK_FIELD_KEYS: &[&str] = &[
    "fieldType",
    "currentTableFileId",
    "linkTableFieldId",
    "customFieldName",
    "customFileComment",
    "tableFileAlias",
    "tableFileInfo",
    "linkTableFieldInfo",
];
/// 其中只有两个字段是 Long，fastjson2 会把 "123" 转成数字；其余 String 字段反之。
const LINK_LONG_KEYS: &[&str] = &["currentTableFileId", "linkTableFieldId"];

/// Java: GenColumnDialog 的 Jackson 键顺序（无父类；注意 `checkBoxColumnList` 的大写 C）
const COLUMN_DIALOG_KEYS: &[&str] = &[
    "dialogNumber",
    "checkboxNumber",
    "radioNumber",
    "dialogColumnList",
    "checkBoxColumnList",
    "radioColumnList",
    "tableFieldList",
    "customFieldList",
    "fieldList",
];

/// Java: GenTableServiceImpl.initLinkTableInfo —— 就地加工 `columns`，返回 GenColumnDialog。
pub(crate) async fn link_table_info(
    pool: &MySqlPool,
    columns: &mut Vec<Value>,
) -> Result<Value, String> {
    if columns.is_empty() {
        // Java: 列集合为空时方法直接返回，table.columnDialogInfo 保持 null
        return Ok(Value::Null);
    }
    let link_indexes: Vec<usize> = columns
        .iter()
        .enumerate()
        .filter(|(_, column)| is_link_column(column))
        .map(|(index, _)| index)
        .collect();

    // 1) initDialogQueryShowData：dialog 搜索/展示列 + 关联表（mapper 原样 + setPkColumn）
    for index in &link_indexes {
        let search_ids = str_of(&columns[*index], "dialogSearchColumnIds");
        let list_ids = str_of(&columns[*index], "dialogListColumnIds");
        let link_table_id = columns[*index]
            .get("linkTableId")
            .cloned()
            .unwrap_or(Value::Null);
        if !search_ids.is_empty() {
            let rows = select_columns_by_ids(pool, &split_ids(&search_ids)).await?;
            put(&mut columns[*index], "dialogSearchColumnList", rows);
        }
        if !list_ids.is_empty() {
            let rows = select_columns_by_ids(pool, &split_ids(&list_ids)).await?;
            put(&mut columns[*index], "dialogShowColumnList", rows);
        }
        let link_table = select_link_table(pool, &link_table_id).await?;
        put(&mut columns[*index], "linkTable", link_table);
    }

    // 2) 解析 field_map_string，按 fieldType 10/20 分流；radio/checkbox 与三张全局列表同时累积
    let mut majors: Vec<(usize, usize)> = Vec::new();
    let mut radio: Vec<usize> = Vec::new();
    let mut checkbox: Vec<usize> = Vec::new();
    let mut all_table: Vec<(usize, usize)> = Vec::new();
    let mut all_custom: Vec<(usize, usize)> = Vec::new();
    // (列下标, 是否表字段, 字段在该列表里的下标)
    let mut all_field: Vec<(usize, bool, usize)> = Vec::new();

    for index in &link_indexes {
        if str_of(&columns[*index], "singleSelection") == "1" {
            radio.push(*index);
        }
        if str_of(&columns[*index], "multipleSelections") == "1" {
            checkbox.push(*index);
        }
        let raw = str_of(&columns[*index], "fieldMapString");
        let fields = parse_field_map(&raw)?;
        let table_positions: Vec<usize> = positions(&fields, FIELD_TYPE_TABLE);
        let custom_positions: Vec<usize> = positions(&fields, FIELD_TYPE_CUSTOM);
        // 记下标用的是「该列自己 tableFieldList/customFieldList 里的序号」，
        // 不是 field_map_string 数组里的原始下标 —— 后面按它原地回写字段对象。
        if !table_positions.is_empty() {
            let list = table_positions
                .iter()
                .map(|p| fields[*p].clone())
                .collect::<Vec<_>>();
            put(&mut columns[*index], "tableFieldList", Value::Array(list));
            for ordinal in 0..table_positions.len() {
                all_table.push((*index, ordinal));
                all_field.push((*index, true, ordinal));
            }
        }
        if !custom_positions.is_empty() {
            let list = custom_positions
                .iter()
                .map(|p| fields[*p].clone())
                .collect::<Vec<_>>();
            put(&mut columns[*index], "customFieldList", Value::Array(list));
            for ordinal in 0..custom_positions.len() {
                all_custom.push((*index, ordinal));
                all_field.push((*index, false, ordinal));
            }
        }
        put(&mut columns[*index], "generateLinkTableFlag", json!("1"));
        // Java: tableFieldList.filter(currentTableFileId == columnId).findFirst().get()
        // 没有匹配就抛 NoSuchElementException -> 500；这里同样显式失败，不静默跳过。
        let column_id = columns[*index]
            .get("columnId")
            .cloned()
            .unwrap_or(Value::Null);
        let major = table_positions
            .iter()
            .position(|position| {
                id_of(fields[*position].get("currentTableFileId")) == id_of(Some(&column_id))
            })
            .ok_or_else(|| {
                format!(
                    "关联字段映射里没有当前表列 {} 的表字段",
                    id_of(Some(&column_id))
                )
            })?;
        // Java 的 majorLinkFieldInfo 与 tableFieldList[major] 是同一个对象，后面
        // initTableFieldInfo/initLinkTableFieldInfo 补的字段它也要能看到，所以这里只记下标，
        // 等回写完成后（下面第 5 步之前）再从列表里取。
        majors.push((*index, major));
    }

    // 3) initTableFieldInfo：按 currentTableFileId 回查列，写 tableFileInfo
    let ids: Vec<String> = all_table
        .iter()
        .map(|(column, position)| field_id(columns, *column, true, *position, "currentTableFileId"))
        .collect();
    let lookup = columns_by_id(pool, &ids).await?;
    for (column, position) in &all_table {
        let key = field_id(columns, *column, true, *position, "currentTableFileId");
        if let Some(row) = lookup.get(&key) {
            put_field(
                columns,
                *column,
                true,
                *position,
                "tableFileInfo",
                row.clone(),
            );
        }
    }

    // 4) initLinkTableFieldInfo：按 linkTableFieldId 回查列，写 linkTableFieldInfo
    let ids: Vec<String> = all_field
        .iter()
        .map(|(column, is_table, position)| {
            field_id(columns, *column, *is_table, *position, "linkTableFieldId")
        })
        .collect();
    let lookup = columns_by_id(pool, &ids).await?;
    for (column, is_table, position) in &all_field {
        let key = field_id(columns, *column, *is_table, *position, "linkTableFieldId");
        if let Some(row) = lookup.get(&key) {
            put_field(
                columns,
                *column,
                *is_table,
                *position,
                "linkTableFieldInfo",
                row.clone(),
            );
        }
    }

    // 5) majorLinkFieldInfo 指回已经被补全过的表字段对象
    for (column, ordinal) in &majors {
        let value = field(columns, *column, true, *ordinal);
        put(&mut columns[*column], "majorLinkFieldInfo", value);
    }

    // 6) 组装 GenColumnDialog（此时所有原地补写都已完成，克隆出来即为最终形态）
    let dialog = json!({
        "dialogNumber": link_indexes.len(),
        "checkboxNumber": checkbox.len(),
        "radioNumber": radio.len(),
        "dialogColumnList": link_indexes.iter().map(|i| columns[*i].clone()).collect::<Vec<_>>(),
        "checkBoxColumnList": checkbox.iter().map(|i| columns[*i].clone()).collect::<Vec<_>>(),
        "radioColumnList": radio.iter().map(|i| columns[*i].clone()).collect::<Vec<_>>(),
        "tableFieldList": all_table.iter().map(|(c, p)| field(columns, *c, true, *p)).collect::<Vec<_>>(),
        "customFieldList": all_custom.iter().map(|(c, p)| field(columns, *c, false, *p)).collect::<Vec<_>>(),
        "fieldList": all_field.iter().map(|(c, t, p)| field(columns, *c, *t, *p)).collect::<Vec<_>>(),
    });
    Ok(reorder(&dialog, COLUMN_DIALOG_KEYS))
}

fn is_link_column(column: &Value) -> bool {
    column
        .get("linkTableId")
        .map(|value| !value.is_null())
        .unwrap_or(false)
        && !str_of(column, "fieldMapString").trim().is_empty()
}

fn positions(fields: &[Value], code: &str) -> Vec<usize> {
    fields
        .iter()
        .enumerate()
        .filter(|(_, field)| field.get("fieldType").and_then(Value::as_str) == Some(code))
        .map(|(position, _)| position)
        .collect()
}

fn str_of(column: &Value, key: &str) -> String {
    match column.get(key) {
        Some(Value::String(text)) => text.clone(),
        Some(value) if !value.is_null() => value.to_string(),
        _ => String::new(),
    }
}

fn put(column: &mut Value, key: &str, value: Value) {
    if let Some(object) = column.as_object_mut() {
        object.insert(key.to_string(), value);
    }
}

/// Java 的 id 进 IN 列表前是 `String.valueOf(x)`，null 会变成字面量 "null"。
fn id_of(value: Option<&Value>) -> String {
    match value {
        None | Some(Value::Null) => "null".to_string(),
        Some(Value::String(text)) => text.clone(),
        Some(other) => other.to_string(),
    }
}

fn field(columns: &[Value], column: usize, is_table: bool, position: usize) -> Value {
    let name = if is_table {
        "tableFieldList"
    } else {
        "customFieldList"
    };
    columns
        .get(column)
        .and_then(|row| row.get(name))
        .and_then(Value::as_array)
        .and_then(|items| items.get(position))
        .cloned()
        .unwrap_or(Value::Null)
}

fn field_id(
    columns: &[Value],
    column: usize,
    is_table: bool,
    position: usize,
    key: &str,
) -> String {
    let value = field(columns, column, is_table, position);
    id_of(value.get(key))
}

fn put_field(
    columns: &mut [Value],
    column: usize,
    is_table: bool,
    position: usize,
    key: &str,
    value: Value,
) {
    let name = if is_table {
        "tableFieldList"
    } else {
        "customFieldList"
    };
    let Some(items) = columns
        .get_mut(column)
        .and_then(|row| row.get_mut(name))
        .and_then(Value::as_array_mut)
    else {
        return;
    };
    if let Some(item) = items.get_mut(position).and_then(Value::as_object_mut) {
        item.insert(key.to_string(), value);
    }
}

/// Java: JSON.parseArray(fieldMapString, LinkTableField.class)；解析不了就是异常（500）。
fn parse_field_map(raw: &str) -> Result<Vec<Value>, String> {
    let parsed: Value = serde_json::from_str(raw)
        .map_err(|err| format!("field_map_string 不是合法 JSON 数组: {err}"))?;
    let items = parsed
        .as_array()
        .ok_or_else(|| "field_map_string 不是 JSON 数组".to_string())?;
    Ok(items.iter().map(link_field).collect())
}

fn link_field(item: &Value) -> Value {
    let mut out = Map::new();
    for key in LINK_FIELD_KEYS {
        let raw = item.get(*key).cloned().unwrap_or(Value::Null);
        let value = match raw {
            Value::Null => Value::Null,
            Value::String(text) if LINK_LONG_KEYS.contains(key) => match text.trim().parse::<i64>()
            {
                Ok(number) => json!(number),
                Err(_) => Value::Null,
            },
            other if !LINK_LONG_KEYS.contains(key) => match other {
                Value::Number(number) => json!(number.to_string()),
                Value::Bool(flag) => json!(flag.to_string()),
                other => other,
            },
            other => other,
        };
        out.insert((*key).to_string(), value);
    }
    // getCustomFileComment 有 "" 兜底，序列化时永不为 null
    if out
        .get("customFileComment")
        .map(|v| v.is_null())
        .unwrap_or(true)
    {
        out.insert("customFileComment".to_string(), json!(""));
    }
    Value::Object(out)
}

fn reorder(row: &Value, order: &[&str]) -> Value {
    let Some(source) = row.as_object() else {
        return row.clone();
    };
    let mut out = Map::with_capacity(source.len());
    for key in order {
        if let Some(value) = source.get(*key) {
            out.insert((*key).to_string(), value.clone());
        }
    }
    for (key, value) in source {
        out.entry(key.clone()).or_insert_with(|| value.clone());
    }
    Value::Object(out)
}

/// Java: StringUtils.stringToList —— 逗号切分，空串得空列表（service 层再 return null）
fn split_ids(raw: &str) -> Vec<String> {
    raw.split(',')
        .map(str::trim)
        .filter(|item| !item.is_empty())
        .map(str::to_string)
        .collect()
}

/// Java: GenTableColumnMapper.selectGenTableColumnListByTableColumnIds
/// （列片段顺序照抄 XML —— 6 个关联列在最前；`order by sort`；无 table_id 过滤）
async fn select_columns_by_ids(pool: &MySqlPool, ids: &[String]) -> Result<Value, String> {
    if ids.is_empty() {
        return Ok(Value::Null);
    }
    let mut builder = QueryBuilder::<MySql>::new(format!(
        "select {} from gen_table_column where column_id in (",
        gen::DIALOG_COLUMN_COLUMNS
    ));
    let mut separated = builder.separated(", ");
    for id in ids {
        separated.push_bind(id.clone());
    }
    builder.push(") order by sort");
    let rows = builder
        .build()
        .fetch_all(pool)
        .await
        .map_err(|err| err.to_string())?;
    Ok(Value::Array(
        crate::db::rows::rows_to_json(&rows)
            .iter()
            .filter_map(Value::as_object)
            .map(gen::shape_column)
            .collect(),
    ))
}

async fn columns_by_id(pool: &MySqlPool, ids: &[String]) -> Result<HashMap<String, Value>, String> {
    let mut out = HashMap::new();
    let Value::Array(rows) = select_columns_by_ids(pool, ids).await? else {
        return Ok(out);
    };
    for row in rows {
        let key = id_of(row.get("columnId"));
        out.insert(key, row);
    }
    Ok(out)
}

/// Java: genTableMapper.selectGenTableById(linkTableId) 后紧跟 setPkColumn(linkTable)。
/// 走 mapper，不经过 setTableFromOptions，也不做字典/关联加工。
async fn select_link_table(pool: &MySqlPool, table_id: &Value) -> Result<Value, String> {
    let id = id_of(Some(table_id));
    let Some(row) = sqlx::query(&format!(
        "select {} from gen_table where table_id = ?",
        gen::INFO_COLUMNS
    ))
    .bind(&id)
    .fetch_optional(pool)
    .await
    .map_err(|err| err.to_string())?
    else {
        // Java: selectGenTableById 返回 null 后 setPkColumn(null) 抛 NPE -> 500
        return Err(format!("关联表不存在: table_id={id}"));
    };
    let mut table = crate::db::rows::row_to_json(&row);
    let columns = gen::select_columns(pool, &id)
        .await
        .map_err(|err| err.to_string())?;
    let pk = gen_render::pk_column(&columns);
    gen::finish_gen_table_row(&mut table, Some(columns));
    put(&mut table, "pkColumn", pk.unwrap_or(Value::Null));
    Ok(table)
}
