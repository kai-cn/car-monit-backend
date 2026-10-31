// JAVA 对照: ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysFileController.java:26-238
// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysFileServiceImpl.java:1-900
// JAVA 对照: ruoyi-system/src/main/resources/mapper/system/SysFileMapper.xml:1-142
// JAVA 对照: ruoyi-admin/src/main/java/com/ruoyi/web/util/Base64DecodeMultipartFile.java
// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/system/service/forest/FileApi.java
// 类/职责: 文件管理 — 查询/上传（multipart、url、base64、供应商、PDF）/下载/编辑/删除/CA 更新
// 对应 Go 文件: internal/modules/systemaux/file.go
//
// DIFF: Java 的 MultipartFile 是接口，上传链路的 fileLog/putObject 只认它；Go 用 fileSource
// 把 multipart、url 下载字节、base64 解码字节统一成“文件名 + 大小 + 可重复打开的流”。
// DIFF: Gin 同一路径位置只允许一个通配符名，`/{bucket}/{fileName}` 注册成
// `/:ids/:fileName`（`:ids` 在 handler 里当 bucket 用），`/view/**` 保持独立。
// DIFF: 没有控制器的 service 重载（uploadFile(MultipartFile)、uploadFilesUser、
// getFileToUrl、getFile(OutputStream)、getFileUrl、uploadBase64Picture、uploadFile(InputStream)）
// 不迁移，仅保留本文件实际可达的链路。
package systemaux

import (
	"bytes"
	"context"
	"encoding/base64"
	"errors"
	"fmt"
	"io"
	"mime/multipart"
	"net/http"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/gin-gonic/gin"
	"gorm.io/gorm"

	"car-monit-go/internal/app"
	"car-monit-go/internal/auth"
	"car-monit-go/internal/middleware"
	"car-monit-go/internal/model"
	"car-monit-go/internal/router"
	"car-monit-go/internal/web"
)

// JAVA 对照: SysFileServiceImpl#fileLog 白名单（FileUtil.extName 后 indexOf 的判断集合）
var fileSupportedExtensions = []string{
	"doc", "docx", "pdf", "xls", "xlsx", "pptx", "txt", "zip", "rar",
	"jpg", "jpeg", "png", "gif", "mp3", "mp4", "flv", "3gp",
}

// JAVA 对照: SysFileServiceImpl#fileLogId 白名单：比上面多一条带点的 ".ppt"（永不命中，死代码）。
var fileSupportedExtensionsForID = []string{
	"doc", "docx", "pdf", "xls", "txt", "xlsx", ".ppt", "pptx", "zip", "rar",
	"jpg", "jpeg", "png", "gif", "mp3", "mp4", "flv", "3gp",
}

// JAVA 对照: String.format("/system/file/%s/%s", bucketName, fileName)
const fileURLFormat = "/system/file/%s/%s"

const (
	// JAVA 对照: SysFileController#upload 的 15M 图片上限
	wechatMaxFileSize = 1024 * 1024 * 15
	// JAVA 对照: SysFileController#getInfo 的占位 id
	emptyIDsPlaceholder = "-111111"
	// JAVA 对照: SysFileController#getNewCa 的失败文案
	caNotFoundMessage = "未找到CA驱动程序"
)

const sysFileSelectVo = `t.id, t.file_name, t.bucket_name, t.original, t.type, t.file_size, t.buss_type, t.buss_name,
       t.create_user, t.create_time, t.update_user, t.update_time, t.del_flag, t.tenant_id`

// ---------------------------------------------------------------------------
// 上传源抽象
// ---------------------------------------------------------------------------

type fileSource struct {
	Filename string
	Size     int64
	open     func() (io.ReadCloser, error)
}

func fileSourceFromHeader(fh *multipart.FileHeader) fileSource {
	return fileSource{
		Filename: fh.Filename,
		Size:     fh.Size,
		open:     func() (io.ReadCloser, error) { return fh.Open() },
	}
}

func fileSourceFromBytes(name string, data []byte) fileSource {
	return fileSource{
		Filename: name,
		Size:     int64(len(data)),
		open:     func() (io.ReadCloser, error) { return io.NopCloser(bytes.NewReader(data)), nil },
	}
}

// bytes 对应 Java 每次 getInputStream() 都拿到一个新流：这里每次都重新打开。
func (s fileSource) bytes() ([]byte, error) {
	rc, err := s.open()
	if err != nil {
		return nil, err
	}
	defer func() { _ = rc.Close() }()
	return io.ReadAll(rc)
}

// ---------------------------------------------------------------------------
// 查询条件 / 请求体
// ---------------------------------------------------------------------------

// JAVA 对照: Spring 把 GET 参数绑定到 SysFile（Long/String/Date 包装类型可为 null）。
type sysFileQuery struct {
	ID         *int64
	FileName   *string
	BucketName *string
	Original   *string
	Type       *string
	FileSize   *int64
	BussType   *string
	BussName   *string
	CreateUser *string
	UpdateUser *string
	TenantID   *int64
}

func bindSysFileQuery(c *gin.Context) sysFileQuery {
	return sysFileQuery{
		ID:         queryInt64Ptr(c, "id"),
		FileName:   queryPtr(c, "fileName"),
		BucketName: queryPtr(c, "bucketName"),
		Original:   queryPtr(c, "original"),
		Type:       queryPtr(c, "type"),
		FileSize:   queryInt64Ptr(c, "fileSize"),
		BussType:   queryPtr(c, "bussType"),
		BussName:   queryPtr(c, "bussName"),
		CreateUser: queryPtr(c, "createUser"),
		UpdateUser: queryPtr(c, "updateUser"),
		TenantID:   queryInt64Ptr(c, "tenantId"),
	}
}

