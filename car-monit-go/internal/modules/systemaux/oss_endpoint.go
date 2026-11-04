// JAVA 对照: ruoyi-common/src/main/java/com/ruoyi/common/utils/http/OssEndpoint.java:26-114
// JAVA 对照: ruoyi-common/src/main/java/com/ruoyi/common/utils/http/OssTemplate.java
// 类/职责: /oss/** 对象存储端点（bucket 与 object 的增删查、预签名链接）
// 对应 Go 文件: internal/modules/systemaux/oss_endpoint.go
//
// 这组端点在 Java 里不是 AjaxResult 信封：成功时直接返回 SDK 对象的 JSON
// （数组/对象/空体），异常才落到 GlobalExceptionHandler 的 {msg, code:500}。
//
// DIFF: Java 用 AWS SDK v1（离线签名），Go 其余操作用 minio-go（同一 S3 协议）。
// DIFF: expires 参数在 Java 里是「天」（Calendar.DAY_OF_MONTH 相加）；AWS SDK v1 的
// 预签名不联网也不限 7 天，所以这里同样离线算签名、不做长度校验（minio-go 会先请求
// ?location= 取区域，端点不可达时整条链路 500）。
// DIFF: 上传成功后的返回值 Java 是 S3Object（含 objectMetadata 大对象），本环境
// MinIO(oss.endpoint) 不可达，无法核对成功形态，这里返回与列表一致的摘要字段。
package systemaux

import (
	"net/http"
	"strconv"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/minio/minio-go/v7"

	"car-monit-go/internal/app"
	"car-monit-go/internal/router"
	"car-monit-go/internal/web"
)

type ossEndpointHandler struct {
	store  *ossStorage
	bucket string
}

func newOSSEndpoint(a *app.App) *ossEndpointHandler {
	cfg := a.Cfg.Oss
	return &ossEndpointHandler{store: newOssStorage(cfg), bucket: cfg.BucketName}
}

// ossBucketJSON 对应 AWS Bucket 的 Jackson 输出（name + creationDate，owner 为空不输出）。
func ossBucketJSON(name string, created time.Time) map[string]any {
	return map[string]any{
		"name":         name,
		"creationDate": web.ISODateTime{Time: created},
	}
}

// ossObjectJSON 对应 S3ObjectSummary 的 Jackson 输出字段集。
func ossObjectJSON(bucket string, info minio.ObjectInfo) map[string]any {
	return map[string]any{
		"bucketName":   bucket,
		"key":          info.Key,
		"size":         info.Size,
		"etag":         info.ETag,
		"storageClass": info.StorageClass,
		"lastModified": web.ISODateTime{Time: info.LastModified},
	}
}

// ossFail 对应 @SneakyThrows + GlobalExceptionHandler：HTTP 200，body {msg, code:500}。
func ossFail(c *gin.Context, err error) {
	if err == nil {
		return
	}
	web.JSON(c, web.ErrorResult(err))
}

// Buckets 对应 GET /oss/bucket -> template.getAllBuckets()。
func (h *ossEndpointHandler) Buckets(c *gin.Context) {
	buckets, err := h.store.client.ListBuckets(c.Request.Context())
	if err != nil {
		ossFail(c, err)
		return
	}
	out := make([]map[string]any, 0, len(buckets))
	for _, b := range buckets {
		out = append(out, ossBucketJSON(b.Name, b.CreationDate))
	}
	c.JSON(http.StatusOK, out)
}

// GetBucket 对应 GET /oss/bucket/{bucketName}：找不到时 Java 抛
// IllegalArgumentException("Bucket Name not found!")。
func (h *ossEndpointHandler) GetBucket(c *gin.Context) {
	bucket := c.Param("bucketName")
	buckets, err := h.store.client.ListBuckets(c.Request.Context())
	if err != nil {
		ossFail(c, err)
		return
	}
	for _, b := range buckets {
		if b.Name == bucket {
			c.JSON(http.StatusOK, ossBucketJSON(b.Name, b.CreationDate))
			return
		}
	}
	web.JSON(c, web.ErrorMsg("Bucket Name not found!"))
}

// CreateBucket 对应 POST /oss/bucket/{bucketName}：createBucket（已存在则跳过）+ getBucket().get()。
func (h *ossEndpointHandler) CreateBucket(c *gin.Context) {
	ctx := c.Request.Context()
	bucket := c.Param("bucketName")
	exists, err := h.store.client.BucketExists(ctx, bucket)
	if err != nil {
		ossFail(c, err)
		return
	}
	if !exists {
		if err := h.store.client.MakeBucket(ctx, bucket, minio.MakeBucketOptions{}); err != nil {
			ossFail(c, err)
			return
		}
	}
	h.GetBucket(c)
}

