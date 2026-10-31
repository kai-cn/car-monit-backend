// JAVA 对照: ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysDictTypeController.java:25-125
// JAVA 对照: ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysDictDataController.java:29-133
// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysDictTypeServiceImpl.java:24-243
// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysDictDataServiceImpl.java:20-140
// JAVA 对照: ruoyi-system/src/main/resources/mapper/system/SysDictTypeMapper.xml:23-105
// JAVA 对照: ruoyi-system/src/main/resources/mapper/system/SysDictDataMapper.xml:28-134
// JAVA 对照: com/ruoyi/common/utils/DictUtils.java:18-165
// 类/职责: 数据字典 — 字典类型/字典数据的 HTTP 入口、服务层与 sys_dict:* 缓存
// 对应 Go 文件: internal/modules/systemaux/sysdict.go
//
// DIFF: Java 的 @Cacheable(DictUtils.getDictCache) / @CacheEvict(allEntries=true) 在 Go 中
// 显式写成 cache.Get / cache.Keys("sys_dict:*") + delete，语义保持一致。
// DIFF: 启动时的 @PostConstruct init() 预热在 Go 侧省略（main.go 不可改），改为首次读取回填。
package systemaux

import (
	"context"
	"errors"
	"strings"

	"github.com/gin-gonic/gin"
	"gorm.io/gorm"

	"car-monit-go/internal/app"
	"car-monit-go/internal/auth"
	"car-monit-go/internal/middleware"
	"car-monit-go/internal/model"
	"car-monit-go/internal/router"
	"car-monit-go/internal/web"
)

// dictTypeBody 对应 @RequestBody SysDictType。
type dictTypeBody struct {
	DictID   *int64  `json:"dictId"`
	DictName *string `json:"dictName"`
	DictType *string `json:"dictType"`
	Status   *string `json:"status"`
	CreateBy *string `json:"createBy"`
	UpdateBy *string `json:"updateBy"`
	Remark   *string `json:"remark"`
}

func (b *dictTypeBody) validate() string {
	if isBlank(strVal(b.DictName)) {
		return "字典名称不能为空"
	}
	if len([]rune(strVal(b.DictName))) > 100 {
		return "字典类型名称长度不能超过100个字符"
	}
	if isBlank(strVal(b.DictType)) {
		return "字典类型不能为空"
	}
	if len([]rune(strVal(b.DictType))) > 100 {
		return "字典类型类型长度不能超过100个字符"
	}
	return ""
}

// dictDataBody 对应 @RequestBody SysDictData。
type dictDataBody struct {
	DictCode  *int64  `json:"dictCode"`
	DictSort  *int64  `json:"dictSort"`
	DictLabel *string `json:"dictLabel"`
	DictValue *string `json:"dictValue"`
	DictType  *string `json:"dictType"`
	CssClass  *string `json:"cssClass"`
	ListClass *string `json:"listClass"`
	IsDefault *string `json:"isDefault"`
	Status    *string `json:"status"`
	CreateBy  *string `json:"createBy"`
	UpdateBy  *string `json:"updateBy"`
	Remark    *string `json:"remark"`
}

func (b *dictDataBody) validate() string {
	if isBlank(strVal(b.DictLabel)) {
		return "字典标签不能为空"
	}
	if len([]rune(strVal(b.DictLabel))) > 100 {
		return "字典标签长度不能超过100个字符"
	}
	if isBlank(strVal(b.DictValue)) {
		return "字典键值不能为空"
	}
	if len([]rune(strVal(b.DictValue))) > 100 {
		return "字典键值长度不能超过100个字符"
	}
	if isBlank(strVal(b.DictType)) {
		return "字典类型不能为空"
	}
	if len([]rune(strVal(b.DictType))) > 100 {
		return "字典类型长度不能超过100个字符"
	}
	if b.CssClass != nil && len([]rune(*b.CssClass)) > 100 {
		return "样式属性长度不能超过100个字符"
	}
	return ""
}

type dictService struct {
	app *app.App
}

func newDictService(a *app.App) *dictService { return &dictService{app: a} }

// dictCacheKey 对应 DictUtils.getCacheKey：Constants.SYS_DICT_KEY + dictType。
func dictCacheKey(dictType string) string { return auth.SysDictKey + dictType }

