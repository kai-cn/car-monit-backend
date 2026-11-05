// 来源: org.apache.velocity:velocity-engine-core:2.3（RuoYi VelocityInitializer + VelocityUtils 的用法）
// 职责: 代码生成模板（config/../templates/vm*）渲染所需的 Velocity 子集。
// 支持: 文本、##、#*..*#、#[[..]]#、#set、#if/#elseif/#else/#end、
//       #foreach(...in...) 与 #break/#continue、$foreach.count/index/first/last、
//       $ref/$!ref/${ref}、属性与方法链、字符串/数字/布尔字面量、
//       ==、!=、<、<=、>、>=、&&、||、!、+（字符串拼接或数值相加）。
//
// 与 Java 一致的三条关键语义：
// 1. 未解析或取值为 null 的非静默引用**原样输出**（`$foo.bar`），`$!foo` 才输出空串；
// 2. `#if` 的真值：null/Boolean(false) 为假，其余（含空串、0、空集合）为真；
// 3. `lines` 空格吞噬：独占一行的指令不产生任何输出（含其换行）。

use serde_json::{Map, Value};
use std::fmt;

pub type VelResult<T> = Result<T, String>;

#[derive(Clone, Debug)]
pub enum Value_ {
    Val(Value),
    Unresolved,
}

#[derive(Clone, Debug)]
pub enum Seg {
    Prop(String),
    Method(String, Vec<Expr>),
}

#[derive(Clone, Copy, Debug, PartialEq)]
pub enum CmpOp {
    Eq,
    Ne,
    Lt,
    Le,
    Gt,
    Ge,
}

#[derive(Clone, Debug)]
pub enum Expr {
    Lit(Value),
    Ref(Vec<Seg>),
    /// 字符串插值里的引用：解析不到时输出模板里写的那段原文。
    RefText(Vec<Seg>, String),
    Not(Box<Expr>),
    Neg(Box<Expr>),
    Add(Vec<Expr>),
    Cmp(Box<Expr>, CmpOp, Box<Expr>),
    And(Box<Expr>, Box<Expr>),
    Or(Box<Expr>, Box<Expr>),
}

#[derive(Debug)]
pub enum Node {
    Text(String),
    Out {
        expr: Expr,
        src: String,
        quiet: bool,
    },
    Set {
        name: String,
        expr: Expr,
    },
    If {
        branches: Vec<(Expr, Vec<Node>)>,
        els: Vec<Node>,
    },
    Foreach {
        var: String,
        list: Box<Expr>,
        body: Vec<Node>,
    },
    Break,
    Continue,
    Verbatim(String),
}

#[derive(Default, Debug)]
pub struct Ctx {
    scopes: Vec<Map<String, Value>>,
}

impl Ctx {
    pub fn new() -> Self {
        Self {
            scopes: vec![Map::new()],
        }
    }

    pub fn with_root(map: Map<String, Value>) -> Self {
        Self { scopes: vec![map] }
    }

    pub fn push(&mut self) {
        self.scopes.push(Map::new());
    }

    pub fn pop(&mut self) {
        self.scopes.pop();
    }

    pub fn set(&mut self, key: &str, value: Value) {
        if let Some(top) = self.scopes.last_mut() {
            top.insert(key.to_string(), value);
        }
    }

    pub fn get(&self, key: &str) -> Option<&Value> {
        for scope in self.scopes.iter().rev() {
            if let Some(value) = scope.get(key) {
                return Some(value);
            }
        }
        None
    }
}

struct Flow {
    break_now: bool,
    /// Java: Velocity 保留模板的原始行尾（本项目模板全为 CRLF），
    /// 解析时先归一成 LF，输出文本节点时再还原成 CRLF。
    crlf: bool,
}

impl Flow {
    fn with_crlf(crlf: bool) -> Self {
        Self {
            break_now: false,
            crlf,
        }
    }

    fn push_text(&self, out: &mut String, text: &str) {
        if !self.crlf {
            out.push_str(text);
            return;
        }
        let lf = char::from_u32(10).unwrap_or('x');
        let cr = char::from_u32(13).unwrap_or('x');
        let mut rest = text;
        while let Some(index) = rest.find(lf) {
            out.push_str(&rest[..index]);
            out.push(cr);
            out.push(lf);
            rest = &rest[index + 1..];
        }
        out.push_str(rest);
    }
}

pub fn render(template: &str, ctx: &mut Ctx) -> VelResult<String> {
    // 解析前把 CRLF/CR 归一成 LF（行内逻辑只认 '\n'），行尾由 Flow::push_text 还原。
    // 用码位常量写，避免转义在脚本链路里被改写。
    let cr = char::from_u32(13).unwrap_or('x');
    let lf = char::from_u32(10).unwrap_or('x');
    let lf_text: String = lf.to_string();
    let crlf_text: String = cr.to_string() + &lf_text;
    let crlf = template.contains(&crlf_text);
    let normalized = if template.contains(cr) {
        std::borrow::Cow::Owned(template.replace(&crlf_text, &lf_text).replace(cr, &lf_text))
    } else {
        std::borrow::Cow::Borrowed(template)
    };
    let (nodes, _) = Parser::new(normalized.as_ref()).parse_nodes(&[], false)?;
    let mut out = String::new();
    let mut flow = Flow::with_crlf(crlf);
    render_nodes(&nodes, ctx, &mut out, &mut flow)?;
    Ok(out)
}

const DIRECTIVES: &[&str] = &[
    "if", "elseif", "else", "end", "set", "foreach", "break", "continue", "stop", "include",
    "parse", "macro",
];

pub struct Parser {
    chars: Vec<char>,
    pos: usize,
    /// 当前物理行内是否已经出现过非空白内容（文本或引用）。
    /// 只有「整行除空白外只有指令」时才允许吞掉指令行的换行，
    /// 而引用节点会提前 flush 掉 text，所以必须单独记这个状态。
    line_has_content: bool,
}

impl Parser {
    pub fn new(text: &str) -> Self {
        Self {
            chars: text.chars().collect(),
            pos: 0,
            line_has_content: false,
        }
    }

    fn cur(&self) -> Option<char> {
        self.chars.get(self.pos).copied()
    }

    fn at(&self, offset: usize) -> Option<char> {
        self.chars.get(self.pos + offset).copied()
    }

    fn eat(&mut self, count: usize) {
        self.pos = (self.pos + count).min(self.chars.len());
    }

