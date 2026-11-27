// JAVA 对照: org.apache.velocity:velocity-engine-core:2.3（模板引擎，无对应 Java 源文件）
// JAVA 对照: ruoyi-generator/src/main/java/com/ruoyi/generator/util/VelocityInitializer.java
// 类/职责: Velocity 2.3 子集解释器 — 预览 / 下载 / 生成代码必须与 Java 逐字符一致
// 对应 Go 文件: internal/modules/generator/velocity.go
//
// DIFF: Java 侧由 Apache Velocity 解释 .vm；Go 侧移植 car-monit-py 的同一实现，
// 保留 space.gobbling=lines、未定义引用原样输出、$foreach 状态等可观测行为。
// 模板文件原封不动使用 configs/vm、configs/vmplus（与 Java classpath 同构）。
package generator

import (
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"reflect"
	"regexp"
	"strconv"
	"strings"
	"sync"
)

// ---------------------------------------------------------------------------
// 未定义 / 上下文
// ---------------------------------------------------------------------------

type undefinedType struct{}

func (u *undefinedType) String() string { return "UNDEFINED" }

var undefined = &undefinedType{}

func isUndefined(value any) bool {
	_, ok := value.(*undefinedType)
	return ok
}

// velocityContext 对应 org.apache.velocity.VelocityContext（get/put 字典）。
type velocityContext struct {
	values map[string]any
}

func newVelocityContext() *velocityContext {
	return &velocityContext{values: map[string]any{}}
}

func (c *velocityContext) Put(key string, value any) { c.values[key] = value }

func (c *velocityContext) get(key string) (any, bool) {
	value, ok := c.values[key]
	return value, ok
}

func (c *velocityContext) Lookup(key string) any {
	if value, ok := c.values[key]; ok {
		return value
	}
	return undefined
}

func (c *velocityContext) remove(key string) { delete(c.values, key) }

// ---------------------------------------------------------------------------
// 节点
// ---------------------------------------------------------------------------

var errBreakLoop = errors.New("velocity break")

type velocityNode interface {
	render(ctx *velocityContext, out *strings.Builder) error
}

type textNode struct{ text string }

func (n *textNode) render(_ *velocityContext, out *strings.Builder) error {
	out.WriteString(n.text)
	return nil
}

type refStep struct {
	property bool
	name     string
	args     []velocityExpr
}

// velocityRef 对应 Java ASTReference：根变量 + 属性/方法链。
type velocityRef struct {
	raw   string
	root  string
	chain []refStep
	quiet bool
}

func (r *velocityRef) evaluate(ctx *velocityContext) any {
	value := ctx.Lookup(r.root)
	for _, step := range r.chain {
		if value == nil || isUndefined(value) {
			return undefined
		}
		if step.property {
			value = getProperty(value, step.name)
		} else {
			args := make([]any, 0, len(step.args))
			for _, arg := range step.args {
				args = append(args, evalExpr(arg, ctx))
			}
			value = callMethod(value, step.name, args)
		}
		if isUndefined(value) {
			return undefined
		}
	}
	return value
}

func (r *velocityRef) render(ctx *velocityContext, out *strings.Builder) error {
	value := r.evaluate(ctx)
	if value == nil || isUndefined(value) {
		// Java: 求值不到 null 时把引用原文写回输出流。
		if !r.quiet {
			out.WriteString(r.raw)
		}
		return nil
	}
	out.WriteString(toJavaString(value))
	return nil
}

type ifBranch struct {
	condition velocityExpr
	nodes     []velocityNode
}

type ifNode struct {
	branches  []ifBranch
	elseNodes []velocityNode
}

func (n *ifNode) render(ctx *velocityContext, out *strings.Builder) error {
	for _, branch := range n.branches {
		if truthy(evalExpr(branch.condition, ctx)) {
			return renderNodes(branch.nodes, ctx, out)
		}
	}
	return renderNodes(n.elseNodes, ctx, out)
}

type foreachStatus struct {
	Index   int
	Count   int
	HasNext bool
	First   bool
	Last    bool
}

type foreachNode struct {
	varName  string
	iterable velocityExpr
	body     []velocityNode
}

func (n *foreachNode) render(ctx *velocityContext, out *strings.Builder) error {
	items := evalExpr(n.iterable, ctx)
	if items == nil || isUndefined(items) {
		// Java: 迭代 null 集合 —— 循环体一次都不执行。
		return nil
	}
	rvs := reflect.ValueOf(items)
	for rvs.Kind() == reflect.Pointer || rvs.Kind() == reflect.Interface {
		if rvs.IsNil() {
			return nil
		}
		rvs = rvs.Elem()
	}
	var list []any
	switch rvs.Kind() {
	case reflect.Slice, reflect.Array:
		list = make([]any, 0, rvs.Len())
		for i := 0; i < rvs.Len(); i++ {
			list = append(list, rvs.Index(i).Interface())
		}
	case reflect.Map:
		list = make([]any, 0, rvs.Len())
		iter := rvs.MapRange()
		for iter.Next() {
			list = append(list, iter.Key().Interface())
		}
	default:
		return fmt.Errorf("velocity: #foreach 无法迭代 %T", items)
	}

	savedVar, hadVar := ctx.get(n.varName)
	savedForeach, hadForeach := ctx.get("foreach")
	savedCount, hadCount := ctx.get("velocityCount")
	defer func() {
		restore := func(key string, value any, had bool) {
			if had {
				ctx.Put(key, value)
			} else {
				ctx.remove(key)
			}
		}
		restore(n.varName, savedVar, hadVar)
		restore("foreach", savedForeach, hadForeach)
		restore("velocityCount", savedCount, hadCount)
	}()

	total := len(list)
	for index, item := range list {
		count := index + 1
		ctx.Put(n.varName, item)
		ctx.Put("velocityCount", int64(count))
		ctx.Put("foreach", &foreachStatus{
			Index:   index,
			Count:   count,
			HasNext: count < total,
			First:   count == 1,
			Last:    count == total,
		})
		if err := renderNodes(n.body, ctx, out); err != nil {
			if errors.Is(err, errBreakLoop) {
				return nil
			}
			return err
		}
	}
	return nil
}

