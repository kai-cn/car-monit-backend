// 来源: ruoyi-common/src/main/java/com/ruoyi/common/core/page/PageDomain.java
//       ruoyi-common/src/main/java/com/ruoyi/common/core/page/TableSupport.java
//       ruoyi-common/src/main/java/com/ruoyi/common/utils/PageUtils.java
//       ruoyi-common/src/main/java/com/ruoyi/common/utils/sql/SqlUtil.java
// 职责: 分页参数解析、orderBy 拼接与 SQL 注入校验、PageHelper 的 reasonable 语义。
// 对应关系: startPage() + PageDomain -> PageDomain::from_uri/order_by/resolve。

use std::collections::HashMap;

use crate::error::AppError;

pub const PAGE_NUM: &str = "pageNum";
pub const PAGE_SIZE: &str = "pageSize";
pub const ORDER_BY_COLUMN: &str = "orderByColumn";
pub const IS_ASC: &str = "isAsc";
pub const REASONABLE: &str = "reasonable";

/// Java: `SqlUtil.SQL_PATTERN = "[a-zA-Z0-9_\\ \\,\\.]+"`
fn sql_pattern_allowed(c: char) -> bool {
    c.is_ascii_alphanumeric() || matches!(c, '_' | ' ' | ',' | '.')
}

const ORDER_BY_MAX_LENGTH: usize = 500;

#[derive(Debug, Clone)]
pub struct PageDomain {
    pub page_num: i64,
    pub page_size: i64,
    pub order_by_column: Option<String>,
    /// 已按 PageDomain.setIsAsc 归一化：asc / desc
    pub is_asc: String,
    /// Java: getReasonable() —— null 时返回 TRUE
    pub reasonable: bool,
}

impl Default for PageDomain {
    fn default() -> Self {
        Self {
            page_num: 1,
            page_size: 10,
            order_by_column: None,
            is_asc: "asc".to_string(),
            reasonable: true,
        }
    }
}

impl PageDomain {
    /// Java: TableSupport.getPageDomain —— 缺省 pageNum=1、pageSize=10、isAsc=asc、reasonable=true。
    pub fn from_map(params: &HashMap<String, String>) -> Self {
        let page_num = params.get(PAGE_NUM).map(|v| to_int(v, 1)).unwrap_or(1);
        let page_size = params.get(PAGE_SIZE).map(|v| to_int(v, 10)).unwrap_or(10);
        let order_by_column = params
            .get(ORDER_BY_COLUMN)
            .filter(|v| !v.is_empty())
            .cloned();
        let is_asc = match params.get(IS_ASC).map(String::as_str) {
            Some("ascending") => "asc".to_string(),
            Some("descending") => "desc".to_string(),
            Some(v) if !v.is_empty() => v.to_string(),
            _ => "asc".to_string(),
        };
        let reasonable = match params.get(REASONABLE).map(String::as_str) {
            Some("true") | Some("yes") | Some("ok") | Some("1") => true,
            Some("false") | Some("no") | Some("0") => false,
            _ => true,
        };
        Self {
            page_num,
            page_size,
            order_by_column,
            is_asc,
            reasonable,
        }
    }

    /// Servlet 的 `getParameter` 取第一个值；这里等价处理 query string。
    pub fn from_query(query: Option<&str>) -> Self {
        let mut params: HashMap<String, String> = HashMap::new();
        if let Some(query) = query {
            for (key, value) in url::form_urlencoded::parse(query.as_bytes()) {
                params
                    .entry(key.into_owned())
                    .or_insert_with(|| value.into_owned());
            }
        }
        Self::from_map(&params)
    }

    /// Java: PageDomain.getOrderBy() —— column 转下划线后与方向拼接；空列返回空串。
    pub fn order_by(&self) -> String {
        match self.order_by_column.as_deref() {
            Some(column) if !column.is_empty() => {
                format!("{} {}", to_under_score_case(column), self.is_asc)
            }
            _ => String::new(),
        }
    }