    fn word(&self) -> String {
        let mut out = String::new();
        let mut index = self.pos;
        while let Some(ch) = self.chars.get(index).copied() {
            if ch.is_ascii_alphanumeric() || ch == '_' {
                out.push(ch);
                index += 1;
            } else {
                break;
            }
        }
        out
    }

    fn skip_spaces(&mut self) {
        while matches!(self.cur(), Some(ch) if ch == ' ' || ch == '\t') {
            self.eat(1);
        }
    }

    /// 指令行的空白吞噬（Velocity 2.x 默认 space.gobbling = "lines"）：
    /// 独占一行的指令，消失的是**它自己那一行**的行尾换行（连同指令前的缩进），
    /// 上一行的换行属于正文，必须保留。
    fn gobble_line_before(text: &mut String) {
        let tail_start = match text.rfind('\n') {
            Some(index) => index + 1,
            None => 0,
        };
        if text[tail_start..]
            .chars()
            .all(|ch| ch == ' ' || ch == '\t' || ch == '\r')
        {
            text.truncate(tail_start);
        }
    }

    /// 吞掉指令自身行剩余的空格与那个换行。
    fn gobble_eol(&mut self) {
        self.gobble_line_after("");
    }

    /// 指令头之后的空白：同行后面还有内容时也要跳过那些空格（Java 解析器在指令态里
    /// 会跳过词间空白），若该行此后只剩空白则连换行一起吞掉。
    fn gobble_after_header(&mut self) {
        let mut index = self.pos;
        while matches!(self.chars.get(index).copied(), Some(' ') | Some('\t')) {
            index += 1;
        }
        match self.chars.get(index).copied() {
            Some('\r') if self.chars.get(index + 1) == Some(&'\n') => {
                self.pos = index + 2;
                self.line_has_content = false;
            }
            Some('\n') => {
                self.pos = index + 1;
                self.line_has_content = false;
            }
            _ => self.pos = index,
        }
    }

    fn gobble_line_after(&mut self, text: &str) {
        if !text
            .chars()
            .all(|ch| ch == ' ' || ch == '\t' || ch == '\n' || ch == '\r')
        {
            return;
        }
        let mut index = self.pos;
        while matches!(self.chars.get(index).copied(), Some(' ') | Some('\t')) {
            index += 1;
        }
        match self.chars.get(index).copied() {
            Some('\r') if self.chars.get(index + 1) == Some(&'\n') => {
                self.pos = index + 2;
                self.line_has_content = false;
            }
            Some('\n') => {
                self.pos = index + 1;
                self.line_has_content = false;
            }
            _ => {}
        }
    }

    /// `for_foreach` 标记本段是否是 #foreach 的正文：Velocity 里 #foreach 的收尾 `#end`
    /// 会吃掉同行剩余空白与换行，而 #if 的 `#end` 不会（mapper.xml.vm 的列清单靠这个换行分行）。
    fn parse_nodes(
        &mut self,
        terminators: &[&str],
        for_foreach: bool,
    ) -> VelResult<(Vec<Node>, String)> {
        let mut nodes: Vec<Node> = Vec::new();
        let mut text = String::new();
        while let Some(ch) = self.cur() {
            if ch == '#' {
                if self.starts_comment() {
                    Self::gobble_line_before(&mut text);
                    self.skip_comment();
                    self.gobble_line_after(&text.clone());
                    continue;
                }
                if self.starts_verbatim() {
                    Self::gobble_line_before(&mut text);
                    let body = self.take_verbatim();
                    nodes.push(Node::Verbatim(body));
                    self.gobble_line_after(&text.clone());
                    continue;
                }
                if let Some(name) = self.directive_name() {
                    // 只有「整行除空白外只有这个指令」时才吞掉它所在行的换行；
                    // 与正文同行的指令（如 `t.$x#if($y),#end`）不能吞。
                    let alone = !self.line_has_content;
                    if terminators.contains(&name.as_str()) {
                        if alone {
                            Self::gobble_line_before(&mut text);
                        }
                        if !text.is_empty() {
                            nodes.push(Node::Text(std::mem::take(&mut text)));
                        }
                        self.eat(1 + name.len());
                        if alone || (for_foreach && name.as_str() == "end") {
                            self.gobble_line_after("");
                        }
                        return Ok((nodes, name));
                    }
                    if DIRECTIVES.contains(&name.as_str()) {
                        if alone {
                            Self::gobble_line_before(&mut text);
                        }
                        if !text.is_empty() {
                            nodes.push(Node::Text(std::mem::take(&mut text)));
                        }
                        // 指令本身就算这一行的内容：正文里同一行的后续指令不再算「独占一行」。
                        self.line_has_content = true;
                        let node = self.parse_directive(&name, alone)?;
                        // if/foreach 的行尾换行已由其 #end 分支吞掉，这里再吞一次会吃掉后续空行。
                        if alone && !matches!(name.as_str(), "if" | "foreach") {
                            self.gobble_line_after("");
                        }
                        if let Some(node) = node {
                            nodes.push(node);
                        }
                        continue;
                    }
                }
                if let Some(node) = self.try_formal_reference()? {
                    if !text.is_empty() {
                        nodes.push(Node::Text(std::mem::take(&mut text)));
                    }
                    nodes.push(node);
                    continue;
                }
                text.push('#');
                self.eat(1);
                continue;
            }
            if ch == '$' {
                if let Some(node) = self.try_reference()? {
                    if !text.is_empty() {
                        nodes.push(Node::Text(std::mem::take(&mut text)));
                    }
                    nodes.push(node);
                    self.line_has_content = true;
                    continue;
                }
            }
            if ch == '\n' {
                self.line_has_content = false;
            } else if ch != ' ' && ch != '\t' && ch != '\r' {
                self.line_has_content = true;
            }
            text.push(ch);
            self.eat(1);
        }
        if !text.is_empty() {
            nodes.push(Node::Text(text));
        }
        Ok((nodes, String::new()))
    }

    fn starts_comment(&self) -> bool {
        self.at(1) == Some('#') || (self.at(1) == Some('*'))
    }

    fn starts_verbatim(&self) -> bool {
        self.at(1) == Some('[') && self.at(2) == Some('[')
    }

    fn skip_comment(&mut self) {
        if self.at(1) == Some('#') {
            while let Some(ch) = self.cur() {
                self.eat(1);
                if ch == '\n' {
                    break;
                }
            }
            return;
        }
        // #* ... *#
        while let Some(ch) = self.cur() {
            if ch == '*' && self.at(1) == Some('#') {
                self.eat(2);
                return;
            }
            self.eat(1);
        }
    }