type setNode struct {
	name string
	expr velocityExpr
}

func (n *setNode) render(ctx *velocityContext, out *strings.Builder) error {
	value := evalExpr(n.expr, ctx)
	if value == nil || isUndefined(value) {
		// Java: #set 右侧为 null 时不赋值（变量保持未定义）。
		ctx.remove(n.name)
		return nil
	}
	ctx.Put(n.name, value)
	return nil
}

type breakNode struct{}

func (n *breakNode) render(_ *velocityContext, _ *strings.Builder) error { return errBreakLoop }

func renderNodes(nodes []velocityNode, ctx *velocityContext, out *strings.Builder) error {
	for _, node := range nodes {
		if err := node.render(ctx, out); err != nil {
			return err
		}
	}
	return nil
}

// ---------------------------------------------------------------------------
// 词法辅助
// ---------------------------------------------------------------------------

var directiveOrder = []string{"foreach", "elseif", "break", "else", "stop", "end", "set", "if"}

var withArgsDirectives = map[string]bool{"if": true, "elseif": true, "foreach": true, "set": true}

var ifStops = map[string]bool{"end": true, "else": true, "elseif": true}
var endOnly = map[string]bool{"end": true}

var foreachPattern = regexp.MustCompile(`(?s)^\s*\$!?\{?([A-Za-z_][A-Za-z0-9_]*)\}?\s+in\s+(.+)$`)
var setLHSPattern = regexp.MustCompile(`^\s*\$!?\{?([A-Za-z_][A-Za-z0-9_]*)\}?\s*$`)

func isIdentifierChar(ch byte) bool {
	return ch == '_' || (ch >= 'a' && ch <= 'z') || (ch >= 'A' && ch <= 'Z') || (ch >= '0' && ch <= '9')
}

func skipStringLiteral(text string, index int) (int, error) {
	quote := text[index]
	index++
	for index < len(text) {
		ch := text[index]
		if ch == '\\' {
			index += 2
			continue
		}
		if ch == quote {
			return index + 1, nil
		}
		index++
	}
	return 0, errors.New("velocity: 字符串没有闭合引号")
}

func readBalanced(text string, openPos int) (string, int, error) {
	depth := 0
	index := openPos
	for index < len(text) {
		ch := text[index]
		if ch == '"' || ch == '\'' {
			after, err := skipStringLiteral(text, index)
			if err != nil {
				return "", 0, err
			}
			index = after
			continue
		}
		switch ch {
		case '(':
			depth++
		case ')':
			depth--
			if depth == 0 {
				return text[openPos+1 : index], index + 1, nil
			}
		}
		index++
	}
	return "", 0, fmt.Errorf("velocity: 括号没有闭合: %q", text[openPos:])
}

func findCloseBrace(text string, start int) int {
	index := start
	paren := 0
	for index < len(text) {
		ch := text[index]
		if ch == '"' || ch == '\'' {
			after, err := skipStringLiteral(text, index)
			if err != nil {
				return -1
			}
			index = after
			continue
		}
		switch ch {
		case '(':
			paren++
		case ')':
			paren--
		case '}':
			if paren == 0 {
				return index
			}
		}
		index++
	}
	return -1
}

type directive struct {
	name  string
	arg   string
	after int
}

// scanDirective 识别 pos 处的 # 指令；不是指令时第二个返回值为 false。
func scanDirective(text string, pos int) (directive, bool) {
	if pos >= len(text) || text[pos] != '#' {
		return directive{}, false
	}
	length := len(text)
	if strings.HasPrefix(text[pos:], "##") {
		newline := strings.IndexByte(text[pos:], '\n')
		if newline == -1 {
			return directive{name: "comment", after: length}, true
		}
		return directive{name: "comment", after: pos + newline + 1}, true
	}
	if strings.HasPrefix(text[pos:], "#[[") {
		end := strings.Index(text[pos+3:], "]]#")
		if end == -1 {
			return directive{}, false
		}
		return directive{name: "raw", arg: text[pos+3 : pos+3+end], after: pos + 3 + end + 3}, true
	}
	if strings.HasPrefix(text[pos:], "#*") {
		end := strings.Index(text[pos+2:], "*#")
		if end == -1 {
			return directive{}, false
		}
		return directive{name: "comment", after: pos + 2 + end + 2}, true
	}

	name := ""
	for _, candidate := range directiveOrder {
		if strings.HasPrefix(text[pos+1:], candidate) {
			name = candidate
			break
		}
	}
	if name == "" {
		return directive{}, false
	}
	index := pos + 1 + len(name)
	if withArgsDirectives[name] {
		cursor := index
		for cursor < length && (text[cursor] == ' ' || text[cursor] == '\t') {
			cursor++
		}
		if cursor >= length || text[cursor] != '(' {
			return directive{}, false
		}
		inner, after, err := readBalanced(text, cursor)
		if err != nil {
			return directive{}, false
		}
		return directive{name: name, arg: inner, after: after}, true
	}
	return directive{name: name, after: index}, true
}

