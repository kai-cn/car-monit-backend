// JAVA 对照: ruoyi-admin/src/main/java/com/ruoyi/web/controller/tool/TestController.java
// 类/职责: swagger 用户测试方法 — 进程内 LinkedHashMap 的用户 CRUD（不碰数据库）
// 对应 Go 文件: internal/modules/ops/test.go
//
// DIFF: Java 的 LinkedHashMap 非线程安全；Go 的 map 并发读写会直接 panic，因此这里加
// 互斥锁保护。单请求语义（插入顺序、put 已存在键不挪位置、update 先删后插挪到末尾）不变。
// DIFF: save 的形参**没有** @RequestBody，读 query string / 表单参数（不是 JSON 请求体）；
// update 读 JSON — 与 Java 一致。同名参数 query 优先于表单（Tomcat 的解析顺序）。
// DIFF: 登录即可访问，无权限点（SecurityConfig 落到 anyRequest().authenticated()）。
package ops

import (
	"encoding/json"
	"strconv"
	"strings"
	"sync"

	"github.com/gin-gonic/gin"

	"car-monit-go/internal/web"
)

// testUserEntity 对应 TestController.java 里包级可见的 UserEntity。
// 字段声明顺序即 Jackson 输出顺序；String 字段可为 null，所以用指针。
type testUserEntity struct {
	UserID   int     `json:"userId"`
	Username *string `json:"username"`
	Password *string `json:"password"`
	Mobile   *string `json:"mobile"`
}

// testUserInput 对应 Spring 绑定中的可空 Integer userId。
type testUserInput struct {
	UserID   *int    `json:"userId"`
	Username *string `json:"username"`
	Password *string `json:"password"`
	Mobile   *string `json:"mobile"`
}

func testStrPtr(v string) *string { return &v }

// JAVA 对照: private final static Map<Integer, UserEntity> users = new LinkedHashMap<>();
var (
	testUsersMu   sync.Mutex
	testUsers     = map[int]*testUserEntity{}
	testUserOrder = []int{}
)

func init() {
	resetTestUsers()
}

// resetTestUsers 把内存表恢复成 Java 实例初始化块里的两条种子数据。
func resetTestUsers() {
	testUsersMu.Lock()
	defer testUsersMu.Unlock()
	testUsers = map[int]*testUserEntity{
		1: {UserID: 1, Username: testStrPtr("admin"), Password: testStrPtr("admin123"), Mobile: testStrPtr("15888888888")},
		2: {UserID: 2, Username: testStrPtr("ry"), Password: testStrPtr("admin123"), Mobile: testStrPtr("15666666666")},
	}
	testUserOrder = []int{1, 2}
}

type testHandler struct{}

// List 对应 GET /test/user/list。
func (h *testHandler) List(c *gin.Context) {
	testUsersMu.Lock()
	rows := make([]*testUserEntity, 0, len(testUserOrder))
	for _, id := range testUserOrder {
		if row, ok := testUsers[id]; ok {
			rows = append(rows, row)
		}
	}
	testUsersMu.Unlock()
	web.JSON(c, web.ROK(rows))
}

// GetUser 对应 GET /test/user/{userId}。
func (h *testHandler) GetUser(c *gin.Context) {
	id, ok := parseTestUserID(c)
	if !ok {
		return
	}
	testUsersMu.Lock()
	row, exists := testUsers[id]
	testUsersMu.Unlock()
	if exists {
		web.JSON(c, web.ROK(row))
		return
	}
	web.JSON(c, web.RFailMsg("用户不存在"))
}

// Save 对应 POST /test/user/save（query / 表单参数，**不是** JSON 请求体）。
func (h *testHandler) Save(c *gin.Context) {
	input, err := bindTestUserParams(c)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if input.UserID == nil {
		web.JSON(c, web.RFailMsg("用户ID不能为空"))
		return
	}
	entity := &testUserEntity{
		UserID:   *input.UserID,
		Username: input.Username,
		Password: input.Password,
		Mobile:   input.Mobile,
	}
	testUsersMu.Lock()
	if _, exists := testUsers[entity.UserID]; !exists {
		testUserOrder = append(testUserOrder, entity.UserID)
	}
	// Java: LinkedHashMap.put —— 已存在键只改值、不挪位置。
	testUsers[entity.UserID] = entity
	testUsersMu.Unlock()
	web.JSON(c, web.ROK(nil))
}