    fn take_verbatim(&mut self) -> String {
        self.eat(3); // #[[
        let mut out = String::new();
        while let Some(ch) = self.cur() {
            if ch == ']' && self.at(1) == Some(']') && self.at(2) == Some('#') {
                self.eat(3);
                return out;
            }
            out.push(ch);
            self.eat(1);
        }
        out
    }

    fn directive_name(&self) -> Option<String> {
        let mut index = self.pos + 1;
        if self.chars.get(index) == Some(&'!') {
            index += 1;
        }
        let mut name = String::new();
        while let Some(ch) = self.chars.get(index).copied() {
            if ch.is_ascii_alphabetic() || ch == '_' {
                name.push(ch);
                index += 1;
            } else {
                break;
            }
        }
        if name.is_empty() {
            None
        } else {
            Some(name)
        }
    }

    fn parse_directive(&mut self, name: &str, alone: bool) -> VelResult<Option<Node>> {
        self.eat(1 + name.len());
        match name {
            "break" => Ok(Some(Node::Break)),
            "continue" => Ok(Some(Node::Continue)),
            "stop" => Ok(Some(Node::Break)),
            "set" => {
                self.expect_char('(')?;
                self.skip_spaces();
                if self.cur() != Some('$') {
                    return Err("#set 需要 $变量".to_string());
                }
                self.eat(1);
                let var = self.read_identifier();
                self.skip_spaces();
                if self.cur() != Some('=') {
                    return Err("#set 缺少 =".to_string());
                }
                self.eat(1);
                self.skip_spaces();
                let expr = self.parse_expression()?;
                self.skip_spaces();
                self.expect_char(')')?;
                Ok(Some(Node::Set { name: var, expr }))
            }
            "foreach" => {
                self.expect_char('(')?;
                self.skip_spaces();
                if self.cur() != Some('$') {
                    return Err("#foreach 需要 $变量".to_string());
                }
                self.eat(1);
                let var = self.read_identifier();
                self.skip_spaces();
                let word = self.word();
                if word != "in" {
                    return Err("#foreach 缺少 in".to_string());
                }
                self.eat(word.len());
                self.skip_spaces();
                let list = self.parse_expression()?;
                self.skip_spaces();
                self.expect_char(')')?;
                if alone {
                    self.gobble_eol();
                }
                let (body, _) = self.parse_nodes(&["end"], true)?;
                Ok(Some(Node::Foreach {
                    var,
                    list: Box::new(list),
                    body,
                }))
            }
            "if" => {
                self.expect_char('(')?;
                let cond = self.parse_expression()?;
                self.skip_spaces();
                self.expect_char(')')?;
                if alone {
                    self.gobble_after_header();
                }
                let mut branches = Vec::new();
                let (body, terminator) = self.parse_nodes(&["else", "elseif", "end"], false)?;
                branches.push((cond, body));
                let mut els = Vec::new();
                let mut current = terminator;
                loop {
                    match current.as_str() {
                        "elseif" => {
                            self.skip_spaces();
                            self.expect_char('(')?;
                            let next = self.parse_expression()?;
                            self.skip_spaces();
                            self.expect_char(')')?;
                            if alone {
                                self.gobble_after_header();
                            }
                            let (body, terminator) =
                                self.parse_nodes(&["else", "elseif", "end"], false)?;
                            branches.push((next, body));
                            current = terminator;
                        }
                        "else" => {
                            let (body, terminator) = self.parse_nodes(&["end"], false)?;
                            els = body;
                            current = terminator;
                        }
                        _ => break,
                    }
                }
                Ok(Some(Node::If { branches, els }))
            }
            "include" | "parse" | "macro" => Err(format!("模板用到未支持的指令 #{name}")),
            _ => Ok(None),
        }
    }

    fn expect_char(&mut self, ch: char) -> VelResult<()> {
        self.skip_spaces();
        if self.cur() == Some(ch) {
            self.eat(1);
            Ok(())
        } else {
            Err(format!("期望 {ch}，实际 {:?}", self.cur()))
        }
    }

    fn read_identifier(&mut self) -> String {
        let name = self.word();
        self.eat(name.chars().count());
        name
    }

    /// `#{ident}`：形式引用；解析不到时 Velocity 原样输出整段文本。
    fn try_formal_reference(&mut self) -> VelResult<Option<Node>> {
        if self.at(1) != Some('{') {
            return Ok(None);
        }
        let mut index = self.pos + 2;
        let mut name = String::new();
        while let Some(ch) = self.chars.get(index).copied() {
            if ch.is_ascii_alphanumeric() || ch == '_' {
                name.push(ch);
                index += 1;
            } else {
                break;
            }
        }
        if name.is_empty() || self.chars.get(index) != Some(&'}') {
            return Ok(None);
        }
        let src = format!("#{{{name}}}");
        self.pos = index + 1;
        Ok(Some(Node::Out {
            expr: Expr::Ref(vec![Seg::Prop(name)]),
            src,
            quiet: false,
        }))
    }

    /// 解析 `$name`、`$!name`、`${name}`、`$!${...}` 形式的引用，返回 (链, 是否静默, 结束位置)。
    fn read_reference_at(&self, pos: usize) -> Option<(Vec<Seg>, bool, usize)> {
        if self.chars.get(pos) != Some(&'$') {
            return None;
        }
        let mut index = pos + 1;
        let quiet = self.chars.get(index) == Some(&'!');
        if quiet {
            index += 1;
        }
        let braced = self.chars.get(index) == Some(&'{');
        if braced {
            index += 1;
        }
        if !matches!(self.chars.get(index), Some(ch) if ch.is_ascii_alphabetic()) {
            return None;
        }
        let Ok(segs) = self.chain_from(&mut index) else {
            return None;
        };
        if segs.is_empty() {
            return None;
        }
        if braced {
            if self.chars.get(index) == Some(&'}') {
                index += 1;
            } else {
                return None;
            }
        }
        Some((segs, quiet, index))
    }

    fn try_reference(&mut self) -> VelResult<Option<Node>> {
        let Some((segs, quiet, end)) = self.read_reference_at(self.pos) else {
            return Ok(None);
        };
        let src: String = self.chars[self.pos..end].iter().collect();
        self.pos = end;
        Ok(Some(Node::Out {
            expr: Expr::Ref(segs),
            src,
            quiet,
        }))
    }

