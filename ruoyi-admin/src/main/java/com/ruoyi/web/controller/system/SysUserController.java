package com.ruoyi.web.controller.system;

import com.ruoyi.common.annotation.Log;
import com.ruoyi.common.constant.UserConstants;
import com.ruoyi.common.core.controller.BaseController;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.domain.entity.SysRole;
import com.ruoyi.common.core.domain.entity.SysUser;
import com.ruoyi.common.core.domain.model.LoginUser;
import com.ruoyi.common.core.page.TableDataInfo;
import com.ruoyi.common.enums.BusinessType;
import com.ruoyi.common.utils.SecurityUtils;
import com.ruoyi.common.utils.ServletUtils;
import com.ruoyi.common.utils.StringUtils;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.framework.web.service.TokenService;
import com.ruoyi.system.service.ISysPostService;
import com.ruoyi.system.service.ISysRoleService;
import com.ruoyi.system.service.ISysUserService;
import com.ruoyi.web.util.CommonUtil;
import org.apache.commons.collections4.CollectionUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;
import java.util.stream.Collectors;

/**
 * 用户信息
 *
 * @author ruoyi
 */
@RestController
@RequestMapping("/system/user")
public class SysUserController extends BaseController {

    @Autowired
    private ISysUserService userService;

    @Autowired
    private ISysRoleService roleService;

    @Autowired
    private ISysPostService postService;

    @Autowired
    private TokenService tokenService;

    /**
     * 查询本单位的机构用户：机构用户管理
     */
    @GetMapping("/list")
    public TableDataInfo list(SysUser user) {
        startPage();
        // 查询机构用户
        user.setUserType("1");
        List<SysUser> list = userService.selectUserList(user);
        return getDataTable(list);
    }

    /**
     * 查询自己单位所有的用户 (包含1=机构用户2专家3供应商)
     */
    @GetMapping("/listAll")
    public TableDataInfo listAll(SysUser user) {
        startPage();
        user.setTenantId(SecurityUtils.getTenantId());
        List<SysUser> list = userService.selectUserList(user);
        return getDataTable(list);
    }

    /**
     * 根据租户id 查询机构用户 需要传入租户ID
     * userType  前台页面传入过来-非必填
     */
    @GetMapping("/listTenantIdAll")
    public TableDataInfo listTenantIdAll(SysUser user) {
        startPage();
        if (null == user.getTenantId()) {
            user.setTenantId(-1L);
        }
        List<SysUser> list = userService.selectUserList(user);
        return getDataTable(list);
    }

    /**
     * 获取用户列表 (没权限) -- 弹出页面组件
     */
    @GetMapping("/listutil")
    public TableDataInfo listutil(SysUser user) {
        startPage();
        // 根据flag 来查询
        String flag = CommonUtil.isNull(user.getFlag());
        // 查询机构用户
        if (flag.equals("myDept")) {
            user.setStatus("0");
            user.setUserType("1");
            user.setTenantId(SecurityUtils.getTenantId());
        } else if (flag.equals("myDeptCg")) {
            user.setStatus("0");
            user.setUserType("1");
            user.setTenantId(SecurityUtils.getTenantId());
        }else if (flag.equals("sjzbDept")||flag.equals("sjzbDeptCg")) {
            // 上级有资格的招标单位
            user.setDataId(SecurityUtils.getTenantId() + "");
        } else if (flag.equals("allDept")) {

        } else {
            user.setUserId(-1l);
        }
        List<SysUser> list = userService.selectUserList(user);
        return getDataTable(list);
    }

    /**
     * 获取用户列表同部门-- 弹出页面组件
     */
    @GetMapping("/listSameUtil")
    public TableDataInfo listSameUtil(SysUser user) {
        startPage();
        user.setStatus("0");
        user.setUserType("1");
        user.setTenantId(SecurityUtils.getTenantId());
        user.setDeptId(SecurityUtils.getEpsId());
        List<SysUser> list = userService.selectUserList(user);
        return getDataTable(list);
    }

    /**
     * 查询自己
     */
    @GetMapping("/listMy")
    public TableDataInfo listMy(SysUser user) {
        startPage();
        user.setUserId(SecurityUtils.getUserId());
        List<SysUser> list = userService.selectUserList(user);
        return getDataTable(list);
    }

    @Log(title = "用户管理", businessType = BusinessType.EXPORT)
    @PreAuthorize("@ss.hasPermi('system:user:export')")
    @GetMapping("/export")
    public AjaxResult export(SysUser user) {
        List<SysUser> list = userService.selectUserList(user);
        ExcelUtil<SysUser> util = new ExcelUtil<SysUser>(SysUser.class);
        return util.exportExcel(list, "用户数据");
    }

    @Log(title = "用户管理", businessType = BusinessType.IMPORT)
    @PreAuthorize("@ss.hasPermi('system:user:import')")
    @PostMapping("/importData")
    public AjaxResult importData(MultipartFile file, boolean updateSupport) throws Exception {
        ExcelUtil<SysUser> util = new ExcelUtil<SysUser>(SysUser.class);
        List<SysUser> userList = util.importExcel(file.getInputStream());
        LoginUser loginUser = tokenService.getLoginUser(ServletUtils.getRequest());
        String operName = loginUser.getUsername();
        String message = userService.importUser(userList, updateSupport, operName);
        return AjaxResult.success(message);
    }