// clearDictCache 对应 DictUtils.clearDictCache（@CacheEvict(allEntries=true)）。
func (s *dictService) clearDictCache(ctx context.Context) {
	keys := s.app.Cache.Keys(ctx, auth.SysDictKey+"*")
	s.app.Cache.Delete(ctx, keys...)
}

// ---------------------------------------------------------------------------
// 字典类型
// ---------------------------------------------------------------------------

// selectTypeList 对应 SysDictTypeMapper.selectDictTypeList。
func (s *dictService) selectTypeList(ctx context.Context, pd web.PageDomain, q dictTypeQuery) ([]model.SysDictType, int64, error) {
	where := " from sys_dict_type where 1 = 1"
	args := make([]any, 0, 4)
	if v := strVal(q.DictName); v != "" {
		where += " and dict_name like concat('%', ?, '%')"
		args = append(args, v)
	}
	if v := strVal(q.Status); v != "" {
		where += " and status = ?"
		args = append(args, v)
	}
	if v := strVal(q.DictType); v != "" {
		where += " and dict_type like concat('%', ?, '%')"
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
	listSQL := "select dict_id, dict_name, dict_type, status, create_by, create_time, remark" + where
	countSQL := "select count(1)" + where
	return queryPage[model.SysDictType](ctx, s.app.DB, pd, countSQL, args, listSQL, "create_time desc")
}

// selectTypeAll 对应 selectDictTypeAll。
func (s *dictService) selectTypeAll(ctx context.Context) ([]model.SysDictType, error) {
	var rows []model.SysDictType
	err := s.app.DB.WithContext(ctx).Raw(
		"select dict_id, dict_name, dict_type, status, create_by, create_time, remark from sys_dict_type order by create_time desc").
		Scan(&rows).Error
	return rows, err
}

// selectTypeByID 对应 selectDictTypeById。
func (s *dictService) selectTypeByID(ctx context.Context, dictID int64) (*model.SysDictType, error) {
	var row model.SysDictType
	// JAVA 对照: selectDictTypeVo 只查 7 列（不含 update_by/update_time）。
	err := s.app.DB.WithContext(ctx).
		Select("dict_id, dict_name, dict_type, status, create_by, create_time, remark").
		Where("dict_id = ?", dictID).Take(&row).Error
	if errors.Is(err, gorm.ErrRecordNotFound) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	return &row, nil
}

// insertType 对应 insertDictType：成功后清空字典缓存。
func (s *dictService) insertType(ctx context.Context, b *dictTypeBody) (int64, error) {
	row := map[string]any{
		"dict_name":   strVal(b.DictName),
		"dict_type":   strVal(b.DictType),
		"create_time": web.Now(),
	}
	if b.Status != nil {
		row["status"] = *b.Status
	}
	if v := strVal(b.Remark); v != "" {
		row["remark"] = v
	}
	if v := strVal(b.CreateBy); v != "" {
		row["create_by"] = v
	}
	res := s.app.DB.WithContext(ctx).Table("sys_dict_type").Create(row)
	if res.Error != nil {
		return 0, res.Error
	}
	if res.RowsAffected > 0 {
		s.clearDictCache(ctx)
	}
	return res.RowsAffected, nil
}

// updateType 对应 updateDictType(@Transactional)：
// 先把 sys_dict_data.dict_type 从旧值改成新值，再更新类型行，最后清空字典缓存。
func (s *dictService) updateType(ctx context.Context, b *dictTypeBody) (int64, error) {
	sets := map[string]any{"update_time": web.Now()}
	if v := strVal(b.DictName); v != "" {
		sets["dict_name"] = v
	}
	if v := strVal(b.DictType); v != "" {
		sets["dict_type"] = v
	}
	if b.Status != nil {
		sets["status"] = *b.Status
	}
	if b.Remark != nil {
		sets["remark"] = *b.Remark
	}
	if v := strVal(b.UpdateBy); v != "" {
		sets["update_by"] = v
	}
	var row int64
	err := s.app.DB.WithContext(ctx).Transaction(func(tx *gorm.DB) error {
		old, err := s.selectTypeByID(ctx, numVal(b.DictID))
		if err != nil {
			return err
		}
		if old != nil && model.Str(old.DictType) != strVal(b.DictType) {
			if err := tx.WithContext(ctx).Exec(
				"update sys_dict_data set dict_type = ? where dict_type = ?", strVal(b.DictType), model.Str(old.DictType)).Error; err != nil {
				return err
			}
		}
		res := tx.WithContext(ctx).Table("sys_dict_type").Where("dict_id = ?", numVal(b.DictID)).Updates(sets)
		if res.Error != nil {
			return res.Error
		}
		row = res.RowsAffected
		return nil
	})
	if err != nil {
		return 0, err
	}
	if row > 0 {
		s.clearDictCache(ctx)
	}
	return row, nil
}

// deleteTypeByIDs 对应 deleteDictTypeByIds：已分配字典数据的类型拒绝删除。
func (s *dictService) deleteTypeByIDs(ctx context.Context, ids []int64) (int64, error) {
	for _, id := range ids {
		dictType, err := s.selectTypeByID(ctx, id)
		if err != nil {
			return 0, err
		}
		// DIFF: Java 在 selectDictTypeById 返回 null 时会 NPE；Go 侧跳过缺失行（避免 panic）。
		if dictType == nil {
			continue
		}
		var count int64
		if err := s.app.DB.WithContext(ctx).Raw(
			"select count(1) from sys_dict_data where dict_type = ?", dictType.DictType).Scan(&count).Error; err != nil {
			return 0, err
		}
		if count > 0 {
			// JAVA 对照: throw new CustomException(String.format("%1$s已分配,不能删除", dictName))
			return 0, web.NewServiceError("%s已分配,不能删除", model.Str(dictType.DictName))
		}
	}
	res := s.app.DB.WithContext(ctx).Exec("delete from sys_dict_type where dict_id in ("+inPlaceholders(len(ids))+")", int64Args(ids)...)
	if res.Error != nil {
		return 0, res.Error
	}
	if res.RowsAffected > 0 {
		s.clearDictCache(ctx)
	}
	return res.RowsAffected, nil
}

// checkTypeUnique 对应 checkDictTypeUnique。
func (s *dictService) checkTypeUnique(ctx context.Context, dictType string, dictID int64) (string, error) {
	var row model.SysDictType
	err := s.app.DB.WithContext(ctx).Where("dict_type = ?", dictType).Take(&row).Error
	if errors.Is(err, gorm.ErrRecordNotFound) {
		return uniqueOld, nil
	}
	if err != nil {
		return "", err
	}
	if row.DictID != dictID {
		return notUniqueOld, nil
	}
	return uniqueOld, nil
}

// ---------------------------------------------------------------------------
// 字典数据
// ---------------------------------------------------------------------------

// selectDataList 对应 SysDictDataMapper.selectDictDataList。
func (s *dictService) selectDataList(ctx context.Context, pd web.PageDomain, q dictDataQuery) ([]model.SysDictData, int64, error) {
	where := " from sys_dict_data where 1 = 1"
	args := make([]any, 0, 3)
	if v := strVal(q.DictType); v != "" {
		where += " and dict_type = ?"
		args = append(args, v)
	}
	if v := strVal(q.DictLabel); v != "" {
		where += " and dict_label like concat('%', ?, '%')"
		args = append(args, v)
	}
	if v := strVal(q.Status); v != "" {
		where += " and status = ?"
		args = append(args, v)
	}
	listSQL := "select dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, remark" + where
	countSQL := "select count(1)" + where
	return queryPage[model.SysDictData](ctx, s.app.DB, pd, countSQL, args, listSQL, "dict_sort asc")
}

// selectDataByID 对应 selectDictDataById。
func (s *dictService) selectDataByID(ctx context.Context, dictCode int64) (*model.SysDictData, error) {
	var row model.SysDictData
	// JAVA 对照: selectDictDataVo 只查 12 列（不含 update_by/update_time）。
	err := s.app.DB.WithContext(ctx).
		Select("dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, remark").
		Where("dict_code = ?", dictCode).Take(&row).Error
	if errors.Is(err, gorm.ErrRecordNotFound) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	return &row, nil
}

// selectDataByType 对应 SysDictTypeServiceImpl.selectDictDataByType：
// @Cacheable —— 先查缓存，未命中查库（status='0'），非空回填，仍为空返回 nil。
func (s *dictService) selectDataByType(ctx context.Context, dictType string) ([]model.SysDictData, error) {
	key := dictCacheKey(dictType)
	var cached []model.SysDictData
	if s.app.Cache.Get(ctx, key, &cached) && len(cached) > 0 {
		return cached, nil
	}
	var rows []model.SysDictData
	if err := s.app.DB.WithContext(ctx).Raw(
		"select dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, remark "+
			"from sys_dict_data where status = '0' and dict_type = ? order by dict_sort asc", dictType).Scan(&rows).Error; err != nil {
		return nil, err
	}
	if len(rows) > 0 {
		if err := s.app.Cache.Set(ctx, key, rows, 0); err != nil {
			s.app.Log.Warn("写入字典缓存失败", "dictType", dictType, "err", err)
		}
		return rows, nil
	}
	return nil, nil
}

// selectDataByTypeMore 对应 selectDictDataByTypeMore（逗号分隔的多类型，同样走缓存）。
//
// DIFF: Java 的 `dictType.substring(0, dictType.length())` 是空操作（结尾逗号并未去掉），
// 这里同样保留原字符串作为缓存键；拆分时过滤空片段，等价于 String#split 丢弃尾部空串。
func (s *dictService) selectDataByTypeMore(ctx context.Context, dictType string) ([]model.SysDictData, error) {
	if dictType == "" {
		dictType = "-dadadadas"
	}
	if dictType == "" {
		dictType = "-dadadadas"
	}
	key := dictCacheKey(dictType)
	var cached []model.SysDictData
	if s.app.Cache.Get(ctx, key, &cached) && len(cached) > 0 {
		return cached, nil
	}
	types := make([]string, 0, 4)
	for _, part := range strings.Split(dictType, ",") {
		if part != "" {
			types = append(types, part)
		}
	}
	if len(types) == 0 {
		return nil, nil
	}
	args := make([]any, 0, len(types))
	for _, t := range types {
		args = append(args, t)
	}
	var rows []model.SysDictData
	sql := "select dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, status, create_by, create_time, remark " +
		"from sys_dict_data where status = '0' and dict_type in (" + inPlaceholders(len(types)) + ") order by dict_type, dict_sort asc"
	if err := s.app.DB.WithContext(ctx).Raw(sql, args...).Scan(&rows).Error; err != nil {
		return nil, err
	}
	if len(rows) > 0 {
		if err := s.app.Cache.Set(ctx, key, rows, 0); err != nil {
			s.app.Log.Warn("写入字典缓存失败", "dictType", dictType, "err", err)
		}
		return rows, nil
	}
	return nil, nil
}

// insertData 对应 insertDictData：成功后清空字典缓存。
func (s *dictService) insertData(ctx context.Context, b *dictDataBody) (int64, error) {
	row := map[string]any{
		"dict_label":  strVal(b.DictLabel),
		"dict_value":  strVal(b.DictValue),
		"dict_type":   strVal(b.DictType),
		"create_time": web.Now(),
	}
	if b.DictSort != nil {
		row["dict_sort"] = *b.DictSort
	}
	if v := strVal(b.CssClass); v != "" {
		row["css_class"] = v
	}
	if v := strVal(b.ListClass); v != "" {
		row["list_class"] = v
	}
	if v := strVal(b.IsDefault); v != "" {
		row["is_default"] = v
	}
	if b.Status != nil {
		row["status"] = *b.Status
	}
	if v := strVal(b.Remark); v != "" {
		row["remark"] = v
	}
	if v := strVal(b.CreateBy); v != "" {
		row["create_by"] = v
	}
	res := s.app.DB.WithContext(ctx).Table("sys_dict_data").Create(row)
	if res.Error != nil {
		return 0, res.Error
	}
	if res.RowsAffected > 0 {
		s.clearDictCache(ctx)
	}
	return res.RowsAffected, nil
}

// updateData 对应 updateDictData。
func (s *dictService) updateData(ctx context.Context, b *dictDataBody) (int64, error) {
	sets := map[string]any{"update_time": web.Now()}
	if b.DictSort != nil {
		sets["dict_sort"] = *b.DictSort
	}
	if v := strVal(b.DictLabel); v != "" {
		sets["dict_label"] = v
	}
	if v := strVal(b.DictValue); v != "" {
		sets["dict_value"] = v
	}
	if v := strVal(b.DictType); v != "" {
		sets["dict_type"] = v
	}
	if b.CssClass != nil {
		sets["css_class"] = *b.CssClass
	}
	if b.ListClass != nil {
		sets["list_class"] = *b.ListClass
	}
	if v := strVal(b.IsDefault); v != "" {
		sets["is_default"] = v
	}
	if b.Status != nil {
		sets["status"] = *b.Status
	}
	if b.Remark != nil {
		sets["remark"] = *b.Remark
	}
	if v := strVal(b.UpdateBy); v != "" {
		sets["update_by"] = v
	}
	res := s.app.DB.WithContext(ctx).Table("sys_dict_data").Where("dict_code = ?", numVal(b.DictCode)).Updates(sets)
	if res.Error != nil {
		return 0, res.Error
	}
	if res.RowsAffected > 0 {
		s.clearDictCache(ctx)
	}
	return res.RowsAffected, nil
}

// deleteDataByIDs 对应 deleteDictDataByIds。
func (s *dictService) deleteDataByIDs(ctx context.Context, ids []int64) (int64, error) {
	res := s.app.DB.WithContext(ctx).Exec("delete from sys_dict_data where dict_code in ("+inPlaceholders(len(ids))+")", int64Args(ids)...)
	if res.Error != nil {
		return 0, res.Error
	}
	if res.RowsAffected > 0 {
		s.clearDictCache(ctx)
	}
	return res.RowsAffected, nil
}

// ---------------------------------------------------------------------------
// 查询条件
// ---------------------------------------------------------------------------

type dictTypeQuery struct {
	DictName  *string
	DictType  *string
	Status    *string
	BeginTime *string
	EndTime   *string
}

func bindDictTypeQuery(c *gin.Context) dictTypeQuery {
	return dictTypeQuery{
		DictName:  queryPtr(c, "dictName"),
		DictType:  queryPtr(c, "dictType"),
		Status:    queryPtr(c, "status"),
		BeginTime: queryPtr(c, "params[beginTime]"),
		EndTime:   queryPtr(c, "params[endTime]"),
	}
}

type dictDataQuery struct {
	DictType  *string
	DictLabel *string
	Status    *string
}

func bindDictDataQuery(c *gin.Context) dictDataQuery {
	return dictDataQuery{
		DictType:  queryPtr(c, "dictType"),
		DictLabel: queryPtr(c, "dictLabel"),
		Status:    queryPtr(c, "status"),
	}
}

// ---------------------------------------------------------------------------
// HTTP 入口
// ---------------------------------------------------------------------------

type dictHandler struct {
	app *app.App
	svc *dictService
}

func newDictHandler(a *app.App) *dictHandler { return &dictHandler{app: a, svc: newDictService(a)} }

// TypeList 对应 SysDictTypeController.list（GET /system/dict/type/list）。
func (h *dictHandler) TypeList(c *gin.Context) {
	rows, total, err := h.svc.selectTypeList(c.Request.Context(), web.Page(c), bindDictTypeQuery(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.Table(rows, total))
}

// TypeExport 对应 SysDictTypeController.export。
func (h *dictHandler) TypeExport(c *gin.Context) {
	rows, _, err := h.svc.selectTypeList(c.Request.Context(), web.PageDomain{}, bindDictTypeQuery(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	data := make([][]any, 0, len(rows))
	for i := range rows {
		data = append(data, []any{rows[i].DictID, model.Str(rows[i].DictName), model.Str(rows[i].DictType), normalDisabled(model.Str(rows[i].Status))})
	}
	filename, err := exportExcel(h.app, "字典类型", []string{"字典主键", "字典名称", "字典类型", "状态"}, data)
	excelSend(c, filename, err)
}

// normalDisabled 对应 Excel readConverterExp="0=正常,1=停用"。
func normalDisabled(v string) string {
	switch v {
	case "0":
		return "正常"
	case "1":
		return "停用"
	}
	return v
}

// TypeGetInfo 对应 SysDictTypeController.getInfo。
func (h *dictHandler) TypeGetInfo(c *gin.Context) {
	ids, err := parseLongArray("dictId", c.Param("dictId"))
	if err != nil || len(ids) == 0 {
		web.JSON(c, web.ErrorResult(orParamTypeError(err)))
		return
	}
	row, err := h.svc.selectTypeByID(c.Request.Context(), ids[0])
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if row == nil {
		web.JSON(c, web.SuccessData(nil))
		return
	}
	web.JSON(c, web.SuccessData(row))
}

// TypeAdd 对应 SysDictTypeController.add。
func (h *dictHandler) TypeAdd(c *gin.Context) {
	var body dictTypeBody
	if err := c.ShouldBindJSON(&body); err != nil {
		web.JSON(c, web.ErrorMsg("请求参数解析异常"))
		return
	}
	if msg := body.validate(); msg != "" {
		web.JSON(c, web.ErrorMsg(msg))
		return
	}
	unique, err := h.svc.checkTypeUnique(c.Request.Context(), strVal(body.DictType), -1)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if unique == notUniqueOld {
		web.JSON(c, web.ErrorMsg("新增字典'"+strVal(body.DictName)+"'失败，字典类型已存在"))
		return
	}
	body.CreateBy = strPtr(auth.CurrentUsername(c))
	rows, err := h.svc.insertType(c.Request.Context(), &body)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.ToAjax(rows))
}

// TypeEdit 对应 SysDictTypeController.edit。
func (h *dictHandler) TypeEdit(c *gin.Context) {
	var body dictTypeBody
	if err := c.ShouldBindJSON(&body); err != nil {
		web.JSON(c, web.ErrorMsg("请求参数解析异常"))
		return
	}
	if msg := body.validate(); msg != "" {
		web.JSON(c, web.ErrorMsg(msg))
		return
	}
	unique, err := h.svc.checkTypeUnique(c.Request.Context(), strVal(body.DictType), numVal(body.DictID))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if unique == notUniqueOld {
		web.JSON(c, web.ErrorMsg("修改字典'"+strVal(body.DictName)+"'失败，字典类型已存在"))
		return
	}
	body.UpdateBy = strPtr(auth.CurrentUsername(c))
	rows, err := h.svc.updateType(c.Request.Context(), &body)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.ToAjax(rows))
}

// TypeRemove 对应 SysDictTypeController.remove。
func (h *dictHandler) TypeRemove(c *gin.Context) {
	ids, err := parseLongArray("dictIds", c.Param("dictIds"))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	rows, err := h.svc.deleteTypeByIDs(c.Request.Context(), ids)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.ToAjax(rows))
}

// TypeClearCache 对应 SysDictTypeController.clearCache。
func (h *dictHandler) TypeClearCache(c *gin.Context) {
	h.svc.clearDictCache(c.Request.Context())
	web.JSON(c, web.Success())
}

// TypeOptionSelect 对应 SysDictTypeController.optionselect（无 @PreAuthorize）。
func (h *dictHandler) TypeOptionSelect(c *gin.Context) {
	rows, err := h.svc.selectTypeAll(c.Request.Context())
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.SuccessData(rows))
}