    /// Java: SqlUtil.escapeOrderBySql —— 非法字符/超长时由全局异常处理返回 500。
    pub fn escape_order_by_sql(&self) -> Result<String, AppError> {
        let value = self.order_by();
        if !value.is_empty() && !value.chars().all(sql_pattern_allowed) {
            return Err(AppError::Service(
                "参数不符合规范，不能进行查询".to_string(),
            ));
        }
        if value.chars().count() > ORDER_BY_MAX_LENGTH {
            return Err(AppError::Service(
                "参数已超过最大限制，不能进行查询".to_string(),
            ));
        }
        Ok(value)
    }

    /// Java: PageHelper 的 reasonable 语义 + `Page.calculateStartAndEndRow`。
    pub fn resolve(&self, total: i64) -> (i64, i64) {
        let size = self.page_size.max(0);
        let mut page_num = self.page_num;
        if self.reasonable && page_num < 1 {
            page_num = 1;
        }
        let pages = if size > 0 && total > 0 {
            (total + size - 1) / size
        } else {
            0
        };
        if self.reasonable && pages > 0 && page_num > pages {
            page_num = pages;
        }
        let offset = if page_num > 0 {
            (page_num - 1) * size
        } else {
            0
        };
        (offset, size)
    }
}

/// Java: Convert.toInt(String, defaultValue) —— 空串/解析失败回退默认值。
fn to_int(value: &str, default: i64) -> i64 {
    if value.is_empty() {
        return default;
    }
    value.trim().parse::<i64>().unwrap_or(default)
}

/// Java: StringUtils.toUnderScoreCase —— 驼峰转下划线（保持连续大写规则）。
pub fn to_under_score_case(value: &str) -> String {
    let chars: Vec<char> = value.chars().collect();
    let mut out = String::with_capacity(value.len() + 4);
    for (index, current) in chars.iter().enumerate() {
        let previous_upper = if index > 0 {
            chars[index - 1].is_uppercase()
        } else {
            false
        };
        let current_upper = current.is_uppercase();
        let next_upper = if index + 1 < chars.len() {
            chars[index + 1].is_uppercase()
        } else {
            // Java 的 nexteCharIsUpperCase 只在 i < len-1 时更新，
            // 最后一个字符保留上一轮的值（即当前字符自身的上一轮判断）。
            current_upper
        };
        if previous_upper && current_upper && !next_upper {
            out.push('_');
        } else if index != 0 && !previous_upper && current_upper {
            out.push('_');
        }
        out.extend(current.to_lowercase());
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn order_by_matches_java_underscore_rules() {
        assert_eq!(to_under_score_case("userName"), "user_name");
        assert_eq!(to_under_score_case("deptId"), "dept_id");
        assert_eq!(to_under_score_case("ABC"), "abc");
        assert_eq!(to_under_score_case("createTime"), "create_time");
        assert_eq!(to_under_score_case("snapshottime"), "snapshottime");
    }

    #[test]
    fn defaults_and_direction_normalization() {
        let page = PageDomain::from_query(Some("pageNum=2&pageSize=20&isAsc=descending"));
        assert_eq!(page.page_num, 2);
        assert_eq!(page.page_size, 20);
        assert_eq!(page.is_asc, "desc");
        assert!(page.reasonable);

        let page = PageDomain::from_query(Some("orderByColumn=createTime"));
        assert_eq!(page.order_by(), "create_time asc");
    }

    #[test]
    fn escape_rejects_injection() {
        let page = PageDomain::from_map(&HashMap::from([(
            "orderByColumn".to_string(),
            "a;drop table x".to_string(),
        )]));
        assert!(page.escape_order_by_sql().is_err());
    }

    #[test]
    fn reasonable_clamps_to_last_page() {
        let page = PageDomain::from_query(Some("pageNum=9&pageSize=10"));
        assert_eq!(page.resolve(35), (30, 10));
        let page = PageDomain::from_query(Some("pageNum=0&pageSize=10"));
        assert_eq!(page.resolve(35), (0, 10));
        let page = PageDomain::from_query(Some("pageNum=1&pageSize=10&reasonable=false"));
        assert_eq!(page.resolve(35), (0, 10));
    }
}
