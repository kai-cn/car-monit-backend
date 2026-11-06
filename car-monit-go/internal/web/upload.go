// 类/职责: 文件上传的表单解析，等价 Spring 对 MultipartFile 参数的绑定失败形态
// JAVA 对照: ServletRequestMethodArgumentResolver + GlobalExceptionHandler（异常消息直接取 e.getMessage()）
package web

import (
	"archive/zip"
	"errors"
	"io"
	"mime/multipart"
	"strings"

	"github.com/gin-gonic/gin"
)

// FormFile 取上传的 file part。两类失败的消息是 Spring 给的，不是业务文案，
// 对拍时不能替换成中文提示：
//   - 请求本身不是 multipart → "Current request is not a multipart request"
//   - multipart 里没有这个 part → "Required request part 'file' is not present"
//
// 调用点还要不要再判"空文件/后缀不对"，取决于 Java 侧那个控制器自己有没有做这一步校验
// （SysUserController.importData 没有，直接把流交给 POI；ImportSysUtil 有）。
func FormFile(c *gin.Context, name string) (*multipart.FileHeader, error) {
	if !strings.HasPrefix(c.GetHeader("Content-Type"), "multipart/") {
		return nil, errors.New("Current request is not a multipart request")
	}
	fh, err := c.FormFile(name)
	if err != nil {
		return nil, errors.New("Required request part '" + name + "' is not present")
	}
	return fh, nil
}

// contentTypePart 是 OPC 包里 POI 必查的那一条：缺了它 POI 抛
// InvalidFormatException("Package should contain a content type part [M1.13]")，
// Java 侧 GlobalExceptionHandler 直接把 e.getMessage() 当消息返回（异常类名也在里面）。
const contentTypePart = "[Content_Types].xml"

const missingContentTypeMsg = "org.apache.poi.openxml4j.exceptions.InvalidFormatException: " +
	"Package should contain a content type part [M1.13]"

// uploadFile 是 multipart.File 用到的那组方法（ReadSeeker 不含 ReadAt，zip 需要）。
type uploadFile interface {
	io.Reader
	io.ReaderAt
	io.Seeker
}

// CheckUpload 复刻 POI 打开上传流的失败链路：0 字节、既不是 zip(OOXML) 也不是 OLE2、
// 是 zip 但没有 [Content_Types].xml、以及"内容是 OLE2 但这条入口只认 OOXML"。
// 两条文案都随 Java 入口而不同：ExcelUtil 走 WorkbookFactory（OLE2 能用 HSSF 读，故 ole2Msg 传空），
// ImportSysUtil 走 XSSFWorkbook（遇到 OLE2 直接报 HSSF 那句）。其余消息两端共用。
// 返回空串表示看起来是工作簿，交给各自的解析层。读位置会被还原到开头。
func CheckUpload(size int64, r uploadFile, nonWorkbookMsg, ole2Msg string) string {
	if size == 0 {
		return "The supplied file was empty (zero bytes long)"
	}
	head := make([]byte, 4)
	n, _ := io.ReadFull(r, head)
	if _, err := r.Seek(0, io.SeekStart); err != nil {
		return ""
	}
	if n < 4 {
		return nonWorkbookMsg
	}
	if head[0] == 0xD0 && head[1] == 0xCF && head[2] == 0x11 && head[3] == 0xE0 {
		return ole2Msg // OLE2（老 .xls）：能不能读，取决于 Java 那条入口用的是哪个 POI 分支
	}
	if string(head[:2]) != "PK" {
		return nonWorkbookMsg
	}
	zr, err := zip.NewReader(r, size)
	if _, seekErr := r.Seek(0, io.SeekStart); seekErr != nil {
		return ""
	}
	if err != nil {
		return nonWorkbookMsg
	}
	for _, f := range zr.File {
		if f.Name == contentTypePart {
			return ""
		}
	}
	return missingContentTypeMsg
}
