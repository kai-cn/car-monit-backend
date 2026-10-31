// JAVA 对照: com/ruoyi/common/utils/http/OssTemplate.java:1-200
// JAVA 对照: com/ruoyi/common/config/OssProperties.java
// 类/职责: S3 兼容对象存储客户端 — putObject / getObject / removeObject
// 对应 Go 文件: internal/modules/systemaux/oss.go
//
// DIFF: Java 用 AWS SDK v1（endpoint 带 http:// 前缀、path-style）；Go 用 minio-go，
// 端点必须去掉协议头并用 Secure 单独表达。Bucket 固定取配置 oss.bucketName，
// 与 OssProperties 的注入方式一致。
package systemaux

import (
	"bytes"
	"context"
	"io"
	"strings"

	"github.com/minio/minio-go/v7"
	"github.com/minio/minio-go/v7/pkg/credentials"

	"car-monit-go/internal/config"
)

type ossStorage struct {
	client *minio.Client
	bucket string
	err    error
}

// newOssStorage 对应 OssTemplate.afterPropertiesSet：启动时构建一次客户端。
func newOssStorage(cfg config.Oss) *ossStorage {
	endpoint := strings.TrimSpace(cfg.Endpoint)
	secure := false
	switch {
	case strings.HasPrefix(endpoint, "https://"):
		endpoint = strings.TrimPrefix(endpoint, "https://")
		secure = true
	case strings.HasPrefix(endpoint, "http://"):
		endpoint = strings.TrimPrefix(endpoint, "http://")
	}
	endpoint = strings.TrimSuffix(endpoint, "/")

	client, err := minio.New(endpoint, &minio.Options{
		Creds:  credentials.NewStaticV4(cfg.AccessKey, cfg.SecretKey, ""),
		Secure: secure,
	})
	return &ossStorage{client: client, bucket: cfg.BucketName, err: err}
}

// putObject 对应 OssTemplate.putObject(bucketName, objectName, InputStream)：
// Java 先把流读成字节数组再上传，内容类型固定 application/octet-stream。
func (o *ossStorage) putObject(ctx context.Context, objectName string, data []byte) error {
	if o.err != nil {
		return o.err
	}
	_, err := o.client.PutObject(ctx, o.bucket, objectName, bytes.NewReader(data), int64(len(data)),
		minio.PutObjectOptions{ContentType: "application/octet-stream"})
	return err
}

// getObject 对应 OssTemplate.getObject：Java 返回惰性 S3Object，这里直接读完字节。
func (o *ossStorage) getObject(ctx context.Context, bucket, objectName string) ([]byte, error) {
	if o.err != nil {
		return nil, o.err
	}
	obj, err := o.client.GetObject(ctx, bucket, objectName, minio.GetObjectOptions{})
	if err != nil {
		return nil, err
	}
	defer func() { _ = obj.Close() }()
	return io.ReadAll(obj)
}

// removeObject 对应 OssTemplate.removeObject（deleteObject，不抛 404）。
func (o *ossStorage) removeObject(ctx context.Context, bucket, objectName string) error {
	if o.err != nil {
		return o.err
	}
	return o.client.RemoveObject(ctx, bucket, objectName, minio.RemoveObjectOptions{})
}