    @GetMapping("/importTemplate")
    public AjaxResult importTemplate() {
        ExcelUtil<SysUser> util = new ExcelUtil<SysUser>(SysUser.class);
        return util.importTemplateExcel("用户数据");
    }

    /**
     * 根据用户编号获取详细信息
     */
    @PreAuthorize("@ss.hasPermi('system:user:query')")
    @GetMapping(value = {"/", "/{userId}"})
    public AjaxResult getInfo(@PathVariable(value = "userId", required = false) Long userId) {
        AjaxResult ajax = AjaxResult.success();
        List<SysRole> roles = roleService.selectRoleAll();
        ajax.put("roles", SysUser.isAdmin(userId) ? roles : roles.stream().filter(r -> !r.isAdmin()).collect(Collectors.toList()));
        ajax.put("posts", postService.selectPostAll());
        if (StringUtils.isNotNull(userId)) {
            ajax.put(AjaxResult.DATA_TAG, userService.selectUserById(userId));
            ajax.put("postIds", postService.selectPostListByUserId(userId));
            ajax.put("roleIds", roleService.selectRoleListByUserId(userId));
        }
        return ajax;
    }

    /**
     * 新增用户
     */
    @PreAuthorize("@ss.hasPermi('system:user:add')")
    @Log(title = "用户管理", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@Validated @RequestBody SysUser user) {
        if (UserConstants.NOT_UNIQUE_OLD.equals(userService.checkUserNameUnique(user.getUserName()))) {
            return AjaxResult.error("新增用户'" + user.getUserName() + "'失败，登录账号已存在");
        } else if (StringUtils.isNotEmpty(user.getPhonenumber())
                && UserConstants.NOT_UNIQUE_OLD.equals(userService.checkPhoneUnique(user))) {
            return AjaxResult.error("新增用户'" + user.getUserName() + "'失败，手机号码已存在");
        } else if (StringUtils.isNotEmpty(user.getEmail())
                && UserConstants.NOT_UNIQUE_OLD.equals(userService.checkEmailUnique(user))) {
            return AjaxResult.error("新增用户'" + user.getUserName() + "'失败，邮箱账号已存在");
        }


        if(CommonUtil.checkPassword(user.getPassword())){
            return AjaxResult.error("对不起，密码长度8-20位且至少包含大写字母、小写字母、数字和特殊符号");
        }



        /*if (StringUtils.isNotEmpty(user.getCertEntityId())) {
            SysUser querybo = new SysUser();
            querybo.setCertEntityId(user.getCertEntityId());
            List<SysUser> userList = userService.selectUserList(querybo);
            if (userList.size() > 0) {
                return AjaxResult.error("唯一实体标识已绑定，请确认！");
            }
        }


        if (StringUtils.isNotEmpty(user.getCertId())) {
            SysUser querybo = new SysUser();
            querybo.setCertId(user.getCertId());
            List<SysUser> userList = userService.selectUserList(querybo);
            if (userList.size() > 0) {
                return AjaxResult.error("密码卡/USD-Key序列号已绑定，请确认！");
            }
        }*/

        user.setCreateBy(SecurityUtils.getUsername());
        user.setPassword(SecurityUtils.encryptPassword(user.getPassword()));
        return toAjax(userService.insertUser(user));
    }

    /**
     * 修改用户
     */
    @PreAuthorize("@ss.hasPermi('system:user:edit')")
    @Log(title = "用户管理", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@Validated @RequestBody SysUser user) {
        userService.checkUserAllowed(user);
        if (StringUtils.isNotEmpty(user.getPhonenumber())
                && UserConstants.NOT_UNIQUE_OLD.equals(userService.checkPhoneUnique(user))) {
            return AjaxResult.error("修改用户'" + user.getUserName() + "'失败，手机号码已存在");
        } else if (StringUtils.isNotEmpty(user.getEmail())
                && UserConstants.NOT_UNIQUE_OLD.equals(userService.checkEmailUnique(user))) {
            return AjaxResult.error("修改用户'" + user.getUserName() + "'失败，邮箱账号已存在");
        }

        /*if (StringUtils.isNotEmpty(user.getCertEntityId())) {
            SysUser querybo = new SysUser();
            querybo.setCertEntityId(user.getCertEntityId());
            List<SysUser> userList = userService.selectUserList(querybo);
            if (userList.size() > 0) {
                if (!userList.get(0).getUserId().equals(user.getUserId())) {
                    return AjaxResult.error("唯一实体标识已绑定，请确认！");
                }
            }
        }


        if (StringUtils.isNotEmpty(user.getCertId())) {
            SysUser querybo = new SysUser();
            querybo.setCertId(user.getCertId());
            List<SysUser> userList = userService.selectUserList(querybo);
            if (userList.size() > 0) {
                if (!userList.get(0).getUserId().equals(user.getUserId())) {
                    return AjaxResult.error("密码卡/USD-Key序列号已绑定，请确认！");
                }
            }
        }*/


        user.setUpdateBy(SecurityUtils.getUsername());
        return toAjax(userService.updateUser(user));
    }

