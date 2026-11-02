// 类/职责: FastJson2 兼容编解码的单测（样本取自 Java 进程真实写入的 login_tokens:* 值）
package cache

import (
	"encoding/json"
	"strings"
	"testing"
)

// javaLogin 是 Java(9988) 写进 Redis 的原值片段，含 @type、Set[]、Long 的 L 后缀、嵌套 params。
const javaLogin = `{"@type":"com.ruoyi.common.core.domain.model.LoginUser","browser":"Unknown",` +
	`"expireTime":1793594971681,"ipaddr":"127.0.0.1","loginTime":1793587771681,` +
	`"permissions":Set["*:*:*"],"token":"68c88b29","user":{"admin":true,"deptId":25367L,` +
	`"dept":{"deptId":25367L,"params":{"@type":"java.util.HashMap"},"parentId":25339L},` +
	`"params":{"@type":"java.util.HashMap"},"roles":[{"@type":"com.ruoyi.Foo","params":{"@type":"java.util.HashMap"},"roleId":1L}],` +
	`"userId":1L,"username":"admin"}}`

type loginUserShape struct {
	Token       string   `json:"token"`
	Permissions []string `json:"permissions"`
	ExpireTime  int64    `json:"expireTime"`
	User        struct {
		UserID int64          `json:"userId"`
		DeptID int64          `json:"deptId"`
		Params map[string]any `json:"params"`
		Roles  []struct {
			RoleID int64          `json:"roleId"`
			Params map[string]any `json:"params"`
		} `json:"roles"`
	} `json:"user"`
}

func TestFromJavaStripsFastJson2Syntax(t *testing.T) {
	clean := string(FromJava([]byte(javaLogin)))
	for _, bad := range []string{"Set["} {
		if strings.Contains(clean, bad) {
			t.Errorf("FromJava 后仍残留 %q: %s", bad, clean)
		}
	}
	if strings.Contains(clean, "L,") || strings.Contains(clean, "L}") {
		t.Errorf("FromJava 后仍有 Long 的 L 后缀: %s", clean)
	}
	// @type 是保留的：Java 把它读进 Map<String,Object> 后会原样输出到响应里
	if !strings.Contains(clean, `"@type":"com.ruoyi.common.core.domain.model.LoginUser"`) {
		t.Errorf("@type 应保留: %s", clean)
	}
	var got loginUserShape
	if err := json.Unmarshal([]byte(clean), &got); err != nil {
		t.Fatalf("还原后的文本不是合法 JSON: %v\n%s", err, clean)
	}
	if got.User.UserID != 1 || got.User.DeptID != 25367 || got.ExpireTime != 1793594971681 {
		t.Errorf("数值解析错位: %+v", got)
	}
	if len(got.Permissions) != 1 || got.Permissions[0] != "*:*:*" {
		t.Errorf("Set[] 未还原成数组: %v", got.Permissions)
	}
	if len(got.User.Roles) != 1 || got.User.Roles[0].RoleID != 1 {
		t.Errorf("嵌套数组未还原: %v", got.User.Roles)
	}
	if got.User.Params["@type"] != "java.util.HashMap" {
		t.Errorf("params 应保留 Java 的 @type 成员，实际 %v", got.User.Params)
	}
}

func TestToJavaWritesFastJson2Syntax(t *testing.T) {
	value := map[string]any{
		"token":       "68c88b29",
		"expireTime":  int64(1793594971681),
		"loginTime":   int64(1793587771681),
		"permissions": []string{"*:*:*"},
		"remark":      nil,
		"user": map[string]any{
			"userId": int64(1),
			"deptId": int64(25367),
			"params": map[string]any{},
			"roles": []any{
				map[string]any{"roleId": int64(1), "params": map[string]any{}},
			},
		},
	}
	raw, err := ToJava(value, LoginUserJava)
	if err != nil {
		t.Fatal(err)
	}
	got := string(raw)
	for _, want := range []string{
		`"@type":"com.ruoyi.common.core.domain.model.LoginUser"`,
		`"permissions":Set["*:*:*"]`,
		`"deptId":25367L`,
		`"userId":1L`,
		`"roleId":1L`,
		`"params":{"@type":"java.util.HashMap"}`,
	} {
		if !strings.Contains(got, want) {
			t.Errorf("缺少 %s\n实际: %s", want, got)
		}
	}
	// 原始类型 long 不补 L；null 成员不写
	if strings.Contains(got, "expireTime\":1793594971681L") || strings.Contains(got, `"remark"`) {
		t.Errorf("不该出现 L 后缀或 null 成员: %s", got)
	}
	// 写出的值必须能被读回（Java -> Go -> Java 闭环）
	var back loginUserShape
	if err := json.Unmarshal(FromJava(raw), &back); err != nil {
		t.Fatalf("ToJava 的值读不回来: %v\n%s", err, got)
	}
	if back.User.Roles[0].RoleID != 1 {
		t.Errorf("回读错位: %+v", back)
	}
}

func TestToJavaForcesParamsOnElements(t *testing.T) {
	// sys_dict：Java 空 HashMap 也会写出类型标记，Go 从库里读出的行没有 params 字段
	rows := []any{
		map[string]any{"dictCode": int64(1), "dictType": "sys_x"},
		map[string]any{"dictCode": int64(2), "dictType": "sys_x"},
	}
	raw, err := ToJava(rows, SysDictDataJava)
	if err != nil {
		t.Fatal(err)
	}
	got := string(raw)
	if strings.Count(got, `"params":{"@type":"java.util.HashMap"}`) != 2 {
		t.Errorf("数组每个元素都应补 params: %s", got)
	}
	// 根对象不补：LoginUser 自己没有 params 字段
	root, err := ToJava(map[string]any{
		"token": "t",
		"user":  map[string]any{"userId": int64(1)},
	}, LoginUserJava)
	if err != nil {
		t.Fatal(err)
	}
	if strings.Count(string(root), `"params":{"@type":"java.util.HashMap"}`) != 1 {
		t.Errorf("只应给嵌套的 user 补 params: %s", root)
	}
}

func TestToJavaRootArrayWritesTypePerElement(t *testing.T) {
	rows := []any{
		map[string]any{"id": "1", "epsId": int64(25367)},
		map[string]any{"id": "2"},
	}
	opts := JavaOptions{RootType: "com.ruoyi.manager.domain.CarInfo", Longs: map[string]bool{"epsId": true}}
	raw, err := ToJava(rows, opts)
	if err != nil {
		t.Fatal(err)
	}
	got := string(raw)
	if strings.Count(got, `"@type":"com.ruoyi.manager.domain.CarInfo"`) != 2 {
		t.Errorf("根数组每个元素都应带 @type: %s", got)
	}
	if !strings.Contains(got, `"epsId":25367L`) {
		t.Errorf("Long 未补 L: %s", got)
	}
	if !strings.HasPrefix(got, `[{`) {
		t.Errorf("根数组首个元素应紧跟 @type: %s", got)
	}
}
