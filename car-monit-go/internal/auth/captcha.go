// JAVA 对照: ruoyi-admin/src/main/java/com/ruoyi/web/controller/common/CaptchaController.java
// JAVA 对照: ruoyi-framework/src/main/java/com/ruoyi/framework/config/CaptchaConfig.java
// JAVA 对照: ruoyi-framework/src/main/java/com/ruoyi/framework/config/KaptchaTextCreator.java
// 类/职责: 验证码生成（math / char）
// 对应 Go 文件: internal/auth/captcha.go
//
// DIFF: Java 使用 Google Kaptcha（AWT 字体 + ShadowGimpy 阴影）生成 160x60 JPEG；
// Go 侧不引入 TrueType 字体依赖，用内置 5x7 点阵位图字体绘制同尺寸 JPEG。
// 响应仍是 Base64 字符串（前端自行拼 data:image/gif;base64, 前缀），与 Java 一致。
// 行为保持：验证码答案存 Redis（captcha_codes:<uuid>，2 分钟），校验后立即删除。
package auth

import (
	"bytes"
	crand "crypto/rand"
	"encoding/base64"
	"fmt"
	"image"
	"image/color"
	"image/jpeg"
	"math/big"
	"strings"

	"github.com/google/uuid"
)

const (
	captchaWidth  = 160
	captchaHeight = 60
	glyphScale    = 3
	glyphWidth    = 5
	glyphHeight   = 7
	charGap       = 7
)

// newCaptchaImage 返回 (uuid, base64(jpeg), answer, error)。
func newCaptchaImage(captchaType string) (string, string, string, error) {
	id := uuid.NewString()
	var expression, answer string
	if strings.EqualFold(captchaType, "char") {
		const chars = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
		var b strings.Builder
		for i := 0; i < 4; i++ {
			b.WriteByte(chars[randInt(len(chars))])
		}
		answer = b.String()
		expression = answer
	} else {
		a := randInt(9) + 1
		b := randInt(9) + 1
		op := "+"
		result := a + b
		if randInt(2) == 0 && a > b {
			op = "-"
			result = a - b
		}
		expression = fmt.Sprintf("%d%s%d=?", a, op, b)
		answer = fmt.Sprintf("%d", result)
	}

	img, err := renderJPEG(expression)
	if err != nil {
		return "", "", "", err
	}
	return id, base64.StdEncoding.EncodeToString(img), answer, nil
}

// renderJPEG 绘制 160x60 验证码位图。文本只含数字/字母/运算符，无注入风险。
func renderJPEG(text string) ([]byte, error) {
	img := image.NewRGBA(image.Rect(0, 0, captchaWidth, captchaHeight))

	// 背景：白到浅灰的斜向渐变。
	for y := 0; y < captchaHeight; y++ {
		for x := 0; x < captchaWidth; x++ {
			v := uint8(250 - (x+y)*60/(captchaWidth+captchaHeight))
			img.SetRGBA(x, y, color.RGBA{v, v, v, 255})
		}
	}
	// 噪点
	for i := 0; i < 120; i++ {
		c := rgb(randInt(160), randInt(160), randInt(160))
		img.SetRGBA(randInt(captchaWidth), randInt(captchaHeight), c)
	}
	// 干扰线
	for i := 0; i < 5; i++ {
		drawLine(img, randInt(captchaWidth), randInt(captchaHeight),
			randInt(captchaWidth), randInt(captchaHeight), rgb(90+randInt(80), 90+randInt(80), 90+randInt(80)))
	}
	// 边框
	drawRect(img, rgb(105, 179, 90))

	// 文本
	totalWidth := len(text)*(glyphWidth*glyphScale+charGap) - charGap
	x := (captchaWidth - totalWidth) / 2
	baseY := (captchaHeight - glyphHeight*glyphScale) / 2
	for _, ch := range text {
		glyph, ok := bitmapFont[byte(ch)]
		if !ok {
			glyph = bitmapFont['?']
		}
		c := rgb(20+randInt(80), 20+randInt(80), 20+randInt(80))
		drawGlyph(img, glyph, x, baseY+randInt(7)-3, c)
		x += glyphWidth*glyphScale + charGap
	}

	var buf bytes.Buffer
	if err := jpeg.Encode(&buf, img, &jpeg.Options{Quality: 90}); err != nil {
		return nil, err
	}
	return buf.Bytes(), nil
}

// drawGlyph 把 5x7 点阵按 glyphScale 放大绘制。
func drawGlyph(img *image.RGBA, glyph [7]string, x0, y0 int, c color.RGBA) {
	for row, line := range glyph {
		for col := 0; col < len(line); col++ {
			if line[col] != '1' {
				continue
			}
			for dy := 0; dy < glyphScale; dy++ {
				for dx := 0; dx < glyphScale; dx++ {
					img.SetRGBA(x0+col*glyphScale+dx, y0+row*glyphScale+dy, c)
				}
			}
		}
	}
}

