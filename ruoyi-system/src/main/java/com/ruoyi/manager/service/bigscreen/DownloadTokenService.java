package com.ruoyi.manager.service.bigscreen;

import com.ruoyi.integration.api.ApiClientException;
import com.ruoyi.integration.api.ApiErrorCode;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

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
 * @author car-monit-backend-java-v3
 */
@Service
public class DownloadTokenService
{
    private static final String HMAC_ALGORITHM = "HmacSHA256";

    @Value("${export.download.secret:${token.secret:abcdefghijklmnopqrstuvwxyz}}")
    private String secret;

    @Value("${export.download.token-ttl-seconds:900}")
    private long tokenTtlSeconds;

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
