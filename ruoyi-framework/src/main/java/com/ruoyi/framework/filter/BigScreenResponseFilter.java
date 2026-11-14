package com.ruoyi.framework.filter;

import com.ruoyi.common.core.cache.CacheContext;
import com.ruoyi.common.core.cache.CacheMeta;
import org.springframework.util.DigestUtils;
import org.springframework.web.filter.OncePerRequestFilter;
import org.springframework.web.util.ContentCachingResponseWrapper;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

/**
 * 大屏 GET 响应过滤器：统一输出 ETag/304 与缓存/降级响应头。
 *
 * <ul>
 *   <li>{@code ETag} + {@code If-None-Match} → 304，减少轮询带宽；</li>
 *   <li>{@code X-Cache}：L1/L2/MISS/STALE/DEGRADED；</li>
 *   <li>{@code X-Data-Age}：数据年龄（秒）；</li>
 *   <li>{@code X-Degrade}：降级原因（api/redis 不可用等）；</li>
 *   <li>{@code X-Data-As-Of}：数据截止时间。</li>
 * </ul>
 *
 * <p>下载接口（流式）不参与缓冲与 ETag。</p>
 *
 * @author car-monit-backend-java-v3
 */
public class BigScreenResponseFilter extends OncePerRequestFilter
{
    private static final String PREFIX = "/manager/bigScreen";

    private static final String DOWNLOAD_PATH = "/export/download/";

    @Override
    protected boolean shouldNotFilter(HttpServletRequest request)
    {
        if (!"GET".equalsIgnoreCase(request.getMethod()))
        {
            return true;
        }
        String uri = request.getRequestURI();
        String contextPath = request.getContextPath();
        if (contextPath != null && !contextPath.isEmpty() && uri.startsWith(contextPath))
        {
            uri = uri.substring(contextPath.length());
        }
        return !uri.startsWith(PREFIX) || uri.contains(DOWNLOAD_PATH);
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response,
                                    FilterChain filterChain) throws ServletException, IOException
    {
        CacheContext.clear();
        ContentCachingResponseWrapper wrapper = new ContentCachingResponseWrapper(response);
        try
        {
            filterChain.doFilter(request, wrapper);
        }
        finally
        {
            byte[] body = wrapper.getContentAsByteArray();
            CacheMeta meta = CacheContext.peek();
            if (response.getStatus() == HttpServletResponse.SC_OK)
            {
                String etag = "\"" + DigestUtils.md5DigestAsHex(body) + "\"";
                response.setHeader("ETag", etag);
                response.setHeader("Cache-Control", "private, max-age=" + maxAge(request.getRequestURI())
                        + ", must-revalidate");
                response.setHeader("Access-Control-Expose-Headers",
                        "ETag, X-Data-Age, X-Cache, X-Degrade, X-Data-As-Of, X-Data-Source");
                writeMetaHeaders(response, meta);

                String ifNoneMatch = request.getHeader("If-None-Match");
                if (etag.equals(ifNoneMatch))
                {
                    wrapper.resetBuffer();
                    response.setStatus(HttpServletResponse.SC_NOT_MODIFIED);
                }
            }
            wrapper.copyBodyToResponse();
            CacheContext.clear();
        }
    }

    private void writeMetaHeaders(HttpServletResponse response, CacheMeta meta)
    {
        if (meta == null)
        {
            return;
        }
        if (meta.getLevel() != null)
        {
            response.setHeader("X-Cache", meta.getLevel());
        }
        response.setHeader("X-Data-Age", String.valueOf(meta.getDataAgeSeconds()));
        if (meta.getSource() != null)
        {
            response.setHeader("X-Data-Source", meta.getSource());
        }
        if (meta.getDegradeReason() != null)
        {
            response.setHeader("X-Degrade", meta.getDegradeReason());
        }
        if (meta.getDataAsOf() != null)
        {
            response.setHeader("X-Data-As-Of", format(meta.getDataAsOf()));
        }
    }

    private String format(Date date)
    {
        SimpleDateFormat format = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ssXXX", Locale.CHINA);
        return format.format(date);
    }

    private int maxAge(String uri)
    {
        if (uri.contains("/export/status/"))
        {
            return 5;
        }
        if (uri.contains("/sectionList") || uri.contains("/tollGantryFwqList")
                || uri.contains("/orgList"))
        {
            return 300;
        }
        if (uri.contains("/carLocation") || uri.contains("/carWarning"))
        {
            return 10;
        }
        return 30;
    }
}
