"""组织（部门）信息同步 bean（``@Component("orgTask")``）.

# Migrated from: ruoyi-quartz/src/main/java/com/ruoyi/quartz/task/OrgTask.java

**方法体整段被注释掉了，所以这是个空任务。** 线上 ``sys_job`` 里确实有一行
``orgTask.syncOrgInfo``（组 ``SYSTEM``），每次触发都只是"进方法 -> 立刻返回"，
不产生任何副作用。

按"不删除看似无用的代码"的原则，这里保留：
* 两个 ``@Autowired`` 依赖的声明（``odsYhglVBaseOrgService`` / ``sysDeptService``，
  在 Java 里**从未被使用**，只是注入）；
* 被注释掉的那 30 行原文（改成 Python 注释），因为它记录着原本的业务规则：
  "只同步 ``00000011005399999999`` 与 ``0000001100530008*`` 两个组织下的数据，
  ``deptId`` 取 ``bigId``"。

为什么是注释而不是代码
----------------------
``@Transactional(rollbackFor = Exception.class)`` 挂在一个**空方法**上 —— 事务会开，
然后什么都不做就提交。Python 侧同样什么都不做（连事务都不开，因为没有语句）。

依赖注入的处理
--------------
Java 的两个字段只用于让 Spring 装配成功；Python 里不需要构造参数。为了让
:mod:`app.quartz.task` 的注册表与 Spring 的 Bean 图一一对应，这里用属性暴露
两个协作对象的**取值函数**（惰性 import，避免 ``app.system`` <- ``app.quartz``
的循环导入）。
"""

from __future__ import annotations

from typing import Any, Optional
from app.config.database import transactional

#: Java: ``@Component("orgTask")``
BEAN_NAME = "orgTask"


class OrgTask:
    """Java: ``class OrgTask``（``@Component("orgTask")``）."""

    def __init__(
        self,
        ods_yhgl_v_base_org_service: Optional[Any] = None,
        sys_dept_service: Optional[Any] = None,
    ) -> None:
        # Java: @Autowired private IOdsYhglVBaseOrgService odsYhglVBaseOrgService;
        # Java: @Autowired private ISysDeptService sysDeptService;
        # 两个字段在 Java 里**从未被引用**（唯一用到它们的那段代码被注释了）。
        self._ods_yhgl_v_base_org_service_override = ods_yhgl_v_base_org_service
        self._sys_dept_service_override = sys_dept_service

    # Java: @Autowired private IOdsYhglVBaseOrgService odsYhglVBaseOrgService
    @property
    def ods_yhgl_v_base_org_service(self) -> Any:
        if self._ods_yhgl_v_base_org_service_override is not None:
            return self._ods_yhgl_v_base_org_service_override
        from app.base.service.ods_yhgl_v_base_org_service import (
            get_ods_yhgl_v_base_org_service,
        )

        return get_ods_yhgl_v_base_org_service()

    # Java: @Autowired private ISysDeptService sysDeptService
    @property
    def sys_dept_service(self) -> Any:
        if self._sys_dept_service_override is not None:
            return self._sys_dept_service_override
        from app.system.service.sys_dept_service import get_dept_service

        return get_dept_service()

    # Java: @Transactional(rollbackFor = Exception.class) public void syncOrgInfo()
    @transactional
    def sync_org_info(self) -> None:
        """同步组织信息 —— **空方法体**，Java 原文整段被注释.

        Java 原文（保留以便日后恢复，行为等价于"什么都不做"）::

            // 查询同步的组织数据
            OdsYhglVBaseOrg orgbo = new OdsYhglVBaseOrg();
            List<OdsYhglVBaseOrg> list = odsYhglVBaseOrgService.selectOdsYhglVBaseOrgList(orgbo);
            if (CollectionUtil.isEmpty(list)) {
                return;
            }

            // 只查询江西省交通投资集团有限责任公司下的数据
            List<SysDept> sysDeptList = list.stream()
                .filter(v -> "00000011005399999999".equals(v.getOrgLevelCode())
                          || v.getOrgLevelCode().contains("0000001100530008"))
                .map(v -> {
                    SysDept sysDept = new SysDept();
                    sysDept.setDeptId(Long.parseLong(v.getBigId()));
                    sysDept.setParentId(v.getParentId());
                    sysDept.setDeptName(v.getOrgName());
                    sysDept.setSubCode(v.getOrgLevelCode());
                    sysDept.setDeptJc(v.getOrgShortName());
                    sysDept.setDelFlag(v.getOrgIsDeleted());

                    // 部门编码
                    sysDept.setSocialCode(v.getOrgCode());
                    // 父编码
                    sysDept.setPostalCode(v.getOrgParentId());

                    sysDept.setCreateBy("-9999");
                    sysDept.setCreateTime(DateUtils.getTimestamp());
                    sysDept.setUpdateTime(DateUtils.getTimestamp());
                    return sysDept;
                }).collect(Collectors.toList());
            this.sysDeptService.saveAll(sysDeptList);
        """


__all__ = ["BEAN_NAME", "OrgTask"]
