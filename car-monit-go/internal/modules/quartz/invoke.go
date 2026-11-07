// JAVA 对照: ruoyi-quartz/src/main/java/com/ruoyi/quartz/util/JobInvokeUtil.java:1-182
// JAVA 对照: ruoyi-common/src/main/java/com/ruoyi/common/constant/Constants.java:164-173
// 类/职责: invokeTarget "bean.method(params)" 解析、白名单校验、方法派发
// 对应 Go 文件: internal/modules/quartz/invoke.go
// 关键映射: SpringUtils.getBean(beanName) + 反射 Method.invoke -> 任务注册表（bean -> method -> func）
//
// DIFF: Java 用反射调用任意 Bean / 任意类（Class.forName）。Go 没有运行时反射调用 Spring Bean 的能力，
// 用显式注册表承担：只有注册过的 bean.method 可执行。Class 形式（≥2 个点）也只允许
// com.ruoyi.quartz.task 包下的类，并映射回同名 bean。
// DIFF: Constants.JOB_ERROR_STR 在 Java 侧只是常量（本仓库的 JobInvokeUtil 未使用），
// 这里按任务要求真正生效：命中黑名单直接拒绝，属于安全加固，业务上只会拒绝本应失败的调用。
// DIFF: 参数类型推断完全沿用 Java 的规则（'x'->String、true/false->Boolean、含 L->Long、
// 含 D->Double、其余->Integer），因此 "5" 传进去是 Integer，任务方法在 Go 侧按 int 接收。
package quartz

import (
	"context"
	"errors"
	"fmt"
	"strconv"
	"strings"

	"car-monit-go/internal/app"
)

// javaJobErrorStr 对应 Constants.JOB_ERROR_STR（定时任务违规的字符）。
var javaJobErrorStr = []string{
	"java.net.URL",
	"javax.naming.InitialContext",
	"org.yaml.snakeyaml",
	"org.springframework",
	"org.apache",
	"com.ruoyi.common.utils.file",
	"com.ruoyi.common.config",
	"com.ruoyi.generator",
}

// javaJobWhitelistStr 对应 Constants.JOB_WHITELIST_STR（仅允许访问的包名）。
var javaJobWhitelistStr = []string{"com.ruoyi.quartz.task"}

// TaskFunc 是被调度方法的 Go 形态。
// args 已按 JobInvokeUtil.getMethodParams 的规则转换为 string/bool/int64/float64/int。
type TaskFunc func(ctx context.Context, args []any) error

type taskBean struct {
	name    string
	methods map[string]TaskFunc
}

// Invoker 是 JobInvokeUtil + SpringUtils 的组合体。
type Invoker struct {
	beans map[string]*taskBean
}

// NewInvoker 构造任务注册表，等价于 Spring 容器中所有 @Component 任务 Bean。
func NewInvoker(a *app.App) *Invoker {
	inv := &Invoker{beans: map[string]*taskBean{}}
	for _, b := range builtinTaskBeans(a) {
		inv.beans[b.name] = b
	}
	return inv
}

// IsValidClassName 对应 JobInvokeUtil.isValidClassName：点的个数 > 1 视为全限定类名。
func IsValidClassName(invokeTarget string) bool {
	return strings.Count(invokeTarget, ".") > 1
}

// GetBeanName 对应 JobInvokeUtil.getBeanName。
func GetBeanName(invokeTarget string) string {
	beanName := substringBefore(invokeTarget, "(")
	return substringBeforeLast(beanName, ".")
}

// GetMethodName 对应 JobInvokeUtil.getMethodName。
func GetMethodName(invokeTarget string) string {
	methodName := substringBefore(invokeTarget, "(")
	return substringAfterLast(methodName, ".")
}

