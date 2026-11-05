// JAVA 对照: com.ruoyi.base.domain.* 上的 @Excel(name=...) 注解
// 类/职责: ExcelUtil 导出的列定义（表头文案与列顺序照抄实体字段声明顺序）
// 对应 Go 文件: internal/modules/base/exports.go
//
// DIFF: @Excel(readConverterExp) 只影响导入，这里不处理；@Excel(dateFormat="yyyy-MM-dd")
// 的日期列用 DateOnly 输出。
package base

// serviceAreaExportCols 对应 BaseConfigServiceArea 的 @Excel 列。
func serviceAreaExportCols() []exportCol {
	return []exportCol{
		{Title: "判定进入的服务区编码", Field: "fwqbm"},
		{Title: "判定进入的服务区名称", Field: "fwqmc"},
		{Title: "经度", Field: "lon"},
		{Title: "维度", Field: "lat"},
		{Title: "路线编码", Field: "roadCode"},
		{Title: "路段编码", Field: "sectionCode"},
		{Title: "桩号", Field: "pileNo"},
	}
}

// warningConfigExportCols 对应 CarWarningConfig 的 @Excel 列。
func warningConfigExportCols() []exportCol {
	return []exportCol{
		{Title: "进入门架编号", Field: "gantryCodeIn", Exp: "分=离"},
		{Title: "进入门架名称", Field: "gantryNameIn"},
		{Title: "出去门架编号", Field: "gantryCodeOut", Exp: "分=离"},
		{Title: "出去门架名称", Field: "gantryNameOut"},
		{Title: "判定时间间隔", Field: "timeSpan", Exp: "分=钟"},
		{Title: "判定进入的服务区编码", Field: "fwqbm"},
		{Title: "判定进入的服务区名称", Field: "fwqmc"},
		{Title: "经度", Field: "lon"},
		{Title: "维度", Field: "lat"},
		{Title: "路线编码", Field: "roadCode"},
		{Title: "路段编码", Field: "sectionCode"},
		{Title: "桩号", Field: "pileNo"},
		{Title: "备注", Field: "remark"},
	}
}

// fwqjcxxExportCols 对应 DwdLcztFwqjcxx 的 @Excel 列（agentPk 没有 @Excel）。
func fwqjcxxExportCols() []exportCol {
	return []exportCol{
		{Title: "源系统主键", Field: "yxtzj"},
		{Title: "服务区编码", Field: "fwqbm"},
		{Title: "服务区名称", Field: "fwqmc"},
		{Title: "纬度", Field: "wd"},
		{Title: "方向名称", Field: "fxmc"},
		{Title: "方向代码", Field: "fxdm"},
		{Title: "经度", Field: "jd"},
		{Title: "所属路线编号", Field: "sslxbh"},
		{Title: "所属路线名称", Field: "sslxmc"},
		{Title: "所属路段编号", Field: "ssldbh"},
		{Title: "所属路段名称", Field: "ssldmc"},
		{Title: "所处桩号(K格式)", Field: "sczhkgs"},
		{Title: "所处桩号(数值格式)", Field: "sczhszgs"},
		{Title: "所属管理中心编码", Field: "ssglzxbm"},
		{Title: "所属管理中心名称", Field: "ssglzxmc"},
		{Title: "行政区划名称", Field: "xzqhmc"},
		{Title: "营业日期", Field: "yyrq"},
		{Title: "车位数", Field: "cws"},
		{Title: "是否设置了卡口", Field: "sfszlkk"},
		{Title: "充电桩数", Field: "cdzs"},
		{Title: "是否餐饮服务", Field: "sfcyfw"},
		{Title: "是否提供住宿服务", Field: "sftgzsfw"},
		{Title: "是否提供汽修服务", Field: "sftgqxfw"},
		{Title: "是否提供超市服务", Field: "sftgcsfw"},
		{Title: "是否提供加油服务", Field: "sftgjyfw"},
		{Title: "面积(平方米)", Field: "mj"},
		{Title: "是否提供厕所服务", Field: "sftgcshfw"},
		{Title: "行政区划代码", Field: "xzqhdm"},
		{Title: "使用年限", Field: "synx"},
		{Title: "来源系统", Field: "lyxt"},
		{Title: "加载日期", Field: "loadTime"},
		{Title: "全字段MD5", Field: "allColPk"},
	}
}

// sfsjcxxExportCols 对应 DwdLcztSfsjcxx 的 @Excel 列。
func sfsjcxxExportCols() []exportCol {
	return []exportCol{
		{Title: "源系统主键", Field: "yxtzj"},
		{Title: "收费所编码", Field: "sfsbm"},
		{Title: "收费所名称", Field: "sfsmc"},
		{Title: "经度", Field: "jd"},
		{Title: "纬度", Field: "wd"},
		{Title: "所属路线编号", Field: "sslxbh"},
		{Title: "所属路线名称", Field: "sslxmc"},
		{Title: "所属路段编号", Field: "ssldbh"},
		{Title: "所属路段名称", Field: "ssldmc"},
		{Title: "所处桩号(K格式)", Field: "sczhK"},
		{Title: "所处桩号(数值格式)", Field: "sczhN"},
		{Title: "所属管理中心编码", Field: "ssglzxbm"},
		{Title: "所属管理中心名称", Field: "ssglzxmc"},
		{Title: "来源系统", Field: "lyxt"},
		{Title: "加载日期", Field: "loadTime"},
		{Title: "全字段MD5", Field: "allColPk"},
	}
}

