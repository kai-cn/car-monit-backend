// 由 scripts/gen_crud_spec.py 生成（area=base）。
// 重新生成: python scripts/gen_crud_spec.py --area base
//
// 只覆盖同构 CRUD：list / export / getInfo / add / edit / remove。
// 非 CRUD 接口、唯一性校验、tenant 过滤、软删除、外部服务依赖等仍由手写控制器负责
// （src/cm/web/controller/**）。解析不到的控制器整只跳过，见生成器输出。
//
// 每个实体的 Spec 通过 spec<Entity>() 暴露（声明见 BaseCrudSpecs.hpp），
// 手写控制器可以复用同一份列定义，避免把几十个字段再抄一遍。
#include "cm/framework/web/Router.hpp"
#include "cm/framework/web/crud/CrudSpec.hpp"
#include "cm/web/specs/BaseCrudSpecs.hpp"

namespace cm::web::crud {

const Spec& specBaseConfigServiceArea() {
    static const Spec s = [] {
        Spec s;
        s.table = "base_config_service_area";
        s.alias = "t";
        s.fields = {
            {"id", nullptr, Fmt::Str, Cond::Eq, nullptr, false, false, false, false, nullptr},
            {"epsId", nullptr, Fmt::Long, Cond::None, nullptr, false, false, false, false, nullptr},
            {"delFlag", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr},
            {"createBy", nullptr, Fmt::Long, Cond::Eq, nullptr, false, false, false, false, nullptr},
            {"createTime", nullptr, Fmt::DateYmdHms, Cond::None, nullptr, false, false, false, false, nullptr},
            {"updateBy", nullptr, Fmt::Long, Cond::None, nullptr, false, false, false, false, nullptr},
            {"updateTime", nullptr, Fmt::DateYmdHms, Cond::None, nullptr, false, false, false, false, nullptr},
            {"sort", nullptr, Fmt::Int, Cond::None, nullptr, false, false, false, false, nullptr},
            {"tenantId", nullptr, Fmt::Long, Cond::None, nullptr, false, false, false, false, nullptr},
            {"fwqbm", "fwqbm", Fmt::Str, Cond::Eq, "判定进入的服务区编码", false, false, true, true},
            {"fwqmc", "fwqmc", Fmt::Str, Cond::Eq, "判定进入的服务区名称", false, false, true, true},
            {"lon", "lon", Fmt::Str, Cond::Eq, "经度", false, false, true, true},
            {"lat", "lat", Fmt::Str, Cond::Eq, "维度", false, false, true, true},
            {"roadCode", "road_code", Fmt::Str, Cond::Eq, "路线编码", false, false, true, true},
            {"sectionCode", "section_code", Fmt::Str, Cond::Eq, "路段编码", false, false, true, true},
            {"pileNo", "pile_no", Fmt::Str, Cond::Eq, "桩号", false, false, true, true},
        };
        // 父类 BasePlusEntity 声明了 fill = FieldFill.INSERT / UPDATE ⇒ MP 的 MetaObjectHandler
        // 会在 insert 补 create_by/create_time/eps_id，在 update 补 update_by/update_time。
        // 少写这两行，列表接口返回的 updateTime 会停在改之前的旧值。
        s.auditFillInsert = true;
        s.auditFillUpdate = true;
        s.excelSheetName = "服务区";
        return s;
    }();
    return s;
}

const Spec& specCarWarningConfig() {
    static const Spec s = [] {
        Spec s;
        s.table = "car_warning_config";
        s.alias = "t";
        s.fields = {
            {"id", "id", Fmt::Str, Cond::Eq, nullptr, true, false, true, true},
            {"gantryCodeIn", "gantry_code_in", Fmt::Str, Cond::Eq, "进入门架编号", false, false, true, true},
            {"gantryNameIn", "gantry_name_in", Fmt::Str, Cond::Like, "进入门架名称", false, false, true, true},
            {"gantryCodeOut", "gantry_code_out", Fmt::Str, Cond::Eq, "出去门架编号", false, false, true, true},
            {"gantryNameOut", "gantry_name_out", Fmt::Str, Cond::Like, "出去门架名称", false, false, true, true},
            {"timeSpan", "time_span", Fmt::Long, Cond::Eq, "判定时间间隔", false, false, true, true},
            {"fwqbm", "fwqbm", Fmt::Str, Cond::Eq, "判定进入的服务区编码", false, false, true, true},
            {"fwqmc", "fwqmc", Fmt::Str, Cond::Like, "判定进入的服务区名称", false, false, true, true},
            {"lon", "lon", Fmt::Str, Cond::Eq, "经度", false, false, true, true},
            {"lat", "lat", Fmt::Str, Cond::Eq, "维度", false, false, true, true},
            {"roadCode", "road_code", Fmt::Str, Cond::Eq, "路线编码", false, false, true, true},
            {"sectionCode", "section_code", Fmt::Str, Cond::Eq, "路段编码", false, false, true, true},
            {"pileNo", "pile_no", Fmt::Str, Cond::Eq, "桩号", false, false, true, true},
            {"remark", "remark", Fmt::Str, Cond::None, "备注", false, false, true, true},
        };
        s.excelSheetName = "服务区判定规则";
        return s;
    }();
    return s;
}

const Spec& specDwdLcztFwqjcxx() {
    static const Spec s = [] {
        Spec s;
        s.table = "dwd_lczt_fwqjcxx";
        s.alias = "t";
        s.fields = {
            {"agentPk", "agent_pk", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"yxtzj", "yxtzj", Fmt::Str, Cond::Eq, "源系统主键", false, false, true, true},
            {"fwqbm", "fwqbm", Fmt::Str, Cond::Eq, "服务区编码", false, false, true, true},
            {"fwqmc", "fwqmc", Fmt::Str, Cond::Like, "服务区名称", false, false, true, true},
            {"wd", "wd", Fmt::Str, Cond::Eq, "纬度", false, false, true, true},
            {"fxmc", "fxmc", Fmt::Str, Cond::Eq, "方向名称", false, false, true, true},
            {"fxdm", "fxdm", Fmt::Str, Cond::Eq, "方向代码", false, false, true, true},
            {"jd", "jd", Fmt::Str, Cond::Eq, "经度", false, false, true, true},
            {"sslxbh", "sslxbh", Fmt::Str, Cond::Eq, "所属路线编号", false, false, true, true},
            {"sslxmc", "sslxmc", Fmt::Str, Cond::Eq, "所属路线名称", false, false, true, true},
            {"ssldbh", "ssldbh", Fmt::Str, Cond::Eq, "所属路段编号", false, false, true, true},
            {"ssldmc", "ssldmc", Fmt::Str, Cond::Eq, "所属路段名称", false, false, true, true},
            {"sczhkgs", "sczhkgs", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"sczhszgs", "sczhszgs", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"ssglzxbm", "ssglzxbm", Fmt::Str, Cond::Eq, "所属管理中心编码", false, false, true, true},
            {"ssglzxmc", "ssglzxmc", Fmt::Str, Cond::Eq, "所属管理中心名称", false, false, true, true},
            {"xzqhmc", "xzqhmc", Fmt::Str, Cond::Eq, "行政区划名称", false, false, true, true},
            {"yyrq", "yyrq", Fmt::Str, Cond::Eq, "营业日期", false, false, true, true},
            {"cws", "cws", Fmt::Str, Cond::Eq, "车位数", false, false, true, true},
            {"sfszlkk", "sfszlkk", Fmt::Str, Cond::Eq, "是否设置了卡口", false, false, true, true},
            {"cdzs", "cdzs", Fmt::Str, Cond::Eq, "充电桩数", false, false, true, true},
            {"sfcyfw", "sfcyfw", Fmt::Str, Cond::Eq, "是否餐饮服务", false, false, true, true},
            {"sftgzsfw", "sftgzsfw", Fmt::Str, Cond::Eq, "是否提供住宿服务", false, false, true, true},
            {"sftgqxfw", "sftgqxfw", Fmt::Str, Cond::Eq, "是否提供汽修服务", false, false, true, true},
            {"sftgcsfw", "sftgcsfw", Fmt::Str, Cond::Eq, "是否提供超市服务", false, false, true, true},
            {"sftgjyfw", "sftgjyfw", Fmt::Str, Cond::Eq, "是否提供加油服务", false, false, true, true},
            {"mj", "mj", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"sftgcshfw", "sftgcshfw", Fmt::Str, Cond::Eq, "是否提供厕所服务", false, false, true, true},
            {"xzqhdm", "xzqhdm", Fmt::Str, Cond::Eq, "行政区划代码", false, false, true, true},
            {"synx", "synx", Fmt::Str, Cond::Eq, "使用年限", false, false, true, true},
            {"lyxt", "lyxt", Fmt::Str, Cond::Eq, "来源系统", false, false, true, true},
            {"loadTime", "load_time", Fmt::Str, Cond::Eq, "加载日期", false, false, true, true},
            {"allColPk", "all_col_pk", Fmt::Str, Cond::Eq, "全字段MD5", false, false, true, true},
        };
        s.orderBy = "t.fwqmc";
        s.excelSheetName = "服务区基础信息";
        return s;
    }();
    return s;
}

const Spec& specDwdLcztSfsjcxx() {
    static const Spec s = [] {
        Spec s;
        s.table = "dwd_lczt_sfsjcxx";
        s.alias = "t";
        s.fields = {
            {"agentPk", "agent_pk", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"yxtzj", "yxtzj", Fmt::Str, Cond::Eq, "源系统主键", false, false, true, true},
            {"sfsbm", "sfsbm", Fmt::Str, Cond::Eq, "收费所编码", false, false, true, true},
            {"sfsmc", "sfsmc", Fmt::Str, Cond::Like, "收费所名称", false, false, true, true},
            {"jd", "jd", Fmt::Str, Cond::Eq, "经度", false, false, true, true},
            {"wd", "wd", Fmt::Str, Cond::Eq, "纬度", false, false, true, true},
            {"sslxbh", "sslxbh", Fmt::Str, Cond::Eq, "所属路线编号", false, false, true, true},
            {"sslxmc", "sslxmc", Fmt::Str, Cond::Eq, "所属路线名称", false, false, true, true},
            {"ssldbh", "ssldbh", Fmt::Str, Cond::Eq, "所属路段编号", false, false, true, true},
            {"ssldmc", "ssldmc", Fmt::Str, Cond::Like, "所属路段名称", false, false, true, true},
            {"sczhK", "sczh_k", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"sczhN", "sczh_n", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"ssglzxbm", "ssglzxbm", Fmt::Str, Cond::Eq, "所属管理中心编码", false, false, true, true},
            {"ssglzxmc", "ssglzxmc", Fmt::Str, Cond::Eq, "所属管理中心名称", false, false, true, true},
            {"lyxt", "lyxt", Fmt::Str, Cond::Eq, "来源系统", false, false, true, true},
            {"loadTime", "load_time", Fmt::Str, Cond::Eq, "加载日期", false, false, true, true},
            {"allColPk", "all_col_pk", Fmt::Str, Cond::Eq, "全字段MD5", false, false, true, true},
        };
        s.orderBy = "t.agent_pk";
        s.excelSheetName = "收费所基础信息";
        return s;
    }();
    return s;
}

const Spec& specDwdLcztSfzjcxx() {
    static const Spec s = [] {
        Spec s;
        s.table = "dwd_lczt_sfzjcxx";
        s.alias = "t";
        s.fields = {
            {"agentPk", "agent_pk", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"yxtzj", "yxtzj", Fmt::Str, Cond::Eq, "源系统主键", false, false, true, true},
            {"sfzdm", "sfzdm", Fmt::Str, Cond::Eq, "收费站代码", false, false, true, true},
            {"sfzmc", "sfzmc", Fmt::Str, Cond::Like, "收费站名称", false, false, true, true},
            {"jd", "jd", Fmt::Str, Cond::Eq, "经度", false, false, true, true},
            {"wd", "wd", Fmt::Str, Cond::Eq, "纬度", false, false, true, true},
            {"sslxbh", "sslxbh", Fmt::Str, Cond::Eq, "所属路线编号", false, false, true, true},
            {"sslxmc", "sslxmc", Fmt::Str, Cond::Eq, "所属路线名称", false, false, true, true},
            {"ssldbh", "ssldbh", Fmt::Str, Cond::Eq, "所属路段编号", false, false, true, true},
            {"ssldmc", "ssldmc", Fmt::Str, Cond::Eq, "所属路段名称", false, false, true, true},
            {"sczhK", "sczh_k", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"sczhN", "sczh_n", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"ssglzxbm", "ssglzxbm", Fmt::Str, Cond::Eq, "所属管理中心编码", false, false, true, true},
            {"ssglzxmc", "ssglzxmc", Fmt::Str, Cond::Eq, "所属管理中心名称", false, false, true, true},
            {"lyxt", "lyxt", Fmt::Str, Cond::Eq, "来源系统", false, false, true, true},
            {"loadTime", "load_time", Fmt::Str, Cond::Eq, "加载日期", false, false, true, true},
            {"allColPk", "all_col_pk", Fmt::Str, Cond::Eq, "全字段MD5", false, false, true, true},
        };
        s.orderBy = "t.agent_pk";
        s.excelSheetName = "收费站基础信息";
        return s;
    }();
    return s;
}

const Spec& specGeometry() {
    static const Spec s = [] {
        Spec s;
        s.table = "geometry";
        s.alias = "t";
        s.fields = {
            {"id", "id", Fmt::Int, Cond::Eq, nullptr, true, false, true, true},
            {"lxbh", "lxbh", Fmt::Str, Cond::Eq, "路线编号", false, false, true, true},
            {"lxfx", "lxfx", Fmt::Str, Cond::Eq, "路线方向", false, false, true, true},
            {"qdzh", "qdzh", Fmt::Int, Cond::Eq, "起点桩号", false, false, true, true},
            {"zdzh", "zdzh", Fmt::Int, Cond::Eq, "终点桩号", false, false, true, true},
            {"paths", "paths", Fmt::Str, Cond::Eq, "经纬度", false, false, true, true},
            {"zhStr", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
        };
        s.orderBy = "lxbh,t.qdzh";
        s.excelSheetName = "车辆信息";
        return s;
    }();
    return s;
}

const Spec& specOdsCxztFwqclls() {
    static const Spec s = [] {
        Spec s;
        s.table = "ods_cxzt_fwqclls";
        s.alias = "t";
        s.fields = {
            {"bigId", "big_id", Fmt::Long, Cond::Eq, nullptr, false, false, true, true},
            {"datauuid", "datauuid", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"targetpicurl", "targetpicurl", Fmt::Str, Cond::Eq, "抓拍照片url", false, false, true, true},
            {"vehiclebrand", "vehiclebrand", Fmt::Str, Cond::Eq, "车辆品牌", false, false, true, true},
            {"platepicurl", "platepicurl", Fmt::Str, Cond::Eq, "车牌照片", false, false, true, true},
            {"rollvehiclestype", "rollvehiclestype", Fmt::Str, Cond::Eq, "车类型", false, false, true, true},
            {"plateno", "plateno", Fmt::Str, Cond::Eq, "车牌", false, false, true, true},
            {"directionname", "directionname", Fmt::Str, Cond::Like, "方向名称", false, false, true, true},
            {"platetype", "platetype", Fmt::Str, Cond::Eq, "车牌类型", false, false, true, true},
            {"dangmark", "dangmark", Fmt::Str, Cond::Eq, "是否危化品车", false, false, true, true},
            {"crosstime", "crosstime", Fmt::DateIso, Cond::Eq, "通过时间", false, false, true, true},
            {"axles", "axles", Fmt::Str, Cond::Eq, "坐标", false, false, true, true},
            {"devicename", "devicename", Fmt::Str, Cond::Like, "设备名称", false, false, true, true},
            {"ipaddress", "ipaddress", Fmt::Str, Cond::Eq, "IP地址", false, false, true, true},
            {"servicename", "servicename", Fmt::Str, Cond::Like, "服务区名称", false, false, true, true},
            {"vehicletype", "vehicletype", Fmt::Str, Cond::Eq, "车辆类型", false, false, true, true},
            {"loadTime", "load_time", Fmt::Str, Cond::Eq, "加载时间", false, false, true, true},
            {"gradeLevel", "grade_level", Fmt::Str, Cond::Eq, "分类分级", false, false, true, true},
        };
        s.excelSheetName = "OdsCxztFwqclls";
        return s;
    }();
    return s;
}

const Spec& specOdsLwzxsfsjFeeGantryFusion01() {
    static const Spec s = [] {
        Spec s;
        s.table = "ods_lwzxsfsj_fee_gantry_fusion_01";
        s.alias = "t";
        s.fields = {
            {"bigId", "big_id", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"actualfeeclass", "actualfeeclass", Fmt::Str, Cond::Eq, "实际计费方式", false, false, true, true},
            {"axlecount", "axlecount", Fmt::Long, Cond::Eq, "车轴数", false, false, true, true},
            {"createtime", "createtime", Fmt::DateIso, Cond::Eq, "创建时间", false, false, true, true},
            {"discountfee", "discountfee", Fmt::Long, Cond::Eq, "优惠金额", false, false, true, true},
            {"electricalpercentage", "electricalpercentage", Fmt::Long, Cond::Eq, "单片式OBU/CPC卡电量百分比", false, false, true, true},
            {"enaxlecount", "enaxlecount", Fmt::Long, Cond::Eq, "入口车轴数", false, false, true, true},
            {"entime", "entime", Fmt::DateYmd, Cond::Eq, "入站时间", false, false, true, true},
            {"entolllanehex", "entolllanehex", Fmt::Str, Cond::Eq, "入口车道hex", false, false, true, true},
            {"entolllaneid", "entolllaneid", Fmt::Str, Cond::Eq, "入口车道ID", false, false, true, true},
            {"entollstationid", "entollstationid", Fmt::Str, Cond::Eq, "入口收费站编码", false, false, true, true},
            {"entollstationname", "entollstationname", Fmt::Str, Cond::Like, "入口收费站名称", false, false, true, true},
            {"envehicleclass", "envehicleclass", Fmt::Long, Cond::Eq, "入口车种", false, false, true, true},
            {"envehicleid", "envehicleid", Fmt::Str, Cond::Eq, "入口车牌号+车牌类型", false, false, true, true},
            {"envehicleidcolor", "envehicleidcolor", Fmt::Str, Cond::Eq, "入口车牌号+颜色", false, false, true, true},
            {"envehicletype", "envehicletype", Fmt::Long, Cond::Eq, "入口车型", false, false, true, true},
            {"enweight", "enweight", Fmt::Long, Cond::Eq, "入口称重", false, false, true, true},
            {"entryoperatorid", "entryoperatorid", Fmt::Str, Cond::Eq, "入口操作人员id", false, false, true, true},
            {"extime", "extime", Fmt::DateYmd, Cond::Eq, "出站时间", false, false, true, true},
            {"extolllaneid", "extolllaneid", Fmt::Str, Cond::Eq, "出口车道号编码", false, false, true, true},
            {"extollstationid", "extollstationid", Fmt::Str, Cond::Eq, "出口收费站编码", false, false, true, true},
            {"extollstationname", "extollstationname", Fmt::Str, Cond::Like, "出口收费站名称", false, false, true, true},
            {"exvehicleclass", "exvehicleclass", Fmt::Long, Cond::Eq, "出口车种", false, false, true, true},
            {"exvehicleid", "exvehicleid", Fmt::Str, Cond::Eq, "出口车牌号+车牌类型", false, false, true, true},
            {"exvehicletype", "exvehicletype", Fmt::Long, Cond::Eq, "出口车型", false, false, true, true},
            {"exweight", "exweight", Fmt::Long, Cond::Eq, "出口称重", false, false, true, true},
            {"exitid", "exitid", Fmt::Str, Cond::Eq, "出口id", false, false, true, true},
            {"fee", "fee", Fmt::Long, Cond::Eq, "费用", false, false, true, true},
            {"feeboardplay", "feeboardplay", Fmt::Str, Cond::Eq, "费显显示信息", false, false, true, true},
            {"feemileage", "feemileage", Fmt::Long, Cond::Eq, "收费里程", false, false, true, true},
            {"feerate", "feerate", Fmt::Str, Cond::Eq, "交易金额占比", false, false, true, true},
            {"fusiondesc", "fusiondesc", Fmt::Str, Cond::Eq, "融合描述", false, false, true, true},
            {"fusionflag", "fusionflag", Fmt::Str, Cond::Eq, "融合标识,", false, false, true, true},
            {"id", "id", Fmt::Str, Cond::Eq, "id", false, false, true, true},
            {"identification", "identification", Fmt::Str, Cond::Eq, "开票标识", false, false, true, true},
            {"identifyvehicleid", "identifyvehicleid", Fmt::Str, Cond::Eq, "出口识别车牌号+车牌类型", false, false, true, true},
            {"identifyvehicleidcolor", "identifyvehicleidcolor", Fmt::Str, Cond::Eq, "出口识别车牌号+颜色", false, false, true, true},
            {"lanetype", "lanetype", Fmt::Str, Cond::Eq, "出口车道类型", false, false, true, true},
            {"mediano", "mediano", Fmt::Str, Cond::Eq, "介质编码", false, false, true, true},
            {"mediatype", "mediatype", Fmt::Str, Cond::Eq, "通行介质", false, false, true, true},
            {"nocardcount", "nocardcount", Fmt::Long, Cond::Eq, "标签无卡累计次数", false, false, true, true},
            {"obuid", "obuid", Fmt::Str, Cond::Eq, "OBU序号编码", false, false, true, true},
            {"obusign", "obusign", Fmt::Str, Cond::Eq, "OBU 单/双片标识", false, false, true, true},
            {"obutotalamount", "obutotalamount", Fmt::Long, Cond::Eq, "0BU 总累计交易金额", false, false, true, true},
            {"obutotaldiscountamount", "obutotaldiscountamount", Fmt::Long, Cond::Eq, "OBU累计优惠后通行费金额", false, false, true, true},
            {"operid", "operid", Fmt::Str, Cond::Eq, "操作id", false, false, true, true},
            {"params", "params", Fmt::Str, Cond::Eq, "参数", false, false, true, true},
            {"passid", "passid", Fmt::Str, Cond::Eq, "通行id", false, false, true, true},
            {"paycardid", "paycardid", Fmt::Str, Cond::Eq, "支付id", false, false, true, true},
            {"payfee", "payfee", Fmt::Long, Cond::Eq, "应收总额", false, false, true, true},
            {"paytype", "paytype", Fmt::Str, Cond::Eq, "支付类型", false, false, true, true},
            {"provfee", "provfee", Fmt::Long, Cond::Eq, nullptr, false, false, true, true},
            {"provtranscount", "provtranscount", Fmt::Long, Cond::Eq, "本省交易成功次数", false, false, true, true},
            {"provincecount", "provincecount", Fmt::Long, Cond::Eq, "通行省份个数", false, false, true, true},
            {"receivetime", "receivetime", Fmt::DateYmd, Cond::Eq, "接收时间", false, false, true, true},
            {"shift", "shift", Fmt::Str, Cond::Eq, "工班号", false, false, true, true},
            {"shortfee", "shortfee", Fmt::Long, Cond::Eq, "最短收费金额", false, false, true, true},
            {"shortfeemileage", "shortfeemileage", Fmt::Long, Cond::Eq, "最短路径里程数", false, false, true, true},
            {"signstatus", "signstatus", Fmt::Str, Cond::Eq, "标记状态", false, false, true, true},
            {"spcrateversion", "spcrateversion", Fmt::Str, Cond::Eq, "全网最小费额费率版本号", false, false, true, true},
            {"specialtype", "specialtype", Fmt::Str, Cond::Eq, "特殊类型", false, false, true, true},
            {"splitprovince", "splitprovince", Fmt::Str, Cond::Eq, "多条省内交易信息", false, false, true, true},
            {"tac", "tac", Fmt::Str, Cond::Eq, "TAC码", false, false, true, true},
            {"terminalno", "terminalno", Fmt::Str, Cond::Eq, "终端机编号", false, false, true, true},
            {"terminaltransno", "terminaltransno", Fmt::Str, Cond::Eq, "PSAM卡脱机交易序列号", false, false, true, true},
            {"transfee", "transfee", Fmt::Long, Cond::Eq, "卡面扣费金额", false, false, true, true},
            {"transpaytype", "transpaytype", Fmt::Str, Cond::Eq, "交易支付类型", false, false, true, true},
            {"transtype", "transtype", Fmt::Str, Cond::Eq, "交易类型", false, false, true, true},
            {"vehiclesign", "vehiclesign", Fmt::Str, Cond::Eq, "车辆识别标识", false, false, true, true},
            {"vehiclesignid", "vehiclesignid", Fmt::Str, Cond::Eq, "车牌识别流水号", false, false, true, true},
            {"vid", "vid", Fmt::Str, Cond::Eq, "车牌号ID", false, false, true, true},
            {"loadTime", "load_time", Fmt::DateYmd, Cond::Eq, "加载时间", false, false, true, true},
            {"gradeLevel", "grade_level", Fmt::Long, Cond::Eq, "分类分级", false, false, true, true},
            {"inApplyTime1", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"inApplyTime2", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"outApplyTime1", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"outApplyTime2", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"pageNum", nullptr, Fmt::Int, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"pageSize", nullptr, Fmt::Int, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
        };
        s.orderBy = "t.big_id";
        s.excelSheetName = "交易流水";
        return s;
    }();
    return s;
}

const Spec& specOdsLwzxsfsjFeeRecords01() {
    static const Spec s = [] {
        Spec s;
        s.table = "ods_lwzxsfsj_fee_records_01";
        s.alias = "t";
        s.fields = {
            {"bigId", "big_id", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"algorithmidentifier", "algorithmidentifier", Fmt::Str, Cond::Eq, "算法标识", false, false, true, true},
            {"antennaid", "antennaid", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"axlecount", "axlecount", Fmt::Long, Cond::Eq, "车轴数", false, false, true, true},
            {"balanceafter", "balanceafter", Fmt::Double, Cond::Eq, "交易后余额", false, false, true, true},
            {"balancebefore", "balancebefore", Fmt::Double, Cond::Eq, "交易前余额", false, false, true, true},
            {"cardfeesumafter", "cardfeesumafter", Fmt::Double, Cond::Eq, "本次交易后卡片累计金额", false, false, true, true},
            {"cardfeesumbefore", "cardfeesumbefore", Fmt::Double, Cond::Eq, "本次交易前卡片累计金额", false, false, true, true},
            {"computerorder", "computerorder", Fmt::Str, Cond::Eq, "控制器序号", false, false, true, true},
            {"consumetime", "consumetime", Fmt::Long, Cond::Eq, "交易耗时", false, false, true, true},
            {"cpucardid", "cpucardid", Fmt::Str, Cond::Eq, "CPU卡编号", false, false, true, true},
            {"cpucardtype", "cpucardtype", Fmt::Str, Cond::Eq, "CPU卡类型", false, false, true, true},
            {"cpuenddate", "cpuenddate", Fmt::Str, Cond::Eq, "CPU截止日期", false, false, true, true},
            {"cpuissueid", "cpuissueid", Fmt::Str, Cond::Eq, "CPU卡片发行方标识", false, false, true, true},
            {"cpunetid", "cpunetid", Fmt::Str, Cond::Eq, "CPU卡片网络编号", false, false, true, true},
            {"cpustartdate", "cpustartdate", Fmt::Str, Cond::Eq, "CPU起始日期", false, false, true, true},
            {"cpuvehicleplate", "cpuvehicleplate", Fmt::Str, Cond::Eq, "CPU 内车牌号码", false, false, true, true},
            {"cpuvehicletype", "cpuvehicletype", Fmt::Str, Cond::Eq, "CPU内车型", false, false, true, true},
            {"cpuversion", "cpuversion", Fmt::Str, Cond::Eq, "CPU用户卡版本号", false, false, true, true},
            {"dealstatus", "dealstatus", Fmt::Str, Cond::Eq, "处理状态", false, false, true, true},
            {"discountfee", "discountfee", Fmt::Double, Cond::Eq, "优惠金额", false, false, true, true},
            {"discountfeegroup", "discountfeegroup", Fmt::Str, Cond::Eq, "优惠金额组合", false, false, true, true},
            {"enlanetype", "enlanetype", Fmt::Str, Cond::Eq, "入口车道类型", false, false, true, true},
            {"entime", "entime", Fmt::DateYmdHms, Cond::Eq, "进站时间", false, false, true, true},
            {"entolllaneid", "entolllaneid", Fmt::Str, Cond::Eq, "进站收费站车道号", false, false, true, true},
            {"entollstationhex", "entollstationhex", Fmt::Str, Cond::Eq, "进站收费站hex编码", false, false, true, true},
            {"fee", "fee", Fmt::Double, Cond::Eq, "费用", false, false, true, true},
            {"feecalcresult", "feecalcresult", Fmt::Str, Cond::Eq, "计费模块响应计费结果", false, false, true, true},
            {"feecalcspecial", "feecalcspecial", Fmt::Str, Cond::Eq, "计费接口特情值", false, false, true, true},
            {"feecalcspecials", "feecalcspecials", Fmt::Str, Cond::Eq, "计费特情值组合", false, false, true, true},
            {"feegroup", "feegroup", Fmt::Str, Cond::Eq, "交易金额组合", false, false, true, true},
            {"feeinfo1", "feeinfo1", Fmt::Str, Cond::Eq, "计费信息1", false, false, true, true},
            {"feeinfo2", "feeinfo2", Fmt::Str, Cond::Eq, "计费信息2", false, false, true, true},
            {"feeinfo3", "feeinfo3", Fmt::Str, Cond::Eq, "计费信息3", false, false, true, true},
            {"feemileage", "feemileage", Fmt::Double, Cond::Eq, "收费里程", false, false, true, true},
            {"feeprovbeginhex", "feeprovbeginhex", Fmt::Str, Cond::Eq, "本省计费起点", false, false, true, true},
            {"feespare1", "feespare1", Fmt::Str, Cond::Eq, "计费协议保留字段1", false, false, true, true},
            {"feespare2", "feespare2", Fmt::Str, Cond::Eq, "计费协议保留字段2", false, false, true, true},
            {"feevehicletype", "feevehicletype", Fmt::Str, Cond::Eq, "计费车型", false, false, true, true},
            {"gantryhex", "gantryhex", Fmt::Str, Cond::Eq, "门架Hex值", false, false, true, true},
            {"gantryhexopposite", "gantryhexopposite", Fmt::Str, Cond::Eq, "对向门架Hex值", false, false, true, true},
            {"gantryid", "gantryid", Fmt::Str, Cond::Eq, "门架编码", false, false, true, true},
            {"gantryordernum", "gantryordernum", Fmt::Long, Cond::Eq, "门架顺序号", false, false, true, true},
            {"gantrytype", "gantrytype", Fmt::Str, Cond::Eq, "门架类型", false, false, true, true},
            {"holidaystate", "holidaystate", Fmt::Str, Cond::Eq, "节假日状态", false, false, true, true},
            {"hourbatchno", "hourbatchno", Fmt::Str, Cond::Eq, "小时批次号", false, false, true, true},
            {"keyversion", "keyversion", Fmt::Str, Cond::Eq, "消费密钥版本号", false, false, true, true},
            {"lastgantryhex", "lastgantryhex", Fmt::Str, Cond::Eq, "上一个门架的hex编号", false, false, true, true},
            {"lastgantrytime", "lastgantrytime", Fmt::DateYmdHms, Cond::Eq, "通过上一个门架的时间", false, false, true, true},
            {"matchstatus", "matchstatus", Fmt::Str, Cond::Eq, "匹配状态", false, false, true, true},
            {"mediatype", "mediatype", Fmt::Str, Cond::Eq, "通行介质类型", false, false, true, true},
            {"nocardtimesafter", "nocardtimesafter", Fmt::Long, Cond::Eq, "本次交易后累计无卡次数", false, false, true, true},
            {"nocardtimesbefore", "nocardtimesbefore", Fmt::Long, Cond::Eq, "本次交易前累计无卡次数", false, false, true, true},
            {"obuelectrical", "obuelectrical", Fmt::Long, Cond::Eq, "OBU/CPC卡电量百分比", false, false, true, true},
            {"obuenddate", "obuenddate", Fmt::Str, Cond::Eq, "OBU/CPC截止日期", false, false, true, true},
            {"obufeesumafter", "obufeesumafter", Fmt::Double, Cond::Eq, "本次交易后标签累计实收金额", false, false, true, true},
            {"obufeesumbefore", "obufeesumbefore", Fmt::Double, Cond::Eq, "本次交易前标签累计实收金额", false, false, true, true},
            {"obuinfotyperead", "obuinfotyperead", Fmt::Str, Cond::Eq, "读取标签入口信息类型", false, false, true, true},
            {"obuinfotypewrite", "obuinfotypewrite", Fmt::Str, Cond::Eq, "本次写入标签入口信息类型", false, false, true, true},
            {"obuissueid", "obuissueid", Fmt::Str, Cond::Eq, "OBU/CPC发行方标识", false, false, true, true},
            {"obulastgantryhex", "obulastgantryhex", Fmt::Str, Cond::Eq, "OBU中上一个门架HEX", false, false, true, true},
            {"obulastgantrytime", "obulastgantrytime", Fmt::DateYmdHms, Cond::Eq, "OBU中通过上一个门架时间", false, false, true, true},
            {"obumac", "obumac", Fmt::Str, Cond::Eq, "OBU /CPC物理地址", false, false, true, true},
            {"obumileageafter", "obumileageafter", Fmt::Double, Cond::Eq, "本次交易后标签累计里程", false, false, true, true},
            {"obumileagebefore", "obumileagebefore", Fmt::Double, Cond::Eq, "本次交易前标签累计里程", false, false, true, true},
            {"obupassstate", "obupassstate", Fmt::Str, Cond::Eq, "标签入口状态", false, false, true, true},
            {"obupayfeesumafter", "obupayfeesumafter", Fmt::Double, Cond::Eq, "本次交易后标签累计应收金额", false, false, true, true},
            {"obupayfeesumbefore", "obupayfeesumbefore", Fmt::Double, Cond::Eq, "本次交易前标签累计应收金额", false, false, true, true},
            {"obuprovfeesumafter", "obuprovfeesumafter", Fmt::Double, Cond::Eq, "本次交易后标签累计金额", false, false, true, true},
            {"obuprovfeesumbefore", "obuprovfeesumbefore", Fmt::Double, Cond::Eq, "本次交易前标签累计金额 ", false, false, true, true},
            {"obuprovpayfeesumafter", "obuprovpayfeesumafter", Fmt::Double, Cond::Eq, "本次交易后标签累计应收金额", false, false, true, true},
            {"obuprovpayfeesumbefore", "obuprovpayfeesumbefore", Fmt::Double, Cond::Eq, "本次交易前标签累计应收金额", false, false, true, true},
            {"obuprovtradesuccnumafter", "obuprovtradesuccnumafter", Fmt::Long, Cond::Eq, "省内本次交易后标签累计写入成功数量", false, false, true, true},
            {"obuprovtradesuccnumbefore", "obuprovtradesuccnumbefore", Fmt::Long, Cond::Eq, "省内本次交易前标签累计写入成功数量", false, false, true, true},
            {"obusign", "obusign", Fmt::Str, Cond::Eq, "OBU 单/双片标识", false, false, true, true},
            {"obusn", "obusn", Fmt::Str, Cond::Eq, "OBU/CPC序号编码", false, false, true, true},
            {"obustartdate", "obustartdate", Fmt::Str, Cond::Eq, "OBU/CPC起始日期", false, false, true, true},
            {"obustate", "obustate", Fmt::Str, Cond::Eq, "OBU/CPC状态", false, false, true, true},
            {"obutotaltradesuccnumafter", "obutotaltradesuccnumafter", Fmt::Long, Cond::Eq, "本次交易后标签累计写入成功总量", false, false, true, true},
            {"obutotaltradesuccnumbefore", "obutotaltradesuccnumbefore", Fmt::Long, Cond::Eq, "本次交易前标签累计写入成功总量", false, false, true, true},
            {"obutraderesult", "obutraderesult", Fmt::Str, Cond::Eq, "标签写入结果", false, false, true, true},
            {"obuvehicleplate", "obuvehicleplate", Fmt::Str, Cond::Eq, "obu车牌", false, false, true, true},
            {"obuvehicletype", "obuvehicletype", Fmt::Str, Cond::Eq, "obu车牌类型", false, false, true, true},
            {"obuversion", "obuversion", Fmt::Str, Cond::Eq, "OBU/CPC版本号", false, false, true, true},
            {"params", "params", Fmt::Str, Cond::Eq, "参数", false, false, true, true},
            {"passid", "passid", Fmt::Str, Cond::Eq, "通行id", false, false, true, true},
            {"passstate", "passstate", Fmt::Str, Cond::Eq, "通行状态", false, false, true, true},
            {"pathfitflag", "pathfitflag", Fmt::Str, Cond::Eq, "本次计费拟合结果标识", false, false, true, true},
            {"payfee", "payfee", Fmt::Double, Cond::Eq, "应收金额", false, false, true, true},
            {"payfeegroup", "payfeegroup", Fmt::Str, Cond::Eq, "应收金额组合", false, false, true, true},
            {"pcrsuversion", "pcrsuversion", Fmt::Str, Cond::Eq, "PC-RSU接口协议版本号", false, false, true, true},
            {"provminfee", "provminfee", Fmt::Double, Cond::Eq, "本省累计通行金额参考", false, false, true, true},
            {"provincenumafter", "provincenumafter", Fmt::Long, Cond::Eq, "本次交易后累计省份数量", false, false, true, true},
            {"provincenumbefore", "provincenumbefore", Fmt::Long, Cond::Eq, "本次交易前累计省份数量", false, false, true, true},
            {"ratecompute", "ratecompute", Fmt::Str, Cond::Eq, "计费模块计费模式", false, false, true, true},
            {"ratefitcount", "ratefitcount", Fmt::Long, Cond::Eq, "计费模块拟合点总数", false, false, true, true},
            {"rateversion", "rateversion", Fmt::Str, Cond::Eq, "计费模块和计费参数版本号", false, false, true, true},
            {"readciphertextverify", "readciphertextverify", Fmt::Str, Cond::Eq, "本次交易读取的EF04加密摘要验证结果", false, false, true, true},
            {"receivetime", "receivetime", Fmt::DateYmdHms, Cond::Eq, "接收时间", false, false, true, true},
            {"servicetype", "servicetype", Fmt::Str, Cond::Eq, "交易的服务类型", false, false, true, true},
            {"stationdbtime", "stationdbtime", Fmt::DateYmdHms, Cond::Eq, "门架后台入库时间", false, false, true, true},
            {"stationdealtime", "stationdealtime", Fmt::DateYmdHms, Cond::Eq, "门架后台处理时间", false, false, true, true},
            {"stationmatchtime", "stationmatchtime", Fmt::DateYmdHms, Cond::Eq, "门架后台匹配时间", false, false, true, true},
            {"stationvalidtime", "stationvalidtime", Fmt::DateYmdHms, Cond::Eq, "门架后台去重时间", false, false, true, true},
            {"tac", "tac", Fmt::Str, Cond::Eq, "TAC码", false, false, true, true},
            {"terminalno", "terminalno", Fmt::Str, Cond::Eq, "终端机编号", false, false, true, true},
            {"terminaltransno", "terminaltransno", Fmt::Str, Cond::Eq, "PSAM卡脱机交易序列号", false, false, true, true},
            {"tollintervalid", "tollintervalid", Fmt::Str, Cond::Eq, "收费单元编号组合", false, false, true, true},
            {"tollintervalsign", "tollintervalsign", Fmt::Str, Cond::Eq, "收费单元处理标识", false, false, true, true},
            {"totalweight", "totalweight", Fmt::Double, Cond::Eq, "车货总重", false, false, true, true},
            {"tradeid", "tradeid", Fmt::Str, Cond::Eq, "计费交易编号", false, false, true, true},
            {"tradereadciphertext", "tradereadciphertext", Fmt::Str, Cond::Eq, "本次交易读取的EF04加密摘要", false, false, true, true},
            {"traderesult", "traderesult", Fmt::Str, Cond::Eq, "卡片复合交易结果", false, false, true, true},
            {"tradetype", "tradetype", Fmt::Str, Cond::Eq, "交易类型", false, false, true, true},
            {"tradewriteciphertext", "tradewriteciphertext", Fmt::Str, Cond::Eq, "本次交易生成的EF04加密摘要", false, false, true, true},
            {"transfee", "transfee", Fmt::Double, Cond::Eq, "卡面扣费金额", false, false, true, true},
            {"transno", "transno", Fmt::Str, Cond::Eq, "IC卡交易序号", false, false, true, true},
            {"transtime", "transtime", Fmt::DateYmdHms, Cond::Eq, "计费交易时间", false, false, true, true},
            {"transtype", "transtype", Fmt::Str, Cond::Eq, "交易类型标识", false, false, true, true},
            {"validstatus", "validstatus", Fmt::Str, Cond::Eq, "去重状态", false, false, true, true},
            {"vehicleclass", "vehicleclass", Fmt::Str, Cond::Eq, "车种", false, false, true, true},
            {"vehiclehight", "vehiclehight", Fmt::Double, Cond::Eq, "车高", false, false, true, true},
            {"vehiclelength", "vehiclelength", Fmt::Double, Cond::Eq, "车长", false, false, true, true},
            {"vehicleplate", "vehicleplate", Fmt::Str, Cond::Eq, "车牌号+类型", false, false, true, true},
            {"vehicleseat", "vehicleseat", Fmt::Str, Cond::Eq, "车辆座位数/载重", false, false, true, true},
            {"vehiclesign", "vehiclesign", Fmt::Str, Cond::Eq, "车辆状态标识", false, false, true, true},
            {"vehicletype", "vehicletype", Fmt::Str, Cond::Eq, "车辆类型", false, false, true, true},
            {"vehicleusertype", "vehicleusertype", Fmt::Str, Cond::Eq, "车辆用户类型", false, false, true, true},
            {"vehiclewidth", "vehiclewidth", Fmt::Double, Cond::Eq, "车宽", false, false, true, true},
            {"verifycode", "verifycode", Fmt::Str, Cond::Eq, "校验码", false, false, true, true},
            {"loadTime", "load_time", Fmt::DateYmdHms, Cond::Eq, "加载时间", false, false, true, true},
            {"gradeLevel", "grade_level", Fmt::Long, Cond::Eq, "分类分级", false, false, true, true},
            {"cid", nullptr, Fmt::Str, Cond::None, "cid", false, false, false, false, nullptr, nullptr},
            {"cidList", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"inApplyTime1", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"inApplyTime2", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"outApplyTime1", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"outApplyTime2", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"pageNum", nullptr, Fmt::Int, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"pageSize", nullptr, Fmt::Int, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"plateColor", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"gantryName", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"receivetimeStr", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"sectionCodeStr", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"type", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"code", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"sectionName", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"roadname", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"transtimeStr", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"lastgantrytimeStr", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"chargeStatus", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"entimeStr", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
        };
        s.orderBy = "t.big_id";
        s.excelSheetName = "基础-收费流水";
        return s;
    }();
    return s;
}

const Spec& specOdsLwzxsfsjFeeStationEnter01() {
    static const Spec s = [] {
        Spec s;
        s.table = "ods_lwzxsfsj_fee_station_enter_01";
        s.alias = "t";
        s.fields = {
            {"bigId", "big_id", Fmt::Long, Cond::Eq, nullptr, true, false, true, true},
            {"cardid", "cardid", Fmt::Str, Cond::Eq, "CPC卡或ETC卡的编号", false, false, true, true},
            {"electricalpercentage", "electricalpercentage", Fmt::Long, Cond::Eq, "单片式OBU/CPC卡电量百分比", false, false, true, true},
            {"enaxlecount", "enaxlecount", Fmt::Long, Cond::Eq, "入站车轴数", false, false, true, true},
            {"entime", "entime", Fmt::DateYmd, Cond::Eq, "入站时间", false, false, true, true},
            {"entolllanehex", "entolllanehex", Fmt::Str, Cond::Eq, "入口车道hex", false, false, true, true},
            {"entolllaneid", "entolllaneid", Fmt::Str, Cond::Eq, "入口车道id", false, false, true, true},
            {"entollstationid", "entollstationid", Fmt::Str, Cond::Eq, "入口收费站编码", false, false, true, true},
            {"enweight", "enweight", Fmt::Double, Cond::Eq, "入口称重", false, false, true, true},
            {"identifyvehicleid", "identifyvehicleid", Fmt::Str, Cond::Eq, "车牌号+车牌类型", false, false, true, true},
            {"lanetype", "lanetype", Fmt::Str, Cond::Eq, "车道类型", false, false, true, true},
            {"mediatype", "mediatype", Fmt::Str, Cond::Eq, "介质类型", false, false, true, true},
            {"operid", "operid", Fmt::Str, Cond::Eq, "操作id", false, false, true, true},
            {"operationmedia", "operationmedia", Fmt::Str, Cond::Eq, "作业媒介", false, false, true, true},
            {"params", "params", Fmt::Str, Cond::Eq, "参数", false, false, true, true},
            {"passid", "passid", Fmt::Str, Cond::Eq, "通行id", false, false, true, true},
            {"receivetime", "receivetime", Fmt::DateYmd, Cond::Eq, "接收时间", false, false, true, true},
            {"shift", "shift", Fmt::Str, Cond::Eq, "工班号", false, false, true, true},
            {"signstatus", "signstatus", Fmt::Str, Cond::Eq, "标记状态", false, false, true, true},
            {"specialtype", "specialtype", Fmt::Str, Cond::Eq, "特殊类型", false, false, true, true},
            {"tac", "tac", Fmt::Str, Cond::Eq, "TAC码", false, false, true, true},
            {"terminalno", "terminalno", Fmt::Str, Cond::Eq, "终端机编号", false, false, true, true},
            {"terminaltransno", "terminaltransno", Fmt::Str, Cond::Eq, "PSAM卡脱机交易序列号", false, false, true, true},
            {"transfee", "transfee", Fmt::Double, Cond::Eq, "交易金额", false, false, true, true},
            {"transtype", "transtype", Fmt::Str, Cond::Eq, "交易类型", false, false, true, true},
            {"vcount", "vcount", Fmt::Long, Cond::Eq, "总数", false, false, true, true},
            {"vehicleclass", "vehicleclass", Fmt::Str, Cond::Eq, "车种", false, false, true, true},
            {"vehicleid", "vehicleid", Fmt::Str, Cond::Eq, "车牌号+车牌类型", false, false, true, true},
            {"vehiclesign", "vehiclesign", Fmt::Str, Cond::Eq, "车辆识别标识", false, false, true, true},
            {"vehiclesignid", "vehiclesignid", Fmt::Str, Cond::Eq, "车牌识别流水号", false, false, true, true},
            {"vehicletype", "vehicletype", Fmt::Str, Cond::Eq, "车辆类型", false, false, true, true},
            {"loadTime", "load_time", Fmt::DateYmd, Cond::Eq, "加载时间", false, false, true, true},
            {"gradeLevel", "grade_level", Fmt::Str, Cond::Eq, "分类分级", false, false, true, true},
            {"cid", "cid", Fmt::Str, Cond::None, "cid", false, false, true, true},
        };
        s.orderBy = "t.big_id";
        s.excelSheetName = "OdsLwzxsfsjFeeStationEnter01";
        return s;
    }();
    return s;
}

const Spec& specOdsLwzxsfsjFeeStationExit01() {
    static const Spec s = [] {
        Spec s;
        s.table = "ods_lwzxsfsj_fee_station_exit_01";
        s.alias = "t";
        s.fields = {
            {"bigId", "big_id", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"actualfeeclass", "actualfeeclass", Fmt::Str, Cond::Eq, "实际计费方式", false, false, true, true},
            {"axlecount", "axlecount", Fmt::Int, Cond::Eq, "车轴数", false, false, true, true},
            {"discountfee", "discountfee", Fmt::Long, Cond::Eq, "优惠金额", false, false, true, true},
            {"electricalpercentage", "electricalpercentage", Fmt::Int, Cond::Eq, "单片式OBU/CPC卡电量百分比", false, false, true, true},
            {"enaxlecount", "enaxlecount", Fmt::Int, Cond::Eq, "入站车轴数", false, false, true, true},
            {"entime", "entime", Fmt::DateYmd, Cond::Eq, "进站时间", false, false, true, true},
            {"entolllanehex", "entolllanehex", Fmt::Str, Cond::Eq, "入口车道hex", false, false, true, true},
            {"entolllaneid", "entolllaneid", Fmt::Str, Cond::Eq, "进站收费站车道号", false, false, true, true},
            {"entollstationid", "entollstationid", Fmt::Str, Cond::Eq, "入口收费站编码", false, false, true, true},
            {"entollstationname", "entollstationname", Fmt::Str, Cond::Like, "入口收费站名称", false, false, true, true},
            {"envehicleclass", "envehicleclass", Fmt::Int, Cond::Eq, "入口车种", false, false, true, true},
            {"envehicleid", "envehicleid", Fmt::Str, Cond::Eq, "入口车牌号+车牌类型", false, false, true, true},
            {"envehicletype", "envehicletype", Fmt::Int, Cond::Eq, "入口车型", false, false, true, true},
            {"enweight", "enweight", Fmt::Long, Cond::Eq, "入口称重", false, false, true, true},
            {"entryoperatorid", "entryoperatorid", Fmt::Str, Cond::Eq, "入口操作人员id", false, false, true, true},
            {"extime", "extime", Fmt::DateYmd, Cond::Eq, "出站时间", false, false, true, true},
            {"extolllaneid", "extolllaneid", Fmt::Str, Cond::Eq, "出口车道号编码", false, false, true, true},
            {"extollstationid", "extollstationid", Fmt::Str, Cond::Eq, "出口收费站编码", false, false, true, true},
            {"extollstationname", "extollstationname", Fmt::Str, Cond::Like, "出口收费站名称", false, false, true, true},
            {"exvehicleclass", "exvehicleclass", Fmt::Int, Cond::Eq, "出口车种", false, false, true, true},
            {"exvehicleid", "exvehicleid", Fmt::Str, Cond::Eq, "出口车牌号+车牌类型", false, false, true, true},
            {"exvehicletype", "exvehicletype", Fmt::Int, Cond::Eq, "出口车型", false, false, true, true},
            {"fee", "fee", Fmt::Long, Cond::Eq, "费用", false, false, true, true},
            {"exweight", "exweight", Fmt::Long, Cond::Eq, "出口称重", false, false, true, true},
            {"feeboardplay", "feeboardplay", Fmt::Str, Cond::Eq, "费显显示信息", false, false, true, true},
            {"feemileage", "feemileage", Fmt::Long, Cond::Eq, "收费里程", false, false, true, true},
            {"identification", "identification", Fmt::Str, Cond::Eq, "开票标识", false, false, true, true},
            {"feerate", "feerate", Fmt::Double, Cond::Eq, "交易金额占比", false, false, true, true},
            {"identifyvehicleid", "identifyvehicleid", Fmt::Str, Cond::Eq, "车牌号+车牌类型", false, false, true, true},
            {"lanetype", "lanetype", Fmt::Str, Cond::Eq, "车道类型", false, false, true, true},
            {"mediano", "mediano", Fmt::Str, Cond::Eq, "介质编码", false, false, true, true},
            {"mediatype", "mediatype", Fmt::Str, Cond::Eq, "通行介质类型", false, false, true, true},
            {"nocardcount", "nocardcount", Fmt::Int, Cond::Eq, "标签无卡累计次数", false, false, true, true},
            {"obuid", "obuid", Fmt::Str, Cond::Eq, "OBU序号编码", false, false, true, true},
            {"obusign", "obusign", Fmt::Str, Cond::Eq, "OBU 单/双片标识", false, false, true, true},
            {"obutotalamount", "obutotalamount", Fmt::Long, Cond::Eq, "0BU 总累计交易金额", false, false, true, true},
            {"obutotaldiscountamount", "obutotaldiscountamount", Fmt::Long, Cond::Eq, "OBU累计优惠后通行费金额", false, false, true, true},
            {"params", "params", Fmt::Str, Cond::Eq, "参数", false, false, true, true},
            {"operid", "operid", Fmt::Str, Cond::Eq, "操作id", false, false, true, true},
            {"passid", "passid", Fmt::Str, Cond::Eq, "通行id", false, false, true, true},
            {"paycardid", "paycardid", Fmt::Str, Cond::Eq, "支付id", false, false, true, true},
            {"payfee", "payfee", Fmt::Long, Cond::Eq, "应收金额", false, false, true, true},
            {"paytype", "paytype", Fmt::Str, Cond::Eq, "支付类型", false, false, true, true},
            {"provfee", "provfee", Fmt::Long, Cond::Eq, nullptr, false, false, true, true},
            {"provtranscount", "provtranscount", Fmt::Int, Cond::Eq, "本省交易成功次数", false, false, true, true},
            {"provincecount", "provincecount", Fmt::Int, Cond::Eq, "通行省份个数", false, false, true, true},
            {"shift", "shift", Fmt::Str, Cond::Eq, "工班号", false, false, true, true},
            {"receivetime", "receivetime", Fmt::DateYmd, Cond::Eq, "接收时间", false, false, true, true},
            {"shortfee", "shortfee", Fmt::Long, Cond::Eq, "最短收费金额", false, false, true, true},
            {"shortfeemileage", "shortfeemileage", Fmt::Long, Cond::Eq, "最短路径里程数", false, false, true, true},
            {"signstatus", "signstatus", Fmt::Str, Cond::Eq, "标记状态", false, false, true, true},
            {"spcrateversion", "spcrateversion", Fmt::Str, Cond::Eq, "全网最小费额费率版本号", false, false, true, true},
            {"tac", "tac", Fmt::Str, Cond::Eq, "TAC码", false, false, true, true},
            {"specialtype", "specialtype", Fmt::Str, Cond::Eq, "特殊类型", false, false, true, true},
            {"splitprovince", "splitprovince", Fmt::Str, Cond::Eq, "多条省内交易信息", false, false, true, true},
            {"terminalno", "terminalno", Fmt::Str, Cond::Eq, "终端机编号", false, false, true, true},
            {"terminaltransno", "terminaltransno", Fmt::Str, Cond::Eq, "PSAM卡脱机交易序列号", false, false, true, true},
            {"transfee", "transfee", Fmt::Long, Cond::Eq, "卡面扣费金额", false, false, true, true},
            {"transpaytype", "transpaytype", Fmt::Str, Cond::Eq, "交易支付类型", false, false, true, true},
            {"transtype", "transtype", Fmt::Str, Cond::Eq, "交易类型标识", false, false, true, true},
            {"loadTime", "load_time", Fmt::DateYmd, Cond::Eq, "加载时间", false, false, true, true},
            {"vehiclesignid", "vehiclesignid", Fmt::Str, Cond::Eq, "车牌识别流水号", false, false, true, true},
            {"vehiclesign", "vehiclesign", Fmt::Str, Cond::Eq, "车辆状态标识", false, false, true, true},
            {"gradeLevel", "grade_level", Fmt::Str, Cond::Eq, "分类分级", false, false, true, true},
            {"cid", nullptr, Fmt::Str, Cond::None, "cid", false, false, false, false, nullptr, nullptr},
            {"pageNum", nullptr, Fmt::Int, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"pageSize", nullptr, Fmt::Int, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
        };
        s.orderBy = "t.big_id";
        s.excelSheetName = "收费站出口流水";
        return s;
    }();
    return s;
}

const Spec& specOdsRtSzdnSnapshotFlowAddcode() {
    static const Spec s = [] {
        Spec s;
        s.table = "ods_rt_szdn_snapshot_flow_addcode";
        s.alias = "t";
        s.fields = {
            {"bigId", "big_id", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"datasource", "datasource", Fmt::Str, Cond::Eq, "数据类型", false, false, true, true},
            {"cameratype", "cameratype", Fmt::Str, Cond::Eq, "设备类型", false, false, true, true},
            {"deviceid", "deviceid", Fmt::Str, Cond::Eq, "设备编号", false, false, true, true},
            {"gantrycode", "gantrycode", Fmt::Str, Cond::Eq, "门架编号", false, false, true, true},
            {"gantryname", "gantryname", Fmt::Str, Cond::Like, "门架名称", false, false, true, true},
            {"roadcode", "roadcode", Fmt::Str, Cond::Eq, "所属路线编码", false, false, true, true},
            {"roadname", "roadname", Fmt::Str, Cond::Like, "所属路线名称", false, false, true, true},
            {"sectioncode", "sectioncode", Fmt::Str, Cond::Eq, "所属路段编码", false, false, true, true},
            {"sectionname", "sectionname", Fmt::Str, Cond::Like, "所属路段名称", false, false, true, true},
            {"tollcode", "tollcode", Fmt::Str, Cond::Eq, "所属收费站编码", false, false, true, true},
            {"tollname", "tollname", Fmt::Str, Cond::Like, "所属收费站名称", false, false, true, true},
            {"orgcode", "orgcode", Fmt::Str, Cond::Eq, "所属管理中心机构编码", false, false, true, true},
            {"orgname", "orgname", Fmt::Str, Cond::Like, "所属管理中心机构名称", false, false, true, true},
            {"direction", "direction", Fmt::Int, Cond::Eq, "方向", false, false, true, true},
            {"hexcode", "hexcode", Fmt::Str, Cond::Eq, "门架二进制编号", false, false, true, true},
            {"pileno", "pileno", Fmt::Str, Cond::Eq, "桩号", false, false, true, true},
            {"lon", "lon", Fmt::Double, Cond::Eq, "经度", false, false, true, true},
            {"lat", "lat", Fmt::Double, Cond::Eq, "纬度", false, false, true, true},
            {"deviceip", "deviceip", Fmt::Str, Cond::Eq, "设备IP", false, false, true, true},
            {"siteid", "siteid", Fmt::Long, Cond::Eq, "站点ID", false, false, true, true},
            {"laneid", "laneid", Fmt::Int, Cond::Eq, "车道编号", false, false, true, true},
            {"snapshottimeunix", "snapshottimeunix", Fmt::Long, Cond::Eq, "抓拍时间Unix格式", false, false, true, true},
            {"snapshottime", "snapshottime", Fmt::DateIso, Cond::Eq, nullptr, false, false, true, true},
            {"receivedtimeunix", "receivedtimeunix", Fmt::Long, Cond::Eq, "接收时间Unix格式", false, false, true, true},
            {"receivedtime", "receivedtime", Fmt::DateYmd, Cond::Eq, "接收时间", false, false, true, true},
            {"platenumber", "platenumber", Fmt::Str, Cond::Eq, "车牌号", false, false, true, true},
            {"platecolor", "platecolor", Fmt::Str, Cond::Eq, "车牌颜色", false, false, true, true},
            {"platecolorcode", "platecolorcode", Fmt::Int, Cond::Eq, "车牌颜色编码", false, false, true, true},
            {"platetype", "platetype", Fmt::Str, Cond::Eq, "车牌类型", false, false, true, true},
            {"platetypecode", "platetypecode", Fmt::Int, Cond::Eq, "车牌类型编码", false, false, true, true},
            {"plateconfidence", "plateconfidence", Fmt::Int, Cond::Eq, "车牌置信度", false, false, true, true},
            {"carbrand", "carbrand", Fmt::Str, Cond::Eq, "车辆品牌", false, false, true, true},
            {"carcolor", "carcolor", Fmt::Str, Cond::Eq, "车辆颜色", false, false, true, true},
            {"carcolorcode", "carcolorcode", Fmt::Int, Cond::Eq, "车辆颜色编码", false, false, true, true},
            {"cartype", "cartype", Fmt::Str, Cond::Eq, "车辆类型", false, false, true, true},
            {"cartypecode", "cartypecode", Fmt::Int, Cond::Eq, "车辆类型编码", false, false, true, true},
            {"cardirection", "cardirection", Fmt::Str, Cond::Eq, "行驶方向", false, false, true, true},
            {"snappicturepath", "snappicturepath", Fmt::Str, Cond::Eq, "图片路径", false, false, true, true},
            {"loadtime", "loadtime", Fmt::DateYmd, Cond::Eq, "加载时间", false, false, true, true},
            {"gradelevel", "gradelevel", Fmt::Int, Cond::Eq, "分类分级", false, false, true, true},
            {"datauuid", "datauuid", Fmt::Str, Cond::Eq, "uuid", false, false, true, true},
            {"reserve3", "reserve3", Fmt::Str, Cond::Eq, "备用字段", false, false, true, true},
            {"id", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"snapshottimeStr", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"applyTime1", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"applyTime2", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"pageNum", nullptr, Fmt::Int, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"pageSize", nullptr, Fmt::Int, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"directionStr", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"sectionCodeStr", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"type", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"code", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
        };
        s.orderBy = "t.big_id";
        s.excelSheetName = "门架抓拍流水";
        return s;
    }();
    return s;
}

const Spec& specOdsRtSzdnSnapshotFlowProvcaptureAddcode() {
    static const Spec s = [] {
        Spec s;
        s.table = "ods_rt_szdn_snapshot_flow_provcapture_addcode";
        s.alias = "t";
        s.fields = {
            {"bigId", "big_id", Fmt::Long, Cond::Eq, nullptr, true, false, true, true},
            {"deviceip", "deviceip", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"tailcapturetimeunix", "tailcapturetimeunix", Fmt::Long, Cond::Eq, nullptr, false, false, true, true},
            {"tailcapturetime", "tailcapturetime", Fmt::DateIso, Cond::Eq, nullptr, false, false, true, true},
            {"extendattribute", "extendattribute", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"smallsideimagewidth", "smallsideimagewidth", Fmt::Int, Cond::Eq, nullptr, false, false, true, true},
            {"axletype", "axletype", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"smallsideimageheight", "smallsideimageheight", Fmt::Int, Cond::Eq, "小侧图高度", false, false, true, true},
            {"platecolorcode", "platecolorcode", Fmt::Int, Cond::Eq, "车牌颜色编码", false, false, true, true},
            {"platecolor", "platecolor", Fmt::Str, Cond::Eq, "车牌颜色", false, false, true, true},
            {"cover", "cover", Fmt::Str, Cond::Eq, "遮挡信息", false, false, true, true},
            {"averageauthoritative", "averageauthoritative", Fmt::Int, Cond::Eq, "平均可信度", false, false, true, true},
            {"headlanecode", "headlanecode", Fmt::Int, Cond::Eq, "车头车道号", false, false, true, true},
            {"specialvehicle", "specialvehicle", Fmt::Int, Cond::Eq, "特殊车辆标识", false, false, true, true},
            {"carlength", "carlength", Fmt::Int, Cond::Eq, "车长", false, false, true, true},
            {"resulttype", "resulttype", Fmt::Str, Cond::Eq, "结果类型", false, false, true, true},
            {"carhight", "carhight", Fmt::Int, Cond::Eq, "车高", false, false, true, true},
            {"carmodelscode", "carmodelscode", Fmt::Int, Cond::Eq, "车型编码", false, false, true, true},
            {"carmodels", "carmodels", Fmt::Str, Cond::Eq, "车型", false, false, true, true},
            {"laneposition", "laneposition", Fmt::Str, Cond::Eq, "车道位置", false, false, true, true},
            {"firstauthoritative", "firstauthoritative", Fmt::Int, Cond::Eq, "首字可信度", false, false, true, true},
            {"tailplateimageheight", "tailplateimageheight", Fmt::Int, Cond::Eq, "车尾车牌图高度", false, false, true, true},
            {"axlecount", "axlecount", Fmt::Int, Cond::Eq, "车轴数", false, false, true, true},
            {"plateimagewidth", "plateimagewidth", Fmt::Int, Cond::Eq, "车牌图宽度", false, false, true, true},
            {"specialclass", "specialclass", Fmt::Str, Cond::Eq, "特殊类别", false, false, true, true},
            {"tailplatenumber", "tailplatenumber", Fmt::Str, Cond::Eq, "车尾车牌号", false, false, true, true},
            {"tailimage", "tailimage", Fmt::Str, Cond::Eq, "车尾图路径", false, false, true, true},
            {"sidecapturetimeunix", "sidecapturetimeunix", Fmt::Long, Cond::Eq, nullptr, false, false, true, true},
            {"sidecapturetime", "sidecapturetime", Fmt::DateIso, Cond::Eq, nullptr, false, false, true, true},
            {"sidelanecode", "sidelanecode", Fmt::Int, Cond::Eq, "车身车道号", false, false, true, true},
            {"wheelbase", "wheelbase", Fmt::Int, Cond::Eq, "轴距", false, false, true, true},
            {"attached", "attached", Fmt::Str, Cond::Eq, "附加信息", false, false, true, true},
            {"wheelcount", "wheelcount", Fmt::Int, Cond::Eq, "车轮数量", false, false, true, true},
            {"guid", "guid", Fmt::Str, Cond::Eq, "全局唯一标识符", false, false, true, true},
            {"sideimagewidth", "sideimagewidth", Fmt::Int, Cond::Eq, "车身图宽度", false, false, true, true},
            {"plateimageheight", "plateimageheight", Fmt::Int, Cond::Eq, "车牌图高度", false, false, true, true},
            {"datasource", "datasource", Fmt::Str, Cond::Eq, "数据来源", false, false, true, true},
            {"carclass", "carclass", Fmt::Str, Cond::Eq, "车辆分类", false, false, true, true},
            {"gantryid", "gantryid", Fmt::Str, Cond::Eq, "门架编号", false, false, true, true},
            {"smallsideimage", "smallsideimage", Fmt::Str, Cond::Eq, "小侧图路径", false, false, true, true},
            {"headimageheight", "headimageheight", Fmt::Int, Cond::Eq, "车头图高度", false, false, true, true},
            {"sidescenetypecode", "sidescenetypecode", Fmt::Int, Cond::Eq, "车侧拍摄场景编码", false, false, true, true},
            {"sidescenetype", "sidescenetype", Fmt::Str, Cond::Eq, "车侧拍摄场景", false, false, true, true},
            {"tailimagewidth", "tailimagewidth", Fmt::Int, Cond::Eq, "车尾图宽度", false, false, true, true},
            {"envstate", "envstate", Fmt::Str, Cond::Eq, "环境状态", false, false, true, true},
            {"headscenetypecode", "headscenetypecode", Fmt::Int, Cond::Eq, "车头拍摄场景编码", false, false, true, true},
            {"headscenetype", "headscenetype", Fmt::Str, Cond::Eq, "车头拍摄场景", false, false, true, true},
            {"sidedrivingdirectioncode", "sidedrivingdirectioncode", Fmt::Int, Cond::Eq, "车侧行驶方向编码", false, false, true, true},
            {"sidedrivingdirection", "sidedrivingdirection", Fmt::Str, Cond::Eq, "车侧行驶方向", false, false, true, true},
            {"sideimageheight", "sideimageheight", Fmt::Int, Cond::Eq, "车身图高度", false, false, true, true},
            {"speed", "speed", Fmt::Str, Cond::Eq, "车速", false, false, true, true},
            {"tailplateimage", "tailplateimage", Fmt::Str, Cond::Eq, "车尾车牌图路径", false, false, true, true},
            {"headdrivingdirectioncode", "headdrivingdirectioncode", Fmt::Int, Cond::Eq, "车头行驶方向编码", false, false, true, true},
            {"headdrivingdirection", "headdrivingdirection", Fmt::Str, Cond::Eq, "车头行驶方向", false, false, true, true},
            {"cartype", "cartype", Fmt::Str, Cond::Eq, "车辆类型", false, false, true, true},
            {"plateimage", "plateimage", Fmt::Str, Cond::Eq, "车牌图路径", false, false, true, true},
            {"changelane", "changelane", Fmt::Str, Cond::Eq, "变道信息", false, false, true, true},
            {"sideimage", "sideimage", Fmt::Str, Cond::Eq, "车身图路径", false, false, true, true},
            {"tailplateposition", "tailplateposition", Fmt::Str, Cond::Eq, "车尾车牌位置", false, false, true, true},
            {"headimagewidth", "headimagewidth", Fmt::Int, Cond::Eq, "车头图宽度", false, false, true, true},
            {"headimage", "headimage", Fmt::Str, Cond::Eq, "车头图路径", false, false, true, true},
            {"carweight", "carweight", Fmt::Int, Cond::Eq, "车重", false, false, true, true},
            {"tailimageheight", "tailimageheight", Fmt::Int, Cond::Eq, "车尾图高度", false, false, true, true},
            {"devicecode", "devicecode", Fmt::Str, Cond::Eq, "设备编号", false, false, true, true},
            {"platenumber", "platenumber", Fmt::Str, Cond::Eq, "车牌号码", false, false, true, true},
            {"tailplatecolorcode", "tailplatecolorcode", Fmt::Int, Cond::Eq, "车尾车牌颜色编码", false, false, true, true},
            {"tailplatecolor", "tailplatecolor", Fmt::Str, Cond::Eq, "车尾车牌颜色", false, false, true, true},
            {"uploadtimeunix", "uploadtimeunix", Fmt::Long, Cond::Eq, nullptr, false, false, true, true},
            {"uploadtime", "uploadtime", Fmt::DateIso, Cond::Eq, nullptr, false, false, true, true},
            {"impostoraxlecount", "impostoraxlecount", Fmt::Int, Cond::Eq, "假轴数", false, false, true, true},
            {"taillanecode", "taillanecode", Fmt::Int, Cond::Eq, "车尾车道号", false, false, true, true},
            {"siteid", "siteid", Fmt::Int, Cond::Eq, "站点ID", false, false, true, true},
            {"headcapturetimeunix", "headcapturetimeunix", Fmt::Long, Cond::Eq, nullptr, false, false, true, true},
            {"headcapturetime", "headcapturetime", Fmt::DateIso, Cond::Eq, nullptr, false, false, true, true},
            {"plateposition", "plateposition", Fmt::Str, Cond::Eq, "车牌位置", false, false, true, true},
            {"tailplateimagewidth", "tailplateimagewidth", Fmt::Int, Cond::Eq, "车尾车牌图宽度", false, false, true, true},
            {"loadtime", "loadtime", Fmt::DateIso, Cond::Eq, nullptr, false, false, true, true},
            {"gradelevel", "gradelevel", Fmt::Int, Cond::Eq, nullptr, false, false, true, true},
            {"datauuid", "datauuid", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"reserve1", "reserve1", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"reserve2", "reserve2", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"reserve3", "reserve3", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
        };
        s.orderBy = "t.big_id";
        s.excelSheetName = "OdsRtSzdnSnapshotFlowProvcaptureAddcode";
        return s;
    }();
    return s;
}

const Spec& specOdsRtSzdnSnapshotFlowStationcaptureAddcode() {
    static const Spec s = [] {
        Spec s;
        s.table = "ods_rt_szdn_snapshot_flow_stationcapture_addcode";
        s.alias = "t";
        s.fields = {
            {"bigId", "big_id", Fmt::Long, Cond::Eq, nullptr, true, false, true, true},
            {"datasource", "datasource", Fmt::Str, Cond::Eq, "数据类型", false, false, true, true},
            {"cameratype", "cameratype", Fmt::Str, Cond::Eq, "设备类型", false, false, true, true},
            {"deviceid", "deviceid", Fmt::Str, Cond::Eq, "设备编号", false, false, true, true},
            {"deviceip", "deviceip", Fmt::Str, Cond::Eq, "设备IP", false, false, true, true},
            {"tollcode", "tollcode", Fmt::Str, Cond::Eq, "收费站编码", false, false, true, true},
            {"tollname", "tollname", Fmt::Str, Cond::Like, "收费站名称", false, false, true, true},
            {"orgcode", "orgcode", Fmt::Long, Cond::Eq, "组织机构编码", false, false, true, true},
            {"siteid", "siteid", Fmt::Long, Cond::Eq, "站点ID", false, false, true, true},
            {"laneid", "laneid", Fmt::Int, Cond::Eq, "车道编号", false, false, true, true},
            {"snapshottimeunix", "snapshottimeunix", Fmt::Long, Cond::Eq, "抓拍时间Unix格式", false, false, true, true},
            {"snapshottime", "snapshottime", Fmt::DateYmd, Cond::Eq, "抓拍时间", false, false, true, true},
            {"receivedtimeunix", "receivedtimeunix", Fmt::Long, Cond::Eq, "接收时间Unix格式", false, false, true, true},
            {"receivedtime", "receivedtime", Fmt::DateYmd, Cond::Eq, "接收时间", false, false, true, true},
            {"platenumber", "platenumber", Fmt::Str, Cond::Eq, "车牌号", false, false, true, true},
            {"platecolorcode", "platecolorcode", Fmt::Int, Cond::Eq, "车牌颜色编码", false, false, true, true},
            {"platecolor", "platecolor", Fmt::Str, Cond::Eq, "车牌颜色", false, false, true, true},
            {"platetypecode", "platetypecode", Fmt::Int, Cond::Eq, "车牌类型编码", false, false, true, true},
            {"platetype", "platetype", Fmt::Str, Cond::Eq, "车牌类型", false, false, true, true},
            {"plateconfidence", "plateconfidence", Fmt::Int, Cond::Eq, "车牌置信度", false, false, true, true},
            {"carbrand", "carbrand", Fmt::Str, Cond::Eq, "车辆品牌", false, false, true, true},
            {"carcolorcode", "carcolorcode", Fmt::Int, Cond::Eq, "车辆颜色编码", false, false, true, true},
            {"carcolor", "carcolor", Fmt::Str, Cond::Eq, "车辆颜色", false, false, true, true},
            {"cartypecode", "cartypecode", Fmt::Int, Cond::Eq, "车辆类型编码", false, false, true, true},
            {"cartype", "cartype", Fmt::Str, Cond::Eq, "车辆类型", false, false, true, true},
            {"cardirectioncode", "cardirectioncode", Fmt::Int, Cond::Eq, "行驶方向编码", false, false, true, true},
            {"cardirection", "cardirection", Fmt::Str, Cond::Eq, "行驶方向", false, false, true, true},
            {"snappicturepath", "snappicturepath", Fmt::Str, Cond::Eq, "图片路径", false, false, true, true},
            {"loadtime", "loadtime", Fmt::DateYmd, Cond::Eq, "加载时间", false, false, true, true},
            {"gradelevel", "gradelevel", Fmt::Int, Cond::Eq, "分类分级", false, false, true, true},
            {"datauuid", "datauuid", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"maindirection", "maindirection", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"maindirectionname", "maindirectionname", Fmt::Str, Cond::Like, nullptr, false, false, true, true},
            {"reserve3", "reserve3", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
        };
        s.orderBy = "t.big_id";
        s.excelSheetName = "OdsRtSzdnSnapshotFlowStationcaptureAddcode";
        return s;
    }();
    return s;
}

const Spec& specOdsSzdnGantry() {
    static const Spec s = [] {
        Spec s;
        s.table = "ods_szdn_gantry";
        s.alias = "t";
        s.fields = {
            {"id", "id", Fmt::Str, Cond::Eq, nullptr, true, false, true, true},
            {"gantryCode", "gantry_code", Fmt::Str, Cond::Eq, "门架编号", false, false, true, true},
            {"gantryName", "gantry_name", Fmt::Str, Cond::Like, "门架名称", false, false, true, true},
            {"roadCode", "road_code", Fmt::Str, Cond::Eq, "所属路线编码", false, false, true, true},
            {"sectionCode", "section_code", Fmt::Str, Cond::Eq, "所属路段编码", false, false, true, true},
            {"tollCode", "toll_code", Fmt::Str, Cond::Eq, "所属收费站编码", false, false, true, true},
            {"orgCode", "org_code", Fmt::Str, Cond::Eq, "所属管理中心机构编码", false, false, true, true},
            {"hexCode", "hex_code", Fmt::Str, Cond::Eq, "门架二进制编号", false, false, true, true},
            {"direction", "direction", Fmt::Str, Cond::Eq, "方向", false, false, true, true},
            {"pileNo", "pile_no", Fmt::Str, Cond::Like, "桩号", false, false, true, true},
            {"lon", "lon", Fmt::Str, Cond::Eq, "经度", false, false, true, true},
            {"lat", "lat", Fmt::Str, Cond::Eq, "纬度", false, false, true, true},
            {"isVirtual", "is_virtual", Fmt::Str, Cond::Eq, "是否虚门架", false, false, true, true},
            {"mileage", "mileage", Fmt::Str, Cond::Eq, "里程", false, false, true, true},
            {"boundaryGantryType", "boundary_gantry_type", Fmt::Str, Cond::Eq, "边界门架类型", false, false, true, true},
            {"gantryType", "gantry_type", Fmt::Str, Cond::Eq, "门架类型", false, false, true, true},
            {"cityCode", "city_code", Fmt::Str, Cond::Eq, "城市编码", false, false, true, true},
            {"districtName", "district_name", Fmt::Str, Cond::Like, "行政区名称", false, false, true, true},
            {"belongGroup", "belong_group", Fmt::Str, Cond::Eq, "是否属于集团，0：否；1：是", false, false, true, true},
            {"gantryCodeMerge", "gantry_code_merge", Fmt::Str, Cond::Eq, "门架编号", false, false, true, true},
            {"gantryNameAlias", "gantry_name_alias", Fmt::Str, Cond::Eq, "门架别名", false, false, true, true},
            {"remark", "remark", Fmt::Str, Cond::None, "备注", false, false, true, true},
            {"isData", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"roadName", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"sectionName", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"tollName", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"orgName", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
        };
        s.orderBy = "t.gantry_name";
        s.excelSheetName = "门架信息";
        return s;
    }();
    return s;
}

const Spec& specOdsSzdnGantryIp() {
    static const Spec s = [] {
        Spec s;
        s.table = "ods_szdn_gantry_ip";
        s.alias = "t";
        s.fields = {
            {"id", "id", Fmt::Long, Cond::Eq, nullptr, true, false, true, true},
            {"gantryCode", "gantry_code", Fmt::Str, Cond::Eq, "门架编号", false, false, true, true},
            {"gantryName", "gantry_name", Fmt::Str, Cond::Like, "门架名称", false, false, true, true},
            {"orgCode", "org_code", Fmt::Str, Cond::Eq, "机构编码", false, false, true, true},
            {"ip", "ip", Fmt::Str, Cond::Eq, "设备ip", false, false, true, true},
            {"brand", "brand", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"type", "type", Fmt::Str, Cond::Eq, "类型1是省界门架", false, false, true, true},
            {"odsSzdnGantry", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
        };
        s.orderBy = "t.id";
        s.excelSheetName = "OdsSzdnGantryIp";
        return s;
    }();
    return s;
}

const Spec& specOdsSzdnProvinceBorderVehicleWeightNewstructure() {
    static const Spec s = [] {
        Spec s;
        s.table = "ods_szdn_province_border_vehicle_weight_newstructure";
        s.alias = "t";
        s.fields = {
            {"dataSource", "dataSource", Fmt::Str, Cond::Eq, "数据来源", false, false, true, true},
            {"dataType", "dataType", Fmt::Str, Cond::Eq, "数据类型", false, false, true, true},
            {"plateNo", "plateNo", Fmt::Str, Cond::Eq, "车牌号", false, false, true, true},
            {"siteId", "siteId", Fmt::Str, Cond::Eq, "站点ID", false, false, true, true},
            {"location", "location", Fmt::Str, Cond::Eq, "设备地点", false, false, true, true},
            {"driveNo", "driveNo", Fmt::Long, Cond::Eq, "车道号", false, false, true, true},
            {"plateColor", "plateColor", Fmt::Str, Cond::Eq, "车牌颜色索引", false, false, true, true},
            {"plateColorCode", "plateColorCode", Fmt::Str, Cond::Eq, "车牌颜色代码", false, false, true, true},
            {"plateType", "plateType", Fmt::Str, Cond::Eq, "车牌类型索引", false, false, true, true},
            {"plateTypeCode", "plateTypeCode", Fmt::Str, Cond::Eq, "车牌类型代码", false, false, true, true},
            {"vehicleColor", "vehicleColor", Fmt::Str, Cond::Eq, "车辆颜色代号", false, false, true, true},
            {"vehicleColorCode", "vehicleColorCode", Fmt::Str, Cond::Eq, "车辆颜色代码", false, false, true, true},
            {"vehicleType", "vehicleType", Fmt::Str, Cond::Eq, "车辆类型代号", false, false, true, true},
            {"vehicleTypeCode", "vehicleTypeCode", Fmt::Str, Cond::Eq, "车辆类型代码", false, false, true, true},
            {"vehicleSpeed", "vehicleSpeed", Fmt::Long, Cond::Eq, "车辆速度", false, false, true, true},
            {"isOverweight", "isOverweight", Fmt::Long, Cond::Eq, "是否超载", false, false, true, true},
            {"axleNum", "axleNum", Fmt::Long, Cond::Eq, "轴数", false, false, true, true},
            {"overWeight", "overWeight", Fmt::Long, Cond::Eq, "超重量", false, false, true, true},
            {"vehicleWeight", "vehicleWeight", Fmt::Long, Cond::Eq, "重量", false, false, true, true},
            {"limitWeight", "limitWeight", Fmt::Long, Cond::Eq, "车辆限重", false, false, true, true},
            {"checkTimeUnix", "checkTimeUnix", Fmt::Long, Cond::Eq, "检测时间Unix格式", false, false, true, true},
            {"checkTime", "checkTime", Fmt::DateYmd, Cond::Eq, "检测时间", false, false, true, true},
            {"axleModel", "axleModel", Fmt::Long, Cond::Eq, "轴型", false, false, true, true},
            {"loadRate", "loadRate", Fmt::Long, Cond::Eq, "超载率", false, false, true, true},
            {"axleArray", "axleArray", Fmt::Str, Cond::Eq, "轴型详细数据", false, false, true, true},
            {"weighingImagesArry", "weighingImagesArry", Fmt::Str, Cond::Eq, "图片数组", false, false, true, true},
            {"loadTime", "load_time", Fmt::DateYmd, Cond::Eq, "加载时间", false, false, true, true},
            {"gradeLevel", "grade_level", Fmt::Long, Cond::Eq, "分类分级", false, false, true, true},
            {"datauuid", "datauuid", Fmt::Str, Cond::Eq, "datauuid", true, false, true, true},
            {"reserve1", "reserve1", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"reserve2", "reserve2", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"reserve3", "reserve3", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
        };
        s.excelSheetName = "OdsSzdnProvinceBorderVehicleWeightNewstructure";
        return s;
    }();
    return s;
}

const Spec& specOdsSzdnSection() {
    static const Spec s = [] {
        Spec s;
        s.table = "ods_szdn_section";
        s.alias = "t";
        s.fields = {
            {"id", "id", Fmt::Str, Cond::Eq, nullptr, true, false, true, true},
            {"roadCode", "road_code", Fmt::Str, Cond::Eq, "路线编码", false, false, true, true},
            {"roadName", "road_name", Fmt::Str, Cond::Like, "路线名称", false, false, true, true},
            {"sectionCode", "section_code", Fmt::Str, Cond::Eq, "路段编码", false, false, true, true},
            {"sectionName", "section_name", Fmt::Str, Cond::Like, "路段名称", false, false, true, true},
            {"startPileNo", "start_pile_no", Fmt::Long, Cond::Eq, "起点桩号", false, false, true, true},
            {"endPileNo", "end_pile_no", Fmt::Long, Cond::Eq, "终点桩号", false, false, true, true},
            {"orgCode", "org_code", Fmt::Str, Cond::Eq, "机构代码", false, false, true, true},
            {"orgName", "org_name", Fmt::Str, Cond::Like, "机构名称", false, false, true, true},
            {"orgLevelCode", "org_level_code", Fmt::Str, Cond::Eq, "层级代码", false, false, true, true},
            {"orgCategory", "org_category", Fmt::Str, Cond::Eq, "机构分类", false, false, true, true},
            {"mileage", "mileage", Fmt::Long, Cond::Eq, "里程", false, false, true, true},
            {"openDate", "open_date", Fmt::DateYmd, Cond::Eq, "通车日期", false, false, true, true},
        };
        s.orderBy = "t.road_code,t.section_code";
        s.excelSheetName = "路段信息";
        return s;
    }();
    return s;
}

const Spec& specOdsSzdnToll() {
    static const Spec s = [] {
        Spec s;
        s.table = "ods_szdn_toll";
        s.alias = "t";
        s.fields = {
            {"id", "id", Fmt::Str, Cond::Eq, nullptr, true, false, true, true},
            {"roadCode", "road_code", Fmt::Str, Cond::Eq, "路线编号", false, false, true, true},
            {"idCard", "id_card", Fmt::Str, Cond::Eq, "收费站业务唯一编码", false, false, true, true},
            {"tollCode", "toll_code", Fmt::Str, Cond::Eq, "收费站编号", false, false, true, true},
            {"tollName", "toll_name", Fmt::Str, Cond::Like, "收费站名称", false, false, true, true},
            {"pileNo", "pile_no", Fmt::Str, Cond::Eq, "桩号", false, false, true, true},
            {"orgName", "org_name", Fmt::Str, Cond::Like, "所属机构名称", false, false, true, true},
            {"hexCode", "hex_code", Fmt::Str, Cond::Eq, "收费站HEX编码", false, false, true, true},
            {"stateCode", "state_code", Fmt::Str, Cond::Eq, "国网编号", false, false, true, true},
            {"orgCode", "org_code", Fmt::Str, Cond::Eq, "机构编码", false, false, true, true},
            {"longitude", "longitude", Fmt::Str, Cond::Eq, "经度", false, false, true, true},
            {"latitude", "latitude", Fmt::Str, Cond::Eq, "纬度", false, false, true, true},
            {"openDate", "open_date", Fmt::DateYmd, Cond::Eq, "开通日期", false, false, true, true},
            {"tollAliasName", "toll_alias_name", Fmt::Str, Cond::Like, "收费站别名", false, false, true, true},
            {"inMonitorResource", "in_monitor_resource", Fmt::Str, Cond::Eq, "入口治超监控资源，多个以英文逗号分割", false, false, true, true},
            {"laneMonitorResource", "lane_monitor_resource", Fmt::Str, Cond::Eq, "车道抓拍监控资源，多个以英文逗号分割", false, false, true, true},
            {"squareMonitorResource", "square_monitor_resource", Fmt::Str, Cond::Eq, "广场监控资源，多个以英文逗号分割", false, false, true, true},
            {"dynamicMonitorResource", "dynamic_monitor_resource", Fmt::Str, Cond::Eq, "动环监控资源，多个以英文逗号分割", false, false, true, true},
            {"tollCodeMerge", "toll_code_merge", Fmt::Str, Cond::Eq, "收费站编号", false, false, true, true},
            {"stateCodeMerge", "state_code_merge", Fmt::Str, Cond::Eq, "国网编号", false, false, true, true},
            {"tollNameMerge", "toll_name_merge", Fmt::Str, Cond::Like, "收费站名称", false, false, true, true},
            {"sectionCode", "section_code", Fmt::Str, Cond::Eq, "所属路段编码", false, false, true, true},
            {"tollOrgCode", "toll_org_code", Fmt::Str, Cond::Eq, "收费站对应机构编码", false, false, true, true},
            {"isAccess", "is_access", Fmt::Str, Cond::Eq, "流水是否接入", false, false, true, true},
            {"sectionName", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
        };
        s.orderBy = "t.toll_name";
        s.excelSheetName = "收费站基础信息";
        return s;
    }();
    return s;
}

const Spec& specOdsSzdnTollStationIp() {
    static const Spec s = [] {
        Spec s;
        s.table = "ods_szdn_toll_station_ip";
        s.alias = "t";
        s.fields = {
            {"id", "id", Fmt::Long, Cond::None, nullptr, true, false, true, true},
            {"tollCode", "toll_code", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"tollName", "toll_name", Fmt::Str, Cond::Like, nullptr, false, false, true, true},
            {"orgCode", "org_code", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"ip", "ip", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"brand", "brand", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"odsSzdnToll", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
        };
        s.orderBy = "t.big_id";
        s.excelSheetName = "OdsSzdnTollStationIp";
        return s;
    }();
    return s;
}

const Spec& specOdsYhglVBaseOrg() {
    static const Spec s = [] {
        Spec s;
        s.table = "ods_yhgl_v_base_org";
        s.alias = "t";
        s.fields = {
            {"bigId", "big_id", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"orgCode", "org_code", Fmt::Str, Cond::Eq, "机构代码", false, false, true, true},
            {"orgName", "org_name", Fmt::Str, Cond::Like, "机构名称", false, false, true, true},
            {"orgShortName", "org_short_name", Fmt::Str, Cond::Like, "机构简称", false, false, true, true},
            {"orgParentId", "org_parent_id", Fmt::Str, Cond::Eq, "上级机构ID", false, false, true, true},
            {"orgLevelCode", "org_level_code", Fmt::Str, Cond::Eq, "层级代码", false, false, true, true},
            {"orgIsVirtual", "org_is_virtual", Fmt::Str, Cond::Eq, "是否虚机构 1：虚机构，0：非需机构", false, false, true, true},
            {"orgMaintenance", "org_maintenance", Fmt::Str, Cond::Eq, "是否是养护类", false, false, true, true},
            {"orgSequence", "org_sequence", Fmt::Long, Cond::Eq, "机构顺序", false, false, true, true},
            {"orgIsManager", "org_is_manager", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"orgIsDeleted", "org_is_deleted", Fmt::Str, Cond::Eq, "是否删除 1：是 0：否", false, false, true, true},
            {"orgCategory", "org_category", Fmt::Str, Cond::Eq, "机构分类： 01集团 02公司 03管理中心 10部门 11所 12服务区 13养护区 14站 15项目办 16信息中心 17项目部  99其它", false, false, true, true},
            {"orgIsAuthorized", "org_is_authorized", Fmt::Str, Cond::Eq, "是否授权机构 1：是 0：否", false, false, true, true},
            {"orgAddress", "org_address", Fmt::Str, Cond::Eq, "机构地址", false, false, true, true},
            {"orgIsYhAutarky", "org_is_yh_autarky", Fmt::Str, Cond::Eq, "是自营养护单位", false, false, true, true},
            {"loadTime", "load_time", Fmt::DateYmd, Cond::Eq, "加载时间", false, false, true, true},
            {"gradeLevel", "grade_level", Fmt::Int, Cond::Eq, "分类分级", false, false, true, true},
            {"parentId", nullptr, Fmt::Long, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
        };
        s.orderBy = "t.big_id";
        s.excelSheetName = "机构信息";
        return s;
    }();
    return s;
}

const Spec& specZdataLocationDict() {
    static const Spec s = [] {
        Spec s;
        s.table = "zdata_location_dict";
        s.alias = "t";
        s.fields = {
            {"id", "id", Fmt::Long, Cond::Eq, nullptr, false, false, true, true},
            {"type", "type", Fmt::Str, Cond::Eq, "类型", false, false, true, true},
            {"name", "name", Fmt::Str, Cond::Like, "收费站", false, false, true, true},
            {"rawCode", "raw_code", Fmt::Str, Cond::Eq, "轨迹表和实时轨迹code", false, false, true, true},
            {"standardCode", "standard_code", Fmt::Str, Cond::Eq, "收费站/门架code", false, false, true, true},
            {"roadcode", "roadcode", Fmt::Str, Cond::Eq, "路线编码", false, false, true, true},
            {"roadname", "roadname", Fmt::Str, Cond::Like, "路线名称", false, false, true, true},
            {"sectioncode", "sectioncode", Fmt::Str, Cond::Eq, "路段编码", false, false, true, true},
            {"sectionname", "sectionname", Fmt::Str, Cond::Like, "路段名称", false, false, true, true},
            {"tollcode", "tollcode", Fmt::Str, Cond::Eq, "收费站编码", false, false, true, true},
            {"tollname", "tollname", Fmt::Str, Cond::Like, "收费站名称", false, false, true, true},
            {"orgcode", "orgcode", Fmt::Str, Cond::Eq, "组织机构编码", false, false, true, true},
            {"orgname", "orgname", Fmt::Str, Cond::Like, "组织机构名称", false, false, true, true},
            {"createdAt", "created_at", Fmt::DateYmd, Cond::Eq, "创建时间", false, false, true, true},
            {"updatedAt", "updated_at", Fmt::DateYmd, Cond::Eq, "修改时间", false, false, true, true},
        };
        s.excelSheetName = "ZdataLocationDict";
        return s;
    }();
    return s;
}

const Spec& specZdataTrailFitting() {
    static const Spec s = [] {
        Spec s;
        s.table = "zdata_trail_fitting";
        s.alias = "t";
        s.extraWhere = " and t.del_flag = '0'";
        s.fields = {
            {"cid", "cid", Fmt::Str, Cond::None, nullptr, false, false, true, true},
            {"enaxlecount", "enaxlecount", Fmt::Int, Cond::Eq, "入口车轴数", false, false, true, true},
            {"entime", "entime", Fmt::DateYmd, Cond::Eq, "入口时间", false, false, true, true},
            {"entolllaneid", "entolllaneid", Fmt::Str, Cond::Eq, "入口车道编号", false, false, true, true},
            {"entollstationid", "entollstationid", Fmt::Str, Cond::Eq, "入口收费站编号", false, false, true, true},
            {"entollstationname", "entollstationname", Fmt::Str, Cond::Like, "入口收费站名称", false, false, true, true},
            {"envehicleclass", "envehicleclass", Fmt::Int, Cond::Eq, "入口车型分类", false, false, true, true},
            {"envehicleid", "envehicleid", Fmt::Str, Cond::Eq, "入口车辆编号", false, false, true, true},
            {"envehicletype", "envehicletype", Fmt::Int, Cond::Eq, "入口车辆类型代码", false, false, true, true},
            {"enweight", "enweight", Fmt::Long, Cond::Eq, "入口称重", false, false, true, true},
            {"extime", "extime", Fmt::DateIso, Cond::Eq, "出口时间", false, false, true, true},
            {"extolllaneid", "extolllaneid", Fmt::Str, Cond::Eq, "出口车道编号", false, false, true, true},
            {"extollstationid", "extollstationid", Fmt::Str, Cond::Eq, "出口收费站编号", false, false, true, true},
            {"extollstationname", "extollstationname", Fmt::Str, Cond::Like, "出口收费站名称", false, false, true, true},
            {"exvehicleclass", "exvehicleclass", Fmt::Int, Cond::Eq, "出口车型分类", false, false, true, true},
            {"exvehicleid", "exvehicleid", Fmt::Str, Cond::Eq, "出口车辆编号", false, false, true, true},
            {"exvehicletype", "exvehicletype", Fmt::Int, Cond::Eq, "出口车辆类型代码", false, false, true, true},
            {"exweight", "exweight", Fmt::Long, Cond::Eq, "出口称重", false, false, true, true},
            {"trailpoints", "trailpoints", Fmt::Str, Cond::Eq, "拟合轨迹点集合", false, false, true, true},
        };
        s.excelSheetName = "ZdataTrailFitting";
        return s;
    }();
    return s;
}

const Spec& specZdataTrailTracks() {
    static const Spec s = [] {
        Spec s;
        s.table = "zdata_trail_tracks";
        s.alias = "t";
        s.fields = {
            {"uuid", "uuid", Fmt::Str, Cond::Eq, "唯一标识符", true, false, true, true},
            {"type", "type", Fmt::Int, Cond::Eq, "轨迹类型", false, false, true, true},
            {"pointCount", "point_count", Fmt::Long, Cond::Eq, "轨迹点数量", false, false, true, true},
            {"plateKey", "plate_key", Fmt::Str, Cond::Like, "车牌唯一标识", false, false, true, true},
            {"enterTime", "enter_time", Fmt::DateYmdHms, Cond::Eq, "进入时间", false, false, true, true},
            {"exitTime", "exit_time", Fmt::DateYmdHms, Cond::Eq, "离开时间", false, false, true, true},
            {"trailPoints", "trail_points", Fmt::Str, Cond::Eq, "轨迹点集合，推荐存 JSON 格式，包含坐标/时间/速度等信息", false, false, true, true},
            {"enterLocationcode", "enter_locationcode", Fmt::Str, Cond::None, "进入位置code", false, false, true, true},
            {"exitLocationcode", "exit_locationcode", Fmt::Str, Cond::None, "离开位置code", false, false, true, true},
            {"trackJosn", "track_josn", Fmt::Str, Cond::None, "集合详情", false, false, true, true},
            {"enaxlecount", "enaxlecount", Fmt::Int, Cond::None, "入口车轴数", false, false, true, true},
            {"entolllaneid", "entolllaneid", Fmt::Str, Cond::None, "入口车道编号", false, false, true, true},
            {"entollstationid", "entollstationid", Fmt::Str, Cond::Eq, "入口收费站编号", false, false, true, true},
            {"entollstationname", "entollstationname", Fmt::Str, Cond::None, "入口收费站名称", false, false, true, true},
            {"envehicleclass", "envehicleclass", Fmt::Str, Cond::None, "入口车型分类", false, false, true, true},
            {"envehicleid", "envehicleid", Fmt::Str, Cond::None, "入口车辆编号", false, false, true, true},
            {"envehicletype", "envehicletype", Fmt::Str, Cond::None, "入口车辆类型代码", false, false, true, true},
            {"enweight", "enweight", Fmt::Double, Cond::None, "入口称重", false, false, true, true},
            {"extolllaneid", "extolllaneid", Fmt::Str, Cond::None, "出口车道编号", false, false, true, true},
            {"extollstationid", "extollstationid", Fmt::Str, Cond::None, "出口收费站编号", false, false, true, true},
            {"extollstationname", "extollstationname", Fmt::Str, Cond::None, "出口收费站名称", false, false, true, true},
            {"exvehicleclass", "exvehicleclass", Fmt::Str, Cond::None, "出口车型分类", false, false, true, true},
            {"exvehicleid", "exvehicleid", Fmt::Str, Cond::None, "出口车辆编号", false, false, true, true},
            {"exvehicletype", "exvehicletype", Fmt::Str, Cond::None, "出口车辆类型代码", false, false, true, true},
            {"exweight", "exweight", Fmt::Double, Cond::None, "出口称重", false, false, true, true},
            {"startLon", "start_lon", Fmt::Str, Cond::None, "入口收费站经度", false, false, true, true},
            {"stratLat", "strat_lat", Fmt::Str, Cond::None, "入口收费站维度", false, false, true, true},
            {"endLon", "end_lon", Fmt::Str, Cond::None, "出口收费站经度", false, false, true, true},
            {"endLat", "end_lat", Fmt::Str, Cond::None, "出口收费站维度", false, false, true, true},
            {"firtStationCode", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"firtStationName", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"firtStationTime", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"plateColor", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"carType", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"carNo", nullptr, Fmt::Str, Cond::Eq, nullptr, false, false, false, false, "plate_key", nullptr},
            {"carVehicle", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"carNum", nullptr, Fmt::Long, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"escapedType", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"passType", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"escapedTypeRemark", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"applyTime1", nullptr, Fmt::Str, Cond::Gte, nullptr, false, false, false, false, "enter_time", nullptr},
            {"applyTime2", nullptr, Fmt::Str, Cond::Lte, nullptr, false, false, false, false, "enter_time", nullptr},
            {"isCylx", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"flag", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"startLonDec", nullptr, Fmt::Double, Cond::None, "入口收费站经度", false, false, false, false, nullptr, nullptr},
            {"stratLatDec", nullptr, Fmt::Double, Cond::None, "入口收费站维度", false, false, false, false, nullptr, nullptr},
            {"endLonDec", nullptr, Fmt::Double, Cond::None, "出口收费站经度", false, false, false, false, nullptr, nullptr},
            {"endLatDec", nullptr, Fmt::Double, Cond::None, "出口收费站维度", false, false, false, false, nullptr, nullptr},
            {"uuidList", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"passCount", nullptr, Fmt::Int, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"escapedTfcj", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
        };
        s.orderBy = "t.enter_time desc";
        s.excelSheetName = "ZdataTrailTracks";
        return s;
    }();
    return s;
}

void registerBaseArea(Router& r) {
    {
        // ruoyi-system/src/main/java/com/ruoyi/base/domain/BaseConfigServiceArea.java
        // ruoyi-system/src/main/resources/mapper/base/BaseConfigServiceAreaMapper.xml
        Perms p;
        p.list = "base:configServiceArea:list";
        registerCrud(r, "/base/configServiceArea", specBaseConfigServiceArea(), p, "fwqbm");
        registerListVariant(r, "/base/configServiceArea/listQuery", specBaseConfigServiceArea(), ListKind::Plain);
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/base/domain/CarWarningConfig.java
        // ruoyi-system/src/main/resources/mapper/base/CarWarningConfigMapper.xml
        Perms p;
        p.list = "base:config:list";
        registerCrud(r, "/base/config", specCarWarningConfig(), p, "id");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/base/domain/DwdLcztFwqjcxx.java
        // ruoyi-system/src/main/resources/mapper/base/DwdLcztFwqjcxxMapper.xml
        Perms p;
        registerCrud(r, "/base/fwqjcxx", specDwdLcztFwqjcxx(), p, "agentPk");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/base/domain/DwdLcztSfsjcxx.java
        // ruoyi-system/src/main/resources/mapper/base/DwdLcztSfsjcxxMapper.xml
        Perms p;
        registerCrud(r, "/base/sfsjcxx", specDwdLcztSfsjcxx(), p, "agentPk");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/base/domain/DwdLcztSfzjcxx.java
        // ruoyi-system/src/main/resources/mapper/base/DwdLcztSfzjcxxMapper.xml
        Perms p;
        registerCrud(r, "/base/sfzjcxx", specDwdLcztSfzjcxx(), p, "agentPk");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/base/domain/Geometry.java
        // ruoyi-system/src/main/resources/mapper/base/GeometryMapper.xml
        Perms p;
        p.list = "base:geometry:list";
        registerCrud(r, "/base/geometry", specGeometry(), p, "ID");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsCxztFwqclls.java
        // ruoyi-system/src/main/resources/mapper/base/OdsCxztFwqcllsMapper.xml
        Perms p;
        p.list = "manager:fwqclls:list";
        registerCrud(r, "/manager/fwqclls", specOdsCxztFwqclls(), p, "bigId");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsLwzxsfsjFeeGantryFusion01.java
        // ruoyi-system/src/main/resources/mapper/base/OdsLwzxsfsjFeeGantryFusion01Mapper.xml
        Perms p;
        p.list = "base:feeGantry:list";
        registerCrud(r, "/base/feeGantry", specOdsLwzxsfsjFeeGantryFusion01(), p, "bigId");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsLwzxsfsjFeeRecords01.java
        // ruoyi-system/src/main/resources/mapper/base/OdsLwzxsfsjFeeRecords01Mapper.xml
        Perms p;
        p.list = "base:feerecords:list";
        p.exportList = "base:feerecords:list";
        registerCrud(r, "/base/feerecords", specOdsLwzxsfsjFeeRecords01(), p, "bigId");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsLwzxsfsjFeeStationEnter01.java
        // ruoyi-system/src/main/resources/mapper/base/OdsLwzxsfsjFeeStationEnter01Mapper.xml
        Perms p;
        registerCrud(r, "/base/feeStationEnter", specOdsLwzxsfsjFeeStationEnter01(), p, "bigId");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsLwzxsfsjFeeStationExit01.java
        // ruoyi-system/src/main/resources/mapper/base/OdsLwzxsfsjFeeStationExit01Mapper.xml
        Perms p;
        p.list = "base:feestationexit:list";
        registerCrud(r, "/base/feestationexit", specOdsLwzxsfsjFeeStationExit01(), p, "bigId");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsRtSzdnSnapshotFlowAddcode.java
        // ruoyi-system/src/main/resources/mapper/base/OdsRtSzdnSnapshotFlowAddcodeMapper.xml
        Perms p;
        p.list = "base:snapshotflow:list";
        p.exportList = "base:snapshotflow:list";
        registerCrud(r, "/base/snapshotflow", specOdsRtSzdnSnapshotFlowAddcode(), p, "bigId");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsRtSzdnSnapshotFlowProvcaptureAddcode.java
        // ruoyi-system/src/main/resources/mapper/base/OdsRtSzdnSnapshotFlowProvcaptureAddcodeMapper.xml
        Perms p;
        registerCrud(r, "/base/provcapture", specOdsRtSzdnSnapshotFlowProvcaptureAddcode(), p, "bigId");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsRtSzdnSnapshotFlowStationcaptureAddcode.java
        // ruoyi-system/src/main/resources/mapper/base/OdsRtSzdnSnapshotFlowStationcaptureAddcodeMapper.xml
        Perms p;
        registerCrud(r, "/base/stationcapture", specOdsRtSzdnSnapshotFlowStationcaptureAddcode(), p, "bigId");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsSzdnGantry.java
        // ruoyi-system/src/main/resources/mapper/base/OdsSzdnGantryMapper.xml
        Perms p;
        registerCrud(r, "/base/gantry", specOdsSzdnGantry(), p, "id");
        registerListVariant(r, "/base/gantry/listAll", specOdsSzdnGantry(), ListKind::Paged);
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsSzdnGantryIp.java
        // ruoyi-system/src/main/resources/mapper/base/OdsSzdnGantryIpMapper.xml
        Perms p;
        registerCrud(r, "/base/gantryIp", specOdsSzdnGantryIp(), p, "id");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsSzdnProvinceBorderVehicleWeightNewstructure.java
        // ruoyi-system/src/main/resources/mapper/base/OdsSzdnProvinceBorderVehicleWeightNewstructureMapper.xml
        Perms p;
        registerCrud(r, "/base/vehicleweight", specOdsSzdnProvinceBorderVehicleWeightNewstructure(), p, "dataSource");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsSzdnSection.java
        // ruoyi-system/src/main/resources/mapper/base/OdsSzdnSectionMapper.xml
        Perms p;
        registerCrud(r, "/base/section", specOdsSzdnSection(), p, "id");
        registerListVariant(r, "/base/section/listAll", specOdsSzdnSection(), ListKind::Paged);
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsSzdnToll.java
        // ruoyi-system/src/main/resources/mapper/base/OdsSzdnTollMapper.xml
        Perms p;
        registerCrud(r, "/base/toll", specOdsSzdnToll(), p, "id");
        registerListVariant(r, "/base/toll/listAll", specOdsSzdnToll(), ListKind::Paged);
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsSzdnTollStationIp.java
        // ruoyi-system/src/main/resources/mapper/base/OdsSzdnTollStationIpMapper.xml
        Perms p;
        registerCrud(r, "/base/tollStationIp", specOdsSzdnTollStationIp(), p, "id");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsYhglVBaseOrg.java
        // ruoyi-system/src/main/resources/mapper/base/OdsYhglVBaseOrgMapper.xml
        Perms p;
        registerCrud(r, "/base/org", specOdsYhglVBaseOrg(), p, "bigId");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/base/domain/ZdataLocationDict.java
        // ruoyi-system/src/main/resources/mapper/base/ZdataLocationDictMapper.xml
        Perms p;
        registerCrud(r, "/base/location", specZdataLocationDict(), p, "id");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/base/domain/ZdataTrailFitting.java
        // ruoyi-system/src/main/resources/mapper/base/ZdataTrailFittingMapper.xml
        Perms p;
        registerCrud(r, "/base/fitting", specZdataTrailFitting(), p, "cid");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/base/domain/ZdataTrailTracks.java
        // ruoyi-system/src/main/resources/mapper/base/ZdataTrailTracksMapper.xml
        Perms p;
        registerCrud(r, "/base/trailtracks", specZdataTrailTracks(), p, "uuid");
    }
}

} // namespace cm::web::crud