// GetMethodParams 对应 JobInvokeUtil.getMethodParams。
func GetMethodParams(invokeTarget string) ([]any, error) {
	methodStr := substringBetween(invokeTarget, "(", ")")
	if strings.TrimSpace(methodStr) == "" {
		return nil, nil
	}
	parts := strings.Split(methodStr, ",")
	out := make([]any, 0, len(parts))
	for _, raw := range parts {
		str := strings.TrimSpace(raw)
		switch {
		case strings.Contains(str, "'"):
			out = append(out, strings.ReplaceAll(str, "'", ""))
		case str == "true" || strings.EqualFold(str, "false"):
			v, err := strconv.ParseBool(strings.ToLower(str))
			if err != nil {
				return nil, fmt.Errorf("参数解析失败: %s", str)
			}
			out = append(out, v)
		case strings.Contains(strings.ToUpper(str), "L"):
			v, err := strconv.ParseInt(strings.ReplaceAll(strings.ToUpper(str), "L", ""), 10, 64)
			if err != nil {
				return nil, fmt.Errorf("参数解析失败（Long）: %s", str)
			}
			out = append(out, v)
		case strings.Contains(strings.ToUpper(str), "D"):
			v, err := strconv.ParseFloat(strings.ReplaceAll(strings.ToUpper(str), "D", ""), 64)
			if err != nil {
				return nil, fmt.Errorf("参数解析失败（Double）: %s", str)
			}
			out = append(out, v)
		default:
			// JAVA 对照: Integer.valueOf(str) —— 失败即抛 NumberFormatException。
			v, err := strconv.Atoi(str)
			if err != nil {
				return nil, fmt.Errorf("参数解析失败（Integer）: %s", str)
			}
			out = append(out, v)
		}
	}
	return out, nil
}

// CheckInvokeTarget 实现 JOB_ERROR_STR 黑名单 + com.ruoyi.quartz.task 白名单校验。
func CheckInvokeTarget(invokeTarget string) error {
	target := strings.TrimSpace(invokeTarget)
	if target == "" {
		return errors.New("调用目标字符串不能为空")
	}
	if !strings.HasSuffix(target, ")") || !strings.Contains(target, "(") {
		return fmt.Errorf("调用目标字符串格式非法: %s", target)
	}
	lower := strings.ToLower(target)
	for _, bad := range javaJobErrorStr {
		if strings.Contains(lower, strings.ToLower(bad)) {
			return fmt.Errorf("调用目标字符串包含违规字符 %s，不允许执行", bad)
		}
	}
	beanName := GetBeanName(target)
	if beanName == "" || GetMethodName(target) == "" {
		return fmt.Errorf("调用目标字符串格式非法: %s", target)
	}
	if IsValidClassName(beanName) && !hasPrefixAny(beanName, javaJobWhitelistStr) {
		return fmt.Errorf("调用目标 %s 不在白名单 %v 内，不允许执行", beanName, javaJobWhitelistStr)
	}
	return nil
}

func hasPrefixAny(s string, prefixes []string) bool {
	for _, p := range prefixes {
		if strings.HasPrefix(s, p) {
			return true
		}
	}
	return false
}

// resolveBean 对应 SpringUtils.getBean(beanName) / Class.forName(beanName).newInstance()。
// 类名形式（com.ruoyi.quartz.task.RyTask）按简单类名映射到同名 bean（首字母大小写不敏感）。
func (i *Invoker) resolveBean(beanName string) *taskBean {
	if b, ok := i.beans[beanName]; ok {
		return b
	}
	simple := beanName
	if idx := strings.LastIndexByte(simple, '.'); idx >= 0 {
		simple = simple[idx+1:]
	}
	for name, b := range i.beans {
		if strings.EqualFold(name, simple) {
			return b
		}
	}
	return nil
}

// unmigratedTargets 记录"Java 有、Go 未迁移"的数据接入任务。
//
// DIFF: Java 允许保存这些任务（执行时才失败）；Go 版本在保存阶段直接拒绝，
// 避免运维看到"保存成功"却只能在 sys_job_log 里发现持续失败。
// 归属决策见 docs/MAPPING.md §4 与 docs/MIGRATION_GUIDE.md「数据接入边界」。
var unmigratedTargets = map[string]string{
	"trackTask.syncHistoryTrack": "历史轨迹同步依赖 ICarTrackInfoService/IGeometryService 与远端轨迹接口",

	"vehicleMonitoringTask.syncOrgInfo":             "机构信息同步依赖 HttpBaseInfoApiService",
	"vehicleMonitoringTask.syncSectionInfo":         "路段信息同步依赖 HttpBaseInfoApiService",
	"vehicleMonitoringTask.syncGantryInfo":          "门架信息同步依赖 HttpBaseInfoApiService",
	"vehicleMonitoringTask.syncServiceAreaInfoInfo": "服务区信息同步依赖 HttpBaseInfoApiService",
	"vehicleMonitoringTask.syncTollBoothInfoInfo":   "收费所信息同步依赖 HttpBaseInfoApiService",
	"vehicleMonitoringTask.syncSfzjcxxInfoInfo":     "收费站位置同步依赖 HttpBaseInfoApiService",
	"vehicleMonitoringTask.syncTollStationInfo":     "收费站信息同步依赖 HttpBaseInfoApiService",

	"snapshotFlowSyncTask.syncFullData":          "门架抓拍流水全量同步依赖 GaussDB 与分表 Mapper",
	"snapshotFlowSyncTask.manualFullSync":        "门架抓拍流水全量同步依赖 GaussDB 与分表 Mapper",
	"snapshotFlowSyncTask.manualIncrementalSync": "门架抓拍流水增量同步依赖 GaussDB 与分表 Mapper",
	"snapshotFlowSyncTask.syncIncrementalData":   "门架抓拍流水增量同步依赖 GaussDB 与分表 Mapper",
	"snapshotFlowSyncTask.syncSingleMonth":       "门架抓拍流水单月同步依赖 GaussDB 与分表 Mapper",
	"snapshotFlowSyncTask.preCreateTables":       "分表预创建依赖 ShardingTableUtil",
}