// sysFileBody 对应 @RequestBody SysFile：可空字段保留指针，才能复刻 MyBatis 的 != null 分支。
type sysFileBody struct {
	ID         *int64        `json:"id"`
	FileName   *string       `json:"fileName"`
	BucketName *string       `json:"bucketName"`
	Original   *string       `json:"original"`
	Type       *string       `json:"type"`
	FileSize   *int64        `json:"fileSize"`
	BussType   *string       `json:"bussType"`
	BussName   *string       `json:"bussName"`
	CreateUser *string       `json:"createUser"`
	CreateTime *web.DateTime `json:"createTime"`
	UpdateUser *string       `json:"updateUser"`
	UpdateTime *web.DateTime `json:"updateTime"`
	DelFlag    *string       `json:"delFlag"`
	TenantID   *int64        `json:"tenantId"`
	Files      *string       `json:"files"`
}

// JAVA 对照: UploadRo / UploadByUrlRo
type uploadByURLRo struct {
	FileName *string `json:"fileName"`
	URL      *string `json:"url"`
}

type uploadRo struct {
	List []uploadByURLRo `json:"list"`
}

type fileColumn struct {
	name  string
	value any
}

// ---------------------------------------------------------------------------
// 服务层
// ---------------------------------------------------------------------------

type fileService struct {
	app  *app.App
	oss  *ossStorage
	http *http.Client
}

func newFileService(a *app.App) *fileService {
	timeout := time.Duration(a.Cfg.Forest.Timeout) * time.Millisecond
	if timeout <= 0 {
		timeout = 60 * time.Second
	}
	return &fileService{
		app:  a,
		oss:  newOssStorage(a.Cfg.Oss),
		http: &http.Client{Timeout: timeout},
	}
}

func (s *fileService) bucket() string { return s.app.Cfg.Oss.BucketName }

// newResultMap 对应 Java 的 new HashMap<>(4) + bucketName/fileName/url 三个键。
func (s *fileService) newResultMap(fileName string) *web.JavaMap {
	m := web.NewJavaMap()
	m.Put("bucketName", s.bucket())
	m.Put("fileName", fileName)
	m.Put("url", fmt.Sprintf(fileURLFormat, s.bucket(), fileName))
	return m
}

// JAVA 对照: SysFileMapper.selectSysFileList
func (s *fileService) selectSysFileList(ctx context.Context, pd web.PageDomain, q sysFileQuery) ([]model.SysFile, int64, error) {
	where := " where t.del_flag = '0'"
	args := make([]any, 0, 11)
	if q.ID != nil {
		where += " and t.id = ?"
		args = append(args, *q.ID)
	}
	if v := strVal(q.FileName); v != "" {
		where += " and t.file_name like concat('%', ?, '%')"
		args = append(args, v)
	}
	if v := strVal(q.BucketName); v != "" {
		where += " and t.bucket_name like concat('%', ?, '%')"
		args = append(args, v)
	}
	if v := strVal(q.Original); v != "" {
		where += " and t.original = ?"
		args = append(args, v)
	}
	if v := strVal(q.Type); v != "" {
		where += " and t.type = ?"
		args = append(args, v)
	}
	if q.FileSize != nil {
		where += " and t.file_size = ?"
		args = append(args, *q.FileSize)
	}
	if v := strVal(q.BussType); v != "" {
		where += " and t.buss_type = ?"
		args = append(args, v)
	}
	if v := strVal(q.BussName); v != "" {
		where += " and t.buss_name like concat('%', ?, '%')"
		args = append(args, v)
	}
	if v := strVal(q.CreateUser); v != "" {
		where += " and t.create_user = ?"
		args = append(args, v)
	}
	if v := strVal(q.UpdateUser); v != "" {
		where += " and t.update_user = ?"
		args = append(args, v)
	}
	if q.TenantID != nil {
		where += " and t.tenant_id = ?"
		args = append(args, *q.TenantID)
	}
	return queryPage[model.SysFile](ctx, s.app.DB, pd,
		"select count(1) from sys_file t"+where, args,
		"select "+sysFileSelectVo+" from sys_file t"+where, "t.create_time desc,t.id")
}

// JAVA 对照: SysFileMapper.selectSysFileById（返回 null 表示查不到）
func (s *fileService) selectSysFileByID(ctx context.Context, id int64) (*model.SysFile, error) {
	var row model.SysFile
	err := s.app.DB.WithContext(ctx).
		Raw("select "+sysFileSelectVo+" from sys_file t where t.id = ?", id).Take(&row).Error
	if err == nil {
		return &row, nil
	}
	if errors.Is(err, gorm.ErrRecordNotFound) {
		return nil, nil
	}
	return nil, err
}