// DataList 对应 SysDictDataController.list。
func (h *dictHandler) DataList(c *gin.Context) {
	rows, total, err := h.svc.selectDataList(c.Request.Context(), web.Page(c), bindDictDataQuery(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.Table(rows, total))
}

// DataExport 对应 SysDictDataController.export。
func (h *dictHandler) DataExport(c *gin.Context) {
	rows, _, err := h.svc.selectDataList(c.Request.Context(), web.PageDomain{}, bindDictDataQuery(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	data := make([][]any, 0, len(rows))
	for i := range rows {
		data = append(data, []any{
			rows[i].DictCode, rows[i].DictSort, model.Str(rows[i].DictLabel), model.Str(rows[i].DictValue),
			model.Str(rows[i].DictType), yesNo(model.Str(rows[i].IsDefault)), normalDisabled(model.Str(rows[i].Status)),
		})
	}
	headers := []string{"字典编码", "字典排序", "字典标签", "字典键值", "字典类型", "是否默认", "状态"}
	filename, err := exportExcel(h.app, "字典数据", headers, data)
	excelSend(c, filename, err)
}

// DataGetInfo 对应 SysDictDataController.getInfo。
func (h *dictHandler) DataGetInfo(c *gin.Context) {
	ids, err := parseLongArray("dictCode", c.Param("dictCode"))
	if err != nil || len(ids) == 0 {
		web.JSON(c, web.ErrorResult(orParamTypeError(err)))
		return
	}
	row, err := h.svc.selectDataByID(c.Request.Context(), ids[0])
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if row == nil {
		web.JSON(c, web.SuccessData(nil))
		return
	}
	web.JSON(c, web.SuccessData(row))
}

// DataByType 对应 SysDictDataController.dictType（GET /system/dict/data/type/{dictType}）：
// 查不到时返回空数组而不是 null。
func (h *dictHandler) DataByType(c *gin.Context) {
	rows, err := h.svc.selectDataByType(c.Request.Context(), c.Param("dictType"))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if rows == nil {
		rows = []model.SysDictData{}
	}
	web.JSON(c, web.SuccessData(rows))
}

// DataByTypeMore 对应 SysDictDataController.dictTypeMore：按 dictType 分组返回。
func (h *dictHandler) DataByTypeMore(c *gin.Context) {
	rows, err := h.svc.selectDataByTypeMore(c.Request.Context(), c.Param("dictType"))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if rows == nil {
		rows = []model.SysDictData{}
	}
	grouped := make(map[string][]model.SysDictData)
	for _, row := range rows {
		grouped[model.Str(row.DictType)] = append(grouped[model.Str(row.DictType)], row)
	}
	web.JSON(c, web.SuccessData(grouped))
}

// DataAdd 对应 SysDictDataController.add。
func (h *dictHandler) DataAdd(c *gin.Context) {
	var body dictDataBody
	if err := c.ShouldBindJSON(&body); err != nil {
		web.JSON(c, web.ErrorMsg("请求参数解析异常"))
		return
	}
	if msg := body.validate(); msg != "" {
		web.JSON(c, web.ErrorMsg(msg))
		return
	}
	body.CreateBy = strPtr(auth.CurrentUsername(c))
	rows, err := h.svc.insertData(c.Request.Context(), &body)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.ToAjax(rows))
}

// DataEdit 对应 SysDictDataController.edit。
func (h *dictHandler) DataEdit(c *gin.Context) {
	var body dictDataBody
	if err := c.ShouldBindJSON(&body); err != nil {
		web.JSON(c, web.ErrorMsg("请求参数解析异常"))
		return
	}
	if msg := body.validate(); msg != "" {
		web.JSON(c, web.ErrorMsg(msg))
		return
	}
	body.UpdateBy = strPtr(auth.CurrentUsername(c))
	rows, err := h.svc.updateData(c.Request.Context(), &body)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.ToAjax(rows))
}

// DataRemove 对应 SysDictDataController.remove。
func (h *dictHandler) DataRemove(c *gin.Context) {
	ids, err := parseLongArray("dictCodes", c.Param("dictCodes"))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	rows, err := h.svc.deleteDataByIDs(c.Request.Context(), ids)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.ToAjax(rows))
}

