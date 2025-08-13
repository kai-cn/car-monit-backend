package com.ruoyi.common.flow;

import com.ruoyi.common.utils.StringUtils;
import com.ruoyi.common.utils.spring.SpringUtils;

import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/**
 * @author gl
 * @version 1.0
 * @description
 * @date 2023/2/27 9:54
 */

public class AuditContext {

    /**
     * Spring容器中实现了Audit接口的实现类的集合
     */
    private static List<Audit> auditList;

    /**
     * 空串
     */
    private static final String EMPTY_STRING = "";

    private AuditContext() {}

    /**
     * 获取-Spring容器中实现了Audit接口的实现类的集合
     * @return
     */
    public static List<Audit> getAuditList() {
        if (auditList == null) {
            initAuditList();
        }

        return auditList;
    }

    /**
     * 处理结束回调
     * @param flowKey 流程key
     * @param businessId 业务id
     * @param flowStatus 流程状态
     */
    public static void handleEnd(String flowKey, String businessId, String flowStatus) {
        // 加载auditList数据
        List<Audit> dataList = getAuditList();
        if (dataList != null && !dataList.isEmpty() &&
                flowKey != null && !Objects.equals(flowKey, EMPTY_STRING)) {

            for (Audit audit : dataList) {
                boolean result = doHandleEnd(flowKey, businessId, flowStatus, audit);
                if (result) {
                    // 如果找到了对应的流程, 那么则不需要继续遍历
                    break;
                }
            }
        }
    }

    /**
     * 初始化-Spring容器中实现了Audit接口的实现类的集合
     */
    private static void initAuditList() {
        Map<String, Audit> auditMap = SpringUtils.getBeanOfType(Audit.class);
        if (auditMap.isEmpty()) {
            auditList = new ArrayList<>(16);
        } else {
            auditList = new ArrayList<>(auditMap.values());
        }
    }

    /**
     * 处理结束回调
     * @param flowKey
     * @param businessId
     * @param flowStatus
     * @param audit
     * @return true => 找到了, false => 未找到
     */
    private static boolean doHandleEnd(String flowKey, String businessId, String flowStatus, Audit audit) {
        boolean result = false;
        if (StringUtils.isAnyBlank(flowKey, businessId, flowStatus) || audit == null) {
            return false;
        }

        // key => flowKey, value => 对应的处理函数
        Map<String, String> dealMap = audit.getDealMap();
        for (Map.Entry<String, String> entry : dealMap.entrySet()) {
            if (Objects.equals(entry.getKey(), flowKey)) {
                try {
                    Method method = audit.getClass().getDeclaredMethod(entry.getValue(), String.class, String.class);
                    // 调用处理函数
                    method.invoke(audit, businessId, flowStatus);
                    result = true;
                } catch (Exception exception) {
                    exception.printStackTrace();
                }

                break;
            }
        }

        return result;
    }

}
