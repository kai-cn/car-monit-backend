// JAVA 对照: 各业务缓存写入方（CarInfoServiceImpl#updateRedisCarList、
//
//	CarWhiteInfoServiceImpl#updateRedisCarWhiteList、
//	CarWarningInfoServiceImpl#updateRedisWarningList、
//	CarWarningConfigServiceImpl#cacheWarningConfig、GeometryServiceImpl#updateRedisList、
//	DictUtils#setDictCache、TokenService#setLoginUser）
//
// 类/职责: 与 Java 共用 Redis 时，各缓存键需要的 FastJson2 类型信息
// 对应 Go 文件: internal/cache/javatypes.go
//
// 下面的 RootType / Longs 是从 Java 进程真实写入的原值里核对出来的
// （fastjson2 只给包装类型 Long 补 L，null 字段一律不写）。
package cache

// managerAuditLongs 是 manager/base 里那些继承 BasePlusEntity 的实体共同的 Long 字段：
// epsId / createBy / updateBy / tenantId 是 Long，sort 是 Integer（不补 L）。
var managerAuditLongs = map[string]bool{
	"epsId": true, "createBy": true, "updateBy": true, "tenantId": true,
}

var (
	// LoginUserJava login_tokens:* —— Java 强转 LoginUser，缺 @type 即 ClassCastException。
	//
	// JAVA 对照: LoginUser.expireTime/loginTime 是原始类型 long，不补 L；
	// permissions 是 Set<String>；user/dept/roles 的 params 是 HashMap。
	LoginUserJava = JavaOptions{
		RootType: "com.ruoyi.common.core.domain.model.LoginUser",
		Longs: map[string]bool{
			"deptId": true, "parentId": true, "roleId": true,
			"tenantId": true, "userId": true, "userNo": true,
		},
		Sets: map[string]bool{"permissions": true},
		Maps: map[string]bool{"params": true},
	}

	// CarInfoJava car_list（List<CarInfo> 存成一个 string 值）
	CarInfoJava = JavaOptions{
		RootType: "com.ruoyi.manager.domain.CarInfo",
		Longs:    withKeys(managerAuditLongs, "carNum"),
	}

	// CarWhiteInfoJava white_car_list
	CarWhiteInfoJava = JavaOptions{
		RootType: "com.ruoyi.manager.domain.CarWhiteInfo",
		Longs:    withKeys(managerAuditLongs, "carNum"),
	}

	// CarWarningInfoJava car_warning_list
	CarWarningInfoJava = JavaOptions{
		RootType: "com.ruoyi.manager.domain.CarWarningInfo",
		Longs:    withKeys(managerAuditLongs, "carNum"),
	}

	// CarVOJava car_list_jc（Java 只写 carId/carNo）
	CarVOJava = JavaOptions{RootType: "com.ruoyi.base.domain.CarVO"}

	// CarWarningConfigJava car_warning_config_list
	CarWarningConfigJava = JavaOptions{
		RootType: "com.ruoyi.base.domain.CarWarningConfig",
		Longs:    map[string]bool{"timeSpan": true},
	}

	// GeometryJava lxbh_jdwd:（Geometry.id 是 Integer，不补 L）
	GeometryJava = JavaOptions{RootType: "com.ruoyi.base.domain.Geometry"}

	// OdsSzdnSectionJava section_list（Redis LIST，每个元素一条）
	OdsSzdnSectionJava = JavaOptions{RootType: "com.ruoyi.base.domain.OdsSzdnSection"}

	// OdsSzdnGantryJava gantry_list
	OdsSzdnGantryJava = JavaOptions{RootType: "com.ruoyi.base.domain.OdsSzdnGantry"}

	// SysDictDataJava sys_dict:<type> —— Java 用 setCacheObject 把整个数组写成一个 string 值，
	// 每个元素带自己的 @type；dictCode/dictSort 是 Long。
	SysDictDataJava = JavaOptions{
		RootType: "com.ruoyi.common.core.domain.entity.SysDictData",
		Longs:    map[string]bool{"dictCode": true, "dictSort": true},
		Maps:     map[string]bool{"params": true},
	}
)

func withKeys(base map[string]bool, extra ...string) map[string]bool {
	out := make(map[string]bool, len(base)+len(extra))
	for k := range base {
		out[k] = true
	}
	for _, k := range extra {
		out[k] = true
	}
	return out
}
