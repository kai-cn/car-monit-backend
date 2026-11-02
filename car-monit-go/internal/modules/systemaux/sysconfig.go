// JAVA 对照: ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysConfigController.java:26-129
// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysConfigServiceImpl.java:26-197
// JAVA 对照: ruoyi-system/src/main/resources/mapper/system/SysConfigMapper.xml:36-110
// 类/职责: 参数配置 — /system/config/** 全部 HTTP 入口 + 服务层 + sys_config 存取
// 对应 Go 文件: internal/modules/systemaux/sysconfig.go
//
// DIFF: Java 用 @Cacheable/@CacheEvict 思路（手写 RedisCache 调用）缓存 sys_config:*；
// Go 显式 Get/Set/Delete，语义一一对应。@PostConstruct init() 的启动预热在 Go 侧省略
// （main.go 不可改，且读路径已实现 get-or-load），首次读取同样回填缓存。
// DIFF: Java 的 MyBatis 动态 SQL 用 <if test="x != null">；Go 用指针字段判断“是否传了该字段”，
// 再以 map 形式交给 GORM 动态 Update，保留“未传字段不覆盖”的语义。
package systemaux

import (
	"context"
	"errors"

	"github.com/gin-gonic/gin"
	"gorm.io/gorm"

	"car-monit-go/internal/app"
	"car-monit-go/internal/auth"
	"car-monit-go/internal/middleware"
	"car-monit-go/internal/model"
	"car-monit-go/internal/router"
	"car-monit-go/internal/web"
)

// configBody 对应 @RequestBody SysConfig。
// DIFF: 全字段用指针，保留 JSON null 与空串的区分（MyBatis <if test="x != null">）。
type configBody struct {
	ConfigID    *int64  `json:"configId"`
	ConfigName  *string `json:"configName"`
	ConfigKey   *string `json:"configKey"`
	ConfigValue *string `json:"configValue"`
	ConfigType  *string `json:"configType"`
	CreateBy    *string `json:"createBy"`
	UpdateBy    *string `json:"updateBy"`
	Remark      *string `json:"remark"`
}

// validate 对应 SysConfig 上的 @Validated 约束（GlobalExceptionHandler 取第一条错误文案）。
func (b *configBody) validate() string {
	if isBlank(strVal(b.ConfigName)) {
		return "参数名称不能为空"
	}
	if len([]rune(strVal(b.ConfigName))) > 100 {
		return "参数名称不能超过100个字符"
	}
	if isBlank(strVal(b.ConfigKey)) {
		return "参数键名长度不能为空"
	}
	if len([]rune(strVal(b.ConfigKey))) > 100 {
		return "参数键名长度不能超过100个字符"
	}
	if isBlank(strVal(b.ConfigValue)) {
		return "参数键值不能为空"
	}
	if len([]rune(strVal(b.ConfigValue))) > 500 {
		return "参数键值长度不能超过500个字符"
	}
	return ""
}

type configService struct {
	app *app.App
}

func newConfigService(a *app.App) *configService { return &configService{app: a} }

// cacheKey 对应 SysConfigServiceImpl.getCacheKey：Constants.SYS_CONFIG_KEY + configKey。
func (s *configService) cacheKey(configKey string) string { return auth.SysConfigKey + configKey }

// selectByID 对应 SysConfigServiceImpl.selectConfigById。
func (s *configService) selectByID(ctx context.Context, configID int64) (*model.SysConfig, error) {
	var cfg model.SysConfig
	err := s.app.DB.WithContext(ctx).Where("config_id = ?", configID).Take(&cfg).Error
	if errors.Is(err, gorm.ErrRecordNotFound) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	return &cfg, nil
}

// selectByKey 对应 SysConfigServiceImpl.selectConfigByKey：
// 先读缓存，未命中查库并回填；found=false 表示参数不存在（Java 返回 null）。
func (s *configService) selectByKey(ctx context.Context, configKey string) (value string, found bool, err error) {
	// GetStringJava：Java 写的是 FastJson2 的字符串值（外层带引号），读回要脱引号
	if v, ok := s.app.Cache.GetStringJava(ctx, s.cacheKey(configKey)); ok && v != "" {
		return v, true, nil
	}
	var cfg model.SysConfig
	err = s.app.DB.WithContext(ctx).Where("config_key = ?", configKey).Take(&cfg).Error
	if errors.Is(err, gorm.ErrRecordNotFound) {
		return "", false, nil
	}
	if err != nil {
		return "", false, err
	}
	if err := s.app.Cache.SetJavaString(ctx, s.cacheKey(configKey), model.Str(cfg.ConfigValue), 0); err != nil {
		s.app.Log.Warn("写入参数配置缓存失败", "key", configKey, "err", err)
	}
	return model.Str(cfg.ConfigValue), true, nil
}

