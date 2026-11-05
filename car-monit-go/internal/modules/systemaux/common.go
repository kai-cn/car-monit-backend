// JAVA 对照: com/ruoyi/common/core/controller/BaseController.java:36-171
// JAVA 对照: com/ruoyi/common/utils/StringUtils.java（isEmpty/isBlank）
// JAVA 对照: com/ruoyi/common/constant/UserConstants.java:37,81-83
// JAVA 对照: com/ruoyi/common/utils/poi/ExcelUtil.java:635-650,1383-1403
// 类/职责: systemaux 模块共用工具 — 分页查询、动态 SQL 辅助、Excel 导出、ID 解析、审计时间
// 对应 Go 文件: internal/modules/systemaux/common.go
//
// DIFF: Java 的 BaseController/ExcelUtil 是全局工具类；Go 侧按“模块自持”原则把需要的
// 子集放在本包内（不新增 internal/service 目录，避免与其他并行迁移的模块耦合）。
package systemaux

import (
	"context"
	"errors"
	"fmt"
	"io"
	"mime/multipart"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"sync"
	"sync/atomic"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"github.com/xuri/excelize/v2"

	"car-monit-go/internal/excelx"
	"gorm.io/gorm"

	"car-monit-go/internal/app"
	"car-monit-go/internal/web"
)

// JAVA 对照: UserConstants#UNIQUE_OLD / #NOT_UNIQUE_OLD / #YES
const (
	uniqueOld    = "0"
	notUniqueOld = "1"
	userYes      = "Y"
)

// JAVA 对照: Constants#RESOURCE_PREFIX
const resourcePrefix = "/profile"

// JAVA 对照: FileUploadUtils#DEFAULT_MAX_SIZE / #DEFAULT_FILE_NAME_LENGTH
const (
	defaultMaxSize        = 50 * 1024 * 1024
	defaultFileNameLength = 100
)

// JAVA 对照: MimeTypeUtils#DEFAULT_ALLOWED_EXTENSION:29-39
var defaultAllowedExtension = []string{
	"bmp", "gif", "jpg", "jpeg", "png",
	"doc", "docx", "xls", "xlsx", "ppt", "pptx", "html", "htm", "txt",
	"rar", "zip", "gz", "bz2",
	"mp4", "avi", "rmvb",
	"pdf",
}

// nowPtr 对应 Java new Timestamp(System.currentTimeMillis())。
func nowPtr() *web.DateTime {
	now := web.Now()
	return &now
}

// strVal 取指针字符串，nil 视为 Java 的 null。
func strVal(p *string) string {
	if p == nil {
		return ""
	}
	return *p
}

// numVal 取指针整数，nil 视为 Java 的 null（返回 0）。
func numVal(p *int64) int64 {
	if p == nil {
		return 0
	}
	return *p
}

// isNull 对应 CommonUtil.isNull：null -> ""，否则 trim。
func isNull(p *string) string {
	if p == nil {
		return ""
	}
	return strings.TrimSpace(*p)
}

// isBlank 对应 StringUtils.isBlank / CommonUtil.isBlank。
func isBlank(s string) bool { return strings.TrimSpace(s) == "" }

// isNotEmpty 对应 StringUtils.isNotEmpty（不 trim，null 视为空）。
func isNotEmpty(p *string) bool { return p != nil && *p != "" }

// isNotBlank 对应 StringUtils.isNotBlank / CommonUtil.isNotBlank（trim 后非空）。
func isNotBlank(p *string) bool { return p != nil && strings.TrimSpace(*p) != "" }

// deleteEnd 对应 CommonUtil.deleteEnd：只删一个结尾逗号。
func deleteEnd(s string) string {
	if strings.HasSuffix(s, ",") {
		return s[:len(s)-1]
	}
	return s
}

// requestParam 对应 ServletRequest#getParameter：query string 优先，其次表单体。
// DIFF: Go 的 gin 没有参数聚合 Map，这里显式按 Servlet 优先级取值。
func requestParam(c *gin.Context, name string) string {
	if v, ok := c.GetQuery(name); ok {
		return v
	}
	return c.PostForm(name)
}

// queryPtr 读取 query string：参数不存在返回 nil（对应 Java 包装类型的 null），
// 存在但为空串返回指向 "" 的指针（对应 MyBatis 的 != null 判定）。
func queryPtr(c *gin.Context, name string) *string {
	if v, ok := c.GetQuery(name); ok {
		return &v
	}
	return nil
}