    /// 从 `index`（指向名字首字母）解析 `name.prop.method(...)[i]...` 链。
    fn chain_from(&self, index: &mut usize) -> VelResult<Vec<Seg>> {
        let mut cursor = *index;
        let mut name = String::new();
        while let Some(ch) = self.chars.get(cursor).copied() {
            if ch.is_ascii_alphanumeric() || ch == '_' {
                name.push(ch);
                cursor += 1;
            } else {
                break;
            }
        }
        if name.is_empty() {
            *index = cursor;
            return Ok(Vec::new());
        }
        let mut segs: Vec<Seg> = vec![Seg::Prop(name)];
        loop {
            match self.chars.get(cursor).copied() {
                Some('.') => {
                    cursor += 1;
                    let mut prop = String::new();
                    while let Some(ch) = self.chars.get(cursor).copied() {
                        if ch.is_ascii_alphanumeric() || ch == '_' {
                            prop.push(ch);
                            cursor += 1;
                        } else {
                            break;
                        }
                    }
                    if prop.is_empty() {
                        break;
                    }
                    if self.chars.get(cursor) == Some(&'(') {
                        cursor += 1;
                        let args = self.parse_args_at(&mut cursor)?;
                        segs.push(Seg::Method(prop, args));
                    } else {
                        segs.push(Seg::Prop(prop));
                    }
                }
                Some('[') => {
                    cursor += 1;
                    let mut inner = Parser {
                        chars: self.chars[cursor..].to_vec(),
                        pos: 0,
                        line_has_content: false,
                    };
                    let expr = inner.parse_expression()?;
                    if inner.cur() != Some(']') {
                        break;
                    }
                    cursor += inner.pos + 1;
                    segs.push(Seg::Method("get".to_string(), vec![expr]));
                }
                _ => break,
            }
        }
        *index = cursor;
        Ok(segs)
    }

    /// 解析 `(...)` 内的实参列表，游标停在右括号之后。
    fn parse_args_at(&self, cursor: &mut usize) -> VelResult<Vec<Expr>> {
        let mut inner = Parser {
            chars: self.chars[*cursor..].to_vec(),
            pos: 0,
            line_has_content: false,
        };
        let mut args: Vec<Expr> = Vec::new();
        inner.skip_spaces();
        if inner.cur() != Some(')') {
            loop {
                let arg = inner.parse_expression()?;
                args.push(arg);
                inner.skip_spaces();
                if inner.cur() == Some(',') {
                    inner.eat(1);
                    inner.skip_spaces();
                    continue;
                }
                break;
            }
        }
        if inner.cur() != Some(')') {
            return Err("方法参数缺少 )".to_string());
        }
        *cursor += inner.pos + 1;
        Ok(args)
    }

    fn parse_expression(&mut self) -> VelResult<Expr> {
        let mut inner = Parser {
            chars: self.chars[self.pos..].to_vec(),
            pos: 0,
            line_has_content: false,
        };
        let expr = inner.parse_or()?;
        self.pos += inner.pos;
        Ok(expr)
    }

    fn parse_or(&mut self) -> VelResult<Expr> {
        let mut left = self.parse_and()?;
        loop {
            self.skip_spaces();
            if self.starts_with_symbol("||") || self.word() == "or" {
                self.eat(2);
                let right = self.parse_and()?;
                left = Expr::Or(Box::new(left), Box::new(right));
            } else {
                break;
            }
        }
        Ok(left)
    }

    fn parse_and(&mut self) -> VelResult<Expr> {
        let mut left = self.parse_cmp()?;
        loop {
            self.skip_spaces();
            if self.starts_with_symbol("&&") || self.word() == "and" {
                self.eat(2);
                let right = self.parse_cmp()?;
                left = Expr::And(Box::new(left), Box::new(right));
            } else {
                break;
            }
        }
        Ok(left)
    }

    fn starts_with_symbol(&self, symbol: &str) -> bool {
        symbol
            .chars()
            .enumerate()
            .all(|(index, ch)| self.chars.get(self.pos + index) == Some(&ch))
    }

    fn parse_cmp(&mut self) -> VelResult<Expr> {
        let left = self.parse_additive()?;
        self.skip_spaces();
        let op = if self.starts_with_symbol("==") || self.word() == "eq" {
            Some(CmpOp::Eq)
        } else if self.starts_with_symbol("!=") || self.word() == "ne" {
            Some(CmpOp::Ne)
        } else if self.starts_with_symbol("<=") || self.word() == "le" {
            Some(CmpOp::Le)
        } else if self.starts_with_symbol(">=") || self.word() == "ge" {
            Some(CmpOp::Ge)
        } else if self.cur() == Some('<') || self.word() == "lt" {
            Some(CmpOp::Lt)
        } else if self.cur() == Some('>') || self.word() == "gt" {
            Some(CmpOp::Gt)
        } else {
            None
        };
        let Some(op) = op else {
            return Ok(left);
        };
        self.eat(if self.word_matches_symbol(op) { 2 } else { 1 });
        let right = self.parse_additive()?;
        Ok(Expr::Cmp(Box::new(left), op, right.into()))
    }

    fn word_matches_symbol(&self, op: CmpOp) -> bool {
        matches!(op, CmpOp::Eq | CmpOp::Ne | CmpOp::Le | CmpOp::Ge)
    }

    fn parse_additive(&mut self) -> VelResult<Expr> {
        let mut items = vec![self.parse_unary()?];
        loop {
            self.skip_spaces();
            if self.cur() == Some('+') {
                self.eat(1);
                items.push(self.parse_unary()?);
            } else {
                break;
            }
        }
        Ok(if items.len() == 1 {
            items.pop().expect("one")
        } else {
            Expr::Add(items)
        })
    }

    fn parse_unary(&mut self) -> VelResult<Expr> {
        self.skip_spaces();
        if self.cur() == Some('!') && !self.starts_with_symbol("!=") {
            self.eat(1);
            let inner = self.parse_unary()?;
            return Ok(Expr::Not(Box::new(inner)));
        }
        if self.cur() == Some('-') || self.cur() == Some('+') {
            let negative = self.cur() == Some('-');
            self.eat(1);
            let inner = self.parse_unary()?;
            return Ok(if negative {
                match inner {
                    Expr::Lit(Value::Number(number)) if number.is_i64() => {
                        Expr::Lit(Value::from(-number.as_i64().unwrap_or(0)))
                    }
                    other => Expr::Neg(Box::new(other)),
                }
            } else {
                inner
            });
        }
        self.parse_atom()
    }