func isDirectiveOnlyLine(line string) bool {
	text := strings.TrimRight(line, "\r\n")
	index := 0
	found := false
	for index < len(text) {
		ch := text[index]
		if ch == ' ' || ch == '\t' {
			index++
			continue
		}
		if ch != '#' {
			return false
		}
		scanned, ok := scanDirective(text, index)
		if !ok {
			return false
		}
		if scanned.name == "raw" {
			return false
		}
		index = scanned.after
		found = true
	}
	return found
}

func directivesOf(line string) string {
	text := strings.TrimRight(line, "\r\n")
	var b strings.Builder
	index := 0
	for index < len(text) {
		if text[index] == ' ' || text[index] == '\t' {
			index++
			continue
		}
		scanned, ok := scanDirective(text, index)
		if !ok {
			b.WriteString(text[index:])
			break
		}
		if scanned.name == "comment" {
			break
		}
		b.WriteString(text[index:scanned.after])
		index = scanned.after
	}
	return b.String()
}

// stripDirectiveOnlyLines 实现 Velocity space.gobbling=lines：
// 只由指令与空白组成的行只保留指令本身（丢掉缩进与换行）。
func stripDirectiveOnlyLines(source string) string {
	var b strings.Builder
	start := 0
	for i := 0; i < len(source); i++ {
		if source[i] == '\n' {
			line := source[start : i+1]
			if isDirectiveOnlyLine(line) {
				b.WriteString(directivesOf(line))
			} else {
				b.WriteString(line)
			}
			start = i + 1
		}
	}
	if start < len(source) {
		line := source[start:]
		if isDirectiveOnlyLine(line) {
			b.WriteString(directivesOf(line))
		} else {
			b.WriteString(line)
		}
	}
	return b.String()
}

// ---------------------------------------------------------------------------
// 引用解析
// ---------------------------------------------------------------------------

func parseArgs(text string, openPos, limit int) ([]velocityExpr, int, error) {
	inner, after, err := readBalanced(text[:limit], openPos)
	if err != nil {
		return nil, 0, err
	}
	if strings.TrimSpace(inner) == "" {
		return nil, after, nil
	}
	var args []velocityExpr
	for _, part := range splitTopLevel(inner, ',') {
		expr, err := parseVelocityExpression(part)
		if err != nil {
			return nil, 0, err
		}
		args = append(args, expr)
	}
	return args, after, nil
}

func splitTopLevel(text string, separator byte) []string {
	var parts []string
	depth := 0
	start := 0
	index := 0
	for index < len(text) {
		ch := text[index]
		if ch == '"' || ch == '\'' {
			after, err := skipStringLiteral(text, index)
			if err != nil {
				break
			}
			index = after
			continue
		}
		switch ch {
		case '(', '[', '{':
			depth++
		case ')', ']', '}':
			depth--
		default:
			if ch == separator && depth == 0 {
				parts = append(parts, text[start:index])
				start = index + 1
			}
		}
		index++
	}
	parts = append(parts, text[start:])
	return parts
}

func scanRefBody(text string, index, limit int) (string, []refStep, int, bool) {
	start := index
	for index < limit && isIdentifierChar(text[index]) {
		index++
	}
	if index == start {
		return "", nil, 0, false
	}
	root := text[start:index]
	var chain []refStep
	for index < limit && text[index] == '.' {
		cursor := index + 1
		for cursor < limit && isIdentifierChar(text[cursor]) {
			cursor++
		}
		if cursor == index+1 {
			break
		}
		name := text[index+1 : cursor]
		if cursor < limit && text[cursor] == '(' {
			args, after, err := parseArgs(text, cursor, limit)
			if err != nil {
				return "", nil, 0, false
			}
			chain = append(chain, refStep{name: name, args: args})
			index = after
			continue
		}
		chain = append(chain, refStep{property: true, name: name})
		index = cursor
	}
	return root, chain, index, true
}

func parseReference(text string, pos int) (*velocityRef, int, bool) {
	if pos >= len(text) || text[pos] != '$' {
		return nil, pos, false
	}
	index := pos + 1
	quiet := false
	if index < len(text) && text[index] == '!' {
		quiet = true
		index++
	}
	if index < len(text) && text[index] == '{' {
		closeAt := findCloseBrace(text, index+1)
		if closeAt == -1 {
			return nil, pos, false
		}
		root, chain, after, ok := scanRefBody(text, index+1, closeAt)
		if !ok || after != closeAt {
			return nil, pos, false
		}
		return &velocityRef{raw: text[pos : closeAt+1], root: root, chain: chain, quiet: quiet}, closeAt + 1, true
	}
	root, chain, after, ok := scanRefBody(text, index, len(text))
	if !ok {
		return nil, pos, false
	}
	return &velocityRef{raw: text[pos:after], root: root, chain: chain, quiet: quiet}, after, true
}

