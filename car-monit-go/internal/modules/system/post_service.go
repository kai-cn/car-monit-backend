// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysPostServiceImpl.java:31-181
// JAVA 对照: ruoyi-system/src/main/resources/mapper/system/SysPostMapper.xml
// 类/职责: 岗位业务层 —— 列表/详情/用户岗位/唯一性校验/增删改
// 对应 Go 文件: internal/modules/system/post_service.go
package system

import (
	"context"
	"strings"

	"github.com/gin-gonic/gin"

	"car-monit-go/internal/model"
	"car-monit-go/internal/web"
)

// postQuery 对应作为查询条件的 SysPost。
type postQuery struct {
	PostCode string
	Status   string
	PostName string
}

func parsePostQuery(c *gin.Context) postQuery {
	return postQuery{
		PostCode: queryStr(c, "postCode"),
		Status:   queryStr(c, "status"),
		PostName: queryStr(c, "postName"),
	}
}

// postSelectVo 对应 SysPostMapper.xml:20-23 selectPostVo。
const postSelectVo = `
	select post_id, post_code, post_name, post_sort, status, create_by, create_time, remark
	from sys_post`

func (q postQuery) where() (string, []any) {
	var sb strings.Builder
	args := make([]any, 0, 3)
	first := true
	and := func(cond string, v any) {
		if first {
			sb.WriteString(" where ")
			first = false
		} else {
			sb.WriteString(" and ")
		}
		sb.WriteString(cond)
		args = append(args, v)
	}
	if q.PostCode != "" {
		and("post_code like concat('%', ?, '%')", q.PostCode)
	}
	if q.Status != "" {
		and("status = ?", q.Status)
	}
	if q.PostName != "" {
		and("post_name like concat('%', ?, '%')", q.PostName)
	}
	return sb.String(), args
}

// selectPostList 对应 SysPostServiceImpl.selectPostList（无默认排序，保留 PageHelper 原样）。
func (s *service) selectPostList(ctx context.Context, q postQuery, pd web.PageDomain) ([]model.SysPost, int64, error) {
	where, args := q.where()
	rows, total, err := queryPaged[model.SysPost](ctx, s.db(ctx), pd, postSelectVo+where, args, orderByOr(pd, ""))
	if err != nil {
		return nil, 0, err
	}
	return nonNilSlice(rows), total, nil
}

// selectPostAll 对应 SysPostMapper.selectPostAll。
func (s *service) selectPostAll(ctx context.Context) ([]model.SysPost, error) {
	rows := make([]model.SysPost, 0)
	err := s.db(ctx).Raw(postSelectVo).Scan(&rows).Error
	return rows, err
}

// selectPostByID 对应 SysPostMapper.selectPostById。
func (s *service) selectPostByID(ctx context.Context, postID int64) (*model.SysPost, error) {
	var p model.SysPost
	if err := s.db(ctx).Raw(postSelectVo+" where post_id = ?", postID).Scan(&p).Error; err != nil {
		return nil, err
	}
	if p.PostID == 0 {
		return nil, nil
	}
	return &p, nil
}

// selectPostListByUserID 对应 SysPostMapper.selectPostListByUserId。
func (s *service) selectPostListByUserID(ctx context.Context, userID int64) ([]int64, error) {
	ids := make([]int64, 0)
	err := s.db(ctx).Raw(`
		select p.post_id
		from sys_post p
		left join sys_user_post up on up.post_id = p.post_id
		left join sys_user u on u.user_id = up.user_id
		where u.user_id = ?`, userID).Scan(&ids).Error
	return ids, err
}

// selectPostsByUserName 对应 SysPostMapper.selectPostsByUserName。
func (s *service) selectPostsByUserName(ctx context.Context, userName string) ([]model.SysPost, error) {
	rows := make([]model.SysPost, 0)
	err := s.db(ctx).Raw(`
		select p.post_id, p.post_name, p.post_code
		from sys_post p
		left join sys_user_post up on up.post_id = p.post_id
		left join sys_user u on u.user_id = up.user_id
		where u.user_name = ?`, userName).Scan(&rows).Error
	return rows, err
}

// checkPostNameUnique 对应 SysPostMapper.checkPostNameUnique（用于服务层唯一性校验）。
func (s *service) checkPostNameUnique(ctx context.Context, postName string) (*model.SysPost, error) {
	var p model.SysPost
	if err := s.db(ctx).Raw(postSelectVo+" where post_name = ? limit 1", postName).Scan(&p).Error; err != nil {
		return nil, err
	}
	if p.PostID == 0 {
		return nil, nil
	}
	return &p, nil
}

// checkPostCodeUnique 对应 SysPostMapper.checkPostCodeUnique。
func (s *service) checkPostCodeUnique(ctx context.Context, postCode string) (*model.SysPost, error) {
	var p model.SysPost
	if err := s.db(ctx).Raw(postSelectVo+" where post_code = ? limit 1", postCode).Scan(&p).Error; err != nil {
		return nil, err
	}
	if p.PostID == 0 {
		return nil, nil
	}
	return &p, nil
}