// JAVA 对照: SysFileMapper.selectSysFileByIds：ids.split(",") 不 trim、不过滤空串。
func (s *fileService) selectSysFileByIDs(ctx context.Context, ids string) ([]model.SysFile, error) {
	parts := strings.Split(ids, ",")
	sqlText := "select " + sysFileSelectVo + ", t2.nick_name create_user_name " +
		"from sys_file t left join sys_user t2 on t.create_user = t2.user_id and t2.del_flag = '0' " +
		"where t.id in (" + inPlaceholders(len(parts)) + ") order by t.id"
	args := make([]any, 0, len(parts))
	for _, p := range parts {
		args = append(args, p)
	}
	var rows []model.SysFile
	if err := s.app.DB.WithContext(ctx).Raw(sqlText, args...).Scan(&rows).Error; err != nil {
		return nil, err
	}
	return nonNil(rows), nil
}

// insertFileRow 对应 insertSysFile 的动态列。
func (s *fileService) insertFileRow(ctx context.Context, cols []fileColumn) error {
	names := make([]string, len(cols))
	marks := make([]string, len(cols))
	args := make([]any, len(cols))
	for i, c := range cols {
		names[i] = c.name
		marks[i] = "?"
		args[i] = c.value
	}
	err := s.app.DB.WithContext(ctx).Exec(
		"insert into sys_file ("+strings.Join(names, ", ")+") values ("+strings.Join(marks, ", ")+")",
		args...).Error
	return err
}

// JAVA 对照: SysFileServiceImpl.saveSysFile
func (s *fileService) saveSysFile(ctx context.Context, b *sysFileBody, userID int64) (*web.AjaxResult, error) {
	user := strconv.FormatInt(userID, 10)
	now := web.Now()

	if b.ID != nil {
		sets := make([]string, 0, 15)
		args := make([]any, 0, 16)
		if b.FileName != nil {
			sets = append(sets, "file_name = ?")
			args = append(args, *b.FileName)
		}
		if b.BucketName != nil {
			sets = append(sets, "bucket_name = ?")
			args = append(args, *b.BucketName)
		}
		if b.Original != nil {
			sets = append(sets, "original = ?")
			args = append(args, *b.Original)
		}
		if b.Type != nil {
			sets = append(sets, "type = ?")
			args = append(args, *b.Type)
		}
		if b.FileSize != nil {
			sets = append(sets, "file_size = ?")
			args = append(args, *b.FileSize)
		}
		if b.BussType != nil {
			sets = append(sets, "buss_type = ?")
			args = append(args, *b.BussType)
		}
		if b.BussName != nil {
			sets = append(sets, "buss_name = ?")
			args = append(args, *b.BussName)
		}
		if b.CreateUser != nil {
			sets = append(sets, "create_user = ?")
			args = append(args, *b.CreateUser)
		}
		if b.CreateTime != nil {
			sets = append(sets, "create_time = ?")
			args = append(args, b.CreateTime)
		}
		if b.UpdateUser != nil {
			sets = append(sets, "update_user = ?")
			args = append(args, *b.UpdateUser)
		}
		if b.UpdateTime != nil {
			sets = append(sets, "update_time = ?")
			args = append(args, b.UpdateTime)
		}
		if b.DelFlag != nil {
			sets = append(sets, "del_flag = ?")
			args = append(args, *b.DelFlag)
		}
		if b.TenantID != nil {
			sets = append(sets, "tenant_id = ?")
			args = append(args, *b.TenantID)
		}
		// Java 强制覆盖更新时间
		sets = append(sets, "update_user = ?", "update_time = ?")
		args = append(args, user, now)
		args = append(args, *b.ID)
		if err := s.app.DB.WithContext(ctx).Exec(
			"update sys_file set "+strings.Join(sets, ", ")+" where id = ?", args...).Error; err != nil {
			return nil, err
		}
		return web.SuccessFull("操作成功！", *b.ID), nil
	}

	id := idWorker.Next()
	cols := make([]fileColumn, 0, 14)
	cols = append(cols, fileColumn{"id", id})
	if b.FileName != nil {
		cols = append(cols, fileColumn{"file_name", *b.FileName})
	}
	if b.BucketName != nil {
		cols = append(cols, fileColumn{"bucket_name", *b.BucketName})
	}
	if b.Original != nil {
		cols = append(cols, fileColumn{"original", *b.Original})
	}
	if b.Type != nil {
		cols = append(cols, fileColumn{"type", *b.Type})
	}
	if b.FileSize != nil {
		cols = append(cols, fileColumn{"file_size", *b.FileSize})
	}
	if b.BussType != nil {
		cols = append(cols, fileColumn{"buss_type", *b.BussType})
	}
	if b.BussName != nil {
		cols = append(cols, fileColumn{"buss_name", *b.BussName})
	}
	cols = append(cols,
		fileColumn{"create_user", user},
		fileColumn{"create_time", now},
		fileColumn{"update_user", user},
		fileColumn{"update_time", now},
		fileColumn{"del_flag", "0"},
	)
	if b.TenantID != nil {
		cols = append(cols, fileColumn{"tenant_id", *b.TenantID})
	}
	if err := s.insertFileRow(ctx, cols); err != nil {
		return nil, err
	}
	return web.SuccessFull("操作成功！", id), nil
}

// deleteFileRow 软删除。
func (s *fileService) softDelete(ctx context.Context, ids []int64) (int64, error) {
	res := s.app.DB.WithContext(ctx).Exec(
		"update sys_file set del_flag = '1' where id in ("+inPlaceholders(len(ids))+")",
		int64Args(ids)...)
	return res.RowsAffected, res.Error
}

