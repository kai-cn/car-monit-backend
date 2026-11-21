// 来源: ruoyi-common/src/main/java/com/ruoyi/common/filter/XssFilter.java
//       ruoyi-common/src/main/java/com/ruoyi/common/utils/html/HTMLFilter.java
// 职责: 复刻 Java 的 XSS 过滤器：对 POST/PUT 的 JSON body 与参数值做 HTML 清洗。
// 对应关系: XssFilter/XssHttpServletRequestWrapper -> xss_middleware；HTMLFilter -> clean_html。
// 说明: Rust regex 不支持 lookahead/backreference，`HTMLFilter.balanceHTML` 对「孤立 >」与
//       `encodeQuotes` 的极端分支未逐字节复刻；注释/标签剥离、白名单标签与属性、协议校验、
//       缺闭合标签补齐、空标签删除均按 Java 默认配置实现。

use std::collections::HashMap;
use std::sync::LazyLock;

use axum::body::{Body, Bytes};
use axum::extract::{Request, State};
use axum::http::header::{CONTENT_LENGTH, CONTENT_TYPE};
use axum::http::{HeaderValue, Method};
use axum::middleware::Next;
use axum::response::Response;
use regex::Regex;

use crate::state::AppState;

/// Java: `spring.servlet.multipart.max-request-size: 200MB`。
const MAX_BODY_BYTES: usize = 200 * 1024 * 1024;

/// Java: `HTMLFilter` 默认允许的标签。
const ALLOWED_TAGS: &[&str] = &["a", "img", "b", "strong", "i", "em"];
/// Java: `vNeedClosingTags`。
const NEED_CLOSING_TAGS: &[&str] = &["a", "b", "strong", "i", "em"];
/// Java: `vAllowedProtocols`。
const ALLOWED_PROTOCOLS: &[&str] = &["http", "mailto", "https"];

struct BlankPatterns {
    pair: Regex,
    self_blank: Regex,
}

/// Java: `processRemoveBlanks` —— 删除 `<b></b>` / `<b />` 这类空标签。
static REMOVE_BLANKS: LazyLock<Vec<BlankPatterns>> = LazyLock::new(|| {
    NEED_CLOSING_TAGS
        .iter()
        .map(|tag| BlankPatterns {
            pair: Regex::new(&format!("<{tag}(\\s[^>]*)?></{tag}>"))
                .expect("valid blank pair regex"),
            self_blank: Regex::new(&format!("<{tag}(\\s[^>]*)?/>"))
                .expect("valid blank self regex"),
        })
        .collect()
});

/// Java: `XssFilter.doFilter` —— 逐请求清洗 JSON body 与 query 参数。
pub async fn xss_middleware(
    State(state): State<AppState>,
    mut request: Request,
    next: Next,
) -> Response {
    if !state.settings.xss.enabled {
        return next.run(request).await;
    }
    let method = request.method().clone();
    let path = request.uri().path().to_string();
    if method == Method::GET || method == Method::DELETE || !xss_applies(&state, &path) {
        return next.run(request).await;
    }

    // Java: `XssHttpServletRequestWrapper.getParameterValues` —— 参数值 clean + trim。
    if let Some(query) = request.uri().query() {
        let cleaned = clean_query(query);
        if let Some(uri) = rebuild_uri(request.uri(), &cleaned) {
            *request.uri_mut() = uri;
        }
    }

    // Java: `getInputStream` —— 仅 application/json 清洗整个 body 并 trim。
    let content_type = request
        .headers()
        .get(CONTENT_TYPE)
        .and_then(|value| value.to_str().ok())
        .unwrap_or_default()
        .to_ascii_lowercase();
    if content_type.starts_with("application/json") {
        let (mut parts, body) = request.into_parts();
        let bytes = axum::body::to_bytes(body, MAX_BODY_BYTES)
            .await
            .unwrap_or_else(|_| Bytes::new());
        let cleaned = clean_html(&String::from_utf8_lossy(&bytes))
            .trim()
            .to_string();
        if let Ok(length) = HeaderValue::from_str(&cleaned.len().to_string()) {
            parts.headers.insert(CONTENT_LENGTH, length);
        }
        request = Request::from_parts(parts, Body::from(cleaned));
    }

    next.run(request).await
}

fn xss_applies(state: &AppState, path: &str) -> bool {
    if state
        .settings
        .xss
        .excludes
        .split(',')
        .map(str::trim)
        .filter(|item| !item.is_empty())
        .any(|pattern| ant_match(pattern, path))
    {
        return false;
    }
    state
        .settings
        .xss
        .url_patterns
        .split(',')
        .map(str::trim)
        .filter(|item| !item.is_empty())
        .any(|pattern| servlet_prefix_match(pattern, path))
}

