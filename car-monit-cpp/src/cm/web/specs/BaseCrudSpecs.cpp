// 由 scripts/gen_crud_spec.py 生成（area=base）。
// 重新生成: python scripts/gen_crud_spec.py --area base
//
// 只覆盖同构 CRUD：list / export / getInfo / add / edit / remove。
// 非 CRUD 接口、唯一性校验、tenant 过滤、软删除、外部服务依赖等仍由手写控制器负责
// （src/cm/web/controller/**）。解析不到的控制器整只跳过，见生成器输出。
#include "cm/framework/web/Router.hpp"
#include "cm/framework/web/crud/CrudSpec.hpp"

namespace cm::web::crud {

void registerBaseArea(Router& r) {
    {
        // ruoyi-system/src/main/java/com/ruoyi/base/domain/BaseConfigServiceArea.java
        // ruoyi-system/src/main/resources/mapper/base/BaseConfigServiceAreaMapper.xml
        Spec s;
        s.table = "base_config_service_area";
        s.alias = "t";
        s.fields = {
            {"fwqbm", "fwqbm", Fmt::Str, Cond::Eq, "判定进入的服务区编码", false, false},
            {"fwqmc", "fwqmc", Fmt::Str, Cond::Eq, "判定进入的服务区名称", false, false},
            {"lon", "lon", Fmt::Str, Cond::Eq, "经度", false, false},
            {"lat", "lat", Fmt::Str, Cond::Eq, "维度", false, false},
            {"roadCode", "road_code", Fmt::Str, Cond::Eq, "路线编码", false, false},
            {"sectionCode", "section_code", Fmt::Str, Cond::Eq, "路段编码", false, false},
            {"pileNo", "pile_no", Fmt::Str, Cond::Eq, "桩号", false, false},
        };
        s.excelSheetName = "服务区";
        Perms p;
        p.list = "base:configServiceArea:list";
        registerCrud(r, "/base/configServiceArea", s, p, "fwqbm");
        registerListVariant(r, "/base/configServiceArea/listQuery", s, ListKind::Plain);
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/base/domain/CarWarningConfig.java
        // ruoyi-system/src/main/resources/mapper/base/CarWarningConfigMapper.xml
        Spec s;
        s.table = "car_warning_config";
        s.alias = "t";
        s.fields = {
            {"id", "id", Fmt::Str, Cond::Eq, nullptr, true, false},
            {"gantryCodeIn", "gantry_code_in", Fmt::Str, Cond::Eq, "进入门架编号", false, false},
            {"gantryNameIn", "gantry_name_in", Fmt::Str, Cond::Like, "进入门架名称", false, false},
            {"gantryCodeOut", "gantry_code_out", Fmt::Str, Cond::Eq, "出去门架编号", false, false},
            {"gantryNameOut", "gantry_name_out", Fmt::Str, Cond::Like, "出去门架名称", false, false},
            {"timeSpan", "time_span", Fmt::Long, Cond::Eq, "判定时间间隔", false, false},
            {"fwqbm", "fwqbm", Fmt::Str, Cond::Eq, "判定进入的服务区编码", false, false},
            {"fwqmc", "fwqmc", Fmt::Str, Cond::Like, "判定进入的服务区名称", false, false},
            {"lon", "lon", Fmt::Str, Cond::Eq, "经度", false, false},
            {"lat", "lat", Fmt::Str, Cond::Eq, "维度", false, false},
            {"roadCode", "road_code", Fmt::Str, Cond::Eq, "路线编码", false, false},
            {"sectionCode", "section_code", Fmt::Str, Cond::Eq, "路段编码", false, false},
            {"pileNo", "pile_no", Fmt::Str, Cond::Eq, "桩号", false, false},
            {"remark", "remark", Fmt::Str, Cond::None, "备注", false, false},
        };
        s.excelSheetName = "服务区判定规则";
        Perms p;
        p.list = "base:config:list";
        registerCrud(r, "/base/config", s, p, "id");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/base/domain/DwdLcztFwqjcxx.java
        // ruoyi-system/src/main/resources/mapper/base/DwdLcztFwqjcxxMapper.xml
        Spec s;
        s.table = "dwd_lczt_fwqjcxx";
        s.alias = "t";
        s.fields = {
            {"agentPk", "agent_pk", Fmt::Str, Cond::Eq, nullptr, false, false},
            {"yxtzj", "yxtzj", Fmt::Str, Cond::Eq, "源系统主键", false, false},
            {"fwqbm", "fwqbm", Fmt::Str, Cond::Eq, "服务区编码", false, false},
            {"fwqmc", "fwqmc", Fmt::Str, Cond::Like, "服务区名称", false, false},
            {"wd", "wd", Fmt::Str, Cond::Eq, "纬度", false, false},
            {"fxmc", "fxmc", Fmt::Str, Cond::Eq, "方向名称", false, false},
            {"fxdm", "fxdm", Fmt::Str, Cond::Eq, "方向代码", false, false},
            {"jd", "jd", Fmt::Str, Cond::Eq, "经度", false, false},
            {"sslxbh", "sslxbh", Fmt::Str, Cond::Eq, "所属路线编号", false, false},
            {"sslxmc", "sslxmc", Fmt::Str, Cond::Eq, "所属路线名称", false, false},
            {"ssldbh", "ssldbh", Fmt::Str, Cond::Eq, "所属路段编号", false, false},
            {"ssldmc", "ssldmc", Fmt::Str, Cond::Eq, "所属路段名称", false, false},
            {"sczhkgs", "sczhkgs", Fmt::Str, Cond::Eq, nullptr, false, false},
            {"sczhszgs", "sczhszgs", Fmt::Str, Cond::Eq, nullptr, false, false},
            {"ssglzxbm", "ssglzxbm", Fmt::Str, Cond::Eq, "所属管理中心编码", false, false},
            {"ssglzxmc", "ssglzxmc", Fmt::Str, Cond::Eq, "所属管理中心名称", false, false},
            {"xzqhmc", "xzqhmc", Fmt::Str, Cond::Eq, "行政区划名称", false, false},
            {"yyrq", "yyrq", Fmt::Str, Cond::Eq, "营业日期", false, false},
            {"cws", "cws", Fmt::Str, Cond::Eq, "车位数", false, false},
            {"sfszlkk", "sfszlkk", Fmt::Str, Cond::Eq, "是否设置了卡口", false, false},
            {"cdzs", "cdzs", Fmt::Str, Cond::Eq, "充电桩数", false, false},
            {"sfcyfw", "sfcyfw", Fmt::Str, Cond::Eq, "是否餐饮服务", false, false},
            {"sftgzsfw", "sftgzsfw", Fmt::Str, Cond::Eq, "是否提供住宿服务", false, false},
            {"sftgqxfw", "sftgqxfw", Fmt::Str, Cond::Eq, "是否提供汽修服务", false, false},
            {"sftgcsfw", "sftgcsfw", Fmt::Str, Cond::Eq, "是否提供超市服务", false, false},
            {"sftgjyfw", "sftgjyfw", Fmt::Str, Cond::Eq, "是否提供加油服务", false, false},
            {"mj", "mj", Fmt::Str, Cond::Eq, nullptr, false, false},
            {"sftgcshfw", "sftgcshfw", Fmt::Str, Cond::Eq, "是否提供厕所服务", false, false},
            {"xzqhdm", "xzqhdm", Fmt::Str, Cond::Eq, "行政区划代码", false, false},
            {"synx", "synx", Fmt::Str, Cond::Eq, "使用年限", false, false},
            {"lyxt", "lyxt", Fmt::Str, Cond::Eq, "来源系统", false, false},
            {"loadTime", "load_time", Fmt::Str, Cond::Eq, "加载日期", false, false},
            {"allColPk", "all_col_pk", Fmt::Str, Cond::Eq, "全字段MD5", false, false},
        };
        s.orderBy = "t.fwqmc";
        s.excelSheetName = "服务区基础信息";
        Perms p;
        registerCrud(r, "/base/fwqjcxx", s, p, "agentPk");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/base/domain/DwdLcztSfsjcxx.java
        // ruoyi-system/src/main/resources/mapper/base/DwdLcztSfsjcxxMapper.xml
        Spec s;
        s.table = "dwd_lczt_sfsjcxx";
        s.alias = "t";
        s.fields = {
            {"agentPk", "agent_pk", Fmt::Str, Cond::Eq, nullptr, false, false},
            {"yxtzj", "yxtzj", Fmt::Str, Cond::Eq, "源系统主键", false, false},
            {"sfsbm", "sfsbm", Fmt::Str, Cond::Eq, "收费所编码", false, false},
            {"sfsmc", "sfsmc", Fmt::Str, Cond::Like, "收费所名称", false, false},
            {"jd", "jd", Fmt::Str, Cond::Eq, "经度", false, false},
            {"wd", "wd", Fmt::Str, Cond::Eq, "纬度", false, false},
            {"sslxbh", "sslxbh", Fmt::Str, Cond::Eq, "所属路线编号", false, false},
            {"sslxmc", "sslxmc", Fmt::Str, Cond::Eq, "所属路线名称", false, false},
            {"ssldbh", "ssldbh", Fmt::Str, Cond::Eq, "所属路段编号", false, false},
            {"ssldmc", "ssldmc", Fmt::Str, Cond::Like, "所属路段名称", false, false},
            {"sczhK", "sczh_k", Fmt::Str, Cond::Eq, nullptr, false, false},
            {"sczhN", "sczh_n", Fmt::Str, Cond::Eq, nullptr, false, false},
            {"ssglzxbm", "ssglzxbm", Fmt::Str, Cond::Eq, "所属管理中心编码", false, false},
            {"ssglzxmc", "ssglzxmc", Fmt::Str, Cond::Eq, "所属管理中心名称", false, false},
            {"lyxt", "lyxt", Fmt::Str, Cond::Eq, "来源系统", false, false},
            {"loadTime", "load_time", Fmt::Str, Cond::Eq, "加载日期", false, false},
            {"allColPk", "all_col_pk", Fmt::Str, Cond::Eq, "全字段MD5", false, false},
        };
        s.orderBy = "t.agent_pk";
        s.excelSheetName = "收费所基础信息";
        Perms p;
        registerCrud(r, "/base/sfsjcxx", s, p, "agentPk");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/base/domain/DwdLcztSfzjcxx.java
        // ruoyi-system/src/main/resources/mapper/base/DwdLcztSfzjcxxMapper.xml
        Spec s;
        s.table = "dwd_lczt_sfzjcxx";
        s.alias = "t";
        s.fields = {
            {"agentPk", "agent_pk", Fmt::Str, Cond::Eq, nullptr, false, false},
            {"yxtzj", "yxtzj", Fmt::Str, Cond::Eq, "源系统主键", false, false},
            {"sfzdm", "sfzdm", Fmt::Str, Cond::Eq, "收费站代码", false, false},
            {"sfzmc", "sfzmc", Fmt::Str, Cond::Like, "收费站名称", false, false},
            {"jd", "jd", Fmt::Str, Cond::Eq, "经度", false, false},
            {"wd", "wd", Fmt::Str, Cond::Eq, "纬度", false, false},
            {"sslxbh", "sslxbh", Fmt::Str, Cond::Eq, "所属路线编号", false, false},
            {"sslxmc", "sslxmc", Fmt::Str, Cond::Eq, "所属路线名称", false, false},
            {"ssldbh", "ssldbh", Fmt::Str, Cond::Eq, "所属路段编号", false, false},
            {"ssldmc", "ssldmc", Fmt::Str, Cond::Eq, "所属路段名称", false, false},
            {"sczhK", "sczh_k", Fmt::Str, Cond::Eq, nullptr, false, false},
            {"sczhN", "sczh_n", Fmt::Str, Cond::Eq, nullptr, false, false},
            {"ssglzxbm", "ssglzxbm", Fmt::Str, Cond::Eq, "所属管理中心编码", false, false},
            {"ssglzxmc", "ssglzxmc", Fmt::Str, Cond::Eq, "所属管理中心名称", false, false},
            {"lyxt", "lyxt", Fmt::Str, Cond::Eq, "来源系统", false, false},
            {"loadTime", "load_time", Fmt::Str, Cond::Eq, "加载日期", false, false},
            {"allColPk", "all_col_pk", Fmt::Str, Cond::Eq, "全字段MD5", false, false},
        };
        s.orderBy = "t.agent_pk";
        s.excelSheetName = "收费站基础信息";
        Perms p;
        registerCrud(r, "/base/sfzjcxx", s, p, "agentPk");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/base/domain/Geometry.java
        // ruoyi-system/src/main/resources/mapper/base/GeometryMapper.xml
        Spec s;
        s.table = "geometry";
        s.alias = "t";
        s.fields = {
            {"id", "id", Fmt::Int, Cond::Eq, nullptr, true, false},
            {"lxbh", "lxbh", Fmt::Str, Cond::Eq, "路线编号", false, false},
            {"lxfx", "lxfx", Fmt::Str, Cond::Eq, "路线方向", false, false},
            {"qdzh", "qdzh", Fmt::Int, Cond::Eq, "起点桩号", false, false},
            {"zdzh", "zdzh", Fmt::Int, Cond::Eq, "终点桩号", false, false},
            {"paths", "paths", Fmt::Str, Cond::Eq, "经纬度", false, false},
        };
        s.orderBy = "lxbh,t.qdzh";
        s.excelSheetName = "车辆信息";
        Perms p;
        p.list = "base:geometry:list";
        registerCrud(r, "/base/geometry", s, p, "ID");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsCxztFwqclls.java
        // ruoyi-system/src/main/resources/mapper/base/OdsCxztFwqcllsMapper.xml
        Spec s;
        s.table = "ods_cxzt_fwqclls";
        s.alias = "t";
        s.fields = {
            {"bigId", "big_id", Fmt::Long, Cond::Eq, nullptr, false, false},
            {"datauuid", "datauuid", Fmt::Str, Cond::Eq, nullptr, false, false},
            {"targetpicurl", "targetpicurl", Fmt::Str, Cond::Eq, "抓拍照片url", false, false},
            {"vehiclebrand", "vehiclebrand", Fmt::Str, Cond::Eq, "车辆品牌", false, false},
            {"platepicurl", "platepicurl", Fmt::Str, Cond::Eq, "车牌照片", false, false},
            {"rollvehiclestype", "rollvehiclestype", Fmt::Str, Cond::Eq, "车类型", false, false},
            {"plateno", "plateno", Fmt::Str, Cond::Eq, "车牌", false, false},
            {"directionname", "directionname", Fmt::Str, Cond::Like, "方向名称", false, false},
            {"platetype", "platetype", Fmt::Str, Cond::Eq, "车牌类型", false, false},
            {"dangmark", "dangmark", Fmt::Str, Cond::Eq, "是否危化品车", false, false},
            {"crosstime", "crosstime", Fmt::DateIso, Cond::Eq, "通过时间", false, false},
            {"axles", "axles", Fmt::Str, Cond::Eq, "坐标", false, false},
            {"devicename", "devicename", Fmt::Str, Cond::Like, "设备名称", false, false},
            {"ipaddress", "ipaddress", Fmt::Str, Cond::Eq, "IP地址", false, false},
            {"servicename", "servicename", Fmt::Str, Cond::Like, "服务区名称", false, false},
            {"vehicletype", "vehicletype", Fmt::Str, Cond::Eq, "车辆类型", false, false},
            {"loadTime", "load_time", Fmt::Str, Cond::Eq, "加载时间", false, false},
            {"gradeLevel", "grade_level", Fmt::Str, Cond::Eq, "分类分级", false, false},
        };
        s.excelSheetName = "OdsCxztFwqclls";
        Perms p;
        p.list = "manager:fwqclls:list";
        registerCrud(r, "/manager/fwqclls", s, p, "bigId");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsLwzxsfsjFeeGantryFusion01.java
        // ruoyi-system/src/main/resources/mapper/base/OdsLwzxsfsjFeeGantryFusion01Mapper.xml
        Spec s;
        s.table = "ods_lwzxsfsj_fee_gantry_fusion_01";
        s.alias = "t";
        s.fields = {
            {"bigId", "big_id", Fmt::Str, Cond::Eq, nullptr, false, false},
            {"actualfeeclass", "actualfeeclass", Fmt::Str, Cond::Eq, "实际计费方式", false, false},
            {"axlecount", "axlecount", Fmt::Long, Cond::Eq, "车轴数", false, false},
            {"createtime", "createtime", Fmt::DateIso, Cond::Eq, "创建时间", false, false},
            {"discountfee", "discountfee", Fmt::Long, Cond::Eq, "优惠金额", false, false},
            {"electricalpercentage", "electricalpercentage", Fmt::Long, Cond::Eq, "单片式OBU/CPC卡电量百分比", false, false},
            {"enaxlecount", "enaxlecount", Fmt::Long, Cond::Eq, "入口车轴数", false, false},
            {"entime", "entime", Fmt::DateYmd, Cond::Eq, "入站时间", false, false},
            {"entolllanehex", "entolllanehex", Fmt::Str, Cond::Eq, "入口车道hex", false, false},
            {"entolllaneid", "entolllaneid", Fmt::Str, Cond::Eq, "入口车道ID", false, false},
            {"entollstationid", "entollstationid", Fmt::Str, Cond::Eq, "入口收费站编码", false, false},
            {"entollstationname", "entollstationname", Fmt::Str, Cond::Like, "入口收费站名称", false, false},
            {"envehicleclass", "envehicleclass", Fmt::Long, Cond::Eq, "入口车种", false, false},
            {"envehicleid", "envehicleid", Fmt::Str, Cond::Eq, "入口车牌号+车牌类型", false, false},
            {"envehicleidcolor", "envehicleidcolor", Fmt::Str, Cond::Eq, "入口车牌号+颜色", false, false},
            {"envehicletype", "envehicletype", Fmt::Long, Cond::Eq, "入口车型", false, false},
            {"enweight", "enweight", Fmt::Long, Cond::Eq, "入口称重", false, false},
            {"entryoperatorid", "entryoperatorid", Fmt::Str, Cond::Eq, "入口操作人员id", false, false},
            {"extime", "extime", Fmt::DateYmd, Cond::Eq, "出站时间", false, false},
            {"extolllaneid", "extolllaneid", Fmt::Str, Cond::Eq, "出口车道号编码", false, false},
            {"extollstationid", "extollstationid", Fmt::Str, Cond::Eq, "出口收费站编码", false, false},
            {"extollstationname", "extollstationname", Fmt::Str, Cond::Like, "出口收费站名称", false, false},
            {"exvehicleclass", "exvehicleclass", Fmt::Long, Cond::Eq, "出口车种", false, false},
            {"exvehicleid", "exvehicleid", Fmt::Str, Cond::Eq, "出口车牌号+车牌类型", false, false},
            {"exvehicletype", "exvehicletype", Fmt::Long, Cond::Eq, "出口车型", false, false},
            {"exweight", "exweight", Fmt::Long, Cond::Eq, "出口称重", false, false},
            {"exitid", "exitid", Fmt::Str, Cond::Eq, "出口id", false, false},
            {"fee", "fee", Fmt::Long, Cond::Eq, "费用", false, false},
            {"feeboardplay", "feeboardplay", Fmt::Str, Cond::Eq, "费显显示信息", false, false},
            {"feemileage", "feemileage", Fmt::Long, Cond::Eq, "收费里程", false, false},
            {"feerate", "feerate", Fmt::Str, Cond::Eq, "交易金额占比", false, false},
            {"fusiondesc", "fusiondesc", Fmt::Str, Cond::Eq, "融合描述", false, false},
            {"fusionflag", "fusionflag", Fmt::Str, Cond::Eq, "融合标识,", false, false},
            {"id", "id", Fmt::Str, Cond::Eq, "id", false, false},
            {"identification", "identification", Fmt::Str, Cond::Eq, "开票标识", false, false},
            {"identifyvehicleid", "identifyvehicleid", Fmt::Str, Cond::Eq, "出口识别车牌号+车牌类型", false, false},
            {"identifyvehicleidcolor", "identifyvehicleidcolor", Fmt::Str, Cond::Eq, "出口识别车牌号+颜色", false, false},
            {"lanetype", "lanetype", Fmt::Str, Cond::Eq, "出口车道类型", false, false},
            {"mediano", "mediano", Fmt::Str, Cond::Eq, "介质编码", false, false},
            {"mediatype", "mediatype", Fmt::Str, Cond::Eq, "通行介质", false, false},
            {"nocardcount", "nocardcount", Fmt::Long, Cond::Eq, "标签无卡累计次数", false, false},
            {"obuid", "obuid", Fmt::Str, Cond::Eq, "OBU序号编码", false, false},
            {"obusign", "obusign", Fmt::Str, Cond::Eq, "OBU 单/双片标识", false, false},
            {"obutotalamount", "obutotalamount", Fmt::Long, Cond::Eq, "0BU 总累计交易金额", false, false},
            {"obutotaldiscountamount", "obutotaldiscountamount", Fmt::Long, Cond::Eq, "OBU累计优惠后通行费金额", false, false},
            {"operid", "operid", Fmt::Str, Cond::Eq, "操作id", false, false},
            {"params", "params", Fmt::Str, Cond::Eq, "参数", false, false},
            {"passid", "passid", Fmt::Str, Cond::Eq, "通行id", false, false},
            {"paycardid", "paycardid", Fmt::Str, Cond::Eq, "支付id", false, false},
            {"payfee", "payfee", Fmt::Long, Cond::Eq, "应收总额", false, false},
            {"paytype", "paytype", Fmt::Str, Cond::Eq, "支付类型", false, false},
            {"provfee", "provfee", Fmt::Long, Cond::Eq, nullptr, false, false},
            {"provtranscount", "provtranscount", Fmt::Long, Cond::Eq, "本省交易成功次数", false, false},
            {"provincecount", "provincecount", Fmt::Long, Cond::Eq, "通行省份个数", false, false},
            {"receivetime", "receivetime", Fmt::DateYmd, Cond::Eq, "接收时间", false, false},
            {"shift", "shift", Fmt::Str, Cond::Eq, "工班号", false, false},
            {"shortfee", "shortfee", Fmt::Long, Cond::Eq, "最短收费金额", false, false},
            {"shortfeemileage", "shortfeemileage", Fmt::Long, Cond::Eq, "最短路径里程数", false, false},
            {"signstatus", "signstatus", Fmt::Str, Cond::Eq, "标记状态", false, false},
            {"spcrateversion", "spcrateversion", Fmt::Str, Cond::Eq, "全网最小费额费率版本号", false, false},
            {"specialtype", "specialtype", Fmt::Str, Cond::Eq, "特殊类型", false, false},
            {"splitprovince", "splitprovince", Fmt::Str, Cond::Eq, "多条省内交易信息", false, false},
            {"tac", "tac", Fmt::Str, Cond::Eq, "TAC码", false, false},
            {"terminalno", "terminalno", Fmt::Str, Cond::Eq, "终端机编号", false, false},
            {"terminaltransno", "terminaltransno", Fmt::Str, Cond::Eq, "PSAM卡脱机交易序列号", false, false},
            {"transfee", "transfee", Fmt::Long, Cond::Eq, "卡面扣费金额", false, false},
            {"transpaytype", "transpaytype", Fmt::Str, Cond::Eq, "交易支付类型", false, false},
            {"transtype", "transtype", Fmt::Str, Cond::Eq, "交易类型", false, false},
            {"vehiclesign", "vehiclesign", Fmt::Str, Cond::Eq, "车辆识别标识", false, false},
            {"vehiclesignid", "vehiclesignid", Fmt::Str, Cond::Eq, "车牌识别流水号", false, false},
            {"vid", "vid", Fmt::Str, Cond::Eq, "车牌号ID", false, false},
            {"loadTime", "load_time", Fmt::DateYmd, Cond::Eq, "加载时间", false, false},
            {"gradeLevel", "grade_level", Fmt::Long, Cond::Eq, "分类分级", false, false},
        };
        s.orderBy = "t.big_id";
        s.excelSheetName = "交易流水";
        Perms p;
        p.list = "base:feeGantry:list";
        registerCrud(r, "/base/feeGantry", s, p, "bigId");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsLwzxsfsjFeeRecords01.java
        // ruoyi-system/src/main/resources/mapper/base/OdsLwzxsfsjFeeRecords01Mapper.xml
        Spec s;
        s.table = "ods_lwzxsfsj_fee_records_01";
        s.alias = "t";
        s.fields = {
            {"bigId", "big_id", Fmt::Str, Cond::Eq, nullptr, false, false},
            {"algorithmidentifier", "algorithmidentifier", Fmt::Str, Cond::Eq, "算法标识", false, false},
            {"antennaid", "antennaid", Fmt::Str, Cond::Eq, nullptr, false, false},
            {"axlecount", "axlecount", Fmt::Long, Cond::Eq, "车轴数", false, false},
            {"balanceafter", "balanceafter", Fmt::Double, Cond::Eq, "交易后余额", false, false},
            {"balancebefore", "balancebefore", Fmt::Double, Cond::Eq, "交易前余额", false, false},
            {"cardfeesumafter", "cardfeesumafter", Fmt::Double, Cond::Eq, "本次交易后卡片累计金额", false, false},
            {"cardfeesumbefore", "cardfeesumbefore", Fmt::Double, Cond::Eq, "本次交易前卡片累计金额", false, false},
            {"computerorder", "computerorder", Fmt::Str, Cond::Eq, "控制器序号", false, false},
            {"consumetime", "consumetime", Fmt::Long, Cond::Eq, "交易耗时", false, false},
            {"cpucardid", "cpucardid", Fmt::Str, Cond::Eq, "CPU卡编号", false, false},
            {"cpucardtype", "cpucardtype", Fmt::Str, Cond::Eq, "CPU卡类型", false, false},
            {"cpuenddate", "cpuenddate", Fmt::Str, Cond::Eq, "CPU截止日期", false, false},
            {"cpuissueid", "cpuissueid", Fmt::Str, Cond::Eq, "CPU卡片发行方标识", false, false},
            {"cpunetid", "cpunetid", Fmt::Str, Cond::Eq, "CPU卡片网络编号", false, false},
            {"cpustartdate", "cpustartdate", Fmt::Str, Cond::Eq, "CPU起始日期", false, false},
            {"cpuvehicleplate", "cpuvehicleplate", Fmt::Str, Cond::Eq, "CPU 内车牌号码", false, false},
            {"cpuvehicletype", "cpuvehicletype", Fmt::Str, Cond::Eq, "CPU内车型", false, false},
            {"cpuversion", "cpuversion", Fmt::Str, Cond::Eq, "CPU用户卡版本号", false, false},
            {"dealstatus", "dealstatus", Fmt::Str, Cond::Eq, "处理状态", false, false},
            {"discountfee", "discountfee", Fmt::Double, Cond::Eq, "优惠金额", false, false},
            {"discountfeegroup", "discountfeegroup", Fmt::Str, Cond::Eq, "优惠金额组合", false, false},
            {"enlanetype", "enlanetype", Fmt::Str, Cond::Eq, "入口车道类型", false, false},
            {"entime", "entime", Fmt::DateYmdHms, Cond::Eq, "进站时间", false, false},
            {"entolllaneid", "entolllaneid", Fmt::Str, Cond::Eq, "进站收费站车道号", false, false},
            {"entollstationhex", "entollstationhex", Fmt::Str, Cond::Eq, "进站收费站hex编码", false, false},
            {"fee", "fee", Fmt::Double, Cond::Eq, "费用", false, false},
            {"feecalcresult", "feecalcresult", Fmt::Str, Cond::Eq, "计费模块响应计费结果", false, false},
            {"feecalcspecial", "feecalcspecial", Fmt::Str, Cond::Eq, "计费接口特情值", false, false},
            {"feecalcspecials", "feecalcspecials", Fmt::Str, Cond::Eq, "计费特情值组合", false, false},
            {"feegroup", "feegroup", Fmt::Str, Cond::Eq, "交易金额组合", false, false},
            {"feeinfo1", "feeinfo1", Fmt::Str, Cond::Eq, "计费信息1", false, false},
            {"feeinfo2", "feeinfo2", Fmt::Str, Cond::Eq, "计费信息2", false, false},
            {"feeinfo3", "feeinfo3", Fmt::Str, Cond::Eq, "计费信息3", false, false},
            {"feemileage", "feemileage", Fmt::Double, Cond::Eq, "收费里程", false, false},
            {"feeprovbeginhex", "feeprovbeginhex", Fmt::Str, Cond::Eq, "本省计费起点", false, false},
            {"feespare1", "feespare1", Fmt::Str, Cond::Eq, "计费协议保留字段1", false, false},
            {"feespare2", "feespare2", Fmt::Str, Cond::Eq, "计费协议保留字段2", false, false},
            {"feevehicletype", "feevehicletype", Fmt::Str, Cond::Eq, "计费车型", false, false},
            {"gantryhex", "gantryhex", Fmt::Str, Cond::Eq, "门架Hex值", false, false},
            {"gantryhexopposite", "gantryhexopposite", Fmt::Str, Cond::Eq, "对向门架Hex值", false, false},
            {"gantryid", "gantryid", Fmt::Str, Cond::Eq, "门架编码", false, false},
            {"gantryordernum", "gantryordernum", Fmt::Long, Cond::Eq, "门架顺序号", false, false},
            {"gantrytype", "gantrytype", Fmt::Str, Cond::Eq, "门架类型", false, false},
            {"holidaystate", "holidaystate", Fmt::Str, Cond::Eq, "节假日状态", false, false},
            {"hourbatchno", "hourbatchno", Fmt::Str, Cond::Eq, "小时批次号", false, false},
            {"keyversion", "keyversion", Fmt::Str, Cond::Eq, "消费密钥版本号", false, false},
            {"lastgantryhex", "lastgantryhex", Fmt::Str, Cond::Eq, "上一个门架的hex编号", false, false},
            {"lastgantrytime", "lastgantrytime", Fmt::DateYmdHms, Cond::Eq, "通过上一个门架的时间", false, false},
            {"matchstatus", "matchstatus", Fmt::Str, Cond::Eq, "匹配状态", false, false},
            {"mediatype", "mediatype", Fmt::Str, Cond::Eq, "通行介质类型", false, false},
            {"nocardtimesafter", "nocardtimesafter", Fmt::Long, Cond::Eq, "本次交易后累计无卡次数", false, false},
            {"nocardtimesbefore", "nocardtimesbefore", Fmt::Long, Cond::Eq, "本次交易前累计无卡次数", false, false},
            {"obuelectrical", "obuelectrical", Fmt::Long, Cond::Eq, "OBU/CPC卡电量百分比", false, false},
            {"obuenddate", "obuenddate", Fmt::Str, Cond::Eq, "OBU/CPC截止日期", false, false},
            {"obufeesumafter", "obufeesumafter", Fmt::Double, Cond::Eq, "本次交易后标签累计实收金额", false, false},
            {"obufeesumbefore", "obufeesumbefore", Fmt::Double, Cond::Eq, "本次交易前标签累计实收金额", false, false},
            {"obuinfotyperead", "obuinfotyperead", Fmt::Str, Cond::Eq, "读取标签入口信息类型", false, false},
            {"obuinfotypewrite", "obuinfotypewrite", Fmt::Str, Cond::Eq, "本次写入标签入口信息类型", false, false},
            {"obuissueid", "obuissueid", Fmt::Str, Cond::Eq, "OBU/CPC发行方标识", false, false},
            {"obulastgantryhex", "obulastgantryhex", Fmt::Str, Cond::Eq, "OBU中上一个门架HEX", false, false},
            {"obulastgantrytime", "obulastgantrytime", Fmt::DateYmdHms, Cond::Eq, "OBU中通过上一个门架时间", false, false},
            {"obumac", "obumac", Fmt::Str, Cond::Eq, "OBU /CPC物理地址", false, false},
            {"obumileageafter", "obumileageafter", Fmt::Double, Cond::Eq, "本次交易后标签累计里程", false, false},
            {"obumileagebefore", "obumileagebefore", Fmt::Double, Cond::Eq, "本次交易前标签累计里程", false, false},
            {"obupassstate", "obupassstate", Fmt::Str, Cond::Eq, "标签入口状态", false, false},
            {"obupayfeesumafter", "obupayfeesumafter", Fmt::Double, Cond::Eq, "本次交易后标签累计应收金额", false, false},
            {"obupayfeesumbefore", "obupayfeesumbefore", Fmt::Double, Cond::Eq, "本次交易前标签累计应收金额", false, false},
            {"obuprovfeesumafter", "obuprovfeesumafter", Fmt::Double, Cond::Eq, "本次交易后标签累计金额", false, false},
            {"obuprovfeesumbefore", "obuprovfeesumbefore", Fmt::Double, Cond::Eq, "本次交易前标签累计金额 ", false, false},
            {"obuprovpayfeesumafter", "obuprovpayfeesumafter", Fmt::Double, Cond::Eq, "本次交易后标签累计应收金额", false, false},
            {"obuprovpayfeesumbefore", "obuprovpayfeesumbefore", Fmt::Double, Cond::Eq, "本次交易前标签累计应收金额", false, false},
            {"obuprovtradesuccnumafter", "obuprovtradesuccnumafter", Fmt::Long, Cond::Eq, "省内本次交易后标签累计写入成功数量", false, false},
            {"obuprovtradesuccnumbefore", "obuprovtradesuccnumbefore", Fmt::Long, Cond::Eq, "省内本次交易前标签累计写入成功数量", false, false},
            {"obusign", "obusign", Fmt::Str, Cond::Eq, "OBU 单/双片标识", false, false},
            {"obusn", "obusn", Fmt::Str, Cond::Eq, "OBU/CPC序号编码", false, false},
            {"obustartdate", "obustartdate", Fmt::Str, Cond::Eq, "OBU/CPC起始日期", false, false},
            {"obustate", "obustate", Fmt::Str, Cond::Eq, "OBU/CPC状态", false, false},
            {"obutotaltradesuccnumafter", "obutotaltradesuccnumafter", Fmt::Long, Cond::Eq, "本次交易后标签累计写入成功总量", false, false},
            {"obutotaltradesuccnumbefore", "obutotaltradesuccnumbefore", Fmt::Long, Cond::Eq, "本次交易前标签累计写入成功总量", false, false},
            {"obutraderesult", "obutraderesult", Fmt::Str, Cond::Eq, "标签写入结果", false, false},
            {"obuvehicleplate", "obuvehicleplate", Fmt::Str, Cond::Eq, "obu车牌", false, false},
            {"obuvehicletype", "obuvehicletype", Fmt::Str, Cond::Eq, "obu车牌类型", false, false},
            {"obuversion", "obuversion", Fmt::Str, Cond::Eq, "OBU/CPC版本号", false, false},
            {"params", "params", Fmt::Str, Cond::Eq, "参数", false, false},
            {"passid", "passid", Fmt::Str, Cond::Eq, "通行id", false, false},
            {"passstate", "passstate", Fmt::Str, Cond::Eq, "通行状态", false, false},
            {"pathfitflag", "pathfitflag", Fmt::Str, Cond::Eq, "本次计费拟合结果标识", false, false},
            {"payfee", "payfee", Fmt::Double, Cond::Eq, "应收金额", false, false},
            {"payfeegroup", "payfeegroup", Fmt::Str, Cond::Eq, "应收金额组合", false, false},
            {"pcrsuversion", "pcrsuversion", Fmt::Str, Cond::Eq, "PC-RSU接口协议版本号", false, false},
            {"provminfee", "provminfee", Fmt::Double, Cond::Eq, "本省累计通行金额参考", false, false},
            {"provincenumafter", "provincenumafter", Fmt::Long, Cond::Eq, "本次交易后累计省份数量", false, false},
            {"provincenumbefore", "provincenumbefore", Fmt::Long, Cond::Eq, "本次交易前累计省份数量", false, false},
            {"ratecompute", "ratecompute", Fmt::Str, Cond::Eq, "计费模块计费模式", false, false},
            {"ratefitcount", "ratefitcount", Fmt::Long, Cond::Eq, "计费模块拟合点总数", false, false},
            {"rateversion", "rateversion", Fmt::Str, Cond::Eq, "计费模块和计费参数版本号", false, false},
            {"readciphertextverify", "readciphertextverify", Fmt::Str, Cond::Eq, "本次交易读取的EF04加密摘要验证结果", false, false},
            {"receivetime", "receivetime", Fmt::DateYmdHms, Cond::Eq, "接收时间", false, false},
            {"servicetype", "servicetype", Fmt::Str, Cond::Eq, "交易的服务类型", false, false},
            {"stationdbtime", "stationdbtime", Fmt::DateYmdHms, Cond::Eq, "门架后台入库时间", false, false},
            {"stationdealtime", "stationdealtime", Fmt::DateYmdHms, Cond::Eq, "门架后台处理时间", false, false},
            {"stationmatchtime", "stationmatchtime", Fmt::DateYmdHms, Cond::Eq, "门架后台匹配时间", false, false},
            {"stationvalidtime", "stationvalidtime", Fmt::DateYmdHms, Cond::Eq, "门架后台去重时间", false, false},
            {"tac", "tac", Fmt::Str, Cond::Eq, "TAC码", false, false},
            {"terminalno", "terminalno", Fmt::Str, Cond::Eq, "终端机编号", false, false},
            {"terminaltransno", "terminaltransno", Fmt::Str, Cond::Eq, "PSAM卡脱机交易序列号", false, false},
            {"tollintervalid", "tollintervalid", Fmt::Str, Cond::Eq, "收费单元编号组合", false, false},
            {"tollintervalsign", "tollintervalsign", Fmt::Str, Cond::Eq, "收费单元处理标识", false, false},
            {"totalweight", "totalweight", Fmt::Double, Cond::Eq, "车货总重", false, false},
            {"tradeid", "tradeid", Fmt::Str, Cond::Eq, "计费交易编号", false, false},
            {"tradereadciphertext", "tradereadciphertext", Fmt::Str, Cond::Eq, "本次交易读取的EF04加密摘要", false, false},
            {"traderesult", "traderesult", Fmt::Str, Cond::Eq, "卡片复合交易结果", false, false},
            {"tradetype", "tradetype", Fmt::Str, Cond::Eq, "交易类型", false, false},
            {"tradewriteciphertext", "tradewriteciphertext", Fmt::Str, Cond::Eq, "本次交易生成的EF04加密摘要", false, false},
            {"transfee", "transfee", Fmt::Double, Cond::Eq, "卡面扣费金额", false, false},
            {"transno", "transno", Fmt::Str, Cond::Eq, "IC卡交易序号", false, false},
            {"transtime", "transtime", Fmt::DateYmdHms, Cond::Eq, "计费交易时间", false, false},
            {"transtype", "transtype", Fmt::Str, Cond::Eq, "交易类型标识", false, false},
            {"validstatus", "validstatus", Fmt::Str, Cond::Eq, "去重状态", false, false},
            {"vehicleclass", "vehicleclass", Fmt::Str, Cond::Eq, "车种", false, false},
            {"vehiclehight", "vehiclehight", Fmt::Double, Cond::Eq, "车高", false, false},
            {"vehiclelength", "vehiclelength", Fmt::Double, Cond::Eq, "车长", false, false},
            {"vehicleplate", "vehicleplate", Fmt::Str, Cond::Eq, "车牌号+类型", false, false},
            {"vehicleseat", "vehicleseat", Fmt::Str, Cond::Eq, "车辆座位数/载重", false, false},
            {"vehiclesign", "vehiclesign", Fmt::Str, Cond::Eq, "车辆状态标识", false, false},
            {"vehicletype", "vehicletype", Fmt::Str, Cond::Eq, "车辆类型", false, false},
            {"vehicleusertype", "vehicleusertype", Fmt::Str, Cond::Eq, "车辆用户类型", false, false},
            {"vehiclewidth", "vehiclewidth", Fmt::Double, Cond::Eq, "车宽", false, false},
            {"verifycode", "verifycode", Fmt::Str, Cond::Eq, "校验码", false, false},
            {"loadTime", "load_time", Fmt::DateYmdHms, Cond::Eq, "加载时间", false, false},
            {"gradeLevel", "grade_level", Fmt::Long, Cond::Eq, "分类分级", false, false},
        };
        s.orderBy = "t.big_id";
        s.excelSheetName = "基础-收费流水";
        Perms p;
        p.list = "base:feerecords:list";
        p.exportList = "base:feerecords:list";
        registerCrud(r, "/base/feerecords", s, p, "bigId");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsLwzxsfsjFeeStationEnter01.java
        // ruoyi-system/src/main/resources/mapper/base/OdsLwzxsfsjFeeStationEnter01Mapper.xml
        Spec s;
        s.table = "ods_lwzxsfsj_fee_station_enter_01";
        s.alias = "t";
        s.fields = {
            {"bigId", "big_id", Fmt::Long, Cond::Eq, nullptr, true, false},
            {"cardid", "cardid", Fmt::Str, Cond::Eq, "CPC卡或ETC卡的编号", false, false},
            {"electricalpercentage", "electricalpercentage", Fmt::Long, Cond::Eq, "单片式OBU/CPC卡电量百分比", false, false},
            {"enaxlecount", "enaxlecount", Fmt::Long, Cond::Eq, "入站车轴数", false, false},
            {"entime", "entime", Fmt::DateYmd, Cond::Eq, "入站时间", false, false},
            {"entolllanehex", "entolllanehex", Fmt::Str, Cond::Eq, "入口车道hex", false, false},
            {"entolllaneid", "entolllaneid", Fmt::Str, Cond::Eq, "入口车道id", false, false},
            {"entollstationid", "entollstationid", Fmt::Str, Cond::Eq, "入口收费站编码", false, false},
            {"enweight", "enweight", Fmt::Double, Cond::Eq, "入口称重", false, false},
            {"identifyvehicleid", "identifyvehicleid", Fmt::Str, Cond::Eq, "车牌号+车牌类型", false, false},
            {"lanetype", "lanetype", Fmt::Str, Cond::Eq, "车道类型", false, false},
            {"mediatype", "mediatype", Fmt::Str, Cond::Eq, "介质类型", false, false},
            {"operid", "operid", Fmt::Str, Cond::Eq, "操作id", false, false},
            {"operationmedia", "operationmedia", Fmt::Str, Cond::Eq, "作业媒介", false, false},
            {"params", "params", Fmt::Str, Cond::Eq, "参数", false, false},
            {"passid", "passid", Fmt::Str, Cond::Eq, "通行id", false, false},
            {"receivetime", "receivetime", Fmt::DateYmd, Cond::Eq, "接收时间", false, false},
            {"shift", "shift", Fmt::Str, Cond::Eq, "工班号", false, false},
            {"signstatus", "signstatus", Fmt::Str, Cond::Eq, "标记状态", false, false},
            {"specialtype", "specialtype", Fmt::Str, Cond::Eq, "特殊类型", false, false},
            {"tac", "tac", Fmt::Str, Cond::Eq, "TAC码", false, false},
            {"terminalno", "terminalno", Fmt::Str, Cond::Eq, "终端机编号", false, false},
            {"terminaltransno", "terminaltransno", Fmt::Str, Cond::Eq, "PSAM卡脱机交易序列号", false, false},
            {"transfee", "transfee", Fmt::Double, Cond::Eq, "交易金额", false, false},
            {"transtype", "transtype", Fmt::Str, Cond::Eq, "交易类型", false, false},
            {"vcount", "vcount", Fmt::Long, Cond::Eq, "总数", false, false},
            {"vehicleclass", "vehicleclass", Fmt::Str, Cond::Eq, "车种", false, false},
            {"vehicleid", "vehicleid", Fmt::Str, Cond::Eq, "车牌号+车牌类型", false, false},
            {"vehiclesign", "vehiclesign", Fmt::Str, Cond::Eq, "车辆识别标识", false, false},
            {"vehiclesignid", "vehiclesignid", Fmt::Str, Cond::Eq, "车牌识别流水号", false, false},
            {"vehicletype", "vehicletype", Fmt::Str, Cond::Eq, "车辆类型", false, false},
            {"loadTime", "load_time", Fmt::DateYmd, Cond::Eq, "加载时间", false, false},
            {"gradeLevel", "grade_level", Fmt::Str, Cond::Eq, "分类分级", false, false},
            {"cid", "cid", Fmt::Str, Cond::None, "cid", false, false},
        };
        s.orderBy = "t.big_id";
        s.excelSheetName = "OdsLwzxsfsjFeeStationEnter01";
        Perms p;
        registerCrud(r, "/base/feeStationEnter", s, p, "bigId");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsLwzxsfsjFeeStationExit01.java
        // ruoyi-system/src/main/resources/mapper/base/OdsLwzxsfsjFeeStationExit01Mapper.xml
        Spec s;
        s.table = "ods_lwzxsfsj_fee_station_exit_01";
        s.alias = "t";
        s.fields = {
            {"bigId", "big_id", Fmt::Str, Cond::Eq, nullptr, false, false},
            {"actualfeeclass", "actualfeeclass", Fmt::Str, Cond::Eq, "实际计费方式", false, false},
            {"axlecount", "axlecount", Fmt::Int, Cond::Eq, "车轴数", false, false},
            {"discountfee", "discountfee", Fmt::Long, Cond::Eq, "优惠金额", false, false},
            {"electricalpercentage", "electricalpercentage", Fmt::Int, Cond::Eq, "单片式OBU/CPC卡电量百分比", false, false},
            {"enaxlecount", "enaxlecount", Fmt::Int, Cond::Eq, "入站车轴数", false, false},
            {"entime", "entime", Fmt::DateYmd, Cond::Eq, "进站时间", false, false},
            {"entolllanehex", "entolllanehex", Fmt::Str, Cond::Eq, "入口车道hex", false, false},
            {"entolllaneid", "entolllaneid", Fmt::Str, Cond::Eq, "进站收费站车道号", false, false},
            {"entollstationid", "entollstationid", Fmt::Str, Cond::Eq, "入口收费站编码", false, false},
            {"entollstationname", "entollstationname", Fmt::Str, Cond::Like, "入口收费站名称", false, false},
            {"envehicleclass", "envehicleclass", Fmt::Int, Cond::Eq, "入口车种", false, false},
            {"envehicleid", "envehicleid", Fmt::Str, Cond::Eq, "入口车牌号+车牌类型", false, false},
            {"envehicletype", "envehicletype", Fmt::Int, Cond::Eq, "入口车型", false, false},
            {"enweight", "enweight", Fmt::Long, Cond::Eq, "入口称重", false, false},
            {"entryoperatorid", "entryoperatorid", Fmt::Str, Cond::Eq, "入口操作人员id", false, false},
            {"extime", "extime", Fmt::DateYmd, Cond::Eq, "出站时间", false, false},
            {"extolllaneid", "extolllaneid", Fmt::Str, Cond::Eq, "出口车道号编码", false, false},
            {"extollstationid", "extollstationid", Fmt::Str, Cond::Eq, "出口收费站编码", false, false},
            {"extollstationname", "extollstationname", Fmt::Str, Cond::Like, "出口收费站名称", false, false},
            {"exvehicleclass", "exvehicleclass", Fmt::Int, Cond::Eq, "出口车种", false, false},
            {"exvehicleid", "exvehicleid", Fmt::Str, Cond::Eq, "出口车牌号+车牌类型", false, false},
            {"exvehicletype", "exvehicletype", Fmt::Int, Cond::Eq, "出口车型", false, false},
            {"fee", "fee", Fmt::Long, Cond::Eq, "费用", false, false},
            {"exweight", "exweight", Fmt::Long, Cond::Eq, "出口称重", false, false},
            {"feeboardplay", "feeboardplay", Fmt::Str, Cond::Eq, "费显显示信息", false, false},
            {"feemileage", "feemileage", Fmt::Long, Cond::Eq, "收费里程", false, false},
            {"identification", "identification", Fmt::Str, Cond::Eq, "开票标识", false, false},
            {"feerate", "feerate", Fmt::Double, Cond::Eq, "交易金额占比", false, false},
            {"identifyvehicleid", "identifyvehicleid", Fmt::Str, Cond::Eq, "车牌号+车牌类型", false, false},
            {"lanetype", "lanetype", Fmt::Str, Cond::Eq, "车道类型", false, false},
            {"mediano", "mediano", Fmt::Str, Cond::Eq, "介质编码", false, false},
            {"mediatype", "mediatype", Fmt::Str, Cond::Eq, "通行介质类型", false, false},
            {"nocardcount", "nocardcount", Fmt::Int, Cond::Eq, "标签无卡累计次数", false, false},
            {"obuid", "obuid", Fmt::Str, Cond::Eq, "OBU序号编码", false, false},
            {"obusign", "obusign", Fmt::Str, Cond::Eq, "OBU 单/双片标识", false, false},
            {"obutotalamount", "obutotalamount", Fmt::Long, Cond::Eq, "0BU 总累计交易金额", false, false},
            {"obutotaldiscountamount", "obutotaldiscountamount", Fmt::Long, Cond::Eq, "OBU累计优惠后通行费金额", false, false},
            {"params", "params", Fmt::Str, Cond::Eq, "参数", false, false},
            {"operid", "operid", Fmt::Str, Cond::Eq, "操作id", false, false},
            {"passid", "passid", Fmt::Str, Cond::Eq, "通行id", false, false},
            {"paycardid", "paycardid", Fmt::Str, Cond::Eq, "支付id", false, false},
            {"payfee", "payfee", Fmt::Long, Cond::Eq, "应收金额", false, false},
            {"paytype", "paytype", Fmt::Str, Cond::Eq, "支付类型", false, false},
            {"provfee", "provfee", Fmt::Long, Cond::Eq, nullptr, false, false},
            {"provtranscount", "provtranscount", Fmt::Int, Cond::Eq, "本省交易成功次数", false, false},
            {"provincecount", "provincecount", Fmt::Int, Cond::Eq, "通行省份个数", false, false},
            {"shift", "shift", Fmt::Str, Cond::Eq, "工班号", false, false},
            {"receivetime", "receivetime", Fmt::DateYmd, Cond::Eq, "接收时间", false, false},
            {"shortfee", "shortfee", Fmt::Long, Cond::Eq, "最短收费金额", false, false},
            {"shortfeemileage", "shortfeemileage", Fmt::Long, Cond::Eq, "最短路径里程数", false, false},
            {"signstatus", "signstatus", Fmt::Str, Cond::Eq, "标记状态", false, false},
            {"spcrateversion", "spcrateversion", Fmt::Str, Cond::Eq, "全网最小费额费率版本号", false, false},
            {"tac", "tac", Fmt::Str, Cond::Eq, "TAC码", false, false},
            {"specialtype", "specialtype", Fmt::Str, Cond::Eq, "特殊类型", false, false},
            {"splitprovince", "splitprovince", Fmt::Str, Cond::Eq, "多条省内交易信息", false, false},
            {"terminalno", "terminalno", Fmt::Str, Cond::Eq, "终端机编号", false, false},
            {"terminaltransno", "terminaltransno", Fmt::Str, Cond::Eq, "PSAM卡脱机交易序列号", false, false},
            {"transfee", "transfee", Fmt::Long, Cond::Eq, "卡面扣费金额", false, false},
            {"transpaytype", "transpaytype", Fmt::Str, Cond::Eq, "交易支付类型", false, false},
            {"transtype", "transtype", Fmt::Str, Cond::Eq, "交易类型标识", false, false},
            {"loadTime", "load_time", Fmt::DateYmd, Cond::Eq, "加载时间", false, false},
            {"vehiclesignid", "vehiclesignid", Fmt::Str, Cond::Eq, "车牌识别流水号", false, false},
            {"vehiclesign", "vehiclesign", Fmt::Str, Cond::Eq, "车辆状态标识", false, false},
            {"gradeLevel", "grade_level", Fmt::Str, Cond::Eq, "分类分级", false, false},
        };
        s.orderBy = "t.big_id";
        s.excelSheetName = "收费站出口流水";
        Perms p;
        p.list = "base:feestationexit:list";
        registerCrud(r, "/base/feestationexit", s, p, "bigId");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsRtSzdnSnapshotFlowAddcode.java
        // ruoyi-system/src/main/resources/mapper/base/OdsRtSzdnSnapshotFlowAddcodeMapper.xml
        Spec s;
        s.table = "ods_rt_szdn_snapshot_flow_addcode";
        s.alias = "t";
        s.fields = {
            {"bigId", "big_id", Fmt::Str, Cond::Eq, nullptr, false, false},
            {"datasource", "datasource", Fmt::Str, Cond::Eq, "数据类型", false, false},
            {"cameratype", "cameratype", Fmt::Str, Cond::Eq, "设备类型", false, false},
            {"deviceid", "deviceid", Fmt::Str, Cond::Eq, "设备编号", false, false},
            {"gantrycode", "gantrycode", Fmt::Str, Cond::Eq, "门架编号", false, false},
            {"gantryname", "gantryname", Fmt::Str, Cond::Like, "门架名称", false, false},
            {"roadcode", "roadcode", Fmt::Str, Cond::Eq, "所属路线编码", false, false},
            {"roadname", "roadname", Fmt::Str, Cond::Like, "所属路线名称", false, false},
            {"sectioncode", "sectioncode", Fmt::Str, Cond::Eq, "所属路段编码", false, false},
            {"sectionname", "sectionname", Fmt::Str, Cond::Like, "所属路段名称", false, false},
            {"tollcode", "tollcode", Fmt::Str, Cond::Eq, "所属收费站编码", false, false},
            {"tollname", "tollname", Fmt::Str, Cond::Like, "所属收费站名称", false, false},
            {"orgcode", "orgcode", Fmt::Str, Cond::Eq, "所属管理中心机构编码", false, false},
            {"orgname", "orgname", Fmt::Str, Cond::Like, "所属管理中心机构名称", false, false},
            {"direction", "direction", Fmt::Int, Cond::Eq, "方向", false, false},
            {"hexcode", "hexcode", Fmt::Str, Cond::Eq, "门架二进制编号", false, false},
            {"pileno", "pileno", Fmt::Str, Cond::Eq, "桩号", false, false},
            {"lon", "lon", Fmt::Double, Cond::Eq, "经度", false, false},
            {"lat", "lat", Fmt::Double, Cond::Eq, "纬度", false, false},
            {"deviceip", "deviceip", Fmt::Str, Cond::Eq, "设备IP", false, false},
            {"siteid", "siteid", Fmt::Long, Cond::Eq, "站点ID", false, false},
            {"laneid", "laneid", Fmt::Int, Cond::Eq, "车道编号", false, false},
            {"snapshottimeunix", "snapshottimeunix", Fmt::Long, Cond::Eq, "抓拍时间Unix格式", false, false},
            {"snapshottime", "snapshottime", Fmt::DateIso, Cond::Eq, nullptr, false, false},
            {"receivedtimeunix", "receivedtimeunix", Fmt::Long, Cond::Eq, "接收时间Unix格式", false, false},
            {"receivedtime", "receivedtime", Fmt::DateYmd, Cond::Eq, "接收时间", false, false},
            {"platenumber", "platenumber", Fmt::Str, Cond::Eq, "车牌号", false, false},
            {"platecolor", "platecolor", Fmt::Str, Cond::Eq, "车牌颜色", false, false},
            {"platecolorcode", "platecolorcode", Fmt::Int, Cond::Eq, "车牌颜色编码", false, false},
            {"platetype", "platetype", Fmt::Str, Cond::Eq, "车牌类型", false, false},
            {"platetypecode", "platetypecode", Fmt::Int, Cond::Eq, "车牌类型编码", false, false},
            {"plateconfidence", "plateconfidence", Fmt::Int, Cond::Eq, "车牌置信度", false, false},
            {"carbrand", "carbrand", Fmt::Str, Cond::Eq, "车辆品牌", false, false},
            {"carcolor", "carcolor", Fmt::Str, Cond::Eq, "车辆颜色", false, false},
            {"carcolorcode", "carcolorcode", Fmt::Int, Cond::Eq, "车辆颜色编码", false, false},
            {"cartype", "cartype", Fmt::Str, Cond::Eq, "车辆类型", false, false},
            {"cartypecode", "cartypecode", Fmt::Int, Cond::Eq, "车辆类型编码", false, false},
            {"cardirection", "cardirection", Fmt::Str, Cond::Eq, "行驶方向", false, false},
            {"snappicturepath", "snappicturepath", Fmt::Str, Cond::Eq, "图片路径", false, false},
            {"loadtime", "loadtime", Fmt::DateYmd, Cond::Eq, "加载时间", false, false},
            {"gradelevel", "gradelevel", Fmt::Int, Cond::Eq, "分类分级", false, false},
            {"datauuid", "datauuid", Fmt::Str, Cond::Eq, "uuid", false, false},
            {"reserve3", "reserve3", Fmt::Str, Cond::Eq, "备用字段", false, false},
        };
        s.orderBy = "t.big_id";
        s.excelSheetName = "门架抓拍流水";
        Perms p;
        p.list = "base:snapshotflow:list";
        p.exportList = "base:snapshotflow:list";
        registerCrud(r, "/base/snapshotflow", s, p, "bigId");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsRtSzdnSnapshotFlowProvcaptureAddcode.java
        // ruoyi-system/src/main/resources/mapper/base/OdsRtSzdnSnapshotFlowProvcaptureAddcodeMapper.xml
        Spec s;
        s.table = "ods_rt_szdn_snapshot_flow_provcapture_addcode";
        s.alias = "t";
        s.fields = {
            {"bigId", "big_id", Fmt::Long, Cond::Eq, nullptr, true, false},
            {"deviceip", "deviceip", Fmt::Str, Cond::Eq, nullptr, false, false},
            {"tailcapturetimeunix", "tailcapturetimeunix", Fmt::Long, Cond::Eq, nullptr, false, false},
            {"tailcapturetime", "tailcapturetime", Fmt::DateIso, Cond::Eq, nullptr, false, false},
            {"extendattribute", "extendattribute", Fmt::Str, Cond::Eq, nullptr, false, false},
            {"smallsideimagewidth", "smallsideimagewidth", Fmt::Int, Cond::Eq, nullptr, false, false},
            {"axletype", "axletype", Fmt::Str, Cond::Eq, nullptr, false, false},
            {"smallsideimageheight", "smallsideimageheight", Fmt::Int, Cond::Eq, "小侧图高度", false, false},
            {"platecolorcode", "platecolorcode", Fmt::Int, Cond::Eq, "车牌颜色编码", false, false},
            {"platecolor", "platecolor", Fmt::Str, Cond::Eq, "车牌颜色", false, false},
            {"cover", "cover", Fmt::Str, Cond::Eq, "遮挡信息", false, false},
            {"averageauthoritative", "averageauthoritative", Fmt::Int, Cond::Eq, "平均可信度", false, false},
            {"headlanecode", "headlanecode", Fmt::Int, Cond::Eq, "车头车道号", false, false},
            {"specialvehicle", "specialvehicle", Fmt::Int, Cond::Eq, "特殊车辆标识", false, false},
            {"carlength", "carlength", Fmt::Int, Cond::Eq, "车长", false, false},
            {"resulttype", "resulttype", Fmt::Str, Cond::Eq, "结果类型", false, false},
            {"carhight", "carhight", Fmt::Int, Cond::Eq, "车高", false, false},
            {"carmodelscode", "carmodelscode", Fmt::Int, Cond::Eq, "车型编码", false, false},
            {"carmodels", "carmodels", Fmt::Str, Cond::Eq, "车型", false, false},
            {"laneposition", "laneposition", Fmt::Str, Cond::Eq, "车道位置", false, false},
            {"firstauthoritative", "firstauthoritative", Fmt::Int, Cond::Eq, "首字可信度", false, false},
            {"tailplateimageheight", "tailplateimageheight", Fmt::Int, Cond::Eq, "车尾车牌图高度", false, false},
            {"axlecount", "axlecount", Fmt::Int, Cond::Eq, "车轴数", false, false},
            {"plateimagewidth", "plateimagewidth", Fmt::Int, Cond::Eq, "车牌图宽度", false, false},
            {"specialclass", "specialclass", Fmt::Str, Cond::Eq, "特殊类别", false, false},
            {"tailplatenumber", "tailplatenumber", Fmt::Str, Cond::Eq, "车尾车牌号", false, false},
            {"tailimage", "tailimage", Fmt::Str, Cond::Eq, "车尾图路径", false, false},
            {"sidecapturetimeunix", "sidecapturetimeunix", Fmt::Long, Cond::Eq, nullptr, false, false},
            {"sidecapturetime", "sidecapturetime", Fmt::DateIso, Cond::Eq, nullptr, false, false},
            {"sidelanecode", "sidelanecode", Fmt::Int, Cond::Eq, "车身车道号", false, false},
            {"wheelbase", "wheelbase", Fmt::Int, Cond::Eq, "轴距", false, false},
            {"attached", "attached", Fmt::Str, Cond::Eq, "附加信息", false, false},
            {"wheelcount", "wheelcount", Fmt::Int, Cond::Eq, "车轮数量", false, false},
            {"guid", "guid", Fmt::Str, Cond::Eq, "全局唯一标识符", false, false},
            {"sideimagewidth", "sideimagewidth", Fmt::Int, Cond::Eq, "车身图宽度", false, false},
            {"plateimageheight", "plateimageheight", Fmt::Int, Cond::Eq, "车牌图高度", false, false},
            {"datasource", "datasource", Fmt::Str, Cond::Eq, "数据来源", false, false},
            {"carclass", "carclass", Fmt::Str, Cond::Eq, "车辆分类", false, false},
            {"gantryid", "gantryid", Fmt::Str, Cond::Eq, "门架编号", false, false},
            {"smallsideimage", "smallsideimage", Fmt::Str, Cond::Eq, "小侧图路径", false, false},
            {"headimageheight", "headimageheight", Fmt::Int, Cond::Eq, "车头图高度", false, false},
            {"sidescenetypecode", "sidescenetypecode", Fmt::Int, Cond::Eq, "车侧拍摄场景编码", false, false},
            {"sidescenetype", "sidescenetype", Fmt::Str, Cond::Eq, "车侧拍摄场景", false, false},
            {"tailimagewidth", "tailimagewidth", Fmt::Int, Cond::Eq, "车尾图宽度", false, false},
            {"envstate", "envstate", Fmt::Str, Cond::Eq, "环境状态", false, false},
            {"headscenetypecode", "headscenetypecode", Fmt::Int, Cond::Eq, "车头拍摄场景编码", false, false},
            {"headscenetype", "headscenetype", Fmt::Str, Cond::Eq, "车头拍摄场景", false, false},
            {"sidedrivingdirectioncode", "sidedrivingdirectioncode", Fmt::Int, Cond::Eq, "车侧行驶方向编码", false, false},
            {"sidedrivingdirection", "sidedrivingdirection", Fmt::Str, Cond::Eq, "车侧行驶方向", false, false},
            {"sideimageheight", "sideimageheight", Fmt::Int, Cond::Eq, "车身图高度", false, false},
            {"speed", "speed", Fmt::Str, Cond::Eq, "车速", false, false},
            {"tailplateimage", "tailplateimage", Fmt::Str, Cond::Eq, "车尾车牌图路径", false, false},
            {"headdrivingdirectioncode", "headdrivingdirectioncode", Fmt::Int, Cond::Eq, "车头行驶方向编码", false, false},
            {"headdrivingdirection", "headdrivingdirection", Fmt::Str, Cond::Eq, "车头行驶方向", false, false},
            {"cartype", "cartype", Fmt::Str, Cond::Eq, "车辆类型", false, false},
            {"plateimage", "plateimage", Fmt::Str, Cond::Eq, "车牌图路径", false, false},
            {"changelane", "changelane", Fmt::Str, Cond::Eq, "变道信息", false, false},
            {"sideimage", "sideimage", Fmt::Str, Cond::Eq, "车身图路径", false, false},
            {"tailplateposition", "tailplateposition", Fmt::Str, Cond::Eq, "车尾车牌位置", false, false},
            {"headimagewidth", "headimagewidth", Fmt::Int, Cond::Eq, "车头图宽度", false, false},
            {"headimage", "headimage", Fmt::Str, Cond::Eq, "车头图路径", false, false},
            {"carweight", "carweight", Fmt::Int, Cond::Eq, "车重", false, false},
            {"tailimageheight", "tailimageheight", Fmt::Int, Cond::Eq, "车尾图高度", false, false},
            {"devicecode", "devicecode", Fmt::Str, Cond::Eq, "设备编号", false, false},
            {"platenumber", "platenumber", Fmt::Str, Cond::Eq, "车牌号码", false, false},
            {"tailplatecolorcode", "tailplatecolorcode", Fmt::Int, Cond::Eq, "车尾车牌颜色编码", false, false},
            {"tailplatecolor", "tailplatecolor", Fmt::Str, Cond::Eq, "车尾车牌颜色", false, false},
            {"uploadtimeunix", "uploadtimeunix", Fmt::Long, Cond::Eq, nullptr, false, false},
            {"uploadtime", "uploadtime", Fmt::DateIso, Cond::Eq, nullptr, false, false},
            {"impostoraxlecount", "impostoraxlecount", Fmt::Int, Cond::Eq, "假轴数", false, false},
            {"taillanecode", "taillanecode", Fmt::Int, Cond::Eq, "车尾车道号", false, false},
            {"siteid", "siteid", Fmt::Int, Cond::Eq, "站点ID", false, false},
            {"headcapturetimeunix", "headcapturetimeunix", Fmt::Long, Cond::Eq, nullptr, false, false},
            {"headcapturetime", "headcapturetime", Fmt::DateIso, Cond::Eq, nullptr, false, false},
            {"plateposition", "plateposition", Fmt::Str, Cond::Eq, "车牌位置", false, false},
            {"tailplateimagewidth", "tailplateimagewidth", Fmt::Int, Cond::Eq, "车尾车牌图宽度", false, false},
            {"loadtime", "loadtime", Fmt::DateIso, Cond::Eq, nullptr, false, false},
            {"gradelevel", "gradelevel", Fmt::Int, Cond::Eq, nullptr, false, false},
            {"datauuid", "datauuid", Fmt::Str, Cond::Eq, nullptr, false, false},
            {"reserve1", "reserve1", Fmt::Str, Cond::Eq, nullptr, false, false},
            {"reserve2", "reserve2", Fmt::Str, Cond::Eq, nullptr, false, false},
            {"reserve3", "reserve3", Fmt::Str, Cond::Eq, nullptr, false, false},
        };
        s.orderBy = "t.big_id";
        s.excelSheetName = "OdsRtSzdnSnapshotFlowProvcaptureAddcode";
        Perms p;
        registerCrud(r, "/base/provcapture", s, p, "bigId");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsRtSzdnSnapshotFlowStationcaptureAddcode.java
        // ruoyi-system/src/main/resources/mapper/base/OdsRtSzdnSnapshotFlowStationcaptureAddcodeMapper.xml
        Spec s;
        s.table = "ods_rt_szdn_snapshot_flow_stationcapture_addcode";
        s.alias = "t";
        s.fields = {
            {"bigId", "big_id", Fmt::Long, Cond::Eq, nullptr, true, false},
            {"datasource", "datasource", Fmt::Str, Cond::Eq, "数据类型", false, false},
            {"cameratype", "cameratype", Fmt::Str, Cond::Eq, "设备类型", false, false},
            {"deviceid", "deviceid", Fmt::Str, Cond::Eq, "设备编号", false, false},
            {"deviceip", "deviceip", Fmt::Str, Cond::Eq, "设备IP", false, false},
            {"tollcode", "tollcode", Fmt::Str, Cond::Eq, "收费站编码", false, false},
            {"tollname", "tollname", Fmt::Str, Cond::Like, "收费站名称", false, false},
            {"orgcode", "orgcode", Fmt::Long, Cond::Eq, "组织机构编码", false, false},
            {"siteid", "siteid", Fmt::Long, Cond::Eq, "站点ID", false, false},
            {"laneid", "laneid", Fmt::Int, Cond::Eq, "车道编号", false, false},
            {"snapshottimeunix", "snapshottimeunix", Fmt::Long, Cond::Eq, "抓拍时间Unix格式", false, false},
            {"snapshottime", "snapshottime", Fmt::DateYmd, Cond::Eq, "抓拍时间", false, false},
            {"receivedtimeunix", "receivedtimeunix", Fmt::Long, Cond::Eq, "接收时间Unix格式", false, false},
            {"receivedtime", "receivedtime", Fmt::DateYmd, Cond::Eq, "接收时间", false, false},
            {"platenumber", "platenumber", Fmt::Str, Cond::Eq, "车牌号", false, false},
            {"platecolorcode", "platecolorcode", Fmt::Int, Cond::Eq, "车牌颜色编码", false, false},
            {"platecolor", "platecolor", Fmt::Str, Cond::Eq, "车牌颜色", false, false},
            {"platetypecode", "platetypecode", Fmt::Int, Cond::Eq, "车牌类型编码", false, false},
            {"platetype", "platetype", Fmt::Str, Cond::Eq, "车牌类型", false, false},
            {"plateconfidence", "plateconfidence", Fmt::Int, Cond::Eq, "车牌置信度", false, false},
            {"carbrand", "carbrand", Fmt::Str, Cond::Eq, "车辆品牌", false, false},
            {"carcolorcode", "carcolorcode", Fmt::Int, Cond::Eq, "车辆颜色编码", false, false},
            {"carcolor", "carcolor", Fmt::Str, Cond::Eq, "车辆颜色", false, false},
            {"cartypecode", "cartypecode", Fmt::Int, Cond::Eq, "车辆类型编码", false, false},
            {"cartype", "cartype", Fmt::Str, Cond::Eq, "车辆类型", false, false},
            {"cardirectioncode", "cardirectioncode", Fmt::Int, Cond::Eq, "行驶方向编码", false, false},
            {"cardirection", "cardirection", Fmt::Str, Cond::Eq, "行驶方向", false, false},
            {"snappicturepath", "snappicturepath", Fmt::Str, Cond::Eq, "图片路径", false, false},
            {"loadtime", "loadtime", Fmt::DateYmd, Cond::Eq, "加载时间", false, false},
            {"gradelevel", "gradelevel", Fmt::Int, Cond::Eq, "分类分级", false, false},
            {"datauuid", "datauuid", Fmt::Str, Cond::Eq, nullptr, false, false},
            {"maindirection", "maindirection", Fmt::Str, Cond::Eq, nullptr, false, false},
            {"maindirectionname", "maindirectionname", Fmt::Str, Cond::Like, nullptr, false, false},
            {"reserve3", "reserve3", Fmt::Str, Cond::Eq, nullptr, false, false},
        };
        s.orderBy = "t.big_id";
        s.excelSheetName = "OdsRtSzdnSnapshotFlowStationcaptureAddcode";
        Perms p;
        registerCrud(r, "/base/stationcapture", s, p, "bigId");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsSzdnGantry.java
        // ruoyi-system/src/main/resources/mapper/base/OdsSzdnGantryMapper.xml
        Spec s;
        s.table = "ods_szdn_gantry";
        s.alias = "t";
        s.fields = {
            {"id", "id", Fmt::Str, Cond::Eq, nullptr, true, false},
            {"gantryCode", "gantry_code", Fmt::Str, Cond::Eq, "门架编号", false, false},
            {"gantryName", "gantry_name", Fmt::Str, Cond::Like, "门架名称", false, false},
            {"roadCode", "road_code", Fmt::Str, Cond::Eq, "所属路线编码", false, false},
            {"sectionCode", "section_code", Fmt::Str, Cond::Eq, "所属路段编码", false, false},
            {"tollCode", "toll_code", Fmt::Str, Cond::Eq, "所属收费站编码", false, false},
            {"orgCode", "org_code", Fmt::Str, Cond::Eq, "所属管理中心机构编码", false, false},
            {"hexCode", "hex_code", Fmt::Str, Cond::Eq, "门架二进制编号", false, false},
            {"direction", "direction", Fmt::Str, Cond::Eq, "方向", false, false},
            {"pileNo", "pile_no", Fmt::Str, Cond::Like, "桩号", false, false},
            {"lon", "lon", Fmt::Str, Cond::Eq, "经度", false, false},
            {"lat", "lat", Fmt::Str, Cond::Eq, "纬度", false, false},
            {"isVirtual", "is_virtual", Fmt::Str, Cond::Eq, "是否虚门架", false, false},
            {"mileage", "mileage", Fmt::Str, Cond::Eq, "里程", false, false},
            {"boundaryGantryType", "boundary_gantry_type", Fmt::Str, Cond::Eq, "边界门架类型", false, false},
            {"gantryType", "gantry_type", Fmt::Str, Cond::Eq, "门架类型", false, false},
            {"cityCode", "city_code", Fmt::Str, Cond::Eq, "城市编码", false, false},
            {"districtName", "district_name", Fmt::Str, Cond::Like, "行政区名称", false, false},
            {"belongGroup", "belong_group", Fmt::Str, Cond::Eq, "是否属于集团，0：否；1：是", false, false},
            {"gantryCodeMerge", "gantry_code_merge", Fmt::Str, Cond::Eq, "门架编号", false, false},
            {"gantryNameAlias", "gantry_name_alias", Fmt::Str, Cond::Eq, "门架别名", false, false},
            {"remark", "remark", Fmt::Str, Cond::None, "备注", false, false},
        };
        s.orderBy = "t.gantry_name";
        s.excelSheetName = "门架信息";
        Perms p;
        registerCrud(r, "/base/gantry", s, p, "id");
        registerListVariant(r, "/base/gantry/listAll", s, ListKind::Paged);
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsSzdnGantryIp.java
        // ruoyi-system/src/main/resources/mapper/base/OdsSzdnGantryIpMapper.xml
        Spec s;
        s.table = "ods_szdn_gantry_ip";
        s.alias = "t";
        s.fields = {
            {"id", "id", Fmt::Long, Cond::Eq, nullptr, true, false},
            {"gantryCode", "gantry_code", Fmt::Str, Cond::Eq, "门架编号", false, false},
            {"gantryName", "gantry_name", Fmt::Str, Cond::Like, "门架名称", false, false},
            {"orgCode", "org_code", Fmt::Str, Cond::Eq, "机构编码", false, false},
            {"ip", "ip", Fmt::Str, Cond::Eq, "设备ip", false, false},
            {"brand", "brand", Fmt::Str, Cond::Eq, nullptr, false, false},
            {"type", "type", Fmt::Str, Cond::Eq, "类型1是省界门架", false, false},
        };
        s.orderBy = "t.id";
        s.excelSheetName = "OdsSzdnGantryIp";
        Perms p;
        registerCrud(r, "/base/gantryIp", s, p, "id");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsSzdnProvinceBorderVehicleWeightNewstructure.java
        // ruoyi-system/src/main/resources/mapper/base/OdsSzdnProvinceBorderVehicleWeightNewstructureMapper.xml
        Spec s;
        s.table = "ods_szdn_province_border_vehicle_weight_newstructure";
        s.alias = "t";
        s.fields = {
            {"dataSource", "dataSource", Fmt::Str, Cond::Eq, "数据来源", false, false},
            {"dataType", "dataType", Fmt::Str, Cond::Eq, "数据类型", false, false},
            {"plateNo", "plateNo", Fmt::Str, Cond::Eq, "车牌号", false, false},
            {"siteId", "siteId", Fmt::Str, Cond::Eq, "站点ID", false, false},
            {"location", "location", Fmt::Str, Cond::Eq, "设备地点", false, false},
            {"driveNo", "driveNo", Fmt::Long, Cond::Eq, "车道号", false, false},
            {"plateColor", "plateColor", Fmt::Str, Cond::Eq, "车牌颜色索引", false, false},
            {"plateColorCode", "plateColorCode", Fmt::Str, Cond::Eq, "车牌颜色代码", false, false},
            {"plateType", "plateType", Fmt::Str, Cond::Eq, "车牌类型索引", false, false},
            {"plateTypeCode", "plateTypeCode", Fmt::Str, Cond::Eq, "车牌类型代码", false, false},
            {"vehicleColor", "vehicleColor", Fmt::Str, Cond::Eq, "车辆颜色代号", false, false},
            {"vehicleColorCode", "vehicleColorCode", Fmt::Str, Cond::Eq, "车辆颜色代码", false, false},
            {"vehicleType", "vehicleType", Fmt::Str, Cond::Eq, "车辆类型代号", false, false},
            {"vehicleTypeCode", "vehicleTypeCode", Fmt::Str, Cond::Eq, "车辆类型代码", false, false},
            {"vehicleSpeed", "vehicleSpeed", Fmt::Long, Cond::Eq, "车辆速度", false, false},
            {"isOverweight", "isOverweight", Fmt::Long, Cond::Eq, "是否超载", false, false},
            {"axleNum", "axleNum", Fmt::Long, Cond::Eq, "轴数", false, false},
            {"overWeight", "overWeight", Fmt::Long, Cond::Eq, "超重量", false, false},
            {"vehicleWeight", "vehicleWeight", Fmt::Long, Cond::Eq, "重量", false, false},
            {"limitWeight", "limitWeight", Fmt::Long, Cond::Eq, "车辆限重", false, false},
            {"checkTimeUnix", "checkTimeUnix", Fmt::Long, Cond::Eq, "检测时间Unix格式", false, false},
            {"checkTime", "checkTime", Fmt::DateYmd, Cond::Eq, "检测时间", false, false},
            {"axleModel", "axleModel", Fmt::Long, Cond::Eq, "轴型", false, false},
            {"loadRate", "loadRate", Fmt::Long, Cond::Eq, "超载率", false, false},
            {"axleArray", "axleArray", Fmt::Str, Cond::Eq, "轴型详细数据", false, false},
            {"weighingImagesArry", "weighingImagesArry", Fmt::Str, Cond::Eq, "图片数组", false, false},
            {"loadTime", "load_time", Fmt::DateYmd, Cond::Eq, "加载时间", false, false},
            {"gradeLevel", "grade_level", Fmt::Long, Cond::Eq, "分类分级", false, false},
            {"datauuid", "datauuid", Fmt::Str, Cond::Eq, "datauuid", true, false},
            {"reserve1", "reserve1", Fmt::Str, Cond::Eq, nullptr, false, false},
            {"reserve2", "reserve2", Fmt::Str, Cond::Eq, nullptr, false, false},
            {"reserve3", "reserve3", Fmt::Str, Cond::Eq, nullptr, false, false},
        };
        s.excelSheetName = "OdsSzdnProvinceBorderVehicleWeightNewstructure";
        Perms p;
        registerCrud(r, "/base/vehicleweight", s, p, "dataSource");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsSzdnSection.java
        // ruoyi-system/src/main/resources/mapper/base/OdsSzdnSectionMapper.xml
        Spec s;
        s.table = "ods_szdn_section";
        s.alias = "t";
        s.fields = {
            {"id", "id", Fmt::Str, Cond::Eq, nullptr, true, false},
            {"roadCode", "road_code", Fmt::Str, Cond::Eq, "路线编码", false, false},
            {"roadName", "road_name", Fmt::Str, Cond::Like, "路线名称", false, false},
            {"sectionCode", "section_code", Fmt::Str, Cond::Eq, "路段编码", false, false},
            {"sectionName", "section_name", Fmt::Str, Cond::Like, "路段名称", false, false},
            {"startPileNo", "start_pile_no", Fmt::Long, Cond::Eq, "起点桩号", false, false},
            {"endPileNo", "end_pile_no", Fmt::Long, Cond::Eq, "终点桩号", false, false},
            {"orgCode", "org_code", Fmt::Str, Cond::Eq, "机构代码", false, false},
            {"orgName", "org_name", Fmt::Str, Cond::Like, "机构名称", false, false},
            {"orgLevelCode", "org_level_code", Fmt::Str, Cond::Eq, "层级代码", false, false},
            {"orgCategory", "org_category", Fmt::Str, Cond::Eq, "机构分类", false, false},
            {"mileage", "mileage", Fmt::Long, Cond::Eq, "里程", false, false},
            {"openDate", "open_date", Fmt::DateYmd, Cond::Eq, "通车日期", false, false},
        };
        s.orderBy = "t.road_code,t.section_code";
        s.excelSheetName = "路段信息";
        Perms p;
        registerCrud(r, "/base/section", s, p, "id");
        registerListVariant(r, "/base/section/listAll", s, ListKind::Paged);
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsSzdnToll.java
        // ruoyi-system/src/main/resources/mapper/base/OdsSzdnTollMapper.xml
        Spec s;
        s.table = "ods_szdn_toll";
        s.alias = "t";
        s.fields = {
            {"id", "id", Fmt::Str, Cond::Eq, nullptr, true, false},
            {"roadCode", "road_code", Fmt::Str, Cond::Eq, "路线编号", false, false},
            {"idCard", "id_card", Fmt::Str, Cond::Eq, "收费站业务唯一编码", false, false},
            {"tollCode", "toll_code", Fmt::Str, Cond::Eq, "收费站编号", false, false},
            {"tollName", "toll_name", Fmt::Str, Cond::Like, "收费站名称", false, false},
            {"pileNo", "pile_no", Fmt::Str, Cond::Eq, "桩号", false, false},
            {"orgName", "org_name", Fmt::Str, Cond::Like, "所属机构名称", false, false},
            {"hexCode", "hex_code", Fmt::Str, Cond::Eq, "收费站HEX编码", false, false},
            {"stateCode", "state_code", Fmt::Str, Cond::Eq, "国网编号", false, false},
            {"orgCode", "org_code", Fmt::Str, Cond::Eq, "机构编码", false, false},
            {"longitude", "longitude", Fmt::Str, Cond::Eq, "经度", false, false},
            {"latitude", "latitude", Fmt::Str, Cond::Eq, "纬度", false, false},
            {"openDate", "open_date", Fmt::DateYmd, Cond::Eq, "开通日期", false, false},
            {"tollAliasName", "toll_alias_name", Fmt::Str, Cond::Like, "收费站别名", false, false},
            {"inMonitorResource", "in_monitor_resource", Fmt::Str, Cond::Eq, "入口治超监控资源，多个以英文逗号分割", false, false},
            {"laneMonitorResource", "lane_monitor_resource", Fmt::Str, Cond::Eq, "车道抓拍监控资源，多个以英文逗号分割", false, false},
            {"squareMonitorResource", "square_monitor_resource", Fmt::Str, Cond::Eq, "广场监控资源，多个以英文逗号分割", false, false},
            {"dynamicMonitorResource", "dynamic_monitor_resource", Fmt::Str, Cond::Eq, "动环监控资源，多个以英文逗号分割", false, false},
            {"tollCodeMerge", "toll_code_merge", Fmt::Str, Cond::Eq, "收费站编号", false, false},
            {"stateCodeMerge", "state_code_merge", Fmt::Str, Cond::Eq, "国网编号", false, false},
            {"tollNameMerge", "toll_name_merge", Fmt::Str, Cond::Like, "收费站名称", false, false},
            {"sectionCode", "section_code", Fmt::Str, Cond::Eq, "所属路段编码", false, false},
            {"tollOrgCode", "toll_org_code", Fmt::Str, Cond::Eq, "收费站对应机构编码", false, false},
            {"isAccess", "is_access", Fmt::Str, Cond::Eq, "流水是否接入", false, false},
        };
        s.orderBy = "t.toll_name";
        s.excelSheetName = "收费站基础信息";
        Perms p;
        registerCrud(r, "/base/toll", s, p, "id");
        registerListVariant(r, "/base/toll/listAll", s, ListKind::Paged);
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsSzdnTollStationIp.java
        // ruoyi-system/src/main/resources/mapper/base/OdsSzdnTollStationIpMapper.xml
        Spec s;
        s.table = "ods_szdn_toll_station_ip";
        s.alias = "t";
        s.fields = {
            {"id", "id", Fmt::Long, Cond::None, nullptr, true, false},
            {"tollCode", "toll_code", Fmt::Str, Cond::Eq, nullptr, false, false},
            {"tollName", "toll_name", Fmt::Str, Cond::Like, nullptr, false, false},
            {"orgCode", "org_code", Fmt::Str, Cond::Eq, nullptr, false, false},
            {"ip", "ip", Fmt::Str, Cond::Eq, nullptr, false, false},
            {"brand", "brand", Fmt::Str, Cond::Eq, nullptr, false, false},
        };
        s.orderBy = "t.big_id";
        s.excelSheetName = "OdsSzdnTollStationIp";
        Perms p;
        registerCrud(r, "/base/tollStationIp", s, p, "id");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/base/domain/OdsYhglVBaseOrg.java
        // ruoyi-system/src/main/resources/mapper/base/OdsYhglVBaseOrgMapper.xml
        Spec s;
        s.table = "ods_yhgl_v_base_org";
        s.alias = "t";
        s.fields = {
            {"bigId", "big_id", Fmt::Str, Cond::Eq, nullptr, false, false},
            {"orgCode", "org_code", Fmt::Str, Cond::Eq, "机构代码", false, false},
            {"orgName", "org_name", Fmt::Str, Cond::Like, "机构名称", false, false},
            {"orgShortName", "org_short_name", Fmt::Str, Cond::Like, "机构简称", false, false},
            {"orgParentId", "org_parent_id", Fmt::Str, Cond::Eq, "上级机构ID", false, false},
            {"orgLevelCode", "org_level_code", Fmt::Str, Cond::Eq, "层级代码", false, false},
            {"orgIsVirtual", "org_is_virtual", Fmt::Str, Cond::Eq, "是否虚机构 1：虚机构，0：非需机构", false, false},
            {"orgMaintenance", "org_maintenance", Fmt::Str, Cond::Eq, "是否是养护类", false, false},
            {"orgSequence", "org_sequence", Fmt::Long, Cond::Eq, "机构顺序", false, false},
            {"orgIsManager", "org_is_manager", Fmt::Str, Cond::Eq, nullptr, false, false},
            {"orgIsDeleted", "org_is_deleted", Fmt::Str, Cond::Eq, "是否删除 1：是 0：否", false, false},
            {"orgCategory", "org_category", Fmt::Str, Cond::Eq, "机构分类： 01集团 02公司 03管理中心 10部门 11所 12服务区 13养护区 14站 15项目办 16信息中心 17项目部  99其它", false, false},
            {"orgIsAuthorized", "org_is_authorized", Fmt::Str, Cond::Eq, "是否授权机构 1：是 0：否", false, false},
            {"orgAddress", "org_address", Fmt::Str, Cond::Eq, "机构地址", false, false},
            {"orgIsYhAutarky", "org_is_yh_autarky", Fmt::Str, Cond::Eq, "是自营养护单位", false, false},
            {"loadTime", "load_time", Fmt::DateYmd, Cond::Eq, "加载时间", false, false},
            {"gradeLevel", "grade_level", Fmt::Int, Cond::Eq, "分类分级", false, false},
        };
        s.orderBy = "t.big_id";
        s.excelSheetName = "机构信息";
        Perms p;
        registerCrud(r, "/base/org", s, p, "bigId");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/base/domain/ZdataLocationDict.java
        // ruoyi-system/src/main/resources/mapper/base/ZdataLocationDictMapper.xml
        Spec s;
        s.table = "zdata_location_dict";
        s.alias = "t";
        s.fields = {
            {"id", "id", Fmt::Long, Cond::Eq, nullptr, false, false},
            {"type", "type", Fmt::Str, Cond::Eq, "类型", false, false},
            {"name", "name", Fmt::Str, Cond::Like, "收费站", false, false},
            {"rawCode", "raw_code", Fmt::Str, Cond::Eq, "轨迹表和实时轨迹code", false, false},
            {"standardCode", "standard_code", Fmt::Str, Cond::Eq, "收费站/门架code", false, false},
            {"roadcode", "roadcode", Fmt::Str, Cond::Eq, "路线编码", false, false},
            {"roadname", "roadname", Fmt::Str, Cond::Like, "路线名称", false, false},
            {"sectioncode", "sectioncode", Fmt::Str, Cond::Eq, "路段编码", false, false},
            {"sectionname", "sectionname", Fmt::Str, Cond::Like, "路段名称", false, false},
            {"tollcode", "tollcode", Fmt::Str, Cond::Eq, "收费站编码", false, false},
            {"tollname", "tollname", Fmt::Str, Cond::Like, "收费站名称", false, false},
            {"orgcode", "orgcode", Fmt::Str, Cond::Eq, "组织机构编码", false, false},
            {"orgname", "orgname", Fmt::Str, Cond::Like, "组织机构名称", false, false},
            {"createdAt", "created_at", Fmt::DateYmd, Cond::Eq, "创建时间", false, false},
            {"updatedAt", "updated_at", Fmt::DateYmd, Cond::Eq, "修改时间", false, false},
        };
        s.excelSheetName = "ZdataLocationDict";
        Perms p;
        registerCrud(r, "/base/location", s, p, "id");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/base/domain/ZdataTrailFitting.java
        // ruoyi-system/src/main/resources/mapper/base/ZdataTrailFittingMapper.xml
        Spec s;
        s.table = "zdata_trail_fitting";
        s.alias = "t";
        s.fields = {
            {"cid", "cid", Fmt::Str, Cond::None, nullptr, false, false},
            {"enaxlecount", "enaxlecount", Fmt::Int, Cond::Eq, "入口车轴数", false, false},
            {"entime", "entime", Fmt::DateYmd, Cond::Eq, "入口时间", false, false},
            {"entolllaneid", "entolllaneid", Fmt::Str, Cond::Eq, "入口车道编号", false, false},
            {"entollstationid", "entollstationid", Fmt::Str, Cond::Eq, "入口收费站编号", false, false},
            {"entollstationname", "entollstationname", Fmt::Str, Cond::Like, "入口收费站名称", false, false},
            {"envehicleclass", "envehicleclass", Fmt::Int, Cond::Eq, "入口车型分类", false, false},
            {"envehicleid", "envehicleid", Fmt::Str, Cond::Eq, "入口车辆编号", false, false},
            {"envehicletype", "envehicletype", Fmt::Int, Cond::Eq, "入口车辆类型代码", false, false},
            {"enweight", "enweight", Fmt::Long, Cond::Eq, "入口称重", false, false},
            {"extime", "extime", Fmt::DateIso, Cond::Eq, "出口时间", false, false},
            {"extolllaneid", "extolllaneid", Fmt::Str, Cond::Eq, "出口车道编号", false, false},
            {"extollstationid", "extollstationid", Fmt::Str, Cond::Eq, "出口收费站编号", false, false},
            {"extollstationname", "extollstationname", Fmt::Str, Cond::Like, "出口收费站名称", false, false},
            {"exvehicleclass", "exvehicleclass", Fmt::Int, Cond::Eq, "出口车型分类", false, false},
            {"exvehicleid", "exvehicleid", Fmt::Str, Cond::Eq, "出口车辆编号", false, false},
            {"exvehicletype", "exvehicletype", Fmt::Int, Cond::Eq, "出口车辆类型代码", false, false},
            {"exweight", "exweight", Fmt::Long, Cond::Eq, "出口称重", false, false},
            {"trailpoints", "trailpoints", Fmt::Str, Cond::Eq, "拟合轨迹点集合", false, false},
        };
        s.excelSheetName = "ZdataTrailFitting";
        Perms p;
        registerCrud(r, "/base/fitting", s, p, "cid");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/base/domain/ZdataTrailTracks.java
        // ruoyi-system/src/main/resources/mapper/base/ZdataTrailTracksMapper.xml
        Spec s;
        s.table = "zdata_trail_tracks";
        s.alias = "t";
        s.fields = {
            {"uuid", "uuid", Fmt::Str, Cond::Eq, "唯一标识符", true, false},
            {"type", "type", Fmt::Int, Cond::Eq, "轨迹类型", false, false},
            {"pointCount", "point_count", Fmt::Long, Cond::Eq, "轨迹点数量", false, false},
            {"plateKey", "plate_key", Fmt::Str, Cond::Like, "车牌唯一标识", false, false},
            {"enterTime", "enter_time", Fmt::DateYmdHms, Cond::Eq, "进入时间", false, false},
            {"exitTime", "exit_time", Fmt::DateYmdHms, Cond::Eq, "离开时间", false, false},
            {"trailPoints", "trail_points", Fmt::Str, Cond::Eq, "轨迹点集合，推荐存 JSON 格式，包含坐标/时间/速度等信息", false, false},
            {"enterLocationcode", "enter_locationcode", Fmt::Str, Cond::None, "进入位置code", false, false},
            {"exitLocationcode", "exit_locationcode", Fmt::Str, Cond::None, "离开位置code", false, false},
            {"trackJosn", "track_josn", Fmt::Str, Cond::None, "集合详情", false, false},
            {"enaxlecount", "enaxlecount", Fmt::Int, Cond::None, "入口车轴数", false, false},
            {"entolllaneid", "entolllaneid", Fmt::Str, Cond::None, "入口车道编号", false, false},
            {"entollstationid", "entollstationid", Fmt::Str, Cond::Eq, "入口收费站编号", false, false},
            {"entollstationname", "entollstationname", Fmt::Str, Cond::None, "入口收费站名称", false, false},
            {"envehicleclass", "envehicleclass", Fmt::Str, Cond::None, "入口车型分类", false, false},
            {"envehicleid", "envehicleid", Fmt::Str, Cond::None, "入口车辆编号", false, false},
            {"envehicletype", "envehicletype", Fmt::Str, Cond::None, "入口车辆类型代码", false, false},
            {"enweight", "enweight", Fmt::Double, Cond::None, "入口称重", false, false},
            {"extolllaneid", "extolllaneid", Fmt::Str, Cond::None, "出口车道编号", false, false},
            {"extollstationid", "extollstationid", Fmt::Str, Cond::None, "出口收费站编号", false, false},
            {"extollstationname", "extollstationname", Fmt::Str, Cond::None, "出口收费站名称", false, false},
            {"exvehicleclass", "exvehicleclass", Fmt::Str, Cond::None, "出口车型分类", false, false},
            {"exvehicleid", "exvehicleid", Fmt::Str, Cond::None, "出口车辆编号", false, false},
            {"exvehicletype", "exvehicletype", Fmt::Str, Cond::None, "出口车辆类型代码", false, false},
            {"exweight", "exweight", Fmt::Double, Cond::None, "出口称重", false, false},
            {"startLon", "start_lon", Fmt::Str, Cond::None, "入口收费站经度", false, false},
            {"stratLat", "strat_lat", Fmt::Str, Cond::None, "入口收费站维度", false, false},
            {"endLon", "end_lon", Fmt::Str, Cond::None, "出口收费站经度", false, false},
            {"endLat", "end_lat", Fmt::Str, Cond::None, "出口收费站维度", false, false},
        };
        s.orderBy = "t.enter_time desc";
        s.excelSheetName = "ZdataTrailTracks";
        Perms p;
        registerCrud(r, "/base/trailtracks", s, p, "uuid");
    }
}

} // namespace cm::web::crud
