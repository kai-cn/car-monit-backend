// 来源: ruoyi-common/src/main/java/com/ruoyi/common/utils/poi/ExcelUtil.java
//       RuoYiConfig.getDownloadPath()
// 职责: 导出 xlsx 到 profile/download，并返回文件名（AjaxResult.success(filename)）。
// 对应关系: ExcelUtil.exportExcel(list, sheetName) -> export_workbook。
//
// Java 用 POI 写工作簿；这里用 rust_xlsxwriter（`excel` feature，默认开启）。
// 单元格格式差异：Java 的 @Excel(dateFormat/readConverterExp) 逐实体迁移，
// 本函数只负责「表头 + 单元格值」的机械写入。

use std::path::PathBuf;

use serde_json::Value;

use crate::error::AppError;

/// Java: RuoYiConfig.getDownloadPath() = profile + "/download/"
pub fn download_dir(profile: &str) -> PathBuf {
    PathBuf::from(profile).join("download")
}

/// Java: ExcelUtil.encodingFilename —— UUID + "_" + sheetName + ".xlsx"
pub fn encode_filename(sheet_name: &str) -> String {
    format!("{}_{}.xlsx", uuid::Uuid::new_v4(), sheet_name)
}

/// Java: ExcelUtil.exportExcel(list, sheetName) —— 写文件并返回文件名。
pub fn export_workbook(
    profile: &str,
    sheet_name: &str,
    headers: &[String],
    rows: &[Vec<Value>],
) -> Result<String, AppError> {
    let filename = encode_filename(sheet_name);
    let dir = download_dir(profile);
    std::fs::create_dir_all(&dir).map_err(|err| {
        AppError::Service(format!("导出Excel失败，请联系网站管理员！创建目录失败: {err}"))
    })?;
    let path = dir.join(&filename);

    write_xlsx(&path, sheet_name, headers, rows)
        .map_err(|err| AppError::Service(format!("导出Excel失败，请联系网站管理员！{err}")))?;
    Ok(filename)
}

#[cfg(feature = "excel")]
fn write_xlsx(
    path: &std::path::Path,
    sheet_name: &str,
    headers: &[String],
    rows: &[Vec<Value>],
) -> Result<(), Box<dyn std::error::Error>> {
    use rust_xlsxwriter::{Format, Workbook};

    let mut workbook = Workbook::new();
    let sheet_name = sanitize_sheet_name(sheet_name);
    let worksheet = workbook.add_worksheet();
    worksheet.set_name(&sheet_name)?;

    // Java: createHeadCell —— 表头加粗、灰底、居中。
    let header_format = Format::new()
        .set_bold()
        .set_background_color(rust_xlsxwriter::Color::RGB(0xD9E1F2))
        .set_align(rust_xlsxwriter::FormatAlign::Center);
    for (col, header) in headers.iter().enumerate() {
        worksheet.write_string_with_format(0, col as u16, header, &header_format)?;
    }

    for (row_index, row) in rows.iter().enumerate() {
        let excel_row = (row_index + 1) as u32;
        for (col, value) in row.iter().enumerate() {
            write_cell(worksheet, excel_row, col as u16, value)?;
        }
    }
    workbook.save(path)?;
    Ok(())
}

#[cfg(feature = "excel")]
fn write_cell(
    worksheet: &mut rust_xlsxwriter::Worksheet,
    row: u32,
    col: u16,
    value: &Value,
) -> Result<(), rust_xlsxwriter::XlsxError> {
    match value {
        Value::Null => {
            worksheet.write_blank(row, col, &rust_xlsxwriter::Format::new())?;
        }
        Value::Bool(flag) => {
            worksheet.write_boolean(row, col, *flag)?;
        }
        Value::Number(number) => {
            if let Some(value) = number.as_f64() {
                worksheet.write_number(row, col, value)?;
            } else {
                worksheet.write_string(row, col, number.to_string())?;
            }
        }
        Value::String(text) => {
            worksheet.write_string(row, col, text)?;
        }
        other => {
            worksheet.write_string(row, col, other.to_string())?;
        }
    };
    Ok(())
}

#[cfg(not(feature = "excel"))]
fn write_xlsx(
    _path: &std::path::Path,
    _sheet_name: &str,
    _headers: &[String],
    _rows: &[Vec<Value>],
) -> Result<(), Box<dyn std::error::Error>> {
    Err("编译时未启用 excel feature".into())
}

/// Java: `ExcelUtil.importExcel(inputStream, clazz)` 的读取部分 —— 第一张工作表按行展开为文本。
#[cfg(feature = "excel")]
pub fn read_rows(bytes: &[u8]) -> Result<Vec<Vec<String>>, AppError> {
    use calamine::{open_workbook_auto_from_rs, Reader};
    use std::io::Cursor;

    let cursor = Cursor::new(bytes.to_vec());
    let mut workbook = open_workbook_auto_from_rs(cursor)
        .map_err(|err| AppError::Service(format!("读取Excel失败: {err}")))?;
    let Some(Ok(range)) = workbook.worksheet_range_at(0) else {
        return Ok(Vec::new());
    };
    let mut rows = Vec::new();
    for row in range.rows() {
        rows.push(row.iter().map(cell_text).collect());
    }
    Ok(rows)
}

#[cfg(feature = "excel")]
fn cell_text(cell: &calamine::Data) -> String {
    match cell {
        calamine::Data::Empty => String::new(),
        calamine::Data::String(text) => text.clone(),
        calamine::Data::Float(value) => {
            if value.fract() == 0.0 {
                format!("{}", *value as i64)
            } else {
                value.to_string()
            }
        }
        calamine::Data::Int(value) => value.to_string(),
        calamine::Data::Bool(value) => value.to_string(),
        calamine::Data::DateTime(value) => value.to_string(),
        calamine::Data::DateTimeIso(text) | calamine::Data::DurationIso(text) => text.clone(),
        calamine::Data::Error(err) => format!("{err:?}"),
    }
}

#[cfg(not(feature = "excel"))]
pub fn read_rows(_bytes: &[u8]) -> Result<Vec<Vec<String>>, AppError> {
    Err(AppError::Service("编译时未启用 excel feature".to_string()))
}

/// POI 的 sheet 名限制：不能含 []:*?/\，最长 31 字符。
fn sanitize_sheet_name(name: &str) -> String {    let cleaned: String = name
        .chars()
        .map(|ch| match ch {
            '[' | ']' | ':' | '*' | '?' | '/' | '\\' => '_',
            other => other,
        })
        .take(31)
        .collect();
    if cleaned.is_empty() {
        "Sheet1".to_string()
    } else {
        cleaned
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn filename_matches_java_shape() {
        let name = encode_filename("服务区判定规则数据");
        assert!(name.ends_with("_服务区判定规则数据.xlsx"));
        // UUID 36 字符 + 下划线
        assert_eq!(name.find('_').unwrap(), 36);
    }

    #[test]
    fn sheet_name_is_sanitized() {
        assert_eq!(sanitize_sheet_name("a/b:c"), "a_b_c");
        assert_eq!(sanitize_sheet_name(""), "Sheet1");
    }
}