    fn parse_atom(&mut self) -> VelResult<Expr> {
        self.skip_spaces();
        match self.cur() {
            Some('(') => {
                self.eat(1);
                let expr = self.parse_or()?;
                self.skip_spaces();
                self.expect_char(')')?;
                Ok(expr)
            }
            Some('"') | Some('\'') => self.parse_string_literal(),
            Some('$') => {
                let Some((segs, _quiet, end)) = self.read_reference_at(self.pos) else {
                    return Err(format!(
                        "无法解析引用 @{}: {}",
                        self.pos,
                        self.chars[self.pos..(self.pos + 24).min(self.chars.len())]
                            .iter()
                            .collect::<String>()
                    ));
                };
                self.pos = end;
                Ok(Expr::Ref(segs))
            }
            Some(ch) if ch.is_ascii_digit() => {
                let mut digits = String::new();
                while let Some(ch) = self.cur() {
                    if ch.is_ascii_digit() || ch == '.' {
                        digits.push(ch);
                        self.eat(1);
                    } else {
                        break;
                    }
                }
                if let Ok(integer) = digits.parse::<i64>() {
                    return Ok(Expr::Lit(Value::from(integer)));
                }
                let float: f64 = digits.parse().map_err(|_| format!("非法数字 {digits}"))?;
                Ok(Expr::Lit(
                    serde_json::Number::from_f64(float)
                        .map(Value::Number)
                        .unwrap_or(Value::Null),
                ))
            }
            Some(ch) if ch.is_ascii_alphabetic() => {
                let word = self.word();
                self.eat(word.chars().count());
                match word.as_str() {
                    "true" => Ok(Expr::Lit(Value::Bool(true))),
                    "false" => Ok(Expr::Lit(Value::Bool(false))),
                    "null" => Ok(Expr::Lit(Value::Null)),
                    _ => Ok(Expr::Lit(Value::String(word))),
                }
            }
            other => Err(format!("表达式起始字符异常 {other:?}")),
        }
    }

    /// 双引号字符串里的 `$ref` 会被插值（`#set($k="$a$b")`）。
    fn parse_string_literal(&mut self) -> VelResult<Expr> {
        let quote = self.cur().unwrap_or('"');
        self.eat(1);
        let mut literal = String::new();
        let mut parts: Vec<Expr> = Vec::new();
        let flush = |literal: &mut String, parts: &mut Vec<Expr>| {
            if !literal.is_empty() {
                parts.push(Expr::Lit(Value::String(std::mem::take(literal))));
            }
        };
        while let Some(ch) = self.cur() {
            if ch == '\\' {
                if let Some(next) = self.at(1) {
                    literal.push(next);
                    self.eat(2);
                    continue;
                }
            }
            if ch == quote {
                self.eat(1);
                flush(&mut literal, &mut parts);
                // 空串字面量必须是 Lit("")，否则 `"" != $x` 这类比较会退化成未解析。
                return Ok(if parts.is_empty() {
                    Expr::Lit(Value::String(String::new()))
                } else if parts.len() == 1 {
                    parts.pop().expect("one")
                } else {
                    Expr::Add(parts)
                });
            }
            if ch == '$' {
                if let Some((segs, _quiet, end)) = self.read_reference_at(self.pos) {
                    let src: String = self.chars[self.pos..end].iter().collect();
                    flush(&mut literal, &mut parts);
                    self.pos = end;
                    parts.push(Expr::RefText(segs, src));
                    continue;
                }
            }
            literal.push(ch);
            self.eat(1);
        }
        flush(&mut literal, &mut parts);
        Ok(Expr::Lit(Value::String(literal)))
    }
}

fn render_nodes(nodes: &[Node], ctx: &mut Ctx, out: &mut String, flow: &mut Flow) -> VelResult<()> {
    for node in nodes {
        match node {
            Node::Text(text) => flow.push_text(out, text),
            Node::Verbatim(text) => flow.push_text(out, text),
            Node::Out { expr, src, quiet } => match eval_expr(expr, ctx) {
                Value_::Val(value) if !value.is_null() => out.push_str(&render_value(&value)),
                Value_::Val(ref value) if *quiet => out.push_str(&render_value(value)),
                _ => {
                    if !*quiet {
                        out.push_str(src);
                    }
                }
            },
            Node::Set { name, expr } => {
                let value = match eval_expr(expr, ctx) {
                    Value_::Val(value) => value,
                    Value_::Unresolved => Value::Null,
                };
                ctx.set(name, value);
            }
            Node::If { branches, els } => {
                let mut matched = false;
                for (cond, body) in branches {
                    if truthy(&eval_expr(cond, ctx)) {
                        matched = true;
                        render_nodes(body, ctx, out, flow)?;
                        break;
                    }
                }
                if !matched {
                    render_nodes(els, ctx, out, flow)?;
                }
            }
            Node::Foreach { var, list, body } => {
                let items = match eval_expr(list, ctx) {
                    Value_::Val(Value::Array(items)) => items,
                    Value_::Val(Value::Object(map)) => map
                        .iter()
                        .map(|(key, value)| {
                            json_with(|entry| {
                                entry.insert("key".to_string(), Value::String(key.clone()));
                                entry.insert("value".to_string(), value.clone());
                            })
                        })
                        .collect::<Vec<Value>>(),
                    _ => Vec::new(),
                };
                let size = items.len();
                for (index, item) in items.iter().enumerate() {
                    ctx.push();
                    ctx.set(var, item.clone());
                    // Velocity 2.3 已移除 $velocityCount（本地用 velocity-engine-core-2.3 实测：
                    // 普通与 ${} 形式都原样输出），只提供 $foreach.*。
                    let mut foreach = Map::new();
                    foreach.insert("count".to_string(), Value::from(index as i64 + 1));
                    foreach.insert("index".to_string(), Value::from(index as i64));
                    foreach.insert("first".to_string(), Value::Bool(index == 0));
                    foreach.insert("last".to_string(), Value::Bool(index + 1 == size));
                    foreach.insert("hasNext".to_string(), Value::Bool(index + 1 < size));
                    foreach.insert("hasPrev".to_string(), Value::Bool(index > 0));
                    foreach.insert("size".to_string(), Value::from(size as i64));
                    ctx.set("foreach", Value::Object(foreach));
                    let mut inner = Flow::with_crlf(flow.crlf);
                    render_nodes(body, ctx, out, &mut inner)?;
                    ctx.pop();
                    if inner.break_now {
                        flow.break_now = true;
                        break;
                    }
                    if flow.break_now {
                        return Ok(());
                    }
                }
            }
            Node::Break => {
                flow.break_now = true;
                return Ok(());
            }
            Node::Continue => return Ok(()),
        }
    }
    Ok(())
}