    /**
     * 删除用户
     */
    @PreAuthorize("@ss.hasPermi('system:user:remove')")
    @Log(title = "用户管理", businessType = BusinessType.DELETE)
    @DeleteMapping("/{userIds}")
    public AjaxResult remove(@PathVariable Long[] userIds) {
        return toAjax(userService.deleteUserByIds(userIds));
    }

    /**
     * 重置密码
     */
    @PreAuthorize("@ss.hasPermi('system:user:resetPwd')")
    @Log(title = "用户管理", businessType = BusinessType.UPDATE)
    @PutMapping("/resetPwd")
    public AjaxResult resetPwd(@RequestBody SysUser user) {
        String password = user.getPassword();
        if(CommonUtil.checkPassword(password)){
            return AjaxResult.error("对不起，密码长度8-20位且至少包含大写字母、小写字母、数字和特殊符号");
        }

        userService.checkUserAllowed(user);
        user.setPassword(SecurityUtils.encryptPassword(password));
        user.setUpdateBy(SecurityUtils.getUsername());
        return toAjax(userService.resetPwd(user));
    }

    /**
     * 状态修改
     */
    @PreAuthorize("@ss.hasPermi('system:user:edit')")
    @Log(title = "用户管理", businessType = BusinessType.UPDATE)
    @PutMapping("/changeStatus")
    public AjaxResult changeStatus(@RequestBody SysUser user) {
        userService.checkUserAllowed(user);
        user.setUpdateBy(SecurityUtils.getUsername());
        return toAjax(userService.updateUserStatus(user));
    }

    /**
     * 绑定ukky
     */
    @PutMapping("/bindUky")
    public AjaxResult bindUky(@RequestBody SysUser user) {
        if (null == user.getUserId()) {
            // 获取当前用户绑定CA
            user.setUserId(SecurityUtils.getUserId());
        }

        if (StringUtils.isEmpty(user.getCertEntityId())) {
            return AjaxResult.error("唯一实体标识不能为空");
        }

        if (StringUtils.isEmpty(user.getCertId())) {
            return AjaxResult.error("密码卡/USD-Key序列号不能为空");
        }

        if (StringUtils.isNotEmpty(user.getCertEntityId())) {
            SysUser querybo = new SysUser();
            querybo.setCertEntityId(user.getCertEntityId());
            List<SysUser> userList = userService.selectUserList(querybo);
            if (userList.size() > 0) {
                if (!userList.get(0).getUserId().equals(user.getUserId())) {
                    return AjaxResult.error("唯一实体标识已绑定，请确认！");
                }
            }
        }


        if (StringUtils.isNotEmpty(user.getCertId())) {
            SysUser querybo = new SysUser();
            querybo.setCertId(user.getCertId());
            List<SysUser> userList = userService.selectUserList(querybo);
            if (userList.size() > 0) {
                if (!userList.get(0).getUserId().equals(user.getUserId())) {
                    return AjaxResult.error("密码卡/USD-Key序列号已绑定，请确认！");
                }
            }
        }


        SysUser newUser = new SysUser();
        newUser.setUserId(user.getUserId());
        newUser.setCertId(user.getCertId());
        newUser.setCertEntityId(user.getCertEntityId());
        newUser.setUpdateBy(SecurityUtils.getUsername());


        return toAjax(userService.updateUserStatus(newUser));
    }

    /**
     * 根据角色名称获取人员信息
     */
    @GetMapping(value = "/getroleUser/{roleCode}")
    public AjaxResult getroleUser(@PathVariable String roleCode) {
        SysUser user = new SysUser();
        user.setRoleCode(roleCode);
        user.setTenantId(SecurityUtils.getTenantId());
        List<SysUser> list = userService.selectUserList(user);
        return AjaxResult.success(list);
    }

    /**
     * 根据部门查询对应部门的人员信息
     * @param user
     * @return
     */
    @GetMapping("/list/dept")
    public TableDataInfo listByDept(SysUser user) {
        startPage();
        Long epsId = SecurityUtils.getEpsId();
        if (epsId != null) {
            user.setDeptId(epsId);
        }
        // 是否过滤掉自己
        if (user.getExcludeSelf() != null && user.getExcludeSelf()) {
            user.setExcludeId(SecurityUtils.getUserId());
        }

        // 查询机构用户
        user.setUserType("1");
        List<SysUser> list = userService.selectUserList(user);
        // 设置部门名称
        if (CollectionUtils.isNotEmpty(list)) {
            list.forEach(data -> {
                if (data.getDept() != null && StringUtils.isNotBlank(data.getDept().getDeptName())) {
                    data.setDeptName(data.getDept().getDeptName());
                }
            });
        }

        return getDataTable(list);
    }

    /**
     * 获取当前用户信息
     * @return
     */
    @GetMapping("/currentUser")
    public AjaxResult selectCurrentUser() {
        SysUser currentUser = userService.selectCurrentUser();
        return AjaxResult.success(currentUser);
    }

}
