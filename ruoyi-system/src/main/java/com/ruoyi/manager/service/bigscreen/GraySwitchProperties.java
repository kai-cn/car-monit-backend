package com.ruoyi.manager.service.bigscreen;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * 灰度规则：按租户白名单或百分比切换（优先级：租户白名单 > 百分比）。
 *
 * <pre>
 * bigscreen:
 *   gray:
 *     stats-api-first:
 *       percent: 50
 *       tenants: ["1001", "1002"]
 * </pre>
 *
 * <p>百分比按 {@code 开关名+租户ID} 稳定哈希取桶，同一租户结果固定，避免大屏闪烁。</p>
 *
 * @author car-monit-backend-java-v3
 */
@Component
@ConfigurationProperties(prefix = "bigscreen.gray")
public class GraySwitchProperties
{
    private Map<String, Rule> rules = new LinkedHashMap<String, Rule>();

    public Map<String, Rule> getRules()
    {
        return rules;
    }

    public void setRules(Map<String, Rule> rules)
    {
        this.rules = rules == null ? new LinkedHashMap<String, Rule>() : rules;
    }

    public static class Rule
    {
        /** 放量百分比 0-100；100=全量，0=关闭 */
        private int percent = 100;

        /** 租户白名单；非空时仅这些租户命中 */
        private List<String> tenants = new ArrayList<String>();

        public int getPercent()
        {
            return percent;
        }

        public void setPercent(int percent)
        {
            this.percent = percent;
        }

        public List<String> getTenants()
        {
            return tenants;
        }

        public void setTenants(List<String> tenants)
        {
            this.tenants = tenants == null ? new ArrayList<String>() : tenants;
        }
    }
}
