// JAVA 对照: ruoyi-common/src/main/java/com/ruoyi/common/utils/http/OssTemplate.java:108-115
// （AmazonS3Client#generatePresignedUrl，AWS SDK v1 的查询串签名）
// 类/职责: 离线计算 S3 presigned GET URL
// 对应 Go 文件: internal/modules/systemaux/oss_endpoint.go(GetObjectURL)
//
// DIFF: 不用 minio-go 的 PresignedGetObject —— 它会先向端点发 `?location=` 取区域，
// 端点不可达时整条链路 500；Java 的 v1 SDK 用默认区域直接算签名，从不联网。
package systemaux

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"net/url"
	"sort"
	"strconv"
	"strings"
	"time"
)

// presignRegion Java 侧没有配置 region，AWS SDK v1 落到默认值 us-east-1
// （线上返回的 URL 里 credential scope 即为 us-east-1）。
const presignRegion = "us-east-1"

func awsEncode(s string, keepSlash bool) string {
	var b strings.Builder
	for i := 0; i < len(s); i++ {
		c := s[i]
		if (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') ||
			c == '-' || c == '_' || c == '.' || c == '~' || (keepSlash && c == '/') {
			b.WriteByte(c)
			continue
		}
		fmt.Fprintf(&b, "%%%02X", c)
	}
	return b.String()
}

func hmacSum(key, data []byte) []byte {
	h := hmac.New(sha256.New, key)
	h.Write(data)
	return h.Sum(nil)
}

// presign 对应 generatePresignedUrl(bucket, key, Date expiration)。
func (o *ossStorage) presign(bucket, object string, days int) (string, error) {
	if o.err != nil {
		return "", o.err
	}
	u, err := url.Parse(o.base)
	if err != nil {
		return "", err
	}
	// Java 取两次时钟：OssTemplate 先 new Date() 再 calendar.add(DAY_OF_MONTH, expires)，
	// SDK 内部又 new Date() 反算 (expiration - now)/1000。第二次必然晚于第一次，
	// 差值截断到秒就少 1 秒，所以 1 天下来的一直是 86399。
	expireAt := time.Now().AddDate(0, 0, days)
	now := time.Now().UTC()
	amzDate := now.Format("20060102T150405Z")
	dateStamp := amzDate[:8]
	scope := dateStamp + "/" + presignRegion + "/s3/aws4_request"
	expires := int(expireAt.Sub(now) / time.Second)

	params := map[string]string{
		"X-Amz-Algorithm":     "AWS4-HMAC-SHA256",
		"X-Amz-Credential":    o.accessKey + "/" + scope,
		"X-Amz-Date":          amzDate,
		"X-Amz-Expires":       strconv.Itoa(expires),
		"X-Amz-SignedHeaders": "host",
	}
	names := make([]string, 0, len(params))
	for k := range params {
		names = append(names, k)
	}
	sort.Strings(names)
	pairs := make([]string, 0, len(names))
	for _, k := range names {
		pairs = append(pairs, awsEncode(k, false)+"="+awsEncode(params[k], false))
	}
	canonicalQuery := strings.Join(pairs, "&")
	path := "/" + awsEncode(bucket, true) + "/" + awsEncode(object, true)

	canonicalRequest := strings.Join([]string{
		"GET", path, canonicalQuery, "host:" + u.Host, "", "host", "UNSIGNED-PAYLOAD",
	}, "\n")
	sum := sha256.Sum256([]byte(canonicalRequest))
	stringToSign := strings.Join([]string{
		"AWS4-HMAC-SHA256", amzDate, scope, hex.EncodeToString(sum[:]),
	}, "\n")

	key := hmacSum([]byte("AWS4"+o.secretKey), []byte(dateStamp))
	key = hmacSum(key, []byte(presignRegion))
	key = hmacSum(key, []byte("s3"))
	key = hmacSum(key, []byte("aws4_request"))
	signature := hex.EncodeToString(hmacSum(key, []byte(stringToSign)))

	// 展示顺序照抄 Java 下发的 URL：Algorithm、Date、SignedHeaders、Expires、Credential、Signature
	return strings.Join([]string{
		o.base + path + "?X-Amz-Algorithm=AWS4-HMAC-SHA256",
		"&X-Amz-Date=" + amzDate,
		"&X-Amz-SignedHeaders=host",
		"&X-Amz-Expires=" + params["X-Amz-Expires"],
		"&X-Amz-Credential=" + awsEncode(params["X-Amz-Credential"], false),
		"&X-Amz-Signature=" + signature,
	}, ""), nil
}
