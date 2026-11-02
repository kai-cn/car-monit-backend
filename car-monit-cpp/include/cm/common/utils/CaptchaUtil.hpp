#pragma once
// 对应 Java: Kaptcha（com.google.code.kaptcha）+ CaptchaController
//
// ⚠️ 差异：Java 用 ImageIO 写 **JPEG**，C++ 侧写 **PNG**（无第三方图像库）。
//    前端以 data URI 展示、内容由浏览器嗅探，视觉与交互一致；字节必然不同。
#include <string>

namespace cm::utils {

struct Captcha {
    std::string text;  // 形如 "3*5=?" 的展示文本
    std::string code;  // 校验码（算术结果）
};

class CaptchaUtil {
public:
    /** 对应 KaptchaTextCreator.getText()：返回 "a?b=?@result" 的拆分结果 */
    static Captcha randomMath();
    /** 随机字符验证码（captchaType=char） */
    static Captcha randomChar(int length);
    /** 渲染 PNG（160x60，绿色边框、蓝色文字） */
    static std::string renderPng(const std::string& text, int width = 160, int height = 60);
    static std::string base64(const std::string& data);
};

} // namespace cm::utils
