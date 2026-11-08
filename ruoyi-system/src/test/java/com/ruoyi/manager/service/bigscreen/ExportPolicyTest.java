package com.ruoyi.manager.service.bigscreen;

import com.ruoyi.integration.api.ApiClientException;
import com.ruoyi.integration.api.ApiErrorCode;
import org.junit.jupiter.api.Test;

import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * 导出策略单测：机构范围收敛、过滤字段白名单、展示字段策略。
 */
class ExportPolicyTest
{
    // ------------------------------------------------------------------
    // 机构范围收敛（P0）
    // ------------------------------------------------------------------

    @Test
    void nonAdminWithoutOrgCodeGetsScopeInjected()
    {
        Map<String, String> result = ExportPolicy.applyOrgScope("snapshot", null, false, "3601");
        assertEquals("3601", result.get("orgcode"));
    }

    @Test
    void nonAdminKeepsOtherFiltersAndInjectsScope()
    {
        Map<String, String> input = new LinkedHashMap<String, String>();
        input.put("platenumber", "赣A12345");
        Map<String, String> result = ExportPolicy.applyOrgScope("fee", input, false, "3601");
        assertEquals("赣A12345", result.get("platenumber"));
        assertEquals("3601", result.get("orgcode"));
    }

    @Test
    void nonAdminCannotExportOtherOrg()
    {
        Map<String, String> input = new LinkedHashMap<String, String>();
        input.put("orgCode", "9999");
        ApiClientException e = assertThrows(ApiClientException.class,
                () -> ExportPolicy.applyOrgScope("snapshot", input, false, "3601"));
        assertEquals(ApiErrorCode.FORBIDDEN, e.getCode());
    }

    @Test
    void nonAdminOrgCodeOverridesCaseVariantAndIsCanonical()
    {
        Map<String, String> input = new LinkedHashMap<String, String>();
        input.put("OrgCode", "3601");
        Map<String, String> result = ExportPolicy.applyOrgScope("snapshot", input, false, "3601");
        assertEquals("3601", result.get("orgcode"));
        assertFalse(result.containsKey("OrgCode"));
    }

    @Test
    void nonAdminWithoutBoundOrgIsRejected()
    {
        ApiClientException e = assertThrows(ApiClientException.class,
                () -> ExportPolicy.applyOrgScope("snapshot", null, false, "-1"));
        assertEquals(ApiErrorCode.FORBIDDEN, e.getCode());
        assertThrows(ApiClientException.class,
                () -> ExportPolicy.applyOrgScope("snapshot", null, false, " "));
    }

    @Test
    void nonAdminTrailExportIsRejectedBecauseApiHasNoScopeDimension()
    {
        ApiClientException e = assertThrows(ApiClientException.class,
                () -> ExportPolicy.applyOrgScope("trail", null, false, "3601"));
        assertEquals(ApiErrorCode.FORBIDDEN, e.getCode());
    }

    @Test
    void adminKeepsExplicitOrgCodeButIsNotForced()
    {
        Map<String, String> input = new LinkedHashMap<String, String>();
        input.put("orgcode", "9999");
        assertEquals("9999", ExportPolicy.applyOrgScope("trail", input, true, "3601").get("orgcode"));
        assertFalse(ExportPolicy.applyOrgScope("snapshot", null, true, "3601").containsKey("orgcode"));
    }

    // ------------------------------------------------------------------
    // 过滤字段白名单（P1-6）
    // ------------------------------------------------------------------

    @Test
    void unknownFuzzyFieldIsRejectedInsteadOfSilentlyExportingAll()
    {
        Map<String, String> input = new LinkedHashMap<String, String>();
        input.put("unknownField", "abc");
        ApiClientException e = assertThrows(ApiClientException.class,
                () -> ExportPolicy.validateFuzzy(input));
        assertEquals(ApiErrorCode.INVALID_ARGUMENT, e.getCode());
    }

    @Test
    void plateColorSingleCharacterIsAllowedAsExactField()
    {
        Map<String, String> input = new LinkedHashMap<String, String>();
        input.put("plateColor", "1");
        ExportPolicy.validateFuzzy(input);
        input.clear();
        input.put("plate_color", "2");
        ExportPolicy.validateFuzzy(input);
    }

    @Test
    void orgCodeAndDimensionCodesAllowShortExactValues()
    {
        Map<String, String> input = new LinkedHashMap<String, String>();
        input.put("orgcode", "36");
        input.put("sectioncode", "1");
        input.put("gantryid", "G1");
        ExportPolicy.validateFuzzy(input);
    }

    @Test
    void plateNumberStillRequiresTwoCharacters()
    {
        Map<String, String> input = new LinkedHashMap<String, String>();
        input.put("platenumber", "赣");
        ApiClientException e = assertThrows(ApiClientException.class,
                () -> ExportPolicy.validateFuzzy(input));
        assertEquals(ApiErrorCode.INVALID_ARGUMENT, e.getCode());
    }

    @Test
    void overlyLongFilterValueIsRejected()
    {
        char[] chars = new char[65];
        Arrays.fill(chars, 'a');
        Map<String, String> input = new LinkedHashMap<String, String>();
        input.put("orgname", new String(chars));
        assertThrows(ApiClientException.class, () -> ExportPolicy.validateFuzzy(input));
    }

    // ------------------------------------------------------------------
    // 展示字段策略
    // ------------------------------------------------------------------

    @Test
    void blockedDisplayFieldIsRejected()
    {
        ApiClientException e = assertThrows(ApiClientException.class,
                () -> ExportPolicy.resolveDisplayFields("snapshot",
                        Arrays.asList("platenumber", "trailpoints"), false));
        assertEquals(ApiErrorCode.INVALID_ARGUMENT, e.getCode());
    }

    @Test
    void plateColorNameAddedForSnapshotWhenApiSupportsIt()
    {
        List<String> fields = ExportPolicy.resolveDisplayFields("snapshot", null, true);
        assertTrue(fields.contains("plate_color_name"));
    }

    @Test
    void plateColorNameNotAddedWhenApiDoesNotSupportIt()
    {
        List<String> fields = ExportPolicy.resolveDisplayFields("snapshot", null, false);
        assertFalse(fields.contains("plate_color_name"));
    }

    @Test
    void plateColorNameRejectedForTrailDisplayExport()
    {
        assertThrows(ApiClientException.class, () -> ExportPolicy.resolveDisplayFields("trail",
                Arrays.asList("plate_color_name"), true));
    }

    @Test
    void fullFiltersRejectFieldNotInApiCapabilityMatrix()
    {
        Map<String, String> input = new LinkedHashMap<String, String>();
        input.put("orgcode", "3601");
        // none()：api 未声明任何维度能力
        assertThrows(ApiClientException.class, () -> ExportPolicy.validateFullFilters("snapshot",
                input, ExportCapabilityService.Capabilities.none()));
        // allSupported()：放行
        ExportPolicy.validateFullFilters("snapshot", input,
                ExportCapabilityService.Capabilities.allSupported());
    }
}
