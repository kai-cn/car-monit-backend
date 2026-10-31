// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/common/CaptchaController.java
// 职责: GET /captchaImage —— 生成并缓存验证码，返回 uuid + base64 图片。
// 对应关系: getCode(HttpServletResponse) -> captcha_image。

use std::time::Duration;

use axum::extract::State;
use base64::Engine;

use crate::api::captcha_image;
use crate::common::constants::{CAPTCHA_CODE_KEY, CAPTCHA_EXPIRATION};
use crate::common::utils::simple_uuid;
use crate::error::AppError;
use crate::response::AjaxResult;
use crate::state::AppState;

pub async fn get_code(State(state): State<AppState>) -> Result<AjaxResult, AppError> {
    let uuid = simple_uuid();
    let verify_key = format!("{CAPTCHA_CODE_KEY}{uuid}");

    // Java: captchaType = math | char
    let (display, code) = match state.settings.ruoyi.captcha_type.as_str() {
        "math" => {
            let text = captcha_image::math_text();
            // Java: capText.substring(0, lastIndexOf("@")) / substring(lastIndexOf("@") + 1)
            let index = text
                .rfind('@')
                .ok_or_else(|| AppError::internal("验证码文本缺少分隔符"))?;
            (text[..index].to_string(), text[index + 1..].to_string())
        }
        "char" => {
            let code = captcha_image::char_text(4);
            (code.clone(), code)
        }
        other => {
            // Java 中 image 为 null，ImageIO.write 抛异常 -> 500
            return Err(AppError::internal(format!("不支持的验证码类型: {other}")));
        }
    };

    // Java: redisCache.setCacheObject(verifyKey, code, 2, TimeUnit.MINUTES)
    state
        .redis
        .set_object_ttl(
            &verify_key,
            &code,
            Some(Duration::from_secs(CAPTCHA_EXPIRATION * 60)),
        )
        .await?;

    let image = captcha_image::render(&display)?;
    let img = base64::engine::general_purpose::STANDARD.encode(image);

    Ok(AjaxResult::success().put("uuid", uuid).put("img", img))
}