/// Java: `FilterRegistrationBean.addUrlPatterns` 的 servlet 语义：`/system/*` 匹配全部子路径。
fn servlet_prefix_match(pattern: &str, path: &str) -> bool {
    if let Some(prefix) = pattern.strip_suffix("/*") {
        path == prefix || path.starts_with(&format!("{prefix}/"))
    } else {
        pattern == path
    }
}

/// Java: `StringUtils.isMatch` 的 AntPathMatcher 子集（绝对路径、* 单段、** 任意段）。
fn ant_match(pattern: &str, path: &str) -> bool {
    let pattern = pattern.trim_matches('/');
    let path = path.trim_matches('/');
    let pattern: Vec<&str> = pattern.split('/').filter(|item| !item.is_empty()).collect();
    let path: Vec<&str> = path.split('/').filter(|item| !item.is_empty()).collect();
    ant_segments(&pattern, &path)
}

fn ant_segments(pattern: &[&str], path: &[&str]) -> bool {
    match pattern.split_first() {
        None => path.is_empty(),
        Some((first, rest)) if *first == "**" => {
            ant_segments(rest, path) || (!path.is_empty() && ant_segments(pattern, &path[1..]))
        }
        Some((first, rest)) => match path.split_first() {
            Some((segment, tail)) if *first == "*" || first == segment => ant_segments(rest, tail),
            _ => false,
        },
    }
}

fn clean_query(query: &str) -> String {
    let mut serializer = url::form_urlencoded::Serializer::new(String::new());
    for (key, value) in url::form_urlencoded::parse(query.as_bytes()) {
        serializer.append_pair(&key, clean_html(&value).trim());
    }
    serializer.finish()
}

fn rebuild_uri(uri: &axum::http::Uri, query: &str) -> Option<axum::http::Uri> {
    let path = uri.path();
    let rebuilt = if query.is_empty() {
        path.to_string()
    } else {
        format!("{path}?{query}")
    };
    rebuilt.parse().ok()
}

/// Java: `EscapeUtil.clean` -> `new HTMLFilter().filter(input)`。
pub fn clean_html(input: &str) -> String {
    let mut out = String::with_capacity(input.len());
    let mut counts: HashMap<&'static str, usize> = HashMap::new();
    let mut index = 0;

    while index < input.len() {
        let rest = &input[index..];
        let Some(offset) = rest.find('<') else {
            out.push_str(rest);
            break;
        };
        out.push_str(&rest[..offset]);
        index += offset;

        let after = &input[index + 1..];
        // Java: `escapeComments` + `checkTags` 的净效果是整段注释被丢弃。
        if after.starts_with("!--") {
            match after.find("-->") {
                Some(end) => index += 1 + end + 3,
                None => break,
            }
            continue;
        }

        let next_lt = after.find('<');
        let Some(gt) = after
            .find('>')
            .filter(|end| next_lt.is_none_or(|lt| *end < lt))
        else {
            // Java: `balanceHTML` 把没有闭合 `>` 的 `<` 转义。
            out.push_str("&lt;");
            index += 1;
            continue;
        };
        process_tag(&after[..gt], &mut out, &mut counts);
        index += 1 + gt + 1;
    }

    for tag in NEED_CLOSING_TAGS {
        let count = counts.get(tag).copied().unwrap_or(0);
        for _ in 0..count {
            out.push_str(&format!("</{tag}>"));
        }
    }
    remove_blank_tags(out)
}

fn process_tag(content: &str, out: &mut String, counts: &mut HashMap<&'static str, usize>) {
    let content = content.trim();
    if let Some(rest) = content.strip_prefix('/') {
        let (name, _) = take_name(rest);
        let name = name.to_ascii_lowercase();
        if let Some(allowed) = allowed_tag(&name) {
            if !NEED_CLOSING_TAGS.contains(&allowed) {
                return;
            }
            if let Some(count) = counts.get_mut(allowed) {
                if *count > 0 {
                    *count -= 1;
                    out.push_str(&format!("</{allowed}>"));
                }
            }
        }
        return;
    }

    let (name, rest) = take_name(content);
    let name = name.to_ascii_lowercase();
    let Some(allowed) = allowed_tag(&name) else {
        return;
    };

    let mut tag = format!("<{allowed}");
    for (attr, value) in parse_attrs(rest) {
        if !attr_allowed(allowed, &attr) {
            continue;
        }
        let value = if attr == "href" || attr == "src" {
            process_protocol(&value)
        } else {
            value
        };
        // Java 输出 `attr=\"value\"`：反斜杠保证写回 JSON 文本后仍是合法字符串。
        tag.push(' ');
        tag.push_str(&attr);
        tag.push_str("=\\\"");
        tag.push_str(&value);
        tag.push_str("\\\"");
    }

    if NEED_CLOSING_TAGS.contains(&allowed) {
        *counts.entry(allowed).or_insert(0) += 1;
    } else if allowed == "img" || rest.trim_end().ends_with('/') {
        tag.push_str(" /");
    }
    tag.push('>');
    out.push_str(&tag);
}

