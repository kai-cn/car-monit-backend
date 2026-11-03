#pragma once
// spec 驱动的通用 CRUD —— 对应 Java 侧 MyBatis-Plus BaseMapper + RuoYi Generator 模板
//
// 为什么要这一层：Java 项目里 60 多个控制器是 RuoYi 代码生成器产出的同构 CRUD
// （list / export / getInfo / add / edit / remove + 一个 ServiceImpl 转发 + 一份
//  Mapper XML）。逐条手写 C++ 会产出上万行高度重复、且容易抄错 SQL 的代码。
// 这里把 “XML 里有什么” 变成数据（Field/Spec），由引擎统一翻译成 SQL + JSON，
// 每个实体只需要一份 spec 描述（由 scripts/gen_crud_spec.py 从 Java/XML 抽取）。
//
// 语义对齐要点（与 Java 逐条对拍过）：
//   * 查询条件来自 Mapper XML 的 <if test="x != null and x != ''"> —— 空串不进入 WHERE
//   * 插入/更新走 MyBatis-Plus BaseMapper.insert/updateById：只写 **非 null** 字段
//   * @TableId(type=INPUT) 表示主键由业务侧提供，不自增
//   * 分页由 PageHelper 拦截器完成：只有 pageNum 与 pageSize 同时存在才分页
//   * 日期字段的 JSON 形态由 @JsonFormat 决定，没有注解时是 Jackson 默认的 ISO-8601
#include <functional>
#include <string>
#include <vector>

#include "cm/common/utils/JsonUtils.hpp"
#include "cm/framework/db/Row.hpp"
#include "cm/framework/web/Router.hpp"

namespace cm::web::crud {

/** JSON 输出形态（对应 Java 字段类型 + @JsonFormat） */
enum class Fmt {
    Str,      ///< String / 文本 -> "xxx"，NULL -> null
    Int,      ///< Integer / Long -> 数字，NULL -> null
    Long,
    Double,   ///< Double / BigDecimal -> 数字
    Bool,     ///< Boolean / tinyint(1)
    DateYmd,        ///< @JsonFormat("yyyy-MM-dd")
    DateYmdHms,     ///< @JsonFormat("yyyy-MM-dd HH:mm:ss")
    DateIso,        ///< 无 @JsonFormat 的 java.util.Date（Jackson 默认 ISO-8601 + 时区）
    DateTimeIso,    ///< 同上，带时间
};

/** WHERE 条件形态（对应 XML 里的 <if>） */
enum class Cond {
    None,        ///< 不作为查询条件
    Eq,          ///< and t.col = #{field}（值为 null 或空串都跳过，XML 常见写法）
    EqNotNull,   ///< and t.col = #{field}（只判 null，空串也算条件）
    Like,        ///< and t.col like concat('%', #{field}, '%')
    DateRange,   ///< 需要携带 DateRangeStyle；使用 params.beginTime / params.endTime
    FindInSet,   ///< and find_in_set(#{field}, t.col)（祖级列表 ancestors 常见）
    FindInSetCol,///< and find_in_set(t.col, #{field})（列在第一个参数，如 exceptIds）
};

/** params.beginTime / endTime 的比较粒度（对应 XML 里的 date_format 格式串） */
enum class RangeStyle {
    DayYyyymmdd,   ///< date_format(col,'%Y%m%d')
    MonthYyyymm,   ///< date_format(col,'%Y%m')
    Raw,           ///< col >= #{params.beginTime} 直接比较
};

struct Field {
    const char* json;   ///< Java/JSON 字段名，如 "agentPk"
    const char* column; ///< 数据库列名，如 "agent_pk"
    Fmt fmt{Fmt::Str};
    Cond cond{Cond::None};
    const char* excel{nullptr};  ///< @Excel(name=...)；nullptr 表示不参与导出
    bool pk{false};
    bool autoIncrement{false};   ///< @TableId(type=IdType.AUTO)
    bool insertable{true};       ///< 生成的列不参与 INSERT/UPDATE（如 MP 的 fill 字段）
    bool updatable{true};
    /** 仅作为 WHERE 左值的列名覆盖：XML 里条件列与该属性的取值列不同时用
     *  （如 find_in_set(t.id, #{exceptIds}) —— 拿主键去匹配传入的 csv） */
    const char* condColumn{nullptr};
    /** 非列属性（column==nullptr）在 Java 里的字段初始值，写成 JSON 字面量，
     *  如 "\"0\"" / "0" / "false" / "[]"。Jackson 会把它照样输出，所以不能退化成 null。 */
    const char* dflt{nullptr};
};

/** 每个动作的 @PreAuthorize 权限串（nullptr 表示 Java 侧没有 @PreAuthorize） */
struct Perms {
    const char* list{nullptr};
    const char* exportList{nullptr};
    const char* query{nullptr};
    const char* add{nullptr};
    const char* edit{nullptr};
    const char* remove{nullptr};
};

/** 实体级钩子：Java 里 controller/service 的个性化处理用小函数补齐，
 *  而不是为每个实体手写整个 handler */
struct Hooks {
    /** 查询前：注入 tenantId / dataScope 之类的强制条件 */
    std::function<void(RequestContext&, Json& query)> beforeQuery;
    /** 插入前：补主键（UUID）、createBy、tenantId 等 */
    std::function<void(RequestContext&, Json& body)> beforeInsert;
    /** 更新前 */
    std::function<void(RequestContext&, Json& body)> beforeUpdate;
    /** 行 -> JSON 之后的字段级修补（例如派生 getter） */
    std::function<void(Json& row, const cm::db::Row& raw)> afterRow;
};

struct Spec {
    const char* table;                 ///< "dwd_lczt_sfsjcxx"
    std::vector<Field> fields;
    std::string alias{"t"};             ///< XML 里普遍用 "FROM tbl t"
    std::string orderBy;               ///< "order by t.create_time desc"（不含关键字）
    std::string fromSql;               ///< 覆盖 "FROM tbl t"（join 场景）
    std::string extraWhere;            ///< 固定附加条件，如 "and t.del_flag = '0'"
    RangeStyle rangeStyle{RangeStyle::DayYyyymmdd};
    const char* rangeColumn{nullptr};  ///< DateRange 对应的列，通常是 create_time
    Hooks hooks;
    /** 导出文件名（Java: util.exportExcel(list, "收费所基础信息数据")） */
    std::string excelSheetName;
    /** 软删除列（如 sys_user.del_flag）；为空表示物理删除 */
    std::string softDeleteColumn;

