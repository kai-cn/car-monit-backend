package com.ruoyi.system.service.impl;

import com.ruoyi.common.annotation.DataScope;
import com.ruoyi.common.constant.Constants;
import com.ruoyi.common.constant.UserConstants;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.domain.entity.SysDept;
import com.ruoyi.common.core.domain.entity.SysRole;
import com.ruoyi.common.core.domain.entity.SysUser;
import com.ruoyi.common.core.redis.RedisCache;
import com.ruoyi.common.exception.CustomException;
import com.ruoyi.common.utils.SecurityUtils;
import com.ruoyi.common.utils.StringUtils;
import com.ruoyi.system.domain.SysPost;
import com.ruoyi.system.domain.SysUserPost;
import com.ruoyi.system.domain.SysUserRole;
import com.ruoyi.system.mapper.SysDeptMapper;
import com.ruoyi.system.mapper.SysPostMapper;
import com.ruoyi.system.mapper.SysRoleMapper;
import com.ruoyi.system.mapper.SysUserMapper;
import com.ruoyi.system.mapper.SysUserPostMapper;
import com.ruoyi.system.mapper.SysUserRoleMapper;
import com.ruoyi.system.service.ISysConfigService;
import com.ruoyi.system.service.ISysDeptService;
import com.ruoyi.system.service.ISysRoleService;
import com.ruoyi.system.service.ISysUserService;
import org.apache.commons.collections4.CollectionUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;

/**
 * 用户 业务层处理
 *
 * @author ruoyi
 */
@Service
public class SysUserServiceImpl implements ISysUserService
{
    private static final Logger log = LoggerFactory.getLogger(SysUserServiceImpl.class);

    @Autowired
    private SysUserMapper userMapper;

    @Autowired
    private SysRoleMapper roleMapper;

    @Autowired
    private SysPostMapper postMapper;

    @Autowired
    private SysUserRoleMapper userRoleMapper;

    @Autowired
    private SysUserPostMapper userPostMapper;

    @Autowired
    private ISysConfigService configService;

    @Autowired
    private SysDeptMapper deptMapper;

    @Autowired
    private RedisCache redisCache;

    @Autowired
    private ISysDeptService deptService;

    @Autowired
    private ISysRoleService roleService;

    /**
     * 根据条件分页查询用户列表
     *
     * @param user 用户信息
     * @return 用户信息集合信息
     */
    @Override
    @DataScope(deptAlias = "d", userAlias = "u")
    public List<SysUser> selectUserList(SysUser user)
    {
        return userMapper.selectUserList(user);
    }

    /**
     * 通过用户名查询用户
     *
     * @param userName 用户名
     * @return 用户对象信息
     */
    @Override
    public SysUser selectUserByUserName(String userName)
    {
        return userMapper.selectUserByUserName(userName);
    }
    /**
     * 通过ca实体id查询用户
     *
     * @param strCertEntityID 用户名
     * @return 用户对象信息
     */
    @Override
    public SysUser selectUserByCertEntityID(String strCertEntityID) {
        return userMapper.selectUserByCertEntityID(strCertEntityID);
    }

    /**
     * 通过用户ID查询用户
     *
     * @param userId 用户ID
     * @return 用户对象信息
     */
    @Override
    public SysUser selectUserById(Long userId)
    {
        return userMapper.selectUserById(userId);
    }

    /**
     * 查询用户所属角色组
     *
     * @param userName 用户名
     * @return 结果
     */
    @Override
    public String selectUserRoleGroup(String userName)
    {
        List<SysRole> list = roleMapper.selectRolesByUserName(userName);
        StringBuffer idsStr = new StringBuffer();
        for (SysRole role : list)
        {
            idsStr.append(role.getRoleName()).append(",");
        }
        if (StringUtils.isNotEmpty(idsStr.toString()))
        {
            return idsStr.substring(0, idsStr.length() - 1);
        }
        return idsStr.toString();
    }

    /**
     * 查询用户所属岗位组
     *
     * @param userName 用户名
     * @return 结果
     */
    @Override
    public String selectUserPostGroup(String userName)
    {
        List<SysPost> list = postMapper.selectPostsByUserName(userName);
        StringBuffer idsStr = new StringBuffer();
        for (SysPost post : list)
        {
            idsStr.append(post.getPostName()).append(",");
        }
        if (StringUtils.isNotEmpty(idsStr.toString()))
        {
            return idsStr.substring(0, idsStr.length() - 1);
        }
        return idsStr.toString();
    }

