package com.ruoyi.system.service.impl;

import com.ruoyi.common.annotation.DataScope;
import com.ruoyi.common.constant.UserConstants;
import com.ruoyi.common.core.domain.TreeSelect;
import com.ruoyi.common.core.domain.entity.SysDept;
import com.ruoyi.common.core.domain.entity.SysRole;
import com.ruoyi.common.utils.SecurityUtils;
import com.ruoyi.common.utils.StringUtils;
import com.ruoyi.system.mapper.SysDeptMapper;
import com.ruoyi.system.mapper.SysRoleMapper;
import com.ruoyi.system.service.ISysDeptService;
import org.apache.commons.collections4.CollectionUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;

/**
 * 部门管理 服务实现
 * 
 * @author ruoyi
 */
@Service
public class SysDeptServiceImpl implements ISysDeptService
{
    @Autowired
    private SysDeptMapper deptMapper;

    @Autowired
    private SysRoleMapper roleMapper;

    /**
     * 查询部门管理数据
     * 
     * @param dept 部门信息
     * @return 部门信息集合
     */
    @Override
    @DataScope(deptAlias = "d")
    public List<SysDept> selectDeptList(SysDept dept)
    {
        return deptMapper.selectDeptList(dept);
    }

    /**
     * 构建前端所需要树结构
     * 
     * @param depts 部门列表
     * @return 树结构列表
     */
    @Override
    public List<SysDept> buildDeptTree(List<SysDept> depts)
    {
        List<SysDept> returnList = new ArrayList<SysDept>();
        List<Long> tempList = new ArrayList<Long>();
        for (SysDept dept : depts)
        {
            tempList.add(dept.getDeptId());
        }
        for (Iterator<SysDept> iterator = depts.iterator(); iterator.hasNext();)
        {
            SysDept dept = (SysDept) iterator.next();
            // 如果是顶级节点, 遍历该父节点的所有子节点
            if (!tempList.contains(dept.getParentId()))
            {
                recursionFn(depts, dept);
                returnList.add(dept);
            }
        }
        if (returnList.isEmpty())
        {
            returnList = depts;
        }
        return returnList;
    }

    /**
     * 构建前端所需要下拉树结构
     * 
     * @param depts 部门列表
     * @return 下拉树结构列表
     */
    @Override
    public List<TreeSelect> buildDeptTreeSelect(List<SysDept> depts)
    {
        List<SysDept> deptTrees = buildDeptTree(depts);
        return deptTrees.stream().map(TreeSelect::new).collect(Collectors.toList());
    }

    /**
     * 根据角色ID查询部门树信息
     * 
     * @param roleId 角色ID
     * @return 选中部门列表
     */
    @Override
    public List<Integer> selectDeptListByRoleId(Long roleId)
    {
        SysRole role = roleMapper.selectRoleById(roleId);
        return deptMapper.selectDeptListByRoleId(roleId, role.isDeptCheckStrictly());
    }

    /**
     * 根据部门ID查询信息
     * 
     * @param deptId 部门ID
     * @return 部门信息
     */
    @Override
    public SysDept selectDeptById(Long deptId)
    {
        return deptMapper.selectDeptById(deptId);
    }

    /**
     * 根据ID查询所有子部门（正常状态）
     * 
     * @param deptId 部门ID
     * @return 子部门数
     */
    @Override
    public int selectNormalChildrenDeptById(Long deptId)
    {
        return deptMapper.selectNormalChildrenDeptById(deptId);
    }

    /**
     * 是否存在子节点
     * 
     * @param deptId 部门ID
     * @return 结果
     */
    @Override
    public boolean hasChildByDeptId(Long deptId)
    {
        int result = deptMapper.hasChildByDeptId(deptId);
        return result > 0 ? true : false;
    }

    /**
     * 查询部门是否存在用户
     * 
     * @param deptId 部门ID
     * @return 结果 true 存在 false 不存在
     */
    @Override
    public boolean checkDeptExistUser(Long deptId)
    {
        int result = deptMapper.checkDeptExistUser(deptId);
        return result > 0 ? true : false;
    }