fn take_name(content: &str) -> (String, &str) {
    let end = content
        .char_indices()
        .take_while(|(_, ch)| ch.is_ascii_alphanumeric())
        .last()
        .map(|(index, ch)| index + ch.len_utf8())
        .unwrap_or(0);
    (content[..end].to_string(), &content[end..])
}

fn allowed_tag(name: &str) -> Option<&'static str> {
    ALLOWED_TAGS.iter().copied().find(|tag| *tag == name)
}

fn attr_allowed(tag: &str, attr: &str) -> bool {
    match tag {
        "a" => matches!(attr, "href" | "target"),
        "img" => matches!(attr, "src" | "width" | "height" | "alt"),
        _ => false,
    }
}

fn parse_attrs(content: &str) -> Vec<(String, String)> {
    let mut attrs = Vec::new();
    let mut index = 0;
    while index < content.len() {
        let rest = &content[index..];
        let Some(offset) = rest.find(|ch: char| ch.is_ascii_alphanumeric()) else {
            break;
        };
        index += offset;
        let (name, tail) = take_name(&content[index..]);
        index += name.len();
        let Some(eq) = tail.find('=') else {
            continue;
        };
        if !tail[..eq].chars().all(char::is_whitespace) {
            continue;
        }
        let after_eq = &tail[eq + 1..];
        let value_start = after_eq
            .char_indices()
            .find(|(_, ch)| !ch.is_whitespace())
            .map(|(idx, _)| idx);
        let Some(value_start) = value_start else {
            break;
        };
        index += eq + 1 + value_start;
        let rest = &content[index..];
        let (value, consumed) = if let Some(quote @ ('"' | '\'')) = rest.chars().next() {
            let body = &rest[1..];
            match body.find(quote) {
                Some(end) => (body[..end].to_string(), 1 + end + 1),
                None => (body.to_string(), rest.len()),
            }
        } else {
            let end = rest
                .char_indices()
                .find(|(_, ch)| ch.is_whitespace() || *ch == '/' || *ch == '>')
                .map(|(idx, _)| idx)
                .unwrap_or(rest.len());
            (rest[..end].to_string(), end)
        };
        index += consumed;
        attrs.push((name.to_ascii_lowercase(), value));
    }
    attrs
}

fn process_protocol(value: &str) -> String {
    let Some(colon) = value.find(':') else {
        return value.to_string();
    };
    let protocol = &value[..colon];
    if ALLOWED_PROTOCOLS.contains(&protocol) {
        return value.to_string();
    }
    let mut result = format!("#{}", &value[colon + 1..]);
    if result.starts_with("#//") {
        result = format!("#{}", &result[3..]);
    }
    result
}

fn remove_blank_tags(mut value: String) -> String {
    for patterns in REMOVE_BLANKS.iter() {
        value = patterns.pair.replace_all(&value, "").to_string();
        value = patterns.self_blank.replace_all(&value, "").to_string();
    }
    value
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn script_tags_are_removed_and_text_kept() {
        assert_eq!(clean_html("<script>alert(1)</script>"), "alert(1)");
    }

    #[test]
    fn allowed_tags_and_attributes_survive() {
        assert_eq!(clean_html("<b>bold</b>"), "<b>bold</b>");
        assert_eq!(clean_html("<b onclick=x>bold</b>"), "<b>bold</b>");
        assert_eq!(clean_html("<img src=x onerror=y>"), "<img src=\\\"x\\\" />");
        assert_eq!(
            clean_html("<a href='javascript:1'>x</a>"),
            "<a href=\\\"#1\\\">x</a>"
        );
    }

    #[test]
    fn comments_and_stray_brackets_follow_java() {
        assert_eq!(clean_html("<!--x-->a"), "a");
        assert_eq!(clean_html("a < b"), "a &lt; b");
        assert_eq!(clean_html("<b></b>"), "");
        assert_eq!(clean_html("<b>open"), "<b>open</b>");
    }
}