    /**
     * 校验用户名称是否唯一
     *
     * @param userName 用户名称
     * @return 结果
     */
    @Override
    public String checkUserNameUnique(String userName)
    {
        int count = userMapper.checkUserNameUnique(userName);
        if (count > 0)
        {
            return UserConstants.NOT_UNIQUE_OLD;
        }
        return UserConstants.UNIQUE_OLD;
    }

    /**
     * 校验用户名称是否唯一
     *
     * @param user 用户信息
     * @return
     */
    @Override
    public String checkPhoneUnique(SysUser user)
    {
        Long userId = StringUtils.isNull(user.getUserId()) ? -1L : user.getUserId();
        SysUser info = userMapper.checkPhoneUnique(user.getPhonenumber());
        if (StringUtils.isNotNull(info) && info.getUserId().longValue() != userId.longValue())
        {
            return UserConstants.NOT_UNIQUE_OLD;
        }
        return UserConstants.UNIQUE_OLD;
    }

    /**
     * 校验email是否唯一
     *
     * @param user 用户信息
     * @return
     */
    @Override
    public String checkEmailUnique(SysUser user)
    {
        Long userId = StringUtils.isNull(user.getUserId()) ? -1L : user.getUserId();
        SysUser info = userMapper.checkEmailUnique(user.getEmail());
        if (StringUtils.isNotNull(info) && info.getUserId().longValue() != userId.longValue())
        {
            return UserConstants.NOT_UNIQUE_OLD;
        }
        return UserConstants.UNIQUE_OLD;
    }

    /**
     * 校验用户是否允许操作
     *
     * @param user 用户信息
     */
    @Override
    public void checkUserAllowed(SysUser user)
    {
        if (StringUtils.isNotNull(user.getUserId()) && user.isAdmin())
        {
            throw new CustomException("不允许操作超级管理员用户");
        }
    }

    /**
     * 新增保存用户信息
     *
     * @param user 用户信息
     * @return 结果
     */
    @Override
    @Transactional
    public int insertUser(SysUser user)
    {
        if (null !=user.getDeptId()){
            SysDept sysDept = deptMapper.selectDeptById(user.getDeptId());
            user.setBussName(sysDept.getDeptName());
            user.setTenantId(sysDept.getTenantId());
        }

        // 新增用户信息
        int rows = userMapper.insertUser(user);
        // 新增用户岗位关联
        insertUserPost(user);
        // 新增用户与角色管理
        insertUserRole(user);
        return rows;
    }

    /**
     * 修改保存用户信息
     *
     * @param user 用户信息
     * @return 结果
     */
    @Override
    @Transactional
    public int updateUser(SysUser user)
    {
        Long userId = user.getUserId();
        // 删除用户与角色关联
        userRoleMapper.deleteUserRoleByUserId(userId);
        // 新增用户与角色管理
        insertUserRole(user);
        // 删除用户与岗位关联
        userPostMapper.deleteUserPostByUserId(userId);
        // 新增用户与岗位管理
        insertUserPost(user);

        if (null !=user.getDeptId()){
            SysDept sysDept = deptMapper.selectDeptById(user.getDeptId());
            user.setBussName(sysDept.getDeptName());
            user.setTenantId(sysDept.getTenantId());
        }

        return userMapper.updateUser(user);
    }

    @Override
    public int updateUserInfoByBussId(SysUser user) {
        return userMapper.updateUserInfoByBussId(user);
    }

    /**
     * 修改用户状态
     *
     * @param user 用户信息
     * @return 结果
     */
    @Override
    public int updateUserStatus(SysUser user)
    {
        return userMapper.updateUser(user);
    }

    /**
     * 修改用户基本信息
     *
     * @param user 用户信息
     * @return 结果
     */
    @Override
    public int updateUserProfile(SysUser user)
    {
        return userMapper.updateUser(user);
    }

    /**
     * 修改用户头像
     *
     * @param userName 用户名
     * @param avatar 头像地址
     * @return 结果
     */
    @Override
    public boolean updateUserAvatar(String userName, String avatar)
    {
        return userMapper.updateUserAvatar(userName, avatar) > 0;
    }

    /**
     * 重置用户密码
     *
     * @param user 用户信息
     * @return 结果
     */
    @Override
    public int resetPwd(SysUser user)
    {
        return userMapper.updateUser(user);
    }

    /**
     * 重置用户密码
     *
     * @param userName 用户名
     * @param password 密码
     * @return 结果
     */
    @Override
    public int resetUserPwd(String userName, String password)
    {
        return userMapper.resetUserPwd(userName, password);
    }

