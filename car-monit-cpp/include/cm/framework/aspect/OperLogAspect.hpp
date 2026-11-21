#pragma once
// 对应 Java: com.ruoyi.framework.aspectj.LogAspect（@Log 切面）
//           + com.ruoyi.framework.manager.AsyncManager / factory.AsyncFactory.recordOper
//
// Java 侧凡是标注了 @Log 的控制器方法，返回或抛异常后都会异步插一行 sys_oper_log。
// 规则表由 scripts/gen_operlog_table.py 从 Java 源码抽取，落在 src/cm/web/specs/OperLogTable.cpp。
#include <condition_variable>
#include <deque>
#include <mutex>
#include <optional>
#include <string>
#include <thread>
#include <vector>

#include "cm/common/utils/JsonUtils.hpp"
#include "cm/framework/http/HttpRequest.hpp"
#include "cm/framework/http/HttpResponse.hpp"

namespace cm::web {
class RequestContext;
}

namespace cm::aspect {

/** 一条 @Log 注解 */
struct LogRule {
    std::string http;             // GET/POST/PUT/DELETE
    std::string pattern;          // Java 路径模式，{var} 吃一个路径段
    std::string title;            // @Log.title
    long long businessType{0};    // BusinessType.ordinal()：OTHER0 INSERT1 UPDATE2 DELETE3
                                  // GRANT4 EXPORT5 IMPORT6 FORCE7 GENCODE8 CLEAN9
    long long operatorType{1};    // OperatorType.ordinal()：OTHER0 MANAGE1 MOBILE2（默认 MANAGE）
    bool saveRequest{true};       // isSaveRequestData
    bool saveResponse{true};      // isSaveResponseData
    std::vector<std::string> excludeParamNames;
    std::string classMethod;      // "com.ruoyi...Controller.export()"
};

const std::vector<LogRule>& logRules();

/** 命中该请求的 @Log 规则；未命中返回 nullptr（等价于该方法没有 @Log，切面不生效） */
const LogRule* matchLogRule(const std::string& httpMethod, const std::string& path);

/** 对应 SysOperLog 中会被 insertOperlog 写出的列 */
struct OperLogRow {
    std::optional<std::string> title;
    long long businessType{0};
    std::optional<std::string> method;
    std::optional<std::string> requestMethod;
    long long operatorType{1};
    std::optional<std::string> operName;
    std::optional<std::string> deptName;
    std::optional<std::string> operUrl;
    std::optional<std::string> operIp;
    std::optional<std::string> operLocation;
    std::optional<std::string> operParam;
    std::optional<std::string> jsonResult;
    long long status{0};  // BusinessStatus.ordinal()：SUCCESS=0 FAIL=1
    std::optional<std::string> errorMsg;

    /** 列名与顺序照抄 SysOperLogMapper.xml 的 insertOperlog，oper_time 用 sysdate() */
    std::string toInsertSql() const;
};

/** @AfterThrowing 分支的异常信息。指针非空即"请求抛异常了"（status=1）；
 *  message 本身可以是 null —— Java 的 NullPointerException#getMessage() 就是 null，
 *  此时 StringUtils.substring(null,0,2000) 仍是 null，error_msg 列写 NULL。 */
struct Failure {
    std::optional<std::string> message;
};

/** StringUtils.substring(s, 0, n)：按字符数截断（不切断 UTF-8 序列） */
std::string subAtMost(const std::string& s, size_t chars);

/** 对应 IpUtils.internalIp + AddressUtils.getRealAddressByIP
 *  （ruoyi.addressEnabled=false，所以只有 内网IP / XX XX 两种结果） */
std::string realAddressByIP(const std::string& ip);

/** 对应 JSON.toJSONString(obj)：fastjson2 默认丢掉 null 值（与 Jackson 的输出相反），
 *  并按 PropertyPreExcludeFilter 排除敏感属性。
 *  pojoFieldOrder：序列化的对象是不是 **POJO**。fastjson2 的对象写出器把字段按名字排序
 *  （实机对拍 2.0.43 确认），而 AjaxResult/paramMap 这类 Map 走的是容器自己的顺序 ——
 *  两种顺序不一样，调用方必须说清楚是哪一种。
 *  ⚠️ @Log 的 operParam 那里拿的是 `joinPoint.getArgs()`，Java 到底是哪种取决于方法签名
 *  （POJO 入参排序、Map 入参不排），这里按老的插入序不动，逐条核过再改。 */
std::string fastJsonCompact(const Json& value, const std::vector<std::string>& excludes,
                            bool pojoFieldOrder = false);

/** 对应 ServletUtils.getParamMap()：值为同名多值按 ',' 拼接的字符串，
 *  键顺序是 Java HashMap 的桶序（不是出现顺序） */
std::string paramMapJson(const cm::http::HttpRequest& req, const std::vector<std::string>& excludes);

/** 请求参数是否非空（对应 StringUtils.isEmpty(paramsMap)） */
bool paramMapEmpty(const cm::http::HttpRequest& req);

/** EXCLUDE_PROPERTIES：Java 侧固定排除的敏感属性 */
extern const std::vector<std::string> kExcludeProperties;

class OperLogAspect {
public:
    static OperLogAspect& instance();

    /** 对应 AsyncManager 的单线程定时器：串行落库，顺序与提交顺序一致 */
    void start();
    /** 停机时排空队列（Java 的 ShutterManager 也是先停接收再等任务跑完） */
    void stop();

    /**
     * 对应 LogAspect.handleLog。
     * failure 非空即 @AfterThrowing 分支（status=1 + error_msg），否则 @AfterReturning。
     * 无登录用户时 Java 的 SecurityUtils.getLoginUser() 会抛异常并被 handleLog 吞掉，
     * 因此整行不会写库 —— 这里等价地不写。
     */
    void record(const cm::web::RequestContext& ctx, const cm::http::ApiResponse& resp,
                const Failure* failure);

    /** 只拼装不落库，供单测使用 */
    static std::optional<OperLogRow> build(const cm::http::HttpRequest& req,
                                           const cm::http::ApiResponse& resp,
                                           const Failure* failure,
                                           const LogRule& rule);

private:
    void worker();
    void flushOne(const OperLogRow& row);

    std::mutex mu_;
    std::condition_variable cv_;
    std::deque<OperLogRow> queue_;
    std::thread th_;
    bool running_{false};
};

} // namespace cm::aspect