// Update 对应 PUT /test/user/update（@RequestBody JSON）。
func (h *testHandler) Update(c *gin.Context) {
	var input testUserInput
	if err := json.NewDecoder(c.Request.Body).Decode(&input); err != nil {
		web.JSON(c, web.ErrorMsg(err.Error()))
		return
	}
	if input.UserID == nil {
		web.JSON(c, web.RFailMsg("用户ID不能为空"))
		return
	}
	entity := &testUserEntity{
		UserID:   *input.UserID,
		Username: input.Username,
		Password: input.Password,
		Mobile:   input.Mobile,
	}
	testUsersMu.Lock()
	if _, exists := testUsers[entity.UserID]; !exists {
		testUsersMu.Unlock()
		web.JSON(c, web.RFailMsg("用户不存在"))
		return
	}
	// Java: remove + put —— 在 LinkedHashMap 里等于删了再插，位置推到末尾。
	testUserOrder = removeTestUserID(testUserOrder, entity.UserID)
	testUserOrder = append(testUserOrder, entity.UserID)
	testUsers[entity.UserID] = entity
	testUsersMu.Unlock()
	web.JSON(c, web.ROK(nil))
}

// Delete 对应 DELETE /test/user/{userId}。
func (h *testHandler) Delete(c *gin.Context) {
	id, ok := parseTestUserID(c)
	if !ok {
		return
	}
	testUsersMu.Lock()
	if _, exists := testUsers[id]; exists {
		delete(testUsers, id)
		testUserOrder = removeTestUserID(testUserOrder, id)
		testUsersMu.Unlock()
		web.JSON(c, web.ROK(nil))
		return
	}
	testUsersMu.Unlock()
	web.JSON(c, web.RFailMsg("用户不存在"))
}

// parseTestUserID 对应 @PathVariable Integer：非法数字走参数类型不匹配（code 500）。
func parseTestUserID(c *gin.Context) (int, bool) {
	raw := c.Param("userId")
	id, err := strconv.Atoi(raw)
	if err != nil {
		web.JSON(c, web.ErrorResult(typeMismatch("userId", "java.lang.Integer", raw)))
		return 0, false
	}
	return id, true
}

// bindTestUserParams 复刻 Spring 对无 @RequestBody 形参的绑定：
// 读 query string 与 application/x-www-form-urlencoded / multipart 表单，query 优先。
func bindTestUserParams(c *gin.Context) (*testUserInput, error) {
	_ = c.Request.ParseMultipartForm(32 << 20)
	merged := make(map[string]string)
	for key, values := range c.Request.PostForm {
		if len(values) > 0 {
			merged[key] = values[0]
		}
	}
	// Tomcat 先解析 query string 再解析请求体 -> 同名时 query 的值胜出。
	for key, values := range c.Request.URL.Query() {
		if len(values) > 0 {
			merged[key] = values[0]
		}
	}

	input := &testUserInput{}
	if raw, ok := merged["userId"]; ok {
		// Spring: 空串转 null（Integer 是非 String 类型）。
		if trimmed := strings.TrimSpace(raw); trimmed != "" {
			id, err := strconv.Atoi(trimmed)
			if err != nil {
				return nil, typeMismatch("userId", "java.lang.Integer", raw)
			}
			input.UserID = &id
		}
	}
	if value, ok := merged["username"]; ok {
		input.Username = testStrPtr(value)
	}
	if value, ok := merged["password"]; ok {
		input.Password = testStrPtr(value)
	}
	if value, ok := merged["mobile"]; ok {
		input.Mobile = testStrPtr(value)
	}
	return input, nil
}

// removeTestUserID 从插入顺序里摘掉一个 id（保持其余元素顺序）。
func removeTestUserID(order []int, id int) []int {
	out := order[:0]
	for _, item := range order {
		if item != id {
			out = append(out, item)
		}
	}
	return out
}

// newTestRoutes 注册 /test/user/**。
func newTestRoutes(reg gin.IRouter) {
	h := &testHandler{}
	g := reg.Group("/test/user")
	g.GET("/list", h.List)
	g.GET("/:userId", h.GetUser)
	g.POST("/save", h.Save)
	g.PUT("/update", h.Update)
	g.DELETE("/:userId", h.Delete)
}