// ---------------------------------------------------------------------------
// 表达式
// ---------------------------------------------------------------------------

type velocityExpr any

type litExpr struct{ value any }

type strExpr struct {
	content     string
	interpolate bool
}

type refExpr struct{ ref *velocityRef }

type notExpr struct{ inner velocityExpr }

type binExpr struct {
	op          string
	left, right velocityExpr
}

type mapExpr struct{ entries [][2]velocityExpr }

func parseVelocityExpression(text string) (velocityExpr, error) {
	parser := &exprParser{text: text, length: len(text)}
	node, err := parser.parse()
	if err != nil {
		return nil, err
	}
	return node, nil
}

func evalExpr(expr velocityExpr, ctx *velocityContext) any {
	switch node := expr.(type) {
	case *litExpr:
		return node.value
	case *refExpr:
		return node.ref.evaluate(ctx)
	case *strExpr:
		if !node.interpolate {
			return node.content
		}
		return renderStringTemplate(node.content, ctx)
	case *notExpr:
		return !truthy(evalExpr(node.inner, ctx))
	case *mapExpr:
		result := map[string]any{}
		for _, entry := range node.entries {
			result[toJavaString(evalExpr(entry[0], ctx))] = evalExpr(entry[1], ctx)
		}
		return result
	case *binExpr:
		left := evalExpr(node.left, ctx)
		switch node.op {
		case "&&":
			return truthy(left) && truthy(evalExpr(node.right, ctx))
		case "||":
			return truthy(left) || truthy(evalExpr(node.right, ctx))
		}
		right := evalExpr(node.right, ctx)
		switch node.op {
		case "+":
			return javaAdd(left, right)
		case "==":
			return javaEquals(left, right)
		case "!=":
			return !javaEquals(left, right)
		default:
			return javaCompare(node.op, left, right)
		}
	}
	return undefined
}

func truthy(value any) bool {
	if value == nil || isUndefined(value) {
		return false
	}
	switch v := value.(type) {
	case bool:
		return v
	case string:
		return v != ""
	}
	rv := reflect.ValueOf(value)
	switch rv.Kind() {
	case reflect.Slice, reflect.Array, reflect.Map:
		return rv.Len() > 0
	case reflect.Pointer, reflect.Interface:
		return !rv.IsNil()
	}
	return true
}

func normalizeNull(value any) any {
	if isUndefined(value) {
		return nil
	}
	return value
}

func javaEquals(left, right any) bool {
	left = normalizeNull(left)
	right = normalizeNull(right)
	if left == nil || right == nil {
		return left == nil && right == nil
	}
	if l, ok := intValue(left); ok {
		if r, ok := intValue(right); ok {
			return l == r
		}
	}
	if lf, ok := left.(float64); ok {
		if rf, ok := right.(float64); ok {
			return lf == rf
		}
	}
	if ls, ok := left.(string); ok {
		if rs, ok := right.(string); ok {
			return ls == rs
		}
		return false
	}
	if lb, ok := left.(bool); ok {
		if rb, ok := right.(bool); ok {
			return lb == rb
		}
		return false
	}
	return toJavaString(left) == toJavaString(right)
}

func javaCompare(operator string, left, right any) any {
	left = normalizeNull(left)
	right = normalizeNull(right)
	if left == nil || right == nil {
		return undefined
	}
	var result int
	if l, ok := intValue(left); ok {
		if r, ok := intValue(right); ok {
			switch {
			case l < r:
				result = -1
			case l > r:
				result = 1
			}
		}
	} else if lf, ok := left.(float64); ok {
		if rf, ok := right.(float64); ok {
			switch {
			case lf < rf:
				result = -1
			case lf > rf:
				result = 1
			}
		}
	} else {
		result = strings.Compare(toJavaString(left), toJavaString(right))
	}
	switch operator {
	case ">":
		return result > 0
	case ">=":
		return result >= 0
	case "<":
		return result < 0
	default:
		return result <= 0
	}
}

func javaAdd(left, right any) any {
	left = normalizeNull(left)
	right = normalizeNull(right)
	if l, ok := intValue(left); ok {
		if r, ok := intValue(right); ok {
			return l + r
		}
	}
	if _, ok := left.(float64); ok {
		if _, ok := right.(float64); ok {
			lf, _ := left.(float64)
			rf, _ := right.(float64)
			return lf + rf
		}
	}
	return toJavaString(left) + toJavaString(right)
}

type exprParser struct {
	text   string
	pos    int
	length int
}

func (p *exprParser) parse() (velocityExpr, error) {
	node, err := p.parseOr()
	if err != nil {
		return nil, err
	}
	p.skipSpace()
	if p.pos != p.length {
		return nil, fmt.Errorf("velocity: 表达式无法解析: %q（位置 %d）", p.text, p.pos)
	}
	return node, nil
}