// JAVA 对照: SysFileServiceImpl.deleteSysFileByIds
func (s *fileService) deleteSysFileByIDs(ctx context.Context, ids []int64) *web.AjaxResult {
	for _, id := range ids {
		file, err := s.selectSysFileByID(ctx, id)
		if err != nil {
			return web.ErrorMsg(err.Error())
		}
		if file == nil {
			// Java: file.getFileName() -> NPE，message 为 null
			return javaNullError()
		}
		if err := s.oss.removeObject(ctx, s.bucket(), model.Str(file.FileName)); err != nil {
			return web.ErrorMsg(err.Error())
		}
	}
	count, err := s.softDelete(ctx, ids)
	if err != nil {
		return web.ErrorMsg(err.Error())
	}
	return web.SuccessData(count)
}

// JAVA 对照: SysFileServiceImpl.deleteSysFileById
func (s *fileService) deleteSysFileByID(ctx context.Context, id int64) *web.AjaxResult {
	file, err := s.selectSysFileByID(ctx, id)
	if err != nil {
		return web.ErrorMsg(err.Error())
	}
	if file == nil {
		return javaNullError()
	}
	if err := s.oss.removeObject(ctx, s.bucket(), model.Str(file.FileName)); err != nil {
		return web.ErrorMsg(err.Error())
	}
	count, err := s.softDelete(ctx, []int64{id})
	if err != nil {
		return web.ErrorMsg(err.Error())
	}
	return web.SuccessData(count)
}

// JAVA 对照: SysFileServiceImpl.deleteSysFileByIdNew（内部使用，异常全部吞掉）
func (s *fileService) deleteSysFileByIDNew(ctx context.Context, id int64) {
	file, err := s.selectSysFileByID(ctx, id)
	if err != nil || file == nil {
		return
	}
	if err := s.oss.removeObject(ctx, s.bucket(), model.Str(file.FileName)); err != nil {
		return
	}
	_ = s.app.DB.WithContext(ctx).Exec("delete from sys_file where id = ?", id).Error
}

// insertLogRow 按保存逻辑补雪花 id 与审计列。
func (s *fileService) insertLogRow(ctx context.Context, f *model.SysFile, userID int64, delFlag bool) error {
	f.ID = idWorker.Next()
	user := strconv.FormatInt(userID, 10)
	now := web.Now()
	cols := []fileColumn{
		{"id", f.ID},
		{"file_name", f.FileName},
		{"bucket_name", f.BucketName},
		{"original", f.Original},
		{"type", f.Type},
		{"file_size", f.FileSize},
	}
	if model.Str(f.BussName) != "" {
		cols = append(cols, fileColumn{"buss_name", f.BussName})
	}
	if model.Str(f.BussType) != "" {
		cols = append(cols, fileColumn{"buss_type", f.BussType})
	}
	cols = append(cols, fileColumn{"create_user", user}, fileColumn{"create_time", now})
	if delFlag {
		cols = append(cols, fileColumn{"update_user", user}, fileColumn{"update_time", now}, fileColumn{"del_flag", "0"})
	} else {
		cols = append(cols, fileColumn{"update_time", now})
	}
	return s.insertFileRow(ctx, cols)
}

// JAVA 对照: SysFileServiceImpl#fileLog
func (s *fileService) fileLog(ctx context.Context, src fileSource, fileName string, userID int64) (int64, error) {
	f := &model.SysFile{
		FileName:   model.Ptr(fileName),
		Original:   model.Ptr(src.Filename),
		FileSize:   src.Size,
		BucketName: model.Ptr(s.bucket()),
	}
	ext := strings.ToLower(fileNameExt(src.Filename))
	if ext == "" || !containsExt(ext, fileSupportedExtensions) {
		return -1, nil
	}
	f.Type = model.Ptr(ext)
	if err := s.insertLogRow(ctx, f, userID, true); err != nil {
		return 0, err
	}
	return f.ID, nil
}

// JAVA 对照: SysFileServiceImpl#fileSupplierLog
func (s *fileService) fileSupplierLog(ctx context.Context, src fileSource, fileName, bussName string, userID int64) (int64, error) {
	f := &model.SysFile{
		FileName:   model.Ptr(fileName),
		Original:   model.Ptr(src.Filename),
		FileSize:   src.Size,
		BucketName: model.Ptr(s.bucket()),
		BussName:   model.Ptr(bussName),
	}
	ext := strings.ToLower(fileNameExt(src.Filename))
	if ext == "" || !containsExt(ext, fileSupportedExtensions) {
		return -1, nil
	}
	f.Type = model.Ptr(ext)
	if err := s.insertLogRow(ctx, f, userID, true); err != nil {
		return 0, err
	}
	return f.ID, nil
}

// JAVA 对照: SysFileServiceImpl#fileLogId（先物理删除再按指定主键插入）
func (s *fileService) fileLogID(ctx context.Context, src fileSource, fileName string, fileID int64, userID int64) error {
	ext := strings.ToLower(fileNameExt(src.Filename))
	if ext == "" || !containsExt(ext, fileSupportedExtensionsForID) {
		return nil
	}
	s.deleteSysFileByIDNew(ctx, fileID)

	now := web.Now()
	user := strconv.FormatInt(userID, 10)
	cols := []fileColumn{
		{"id", fileID},
		{"file_name", fileName},
		{"bucket_name", s.bucket()},
		{"original", src.Filename},
		{"type", ext},
		{"file_size", src.Size},
		{"create_user", user},
		{"create_time", now},
		{"update_user", user},
		{"update_time", now},
		{"del_flag", "0"},
	}
	return s.insertFileRow(ctx, cols)
}

