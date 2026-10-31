// JAVA 对照: com.ruoyi.base.domain.DwdLcztFwqjcxx / DwdLcztSfsjcxx / DwdLcztSfzjcxx
// 类/职责: 服务区 / 收费所 / 收费站（治超）基础信息（dwd 只读表）
// 对应 Go 文件: internal/modules/base/models_dwd.go
//
// DIFF: 这三张表的列名是下划线风格、Java 属性名保留原拼音（yxtzj / fwqbm / sczhkgs …），
// JSON 键名与 Java 字段名逐字一致。
package base

// dwdLcztFwqjcxx 对应 DwdLcztFwqjcxx（@TableId agent_pk, INPUT）。
type dwdLcztFwqjcxx struct {
	AgentPk   *string `json:"agentPk" gorm:"column:agent_pk"`
	Yxtzj     *string `json:"yxtzj" gorm:"column:yxtzj"`
	Fwqbm     *string `json:"fwqbm" gorm:"column:fwqbm"`
	Fwqmc     *string `json:"fwqmc" gorm:"column:fwqmc"`
	Wd        *string `json:"wd" gorm:"column:wd"`
	Fxmc      *string `json:"fxmc" gorm:"column:fxmc"`
	Fxdm      *string `json:"fxdm" gorm:"column:fxdm"`
	Jd        *string `json:"jd" gorm:"column:jd"`
	Sslxbh    *string `json:"sslxbh" gorm:"column:sslxbh"`
	Sslxmc    *string `json:"sslxmc" gorm:"column:sslxmc"`
	Ssldbh    *string `json:"ssldbh" gorm:"column:ssldbh"`
	Ssldmc    *string `json:"ssldmc" gorm:"column:ssldmc"`
	Sczhkgs   *string `json:"sczhkgs" gorm:"column:sczhkgs"`
	Sczhszgs  *string `json:"sczhszgs" gorm:"column:sczhszgs"`
	Ssglzxbm  *string `json:"ssglzxbm" gorm:"column:ssglzxbm"`
	Ssglzxmc  *string `json:"ssglzxmc" gorm:"column:ssglzxmc"`
	Xzqhmc    *string `json:"xzqhmc" gorm:"column:xzqhmc"`
	Yyrq      *string `json:"yyrq" gorm:"column:yyrq"`
	Cws       *string `json:"cws" gorm:"column:cws"`
	Sfszlkk   *string `json:"sfszlkk" gorm:"column:sfszlkk"`
	Cdzs      *string `json:"cdzs" gorm:"column:cdzs"`
	Sfcyfw    *string `json:"sfcyfw" gorm:"column:sfcyfw"`
	Sftgzsfw  *string `json:"sftgzsfw" gorm:"column:sftgzsfw"`
	Sftgqxfw  *string `json:"sftgqxfw" gorm:"column:sftgqxfw"`
	Sftgcsfw  *string `json:"sftgcsfw" gorm:"column:sftgcsfw"`
	Sftgjyfw  *string `json:"sftgjyfw" gorm:"column:sftgjyfw"`
	Mj        *string `json:"mj" gorm:"column:mj"`
	Sftgcshfw *string `json:"sftgcshfw" gorm:"column:sftgcshfw"`
	Xzqhdm    *string `json:"xzqhdm" gorm:"column:xzqhdm"`
	Synx      *string `json:"synx" gorm:"column:synx"`
	Lyxt      *string `json:"lyxt" gorm:"column:lyxt"`
	LoadTime  *string `json:"loadTime" gorm:"column:load_time"`
	AllColPk  *string `json:"allColPk" gorm:"column:all_col_pk"`

	// @TableField(exist = false)
	SectionCodeList []*string `json:"sectionCodeList" gorm:"-"`
}

// dwdLcztSfsjcxx 对应 DwdLcztSfsjcxx（收费所，@TableId agent_pk）。
type dwdLcztSfsjcxx struct {
	AgentPk  *string `json:"agentPk" gorm:"column:agent_pk"`
	Yxtzj    *string `json:"yxtzj" gorm:"column:yxtzj"`
	Sfsbm    *string `json:"sfsbm" gorm:"column:sfsbm"`
	Sfsmc    *string `json:"sfsmc" gorm:"column:sfsmc"`
	Jd       *string `json:"jd" gorm:"column:jd"`
	Wd       *string `json:"wd" gorm:"column:wd"`
	Sslxbh   *string `json:"sslxbh" gorm:"column:sslxbh"`
	Sslxmc   *string `json:"sslxmc" gorm:"column:sslxmc"`
	Ssldbh   *string `json:"ssldbh" gorm:"column:ssldbh"`
	Ssldmc   *string `json:"ssldmc" gorm:"column:ssldmc"`
	SczhK    *string `json:"sczhK" gorm:"column:sczh_k"`
	SczhN    *string `json:"sczhN" gorm:"column:sczh_n"`
	Ssglzxbm *string `json:"ssglzxbm" gorm:"column:ssglzxbm"`
	Ssglzxmc *string `json:"ssglzxmc" gorm:"column:ssglzxmc"`
	Lyxt     *string `json:"lyxt" gorm:"column:lyxt"`
	LoadTime *string `json:"loadTime" gorm:"column:load_time"`
	AllColPk *string `json:"allColPk" gorm:"column:all_col_pk"`
}

// dwdLcztSfzjcxx 对应 DwdLcztSfzjcxx（收费站治超，@TableId agent_pk）。
type dwdLcztSfzjcxx struct {
	AgentPk  *string `json:"agentPk" gorm:"column:agent_pk"`
	Yxtzj    *string `json:"yxtzj" gorm:"column:yxtzj"`
	Sfzdm    *string `json:"sfzdm" gorm:"column:sfzdm"`
	Sfzmc    *string `json:"sfzmc" gorm:"column:sfzmc"`
	Jd       *string `json:"jd" gorm:"column:jd"`
	Wd       *string `json:"wd" gorm:"column:wd"`
	Sslxbh   *string `json:"sslxbh" gorm:"column:sslxbh"`
	Sslxmc   *string `json:"sslxmc" gorm:"column:sslxmc"`
	Ssldbh   *string `json:"ssldbh" gorm:"column:ssldbh"`
	Ssldmc   *string `json:"ssldmc" gorm:"column:ssldmc"`
	SczhK    *string `json:"sczhK" gorm:"column:sczh_k"`
	SczhN    *string `json:"sczhN" gorm:"column:sczh_n"`
	Ssglzxbm *string `json:"ssglzxbm" gorm:"column:ssglzxbm"`
	Ssglzxmc *string `json:"ssglzxmc" gorm:"column:ssglzxmc"`
	Lyxt     *string `json:"lyxt" gorm:"column:lyxt"`
	LoadTime *string `json:"loadTime" gorm:"column:load_time"`
	AllColPk *string `json:"allColPk" gorm:"column:all_col_pk"`
}