    /**
     * 校验部门名称是否唯一
     * 
     * @param dept 部门信息
     * @return 结果
     */
    @Override
    public String checkDeptNameUnique(SysDept dept)
    {
        Long deptId = StringUtils.isNull(dept.getDeptId()) ? -1L : dept.getDeptId();
        SysDept info = deptMapper.checkDeptNameUnique(dept.getDeptName(), dept.getParentId());
        if (StringUtils.isNotNull(info) && info.getDeptId().longValue() != deptId.longValue())
        {
            return UserConstants.NOT_UNIQUE_OLD;
        }
        return UserConstants.UNIQUE_OLD;
    }

    /**
     * 新增保存部门信息
     * 
     * @param dept 部门信息
     * @return 结果
     */
    @Override
    @Transactional(rollbackFor = Exception.class)
    public int insertDept(SysDept dept)
    {
       /* SysDept info = deptMapper.selectDeptById(dept.getParentId());
        // 如果父节点不为正常状态,则不允许新增子节点
        *//*if (!UserConstants.DEPT_NORMAL.equals(info.getStatus()))
        {
            throw new CustomException("部门停用，不允许新增");
        }*//*
        dept.setAncestors(info.getAncestors() + "," + dept.getParentId());*/

        // 修改部门编码
        String parentSubCode = ""; //父节点code
        if (null == dept.getParentId())
        {
            dept.setParentId(0L);
            dept.setIsUint("1"); //顶级节点一定是单位
        }
        // 设置树级别
        if (dept.getParentId().equals(0L)) {
            dept.setTreeLeavel(1);
            parentSubCode = "001";
        } else {
            // 查询父节点
            SysDept parentBO = deptMapper.selectDeptById(dept.getParentId());
            dept.setTreeLeavel(parentBO.getTreeLeavel() + 1);
            parentSubCode = parentBO.getSubCode();
        }
        boolean flag = true;
        if (null !=dept.getDeptId())
        {
            SysDept tmpbo = deptMapper.selectDeptById(dept.getDeptId());
            if (tmpbo.getParentId().equals(dept.getParentId()) )
            {
                flag = false;
            }
        }

        if (flag) {
            // 设置subCode
            SysDept pbo = new SysDept();
            pbo.setParentId(dept.getParentId());
            int counts = deptMapper.selectDeptList(pbo).size();
            String subCode = "";
            if (dept.getParentId().equals(0L)) {
                subCode = "00"+  (counts + 1);
            }else{
                if (counts < 9) {
                    subCode = parentSubCode + "-00" + (counts + 1);
                } else if (counts < 99) {
                    subCode = parentSubCode + "-0" + (counts + 1);
                } else {
                    subCode = parentSubCode + "-" + (counts + 1);
                }
            }
            dept.setSubCode(subCode);
        }

        // 如果是部门 -没有招标
        if (dept.getIsUint().equals("0")){
            dept.setIsZbzg("0");
        }

        int count = deptMapper.insertDept(dept);

        // 修改租户id
        if (dept.getIsUint().equals("0")){
            SysDept deptEpsId = deptMapper.selectTenantId(dept);
            if (null !=deptEpsId){
                SysDept insertbo = new SysDept();
                insertbo.setDeptId(dept.getDeptId());
                insertbo.setTenantId(deptEpsId.getDeptId());
                deptMapper.updateDept(insertbo);
            }
        }else{
            // 是单位
            SysDept insertbo = new SysDept();
            insertbo.setDeptId(dept.getDeptId());
            insertbo.setTenantId(dept.getDeptId());
            deptMapper.updateDept(insertbo);
        }

        return count;
    }

