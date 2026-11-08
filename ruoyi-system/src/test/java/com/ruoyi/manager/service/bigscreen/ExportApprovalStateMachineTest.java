package com.ruoyi.manager.service.bigscreen;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * 审批状态机单测：保证 pending→approving→approved 的主链路，
 * 以及 approving 失败回退、终态不可再迁移（并发重复审批会被拒绝）。
 */
class ExportApprovalStateMachineTest
{
    @Test
    void pendingCanStartApprovalOrBeRejected()
    {
        assertTrue(ExportApprovalStateMachine.canTransition(
                ExportApprovalStateMachine.PENDING, ExportApprovalStateMachine.APPROVING));
        assertTrue(ExportApprovalStateMachine.canTransition(
                ExportApprovalStateMachine.PENDING, ExportApprovalStateMachine.REJECTED));
    }

    @Test
    void approvingCanFinishOrRollback()
    {
        assertTrue(ExportApprovalStateMachine.canTransition(
                ExportApprovalStateMachine.APPROVING, ExportApprovalStateMachine.APPROVED));
        assertTrue(ExportApprovalStateMachine.canTransition(
                ExportApprovalStateMachine.APPROVING, ExportApprovalStateMachine.PENDING));
        // CAS 过期后的中断恢复：允许重新进入 approving（仍由 Redis CAS 保证单飞）
        assertTrue(ExportApprovalStateMachine.canTransition(
                ExportApprovalStateMachine.APPROVING, ExportApprovalStateMachine.APPROVING));
    }

    @Test
    void pendingCannotJumpDirectlyToApproved()
    {
        // 必须先落 approving 再提交，否则并发审批会重复提交 api
        assertFalse(ExportApprovalStateMachine.canTransition(
                ExportApprovalStateMachine.PENDING, ExportApprovalStateMachine.APPROVED));
    }

    @Test
    void terminalStatesCannotTransitionAgain()
    {
        assertFalse(ExportApprovalStateMachine.canTransition(
                ExportApprovalStateMachine.APPROVED, ExportApprovalStateMachine.APPROVING));
        assertFalse(ExportApprovalStateMachine.canTransition(
                ExportApprovalStateMachine.REJECTED, ExportApprovalStateMachine.APPROVING));
        assertFalse(ExportApprovalStateMachine.canTransition(
                ExportApprovalStateMachine.APPROVED, ExportApprovalStateMachine.REJECTED));
    }

    @Test
    void assertTransitionThrowsForIllegalMove()
    {
        assertThrows(IllegalStateException.class,
                () -> ExportApprovalStateMachine.assertTransition(
                        ExportApprovalStateMachine.PENDING, ExportApprovalStateMachine.APPROVED));
    }
}