fn json_with(build: impl FnOnce(&mut Map<String, Value>)) -> Value {
    let mut map = Map::new();
    build(&mut map);
    Value::Object(map)
}

fn render_value(value: &Value) -> String {
    match value {
        Value::String(text) => text.clone(),
        Value::Bool(flag) => flag.to_string(),
        Value::Number(number) => number.to_string(),
        Value::Null => String::new(),
        other => other.to_string(),
    }
}

/// Java/VelocityEngine 2.3 的真值规则：未解析或 null 为假；Boolean 取本身；
/// 空字符串为假（模板靠 `#elseif(... && $dictType)` 跳过无字典的列）；其余对象为真。
fn truthy(value: &Value_) -> bool {
    match value {
        Value_::Unresolved => false,
        Value_::Val(Value::Null) => false,
        Value_::Val(Value::Bool(flag)) => *flag,
        Value_::Val(Value::String(text)) => !text.is_empty(),
        _ => true,
    }
}

fn as_number(value: &Value_) -> Option<f64> {
    match value {
        Value_::Val(Value::Number(number)) => number.as_f64(),
        Value_::Val(Value::String(text)) => text.parse::<f64>().ok(),
        _ => None,
    }
}

fn as_text(value: &Value_) -> Option<String> {
    match value {
        Value_::Val(value) if value.is_null() => None,
        Value_::Val(value) => Some(render_value(value)),
        Value_::Unresolved => None,
    }
}

pub fn eval_expr(expr: &Expr, ctx: &Ctx) -> Value_ {
    match expr {
        Expr::Lit(value) => Value_::Val(value.clone()),
        Expr::Ref(segs) => eval_ref(segs, ctx),
        Expr::RefText(segs, src) => match eval_ref(segs, ctx) {
            Value_::Val(value) => Value_::Val(value),
            Value_::Unresolved => Value_::Val(Value::String(src.clone())),
        },
        Expr::Not(inner) => Value_::Val(Value::Bool(!truthy(&eval_expr(inner, ctx)))),
        Expr::Neg(inner) => match eval_expr(inner, ctx) {
            Value_::Val(Value::Number(number)) => {
                if let Some(integer) = number.as_i64() {
                    Value_::Val(Value::from(-integer))
                } else {
                    let float = number.as_f64().unwrap_or(0.0);
                    Value_::Val(
                        serde_json::Number::from_f64(-float)
                            .map(Value::Number)
                            .unwrap_or(Value::Null),
                    )
                }
            }
            _ => Value_::Unresolved,
        },
        Expr::Add(items) => {
            let mut acc: Option<Value_> = None;
            for item in items {
                let right = eval_expr(item, ctx);
                acc = Some(match acc {
                    None => right,
                    Some(left) => add(&left, &right),
                });
            }
            acc.unwrap_or(Value_::Unresolved)
        }
        Expr::Cmp(left, op, right) => {
            let l = eval_expr(left, ctx);
            let r = eval_expr(right, ctx);
            Value_::Val(Value::Bool(compare(&l, *op, &r)))
        }
        Expr::And(l, r) => Value_::Val(Value::Bool(
            truthy(&eval_expr(l, ctx)) && truthy(&eval_expr(r, ctx)),
        )),
        Expr::Or(l, r) => Value_::Val(Value::Bool(
            truthy(&eval_expr(l, ctx)) || truthy(&eval_expr(r, ctx)),
        )),
    }
}

fn add(left: &Value_, right: &Value_) -> Value_ {
    if let (Some(a), Some(b)) = (as_number(left), as_number(right)) {
        if !matches!(left, Value_::Val(Value::String(_)))
            && !matches!(right, Value_::Val(Value::String(_)))
        {
            let sum = a + b;
            if sum.fract() == 0.0 && left.is_int_like() && right.is_int_like() {
                return Value_::Val(Value::from(sum as i64));
            }
            return Value_::Val(
                serde_json::Number::from_f64(sum)
                    .map(Value::Number)
                    .unwrap_or(Value::Null),
            );
        }
    }
    match (as_text(left), as_text(right)) {
        (Some(a), Some(b)) => Value_::Val(Value::String(format!("{a}{b}"))),
        (Some(a), None) => Value_::Val(Value::String(a.to_string())),
        (None, Some(b)) => Value_::Val(Value::String(b.to_string())),
        (None, None) => Value_::Unresolved,
    }
}

trait IsIntLike {
    fn is_int_like(&self) -> bool;
}

impl IsIntLike for Value_ {
    fn is_int_like(&self) -> bool {
        matches!(self, Value_::Val(Value::Number(number)) if number.is_i64())
    }
}

fn compare(left: &Value_, op: CmpOp, right: &Value_) -> bool {
    let ord = match (left, right) {
        (Value_::Val(Value::Null), Value_::Val(Value::Null)) => Some(std::cmp::Ordering::Equal),
        (Value_::Unresolved, Value_::Unresolved) => Some(std::cmp::Ordering::Equal),
        (Value_::Val(Value::Null), _) | (_, Value_::Val(Value::Null)) => {
            // Java: null 与字面量比较恒为 false（除 null == null）
            None
        }
        (Value_::Unresolved, _) | (_, Value_::Unresolved) => None,
        (Value_::Val(a), Value_::Val(b)) => {
            if let (Some(x), Some(y)) = (a.as_f64(), b.as_f64()) {
                Some(x.partial_cmp(&y).unwrap_or(std::cmp::Ordering::Equal))
            } else if a.is_boolean() && b.is_boolean() {
                Some(a.as_bool().cmp(&b.as_bool()))
            } else {
                Some(render_value(a).cmp(&render_value(b)))
            }
        }
    };
    match ord {
        Some(ordering) => match op {
            CmpOp::Eq => ordering == std::cmp::Ordering::Equal,
            CmpOp::Ne => ordering != std::cmp::Ordering::Equal,
            CmpOp::Lt => ordering == std::cmp::Ordering::Less,
            CmpOp::Le => ordering != std::cmp::Ordering::Greater,
            CmpOp::Gt => ordering == std::cmp::Ordering::Greater,
            CmpOp::Ge => ordering != std::cmp::Ordering::Less,
        },
        None => op == CmpOp::Ne,
    }
}

