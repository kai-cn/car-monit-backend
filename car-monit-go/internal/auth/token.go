// JAVA 对照: ruoyi-framework/src/main/java/com/ruoyi/framework/web/service/TokenService.java
// 类/职责: JWT + Redis 登录态 — 令牌创建、解析、续期、注销
// 对应 Go 文件: internal/auth/token.go
// 关键映射: io.jsonwebtoken.Jwts -> golang-jwt/jwt/v5；RedisCache -> internal/cache
//
// DIFF: JJWT 0.9.1 的 HS512 签名密钥按 UTF-8 字节取；golang-jwt 同样使用 []byte(secret)。
// DIFF: Java 用 session.getId() 记录会话；Go 无 HttpSession，生成随机 UUID 代替。
package auth

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/golang-jwt/jwt/v5"
	"github.com/google/uuid"

	"car-monit-go/internal/cache"
	"car-monit-go/internal/config"
	"car-monit-go/internal/model"
)

const (
	LoginTokenKey   = "login_tokens:"
	CaptchaCodeKey  = "captcha_codes:"
	SysConfigKey    = "sys_config:"
	SysDictKey      = "sys_dict:"
	RepeatSubmitKey = "repeat_submit:"
	RateLimitKey    = "rate_limit:"
	PwdErrCntKey    = "pwd_err_cnt:"

	LoginUserKey = "login_user_key"
	TokenPrefix  = "Bearer "
)

type TokenService struct {
	cfg   *config.Config
	cache *cache.Cache
}

func NewTokenService(cfg *config.Config, c *cache.Cache) *TokenService {
	return &TokenService{cfg: cfg, cache: c}
}

// GetToken 对应 TokenService.getToken。
func (s *TokenService) GetToken(c *gin.Context) string {
	token := c.GetHeader(s.cfg.Token.Header)
	if token != "" && strings.HasPrefix(token, TokenPrefix) {
		token = strings.TrimPrefix(token, TokenPrefix)
	}
	return token
}

// GetLoginUser 对应 TokenService.getLoginUser(HttpServletRequest)。
func (s *TokenService) GetLoginUser(ctx context.Context, c *gin.Context) *model.LoginUser {
	token := s.GetToken(c)
	if token == "" {
		return nil
	}
	return s.GetLoginUserByToken(ctx, token)
}

func (s *TokenService) GetLoginUserByToken(ctx context.Context, token string) *model.LoginUser {
	claims, err := s.parseToken(token)
	if err != nil {
		return nil
	}
	raw, ok := claims[LoginUserKey].(string)
	if !ok || raw == "" {
		return nil
	}
	var lu model.LoginUser
	if !s.cache.Get(ctx, LoginTokenKey+raw, &lu) {
		return nil
	}
	s.verifyToken(ctx, &lu)
	return &lu
}

// CreateToken 对应 TokenService.createToken(LoginUser)。
func (s *TokenService) CreateToken(ctx context.Context, lu *model.LoginUser, ip, ua string) (string, error) {
	raw := uuid.NewString()
	lu.Token = raw
	setUserAgent(lu, ip, ua)
	if err := s.refreshToken(ctx, lu); err != nil {
		return "", err
	}
	claims := jwt.MapClaims{LoginUserKey: raw}
	token := jwt.NewWithClaims(jwt.SigningMethodHS512, claims)
	return token.SignedString([]byte(s.cfg.Token.Secret))
}

// SetLoginUser 对应 TokenService.setLoginUser。
func (s *TokenService) SetLoginUser(ctx context.Context, lu *model.LoginUser) {
	if lu != nil && lu.Token != "" {
		_ = s.refreshToken(ctx, lu)
	}
}

// DelLoginUser 对应 TokenService.delLoginUser。
func (s *TokenService) DelLoginUser(ctx context.Context, token string) {
	if token != "" {
		s.cache.Delete(ctx, LoginTokenKey+token)
	}
}