// countUserPostByID 对应 SysUserPostMapper.countUserPostById。
func (s *service) countUserPostByID(ctx context.Context, postID int64) (int64, error) {
	var n int64
	err := s.db(ctx).Raw("select count(1) from sys_user_post where post_id = ?", postID).Scan(&n).Error
	return n, err
}

// postBody 对应 @RequestBody SysPost。
type postBody struct {
	PostID   *int64  `json:"postId"`
	PostCode *string `json:"postCode"`
	PostName *string `json:"postName"`
	PostSort *string `json:"postSort"`
	Status   *string `json:"status"`
	Remark   *string `json:"remark"`
}

// validate 对应 SysPost 上的 @Validated 约束。
func (b *postBody) validate() string {
	switch {
	case strings.TrimSpace(strOr(b.PostCode)) == "":
		return "岗位编码不能为空"
	case len([]rune(strOr(b.PostCode))) > 64:
		return "岗位编码长度不能超过64个字符"
	case strings.TrimSpace(strOr(b.PostName)) == "":
		return "岗位名称不能为空"
	case len([]rune(strOr(b.PostName))) > 50:
		return "岗位名称长度不能超过50个字符"
	case strings.TrimSpace(strOr(b.PostSort)) == "":
		return "显示顺序不能为空"
	}
	return ""
}

// insertPost 对应 SysPostMapper.insertPost（useGeneratedKeys）。
func (s *service) insertPost(ctx context.Context, b *postBody, createBy string) (int64, error) {
	cols := make([]string, 0, 8)
	vals := make([]any, 0, 8)
	add := func(col string, v any) {
		cols = append(cols, col)
		vals = append(vals, v)
	}
	if b.PostID != nil && *b.PostID != 0 {
		add("post_id", *b.PostID)
	}
	if strOr(b.PostCode) != "" {
		add("post_code", *b.PostCode)
	}
	if strOr(b.PostName) != "" {
		add("post_name", *b.PostName)
	}
	if strOr(b.PostSort) != "" {
		add("post_sort", *b.PostSort)
	}
	if strOr(b.Status) != "" {
		add("status", *b.Status)
	}
	if strOr(b.Remark) != "" {
		add("remark", *b.Remark)
	}
	if createBy != "" {
		add("create_by", createBy)
	}
	add("create_time", now())
	sql := "insert into sys_post (" + strings.Join(cols, ", ") + ") values (" + placeholders(len(cols)) + ")"
	res := s.db(ctx).Exec(sql, vals...)
	return res.RowsAffected, res.Error
}

// updatePost 对应 SysPostMapper.updatePost 的 <set>（remark 非 null 即写，允许空串）。
func (s *service) updatePost(ctx context.Context, b *postBody, updateBy string) (int64, error) {
	if b.PostID == nil {
		return 0, web.NewServiceError("岗位ID不能为空")
	}
	sets := make([]string, 0, 8)
	args := make([]any, 0, 8)
	strCol := func(col string, p *string, requireNonEmpty bool) {
		if p == nil {
			return
		}
		if requireNonEmpty && *p == "" {
			return
		}
		sets = append(sets, col+" = ?")
		args = append(args, *p)
	}
	strCol("post_code", b.PostCode, true)
	strCol("post_name", b.PostName, true)
	strCol("post_sort", b.PostSort, true)
	strCol("status", b.Status, true)
	strCol("remark", b.Remark, false)
	if updateBy != "" {
		sets = append(sets, "update_by = ?")
		args = append(args, updateBy)
	}
	sets = append(sets, "update_time = ?")
	args = append(args, now())
	args = append(args, *b.PostID)
	res := s.db(ctx).Exec("update sys_post set "+strings.Join(sets, ", ")+" where post_id = ?", args...)
	return res.RowsAffected, res.Error
}

// deletePostByIDs 对应 SysPostServiceImpl.deletePostByIds：已分配用户的岗位不允许删除。
func (s *service) deletePostByIDs(ctx context.Context, postIDs []int64) (int64, error) {
	for _, id := range postIDs {
		post, err := s.selectPostByID(ctx, id)
		if err != nil {
			return 0, err
		}
		count, err := s.countUserPostByID(ctx, id)
		if err != nil {
			return 0, err
		}
		if count > 0 {
			name := ""
			if post != nil {
				name = model.Str(post.PostName)
			}
			return 0, web.NewServiceError("%s已分配,不能删除", name)
		}
	}
	args := make([]any, 0, len(postIDs))
	for _, id := range postIDs {
		args = append(args, id)
	}
	res := s.db(ctx).Exec("delete from sys_post where post_id in ("+placeholders(len(postIDs))+")", args...)
	return res.RowsAffected, res.Error
}