// ---------------------------------------------------------------------------
// 上传
// ---------------------------------------------------------------------------

// JAVA 对照: SysFileServiceImpl.uploadFiles
func (s *fileService) uploadFiles(ctx context.Context, files []*multipart.FileHeader, userID int64) *web.AjaxResult {
	resultMaps := make([]*web.JavaMap, 0, len(files))
	for _, fh := range files {
		src := fileSourceFromHeader(fh)
		fileName := uuidString() + "." + fileNameExt(src.Filename)
		resultMap := s.newResultMap(fileName)

		fileID, err := s.fileLog(ctx, src, fileName, userID)
		if err != nil {
			return web.ErrorMsg(err.Error())
		}
		resultMap.Put("id", strconv.FormatInt(fileID, 10))
		if fileID != -1 {
			data, err := src.bytes()
			if err == nil {
				err = s.oss.putObject(ctx, fileName, data)
			}
			if err != nil {
				return web.ErrorMsg(err.Error())
			}
		}
		resultMaps = append(resultMaps, resultMap)
	}
	return web.SuccessData(resultMaps)
}

// JAVA 对照: SysFileServiceImpl.uploadByUrl
func (s *fileService) uploadByURL(ctx context.Context, roList []uploadByURLRo, userID int64) *web.AjaxResult {
	if roList == nil {
		// Java: for (ro : null) -> NPE，message 为 null
		return javaNullError()
	}
	resultMaps := make([]*web.JavaMap, 0, len(roList))
	for _, ro := range roList {
		fileName := isNull(ro.FileName) + ".jpg"
		if !isNotBlank(ro.URL) {
			continue
		}
		data, err := s.downloadBytes(ctx, *ro.URL)
		if err != nil {
			s.app.Log.Error("上传失败", "url", *ro.URL, "error", err)
			continue
		}
		src := fileSourceFromBytes(fileName, data)
		objectName := uuidString() + "." + fileNameExt(src.Filename)
		resultMap := s.newResultMap(objectName)

		fileID, err := s.fileLog(ctx, src, objectName, userID)
		if err != nil {
			s.app.Log.Error("上传失败", "url", *ro.URL, "error", err)
			continue
		}
		resultMap.Put("id", strconv.FormatInt(fileID, 10))
		if fileID != -1 {
			if err := s.oss.putObject(ctx, objectName, data); err != nil {
				s.app.Log.Error("上传失败", "url", *ro.URL, "error", err)
				continue
			}
		}
		resultMaps = append(resultMaps, resultMap)
	}
	return web.SuccessData(resultMaps)
}

// JAVA 对照: SysFileServiceImpl.uploadSupplier（bussNames 按位置配对，越界即异常）
func (s *fileService) uploadSupplier(ctx context.Context, files []*multipart.FileHeader, bussNames []string, userID int64) *web.AjaxResult {
	resultMaps := make([]*web.JavaMap, 0, len(files))
	for i, fh := range files {
		if i >= len(bussNames) {
			// Java: ArrayIndexOutOfBoundsException，Java 8 的 message 就是下标
			return web.ErrorMsg(strconv.Itoa(i))
		}
		src := fileSourceFromHeader(fh)
		fileName := uuidString() + "." + fileNameExt(src.Filename)
		resultMap := s.newResultMap(fileName)

		fileID, err := s.fileSupplierLog(ctx, src, fileName, bussNames[i], userID)
		if err != nil {
			return web.ErrorMsg(err.Error())
		}
		resultMap.Put("id", strconv.FormatInt(fileID, 10))
		if fileID != -1 {
			data, err := src.bytes()
			if err == nil {
				err = s.oss.putObject(ctx, fileName, data)
			}
			if err != nil {
				return web.ErrorMsg(err.Error())
			}
		}
		resultMaps = append(resultMaps, resultMap)
	}
	return web.SuccessData(resultMaps)
}

// JAVA 对照: SysFileServiceImpl.uploadFilesPdf
// DIFF: Word->PDF 转换整块被注释，非 pdf 分支只把文件写到本地临时目录，且结果里没有 id。
func (s *fileService) uploadFilesPdf(ctx context.Context, files []*multipart.FileHeader, userID int64) *web.AjaxResult {
	resultMaps := make([]*web.JavaMap, 0, len(files))
	for _, fh := range files {
		src := fileSourceFromHeader(fh)
		fileName := uuidString() + "." + fileNameExt(src.Filename)
		resultMap := s.newResultMap(fileName)

		if fileNameExt(src.Filename) == "pdf" {
			fileID, err := s.fileLog(ctx, src, fileName, userID)
			if err != nil {
				return web.ErrorMsg(err.Error())
			}
			resultMap.Put("id", strconv.FormatInt(fileID, 10))
			if fileID != -1 {
				data, err := src.bytes()
				if err == nil {
					err = s.oss.putObject(ctx, fileName, data)
				}
				if err != nil {
					return web.ErrorMsg(err.Error())
				}
			}
		} else {
			dir := s.app.Cfg.RuoYi.UploadPath() + "/" + uuidString()
			if err := os.MkdirAll(dir, 0o755); err != nil {
				return web.ErrorMsg(err.Error())
			}
			if err := copySourceToFile(src, dir+"/"+fileName); err != nil {
				return web.ErrorMsg(err.Error())
			}
		}
		resultMaps = append(resultMaps, resultMap)
	}
	return web.SuccessData(resultMaps)
}

