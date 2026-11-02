// JAVA 对照: ruoyi-framework/.../TokenService.java#createToken/setLoginUser（RedisCache.setCacheObject）
// 类/职责: 登录态在 Redis 里的 Java 兼容视图
// 对应 Go 文件: internal/auth/login_cache.go
//
// Java 侧 RedisTemplate 的 value 用 FastJson2(WriteClassName) 序列化，
// login_tokens:* 里因此带 @type / Set[] / 253L / params 的 HashMap 标记，
// 且 null 字段不落盘。Go 若直接写标准 JSON，Java 的 getCacheObject 会拿到
// JSONObject 再强转 LoginUser 而抛 ClassCastException（/monitor/online/list 500 的根因）。
package auth

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"car-monit-go/internal/cache"
	"car-monit-go/internal/model"
)

// javaDateLayout 对应 fastjson2 默认的日期写法（Jackson 走的是 ISO8601）。
const javaDateLayout = "2006-01-02 15:04:05"

// loginUserCacheView 把 model.LoginUser 投影成 Java 缓存里的 LoginUser 形状。
func loginUserCacheView(lu *model.LoginUser) map[string]any {
	raw, err := json.Marshal(lu)
	if err != nil {
		return nil
	}
	var view map[string]any
	if err := json.Unmarshal(raw, &view); err != nil {
		return nil
	}
	// LoginUser.username：Java 登录时写入，online 列表用它显示登录账号
	view["username"] = lu.Username()
	user, _ := view["user"].(map[string]any)
	if user == nil || lu.User == nil {
		return view
	}
	// SysUser.password 在 HTTP 响应里被 @JsonIgnore，但 Redis 原值里有
	if lu.User.Password != nil {
		user["password"] = *lu.User.Password
	}
	ensureParams(user)
	if dept, ok := user["dept"].(map[string]any); ok {
		ensureParams(dept)
	}
	if roles, ok := user["roles"].([]any); ok {
		for _, item := range roles {
			if role, ok := item.(map[string]any); ok {
				ensureParams(role)
			}
		}
	}
	if text, ok := user["loginDate"].(string); ok {
		user["loginDate"] = javaDateText(text)
	}
	return view
}

// ensureParams 补 Java BaseEntity.params 的空 HashMap（序列化后是 {"@type":"java.util.HashMap"}）。
func ensureParams(m map[string]any) {
	if v, ok := m["params"].(map[string]any); ok && len(v) == 0 {
		return
	}
	if _, ok := m["params"].(map[string]any); !ok {
		m["params"] = map[string]any{}
	}
}

// javaDateText 把 ISO8601（Jackson 输出）换成 fastjson2 的 "yyyy-MM-dd HH:mm:ss"。
func javaDateText(s string) string {
	for _, layout := range []string{time.RFC3339Nano, "2006-01-02T15:04:05.000-07:00", "2006-01-02T15:04:05Z07:00"} {
		if t, err := time.Parse(layout, s); err == nil {
			return t.Format(javaDateLayout)
		}
	}
	return s
}

// storeLoginUser 写 login_tokens:*，格式与 Java 一致。
func (s *TokenService) storeLoginUser(ctx context.Context, lu *model.LoginUser) error {
	view := loginUserCacheView(lu)
	if view == nil {
		return fmt.Errorf("auth: 登录态无法编码为 Java 缓存格式")
	}
	ttl := time.Duration(s.cfg.Token.ExpireTime) * time.Minute
	return s.cache.SetJava(ctx, LoginTokenKey+lu.Token, view, ttl, cache.LoginUserJava)
}