func (p *exprParser) skipSpace() {
	for p.pos < p.length {
		switch p.text[p.pos] {
		case ' ', '\t', '\r', '\n':
			p.pos++
		default:
			return
		}
	}
}

func (p *exprParser) accept(token string) bool {
	p.skipSpace()
	if strings.HasPrefix(p.text[p.pos:], token) {
		p.pos += len(token)
		return true
	}
	return false
}

func (p *exprParser) parseOr() (velocityExpr, error) {
	node, err := p.parseAnd()
	if err != nil {
		return nil, err
	}
	for p.accept("||") {
		right, err := p.parseAnd()
		if err != nil {
			return nil, err
		}
		node = &binExpr{op: "||", left: node, right: right}
	}
	return node, nil
}

func (p *exprParser) parseAnd() (velocityExpr, error) {
	node, err := p.parseEquality()
	if err != nil {
		return nil, err
	}
	for p.accept("&&") {
		right, err := p.parseEquality()
		if err != nil {
			return nil, err
		}
		node = &binExpr{op: "&&", left: node, right: right}
	}
	return node, nil
}

func (p *exprParser) parseEquality() (velocityExpr, error) {
	node, err := p.parseRelational()
	if err != nil {
		return nil, err
	}
	for {
		if p.accept("==") {
			right, err := p.parseRelational()
			if err != nil {
				return nil, err
			}
			node = &binExpr{op: "==", left: node, right: right}
			continue
		}
		if p.accept("!=") {
			right, err := p.parseRelational()
			if err != nil {
				return nil, err
			}
			node = &binExpr{op: "!=", left: node, right: right}
			continue
		}
		return node, nil
	}
}

func (p *exprParser) parseRelational() (velocityExpr, error) {
	node, err := p.parseAdditive()
	if err != nil {
		return nil, err
	}
	for {
		matched := ""
		for _, operator := range []string{">=", "<=", ">", "<"} {
			if p.accept(operator) {
				matched = operator
				break
			}
		}
		if matched == "" {
			return node, nil
		}
		right, err := p.parseAdditive()
		if err != nil {
			return nil, err
		}
		node = &binExpr{op: matched, left: node, right: right}
	}
}

func (p *exprParser) parseAdditive() (velocityExpr, error) {
	node, err := p.parseUnary()
	if err != nil {
		return nil, err
	}
	for p.accept("+") {
		right, err := p.parseUnary()
		if err != nil {
			return nil, err
		}
		node = &binExpr{op: "+", left: node, right: right}
	}
	return node, nil
}

func (p *exprParser) parseUnary() (velocityExpr, error) {
	p.skipSpace()
	if p.pos < p.length && p.text[p.pos] == '!' {
		p.pos++
		inner, err := p.parseUnary()
		if err != nil {
			return nil, err
		}
		return &notExpr{inner: inner}, nil
	}
	return p.parsePrimary()
}

func (p *exprParser) parsePrimary() (velocityExpr, error) {
	p.skipSpace()
	if p.pos >= p.length {
		return nil, fmt.Errorf("velocity: 表达式不完整: %q", p.text)
	}
	ch := p.text[p.pos]
	switch {
	case ch == '(':
		p.pos++
		node, err := p.parseOr()
		if err != nil {
			return nil, err
		}
		p.skipSpace()
		if p.pos >= p.length || p.text[p.pos] != ')' {
			return nil, fmt.Errorf("velocity: 表达式括号不匹配: %q", p.text)
		}
		p.pos++
		return node, nil
	case ch == '"' || ch == '\'':
		content, after, err := readStringLiteral(p.text, p.pos)
		if err != nil {
			return nil, err
		}
		p.pos = after
		return &strExpr{content: content, interpolate: ch == '"'}, nil
	case ch == '$':
		ref, after, ok := parseReference(p.text, p.pos)
		if !ok {
			return nil, fmt.Errorf("velocity: 引用无法解析: %q", p.text)
		}
		p.pos = after
		return &refExpr{ref: ref}, nil
	case ch >= '0' && ch <= '9', ch == '-' && p.pos+1 < p.length && p.text[p.pos+1] >= '0' && p.text[p.pos+1] <= '9':
		return p.parseNumber()
	case ch == '{':
		return p.parseMapLiteral()
	case (ch >= 'a' && ch <= 'z') || (ch >= 'A' && ch <= 'Z') || ch == '_':
		start := p.pos
		for p.pos < p.length && isIdentifierChar(p.text[p.pos]) {
			p.pos++
		}
		return &strExpr{content: p.text[start:p.pos]}, nil
	}
	return nil, fmt.Errorf("velocity: 表达式无法解析: %q（位置 %d）", p.text, p.pos)
}