// DeleteBucket 对应 DELETE /oss/bucket/{bucketName}（@ResponseStatus(ACCEPTED)，返回空体）。
func (h *ossEndpointHandler) DeleteBucket(c *gin.Context) {
	if err := h.store.client.RemoveBucket(c.Request.Context(), c.Param("bucketName")); err != nil {
		ossFail(c, err)
		return
	}
	c.Status(http.StatusAccepted)
}

// uploadTarget 解析上传的目标桶名：/{bucketName} 形式取路径参数，缺省用配置桶。
func (h *ossEndpointHandler) upload(c *gin.Context, objectName string) {
	// Java 形参是 @RequestBody MultipartFile object —— 表单字段名必须是 object，
	// 取不到时 Java 在 object.getOriginalFilename() 处 NPE（msg=null、code=500）。
	file, header, err := c.Request.FormFile("object")
	if err != nil {
		web.JSON(c, web.ErrorNilMsg())
		return
	}
	defer file.Close()

	bucket := c.Param("bucketName")
	if bucket == "" {
		bucket = h.bucket
	}
	if objectName == "" {
		objectName = header.Filename
	}
	contentType := header.Header.Get("Content-Type")
	if contentType == "" {
		contentType = "application/octet-stream"
	}
	info, err := h.store.client.PutObject(c.Request.Context(), bucket, objectName,
		file, header.Size, minio.PutObjectOptions{ContentType: contentType})
	if err != nil {
		ossFail(c, err)
		return
	}
	c.JSON(http.StatusOK, ossObjectJSON(bucket, minio.ObjectInfo{
		Key: objectName, Size: info.Size,
		ETag: info.ETag, LastModified: time.Now(),
	}))
}

// CreateObject 对应 POST /oss/object/{bucketName}（文件名取上传的原始文件名）。
func (h *ossEndpointHandler) CreateObject(c *gin.Context) { h.upload(c, "") }

// CreateObjectNamed 对应 POST /oss/object/{bucketName}/{objectName}。
func (h *ossEndpointHandler) CreateObjectNamed(c *gin.Context) {
	h.upload(c, c.Param("objectName"))
}

// FilterObject 对应 GET /oss/object/{bucketName}/{objectName}：
// Java 用 listObjects(bucket, prefix) 取摘要列表（recursive 参数在 Java 里未被使用）。
func (h *ossEndpointHandler) FilterObject(c *gin.Context) {
	bucket, prefix := c.Param("bucketName"), c.Param("objectName")
	out := make([]map[string]any, 0)
	for info := range h.store.client.ListObjects(c.Request.Context(), bucket,
		minio.ListObjectsOptions{Prefix: prefix}) {
		if info.Err != nil {
			ossFail(c, info.Err)
			return
		}
		out = append(out, ossObjectJSON(bucket, info))
	}
	c.JSON(http.StatusOK, out)
}

// GetObjectURL 对应 GET /oss/object/{bucketName}/{objectName}/{expires}，
// expires 在 Java 里按「天」计算且不得超过 7 天。
func (h *ossEndpointHandler) GetObjectURL(c *gin.Context) {
	bucket, object := c.Param("bucketName"), c.Param("objectName")
	days, err := strconv.Atoi(c.Param("expires"))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	// Java 的 generatePresignedUrl 不带额外查询参数，且完全不联网（AWS SDK v1 查询串签名）。
	link, err := h.store.presign(bucket, object, days)
	if err != nil {
		ossFail(c, err)
		return
	}
	c.JSON(http.StatusOK, map[string]any{
		"bucket": bucket, "object": object, "url": link, "expires": days,
	})
}

// DeleteObject 对应 DELETE /oss/object/{bucketName}/{objectName}/（202 空体）。
func (h *ossEndpointHandler) DeleteObject(c *gin.Context) {
	err := h.store.client.RemoveObject(c.Request.Context(), c.Param("bucketName"),
		c.Param("objectName"), minio.RemoveObjectOptions{})
	if err != nil {
		ossFail(c, err)
		return
	}
	c.Status(http.StatusAccepted)
}

func registerOSSEndpoint(reg *router.Registry) {
	h := newOSSEndpoint(reg.App)
	g := reg.Authed.Group("/oss")
	g.GET("/bucket", h.Buckets)
	g.GET("/bucket/:bucketName", h.GetBucket)
	g.POST("/bucket/:bucketName", h.CreateBucket)
	g.DELETE("/bucket/:bucketName", h.DeleteBucket)
	g.POST("/object/:bucketName", h.CreateObject)
	g.POST("/object/:bucketName/:objectName", h.CreateObjectNamed)
	g.GET("/object/:bucketName/:objectName", h.FilterObject)
	g.GET("/object/:bucketName/:objectName/:expires", h.GetObjectURL)
	g.DELETE("/object/:bucketName/:objectName", h.DeleteObject)
}
