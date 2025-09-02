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
        List<OdsYhglVBaseOrg> list = odsYhglVBaseOrgService.list();
        if(CollectionUtil.isEmpty(list)){
            return ;
        }

        List<SysDept> sysDeptList = list.stream().map(v -> {
            SysDept sysDept = new SysDept();
            sysDept.setOrgCode(v.getOrgCode());
            sysDept.setParentId(v.getOrgParentId());
            sysDept.setDeptName(v.getOrgName());
            sysDept.setSubCode(v.getOrgLevelCode());
            sysDept.setDeptJc(v.getOrgShortName());
            sysDept.setDelFlag(v.getOrgIsDeleted());
            sysDept.setCreateBy("admin");
            sysDept.setCreateTime(DateUtils.getTimestamp());
            sysDept.setUpdateTime(DateUtils.getTimestamp());
            return sysDept;
        }).collect(Collectors.toList());


        this.sysDeptService.deleteTableData();
        this.sysDeptService.saveOrUpdateBatch(sysDeptList);
    }
}