func (p *exprParser) parseMapLiteral() (velocityExpr, error) {
	p.pos++
	var entries [][2]velocityExpr
	for {
		p.skipSpace()
		if p.pos >= p.length {
			return nil, fmt.Errorf("velocity: map 字面量没有闭合: %q", p.text)
		}
		if p.text[p.pos] == '}' {
			p.pos++
			break
		}
		key, err := p.parseOr()
		if err != nil {
			return nil, err
		}
		p.skipSpace()
		if p.pos >= p.length || p.text[p.pos] != ':' {
			return nil, fmt.Errorf("velocity: map 字面量缺少冒号: %q", p.text)
		}
		p.pos++
		value, err := p.parseOr()
		if err != nil {
			return nil, err
		}
		entries = append(entries, [2]velocityExpr{key, value})
		p.skipSpace()
		if p.pos < p.length && p.text[p.pos] == ',' {
			p.pos++
			continue
		}
		if p.pos < p.length && p.text[p.pos] == '}' {
			p.pos++
			break
		}
		return nil, fmt.Errorf("velocity: map 字面量无法解析: %q", p.text)
	}
	return &mapExpr{entries: entries}, nil
}

func (p *exprParser) parseNumber() (velocityExpr, error) {
	start := p.pos
	if p.text[p.pos] == '-' {
		p.pos++
	}
	seenDot := false
	for p.pos < p.length {
		ch := p.text[p.pos]
		if ch >= '0' && ch <= '9' {
			p.pos++
			continue
		}
		if ch == '.' && !seenDot {
			seenDot = true
			p.pos++
			continue
		}
		break
	}
	raw := p.text[start:p.pos]
	if seenDot {
		value, err := strconv.ParseFloat(raw, 64)
		if err != nil {
			return nil, fmt.Errorf("velocity: 数字无法解析: %q", raw)
		}
		return &litExpr{value: value}, nil
	}
	value, err := strconv.ParseInt(raw, 10, 64)
	if err != nil {
		return nil, fmt.Errorf("velocity: 数字无法解析: %q", raw)
	}
	return &litExpr{value: value}, nil
}

func readStringLiteral(text string, pos int) (string, int, error) {
	quote := text[pos]
	index := pos + 1
	var b strings.Builder
	for index < len(text) {
		ch := text[index]
		if ch == '\\' && index+1 < len(text) {
			switch text[index+1] {
			case 'n':
				b.WriteByte('\n')
			case 't':
				b.WriteByte('\t')
			case 'r':
				b.WriteByte('\r')
			default:
				b.WriteByte(text[index+1])
			}
			index += 2
			continue
		}
		if ch == quote {
			return b.String(), index + 1, nil
		}
		b.WriteByte(ch)
		index++
	}
	return "", 0, fmt.Errorf("velocity: 字符串没有闭合引号: %q", text[pos:])
}

// ---------------------------------------------------------------------------
// 属性 / 方法调用
// ---------------------------------------------------------------------------

type velocityPropertyProvider interface {
	VelocityProperty(name string) (any, bool)
}

type velocityCallProvider interface {
	VelocityCall(name string, args []any) (any, bool)
}

func getProperty(target any, name string) any {
	if target == nil || isUndefined(target) {
		return undefined
	}
	if provider, ok := target.(velocityPropertyProvider); ok {
		if value, found := provider.VelocityProperty(name); found {
			return value
		}
	}
	if m, ok := target.(map[string]any); ok {
		if value, found := m[name]; found {
			return value
		}
		return undefined
	}
	rv := reflect.ValueOf(target)
	for rv.Kind() == reflect.Pointer || rv.Kind() == reflect.Interface {
		if rv.IsNil() {
			return undefined
		}
		rv = rv.Elem()
	}
	if rv.Kind() == reflect.Struct {
		rt := rv.Type()
		for i := 0; i < rt.NumField(); i++ {
			field := rt.Field(i)
			if field.PkgPath != "" {
				continue
			}
			if strings.EqualFold(field.Name, name) {
				return unwrapValue(rv.Field(i))
			}
		}
	}
	return undefined
}

func unwrapValue(value reflect.Value) any {
	if !value.IsValid() {
		return undefined
	}
	switch value.Kind() {
	case reflect.Pointer, reflect.Interface:
		if value.IsNil() {
			return undefined
		}
		return unwrapValue(value.Elem())
	}
	if value.CanInterface() {
		return value.Interface()
	}
	return undefined
}

func callMethod(target any, name string, args []any) any {
	if target == nil || isUndefined(target) {
		return undefined
	}
	if provider, ok := target.(velocityCallProvider); ok {
		if value, found := provider.VelocityCall(name, args); found {
			return value
		}
	}
	if text, ok := target.(string); ok {
		return callStringMethod(text, name, args)
	}
	rv := reflect.ValueOf(target)
	switch rv.Kind() {
	case reflect.Slice, reflect.Array:
		switch name {
		case "size":
			return int64(rv.Len())
		case "isEmpty":
			return rv.Len() == 0
		case "get":
			if len(args) == 1 {
				if index, ok := intValue(args[0]); ok && index >= 0 && int(index) < rv.Len() {
					return rv.Index(int(index)).Interface()
				}
			}
			return undefined
		case "contains":
			if len(args) == 1 {
				for i := 0; i < rv.Len(); i++ {
					if javaEquals(rv.Index(i).Interface(), args[0]) {
						return true
					}
				}
				return false
			}
		case "toString":
			return toJavaString(target)
		}
	case reflect.Map:
		switch name {
		case "size":
			return int64(rv.Len())
		case "isEmpty":
			return rv.Len() == 0
		case "get":
			if len(args) == 1 && rv.Type().Key().Kind() == reflect.String {
				key := reflect.ValueOf(toJavaString(args[0]))
				value := rv.MapIndex(key)
				if value.IsValid() {
					return value.Interface()
				}
			}
			return undefined
		case "contains":
			if len(args) == 1 && rv.Type().Key().Kind() == reflect.String {
				return rv.MapIndex(reflect.ValueOf(toJavaString(args[0]))).IsValid()
			}
		case "toString":
			return toJavaString(target)
		}
	}
	return undefined
}

