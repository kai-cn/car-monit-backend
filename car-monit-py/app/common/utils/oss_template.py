"""aws-s3 通用存储操作（支持所有兼容 S3 协议的云存储：MinIO / 阿里云 OSS / 腾讯云 COS …）.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/utils/http/OssTemplate.java
# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/config/OssAutoConfiguration.java

Java 用 ``AmazonS3``（aws-sdk-java v1）+ 一组 ``static`` 方法共享一个静态字段
``private static AmazonS3 amazonS3``。Python 侧等价的形状是：

* 模块级 ``_AMAZON_S3`` 缓存 —— 对应那个静态字段；
* :meth:`OssTemplate.after_properties_set` —— 对应 ``InitializingBean``，由它在
  ``@Bean`` 初始化时把 client 建好；
* :meth:`OssTemplate.put_object` / :meth:`get_object` / :meth:`remove_object` 仍是
  **静态**方法（Java 侧它们在调用点就是 ``OssTemplate.putObject(...)``，例如
  ``SysFileServiceImpl.uploadBase64Picture``）。

与原版的一处必要差异：**client 延迟创建**
------------------------------------------
Spring 启动时就会执行 ``afterPropertiesSet()``，MinIO 不可达时应用直接起不来。本项目
（见 ``requirements-middleware.txt``）的既定做法是"中间件不可达也要能启动"，所以
:func:`get_amazon_s3` 在**第一次真正用到**时才 ``import boto3`` 并建 client：

* 没装 ``boto3`` -> ``RuntimeError``，落到通用处理器 -> HTTP 200 + ``code 500``；
* 装了但 MinIO 不可达 -> botocore 的 ``EndpointConnectionError`` -> 同上。

也就是说"启动成功"不再等价于"OSS 可用"，但**每个用到的端点的失败形态与 Java 一致**。

``disableChunkedEncoding()``
----------------------------
Java 显式关了分块传输（MinIO 对 ``aws-chunked`` 支持不好）。botocore 对**定长** body
本身就不会用 ``aws-chunked``，所以这里不再单独设置，只在
``Config(signature_version="s3v4")`` 上保持一致。
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, BinaryIO, Dict, List, Optional

from app.settings import OssSection, get_settings

logger = logging.getLogger("app.common.utils.oss_template")

#: Java: ``private static AmazonS3 amazonS3`` —— 进程内共享一个 client。
_AMAZON_S3: Any = None

#: Java: ``putObject(bucket, objectName, stream)`` 里写死的 content type。
DEFAULT_CONTENT_TYPE: str = "application/octet-stream"


class Bucket:
    """Java: ``com.amazonaws.services.s3.model.Bucket``（只保留本项目读取的 ``name``）。"""

    def __init__(self, name: str, creation_date: Optional[datetime] = None) -> None:
        self.name = name
        self.creation_date = creation_date

    # Java: getName()
    def get_name(self) -> str:
        return self.name

    def __repr__(self) -> str:  # pragma: no cover - 只为调试可读
        return f"Bucket(name={self.name!r})"


class S3Object:
    """Java: ``com.amazonaws.services.s3.model.S3Object``.

    只实现本项目用到的 ``getObjectContent()``（返回 ``BinaryIO``）与 ``close()``；Java 里
    它是 ``Closeable``，调用点统一写成 ``try (S3Object s3Object = ...)``，所以这里也支持
    上下文管理器。
    """

    def __init__(
        self,
        body: BinaryIO,
        bucket_name: Optional[str] = None,
        key: Optional[str] = None,
        content_type: Optional[str] = None,
        content_length: Optional[int] = None,
    ) -> None:
        self._body = body
        self.bucket_name = bucket_name
        self.key = key
        self.content_type = content_type
        self.content_length = content_length

    # Java: getObjectContent()
    def get_object_content(self) -> BinaryIO:
        return self._body

    # Java: close()
    def close(self) -> None:
        close = getattr(self._body, "close", None)
        if callable(close):
            close()

    def __enter__(self) -> "S3Object":
        return self

    def __exit__(self, *_exc: Any) -> None:
        self.close()


# --------------------------------------------------------------------------- client


def get_amazon_s3() -> Any:
    """取（必要时创建）那个"静态" client。Java: 读 ``OssTemplate.amazonS3``。"""
    global _AMAZON_S3
    if _AMAZON_S3 is None:
        _AMAZON_S3 = _build_client(get_settings().oss)
    return _AMAZON_S3


def reset_amazon_s3() -> None:
    """Test helper: 丢掉缓存的 client（相当于重新执行一次 ``afterPropertiesSet``）。"""
    global _AMAZON_S3
    _AMAZON_S3 = None


def _build_client(properties: OssSection) -> Any:
    """Java: ``OssTemplate#afterPropertiesSet()``。"""
    try:
        import boto3  # 延迟导入：没装 requirements-middleware.txt 也能启动服务
        from botocore.client import Config
    except ImportError as exc:  # pragma: no cover - 依赖装全时不会走到
        raise RuntimeError(
            "缺少 boto3（OSS/S3 支持），请安装 requirements-middleware.txt"
        ) from exc

    config = Config(
        # Java: clientConfiguration.setMaxConnections(...)
        max_pool_connections=properties.max_connections,
        signature_version="s3v4",
        s3={
            # Java: withPathStyleAccessEnabled(true/false)
            "addressing_style": "path" if properties.path_style_access else "virtual"
        },
    )
    return boto3.client(
        "s3",
        endpoint_url=properties.endpoint,
        aws_access_key_id=properties.access_key,
        aws_secret_access_key=properties.secret_key,
        # Java: EndpointConfiguration(endpoint, region)；yml 里没配 region（null），
        # botocore 需要一个具体的签名区域，缺省与 AWS 客户端一致用 us-east-1。
        region_name=properties.region or "us-east-1",
        config=config,
    )