// registerDict 挂载 /system/dict/type/** 与 /system/dict/data/**。
func registerDict(reg *router.Registry) {
	h := newDictHandler(reg.App)

	t := reg.Authed.Group("/system/dict/type")
	t.GET("/list", middleware.Perm("system:dict:list"), h.TypeList)
	t.GET("/export", middleware.Perm("system:dict:export"),
		middleware.OperLog(reg.App, "字典类型", middleware.BusinessExport), h.TypeExport)
	t.GET("/optionselect", h.TypeOptionSelect)
	t.GET("/:dictId", middleware.Perm("system:dict:query"), h.TypeGetInfo)
	t.POST("", middleware.Perm("system:dict:add"),
		middleware.OperLog(reg.App, "字典类型", middleware.BusinessInsert), h.TypeAdd)
	t.PUT("", middleware.Perm("system:dict:edit"),
		middleware.OperLog(reg.App, "字典类型", middleware.BusinessUpdate), h.TypeEdit)
	t.DELETE("/clearCache", middleware.Perm("system:dict:remove"),
		middleware.OperLog(reg.App, "字典类型", middleware.BusinessClean), h.TypeClearCache)
	t.DELETE("/:dictIds", middleware.Perm("system:dict:remove"),
		middleware.OperLog(reg.App, "字典类型", middleware.BusinessDelete), h.TypeRemove)

	d := reg.Authed.Group("/system/dict/data")
	d.GET("/list", middleware.Perm("system:dict:list"), h.DataList)
	d.GET("/export", middleware.Perm("system:dict:export"),
		middleware.OperLog(reg.App, "字典数据", middleware.BusinessExport), h.DataExport)
	d.GET("/type/:dictType", h.DataByType)
	d.GET("/typemore/:dictType", h.DataByTypeMore)
	d.GET("/:dictCode", middleware.Perm("system:dict:query"), h.DataGetInfo)
	d.POST("", middleware.Perm("system:dict:add"),
		middleware.OperLog(reg.App, "字典数据", middleware.BusinessInsert), h.DataAdd)
	d.PUT("", middleware.Perm("system:dict:edit"),
		middleware.OperLog(reg.App, "字典数据", middleware.BusinessUpdate), h.DataEdit)
	d.DELETE("/:dictCodes", middleware.Perm("system:dict:remove"),
		middleware.OperLog(reg.App, "字典类型", middleware.BusinessDelete), h.DataRemove)
}