func drawLine(img *image.RGBA, x0, y0, x1, y1 int, c color.RGBA) {
	dx := abs(x1 - x0)
	dy := -abs(y1 - y0)
	sx, sy := -1, -1
	if x0 < x1 {
		sx = 1
	}
	if y0 < y1 {
		sy = 1
	}
	err := dx + dy
	for {
		if image.Pt(x0, y0).In(img.Bounds()) {
			img.SetRGBA(x0, y0, c)
		}
		if x0 == x1 && y0 == y1 {
			return
		}
		e2 := 2 * err
		if e2 >= dy {
			err += dy
			x0 += sx
		}
		if e2 <= dx {
			err += dx
			y0 += sy
		}
	}
}

func drawRect(img *image.RGBA, c color.RGBA) {
	for x := 0; x < captchaWidth; x++ {
		img.SetRGBA(x, 0, c)
		img.SetRGBA(x, captchaHeight-1, c)
	}
	for y := 0; y < captchaHeight; y++ {
		img.SetRGBA(0, y, c)
		img.SetRGBA(captchaWidth-1, y, c)
	}
}

func rgb(r, g, b int) color.RGBA {
	return color.RGBA{uint8(r), uint8(g), uint8(b), 255}
}

func abs(v int) int {
	if v < 0 {
		return -v
	}
	return v
}

// bitmapFont 5x7 点阵字体，覆盖数字、大写字母与运算符号。
var bitmapFont = map[byte][7]string{
	'0': {"01110", "10001", "10011", "10101", "11001", "10001", "01110"},
	'1': {"00100", "01100", "00100", "00100", "00100", "00100", "01110"},
	'2': {"01110", "10001", "00001", "00010", "00100", "01000", "11111"},
	'3': {"11111", "00010", "00100", "00010", "00001", "10001", "01110"},
	'4': {"00010", "00110", "01010", "10010", "11111", "00010", "00010"},
	'5': {"11111", "10000", "11110", "00001", "00001", "10001", "01110"},
	'6': {"00110", "01000", "10000", "11110", "10001", "10001", "01110"},
	'7': {"11111", "00001", "00010", "00100", "01000", "01000", "01000"},
	'8': {"01110", "10001", "10001", "01110", "10001", "10001", "01110"},
	'9': {"01110", "10001", "10001", "01111", "00001", "00010", "01100"},
	'+': {"00000", "00100", "00100", "11111", "00100", "00100", "00000"},
	'-': {"00000", "00000", "00000", "11111", "00000", "00000", "00000"},
	'=': {"00000", "00000", "11111", "00000", "11111", "00000", "00000"},
	'?': {"01110", "10001", "00001", "00010", "00100", "00100", "00000"},
	'A': {"01110", "10001", "10001", "11111", "10001", "10001", "10001"},
	'B': {"11110", "10001", "10001", "11110", "10001", "10001", "11110"},
	'C': {"01110", "10001", "10000", "10000", "10000", "10001", "01110"},
	'D': {"11110", "10001", "10001", "10001", "10001", "10001", "11110"},
	'E': {"11111", "10000", "10000", "11110", "10000", "10000", "11111"},
	'F': {"11111", "10000", "10000", "11110", "10000", "10000", "10000"},
	'G': {"01110", "10001", "10000", "10111", "10001", "10001", "01111"},
	'H': {"10001", "10001", "10001", "11111", "10001", "10001", "10001"},
	'I': {"01110", "00100", "00100", "00100", "00100", "00100", "01110"},
	'J': {"00111", "00010", "00010", "00010", "00010", "10010", "01100"},
	'K': {"10001", "10010", "10100", "11000", "10100", "10010", "10001"},
	'L': {"10000", "10000", "10000", "10000", "10000", "10000", "11111"},
	'M': {"10001", "11011", "10101", "10101", "10001", "10001", "10001"},
	'N': {"10001", "11001", "10101", "10011", "10001", "10001", "10001"},
	'O': {"01110", "10001", "10001", "10001", "10001", "10001", "01110"},
	'P': {"11110", "10001", "10001", "11110", "10000", "10000", "10000"},
	'Q': {"01110", "10001", "10001", "10001", "10101", "10010", "01101"},
	'R': {"11110", "10001", "10001", "11110", "10100", "10010", "10001"},
	'S': {"01111", "10000", "10000", "01110", "00001", "00001", "11110"},
	'T': {"11111", "00100", "00100", "00100", "00100", "00100", "00100"},
	'U': {"10001", "10001", "10001", "10001", "10001", "10001", "01110"},
	'V': {"10001", "10001", "10001", "10001", "10001", "01010", "00100"},
	'W': {"10001", "10001", "10001", "10101", "10101", "10101", "01010"},
	'X': {"10001", "10001", "01010", "00100", "01010", "10001", "10001"},
	'Y': {"10001", "10001", "01010", "00100", "00100", "00100", "00100"},
	'Z': {"11111", "00001", "00010", "00100", "01000", "10000", "11111"},
}

// randInt 使用密码学随机源；验证码答案不依赖 math/rand 的伪随机序列。
func randInt(n int) int {
	if n <= 0 {
		return 0
	}
	v, err := crand.Int(crand.Reader, big.NewInt(int64(n)))
	if err != nil {
		return 0
	}
	return int(v.Int64())
}