func callStringMethod(text, name string, args []any) any {
	switch name {
	case "substring":
		runes := []rune(text)
		if len(args) < 1 {
			return undefined
		}
		start, ok := intValue(args[0])
		if !ok {
			return undefined
		}
		end := int64(len(runes))
		if len(args) >= 2 {
			if value, ok := intValue(args[1]); ok {
				end = value
			}
		}
		if start < 0 || end > int64(len(runes)) || start > end {
			return undefined
		}
		return string(runes[start:end])
	case "indexOf":
		if len(args) < 1 {
			return undefined
		}
		needle := toJavaString(args[0])
		runes := []rune(text)
		from := int64(0)
		if len(args) >= 2 {
			if value, ok := intValue(args[1]); ok {
				from = value
			}
		}
		if from < 0 {
			from = 0
		}
		if from > int64(len(runes)) {
			return int64(-1)
		}
		idx := strings.Index(string(runes[from:]), needle)
		if idx == -1 {
			return int64(-1)
		}
		return from + int64(len([]rune(string(runes[from:])[:idx])))
	case "length":
		return int64(len([]rune(text)))
	case "trim":
		return javaTrim(text)
	case "toUpperCase":
		return strings.ToUpper(text)
	case "toLowerCase":
		return strings.ToLower(text)
	case "matches":
		if len(args) < 1 {
			return undefined
		}
		pattern := toJavaString(args[0])
		re, err := regexp.Compile("^(?:" + pattern + ")$")
		if err != nil {
			return false
		}
		return re.MatchString(text)
	case "equals":
		if len(args) < 1 {
			return false
		}
		return javaEquals(text, args[0])
	case "equalsIgnoreCase":
		if len(args) < 1 {
			return false
		}
		return strings.EqualFold(text, toJavaString(args[0]))
	case "isEmpty":
		return text == ""
	case "contains":
		if len(args) < 1 {
			return false
		}
		return strings.Contains(text, toJavaString(args[0]))
	case "toString":
		return text
	}
	return undefined
}

// ---------------------------------------------------------------------------
// 模板
// ---------------------------------------------------------------------------

type velocityTemplate struct {
	name  string
	nodes []velocityNode
}

func newVelocityTemplate(name, source string) (*velocityTemplate, error) {
	stripped := stripDirectiveOnlyLines(source)
	parser := &templateParser{source: stripped, length: len(stripped)}
	nodes, terminator, _, err := parser.parseBlock(map[string]bool{})
	if err != nil {
		return nil, err
	}
	if terminator != "" {
		return nil, fmt.Errorf("velocity: 多余的 #%s", terminator)
	}
	return &velocityTemplate{name: name, nodes: nodes}, nil
}

func (t *velocityTemplate) merge(ctx *velocityContext) (string, error) {
	var out strings.Builder
	if err := renderNodes(t.nodes, ctx, &out); err != nil && !errors.Is(err, errBreakLoop) {
		return "", err
	}
	return out.String(), nil
}

// renderStringTemplate 渲染双引号字符串字面量内部的插值。
func renderStringTemplate(content string, ctx *velocityContext) any {
	parser := &templateParser{source: content, length: len(content)}
	nodes, _, _, err := parser.parseBlock(map[string]bool{})
	if err != nil {
		return undefined
	}
	var out strings.Builder
	if err := renderNodes(nodes, ctx, &out); err != nil {
		return undefined
	}
	return out.String()
}

// velocityEngine 对应 Velocity.getTemplate(name, encoding) + resource loader 缓存。
type velocityEngine struct {
	root  string
	mu    sync.RWMutex
	cache map[string]*velocityTemplate
}

func newVelocityEngine(root string) *velocityEngine {
	return &velocityEngine{root: root, cache: map[string]*velocityTemplate{}}
}

func (e *velocityEngine) getTemplate(name string) (*velocityTemplate, error) {
	e.mu.RLock()
	cached, ok := e.cache[name]
	e.mu.RUnlock()
	if ok {
		return cached, nil
	}
	path := filepath.Join(e.root, filepath.FromSlash(name))
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("velocity: 模板不存在: %s", name)
	}
	template, err := newVelocityTemplate(name, string(data))
	if err != nil {
		return nil, err
	}
	e.mu.Lock()
	e.cache[name] = template
	e.mu.Unlock()
	return template, nil
}

// ---------------------------------------------------------------------------
// 解析器
// ---------------------------------------------------------------------------

type templateParser struct {
	source string
	pos    int
	length int
}