# --------------------------------------------------------------------------- OssTemplate


class OssTemplate:
    """Java: ``class OssTemplate``."""

    def __init__(self, oss_properties: Optional[OssSection] = None) -> None:
        self._oss_properties = oss_properties

    @property
    def oss_properties(self) -> OssSection:
        if self._oss_properties is None:
            self._oss_properties = get_settings().oss
        return self._oss_properties

    # Java: public void afterPropertiesSet()
    def after_properties_set(self) -> None:
        """Java: ``InitializingBean#afterPropertiesSet`` —— 提前建好 client。

        Python 侧**不**在启动时调用它（见模块 docstring）；保留方法名是为了让
        "谁初始化了 client" 这件事在源码里仍然找得到。
        """
        global _AMAZON_S3
        _AMAZON_S3 = _build_client(self.oss_properties)

    # Java: public void createBucket(String bucketName)
    def create_bucket(self, bucket_name: str) -> None:
        """Java: ``if (!amazonS3.doesBucketExistV2(bucketName)) createBucket(...)``."""
        client = get_amazon_s3()
        if not _bucket_exists(client, bucket_name):
            client.create_bucket(Bucket=bucket_name)

    # Java: public List<Bucket> getAllBuckets()
    def get_all_buckets(self) -> List[Bucket]:
        response = get_amazon_s3().list_buckets()
        return [
            Bucket(bucket.get("Name"), bucket.get("CreationDate"))
            for bucket in response.get("Buckets", [])
        ]

    # Java: public Optional<Bucket> getBucket(String bucketName)
    def get_bucket(self, bucket_name: str) -> Optional[Bucket]:
        for bucket in self.get_all_buckets():
            if bucket.name == bucket_name:
                return bucket
        return None

    # Java: public void removeBucket(String bucketName)
    def remove_bucket(self, bucket_name: str) -> None:
        get_amazon_s3().delete_bucket(Bucket=bucket_name)

    # Java: public List<S3ObjectSummary> getAllObjectsByPrefix(String, String, boolean)
    def get_all_objects_by_prefix(
        self, bucket_name: str, prefix: str, recursive: bool
    ) -> List[Dict[str, Any]]:
        """``recursive`` 在 Java 里**没被使用**（原版忽略了它），照抄。"""
        response = get_amazon_s3().list_objects(Bucket=bucket_name, Prefix=prefix)
        return list(response.get("Contents", []))

    # Java: public String getObjectURL(String bucketName, String objectName, Integer expires)
    def get_object_url(self, bucket_name: str, object_name: str, expires: int) -> str:
        """``expires`` 的单位是**天**（Java: ``Calendar.add(DAY_OF_MONTH, expires)``）。"""
        return get_amazon_s3().generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": object_name},
            ExpiresIn=int(expires) * 24 * 60 * 60,
        )

    # Java: public S3Object getObjectInfo(String bucketName, String objectName)
    def get_object_info(self, bucket_name: str, object_name: str) -> S3Object:
        return _get_object(bucket_name, object_name)

    # Java: public static S3Object getObject(String bucketName, String objectName)
    @staticmethod
    def get_object(bucket_name: str, object_name: str) -> S3Object:
        return _get_object(bucket_name, object_name)

    # Java: public static void putObject(String bucketName, String objectName, InputStream stream)
    @staticmethod
    def put_object(
        bucket_name: str, object_name: str, stream: BinaryIO, size: Optional[int] = None,
        content_type: Optional[str] = None,
    ) -> Any:
        """Java 的两个 ``putObject`` 重载合成一个方法（后两个参数可选）。

        Java 3 参版本等价于::

            putObject(bucketName, objectName, stream, (long) stream.available(),
                      "application/octet-stream");
        """
        if size is None:
            size = _available(stream)
        if content_type is None:
            content_type = DEFAULT_CONTENT_TYPE
        return _put_object(bucket_name, object_name, stream, size, content_type)

    # Java: public static PutObjectResult putObject(String, String, InputStream, long, String)
    @staticmethod
    def put_object_with_meta(
        bucket_name: str, object_name: str, stream: BinaryIO, size: int, content_type: str
    ) -> Any:
        return _put_object(bucket_name, object_name, stream, size, content_type)

    # Java: public static void removeObject(String bucketName, String objectName)
    @staticmethod
    def remove_object(bucket_name: str, object_name: Optional[str]) -> None:
        get_amazon_s3().delete_object(Bucket=bucket_name, Key=object_name)


