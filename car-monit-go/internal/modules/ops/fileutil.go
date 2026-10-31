// JAVA 对照: ruoyi-common/src/main/java/com/ruoyi/common/utils/file/FileUtils.java
// JAVA 对照: ruoyi-common/src/main/java/com/ruoyi/common/utils/file/FileUploadUtils.java
// JAVA 对照: ruoyi-common/src/main/java/com/ruoyi/common/utils/file/MimeTypeUtils.java
// JAVA 对照: ruoyi-common/src/main/java/com/ruoyi/common/utils/file/FileTypeUtils.java
// JAVA 对照: ruoyi-common/src/main/java/com/ruoyi/common/utils/uuid/Seq.java
// JAVA 对照: org.apache.commons.io.FilenameUtils（只搬用到的方法）
// 类/职责: 上传/下载路径规则、文件名生成、后缀白名单、附件响应头
// 对应 Go 文件: internal/modules/ops/fileutil.go
//
// DIFF: Java 用 java.io.File + File.separator 拼路径；Go 统一用 "/"（Windows 上同样可用），
// 目录不存在时逐级 mkdir（对应 Java 的 mkdirs()）。
// DIFF: `FilenameUtils.getBaseName` 在 Java 里跳过目录名里的点（`a.b/c` -> `c`），
// 这里逐条复刻同样的判定，而不是简单 rsplit。
package ops

import (
	"errors"
	"fmt"
	"io"
	"mime/multipart"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"sync/atomic"
	"time"

	"github.com/gin-gonic/gin"
)

// 对应 com.ruoyi.common.constant.Constants.RESOURCE_PREFIX。
const resourcePrefix = "/profile"

// 对应 FileUploadUtils.DEFAULT_MAX_SIZE / DEFAULT_FILE_NAME_LENGTH。
const (
	defaultMaxSize       = int64(50 * 1024 * 1024)
	defaultFileNameLimit = 100
)

// defaultAllowedExtension 对应 MimeTypeUtils.DEFAULT_ALLOWED_EXTENSION（顺序即报错文案里的顺序）。
var defaultAllowedExtension = []string{
	// 图片
	"bmp", "gif", "jpg", "jpeg", "png",
	// word excel powerpoint
	"doc", "docx", "xls", "xlsx", "ppt", "pptx", "html", "htm", "txt",
	// 压缩文件
	"rar", "zip", "gz", "bz2",
	// 视频格式
	"mp4", "avi", "rmvb",
	// pdf
	"pdf",
}

// ---------------------------------------------------------------- 后缀与白名单

// getFileType 对应 FileTypeUtils.getFileType：最后一个 "." 之后的部分，转小写。
func getFileType(fileName string) string {
	idx := strings.LastIndex(fileName, ".")
	if idx < 0 {
		return ""
	}
	return strings.ToLower(fileName[idx+1:])
}

// checkAllowDownload 对应 FileUtils.checkAllowDownload：
// 出现 ".." 一律拒绝，后缀必须在默认白名单内（已转小写，所以 .PNG 也能下）。
func checkAllowDownload(resource string) bool {
	if strings.Contains(resource, "..") {
		return false
	}
	ext := getFileType(resource)
	for _, allowed := range defaultAllowedExtension {
		if allowed == ext {
			return true
		}
	}
	return false
}