// selectList 对应 SysConfigMapper.selectConfigList。
func (s *configService) selectList(ctx context.Context, pd web.PageDomain, q configQuery) ([]model.SysConfig, int64, error) {
	where := " from sys_config where 1 = 1"
	args := make([]any, 0, 6)
	if v := strVal(q.ConfigName); v != "" {
		where += " and config_name like concat('%', ?, '%')"
		args = append(args, v)
	}
	if v := strVal(q.ConfigType); v != "" {
		where += " and config_type = ?"
		args = append(args, v)
	}
	if v := strVal(q.ConfigKey); v != "" {
		where += " and config_key like concat('%', ?, '%')"
		args = append(args, v)
	}
	if v := strVal(q.BeginTime); v != "" {
		where += " and date_format(create_time,'%y%m%d') >= date_format(?,'%y%m%d')"
		args = append(args, v)
	}
	if v := strVal(q.EndTime); v != "" {
		where += " and date_format(create_time,'%y%m%d') <= date_format(?,'%y%m%d')"
		args = append(args, v)
	}
	// JAVA 对照: SysConfigMapper.xml:41-60 —— 该 SQL 本身没有 order by，这里也不给默认排序。
	listSQL := "select config_id, config_name, config_key, config_value, config_type, create_by, create_time, update_by, update_time, remark" + where
	countSQL := "select count(1)" + where
	return queryPage[model.SysConfig](ctx, s.app.DB, pd, countSQL, args, listSQL, "")
}

// insert 对应 insertConfig：写入成功后刷新该键缓存。
func (s *configService) insert(ctx context.Context, b *configBody, username string) (int64, error) {
	row := map[string]any{
		"config_name":  strVal(b.ConfigName),
		"config_key":   strVal(b.ConfigKey),
		"config_value": strVal(b.ConfigValue),
		"create_time":  web.Now(),
	}
	if v := strVal(b.ConfigType); v != "" {
		row["config_type"] = v
	}
	if v := strVal(b.CreateBy); v == "" {
		row["create_by"] = username
	} else {
		row["create_by"] = v
	}
	if v := strVal(b.Remark); v != "" {
		row["remark"] = v
	}
	res := s.app.DB.WithContext(ctx).Table("sys_config").Create(row)
	if res.Error != nil {
		return 0, res.Error
	}
	if res.RowsAffected > 0 {
		if err := s.app.Cache.SetJavaString(ctx, s.cacheKey(strVal(b.ConfigKey)), strVal(b.ConfigValue), 0); err != nil {
			s.app.Log.Warn("刷新参数配置缓存失败", "key", strVal(b.ConfigKey), "err", err)
		}
	}
	return res.RowsAffected, nil
}

// update 对应 updateConfig：成功刷新该键缓存。
func (s *configService) update(ctx context.Context, b *configBody) (int64, error) {
	sets := map[string]any{"update_time": web.Now()}
	if v := strVal(b.ConfigName); v != "" {
		sets["config_name"] = v
	}
	if v := strVal(b.ConfigKey); v != "" {
		sets["config_key"] = v
	}
	if v := strVal(b.ConfigValue); v != "" {
		sets["config_value"] = v
	}
	if v := strVal(b.ConfigType); v != "" {
		sets["config_type"] = v
	}
	if v := strVal(b.UpdateBy); v != "" {
		sets["update_by"] = v
	}
	if b.Remark != nil {
		sets["remark"] = *b.Remark
	}
	res := s.app.DB.WithContext(ctx).Table("sys_config").Where("config_id = ?", numVal(b.ConfigID)).Updates(sets)
	if res.Error != nil {
		return 0, res.Error
	}
	if res.RowsAffected > 0 {
		if err := s.app.Cache.SetJavaString(ctx, s.cacheKey(strVal(b.ConfigKey)), strVal(b.ConfigValue), 0); err != nil {
			s.app.Log.Warn("刷新参数配置缓存失败", "key", strVal(b.ConfigKey), "err", err)
		}
	}
	return res.RowsAffected, nil
}