// queryInt64Ptr 对应 Spring 把 GET 参数绑定到包装类型 Long：
// 参数缺失或空串为 nil，解析失败也退化为 nil（Spring 会返回 400，属于非法入参的边角）。
func queryInt64Ptr(c *gin.Context, name string) *int64 {
	v, ok := c.GetQuery(name)
	if !ok {
		return nil
	}
	v = strings.TrimSpace(v)
	if v == "" {
		return nil
	}
	n, err := strconv.ParseInt(v, 10, 64)
	if err != nil {
		return nil
	}
	return &n
}

// parseLongArray 对应 Spring 对 @PathVariable Long[] 的 “1,2,3” 拆分 + 类型转换。
func parseLongArray(name, raw string) ([]int64, error) {
	parts := strings.Split(raw, ",")
	out := make([]int64, 0, len(parts))
	for _, p := range parts {
		p = strings.TrimSpace(p)
		if p == "" {
			continue
		}
		v, err := strconv.ParseInt(p, 10, 64)
		if err != nil {
			// DIFF: Java 抛 MethodArgumentTypeMismatchException，由全局处理器转成同一条文案。
			return nil, web.NewServiceError("请求参数类型不匹配，参数[%s]要求类型为：'java.lang.Long[]'，但输入值为：'%s'", name, raw)
		}
		out = append(out, v)
	}
	return out, nil
}

// inPlaceholders 生成 "?,?,?"；调用方保证 n > 0。
func inPlaceholders(n int) string {
	if n <= 0 {
		return "NULL"
	}
	return strings.TrimSuffix(strings.Repeat("?,", n), ",")
}

// int64Args 把 []int64 转成 []any，便于与 inPlaceholders 配合。
func int64Args(ids []int64) []any {
	out := make([]any, 0, len(ids))
	for _, id := range ids {
		out = append(out, id)
	}
	return out
}

// queryPage 复刻 PageHelper.startPage + BaseController.getDataTable。
//   - pd.HasPage 时先 COUNT 再 LIMIT/OFFSET，total 取 COUNT 结果；
//   - 未分页时 total 取 len(rows)（PageInfo(List) 对非 Page 列表的行为）。
//
// DIFF: Java 由 MyBatis 拦截器改写 SQL；Go 显式拼 ORDER BY/LIMIT，排序列只来自
// web.PageDomain 的白名单校验结果或本包内的常量默认值。
func queryPage[T any](ctx context.Context, db *gorm.DB, pd web.PageDomain,
	countSQL string, args []any, listSQL, defaultOrder string) ([]T, int64, error) {
	if err := pd.StartPageError(); err != nil {
		return nil, 0, err
	}
	var total int64
	if pd.HasPage {
		if err := db.WithContext(ctx).Raw(countSQL, args...).Scan(&total).Error; err != nil {
			return nil, 0, err
		}
	}
	if pd.SkipQuery(total) {
		return []T{}, total, nil
	}
	sql := listSQL
	// JAVA 对照: OrderByParser.converToOrderBySql —— 客户端给了 orderByColumn 就**替换**语句
	// 自带的 order by；没给则沿用 defaultOrder。所以语句本身的排序一律由调用方放进 defaultOrder。
	if order := pd.OrderByWithDefault(defaultOrder); order != "" {
		sql += " order by " + order
	}
	var rows []T
	q := db.WithContext(ctx)
	if pd.HasPage {
		sql += " limit ? offset ?"
		lim, off := pd.LimitOffset(total)
		q = q.Raw(sql, append(append([]any{}, args...), lim, off)...)
	} else {
		q = q.Raw(sql, args...)
	}
	if err := q.Scan(&rows).Error; err != nil {
		return nil, 0, err
	}
	if !pd.HasPage {
		total = int64(len(rows))
	}
	return rows, total, nil
}

// nonNil 保证 JSON 输出 [] 而不是 null（Java 侧 List 不会返回 null）。
func nonNil[T any](in []T) []T {
	if in == nil {
		return make([]T, 0)
	}
	return in
}