    /**
     * 修改保存部门信息
     * 
     * @param dept 部门信息
     * @return 结果
     */
    @Override
    @Transactional(rollbackFor = Exception.class)
    public int updateDept(SysDept dept)
    {

       /* SysDept oldDept = deptMapper.selectDeptById(dept.getDeptId());
        SysDept newParentDept = deptMapper.selectDeptById(dept.getParentId());
        if (StringUtils.isNotNull(newParentDept) && StringUtils.isNotNull(oldDept))
        {
            String newAncestors = newParentDept.getAncestors() + "," + newParentDept.getDeptId();
            String oldAncestors = oldDept.getAncestors();
            dept.setAncestors(newAncestors);
            updateDeptChildren(dept.getDeptId(), newAncestors, oldAncestors);
        }*/

        // 修改部门编码
        String parentSubCode = ""; //父节点code
        if (null == dept.getParentId())
        {
            dept.setParentId(0L);
            dept.setIsUint("1"); //顶级节点一定是单位
        }
        // 设置树级别
        if (dept.getParentId().equals(0L)) {
            dept.setTreeLeavel(1);
            parentSubCode = "001";
        } else {
            // 查询父节点
            SysDept parentBO = deptMapper.selectDeptById(dept.getParentId());
            dept.setTreeLeavel(parentBO.getTreeLeavel() + 1);
            parentSubCode = parentBO.getSubCode();
        }
        boolean flag = true;
        if (null !=dept.getDeptId())
        {
            SysDept tmpbo = deptMapper.selectDeptById(dept.getDeptId());
            if (tmpbo.getParentId().equals(dept.getParentId()))
            {
                flag = false;
            }
        }

        if (flag) {
            // 设置subCode
            SysDept pbo = new SysDept();
            pbo.setParentId(dept.getParentId());
            int counts = deptMapper.selectDeptList(pbo).size();
            String subCode = "";
            if (dept.getParentId().equals(0L)) {
                subCode = "00"+  (counts + 1);
            }else{
                if (counts < 9) {
                    subCode = parentSubCode + "-00" + (counts + 1);
                } else if (counts < 99) {
                    subCode = parentSubCode + "-0" + (counts + 1);
                } else {
                    subCode = parentSubCode + "-" + (counts + 1);
                }
            }
            dept.setSubCode(subCode);
        }

        // 如果是部门 -没有招标
        if (dept.getIsUint().equals("0")){
            dept.setIsZbzg("0");
        }

        int result = deptMapper.updateDept(dept);

        // 如果是子公司, 自己的租户id是自己的id
       /* if ("1".equals(dept.getIsUint())) {
            // 子公司
            dept.setTenantId(dept.getDeptId());
        } else {
            SysDept deptEpsId = deptMapper.selectTenantId(dept);
            if (null !=deptEpsId){
                dept.setTenantId(deptEpsId.getDeptId());
            }
        }*/

        /*if (UserConstants.DEPT_NORMAL.equals(dept.getStatus()))
        {
            // 如果该部门是启用状态，则启用该部门的所有上级部门
            updateParentDeptStatus(dept);
        }*/

        // 批量修改 租户id
        updateTenantId(dept.getSubCode());
        return result;
    }


    private void updateTenantId(String deptSubCode){
        // 批量修改 租户id
        SysDept queryBo = new SysDept();
        queryBo.setDeptSubCode(deptSubCode);
        List<SysDept> querylist = deptMapper.selectDeptList(queryBo);
        for(SysDept dept :querylist){
            // 修改租户id
            if (dept.getIsUint().equals("0")){
                SysDept deptEpsId = deptMapper.selectTenantId(dept);
                if (null !=deptEpsId){
                    SysDept insertbo = new SysDept();
                    insertbo.setDeptId(dept.getDeptId());
                    insertbo.setTenantId(deptEpsId.getDeptId());
                    deptMapper.updateDept(insertbo);
                }
            }else{
                // 是单位
                SysDept insertbo = new SysDept();
                insertbo.setDeptId(dept.getDeptId());
                insertbo.setTenantId(dept.getDeptId());
                deptMapper.updateDept(insertbo);
            }

        }
    }

    /**
     * 修改该部门的父级部门状态
     * 
     * @param dept 当前部门
     */
    private void updateParentDeptStatus(SysDept dept)
    {
        String updateBy = dept.getUpdateBy();
        dept = deptMapper.selectDeptById(dept.getDeptId());
        dept.setUpdateBy(updateBy);
        deptMapper.updateDeptStatus(dept);
    }

    /**
     * 修改子元素关系
     * 
     * @param deptId 被修改的部门ID
     * @param newAncestors 新的父ID集合
     * @param oldAncestors 旧的父ID集合
     */
    public void updateDeptChildren(Long deptId, String newAncestors, String oldAncestors)
    {
        List<SysDept> children = deptMapper.selectChildrenDeptById(deptId);
        for (SysDept child : children)
        {
            child.setAncestors(child.getAncestors().replace(oldAncestors, newAncestors));
        }
        if (children.size() > 0)
        {
            deptMapper.updateDeptChildren(children);
        }
    }