# --------------------------------------------------------------------------- 内部


def _available(stream: BinaryIO) -> int:
    """Java: ``InputStream#available()`` —— 可读的剩余字节数（尽力而为）。"""
    try:
        position = stream.tell()
        stream.seek(0, 2)
        end = stream.tell()
        stream.seek(position)
        return int(end - position)
    except (AttributeError, OSError, ValueError):
        # 不可 seek 的流：Java 的 available() 同样只是"估计值"，这里退回 0。
        return 0


def _get_object(bucket_name: str, object_name: str) -> S3Object:
    response = get_amazon_s3().get_object(Bucket=bucket_name, Key=object_name)
    return S3Object(
        response["Body"],
        bucket_name=bucket_name,
        key=object_name,
        content_type=response.get("ContentType"),
        content_length=response.get("ContentLength"),
    )


def _put_object(
    bucket_name: str, object_name: str, stream: BinaryIO, size: int, content_type: str
) -> Any:
    """Java: ``IOUtils.toByteArray(stream)`` + ``ObjectMetadata`` + ``amazonS3.putObject``.

    先把流转成字节（Java 也这么做），再上传。``size`` 与真实字节数不一致时以真实字节数
    为准 —— Java 会把 ``size`` 塞进 ``Content-Length``，长度对不上时 S3 直接拒绝；这里
    只在上限内纠正这个"必然失败"的情形，可观察结果（要么成功、要么抛错）不变。
    """
    data = stream.read()
    content_length = int(size) if size is not None and int(size) == len(data) else len(data)
    return get_amazon_s3().put_object(
        Bucket=bucket_name,
        Key=object_name,
        Body=data,
        ContentLength=content_length,
        ContentType=content_type,
    )


def _bucket_exists(client: Any, bucket_name: str) -> bool:
    """Java: ``AmazonS3#doesBucketExistV2`` —— 桶不存在时返回 ``False`` 而不是抛错。

    botocore 的 ``head_bucket`` 对 404 抛 ``ClientError``，这里吃成 ``False``。
    """
    from botocore.exceptions import ClientError  # 延迟导入，配合 boto3 一起

    try:
        client.head_bucket(Bucket=bucket_name)
        return True
    except ClientError:
        return False


__all__ = [
    "Bucket",
    "S3Object",
    "OssTemplate",
    "DEFAULT_CONTENT_TYPE",
    "get_amazon_s3",
    "reset_amazon_s3",
]
