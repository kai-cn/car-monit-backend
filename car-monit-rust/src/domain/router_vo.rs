// 来源: ruoyi-system/src/main/java/com/ruoyi/system/domain/vo/RouterVo.java
//       ruoyi-system/src/main/java/com/ruoyi/system/domain/vo/MetaVo.java
// 职责: /getRouters 返回的前端路由树。
// 对应关系: RouterVo 类级 @JsonInclude(NON_EMPTY) -> skip None/空串/空列表；
//           MetaVo 无注解，null 字段照常输出。

use serde::{Deserialize, Serialize};

fn is_none_or_empty_string(value: &Option<String>) -> bool {
    value.as_ref().is_none_or(|s| s.is_empty())
}

fn is_none_or_empty_children(value: &Option<Vec<RouterVo>>) -> bool {
    value.as_ref().is_none_or(|v| v.is_empty())
}

/// Java: `@JsonInclude(JsonInclude.Include.NON_EMPTY)`，字段声明顺序即输出顺序。
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", default)]
pub struct RouterVo {
    #[serde(skip_serializing_if = "is_none_or_empty_string")]
    pub name: Option<String>,
    #[serde(skip_serializing_if = "is_none_or_empty_string")]
    pub path: Option<String>,
    /// primitive boolean：始终输出。
    pub hidden: bool,
    #[serde(skip_serializing_if = "is_none_or_empty_string")]
    pub redirect: Option<String>,
    #[serde(skip_serializing_if = "is_none_or_empty_string")]
    pub component: Option<String>,
    #[serde(skip_serializing_if = "is_none_or_empty_string")]
    pub query: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub always_show: Option<bool>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub meta: Option<MetaVo>,
    #[serde(skip_serializing_if = "is_none_or_empty_children")]
    pub children: Option<Vec<RouterVo>>,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", default)]
pub struct MetaVo {
    pub title: Option<String>,
    pub icon: Option<String>,
    /// Java: `isNoCache()` -> noCache
    pub no_cache: bool,
    pub link: Option<String>,
}

impl MetaVo {
    /// Java: `new MetaVo(title, icon, noCache)`（link 保持 null）。
    pub fn new(title: Option<String>, icon: Option<String>, no_cache: bool) -> Self {
        Self {
            title,
            icon,
            no_cache,
            link: None,
        }
    }

    /// Java: `new MetaVo(title, icon, noCache, link)` —— link 仅 http(s) 开头才保留。
    pub fn with_link(
        title: Option<String>,
        icon: Option<String>,
        no_cache: bool,
        link: Option<String>,
    ) -> Self {
        let link = link.filter(|value| {
            value.starts_with(crate::common::constants::HTTP)
                || value.starts_with(crate::common::constants::HTTPS)
        });
        Self {
            title,
            icon,
            no_cache,
            link,
        }
    }
}