fn eval_ref(segs: &[Seg], ctx: &Ctx) -> Value_ {
    let mut current = match segs.first() {
        Some(Seg::Prop(name)) => match ctx.get(name) {
            Some(value) => Value_::Val(value.clone()),
            None => return Value_::Unresolved,
        },
        _ => return Value_::Unresolved,
    };
    for seg in &segs[1..] {
        current = match seg {
            Seg::Prop(name) => property(&current, name),
            Seg::Method(name, args) => call(&current, name, args, ctx),
        };
        if matches!(current, Value_::Unresolved) {
            return Value_::Unresolved;
        }
    }
    current
}

fn bean_key<'a>(object: &'a Map<String, Value>, name: &str) -> Option<&'a Value> {
    if let Some(value) = object.get(name) {
        return Some(value);
    }
    let capitalized = {
        let mut chars = name.chars();
        match chars.next() {
            Some(first) => format!("{}{}", first.to_uppercase(), chars.as_str()),
            None => String::new(),
        }
    };
    object
        .get(&format!("is{capitalized}"))
        .or_else(|| object.get(&format!("get{capitalized}")))
}

fn property(current: &Value_, name: &str) -> Value_ {
    let object = match current {
        Value_::Val(Value::Object(map)) => map,
        _ => return Value_::Unresolved,
    };
    match bean_key(object, name) {
        Some(Value::Null) => Value_::Unresolved,
        Some(value) => Value_::Val(value.clone()),
        None => Value_::Unresolved,
    }
}

fn call(current: &Value_, name: &str, args: &[Expr], ctx: &Ctx) -> Value_ {
    let arg_values: Vec<Value_> = args.iter().map(|arg| eval_expr(arg, ctx)).collect();
    let text = as_text(current);
    let number_len = |value: &Value_| -> i64 {
        match value {
            Value_::Val(Value::Array(items)) => items.len() as i64,
            Value_::Val(Value::Object(map)) => map.len() as i64,
            Value_::Val(Value::String(s)) => s.chars().count() as i64,
            _ => 0,
        }
    };
    match name {
        "length" | "size" => match current {
            Value_::Val(value) => Value_::Val(Value::from(match value {
                Value::Array(items) => items.len() as i64,
                Value::Object(map) => map.len() as i64,
                Value::String(text) => text.chars().count() as i64,
                _ => number_len(current),
            })),
            _ => Value_::Unresolved,
        },
        "isEmpty" => Value_::Val(Value::Bool(match current {
            Value_::Val(Value::Array(items)) => items.is_empty(),
            Value_::Val(Value::Object(map)) => map.is_empty(),
            Value_::Val(Value::String(text)) => text.is_empty(),
            _ => true,
        })),
        "trim" => Value_::Val(
            text.map(|value| Value::String(value.trim().to_string()))
                .unwrap_or(Value::Null),
        ),
        "toUpperCase" => Value_::Val(
            text.map(|value| Value::String(value.to_uppercase()))
                .unwrap_or(Value::Null),
        ),
        "toLowerCase" => Value_::Val(
            text.map(|value| Value::String(value.to_lowercase()))
                .unwrap_or(Value::Null),
        ),
        "toString" => Value_::Val(
            text.map(Value::String)
                .unwrap_or(Value::String(String::new())),
        ),
        // Java: String.indexOf 返回 UTF-16 码元下标；模板里紧接着 substring(...) 也按字符计数，
        // 所以这里必须换算成字符下标，否则中文备注会被截在错误位置。
        "indexOf" => {
            let needle =
                as_text(arg_values.first().unwrap_or(&Value_::Unresolved)).unwrap_or_default();
            match &text {
                Some(hay) => Value_::Val(Value::from(
                    hay.find(&needle)
                        .map(|byte| hay[..byte].chars().count() as i64)
                        .unwrap_or(-1),
                )),
                None => Value_::Unresolved,
            }
        }
        "startsWith" => {
            let needle =
                as_text(arg_values.first().unwrap_or(&Value_::Unresolved)).unwrap_or_default();
            Value_::Val(Value::Bool(
                text.map(|hay| hay.starts_with(&needle)).unwrap_or(false),
            ))
        }
        "endsWith" => {
            let needle =
                as_text(arg_values.first().unwrap_or(&Value_::Unresolved)).unwrap_or_default();
            Value_::Val(Value::Bool(
                text.map(|hay| hay.ends_with(&needle)).unwrap_or(false),
            ))
        }
        "contains" => {
            let needle =
                as_text(arg_values.first().unwrap_or(&Value_::Unresolved)).unwrap_or_default();
            match current {
                Value_::Val(Value::Array(items)) => Value_::Val(Value::Bool(
                    items.iter().any(|item| render_value(item) == needle),
                )),
                _ => Value_::Val(Value::Bool(
                    text.map(|hay| hay.contains(&needle)).unwrap_or(false),
                )),
            }
        }
        "matches" => {
            let pattern =
                as_text(arg_values.first().unwrap_or(&Value_::Unresolved)).unwrap_or_default();
            match (&text, regex::Regex::new(&pattern)) {
                (Some(hay), Ok(re)) => Value_::Val(Value::Bool(re.is_match(hay))),
                _ => Value_::Val(Value::Bool(false)),
            }
        }
        "substring" => {
            let Some(hay) = &text else {
                return Value_::Unresolved;
            };
            let chars: Vec<char> = hay.chars().collect();
            let begin = arg_values.first().and_then(as_number).unwrap_or(0.0) as usize;
            let end = match arg_values.get(1) {
                Some(value) => as_number(value).unwrap_or(chars.len() as f64) as usize,
                None => chars.len(),
            };
            if begin > end || end > chars.len() || begin > chars.len() {
                // Java: String.substring 越界抛异常 -> 整页 500
                return Value_::Unresolved;
            }
            Value_::Val(Value::String(chars[begin..end].iter().collect()))
        }
        "replace" => {
            let from =
                as_text(arg_values.first().unwrap_or(&Value_::Unresolved)).unwrap_or_default();
            let to = as_text(arg_values.get(1).unwrap_or(&Value_::Unresolved)).unwrap_or_default();
            Value_::Val(
                text.map(|hay| Value::String(hay.replace(&from, &to)))
                    .unwrap_or(Value::Null),
            )
        }
        "split" => {
            let sep =
                as_text(arg_values.first().unwrap_or(&Value_::Unresolved)).unwrap_or_default();
            Value_::Val(match &text {
                Some(hay) => Value::Array(if sep.is_empty() {
                    hay.chars().map(|c| Value::String(c.to_string())).collect()
                } else {
                    hay.split(sep.as_str())
                        .map(|part| Value::String(part.to_string()))
                        .collect()
                }),
                None => Value::Array(Vec::new()),
            })
        }
        "join" => {
            let sep =
                as_text(arg_values.first().unwrap_or(&Value_::Unresolved)).unwrap_or_default();
            match current {
                Value_::Val(Value::Array(items)) => Value_::Val(Value::String(
                    items
                        .iter()
                        .map(render_value)
                        .collect::<Vec<_>>()
                        .join(&sep),
                )),
                _ => Value_::Unresolved,
            }
        }
        "get" => {
            let index = arg_values.first().and_then(as_number).unwrap_or(0.0) as usize;
            match current {
                Value_::Val(Value::Array(items)) => items
                    .get(index)
                    .map(|value| Value_::Val(value.clone()))
                    .unwrap_or(Value_::Unresolved),
                _ => Value_::Unresolved,
            }
        }
        "keySet" | "keys" => match current {
            Value_::Val(Value::Object(map)) => Value_::Val(Value::Array(
                map.keys().map(|key| Value::String(key.clone())).collect(),
            )),
            _ => Value_::Unresolved,
        },
        "values" => match current {
            Value_::Val(Value::Object(map)) => {
                Value_::Val(Value::Array(map.values().cloned().collect()))
            }
            _ => Value_::Unresolved,
        },
        "entrySet" | "entries" => match current {
            Value_::Val(Value::Object(map)) => Value_::Val(Value::Array(
                map.iter()
                    .map(|(key, value)| {
                        json_with(|entry| {
                            entry.insert("key".to_string(), Value::String(key.clone()));
                            entry.insert("value".to_string(), value.clone());
                        })
                    })
                    .collect(),
            )),
            _ => Value_::Unresolved,
        },
        "put" => {
            let mut map = match current {
                Value_::Val(Value::Object(map)) => map.clone(),
                _ => Map::new(),
            };
            let key =
                as_text(arg_values.first().unwrap_or(&Value_::Unresolved)).unwrap_or_default();
            let value = match arg_values.get(1) {
                Some(Value_::Val(value)) => value.clone(),
                _ => Value::Null,
            };
            map.insert(key, value);
            Value_::Val(Value::Object(map))
        }
        "add" => {
            let mut items = match current {
                Value_::Val(Value::Array(items)) => items.clone(),
                _ => Vec::new(),
            };
            if let Some(Value_::Val(value)) = arg_values.first() {
                items.push(value.clone());
            }
            Value_::Val(Value::Array(items))
        }
        // Java: GenTable.isSuperColumn(javaField) / GenTableColumn.isUsableColumn(javaField)
        "isSuperColumn" | "isUsableColumn" => {
            let field = as_text(arg_values.first().unwrap_or(&Value_::Unresolved))
                .unwrap_or_default()
                .to_lowercase();
            let list: &[&str] = if name == "isSuperColumn" {
                &[
                    "createby",
                    "createtime",
                    "updateby",
                    "updatetime",
                    "remark",
                    "parentname",
                    "parentid",
                    "ordernum",
                    "ancestors",
                ]
            } else {
                &["parentid", "ordernum", "remark"]
            };
            Value_::Val(Value::Bool(list.contains(&field.as_str())))
        }
        // 数字/日期之类的取值方法
        "intValue" | "longValue" => Value_::Val(
            as_number(current)
                .map(|number| Value::from(number as i64))
                .unwrap_or(Value::Null),
        ),
        _ => {
            // 未知方法：交给上下文里预置的同名值（例如 readConverterExp 由调用方算好）
            match current {
                Value_::Val(Value::Object(map)) => match bean_key(map, name) {
                    Some(Value::Null) | None => Value_::Unresolved,
                    Some(value) => Value_::Val(value.clone()),
                },
                _ => Value_::Unresolved,
            }
        }
    }
}