func (p *templateParser) parseBlock(stops map[string]bool) ([]velocityNode, string, string, error) {
	nodes := make([]velocityNode, 0, 16)
	for p.pos < p.length {
		ch := p.source[p.pos]
		if ch == '#' {
			scanned, ok := scanDirective(p.source, p.pos)
			if !ok {
				nodes = append(nodes, &textNode{text: "#"})
				p.pos++
				continue
			}
			if scanned.name == "comment" {
				p.pos = scanned.after
				continue
			}
			if scanned.name == "raw" {
				nodes = append(nodes, &textNode{text: scanned.arg})
				p.pos = scanned.after
				continue
			}
			if stops[scanned.name] {
				p.pos = scanned.after
				return nodes, scanned.name, scanned.arg, nil
			}
			var err error
			switch scanned.name {
			case "if":
				var node velocityNode
				node, err = p.parseIf(scanned.arg, scanned.after)
				if err == nil {
					nodes = append(nodes, node)
				}
			case "foreach":
				var node velocityNode
				node, err = p.parseForeach(scanned.arg, scanned.after)
				if err == nil {
					nodes = append(nodes, node)
				}
			case "set":
				var node velocityNode
				node, err = p.parseSet(scanned.arg, scanned.after)
				if err == nil {
					nodes = append(nodes, node)
				}
			case "break":
				nodes = append(nodes, &breakNode{})
				p.pos = scanned.after
			case "stop":
				p.pos = p.length
			default:
				// 游离的 #end / #else —— 原样吐出。
				nodes = append(nodes, &textNode{text: p.source[p.pos:scanned.after]})
				p.pos = scanned.after
			}
			if err != nil {
				return nil, "", "", err
			}
			continue
		}
		if ch == '$' {
			ref, after, ok := parseReference(p.source, p.pos)
			if !ok {
				nodes = append(nodes, &textNode{text: "$"})
				p.pos++
			} else {
				nodes = append(nodes, ref)
				p.pos = after
			}
			continue
		}
		end := strings.IndexAny(p.source[p.pos:], "#$")
		if end == -1 {
			end = p.length
		} else {
			end += p.pos
		}
		nodes = append(nodes, &textNode{text: p.source[p.pos:end]})
		p.pos = end
	}
	return nodes, "", "", nil
}

func (p *templateParser) parseIf(arg string, after int) (velocityNode, error) {
	p.pos = after
	condition, err := parseVelocityExpression(arg)
	if err != nil {
		return nil, err
	}
	body, terminator, terminatorArg, err := p.parseBlock(ifStops)
	if err != nil {
		return nil, err
	}
	branches := []ifBranch{{condition: condition, nodes: body}}
	for terminator == "elseif" {
		condition, err = parseVelocityExpression(terminatorArg)
		if err != nil {
			return nil, err
		}
		body, terminator, terminatorArg, err = p.parseBlock(ifStops)
		if err != nil {
			return nil, err
		}
		branches = append(branches, ifBranch{condition: condition, nodes: body})
	}
	var elseNodes []velocityNode
	if terminator == "else" {
		elseNodes, terminator, _, err = p.parseBlock(endOnly)
		if err != nil {
			return nil, err
		}
	}
	if terminator != "end" {
		return nil, errors.New("velocity: #if 缺少对应的 #end")
	}
	return &ifNode{branches: branches, elseNodes: elseNodes}, nil
}

func (p *templateParser) parseForeach(arg string, after int) (velocityNode, error) {
	p.pos = after
	match := foreachPattern.FindStringSubmatch(arg)
	if match == nil {
		return nil, fmt.Errorf("velocity: #foreach 语法错误: %q", arg)
	}
	iterable, err := parseVelocityExpression(match[2])
	if err != nil {
		return nil, err
	}
	body, terminator, _, err := p.parseBlock(endOnly)
	if err != nil {
		return nil, err
	}
	if terminator != "end" {
		return nil, errors.New("velocity: #foreach 缺少对应的 #end")
	}
	return &foreachNode{varName: match[1], iterable: iterable, body: body}, nil
}

func (p *templateParser) parseSet(arg string, after int) (velocityNode, error) {
	p.pos = after
	splitAt := findAssignment(arg)
	if splitAt == -1 {
		return nil, fmt.Errorf("velocity: #set 语法错误: %q", arg)
	}
	left := arg[:splitAt]
	right := arg[splitAt+1:]
	match := setLHSPattern.FindStringSubmatch(left)
	if match == nil {
		return nil, fmt.Errorf("velocity: #set 左侧必须是简单变量: %q", left)
	}
	expr, err := parseVelocityExpression(right)
	if err != nil {
		return nil, err
	}
	return &setNode{name: match[1], expr: expr}, nil
}

func findAssignment(arg string) int {
	depth := 0
	index := 0
	for index < len(arg) {
		ch := arg[index]
		if ch == '"' || ch == '\'' {
			after, err := skipStringLiteral(arg, index)
			if err != nil {
				return -1
			}
			index = after
			continue
		}
		switch ch {
		case '(', '[', '{':
			depth++
		case ')', ']', '}':
			depth--
		case '=':
			if depth == 0 {
				previous := byte(0)
				if index > 0 {
					previous = arg[index-1]
				}
				following := byte(0)
				if index+1 < len(arg) {
					following = arg[index+1]
				}
				if !strings.ContainsRune("=!<>", rune(previous)) && following != '=' {
					return index
				}
			}
		}
		index++
	}
	return -1
}
