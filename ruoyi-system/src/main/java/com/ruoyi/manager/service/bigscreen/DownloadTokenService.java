package com.ruoyi.manager.service.bigscreen;

import com.ruoyi.integration.api.ApiClientException;
import com.ruoyi.integration.api.ApiErrorCode;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import javax.annotation.PostConstruct;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Base64;

/**
 * 导出下载签名：HMAC-SHA256，令牌绑定 taskId + userId，默认 15 分钟有效。
 *
 * <p>设计文档 §5.5.2「签名 URL（15 分钟）、绑定 taskId + 用户」。令牌只做归属与时效校验，
 * 下载仍需登录态（SecurityConfig 默认 anyRequest authenticated）。</p>
 *
 * <p><b>密钥必须独立配置</b>：{@code export.download.secret} 不允许回退到 {@code token.secret}
 * 或任何内置默认值；未配置时应用启动失败（fail-fast），避免用公开默认密钥伪造下载令牌。</p>
 *
 * @author car-monit-backend-java-v3
 */
@Service
public class DownloadTokenService
{
    private static final String HMAC_ALGORITHM = "HmacSHA256";

    /** 禁止使用的历史默认值（曾回退到 token.secret 的默认串）。 */
    private static final String LEGACY_DEFAULT_SECRET = "abcdefghijklmnopqrstuvwxyz";

    private static final int MIN_SECRET_LENGTH = 16;

    @Value("${export.download.secret:}")
    private String secret;

    @Value("${export.download.token-ttl-seconds:900}")
    private long tokenTtlSeconds;

    @PostConstruct
    public void checkSecret()
    {
        String value = secret == null ? "" : secret.trim();
        if (value.isEmpty())
        {
            throw new IllegalStateException(
                    "缺少导出下载签名密钥：请配置 export.download.secret（或环境变量 EXPORT_DOWNLOAD_SECRET）");
        }
        if (LEGACY_DEFAULT_SECRET.equals(value))
        {
            throw new IllegalStateException(
                    "导出下载签名密钥不能使用内置默认值，请配置独立的 export.download.secret");
        }
        if (value.length() < MIN_SECRET_LENGTH)
        {
            throw new IllegalStateException(
                    "导出下载签名密钥长度不足 " + MIN_SECRET_LENGTH + " 位，请配置更强的 export.download.secret");
        }
        this.secret = value;
    }

    public String sign(String taskId, Long userId)
    {
        long expireAt = System.currentTimeMillis() / 1000L + tokenTtlSeconds;
        String payload = taskId + "|" + userId + "|" + expireAt;
        String data = Base64.getUrlEncoder().withoutPadding()
                .encodeToString(payload.getBytes(StandardCharsets.UTF_8));
        return data + "." + hmac(data);
    }

    /**
     * @return 令牌中的 userId
     */
    public Long verify(String token, String taskId)
    {
        if (token == null || token.trim().isEmpty())
        {
            throw new ApiClientException(ApiErrorCode.FORBIDDEN, "exportDownload", "缺少下载令牌");
        }
        String[] parts = token.split("\\.");
        if (parts.length != 2)
        {
            throw new ApiClientException(ApiErrorCode.FORBIDDEN, "exportDownload", "下载令牌格式非法");
        }
        String expected = hmac(parts[0]);
        if (!MessageDigest.isEqual(expected.getBytes(StandardCharsets.UTF_8),
                parts[1].getBytes(StandardCharsets.UTF_8)))
        {
            throw new ApiClientException(ApiErrorCode.FORBIDDEN, "exportDownload", "下载令牌签名校验失败");
        }
        String payload = new String(Base64.getUrlDecoder().decode(parts[0]), StandardCharsets.UTF_8);
        String[] fields = payload.split("\\|");
        if (fields.length != 3)
        {
            throw new ApiClientException(ApiErrorCode.FORBIDDEN, "exportDownload", "下载令牌内容非法");
        }
        if (!fields[0].equals(taskId))
        {
            throw new ApiClientException(ApiErrorCode.FORBIDDEN, "exportDownload", "下载令牌与任务不匹配");
        }
        long expireAt = Long.parseLong(fields[2]);
        if (System.currentTimeMillis() / 1000L > expireAt)
        {
            throw new ApiClientException(ApiErrorCode.FORBIDDEN, "exportDownload", "下载令牌已过期");
        }
        return Long.valueOf(fields[1]);
    }

    public long getTokenTtlSeconds()
    {
        return tokenTtlSeconds;
    }

    private String hmac(String data)
    {
        try
        {
            Mac mac = Mac.getInstance(HMAC_ALGORITHM);
            mac.init(new SecretKeySpec(secret.getBytes(StandardCharsets.UTF_8), HMAC_ALGORITHM));
            byte[] bytes = mac.doFinal(data.getBytes(StandardCharsets.UTF_8));
            StringBuilder hex = new StringBuilder();
            for (byte b : bytes)
            {
                hex.append(String.format("%02x", b));
            }
            return hex.toString();
        }
        catch (Exception e)
        {
            throw new ApiClientException(ApiErrorCode.UPSTREAM_ERROR, "exportDownload",
                    "下载令牌生成失败", e);
        }
    }
}
