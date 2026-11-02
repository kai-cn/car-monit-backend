#pragma once
// 对应 Java: com.ruoyi.common.exception.*
//
// Java 的异常层级：
//   RuntimeException
//     ├── BaseException (message / code / data)
//     │     ├── ServiceException
//     │     ├── CustomException
//     │     └── UserException → CaptchaException / CaptchaExpireException / ...
//     └── DemoModeException
// C++ 侧用标准异常 + what() 复刻；GlobalExceptionHandler 负责映射到 AjaxResult。
#include <exception>
#include <optional>
#include <string>

#include "cm/common/utils/JsonUtils.hpp"

namespace cm::exception {

class BaseException : public std::exception {
public:
    explicit BaseException(std::string message) : message_(std::move(message)) {}
    BaseException(std::string message, int code) : message_(std::move(message)), code_(code) {}
    BaseException(std::string message, int code, Json data)
        : message_(std::move(message)), code_(code), data_(std::move(data)) {}

    const char* what() const noexcept override { return message_.c_str(); }
    const std::string& getMessage() const { return message_; }
    const std::optional<int>& getCode() const { return code_; }
    const std::optional<Json>& getData() const { return data_; }

protected:
    std::string message_;
    std::optional<int> code_;
    std::optional<Json> data_;
};

class ServiceException : public BaseException {
public:
    explicit ServiceException(std::string message) : BaseException(std::move(message)) {}
    ServiceException(std::string message, int code) : BaseException(std::move(message), code) {}
    ServiceException(std::string message, int code, Json data)
        : BaseException(std::move(message), code, std::move(data)) {}
};

class CustomException : public BaseException {
public:
    explicit CustomException(std::string message) : BaseException(std::move(message)) {}
    CustomException(std::string message, int code) : BaseException(std::move(message), code) {}
};

/** Java NullPointerException：GlobalExceptionHandler 输出 {"msg":null,"code":500} */
class NullPointerException : public std::exception {
public:
    const char* what() const noexcept override { return "null"; }
};

/** Spring Security AccessDeniedException -> AjaxResult(403, "没有权限，请联系管理员授权") */
class AccessDeniedException : public std::exception {
public:
    explicit AccessDeniedException(std::string message = "Access Denied")
        : message_(std::move(message)) {}
    const char* what() const noexcept override { return message_.c_str(); }

private:
    std::string message_;
};

/** HttpRequestMethodNotSupportedException */
class HttpRequestMethodNotSupportedException : public std::exception {
public:
    explicit HttpRequestMethodNotSupportedException(std::string method)
        : message_("Request method '" + method + "' not supported") {}
    const char* what() const noexcept override { return message_.c_str(); }

private:
    std::string message_;
};

/** MethodArgumentTypeMismatchException：对应 Spring 的错误文本 */
class MethodArgumentTypeMismatchException : public std::exception {
public:
    MethodArgumentTypeMismatchException(std::string name, std::string required_type, std::string value)
        : message_("请求参数类型不匹配，参数[" + name + "]要求类型为：'" + required_type + "'，但输入值为：'" +
                   value + "'") {}
    const char* what() const noexcept override { return message_.c_str(); }

private:
    std::string message_;
};

/** MissingPathVariableException（本项目实际很少触发，仅占位） */
class MissingPathVariableException : public std::exception {
public:
    explicit MissingPathVariableException(std::string name)
        : message_("请求路径中缺少必需的路径变量[" + name + "]") {}
    const char* what() const noexcept override { return message_.c_str(); }

private:
    std::string message_;
};

class DemoModeException : public std::exception {
public:
    const char* what() const noexcept override { return "演示模式，不允许操作"; }
};

// ------------------------- 用户相关异常（消息来自 i18n/messages） -------------------------
class UserException : public BaseException {
public:
    explicit UserException(std::string message) : BaseException(std::move(message)) {}
};

class CaptchaException : public UserException {
public:
    CaptchaException() : UserException("验证码错误") {}
};

class CaptchaExpireException : public UserException {
public:
    CaptchaExpireException() : UserException("验证码已失效") {}
};

class UserNotExistsException : public UserException {
public:
    UserNotExistsException() : UserException("用户不存在/密码错误") {}
};

class UserPasswordNotMatchException : public UserException {
public:
    UserPasswordNotMatchException() : UserException("用户不存在/密码错误") {}
};

class UserPasswordRetryLimitExceedException : public UserException {
public:
    explicit UserPasswordRetryLimitExceedException(int retryLimitCount, int lockTime = 10)
        : UserException("密码输入错误" + std::to_string(retryLimitCount) + "次，帐户锁定" +
                        std::to_string(lockTime) + "分钟") {}
};

class BlackListException : public UserException {
public:
    BlackListException() : UserException("很遗憾，访问IP已被列入系统黑名单") {}
};

class UserBlockedException : public UserException {
public:
    UserBlockedException() : UserException("用户已封禁，请联系管理员") {}
};

class RoleBlockedException : public UserException {
public:
    RoleBlockedException() : UserException("角色已封禁，请联系管理员") {}
};

// ------------------------- 文件 / 工具异常 -------------------------
class FileException : public BaseException {
public:
    explicit FileException(std::string message) : BaseException(std::move(message)) {}
};

class FileSizeLimitExceededException : public FileException {
public:
    FileSizeLimitExceededException(long long sizeLimitMb)
        : FileException("上传的文件大小超出限制的文件大小！<br/>允许的文件最大大小是：" +
                        std::to_string(sizeLimitMb) + "MB！") {}
};

class FileNameLengthLimitExceededException : public FileException {
public:
    FileNameLengthLimitExceededException(int lengthLimit)
        : FileException("上传的文件名最长" + std::to_string(lengthLimit) + "个字符") {}
};

class InvalidExtensionException : public FileException {
public:
    InvalidExtensionException(std::string extension, std::string allowedExtension)
        : FileException("文件上传失败，文件名后缀" + extension + "校验失败，实际允许的后缀为：" +
                        allowedExtension) {}
};

class UtilException : public BaseException {
public:
    explicit UtilException(std::string message) : BaseException(std::move(message)) {}
};

class TaskException : public BaseException {
public:
    explicit TaskException(std::string message) : BaseException(std::move(message)) {}
};

// JSON 解析失败（对应 Jackson 的 JsonParseException）
class JsonParseException : public BaseException {
public:
    explicit JsonParseException(std::string message) : BaseException(std::move(message)) {}
};

} // namespace cm::exception
