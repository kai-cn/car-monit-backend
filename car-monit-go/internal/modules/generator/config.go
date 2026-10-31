// JAVA 对照: ruoyi-generator/src/main/java/com/ruoyi/generator/config/GenConfig.java
// JAVA 对照: ruoyi-generator/src/main/resources/generator.yml
// 类/职责: 生成器自身配置（author / packageName / autoRemovePre / tablePrefix）
// 对应 Go 文件: internal/modules/generator/config.go
//
// DIFF: Java 用 @PropertySource("classpath:generator.yml")；Go 把 generator.yml 放在
// config.yaml 同目录，缺失时使用与 Java 资源文件相同的兜底值（生成器不拖垮整个服务）。
package generator

import (
	"path/filepath"

	"github.com/spf13/viper"
)

type genConfig struct {
	Author        string
	PackageName   string
	AutoRemovePre bool
	TablePrefix   string
}

func defaultGenConfig() genConfig {
	return genConfig{
		Author:        "ruoyi",
		PackageName:   "com.ruoyi.manager",
		AutoRemovePre: false,
		TablePrefix:   "sys_",
	}
}

// loadGenConfig 读取 <config.yaml 所在目录>/generator.yml。
// 键既支持 Java 资源文件里的 gen.* 层次，也支持平铺写法。
func loadGenConfig(configFile string) genConfig {
	cfg := defaultGenConfig()
	if configFile == "" {
		return cfg
	}
	path := filepath.Join(filepath.Dir(configFile), "generator.yml")
	v := viper.New()
	v.SetConfigFile(path)
	v.SetConfigType("yaml")
	if err := v.ReadInConfig(); err != nil {
		return cfg
	}
	author := v.GetString("gen.author")
	if author == "" {
		author = v.GetString("author")
	}
	if author != "" {
		cfg.Author = author
	}
	pkg := v.GetString("gen.packageName")
	if pkg == "" {
		pkg = v.GetString("packageName")
	}
	if pkg != "" {
		cfg.PackageName = pkg
	}
	if v.IsSet("gen.autoRemovePre") {
		cfg.AutoRemovePre = v.GetBool("gen.autoRemovePre")
	} else if v.IsSet("autoRemovePre") {
		cfg.AutoRemovePre = v.GetBool("autoRemovePre")
	}
	prefix := v.GetString("gen.tablePrefix")
	if prefix == "" {
		prefix = v.GetString("tablePrefix")
	}
	if prefix != "" {
		cfg.TablePrefix = prefix
	}
	return cfg
}

// templateRoot 为模板根目录（config.yaml 同目录下的 vm/ 与 vmplus/）。
// JAVA 对照: Velocity 的 classpath 根（ruoyi-generator/src/main/resources）。
func templateRoot(configFile string) string {
	if configFile == "" {
		return "."
	}
	return filepath.Dir(configFile)
}
