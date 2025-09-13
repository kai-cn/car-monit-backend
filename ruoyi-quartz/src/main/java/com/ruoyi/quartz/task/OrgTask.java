package com.ruoyi.quartz.task;

import cn.hutool.core.collection.CollectionUtil;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.ruoyi.base.domain.OdsYhglVBaseOrg;
import com.ruoyi.base.service.IOdsYhglVBaseOrgService;
import com.ruoyi.common.core.domain.entity.SysDept;
import com.ruoyi.common.utils.DateUtils;
import com.ruoyi.system.service.ISysDeptService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.util.Collections;
import java.util.List;
import java.util.stream.Collectors;

@Component("orgTask")
public class OrgTask {


    @Autowired
    private IOdsYhglVBaseOrgService odsYhglVBaseOrgService;

    @Autowired
    private ISysDeptService sysDeptService;


    @Transactional(rollbackFor = Exception.class)
    public void syncOrgInfo() {
        // 查询同步的组织数据
        OdsYhglVBaseOrg orgbo = new OdsYhglVBaseOrg();
        List<OdsYhglVBaseOrg> list = odsYhglVBaseOrgService.selectOdsYhglVBaseOrgList(orgbo);
        if(CollectionUtil.isEmpty(list)){
            return ;
        }

        // 只查询江西省交通投资集团有限责任公司下的数据
        List<SysDept> sysDeptList = list.stream().filter(v -> "00000011005399999999".equals(v.getOrgLevelCode()) || v.getOrgLevelCode().contains("0000001100530008")).map(v -> {
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
    }
}
