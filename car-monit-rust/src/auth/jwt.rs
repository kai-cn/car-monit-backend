// 来源: ruoyi-framework/src/main/java/com/ruoyi/framework/web/service/TokenService.java
//       io.jsonwebtoken 0.9.1 的签名/解析行为
// 职责: JWT 签发与解析，兼容 Java 生成的令牌。
// 对应关系: createToken(claims)/parseToken -> create_token/parse_token。

use jsonwebtoken::{Algorithm, DecodingKey, EncodingKey, Header, Validation};
use serde::{Deserialize, Serialize};

use crate::common::constants::LOGIN_USER_KEY;
use crate::error::AppError;

/// Java TokenService 只放一个 claim：login_user_key（UUID）。
#[derive(Debug, Serialize, Deserialize)]
struct Claims {
    #[serde(default)]
    login_user_key: Option<String>,
}

pub struct JwtService {
    encoding: EncodingKey,
    decoding: DecodingKey,
}

impl JwtService {
    /// Java: `signWith(SignatureAlgorithm.HS512, secret)`。
    /// jjwt 0.9.1 用 `TextCodec.BASE64.decode(secret)`，底层是 JAXB 的
    /// `DatatypeConverter.parseBase64Binary`（与 `Base64.getDecoder()` 不同）。
    /// jsonwebtoken 的 `from_base64_secret` 既要求填充又与 JAXB 结果不一致，
    /// 因此这里手写等价解码器。
    pub fn new(secret: &str) -> Result<Self, AppError> {
        let key_bytes = decode_java_base64(secret)?;
        let encoding = EncodingKey::from_secret(&key_bytes);
        let decoding = DecodingKey::from_secret(&key_bytes);
        Ok(Self { encoding, decoding })
    }

    /// Java: `Jwts.builder().setClaims(claims).signWith(HS512, secret).compact()`
    pub fn create_token(&self, uuid: &str) -> Result<String, AppError> {
        let claims = Claims {
            login_user_key: Some(uuid.to_string()),
        };
        jsonwebtoken::encode(&Header::new(Algorithm::HS512), &claims, &self.encoding)
            .map_err(|e| AppError::internal(format!("生成令牌失败: {e}")))
    }

    /// Java: `Jwts.parser().setSigningKey(secret).parseClaimsJws(token).getBody()`
    /// Java 令牌没有 exp claim，因此关闭 jsonwebtoken 默认的 exp 必填校验。
    pub fn parse_token(&self, token: &str) -> Result<String, AppError> {
        let mut validation = Validation::new(Algorithm::HS512);
        validation.required_spec_claims.clear();
        validation.validate_exp = false;
        let data = jsonwebtoken::decode::<Claims>(token, &self.decoding, &validation)
            .map_err(|e| AppError::Unauthorized(format!("令牌解析失败: {e}")))?;
        data.claims
            .login_user_key
            .ok_or_else(|| AppError::Unauthorized(format!("令牌缺少 {LOGIN_USER_KEY}")))
    }
}

/// jjwt 0.9.1 在 Java 8 上使用 JAXB `DatatypeConverter.parseBase64Binary`：
/// 标准字母表、忽略空白；只解码完整的 4 字符组，**没有填充时丢弃尾部不完整组**
/// （默认 secret 26 字符因此解出 18 字节），有 '=' 填充时才输出尾部字节。
/// 已用 jjwt 0.9.1 + JDK 1.8.0_202 实测确认。
fn decode_java_base64(secret: &str) -> Result<Vec<u8>, AppError> {
    fn value(c: u8) -> Option<u32> {
        match c {
            b'A'..=b'Z' => Some((c - b'A') as u32),
            b'a'..=b'z' => Some((c - b'a') as u32 + 26),
            b'0'..=b'9' => Some((c - b'0') as u32 + 52),
            b'+' => Some(62),
            b'/' => Some(63),
            _ => None,
        }
    }

    let cleaned: Vec<u8> = secret
        .bytes()
        .filter(|c| !c.is_ascii_whitespace())
        .collect();
    let padded = cleaned.contains(&b'=');
    let chars: Vec<u8> = cleaned.into_iter().take_while(|c| *c != b'=').collect();

    let mut values = Vec::with_capacity(chars.len());
    for byte in chars {
        values.push(value(byte).ok_or_else(|| {
            AppError::internal(format!(
                "token.secret 不是合法 Base64: 非法字符 {}",
                byte as char
            ))
        })?);
    }

    let full_groups = values.len() / 4;
    // 无填充时 JAXB 丢弃不完整组；1 字符的尾组无论如何都不产出字节。
    let usable = if padded {
        values.len()
    } else {
        full_groups * 4
    };

    let mut out = Vec::with_capacity(usable * 3 / 4);
    for group in values[..usable].chunks(4) {
        out.push(((group[0] << 2) | (group[1] >> 4)) as u8);
        if group.len() > 2 {
            out.push(((group[1] << 4) | (group[2] >> 2)) as u8);
        }
        if group.len() > 3 {
            out.push(((group[2] << 6) | group[3]) as u8);
        }
    }

    if out.is_empty() {
        return Err(AppError::internal(
            "token.secret 不是合法 Base64: 解码结果为空".to_string(),
        ));
    }
    Ok(out)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn java_base64_decoding_matches_jaxb() {
        // jjwt 0.9.1 + JDK 1.8.0_202 实测：26 字符无填充解出 18 字节，
        // 末尾不完整组被 JAXB 丢弃。
        let key = decode_java_base64("abcdefghijklmnopqrstuvwxyz").expect("decode");
        assert_eq!(key.len(), 18);
        assert_eq!(
            key,
            vec![
                0x69, 0xb7, 0x1d, 0x79, 0xf8, 0x21, 0x8a, 0x39, 0x25, 0x9a, 0x7a, 0x29, 0xaa, 0xbb,
                0x2d, 0xba, 0xfc, 0x31
            ]
        );
        // 有 '=' 填充时尾部字节会被输出。
        assert_eq!(decode_java_base64("YWJjZA==").expect("decode"), b"abcd");
        assert_eq!(decode_java_base64("YWJjZA").expect("decode"), b"abc");
    }

    #[test]
    fn round_trip_with_java_style_secret() {
        // application.yml 默认 secret，jjwt 0.9.1 按 Base64 解释。
        let jwt = JwtService::new("abcdefghijklmnopqrstuvwxyz").expect("jwt");
        let token = jwt
            .create_token("2f1c9a7e-0000-0000-0000-000000000000")
            .expect("token");
        assert_eq!(
            jwt.parse_token(&token).expect("parse"),
            "2f1c9a7e-0000-0000-0000-000000000000"
        );
    }

    #[test]
    fn header_is_hs512() {
        let jwt = JwtService::new("abcdefghijklmnopqrstuvwxyz").expect("jwt");
        let token = jwt.create_token("raw-uuid").expect("token");
        let header = jsonwebtoken::decode_header(&token).expect("header");
        assert_eq!(header.alg, Algorithm::HS512);
    }

    #[test]
    fn tampered_token_is_rejected() {
        let jwt = JwtService::new("abcdefghijklmnopqrstuvwxyz").expect("jwt");
        let token = jwt.create_token("raw-uuid").expect("token");
        let mut tampered = token.clone();
        tampered.push('x');
        assert!(jwt.parse_token(&tampered).is_err());
    }
}