// sfzjcxxExportCols 对应 DwdLcztSfzjcxx 的 @Excel 列。
func sfzjcxxExportCols() []exportCol {
	return []exportCol{
		{Title: "源系统主键", Field: "yxtzj"},
		{Title: "收费站代码", Field: "sfzdm"},
		{Title: "收费站名称", Field: "sfzmc"},
		{Title: "经度", Field: "jd"},
		{Title: "纬度", Field: "wd"},
		{Title: "所属路线编号", Field: "sslxbh"},
		{Title: "所属路线名称", Field: "sslxmc"},
		{Title: "所属路段编号", Field: "ssldbh"},
		{Title: "所属路段名称", Field: "ssldmc"},
		{Title: "所处桩号(K格式)", Field: "sczhK"},
		{Title: "所处桩号(数值格式)", Field: "sczhN"},
		{Title: "所属管理中心编码", Field: "ssglzxbm"},
		{Title: "所属管理中心名称", Field: "ssglzxmc"},
		{Title: "来源系统", Field: "lyxt"},
		{Title: "加载日期", Field: "loadTime"},
		{Title: "全字段MD5", Field: "allColPk"},
	}
}

// geometryExportCols 对应 Geometry 的 @Excel 列。
func geometryExportCols() []exportCol {
	return []exportCol{
		{Title: "路线编号", Field: "lxbh"},
		{Title: "路线方向", Field: "lxfx"},
		{Title: "起点桩号", Field: "qdzh"},
		{Title: "终点桩号", Field: "zdzh"},
		{Title: "经纬度", Field: "paths"},
	}
}

// sectionExportCols 对应 OdsSzdnSection 的 @Excel 列。
func sectionExportCols() []exportCol {
	return []exportCol{
		{Title: "路线编码", Field: "roadCode"},
		{Title: "路线名称", Field: "roadName"},
		{Title: "路段编码", Field: "sectionCode"},
		{Title: "路段名称", Field: "sectionName"},
		{Title: "起点桩号", Field: "startPileNo"},
		{Title: "终点桩号", Field: "endPileNo"},
		{Title: "机构代码", Field: "orgCode"},
		{Title: "机构名称", Field: "orgName"},
		{Title: "层级代码", Field: "orgLevelCode"},
		{Title: "机构分类", Field: "orgCategory"},
		{Title: "里程", Field: "mileage"},
		{Title: "通车日期", Field: "openDate", DateOnly: true},
	}
}

// tollExportCols 对应 OdsSzdnToll 的 @Excel 列（sectionName 没有 @Excel）。
func tollExportCols() []exportCol {
	return []exportCol{
		{Title: "路线编号", Field: "roadCode"},
		{Title: "收费站业务唯一编码", Field: "idCard"},
		{Title: "收费站编号", Field: "tollCode", Exp: "内=部"},
		{Title: "收费站名称", Field: "tollName", Exp: "内=部"},
		{Title: "桩号", Field: "pileNo"},
		{Title: "所属机构名称", Field: "orgName"},
		{Title: "收费站HEX编码", Field: "hexCode"},
		{Title: "国网编号", Field: "stateCode", Exp: "内=部"},
		{Title: "机构编码", Field: "orgCode"},
		{Title: "经度", Field: "longitude"},
		{Title: "纬度", Field: "latitude"},
		{Title: "开通日期", Field: "openDate", DateOnly: true},
		{Title: "收费站别名", Field: "tollAliasName"},
		{Title: "入口治超监控资源，多个以英文逗号分割", Field: "inMonitorResource"},
		{Title: "车道抓拍监控资源，多个以英文逗号分割", Field: "laneMonitorResource"},
		{Title: "广场监控资源，多个以英文逗号分割", Field: "squareMonitorResource"},
		{Title: "动环监控资源，多个以英文逗号分割", Field: "dynamicMonitorResource"},
		{Title: "收费站编号", Field: "tollCodeMerge"},
		{Title: "国网编号", Field: "stateCodeMerge"},
		{Title: "收费站名称", Field: "tollNameMerge"},
		{Title: "所属路段编码", Field: "sectionCode"},
		{Title: "收费站对应机构编码", Field: "tollOrgCode"},
		{Title: "流水是否接入", Field: "isAccess"},
	}
}

// orgExportCols 对应 OdsYhglVBaseOrg 的 @Excel 列（bigId/parentId 没有 @Excel）。
func orgExportCols() []exportCol {
	return []exportCol{
		{Title: "机构代码", Field: "orgCode"},
		{Title: "机构名称", Field: "orgName"},
		{Title: "机构简称", Field: "orgShortName"},
		{Title: "上级机构ID", Field: "orgParentId"},
		{Title: "层级代码", Field: "orgLevelCode"},
		{Title: "是否虚机构 1：虚机构，0：非需机构", Field: "orgIsVirtual"},
		{Title: "是否是养护类", Field: "orgMaintenance", Exp: "1=：是，0否"},
		{Title: "机构顺序", Field: "orgSequence"},
		{Title: "是否管理单位，主要指是否是路段管理单位(1：是,0：否)", Field: "orgIsManager"},
		{Title: "是否删除 1：是 0：否", Field: "orgIsDeleted"},
		{Title: "机构分类： 01集团 02公司 03管理中心 10部门 11所 12服务区 13养护区 14站 15项目办 16信息中心 17项目部  99其它", Field: "orgCategory"},
		{Title: "是否授权机构 1：是 0：否", Field: "orgIsAuthorized"},
		{Title: "机构地址", Field: "orgAddress"},
		{Title: "是自营养护单位", Field: "orgIsYhAutarky"},
		{Title: "加载时间", Field: "loadTime", DateOnly: true},
		{Title: "分类分级", Field: "gradeLevel"},
	}
}