// copySourceToFile 对应 Java 1024 字节一块的写文件循环。
func copySourceToFile(src fileSource, path string) error {
	in, err := src.open()
	if err != nil {
		return err
	}
	defer func() { _ = in.Close() }()
	out, err := os.Create(path)
	if err != nil {
		return err
	}
	if _, err = io.Copy(out, in); err != nil {
		_ = out.Close()
		return err
	}
	return out.Close()
}

// JAVA 对照: SysFileServiceImpl.uploadFileId
func (s *fileService) uploadFileID(ctx context.Context, fileID int64, src fileSource, userID int64) *web.AjaxResult {
	fileName := uuidString() + "." + fileNameExt(src.Filename)
	resultMap := s.newResultMap(fileName)
	if err := s.fileLogID(ctx, src, fileName, fileID, userID); err != nil {
		return web.ErrorMsg(err.Error())
	}
	resultMap.Put("id", strconv.FormatInt(fileID, 10))
	if fileID != -1 {
		data, err := src.bytes()
		if err == nil {
			err = s.oss.putObject(ctx, fileName, data)
		}
		if err != nil {
			return web.ErrorMsg(err.Error())
		}
	}
	return web.SuccessData([]*web.JavaMap{resultMap})
}

// downloadBytes 对应 Forest 的 @GetRequest：跟随重定向、忽略状态码、最多重试 2 次。
func (s *fileService) downloadBytes(ctx context.Context, rawURL string) ([]byte, error) {
	var lastErr error
	for attempt := 0; attempt < 3; attempt++ {
		req, err := http.NewRequestWithContext(ctx, http.MethodGet, rawURL, nil)
		if err != nil {
			return nil, err
		}
		resp, err := s.http.Do(req)
		if err == nil {
			body, readErr := io.ReadAll(resp.Body)
			_ = resp.Body.Close()
			if readErr == nil {
				return body, nil
			}
			err = readErr
		}
		lastErr = err
		if attempt < 2 {
			delay := time.Duration(1000<<attempt) * time.Millisecond
			if delay > time.Second {
				delay = time.Second
			}
			select {
			case <-ctx.Done():
				return nil, ctx.Err()
			case <-time.After(delay):
			}
		}
	}
	return nil, fmt.Errorf("文件下载失败: %s: %w", rawURL, lastErr)
}

// ---------------------------------------------------------------------------
// 删除 / CA
// ---------------------------------------------------------------------------

// JAVA 对照: SysFileServiceImpl.updateCAFile
func (s *fileService) updateCAFile(ctx context.Context, b *sysFileBody) *web.AjaxResult {
	s.deleteSysFileByIDNew(ctx, 3001)
	if b.ID != nil {
		if err := s.app.DB.WithContext(ctx).
			Exec("update sys_file set id = 3001 where id = ?", *b.ID).Error; err != nil {
			return web.ErrorMsg(err.Error())
		}
		return web.SuccessFull("操作成功！", *b.ID)
	}
	return web.SuccessFull("操作成功！", nil)
}

// ---------------------------------------------------------------------------
// base64 适配（Base64DecodeMultipartFile）
// ---------------------------------------------------------------------------

// base64Source 对应 Base64DecodeMultipartFile.base64Convert。
func base64Source(raw string) (fileSource, error) {
	parts := strings.Split(raw, ",")
	if len(parts) < 2 {
		// Java: baseStrs[1] -> ArrayIndexOutOfBoundsException("1")
		return fileSource{}, errors.New("1")
	}
	header := strings.Split(parts[0], ";")[0]
	headerParts := strings.Split(header, "/")
	if len(headerParts) < 2 {
		return fileSource{}, errors.New("1")
	}
	// Java: System.currentTimeMillis() + (int) Math.random() * 10000 + "." + ext
	// (int) Math.random() 恒为 0，所以中间永远是 "0"。
	name := strconv.FormatInt(time.Now().UnixMilli(), 10) + "0." + headerParts[1]
	data := decodeBase64Lenient(parts[1])
	return fileSourceFromBytes(name, data), nil
}

// decodeBase64Lenient 复刻 sun.misc.BASE64Decoder#decodeBuffer：
// 跳过非法字符与空白、遇 '=' 结束、允许缺失补齐；解码失败返回空字节。
func decodeBase64Lenient(payload string) []byte {
	clean := make([]byte, 0, len(payload))
	for i := 0; i < len(payload); i++ {
		ch := payload[i]
		if ch == '=' {
			break
		}
		if (ch >= 'A' && ch <= 'Z') || (ch >= 'a' && ch <= 'z') ||
			(ch >= '0' && ch <= '9') || ch == '+' || ch == '/' {
			clean = append(clean, ch)
		}
	}
	for len(clean)%4 != 0 {
		clean = append(clean, '=')
	}
	out, err := base64.StdEncoding.DecodeString(string(clean))
	if err != nil {
		return []byte{}
	}
	return out
}

// javaNullError 对应 AjaxResult.error(null)：code=500 且 msg 键存在、值为 null。
func javaNullError() *web.AjaxResult {
	r := web.NewAjaxResult()
	r.Put(web.TagCode, web.StatusInternalError)
	r.Put(web.TagMsg, nil)
	return r
}

// ---------------------------------------------------------------------------
// 控制器
// ---------------------------------------------------------------------------

type fileHandler struct {
	svc *fileService
}