// exportExcel 对应 ExcelUtil.exportExcel(list, sheetName)：
// 工作表写盘到 ruoyi.profile/download，返回“uuid_sheetName.xlsx”文件名（data 即该名）。
// DIFF: Java 用 POI 生成带样式的 xlsx；Go 用 excelize，仅保证表头+数据与文件名规则一致。
func exportExcel(a *app.App, sheetName string, headers []string, rows [][]any) (string, error) {
	f := excelize.NewFile()
	defer func() { _ = f.Close() }()

	if err := f.SetSheetName("Sheet1", sheetName); err != nil {
		return "", err
	}
	style, err := f.NewStyle(&excelize.Style{Font: &excelize.Font{Bold: true}})
	if err != nil {
		return "", err
	}
	for i, h := range headers {
		cell, err := excelize.CoordinatesToCellName(i+1, 1)
		if err != nil {
			return "", err
		}
		if err := f.SetCellValue(sheetName, cell, h); err != nil {
			return "", err
		}
		if err := f.SetCellStyle(sheetName, cell, cell, style); err != nil {
			return "", err
		}
	}
	for r, row := range rows {
		for c, v := range row {
			cell, err := excelize.CoordinatesToCellName(c+1, r+2)
			if err != nil {
				return "", err
			}
			if err := f.SetCellValue(sheetName, cell, excelx.UtilCell(v)); err != nil {
				return "", err
			}
		}
	}

	filename := uuid.NewString() + "_" + sheetName + ".xlsx"
	dir := a.Cfg.RuoYi.DownloadPath()
	if err := os.MkdirAll(dir, 0o755); err != nil {
		return "", err
	}
	if err := f.SaveAs(filepath.Join(dir, filename)); err != nil {
		return "", err
	}
	return filename, nil
}

// excelSend 统一处理导出响应：成功回 success(filename)（Java AjaxResult.success(filename)），
// 失败交给 web.ErrorResult（对应 GlobalExceptionHandler 的 UtilException 分支）。
func excelSend(c *gin.Context, filename string, err error) {
	if err != nil {
		web.JSON(c, web.ErrorMsg(err.Error()))
		return
	}
	// JAVA 对照: AjaxResult.success(String) 重载 → 文件名放在 msg。
	web.JSON(c, web.SuccessMsg(filename))
}

// ---------------------------------------------------------------------------
// 雪花主键
// JAVA 对照: com/ruoyi/common/utils/uuid/SnowflakeIdWorker（sys_file 主键）
// DIFF: Java 用独立 Bean 的雪花算法；Go 侧在本包内实现等价的时间戳+序号生成器。
// ---------------------------------------------------------------------------

type snowflake struct {
	mu       sync.Mutex
	lastMS   int64
	sequence int64
}

var idWorker = &snowflake{}

const snowflakeEpoch = int64(1288834974657)

func (s *snowflake) Next() int64 {
	s.mu.Lock()
	defer s.mu.Unlock()
	now := time.Now().UnixMilli()
	if now == s.lastMS {
		s.sequence = (s.sequence + 1) & 0xFFF
		if s.sequence == 0 {
			for now <= s.lastMS {
				now = time.Now().UnixMilli()
			}
		}
	} else {
		s.sequence = 0
	}
	s.lastMS = now
	return ((now - snowflakeEpoch) << 22) | (1 << 12) | s.sequence
}

// uuidString 对应 StringUtils.getUUID()（去横线）。
func uuidString() string { return strings.ReplaceAll(uuid.NewString(), "-", "") }

// fileNameExt 对应 hutool FileUtil.extName：最后一个 '.' 之后的部分（无点则为空）。
func fileNameExt(name string) string {
	name = baseName(name)
	if i := strings.LastIndex(name, "."); i >= 0 {
		return name[i+1:]
	}
	return ""
}