    /**
     * 删除部门管理信息
     * 
     * @param deptId 部门ID
     * @return 结果
     */
    @Override
    public int deleteDeptById(Long deptId)
    {
        return deptMapper.deleteDeptById(deptId);
    }

    /**
     * 递归列表
     */
    private void recursionFn(List<SysDept> list, SysDept t)
    {
        // 得到子节点列表
        List<SysDept> childList = getChildList(list, t);
        t.setChildren(childList);
        for (SysDept tChild : childList)
        {
            if (hasChild(list, tChild))
            {
                recursionFn(list, tChild);
            }
        }
    }

    /**
     * 得到子节点列表
     */
    private List<SysDept> getChildList(List<SysDept> list, SysDept t)
    {
        List<SysDept> tlist = new ArrayList<SysDept>();
        Iterator<SysDept> it = list.iterator();
        while (it.hasNext())
        {
            SysDept n = (SysDept) it.next();
            if (StringUtils.isNotNull(n.getParentId()) && n.getParentId().longValue() == t.getDeptId().longValue())
            {
                tlist.add(n);
            }
        }
        return tlist;
    }

    /**
     * 判断是否有子节点
     */
    private boolean hasChild(List<SysDept> list, SysDept t)
    {
        return getChildList(list, t).size() > 0 ? true : false;
    }

    /**
     * 根据权限查询:// 普通员工只能查询自己的项目 部门负责人可以查看本部门  分管领导可以看所有分管部门
     * @return
     */
    @Override
    public String getQxSql(String type){
        String sql = "";
        String tableCol = "t.eps_id";
        Long userId = SecurityUtils.getUserId();
        // 判断是否是分管领导
        SysDept bo = new SysDept();
        bo.setFgldId(userId);
        List<SysDept> fgDeptList = deptMapper.selectDeptList(bo);
        if (null!= fgDeptList && fgDeptList.size() > 0){
           sql = tableCol + " in (" + getSqlDeptIds(fgDeptList) + ")";
        }else{
            // 判断是部门负责人
            SysDept bo1 = new SysDept();
            bo1.setLeaderId(userId);
            List<SysDept> fzrDeptList = deptMapper.selectDeptList(bo1);
            if (null!= fzrDeptList && fzrDeptList.size() > 0){
                sql = tableCol + " in (" + getSqlDeptIds(fzrDeptList) + ")";
            }else{
                sql = " t.create_by="+userId;
            }
        }
        return sql;
    }

    /**
     * 获取总公司部门
     * @return
     */
    @Override
    public Set<SysDept> selectHeadOffice() {
        List<SysDept> deptList = this.selectDeptList(new SysDept());
        if (CollectionUtils.isNotEmpty(deptList)) {
            // 获取 tree_level 为 1 和 2
            Set<SysDept> filterSet = deptList.stream()
                    .filter(dept -> dept.getTreeLeavel().equals(1) || dept.getTreeLeavel().equals(2))
                    .collect(Collectors.toSet());
            Set<Long> filterDeptIdSet = filterSet.stream().map(SysDept::getDeptId).collect(Collectors.toSet());

            Set<SysDept> deptSet = deptList.stream()
                    .filter(dept -> filterDeptIdSet.contains(dept.getTenantId()))
                    .collect(Collectors.toSet());

            filterSet.addAll(deptSet);

            return filterSet;
        }

        return null;
    }

    private String getSqlDeptIds(List<SysDept> deptList){
        String deptIds = "";
        if (null != deptList && deptList.size() > 0){
            for (SysDept vo:deptList){
                deptIds += vo.getDeptId()+",";
            }
            deptIds = deptIds.substring(0, deptIds.length() - 1);
        }
        return deptIds;

    }

    @Transactional(rollbackFor = Exception.class)
    public void saveAll(List<SysDept> depts) {
        if (null != depts && depts.size() > 0) {
            // 先删除所有的，然后新增
            deptMapper.deleteDeptAll();
            for (SysDept dept:depts){
                deptMapper.insertDept(dept);
            }
        }
    }

}