// isAllowedExtension 对应 FileUploadUtils.isAllowedExtension（equalsIgnoreCase）。
func isAllowedExtension(extension string, allowed []string) bool {
	for _, item := range allowed {
		if strings.EqualFold(item, extension) {
			return true
		}
	}
	return false
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

// ---------------------------------------------------------------- FilenameUtils

// indexOfLastSeparator 对应 FilenameUtils.indexOfLastSeparator：'/' 与 '\' 都算。
func indexOfLastSeparator(name string) int {
	return maxInt(strings.LastIndex(name, "/"), strings.LastIndex(name, "\\"))
}

// indexOfExtension 对应 FilenameUtils.indexOfExtension：点在目录名里不算后缀。
func indexOfExtension(name string) int {
	extPos := strings.LastIndex(name, ".")
	if indexOfLastSeparator(name) > extPos {
		return -1
	}
	return extPos
}

// filenameName 对应 FilenameUtils.getName。
func filenameName(name string) string {
	return name[indexOfLastSeparator(name)+1:]
}

// filenameBaseName 对应 FilenameUtils.getBaseName（`a/b.tar.gz` -> `b.tar`）。
// commons-io 的实现是 getName 之后再砍掉最后一段后缀，这里逐步对应。
func filenameBaseName(name string) string {
	short := filenameName(name)
	if idx := strings.LastIndex(short, "."); idx >= 0 {
		return short[:idx]
	}
	return short
}

// filenameExtension 对应 FilenameUtils.getExtension。
func filenameExtension(name string) string {
	idx := indexOfExtension(name)
	if idx < 0 {
		return ""
	}
	return name[idx+1:]
}

// ---------------------------------------------------------------- 文件名生成

// seqUpload 对应 Seq.uploadSeq（AtomicInteger 初始 1）。
var seqUpload atomic.Int64

func init() { seqUpload.Store(1) }

// seqID 对应 Seq.getId(Seq.uploadSeqType)：yyyyMMddHHmmss + "A" + 3 位循环递增。
func seqID() string {
	value := seqUpload.Add(1) - 1 // Java: 先取值再 +1
	if seqUpload.Load() >= 1000 {
		seqUpload.Store(1)
	}
	return time.Now().Format("20060102150405") + "A" + fmt.Sprintf("%03d", value)
}

// datePath 对应 DateUtils.datePath()：yyyy/MM/dd。
func datePath() string { return time.Now().Format("2006/01/02") }

// getAbsoluteFile 对应 FileUploadUtils.getAbsoluteFile：目录不存在时逐级创建。
func getAbsoluteFile(uploadDir, fileName string) (string, error) {
	desc := uploadDir + "/" + fileName
	if _, err := os.Stat(desc); err != nil {
		parent := filepath.Dir(desc)
		if _, statErr := os.Stat(parent); statErr != nil {
			if mkErr := os.MkdirAll(parent, 0o755); mkErr != nil {
				return "", mkErr
			}
		}
	}
	abs, err := filepath.Abs(desc)
	if err != nil {
		return "", err
	}
	return abs, nil
}

// getPathFileName 对应 FileUploadUtils.getPathFileName：把 profile 前缀换成 /profile。
// DIFF: Java 用 StringUtils.substring(uploadDir, profile.length() + 1) 做越界钳位，这里同样钳位。
func getPathFileName(profile, uploadDir, fileName string) string {
	dirLastIndex := len(profile) + 1
	return resourcePrefix + "/" + substringFrom(uploadDir, dirLastIndex) + "/" + fileName
}

// substringFrom 对应 StringUtils.substring(str, start)：start 越界时返回空串。
func substringFrom(s string, start int) string {
	if start < 0 {
		start = 0
	}
	if start >= len(s) {
		return ""
	}
	return s[start:]
}

// ---------------------------------------------------------------- 上传

// uploadFile 对应 FileUploadUtils.upload(baseDir, file, DEFAULT_ALLOWED_EXTENSION)。
// 校验顺序与 Java 一致：文件名长度 -> 大小/后缀 -> 落盘。
func uploadFile(baseDir, profile string, file *multipart.FileHeader) (string, error) {
	original := file.Filename
	if len(original) > defaultFileNameLimit {
		return "", errors.New("上传的文件名最长" + strconv.Itoa(defaultFileNameLimit) + "个字符")
	}

	if file.Size > defaultMaxSize {
		return "", errors.New("上传的文件大小超出限制的文件大小！<br/>允许的文件最大大小是：" +
			strconv.FormatInt(defaultMaxSize/1024/1024, 10) + "MB！")
	}

	extension := filenameExtension(original)
	if extension == "" {
		// Java: MimeTypeUtils.getExtension(Objects.requireNonNull(file.getContentType()))
		extension = mimeExtension(file.Header.Get("Content-Type"))
	}
	if !isAllowedExtension(extension, defaultAllowedExtension) {
		return "", fmt.Errorf("文件[%s]后缀[%s]不正确，请上传%v格式", original, extension, defaultAllowedExtension)
	}

	fileName := fmt.Sprintf("%s/%s_%s.%s", datePath(), filenameBaseName(original), seqID(), extension)
	absPath, err := getAbsoluteFile(baseDir, fileName)
	if err != nil {
		return "", err
	}

	src, err := file.Open()
	if err != nil {
		return "", err
	}
	defer func() { _ = src.Close() }()

	dst, err := os.Create(absPath)
	if err != nil {
		return "", err
	}
	// DIFF: Java 的 MultipartFile.transferTo 可能在失败时留下半个文件；这里同样不清理。
	if _, err = io.Copy(dst, src); err != nil {
		_ = dst.Close()
		return "", err
	}
	if err = dst.Close(); err != nil {
		return "", err
	}
	return getPathFileName(profile, baseDir, fileName), nil
}

// ---------------------------------------------------------------- 下载

// writeBytes 对应 FileUtils.writeBytes(String filePath, OutputStream os)。
// 文件不存在时返回错误（Java 抛 FileNotFoundException，异常被控制器 catch）。
func writeBytes(filePath string, w io.Writer) error {
	f, err := os.Open(filePath)
	if err != nil {
		return err
	}
	defer func() { _ = f.Close() }()
	_, err = io.Copy(w, f)
	return err
}

// deleteFile 对应 FileUtils.deleteFile：只删文件，目录不动。
func deleteFile(filePath string) bool {
	info, err := os.Stat(filePath)
	if err != nil || info.IsDir() {
		return false
	}
	return os.Remove(filePath) == nil
}

// setAttachmentResponseHeader 对应 FileUtils.setAttachmentResponseHeader。
func setAttachmentResponseHeader(c *gin.Context, realFileName string) {
	encoded := percentEncode(realFileName)
	disposition := "attachment; filename=" + encoded + ";filename*=utf-8''" + encoded
	c.Header("Access-Control-Expose-Headers", "Content-Disposition,download-filename")
	c.Header("Content-disposition", disposition)
	c.Header("download-filename", encoded)
}

// percentEncode 对应 FileUtils.percentEncode：URLEncoder.encode(s, UTF-8) 后把 '+' 换成 %20。
func percentEncode(s string) string {
	return strings.ReplaceAll(javaURLEncode(s), "+", "%20")
}

// javaURLEncode 复刻 java.net.URLEncoder.encode(String, "UTF-8")：
// 保留字母数字与 ".-*_"，空格 -> '+'，其余按 UTF-8 逐字节 %XX（大写十六进制）。
func javaURLEncode(s string) string {
	const safe = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.-*_"
	var b strings.Builder
	for _, r := range s {
		if r < 128 && strings.ContainsRune(safe, r) {
			b.WriteRune(r)
			continue
		}
		if r == ' ' {
			b.WriteByte('+')
			continue
		}
		for _, by := range []byte(string(r)) {
			fmt.Fprintf(&b, "%%%02X", by)
		}
	}
	return b.String()
}

func maxInt(a, b int) int {
	if a > b {
		return a
	}
	return b
}

// getName 对应 FileUtils.getName：`/profile/upload/2022/04/16/ruoyi.png` -> `ruoyi.png`。
func getName(fileName string) string {
	return fileName[maxInt(strings.LastIndex(fileName, "/"), strings.LastIndex(fileName, "\\"))+1:]
}