impl fmt::Display for Node {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{self:?}")
    }
}

#[cfg(test)]
mod space_gobbling {
    use super::*;
    use serde_json::json;

    fn render_with(pairs: &[(&str, Value)], template: &str) -> String {
        let mut map = Map::new();
        for (key, value) in pairs {
            map.insert((*key).to_string(), value.clone());
        }
        let mut ctx = Ctx::with_root(map);
        render(template, &mut ctx).unwrap()
    }

    /// vm/vue/index.vue.vm:109：独占一行的 #if 之后同行还有别的指令时，
    /// 只吞指令头后面的空白；#foreach 的收尾 #end 连换行一起吞，正文里的 #set 不再算独占一行。
    #[test]
    fn inline_if_foreach_set_end() {
        let template = concat!(
            "return {
",
            "            #if($ok)  #foreach($d in $dicts)   #set($k=\"$d\")  $k: [],#end
",
            "            #end
",
            "                /** c */
"
        );
        let out = render_with(
            &[
                ("ok", json!(true)),
                ("dicts", json!(["carType", "runType"])),
            ],
            template,
        );
        assert_eq!(
            out,
            "return {
     carType: [],     runType: [],                /** c */
"
        );
    }

    /// vm/xml/mapper.xml.vm:32-33：#if 的收尾 #end 只吞本行缩进、不吞换行（列清单靠它分行），
    /// 只有 #foreach 的收尾 #end 才吞掉换行。
    #[test]
    fn foreach_lines_keep_separating_newline() {
        let template = concat!(
            "<a>
",
            "    #foreach($c in $cols) x=$c#if($foreach.hasNext),
",
            "    #end#end
",
            "</a>
"
        );
        let out = render_with(&[("cols", json!(["id", "no"]))], template);
        assert_eq!(
            out,
            "<a>
 x=id,
 x=no</a>
"
        );
    }

    /// 模板 CRLF 原样保留（Java 侧模板文件本身就是 CRLF，产物也是 CRLF）。
    #[test]
    fn keeps_crlf_line_endings() {
        let cr = char::from_u32(13).unwrap_or('x').to_string();
        let template = format!(
            "a{cr}
b{cr}
"
        );
        let out = render_with(&[("unused", json!(1))], &template);
        assert_eq!(out, template);
    }
}
