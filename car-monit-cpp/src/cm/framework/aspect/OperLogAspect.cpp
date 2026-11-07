// 对应 Java: LogAspect + AsyncManager/AsyncFactory.recordOper + SysOperLogMapper.insertOperlog
#include "cm/framework/aspect/OperLogAspect.hpp"

#include <algorithm>
#include <map>

#include "cm/common/utils/IdUtils.hpp"
#include "cm/common/utils/JavaCollections.hpp"
#include "cm/common/utils/Logger.hpp"
#include "cm/framework/db/Db.hpp"
#include "cm/framework/security/SecurityUtils.hpp"
#include "cm/framework/web/Router.hpp"

namespace cm::aspect {

const std::vector<std::string> kExcludeProperties = {
    "password", "oldPassword", "newPassword", "confirmPassword"};

namespace {

bool excluded(const std::string& key, const std::vector<std::string>& extra) {
    if (std::find(kExcludeProperties.begin(), kExcludeProperties.end(), key) != kExcludeProperties.end()) {
        return true;
    }
    return std::find(extra.begin(), extra.end(), key) != extra.end();
}

std::vector<std::string> segments(const std::string& path) {
    std::vector<std::string> out;
    std::string cur;
    for (char c : path) {
        if (c == '/') {
            if (!cur.empty()) out.push_back(cur);
            cur.clear();
        } else {
            cur.push_back(c);
        }
    }
    if (!cur.empty()) out.push_back(cur);
    return out;
}

/** Spring 的 AntPathMatcher 在 {var} 上只吃一个路径段 */
bool patternMatch(const std::string& pattern, const std::string& path) {
    const auto ps = segments(pattern);
    const auto vs = segments(path);
    if (ps.size() != vs.size()) return false;
    for (size_t i = 0; i < ps.size(); ++i) {
        if (!ps[i].empty() && ps[i].front() == '{') continue;
        if (ps[i] == "**") continue;
        if (ps[i] != vs[i]) return false;
    }
    return true;
}

bool hasVarSegment(const std::string& pattern) {
    return pattern.find('{') != std::string::npos;
}

/** 原始请求 URI（不含 query）：对应 HttpServletRequest#getRequestURI()，保持未解码形态 */
std::string rawUri(const cm::http::HttpRequest& req) {
    const std::string& t = req.target.empty() ? req.path : req.target;
    size_t q = t.find('?');
    std::string uri = q == std::string::npos ? t : t.substr(0, q);
    // 绝对形式（代理请求）时取 path 部分
    if (uri.rfind("http://", 0) == 0 || uri.rfind("https://", 0) == 0) {
        size_t p = uri.find('/', 8);
        uri = p == std::string::npos ? "/" : uri.substr(p);
    }
    return uri;
}

/** 对应 fastjson2 `JSON.toJSONString(...)`。两种顺序必须分开：
 *  * pojoFieldOrder=true —— **POJO**：fastjson2 的对象写出器按字段名排序
 *      （实测 2.0.43：声明序 zzUuid/lon/middle/… 打出来是 countNum,directionIn,emptyStr,lon,nested,zzUuid），
 *      而 nlohmann 的 ordered_json 保留插入序 ⇒ 这里显式排一次。
 *  * pojoFieldOrder=false —— **Map**（AjaxResult extends HashMap、paramMap 那些）：
 *      照插入序输出，调用方自己负责把键摆成 Java 容器的那个顺序。
 *  ⚠️ 递归时沿用同一档：混着来的那处（jsonResult 里 data 挂 POJO）本来就只对了外层。 */
Json compactJson(const Json& v, const std::vector<std::string>& extra, bool pojoFieldOrder) {
    if (v.is_object()) {
        std::vector<std::pair<std::string, Json>> items;
        for (auto it = v.begin(); it != v.end(); ++it) {
            if (it->is_null() || excluded(it.key(), extra)) continue;
            items.emplace_back(it.key(), compactJson(*it, extra, pojoFieldOrder));
        }
        if (pojoFieldOrder) {
            // Java 的比较器是 String.compareTo（UTF-16 code unit）；UTF-8 字节序对纯 ASCII 键
            // 完全一致，字段名不会有非 ASCII，所以不再单独解码。
            std::sort(items.begin(), items.end(),
                      [](const std::pair<std::string, Json>& a,
                         const std::pair<std::string, Json>& b) { return a.first < b.first; });
        }
        Json o = Json::object();
        for (auto& kv : items) o[kv.first] = std::move(kv.second);
        return o;
    }
    if (v.is_array()) {
        Json a = Json::array();
        for (const auto& e : v) a.push_back(compactJson(e, extra, pojoFieldOrder));
        return a;
    }
    return v;
}

} // namespace

std::string subAtMost(const std::string& s, size_t chars) {
    size_t i = 0;
    size_t n = 0;
    while (i < s.size() && n < chars) {
        const unsigned char c = static_cast<unsigned char>(s[i]);
        size_t len = 1;
        if ((c >> 5) == 0x6) len = 2;
        else if ((c >> 4) == 0xE) len = 3;
        else if ((c >> 3) == 0x1E) len = 4;
        if (i + len > s.size()) break;  // 末尾半截的不切断
        i += len;
        ++n;
    }
    return s.substr(0, i);
}

std::string realAddressByIP(const std::string& ip) {
    // ruoyi.addressEnabled=false：内网 -> 内网IP，其它 -> XX XX（不发起外部请求）
    if (cm::utils::internalIp(ip)) return "内网IP";
    return "XX XX";
}

std::string fastJsonCompact(const Json& value, const std::vector<std::string>& excludes,
                            bool pojoFieldOrder) {
    return compactJson(value, excludes, pojoFieldOrder).dump();
}

bool paramMapEmpty(const cm::http::HttpRequest& req) {
    return req.query_params.empty() && req.form_params.empty();
}

std::string paramMapJson(const cm::http::HttpRequest& req, const std::vector<std::string>& excludes) {
    // ServletUtils.getParamMap：同名多值用 ',' 连接；容器是 HashMap -> 输出按桶序
    std::map<std::string, std::string, std::less<>> merged;
    std::vector<std::string> keys;
    auto add = [&](const std::pair<std::string, std::string>& kv) {
        auto it = merged.find(kv.first);
        if (it == merged.end()) {
            merged.emplace(kv.first, kv.second);
            keys.push_back(kv.first);
        } else {
            it->second += "," + kv.second;
        }
    };
    for (const auto& kv : req.query_params) add(kv);
    for (const auto& kv : req.form_params) add(kv);

    Json j = Json::object();
    for (const auto& k : cm::utils::javaMapOrder(keys)) {
        if (excluded(k, excludes)) continue;
        j[k] = merged[k];
    }
    return j.dump();
}

std::string OperLogRow::toInsertSql() const {
    using cm::db::Db;
    return "insert into sys_oper_log(title, business_type, method, request_method, operator_type,"
           " oper_name, dept_name, oper_url, oper_ip, oper_location, oper_param, json_result,"
           " status, error_msg, oper_time)"
           " values (" +
           Db::lit(title) + ", " + Db::lit(businessType) + ", " + Db::lit(method) + ", " +
           Db::lit(requestMethod) + ", " + Db::lit(operatorType) + ", " + Db::lit(operName) + ", " +
           Db::lit(deptName) + ", " + Db::lit(operUrl) + ", " + Db::lit(operIp) + ", " +
           Db::lit(operLocation) + ", " + Db::lit(operParam) + ", " + Db::lit(jsonResult) + ", " +
           Db::lit(status) + ", " + Db::lit(errorMsg) + ", sysdate())";
}

std::optional<OperLogRow> OperLogAspect::build(const cm::http::HttpRequest& req,
                                               const cm::http::ApiResponse& resp,
                                               const Failure* failure,
                                               const LogRule& rule) {
    // Java: SecurityUtils.getLoginUser() 在没有登录态时抛 CustomException，被 handleLog 的
    // catch(Exception) 吞掉 -> 整行不写。这里等价处理。
    auto lu = cm::security::SecurityUtils::current();
    if (!lu) return std::nullopt;

    OperLogRow row;
    row.status = failure ? 1 : 0;  // BusinessStatus.SUCCESS.ordinal()=0 / FAIL.ordinal()=1
    row.operIp = cm::utils::ipAddr(req.remote_addr, req.getHeader("x-forwarded-for"),
                                   req.getHeader("proxy-client-ip"),
                                   req.getHeader("wl-proxy-client-ip"), req.getHeader("x-real-ip"));
    row.operUrl = subAtMost(rawUri(req), 255);
    row.operName = lu->user.userName;  // LoginUser.getUsername() -> user.getUserName()
    if (lu->user.dept && lu->user.dept->deptName) row.deptName = lu->user.dept->deptName;
    row.title = rule.title;
    row.businessType = rule.businessType;
    row.operatorType = rule.operatorType;
    row.method = rule.classMethod;
    row.requestMethod = req.method;
    if (failure && failure->message) row.errorMsg = subAtMost(*failure->message, 2000);

    if (rule.saveRequest) {
        // setRequestValue：参数表为空且是 PUT/POST -> 序列化方法入参；否则序列化参数表
        std::string param;
        if (paramMapEmpty(req) && (req.method == "PUT" || req.method == "POST")) {
            if (req.getHeader("content-type").find("multipart/") != std::string::npos) {
                // ⚠️ Java 的 isFilterObject 会跳过 MultipartFile、只留下其余标量入参；
                //    C++ 侧不掌握方法签名，上传类接口统一记空串。
                param = "";
            } else if (!req.body.empty()) {
                try {
                    Json parsed = Json::parse(req.body, nullptr, false);
                    param = parsed.is_discarded() ? req.body : fastJsonCompact(parsed, rule.excludeParamNames);
                } catch (...) {
                    param = req.body;
                }
            }
        } else {
            param = paramMapJson(req, rule.excludeParamNames);
        }
        row.operParam = subAtMost(param, 2000);
    }

    if (rule.saveResponse && failure == nullptr && !resp.body.empty() &&
        resp.content_type.find("json") != std::string::npos) {
        // 正常返回才有 jsonResult；@AfterThrowing 分支 Java 不传 jsonResult
        try {
            Json parsed = Json::parse(resp.body, nullptr, false);
            if (!parsed.is_discarded()) {
                row.jsonResult = subAtMost(fastJsonCompact(parsed, rule.excludeParamNames), 2000);
            }
        } catch (...) {
        }
    }

    row.operLocation = realAddressByIP(row.operIp.value_or(""));
    return row;
}

// ---- 单例与后台线程 ----

OperLogAspect& OperLogAspect::instance() {
    static OperLogAspect inst;
    return inst;
}

void OperLogAspect::start() {
    std::lock_guard<std::mutex> lk(mu_);
    if (running_) return;
    running_ = true;
    th_ = std::thread([this] { worker(); });
}

void OperLogAspect::stop() {
    {
        std::lock_guard<std::mutex> lk(mu_);
        if (!running_) return;
        running_ = false;
    }
    cv_.notify_all();
    if (th_.joinable()) th_.join();
}

void OperLogAspect::worker() {
    for (;;) {
        OperLogRow row;
        {
            std::unique_lock<std::mutex> lk(mu_);
            cv_.wait(lk, [this] { return !queue_.empty() || !running_; });
            if (queue_.empty()) {
                if (!running_) return;  // 停机时已排空
                continue;
            }
            row = queue_.front();
            queue_.pop_front();
        }
        flushOne(row);
    }
}

void OperLogAspect::flushOne(const OperLogRow& row) {
    // Java 的切面整体包在 try/catch 里：记日志失败只打本地错误，绝不影响业务响应
    try {
        std::string sql = row.toInsertSql();
        if (!cm::db::Db::instance().execute(sql)) {
            LOG_ERROR("OperLogAspect", "写入 sys_oper_log 失败: " + subAtMost(sql, 240));
        }
    } catch (const std::exception& e) {
        LOG_ERROR("OperLogAspect", std::string("写入 sys_oper_log 异常: ") + e.what());
    } catch (...) {
        LOG_ERROR("OperLogAspect", "写入 sys_oper_log 异常");
    }
}

void OperLogAspect::record(const cm::web::RequestContext& ctx, const cm::http::ApiResponse& resp,
                           const Failure* failure) {
    try {
        const LogRule* rule = matchLogRule(ctx.req.method, ctx.req.path);
        if (!rule) return;
        auto row = build(ctx.req, resp, failure, *rule);
        if (!row) return;
        std::lock_guard<std::mutex> lk(mu_);
        if (!running_) return;
        // 有界队列：宁可丢日志也不能把 worker 堆爆（Java 的 timer 队列无界，属于不可移植点）
        if (queue_.size() >= 50000) {
            LOG_ERROR("OperLogAspect", "操作日志队列已满，丢弃一条");
            return;
        }
        queue_.push_back(*row);
        cv_.notify_one();
    } catch (const std::exception& e) {
        LOG_ERROR("OperLogAspect", std::string("记录操作日志异常: ") + e.what());
    } catch (...) {
        LOG_ERROR("OperLogAspect", "记录操作日志异常");
    }
}

const LogRule* matchLogRule(const std::string& httpMethod, const std::string& path) {
    // Spring 的 RequestMappingHandlerMapping 按"字面量优先于 {var}"挑选映射，
    // 这里两趟：先精确字面量，再带路径变量的模式（否则 /monitor/job/clean 会被 /{jobIds} 抢走）
    const LogRule* fuzzy = nullptr;
    for (const auto& r : logRules()) {
        if (r.http != httpMethod) continue;
        if (!patternMatch(r.pattern, path)) continue;
        if (!hasVarSegment(r.pattern)) return &r;
        if (fuzzy == nullptr) fuzzy = &r;
    }
    return fuzzy;
}

} // namespace cm::aspect
