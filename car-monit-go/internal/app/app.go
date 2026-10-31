// JAVA 对照: Spring IoC 容器（@Autowired 注入的 Bean 集合）
// 类/职责: 显式依赖装配 — 对应 Spring ApplicationContext
// 对应 Go 文件: internal/app/app.go
//
// DIFF: Go 社区主流是“main 中显式构造依赖”，没有 @ComponentScan。
// App 充当容器，handler 通过构造参数拿到它，而不是自动注入。
package app

import (
	"log/slog"

	"github.com/redis/go-redis/v9"
	"gorm.io/gorm"

	"car-monit-go/internal/auth"
	"car-monit-go/internal/cache"
	"car-monit-go/internal/config"
)

type App struct {
	Cfg    *config.Config
	DB     *gorm.DB
	Cache  *cache.Cache
	Redis  *redis.Client
	Log    *slog.Logger
	Tokens *auth.TokenService
	Auth   *auth.Service
}

func New(cfg *config.Config, db *gorm.DB, c *cache.Cache, log *slog.Logger) *App {
	tokens := auth.NewTokenService(cfg, c)
	return &App{
		Cfg:    cfg,
		DB:     db,
		Cache:  c,
		Redis:  c.Client(),
		Log:    log,
		Tokens: tokens,
		Auth:   auth.NewService(db, c, tokens, cfg, log),
	}
}
