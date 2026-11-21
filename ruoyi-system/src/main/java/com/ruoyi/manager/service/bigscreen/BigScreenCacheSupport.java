package com.ruoyi.manager.service.bigscreen;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;

/**
 * 大屏缓存 key 辅助工具：参数指纹使用 SHA-256 前 24 位，避免简单 hashCode 碰撞造成跨参数复用。
 *
 * @author car-monit-backend-java-v3
 */
public final class BigScreenCacheSupport
{
    private BigScreenCacheSupport()
    {
    }

    public static String hash(Object... parts)
    {
        StringBuilder sb = new StringBuilder();
        if (parts != null)
        {
            for (Object part : parts)
            {
                sb.append(part == null ? "" : String.valueOf(part)).append('|');
            }
        }
        try
        {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] bytes = digest.digest(sb.toString().getBytes(StandardCharsets.UTF_8));
            StringBuilder hex = new StringBuilder();
            for (byte b : bytes)
            {
                hex.append(String.format("%02x", b));
            }
            return hex.substring(0, 24);
        }
        catch (NoSuchAlgorithmException e)
        {
            return Integer.toHexString(sb.toString().hashCode());
        }
    }

    public static String text(String value)
    {
        return value == null ? "" : value.trim();
    }
}
