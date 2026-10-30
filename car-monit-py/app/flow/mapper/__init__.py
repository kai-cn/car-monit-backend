"""``com.ruoyi.flow.mapper`` —— 工作流 Mapper.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/flow/mapper/

与 manager / base 包不同：**flow 的 7 个 Mapper 接口都不继承 ``BaseMapper``**，
所有语句都写在 XML 里（``insertFlowXxx`` / ``updateFlowXxx`` / ``deleteFlowXxx``）。
因此这里的插入/更新必须按 XML 的 ``<if test="x != null">`` 逐列拼装，
**不能**直接套用 MyBatis-Plus 的 ``INSERT`` / ``UPDATE`` 语义
（否则会多出 ``MetaObjectHandler`` 自动填充、UUID 生成、``del_flag = '0'`` 条件）。
"""