func newFileHandler(a *app.App) *fileHandler { return &fileHandler{svc: newFileService(a)} }

func parseLongPathParam(name, raw string) (int64, error) {
	v, err := strconv.ParseInt(strings.TrimSpace(raw), 10, 64)
	if err != nil {
		return 0, web.NewServiceError(
			"请求参数类型不匹配，参数[%s]要求类型为：'java.lang.Long'，但输入值为：'%s'", name, raw)
	}
	return v, nil
}

// List 对应 GET /system/file/list。
func (h *fileHandler) List(c *gin.Context) {
	rows, total, err := h.svc.selectSysFileList(c.Request.Context(), web.Page(c), bindSysFileQuery(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.Table(nonNil(rows), total))
}

// GetInfoByID 对应 GET /system/file/getInfoById/{id}。
func (h *fileHandler) GetInfoByID(c *gin.Context) {
	id, err := parseLongPathParam("id", c.Param("id"))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	row, err := h.svc.selectSysFileByID(c.Request.Context(), id)
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

// GetNewCa 对应 GET /system/file/getNewCa：分页后取第一条。
func (h *fileHandler) GetNewCa(c *gin.Context) {
	rows, _, err := h.svc.selectSysFileList(c.Request.Context(), web.Page(c), bindSysFileQuery(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if len(rows) == 0 {
		web.JSON(c, web.ErrorMsg(caNotFoundMessage))
		return
	}
	web.JSON(c, web.SuccessData(rows[0]))
}

// GetInfo 对应 GET /system/file/{ids}。
func (h *fileHandler) GetInfo(c *gin.Context) {
	ids := deleteEnd(c.Param("ids"))
	if isBlank(ids) {
		ids = emptyIDsPlaceholder
	}
	rows, err := h.svc.selectSysFileByIDs(c.Request.Context(), ids)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.SuccessData(rows))
}

func (h *fileHandler) multipartFiles(c *gin.Context, field string) ([]*multipart.FileHeader, bool) {
	form, err := c.MultipartForm()
	if err != nil {
		web.JSON(c, web.ErrorMsg(err.Error()))
		return nil, false
	}
	files := form.File[field]
	if len(files) == 0 {
		web.JSON(c, web.ErrorMsg("Required request part '"+field+"' is not present"))
		return nil, false
	}
	return files, true
}

// Upload 对应 POST /system/file/upload。
func (h *fileHandler) Upload(c *gin.Context) {
	files, ok := h.multipartFiles(c, "files")
	if !ok {
		return
	}
	web.JSON(c, h.svc.uploadFiles(c.Request.Context(), files, auth.CurrentUserID(c)))
}

// UploadByURL 对应 POST /system/file/uploadByUrl。
func (h *fileHandler) UploadByURL(c *gin.Context) {
	var body uploadRo
	if err := c.ShouldBindJSON(&body); err != nil {
		web.JSON(c, web.ErrorMsg(err.Error()))
		return
	}
	web.JSON(c, h.svc.uploadByURL(c.Request.Context(), body.List, auth.CurrentUserID(c)))
}

// UploadSupplier 对应 POST /system/file/uploadSupplier。
func (h *fileHandler) UploadSupplier(c *gin.Context) {
	form, err := c.MultipartForm()
	if err != nil {
		web.JSON(c, web.ErrorMsg(err.Error()))
		return
	}
	files := form.File["files"]
	if len(files) == 0 {
		web.JSON(c, web.ErrorMsg("Required request part 'files' is not present"))
		return
	}
	web.JSON(c, h.svc.uploadSupplier(c.Request.Context(), files, form.Value["bussNames"], auth.CurrentUserID(c)))
}

// UploadPdf 对应 POST /system/file/uploadPdf。
func (h *fileHandler) UploadPdf(c *gin.Context) {
	files, ok := h.multipartFiles(c, "files")
	if !ok {
		return
	}
	web.JSON(c, h.svc.uploadFilesPdf(c.Request.Context(), files, auth.CurrentUserID(c)))
}

// UploadFileID 对应 POST /system/file/uploadFileId。
func (h *fileHandler) UploadFileID(c *gin.Context) {
	var body sysFileBody
	if err := c.ShouldBindJSON(&body); err != nil {
		web.JSON(c, web.ErrorMsg(err.Error()))
		return
	}
	if body.Files == nil {
		// Java: Base64DecodeMultipartFile.base64Convert(null) -> NPE（controller 内，未被 catch）
		web.JSON(c, javaNullError())
		return
	}
	src, err := base64Source(*body.Files)
	if err != nil {
		web.JSON(c, web.ErrorMsg(err.Error()))
		return
	}
	if body.ID == nil {
		// Java: uploadFileId(null, file) 里 fileId.equals(-1L) -> NPE -> error(null)
		web.JSON(c, javaNullError())
		return
	}
	web.JSON(c, h.svc.uploadFileID(c.Request.Context(), *body.ID, src, auth.CurrentUserID(c)))
}

// UploadFileEnc 对应 POST /system/file/uploadFileEnc：方法体整块被注释，永远 success([])。
func (h *fileHandler) UploadFileEnc(c *gin.Context) {
	web.JSON(c, web.SuccessData([]*web.JavaMap{}))
}

// Edit 对应 PUT /system/file。
func (h *fileHandler) Edit(c *gin.Context) {
	var body sysFileBody
	if err := c.ShouldBindJSON(&body); err != nil {
		web.JSON(c, web.ErrorMsg(err.Error()))
		return
	}
	result, err := h.svc.saveSysFile(c.Request.Context(), &body, auth.CurrentUserID(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, result)
}

// UpdateCAFile 对应 POST /system/file/updateCAFile。
func (h *fileHandler) UpdateCAFile(c *gin.Context) {
	var body sysFileBody
	if err := c.ShouldBindJSON(&body); err != nil {
		web.JSON(c, web.ErrorMsg(err.Error()))
		return
	}
	web.JSON(c, h.svc.updateCAFile(c.Request.Context(), &body))
}

// RemoveByID 对应 DELETE /system/file/del/{id}。
func (h *fileHandler) RemoveByID(c *gin.Context) {
	id, err := parseLongPathParam("id", c.Param("id"))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, h.svc.deleteSysFileByID(c.Request.Context(), id))
}

// Remove 对应 DELETE /system/file/{ids}。
func (h *fileHandler) Remove(c *gin.Context) {
	ids, err := parseLongArray("ids", c.Param("ids"))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, h.svc.deleteSysFileByIDs(c.Request.Context(), ids))
}

// WechatUpload 对应 POST /system/file/uploadFile（小程序，只收图片且 <=15M）。
func (h *fileHandler) WechatUpload(c *gin.Context) {
	fh, err := c.FormFile("file")
	if err != nil {
		// Java: req.getFile("file") 为 null -> NPE -> error(null)
		web.JSON(c, javaNullError())
		return
	}
	// DIFF: Java 用 CharsetUtil.convert(ISO_8859_1 -> UTF_8) 还原中文名；
	// Go 的 multipart 解析已按 UTF-8 解码，无需再转。
	ext := fileNameExt(fh.Filename)
	if ext == "" || !containsExt(ext, []string{"jpg", "jpeg", "png", "gif"}) {
		web.JSON(c, web.ErrorMsg("上传失败,请上传照片格式的附件！"))
		return
	}
	if fh.Size > wechatMaxFileSize {
		web.JSON(c, web.ErrorMsg("上传失败,你上传的附件大于15M！"))
		return
	}
	web.JSON(c, h.svc.uploadFiles(c.Request.Context(), []*multipart.FileHeader{fh}, auth.CurrentUserID(c)))
}

// Download 对应 GET /system/file/{bucket}/{fileName}。
// DIFF: 路由参数名受 Gin 限制写成 :ids，这里按 bucket 使用。
func (h *fileHandler) Download(c *gin.Context) {
	h.writeObject(c, c.Param("ids"), c.Param("fileName"))
}

// View 对应 GET /system/file/view/{bucket}/{fileName}。
func (h *fileHandler) View(c *gin.Context) {
	h.writeObject(c, c.Param("ids"), c.Param("fileName"))
}

// writeObject 复刻 getFile：成功时 octet-stream，异常吞掉（HTTP 200 + 空 body）。
func (h *fileHandler) writeObject(c *gin.Context, bucket, fileName string) {
	data, err := h.svc.oss.getObject(c.Request.Context(), bucket, fileName)
	if err != nil {
		c.Status(http.StatusOK)
		return
	}
	c.Data(http.StatusOK, "application/octet-stream; charset=UTF-8", data)
}

// registerFile 挂载 /system/file/**。
func registerFile(reg *router.Registry) {
	h := newFileHandler(reg.App)

	g := reg.Authed.Group("/system/file")
	g.GET("/list", middleware.Perm("base:sysflie:list"), h.List)
	g.GET("/getInfoById/:id", h.GetInfoByID)
	g.GET("/getNewCa", h.GetNewCa)
	g.GET("/:ids/:fileName", h.Download)
	g.GET("/:ids", h.GetInfo)
	g.POST("/upload", middleware.OperLog(reg.App, "文件", middleware.BusinessInsert), h.Upload)
	g.POST("/uploadByUrl", middleware.OperLog(reg.App, "文件", middleware.BusinessInsert), h.UploadByURL)
	g.POST("/uploadSupplier", middleware.OperLog(reg.App, "文件", middleware.BusinessInsert), h.UploadSupplier)
	g.POST("/uploadPdf", middleware.OperLog(reg.App, "文件", middleware.BusinessInsert), h.UploadPdf)
	g.POST("/uploadFileId", middleware.OperLog(reg.App, "文件", middleware.BusinessInsert), h.UploadFileID)
	g.POST("/uploadFileEnc", middleware.OperLog(reg.App, "文件", middleware.BusinessInsert), h.UploadFileEnc)
	g.POST("/uploadFile", h.WechatUpload)
	g.POST("/updateCAFile", middleware.OperLog(reg.App, "文件", middleware.BusinessUpdate), h.UpdateCAFile)
	g.PUT("", middleware.OperLog(reg.App, "文件管理", middleware.BusinessUpdate), h.Edit)
	g.DELETE("/del/:id", middleware.OperLog(reg.App, "文件", middleware.BusinessDelete), h.RemoveByID)
	g.DELETE("/:ids", middleware.Perm("base:supplier:remove"),
		middleware.OperLog(reg.App, "文件", middleware.BusinessDelete), h.Remove)

	// JAVA 对照: SecurityConfig.antMatchers("/system/file/view/**").anonymous()
	// DIFF: 没有“仅匿名”语义，登录用户同样可访问。
	reg.Engine.GET("/system/file/view/:ids/:fileName", anonymousOnly(), h.View)
}
