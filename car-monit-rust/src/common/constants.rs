// 来源: ruoyi-common/src/main/java/com/ruoyi/common/constant/Constants.java
//       ruoyi-common/src/main/java/com/ruoyi/common/constant/CacheConstants.java
// 职责: 常量逐值对齐，避免散落魔法字符串。

/// Java: Constants.TOKEN
pub const TOKEN: &str = "token";
/// Java: Constants.TOKEN_PREFIX
pub const TOKEN_PREFIX: &str = "Bearer ";
/// Java: Constants.LOGIN_USER_KEY
pub const LOGIN_USER_KEY: &str = "login_user_key";
/// Java: Constants.LOGIN_TOKEN_KEY
pub const LOGIN_TOKEN_KEY: &str = "login_tokens:";
/// Java: Constants.CAPTCHA_CODE_KEY
pub const CAPTCHA_CODE_KEY: &str = "captcha_codes:";
/// Java: Constants.CAPTCHA_EXPIRATION = 2 分钟
pub const CAPTCHA_EXPIRATION: u64 = 2;
/// Java: Constants.ALL_PERMISSION
pub const ALL_PERMISSION: &str = "*:*:*";
/// Java: Constants.SUPER_ADMIN
pub const SUPER_ADMIN: &str = "admin";
/// Java: Constants.LOGIN_SUCCESS
pub const LOGIN_SUCCESS: &str = "Success";
/// Java: Constants.LOGIN_FAIL
pub const LOGIN_FAIL: &str = "Error";
/// Java: Constants.LOGOUT
pub const LOGOUT: &str = "Logout";
/// Java: Constants.SUCCESS = "0"
pub const SUCCESS: &str = "0";
/// Java: Constants.FAIL = "1"
pub const FAIL: &str = "1";
/// Java: CacheConstants.PWD_ERR_CNT_KEY
pub const PWD_ERR_CNT_KEY: &str = "pwd_err_cnt:";
/// Java: Constants.HTTP
pub const HTTP: &str = "http://";
/// Java: Constants.HTTPS
pub const HTTPS: &str = "https://";

// UserConstants
/// Java: UserConstants.NO_FRAME = "1"
pub const NO_FRAME: &str = "1";
/// Java: UserConstants.YES_FRAME = "0"
pub const YES_FRAME: &str = "0";
/// Java: UserConstants.TYPE_DIR = "M"
pub const TYPE_DIR: &str = "M";
/// Java: UserConstants.TYPE_MENU = "C"
pub const TYPE_MENU: &str = "C";
/// Java: UserConstants.LAYOUT = "Layout"
pub const LAYOUT: &str = "Layout";
/// Java: UserConstants.PARENT_VIEW = "ParentView"
pub const PARENT_VIEW: &str = "ParentView";