// ValidateTarget 在保存任务时做一次快速失败校验（DIFF: Java 直到执行时才暴露错误）。
func (i *Invoker) ValidateTarget(invokeTarget string) error {
	if err := CheckInvokeTarget(invokeTarget); err != nil {
		return err
	}
	key := GetBeanName(invokeTarget) + "." + GetMethodName(invokeTarget)
	if reason, ok := unmigratedTargets[key]; ok {
		return fmt.Errorf("任务 %s 尚未迁移到 Go 版本（%s）；该能力仍由 Java 数据接入服务承担，"+
			"请在 Java 侧配置或等待后续版本", invokeTarget, reason)
	}
	bean := i.resolveBean(GetBeanName(invokeTarget))
	if bean == nil {
		return fmt.Errorf("调用目标不存在（未注册的 Bean）: %s", GetBeanName(invokeTarget))
	}
	if _, ok := bean.methods[GetMethodName(invokeTarget)]; !ok {
		return fmt.Errorf("调用目标不存在（未注册的方法）: %s", invokeTarget)
	}
	return nil
}

// Invoke 对应 JobInvokeUtil.invokeMethod(SysJob)。
func (i *Invoker) Invoke(ctx context.Context, job *SysJob) error {
	return i.InvokeTarget(ctx, job.InvokeTarget)
}

// InvokeTarget 执行 invokeTarget 指定的方法。
func (i *Invoker) InvokeTarget(ctx context.Context, invokeTarget string) error {
	if err := CheckInvokeTarget(invokeTarget); err != nil {
		return err
	}
	bean := i.resolveBean(GetBeanName(invokeTarget))
	if bean == nil {
		return fmt.Errorf("NoSuchBeanDefinitionException: %s", GetBeanName(invokeTarget))
	}
	fn, ok := bean.methods[GetMethodName(invokeTarget)]
	if !ok {
		return fmt.Errorf("NoSuchMethodException: %s.%s", bean.name, GetMethodName(invokeTarget))
	}
	params, err := GetMethodParams(invokeTarget)
	if err != nil {
		return err
	}
	if err := fn(ctx, params); err != nil {
		return err
	}
	return nil
}

// substringBefore 对应 StringUtils.substringBefore（分隔符不存在时返回原串）。
func substringBefore(s, sep string) string {
	if idx := strings.Index(s, sep); idx >= 0 {
		return s[:idx]
	}
	return s
}

// substringAfterLast 对应 StringUtils.substringAfterLast（分隔符不存在时返回空串）。
func substringAfterLast(s, sep string) string {
	if idx := strings.LastIndex(s, sep); idx >= 0 {
		return s[idx+len(sep):]
	}
	return ""
}

// substringBeforeLast 对应 StringUtils.substringBeforeLast（分隔符不存在时返回原串）。
func substringBeforeLast(s, sep string) string {
	if idx := strings.LastIndex(s, sep); idx >= 0 {
		return s[:idx]
	}
	return s
}

// substringBetween 对应 StringUtils.substringBetween(s, "(", ")")。
func substringBetween(s, open, close string) string {
	start := strings.Index(s, open)
	if start < 0 {
		return ""
	}
	start += len(open)
	end := strings.Index(s[start:], close)
	if end < 0 {
		return ""
	}
	return s[start : start+end]
}