    /**
     * 新增用户角色信息
     *
     * @param user 用户对象
     */
    public void insertUserRole(SysUser user)
    {
        Long[] roles = user.getRoleIds();
        if (StringUtils.isNotNull(roles))
        {
            // 新增用户与角色管理
            List<SysUserRole> list = new ArrayList<SysUserRole>();
            for (Long roleId : roles)
            {
                SysUserRole ur = new SysUserRole();
                ur.setUserId(user.getUserId());
                ur.setRoleId(roleId);
                list.add(ur);
            }
            if (list.size() > 0)
            {
                userRoleMapper.batchUserRole(list);
            }
        }
    }

    /**
     * 新增用户岗位信息
     *
     * @param user 用户对象
     */
    public void insertUserPost(SysUser user)
    {
        Long[] posts = user.getPostIds();
        if (StringUtils.isNotNull(posts))
        {
            // 新增用户与岗位管理
            List<SysUserPost> list = new ArrayList<SysUserPost>();
            for (Long postId : posts)
            {
                SysUserPost up = new SysUserPost();
                up.setUserId(user.getUserId());
                up.setPostId(postId);
                list.add(up);
            }
            if (list.size() > 0)
            {
                userPostMapper.batchUserPost(list);
            }
        }
    }

    /**
     * 通过用户ID删除用户
     *
     * @param userId 用户ID
     * @return 结果
     */
    @Override
    @Transactional
    public int deleteUserById(Long userId)
    {
        // 删除用户与角色关联
        userRoleMapper.deleteUserRoleByUserId(userId);
        // 删除用户与岗位表
        userPostMapper.deleteUserPostByUserId(userId);
        return userMapper.deleteUserById(userId);
    }

    /**
     * 批量删除用户信息
     *
     * @param userIds 需要删除的用户ID
     * @return 结果
     */
    @Override
    @Transactional
    public int deleteUserByIds(Long[] userIds)
    {
        for (Long userId : userIds)
        {
            checkUserAllowed(new SysUser(userId));
        }
        // 删除用户与角色关联
        userRoleMapper.deleteUserRole(userIds);
        // 删除用户与岗位关联
        userPostMapper.deleteUserPost(userIds);
        return userMapper.deleteUserByIds(userIds);
    }

    /**
     * 导入用户数据
     *
     * @param userList 用户数据列表
     * @param isUpdateSupport 是否更新支持，如果已存在，则进行更新数据
     * @param operName 操作用户
     * @return 结果
     */
    @Override
    public String importUser(List<SysUser> userList, Boolean isUpdateSupport, String operName)
    {
        if (StringUtils.isNull(userList) || userList.size() == 0)
        {
            throw new CustomException("导入用户数据不能为空！");
        }
        int successNum = 0;
        int failureNum = 0;
        StringBuilder successMsg = new StringBuilder();
        StringBuilder failureMsg = new StringBuilder();
        String password = configService.selectConfigByKey("sys.user.initPassword");
        for (SysUser user : userList)
        {
            try
            {
                // 验证是否存在这个用户
                SysUser u = userMapper.selectUserByUserName(user.getUserName());
                if (StringUtils.isNull(u))
                {
                    user.setPassword(SecurityUtils.encryptPassword(password));
                    user.setCreateBy(operName);
                    this.insertUser(user);
                    successNum++;
                    successMsg.append("<br/>" + successNum + "、账号 " + user.getUserName() + " 导入成功");
                }
                else if (isUpdateSupport)
                {
                    user.setUpdateBy(operName);
                    this.updateUser(user);
                    successNum++;
                    successMsg.append("<br/>" + successNum + "、账号 " + user.getUserName() + " 更新成功");
                }
                else
                {
                    failureNum++;
                    failureMsg.append("<br/>" + failureNum + "、账号 " + user.getUserName() + " 已存在");
                }
            }
            catch (Exception e)
            {
                failureNum++;
                String msg = "<br/>" + failureNum + "、账号 " + user.getUserName() + " 导入失败：";
                failureMsg.append(msg + e.getMessage());
                log.error(msg, e);
            }
        }
        if (failureNum > 0)
        {
            failureMsg.insert(0, "很抱歉，导入失败！共 " + failureNum + " 条数据格式不正确，错误如下：");
            throw new CustomException(failureMsg.toString());
        }
        else
        {
            successMsg.insert(0, "恭喜您，数据已全部导入成功！共 " + successNum + " 条，数据如下：");
        }
        return successMsg.toString();
    }