// deleteByIDs 对应 deleteConfigByIds：内置参数（config_type='Y'）拒绝删除，成功后清空 sys_config:*。
func (s *configService) deleteByIDs(ctx context.Context, ids []int64) (int64, error) {
	for _, id := range ids {
		cfg, err := s.selectByID(ctx, id)
		if err != nil {
			return 0, err
		}
		if cfg != nil && model.Str(cfg.ConfigType) == userYes {
			// JAVA 对照: throw new CustomException(String.format("内置参数【%1$s】不能删除 ", ...)) —— 末尾有空格
			return 0, web.NewServiceError("内置参数【%s】不能删除 ", model.Str(cfg.ConfigKey))
		}
	}
	res := s.app.DB.WithContext(ctx).Exec("delete from sys_config where config_id in ("+inPlaceholders(len(ids))+")", int64Args(ids)...)
	if res.Error != nil {
		return 0, res.Error
	}
	if res.RowsAffected > 0 {
		s.clearCache(ctx)
	}
	return res.RowsAffected, nil
}

// clearCache 对应 clearCache：删除 sys_config:* 全部键（@CacheEvict(allEntries=true)）。
func (s *configService) clearCache(ctx context.Context) {
	keys := s.app.Cache.Keys(ctx, auth.SysConfigKey+"*")
	s.app.Cache.Delete(ctx, keys...)
}

// checkKeyUnique 对应 checkConfigKeyUnique：命中且主键不同则 "1"（不唯一）。
func (s *configService) checkKeyUnique(ctx context.Context, key string, configID int64) (string, error) {
	var cfg model.SysConfig
	err := s.app.DB.WithContext(ctx).Where("config_key = ?", key).Take(&cfg).Error
	if errors.Is(err, gorm.ErrRecordNotFound) {
		return uniqueOld, nil
	}
	if err != nil {
		return "", err
	}
	if cfg.ConfigID != configID {
		return notUniqueOld, nil
	}
	return uniqueOld, nil
}

// configQuery 对应形参 SysConfig config（GET query string 绑定）。
type configQuery struct {
	ConfigName *string
	ConfigType *string
	ConfigKey  *string
	BeginTime  *string
	EndTime    *string
}

func bindConfigQuery(c *gin.Context) configQuery {
	return configQuery{
		ConfigName: queryPtr(c, "configName"),
		ConfigType: queryPtr(c, "configType"),
		ConfigKey:  queryPtr(c, "configKey"),
		BeginTime:  queryPtr(c, "params[beginTime]"),
		EndTime:    queryPtr(c, "params[endTime]"),
	}
}

type configHandler struct {
	app *app.App
	svc *configService
}

func newConfigHandler(a *app.App) *configHandler {
	return &configHandler{app: a, svc: newConfigService(a)}
}

