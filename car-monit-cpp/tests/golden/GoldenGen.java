import com.alibaba.fastjson2.JSON;
import com.alibaba.fastjson2.JSONReader;
import com.alibaba.fastjson2.JSONWriter;
import com.ruoyi.common.core.domain.entity.SysUser;
import com.ruoyi.common.core.domain.model.LoginUser;

import java.io.OutputStreamWriter;
import java.io.PrintWriter;
import java.lang.reflect.Field;
import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.*;

/**
 * 用真实 ruoyi-common 编译产物生成 fastjson2 WriteClassName 的 golden 输出。
 * 序列化调用与 FastJson2JsonRedisSerializer.serialize 完全一致：
 *   JSON.toJSONString(t, JSONWriter.Feature.WriteClassName)
 *
 * 重新生成（Java 侧实体加字段后必须重跑，否则 C++ 的字段集断言会失败）：
 *   javac -encoding UTF-8 \
 *     -cp "<repo>/ruoyi-common/target/classes;<m2>/fastjson2-2.0.43.jar;\
 *          <m2>/spring-security-core-5.5.8.jar;<m2>/poi-4.1.1.jar" \
 *     -d <out> tests/golden/GoldenGen.java
 *   java -Dfile.encoding=UTF-8 -cp "<out>;<上面的 cp>" GoldenGen tests/golden
 */
public class GoldenGen {
    static void set(Object o, String name, Object v) {
        Class<?> c = o.getClass();
        while (c != null && c != Object.class) {
            try {
                Field f = c.getDeclaredField(name);
                f.setAccessible(true);
                f.set(o, v);
                return;
            } catch (NoSuchFieldException e) {
                c = c.getSuperclass();
            } catch (Exception e) {
                throw new RuntimeException(e);
            }
        }
        throw new RuntimeException("缺少字段: " + name);
    }

    static List<String> fieldNames(Class<?> c) {
        List<String> out = new ArrayList<>();
        for (Class<?> k = c; k != null && k != Object.class; k = k.getSuperclass()) {
            for (Field f : k.getDeclaredFields()) {
                if (java.lang.reflect.Modifier.isStatic(f.getModifiers())) continue;
                if (f.isSynthetic()) continue;
                out.add(f.getName());
            }
        }
        Collections.sort(out);
        return out;
    }

    public static void main(String[] args) throws Exception {
        SysUser u = new SysUser();
        set(u, "userId", 1L);
        set(u, "deptId", 103L);
        set(u, "userName", "admin");
        set(u, "nickName", "管理员");
        set(u, "userType", "00");
        set(u, "email", "admin@example.com");
        set(u, "phonenumber", "13800000000");
        set(u, "sex", "0");
        set(u, "avatar", "");
        set(u, "password", null);
        set(u, "status", "0");
        set(u, "delFlag", "0");
        set(u, "loginIp", "127.0.0.1");
        set(u, "loginDate", new Date(1762500000000L));
        set(u, "createBy", "admin");
        set(u, "createTime", new Date(1762400000000L));
        set(u, "updateBy", null);
        set(u, "updateTime", null);
        set(u, "remark", "备注");
        // 登录态的 user.dept 通常非 null（selectUserByUserName 的 association 会填）
        Class<?> deptCls = Class.forName("com.ruoyi.common.core.domain.entity.SysDept");
        Object dept = deptCls.getDeclaredConstructor().newInstance();
        set(dept, "deptId", 103L);
        set(dept, "parentId", 100L);
        set(dept, "ancestors", "0,100");
        set(dept, "deptName", "研发部门");
        set(dept, "orderNum", "1");
        set(dept, "leader", "若依");
        set(dept, "phone", "15888888888");
        set(dept, "email", "ry@qq.com");
        set(dept, "status", "0");
        set(dept, "delFlag", "0");
        set(dept, "createBy", "admin");
        set(dept, "createTime", new Date(1762400000000L));
        set(u, "dept", dept);
        // roles 非 null（普通用户登录时由 selectUserByUserName 的 collection 填充）
        Class<?> roleCls = Class.forName("com.ruoyi.common.core.domain.entity.SysRole");
        Object role = roleCls.getDeclaredConstructor().newInstance();
        set(role, "roleId", 2L);
        set(role, "roleName", "普通角色");
        set(role, "roleKey", "common");
        set(role, "roleSort", "2");
        set(role, "dataScope", "2");
        set(role, "menuCheckStrictly", false);
        set(role, "deptCheckStrictly", false);
        set(role, "status", "0");
        set(role, "delFlag", "0");
        set(role, "flag", false);
        set(u, "roles", Arrays.asList(role));

        LoginUser lu = new LoginUser();
        lu.setToken("e3b0c44298fc1c149afbf4c8996fb924");
        lu.setSessionId("6f1c2a9d-1111-2222-3333-444455556666");
        lu.setLoginTime(1762500000000L);
        lu.setExpireTime(1762507200000L);
        lu.setIpaddr("127.0.0.1");
        lu.setLoginLocation("内网IP");
        lu.setBrowser("Chrome 11");
        lu.setOs("Windows 10");
        // TokenService 实际用 new HashSet<>(permissions)
        lu.setPermissions(new HashSet<>(Arrays.asList("*:*:*")));
        lu.setUser(u);

        String golden = JSON.toJSONString(lu, JSONWriter.Feature.WriteClassName);

        // 反向验证：这正是 FastJson2JsonRedisSerializer.deserialize 的调用
        Object back = JSON.parseObject(golden, Object.class,
                JSONReader.autoTypeFilter(com.ruoyi.common.constant.Constants.JSON_WHITELIST_STR));
        if (!(back instanceof LoginUser)) {
            throw new IllegalStateException("autoType 未还原 LoginUser，实际=" + back.getClass());
        }

        String outDir = args.length > 0 ? args[0] : ".";
        Files.createDirectories(Paths.get(outDir));
        try (PrintWriter w = new PrintWriter(new OutputStreamWriter(
                Files.newOutputStream(Paths.get(outDir, "login_user_fastjson2.json")), StandardCharsets.UTF_8))) {
            w.print(golden);
        }
        try (PrintWriter w = new PrintWriter(new OutputStreamWriter(
                Files.newOutputStream(Paths.get(outDir, "login_user_fields.txt")), StandardCharsets.UTF_8))) {
            w.println("LoginUser=" + fieldNames(LoginUser.class).size());
            for (String f : fieldNames(LoginUser.class)) w.println(f);
            w.println("SysUser=" + fieldNames(SysUser.class).size());
            for (String f : fieldNames(SysUser.class)) w.println(f);
        }

        // 边界用例：空 Set / 其余为 null（Java 侧 user 必然存在，否则 getPassword() 会 NPE）
        LoginUser empty = new LoginUser();
        empty.setPermissions(new HashSet<>());
        empty.setUser(new SysUser());
        String emptyStr = JSON.toJSONString(empty, JSONWriter.Feature.WriteClassName);
        try (PrintWriter w = new PrintWriter(new OutputStreamWriter(
                Files.newOutputStream(Paths.get(outDir, "login_user_empty.json")), StandardCharsets.UTF_8))) {
            w.print(emptyStr);
        }

        System.out.println("golden bytes=" + golden.getBytes(StandardCharsets.UTF_8).length);
        System.out.println(golden);
        System.out.println("--- empty ---");
        System.out.println(emptyStr);
        System.out.println("LoginUser fields=" + fieldNames(LoginUser.class).size()
                + " SysUser fields=" + fieldNames(SysUser.class).size());
    }
}