// VerifyToken 对应 TokenService.verifyToken：剩余不足 20 分钟自动续期。
func (s *TokenService) verifyToken(ctx context.Context, lu *model.LoginUser) {
	expireMillis := lu.ExpireTime
	current := time.Now().UnixMilli()
	if expireMillis-current <= 20*60*1000 {
		_ = s.refreshToken(ctx, lu)
	}
}

func (s *TokenService) refreshToken(ctx context.Context, lu *model.LoginUser) error {
	now := time.Now()
	lu.LoginTime = now.UnixMilli()
	lu.ExpireTime = now.Add(time.Duration(s.cfg.Token.ExpireTime) * time.Minute).UnixMilli()
	return s.cache.Set(ctx, LoginTokenKey+lu.Token, lu, time.Duration(s.cfg.Token.ExpireTime)*time.Minute)
}

func (s *TokenService) parseToken(token string) (jwt.MapClaims, error) {
	parsed, err := jwt.Parse(token, func(t *jwt.Token) (any, error) {
		if _, ok := t.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, fmt.Errorf("unexpected signing method: %v", t.Header["alg"])
		}
		return []byte(s.cfg.Token.Secret), nil
	}, jwt.WithValidMethods([]string{"HS512"}), jwt.WithoutClaimsValidation())
	if err != nil {
		return nil, err
	}
	claims, ok := parsed.Claims.(jwt.MapClaims)
	if !ok {
		return nil, fmt.Errorf("invalid claims")
	}
	return claims, nil
}

// GetUsernameFromToken 对应 TokenService.getUsernameFromToken（JJWT subject，本项目未使用）。
func (s *TokenService) GetUsernameFromToken(token string) string {
	claims, err := s.parseToken(token)
	if err != nil {
		return ""
	}
	v, _ := claims["sub"].(string)
	return v
}

// setUserAgent 对应 TokenService.setUserAgent：解析 UA 与 IP。
func setUserAgent(lu *model.LoginUser, ip, ua string) {
	lu.SessionID = uuid.NewString()
	lu.IPAddr = ip
	lu.LoginLocation = addressByIP(ip)
	lu.Browser = browserName(ua)
	lu.OS = osName(ua)
}

func browserName(ua string) string {
	l := strings.ToLower(ua)
	switch {
	case strings.Contains(l, "edg/"):
		return "Edge"
	case strings.Contains(l, "chrome/"):
		return "Chrome"
	case strings.Contains(l, "firefox/"):
		return "Firefox"
	case strings.Contains(l, "safari/") && !strings.Contains(l, "chrome"):
		return "Safari"
	case strings.Contains(l, "msie") || strings.Contains(l, "trident"):
		return "Internet Explorer"
	default:
		return "Unknown"
	}
}

func osName(ua string) string {
	l := strings.ToLower(ua)
	switch {
	case strings.Contains(l, "windows"):
		return "Windows"
	case strings.Contains(l, "android"):
		return "Android"
	case strings.Contains(l, "iphone") || strings.Contains(l, "ipad"):
		return "iOS"
	case strings.Contains(l, "mac os"):
		return "Mac OS X"
	case strings.Contains(l, "linux"):
		return "Linux"
	default:
		return "Unknown"
	}
}

// addressByIP 对应 AddressUtils.getRealAddressByIP。
// DIFF: Java 用 ip2region 离线库解析省市；Go 侧未内置该库，内网 IP 返回“内网IP”，其余返回空串。
func addressByIP(ip string) string {
	if ip == "" {
		return ""
	}
	if ip == "127.0.0.1" || ip == "0:0:0:0:0:0:0:1" || strings.HasPrefix(ip, "192.168.") ||
		strings.HasPrefix(ip, "10.") || strings.HasPrefix(ip, "172.16.") {
		return "内网IP"
	}
	return ""
}

// MarshalLoginUser 便于把登录态写入 Redis（与 cache.Set 的 JSON 一致）。
func MarshalLoginUser(lu *model.LoginUser) (string, error) {
	b, err := json.Marshal(lu)
	return string(b), err
}