    std::string pkColumn() const;
    std::string pkJson() const;
    bool pkIsString() const;
    /** selectVo 列清单：<sql id="selectXxxVo"> 的等价物 */
    std::string selectColumns() const;
};

// ---- 可复用的构件（单测直接覆盖这些纯函数） ----

/** 单行 -> JSON，字段顺序 = fields 声明顺序（对应 Jackson 按字段声明序输出） */
Json rowToJson(const Spec& spec, const cm::db::Row& row);

/** 依据查询参数拼 WHERE 片段（对应 XML 的 <if> 集合） */
std::string buildWhere(const Spec& spec, const Json& query);

/** JSON body -> INSERT 语句（只含非 null 列，对应 MP insert） */
std::string buildInsert(const Spec& spec, const Json& body);

/** JSON body -> UPDATE 语句（只含非 null 且 updatable 的列，WHERE 用主键） */
std::string buildUpdate(const Spec& spec, const Json& body);

/** 把 HTTP query 参数收集成实体形态的 Json（Spring 的参数绑定） */
Json bindQuery(const Spec& spec, RequestContext& ctx);

/** 主键字面量：字符串列加引号，数字列不加 */
std::string pkLiteral(const Spec& spec, const std::string& raw);

// ---- 注册 ----

/**
 * 注册 6 个标准动作，路径与 Java 完全一致：
 *   GET  <base>/list            GET <base>/export        GET <base>/{pkVar}
 *   POST <base>                 PUT  <base>              DELETE <base>/{pkVar}
 * @param pkVar @PathVariable 的变量名（Java 里可能是 agentPk / id / xxxId）
 */
void registerCrud(Router& router, const std::string& base, const Spec& spec, const Perms& perms,
                  const std::string& pkVar = "id");

/**
 * 注册一个“list 的变体路径”，对应 Java 控制器里那些复制粘贴出来的
 * /listAll、/listQuery、/listnew 等方法。kind 决定返回形态：
 *   Paged   —— startPage() + getDataTable(list)（与 /list 一致）
 *   Plain   —— 不分页，AjaxResult.success(list)（Java 里常见于 /listQuery）
 *   Counted —— 不分页，但 TableDataInfo(total = 条数)
 */
enum class ListKind { Paged, Plain, Counted };

void registerListVariant(Router& router, const std::string& path, const Spec& spec,
                         ListKind kind, const char* perm = nullptr);

/** 只注册 list + getInfo（部分模块只有查询接口） */
void registerReadOnly(Router& router, const std::string& base, const Spec& spec,
                      const Perms& perms, const std::string& pkVar = "id");

/** 导出：返回 Java 侧 ExcelUtil 的响应形态（data = 文件名） */
cm::http::ApiResponse exportExcel(const Spec& spec, const Json& rows, const std::string& sheetName);

} // namespace cm::web::crud