    /**
     * 通过手机号找回密码
     * @param sysUser
     * @return
     */
    @Override
    @Transactional
    public AjaxResult updateUserPwd(SysUser sysUser) {
        String vcode = null;
        try {
            vcode = redisCache.getCacheObject(sysUser.getPhonenumber()).toString();
        } catch (Exception e) {
            e.printStackTrace();
            return AjaxResult.error("验证码错误或过期！");
        }
        if (StringUtils.isEmpty(sysUser.getRemark()) || !sysUser.getRemark().equals(vcode)) {
            return AjaxResult.error("验证码错误或过期！");
        }

        // 根据账号查询用户
        List<SysUser> sysUsers = userMapper.selectUserList(sysUser);

        if (sysUsers.size() == 0 || sysUsers.size() > 1){
            return AjaxResult.error("账号或手机号有误！");
        }

        SysUser user = new SysUser();
        user.setPhonenumber(sysUser.getPhonenumber());
        user.setUserName(sysUser.getUserName());
        user.setPassword(SecurityUtils.encryptPassword(UserConstants.DEFAULT_PWD));
        int i = userMapper.updateUserPwd(user.getPhonenumber(), user.getPassword(),user.getUserName());
        // 说明更新成功
        if (i == 1){
            return AjaxResult.success("密码已重置为",UserConstants.DEFAULT_PWD);
        }
        return AjaxResult.error("找回密码失败！");
    }

    /**
     * 获取当前用户信息
     * @return
     */
    @Override
    public SysUser selectCurrentUser() {
        SysUser user = SecurityUtils.getLoginUser().getUser();
        Long deptId = SecurityUtils.getEpsId();
        SysUser currentUser = new SysUser();

        currentUser.setUserId(user.getUserId());
        currentUser.setDeptId(deptId);
        // 设置默认的总公司标识
        currentUser.setHeadOffice(false);
        // 设置默认的采购经理角色标识
        currentUser.setProcurementManager(false);

        // 获取总公司列表
        Set<SysDept> deptSet = deptService.selectHeadOffice();
        if (CollectionUtils.isNotEmpty(deptSet)) {
            Set<Long> deptIdSet = deptSet.stream().map(SysDept::getDeptId).collect(Collectors.toSet());
            if (deptIdSet.contains(deptId)) {
                currentUser.setHeadOffice(true);
            }
        }

        // 查询采购经理角色信息
        SysRole roleQueryBo = new SysRole();
        roleQueryBo.setRoleKey(Constants.PROCUREMENT_MANAGER_ROLE_KEY);
        List<SysRole> roleList = roleService.selectRoleList(roleQueryBo);
        if (CollectionUtils.isNotEmpty(roleList)) {
            SysRole role = roleList.get(0);
            List<SysRole> userRoleList = roleMapper.selectRolesByUserName(user.getUserName());
            if (CollectionUtils.isNotEmpty(userRoleList)) {
                Set<Long> roleSet = userRoleList.stream().map(SysRole::getRoleId).collect(Collectors.toSet());
                if (roleSet.contains(role.getRoleId())) {
                    currentUser.setProcurementManager(true);
                }
            }
        }

        return currentUser;
    }

    /**
     * 根据 bussId 和 userType 进行更新
     * @param user
     */
    @Override
    public void updateUserInfoByBussIdAndUserType(SysUser user) {
        userMapper.updateUserInfoByBussIdAndUserType(user);
    }

    @Override
    public SysUser selectPwdJudge(Long userId) {
        return userMapper.selectPwdJudge(userId);
    }

    /**
     * 忘记密码
     * @param sysUser
     * @return
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult forgotPassword(SysUser sysUser) {
        String vcode = null;
        try {
            vcode = redisCache.getCacheObject(sysUser.getPhonenumber()).toString();
        } catch (Exception e) {
            e.printStackTrace();
            return AjaxResult.error("验证码错误或过期！");
        }
        if (StringUtils.isEmpty(sysUser.getRemark()) || !sysUser.getRemark().equalsIgnoreCase(vcode)) {
            return AjaxResult.error("验证码错误或过期！");
        }

        // 根据账号查询用户
        List<SysUser> sysUsers = userMapper.selectUserList(sysUser);
        if (CollectionUtils.isEmpty(sysUsers) || sysUsers.size() > 1){
            return AjaxResult.error("账号或手机号有误！");
        }

        SysUser user = new SysUser();
        user.setPhonenumber(sysUser.getPhonenumber());
        user.setUserName(sysUser.getUserName());
        user.setPassword(SecurityUtils.encryptPassword(sysUser.getPassword()));
        int i = userMapper.updateUserPwd(user.getPhonenumber(), user.getPassword(), user.getUserName());
        // 说明更新成功
        if (i == 1){
            return AjaxResult.success("密码已重置为: ", sysUser.getPassword());
        }

        return AjaxResult.error("找回密码失败! ");
    }

}
