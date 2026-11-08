package com.ruoyi.manager.service.bigscreen;

import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

/**
 * 全字段导出审批状态机。
 *
 * <p>状态：{@code pending}（待审批）→ {@code approving}（审批中，已抢占提交权）→
 * {@code approved}（已提交 api）/ {@code rejected}（已驳回）。</p>
 *
 * <p>审批提交不是幂等操作：api 会为每次提交生成新 taskId 与文件。
 * 因此先落 {@code approving} 再提交，用状态迁移把并发审批收敛为一次提交；
 * 提交失败时回退 {@code pending} 允许重试。</p>
 *
 * @author car-monit-backend-java-v3
 */
public final class ExportApprovalStateMachine
{
    public static final String PENDING = "pending";

    public static final String APPROVING = "approving";

    public static final String APPROVED = "approved";

    public static final String REJECTED = "rejected";

    private static final Map<String, Set<String>> TRANSITIONS;

    static
    {
        Map<String, Set<String>> transitions = new HashMap<String, Set<String>>();
        transitions.put(PENDING, new HashSet<String>(Arrays.asList(APPROVING, REJECTED)));
        // approving -> approving：仅当 CAS 占位已过期（上一次进程中断）时用于恢复重试
        transitions.put(APPROVING, new HashSet<String>(Arrays.asList(APPROVED, PENDING, APPROVING)));
        transitions.put(APPROVED, Collections.<String>emptySet());
        transitions.put(REJECTED, Collections.<String>emptySet());
        TRANSITIONS = Collections.unmodifiableMap(transitions);
    }

    private ExportApprovalStateMachine()
    {
    }

    public static boolean canTransition(String from, String to)
    {
        if (from == null || to == null)
        {
            return false;
        }
        Set<String> targets = TRANSITIONS.get(from);
        return targets != null && targets.contains(to);
    }

    public static void assertTransition(String from, String to)
    {
        if (!canTransition(from, to))
        {
            throw new IllegalStateException("审批状态不允许从 " + from + " 迁移到 " + to);
        }
    }
}