// baseName 对应 FilenameUtils.getBaseName 的文件名部分（去路径、去后缀）。
func baseName(name string) string {
	if i := strings.LastIndexAny(name, `/\`); i >= 0 {
		name = name[i+1:]
	}
	return name
}

// fileStem 对应 FilenameUtils.getBaseName：去路径且去最后一个后缀。
func fileStem(name string) string {
	name = baseName(name)
	if i := strings.LastIndex(name, "."); i >= 0 {
		return name[:i]
	}
	return name
}

// containsExt 对应 FileUtil.extName(...).indexOf(x) > -1 的白名单判断。
func containsExt(ext string, candidates []string) bool {
	for _, c := range candidates {
		if strings.Contains(ext, c) {
			return true
		}
	}
	return false
}

// uploadError 构造文件上传异常文案（对应 FileSizeLimitExceededException /
// FileNameLengthLimitExceededException / InvalidExtensionException）。
func fileSizeLimitMessage() string {
	return fmt.Sprintf("上传的文件大小超出限制的文件大小！<br/>允许的文件最大大小是：%dMB！", defaultMaxSize/1024/1024)
}

func fileNameLengthMessage() string {
	return fmt.Sprintf("上传的文件名最长%d个字符", defaultFileNameLength)
}

func invalidExtensionMessage(filename, ext string, allowed []string) string {
	return "文件[" + filename + "]后缀[" + ext + "]不正确，请上传" + javaArrayString(allowed) + "格式"
}

// javaStringLength 对应 String#length：按 UTF-16 码元计数（代理对算 2）。
func javaStringLength(s string) int {
	n := 0
	for _, r := range s {
		if r > 0xFFFF {
			n += 2
		} else {
			n++
		}
	}
	return n
}

// mimeExtension 对应 MimeTypeUtils.getExtension(String contentType)。
func mimeExtension(contentType string) string {
	switch contentType {
	case "image/png":
		return "png"
	case "image/jpg":
		return "jpg"
	case "image/jpeg":
		return "jpeg"
	case "image/bmp":
		return "bmp"
	case "image/gif":
		return "gif"
	}
	return ""
}

// isAllowedExt 对应 FileUploadUtils.isAllowedExtension（equalsIgnoreCase）。
func isAllowedExt(ext string, allowed []string) bool {
	for _, a := range allowed {
		if strings.EqualFold(a, ext) {
			return true
		}
	}
	return false
}

// datePath 对应 DateUtils.datePath（yyyy/MM/dd）。
func datePath() string { return time.Now().Format("2006/01/02") }

// uploadSeq 对应 Seq.uploadSeq（AtomicInteger 初始 1）。
var uploadSeq atomic.Int64

func init() { uploadSeq.Store(1) }

// nextUploadSeqID 对应 Seq.getId(Seq.uploadSeqType)：yyyyMMddHHmmss + "A" + 3 位循环递增。
func nextUploadSeqID() string {
	value := uploadSeq.Add(1) - 1 // Java: 先取值再 +1
	if uploadSeq.Load() >= 1000 {
		uploadSeq.Store(1)
	}
	return time.Now().Format("20060102150405") + "A" + fmt.Sprintf("%03d", value)
}

// javaSubstring 对应 StringUtils.substring(str, start)：越界时钳位。
func javaSubstring(s string, start int) string {
	if start < 0 {
		start = 0
	}
	if start >= len(s) {
		return ""
	}
	return s[start:]
}

// uploadTo 对应 FileUploadUtils.upload(baseDir, file, allowedExtension)：
// 校验顺序与 Java 一致（文件名长度 -> 大小/后缀 -> 落盘），返回 /profile 开头的相对 url。
func uploadTo(baseDir, profile string, fh *multipart.FileHeader, allowed []string) (string, error) {
	original := fh.Filename
	if javaStringLength(original) > defaultFileNameLength {
		return "", errors.New(fileNameLengthMessage())
	}
	if fh.Size > defaultMaxSize {
		return "", errors.New(fileSizeLimitMessage())
	}
	ext := fileNameExt(original)
	if ext == "" {
		ext = mimeExtension(fh.Header.Get("Content-Type"))
	}
	if !isAllowedExt(ext, allowed) {
		return "", errors.New(invalidExtensionMessage(original, ext, allowed))
	}

	fileName := datePath() + "/" + fileStem(original) + "_" + nextUploadSeqID() + "." + ext
	absPath := baseDir + "/" + fileName
	if err := os.MkdirAll(filepath.Dir(absPath), 0o755); err != nil {
		return "", err
	}
	src, err := fh.Open()
	if err != nil {
		return "", err
	}
	defer func() { _ = src.Close() }()
	dst, err := os.Create(absPath)
	if err != nil {
		return "", err
	}
	if _, err = io.Copy(dst, src); err != nil {
		_ = dst.Close()
		return "", err
	}
	if err = dst.Close(); err != nil {
		return "", err
	}
	return resourcePrefix + "/" + javaSubstring(baseDir, len(profile)+1) + "/" + fileName, nil
}

// javaArrayString 对应 Arrays.toString(String[])。
func javaArrayString(items []string) string {
	return "[" + strings.Join(items, ", ") + "]"
}