// List 对应 SysConfigController.list（GET /system/config/list，system:config:list）。
func (h *configHandler) List(c *gin.Context) {
	rows, total, err := h.svc.selectList(c.Request.Context(), web.Page(c), bindConfigQuery(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.Table(rows, total))
}

// Export 对应 SysConfigController.export（GET /system/config/export）。
func (h *configHandler) Export(c *gin.Context) {
	rows, _, err := h.svc.selectList(c.Request.Context(), web.PageDomain{}, bindConfigQuery(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	data := make([][]any, 0, len(rows))
	for i := range rows {
		data = append(data, []any{
			rows[i].ConfigID, model.Str(rows[i].ConfigName), model.Str(rows[i].ConfigKey), model.Str(rows[i].ConfigValue),
			yesNo(model.Str(rows[i].ConfigType)),
		})
	}
	headers := []string{"参数主键", "参数名称", "参数键名", "参数键值", "系统内置"}
	filename, err := exportExcel(h.app, "参数数据", headers, data)
	excelSend(c, filename, err)
}

// yesNo 对应 Excel readConverterExp="Y=是,N=否"。
func yesNo(v string) string {
	switch v {
	case "Y":
		return "是"
	case "N":
		return "否"
	}
	return v
}

// GetInfo 对应 SysConfigController.getInfo（GET /system/config/{configId}）。
func (h *configHandler) GetInfo(c *gin.Context) {
	id, err := parseLongArray("configId", c.Param("configId"))
	if err != nil || len(id) == 0 {
		web.JSON(c, web.ErrorResult(orParamTypeError(err)))
		return
	}
	cfg, err := h.svc.selectByID(c.Request.Context(), id[0])
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if cfg == nil {
		web.JSON(c, web.SuccessData(nil))
		return
	}
	web.JSON(c, web.SuccessData(cfg))
}

// GetConfigKey 对应 SysConfigController.getConfigKey（GET /system/config/configKey/{configKey}）。
func (h *configHandler) GetConfigKey(c *gin.Context) {
	value, found, err := h.svc.selectByKey(c.Request.Context(), c.Param("configKey"))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	// JAVA 对照: AjaxResult.success(String) 命中的是 success(msg) 重载 —— 配置值放在 msg 里；
	// 参数不存在时 selectConfigByKey 返回空串，因此 msg 为空串（不是「操作成功」）。
	_ = found
	web.JSON(c, web.SuccessMsg(value))
}

// Add 对应 SysConfigController.add（POST /system/config，@RepeatSubmit）。
func (h *configHandler) Add(c *gin.Context) {
	var body configBody
	if err := c.ShouldBindJSON(&body); err != nil {
		web.JSON(c, web.ErrorMsg("请求参数解析异常"))
		return
	}
	if msg := body.validate(); msg != "" {
		web.JSON(c, web.ErrorMsg(msg))
		return
	}
	unique, err := h.svc.checkKeyUnique(c.Request.Context(), strVal(body.ConfigKey), -1)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if unique == notUniqueOld {
		web.JSON(c, web.ErrorMsg("新增参数'"+strVal(body.ConfigName)+"'失败，参数键名已存在"))
		return
	}
	body.CreateBy = strPtr(auth.CurrentUsername(c))
	rows, err := h.svc.insert(c.Request.Context(), &body, auth.CurrentUsername(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.ToAjax(rows))
}

// Edit 对应 SysConfigController.edit（PUT /system/config）。
func (h *configHandler) Edit(c *gin.Context) {
	var body configBody
	if err := c.ShouldBindJSON(&body); err != nil {
		web.JSON(c, web.ErrorMsg("请求参数解析异常"))
		return
	}
	if msg := body.validate(); msg != "" {
		web.JSON(c, web.ErrorMsg(msg))
		return
	}
	unique, err := h.svc.checkKeyUnique(c.Request.Context(), strVal(body.ConfigKey), numVal(body.ConfigID))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if unique == notUniqueOld {
		web.JSON(c, web.ErrorMsg("修改参数'"+strVal(body.ConfigName)+"'失败，参数键名已存在"))
		return
	}
	body.UpdateBy = strPtr(auth.CurrentUsername(c))
	rows, err := h.svc.update(c.Request.Context(), &body)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.ToAjax(rows))
}

// Remove 对应 SysConfigController.remove（DELETE /system/config/{configIds}）。
func (h *configHandler) Remove(c *gin.Context) {
	ids, err := parseLongArray("configIds", c.Param("configIds"))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	rows, err := h.svc.deleteByIDs(c.Request.Context(), ids)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.ToAjax(rows))
}

// ClearCache 对应 SysConfigController.clearCache（DELETE /system/config/clearCache）。
func (h *configHandler) ClearCache(c *gin.Context) {
	h.svc.clearCache(c.Request.Context())
	web.JSON(c, web.Success())
}

// strPtr 返回字符串指针，便于复用指针 DTO。
func strPtr(s string) *string { return &s }

// orParamTypeError 在解析失败且 err 为空时给出通用的类型不匹配文案。
func orParamTypeError(err error) error {
	if err != nil {
		return err
	}
	return web.NewServiceError("请求参数类型不匹配")
}

// registerConfig 挂载 /system/config/** 路由。
// JAVA 对照: SysConfigController 的 @RequestMapping("/system/config") 与各 @PreAuthorize。
func registerConfig(reg *router.Registry) {
	h := newConfigHandler(reg.App)
	g := reg.Authed.Group("/system/config")
	g.GET("/list", middleware.Perm("system:config:list"), h.List)
	g.GET("/export", middleware.Perm("system:config:export"),
		middleware.OperLog(reg.App, "参数管理", middleware.BusinessExport), h.Export)
	g.GET("/configKey/:configKey", h.GetConfigKey)
	g.GET("/:configId", middleware.Perm("system:config:query"), h.GetInfo)
	g.POST("", middleware.Perm("system:config:add"), middleware.RepeatSubmit(reg.App, 0),
		middleware.OperLog(reg.App, "参数管理", middleware.BusinessInsert), h.Add)
	g.PUT("", middleware.Perm("system:config:edit"),
		middleware.OperLog(reg.App, "参数管理", middleware.BusinessUpdate), h.Edit)
	g.DELETE("/clearCache", middleware.Perm("system:config:remove"),
		middleware.OperLog(reg.App, "参数管理", middleware.BusinessClean), h.ClearCache)
	g.DELETE("/:configIds", middleware.Perm("system:config:remove"),
		middleware.OperLog(reg.App, "参数管理", middleware.BusinessDelete), h.Remove)
}
