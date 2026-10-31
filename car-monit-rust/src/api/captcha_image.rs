// 来源: com.google.code.kaptcha（CaptchaConfig + KaptchaTextCreator 的等价实现）
// 职责: 生成验证码图片（JPEG），Rust 侧用内置 5x7 点阵字体渲染。
// 对应关系: DefaultKaptcha.createImage -> render；KaptchaTextCreator.getText -> math_text。

use image::codecs::jpeg::JpegEncoder;
use image::{Rgb, RgbImage};
use rand::Rng;

use crate::error::AppError;

const WIDTH: u32 = 160;
const HEIGHT: u32 = 60;
const SCALE: u32 = 5;
const GLYPH_W: u32 = 5;
const GLYPH_H: u32 = 7;
const SPACING: u32 = 3;

/// Java: KaptchaTextCreator.getText()
/// 返回值格式 "{算式}@{答案}"，调用方按最后一个 '@' 切分。
pub fn math_text() -> String {
    let mut rng = rand::thread_rng();
    let x: i32 = rng.gen_range(0..10);
    let y: i32 = rng.gen_range(0..10);
    let op: i32 = rng.gen_range(0..3);

    let (expr, result) = if op == 0 {
        (format!("{x}*{y}"), x * y)
    } else if op == 1 {
        if x != 0 && y % x == 0 {
            (format!("{y}/{x}"), y / x)
        } else {
            (format!("{x}+{y}"), x + y)
        }
    } else if x >= y {
        (format!("{x}-{y}"), x - y)
    } else {
        (format!("{y}-{x}"), y - x)
    };

    format!("{expr}=?@{result}")
}

/// kaptcha 默认字符集（char 模式）
pub fn char_text(len: usize) -> String {
    const CHARS: &[u8] = b"ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
    let mut rng = rand::thread_rng();
    (0..len)
        .map(|_| CHARS[rng.gen_range(0..CHARS.len())] as char)
        .collect()
}

/// Java: DefaultKaptcha.createImage(String) -> BufferedImage -> ImageIO.write(jpg)
pub fn render(text: &str) -> Result<Vec<u8>, AppError> {
    let mut img = RgbImage::from_pixel(WIDTH, HEIGHT, Rgb([245, 245, 245]));

    // 边框（kaptcha: border=yes）
    for x in 0..WIDTH {
        img.put_pixel(x, 0, Rgb([120, 120, 120]));
        img.put_pixel(x, HEIGHT - 1, Rgb([120, 120, 120]));
    }
    for y in 0..HEIGHT {
        img.put_pixel(0, y, Rgb([120, 120, 120]));
        img.put_pixel(WIDTH - 1, y, Rgb([120, 120, 120]));
    }

    let glyph_count = text.chars().count() as u32;
    let text_width = glyph_count * GLYPH_W * SCALE + glyph_count.saturating_sub(1) * SPACING;
    let start_x = WIDTH.saturating_sub(text_width) / 2;
    let start_y = (HEIGHT.saturating_sub(GLYPH_H * SCALE)) / 2;

    for (index, ch) in text.chars().enumerate() {
        let Some(glyph) = glyph(ch.to_ascii_uppercase()) else {
            continue;
        };
        let offset_x = start_x + index as u32 * (GLYPH_W * SCALE + SPACING);
        for (row, line) in glyph.iter().enumerate() {
            for (col, bit) in line.bytes().enumerate() {
                if bit == b'1' {
                    for dy in 0..SCALE {
                        for dx in 0..SCALE {
                            let px = offset_x + col as u32 * SCALE + dx;
                            let py = start_y + row as u32 * SCALE + dy;
                            if px < WIDTH && py < HEIGHT {
                                img.put_pixel(px, py, Rgb([20, 20, 20]));
                            }
                        }
                    }
                }
            }
        }
    }

    // 少量噪点（kaptcha 默认会绘制干扰）
    let mut rng = rand::thread_rng();
    for _ in 0..40 {
        let px = rng.gen_range(1..WIDTH - 1);
        let py = rng.gen_range(1..HEIGHT - 1);
        let shade = rng.gen_range(120..200);
        img.put_pixel(px, py, Rgb([shade, shade, shade]));
    }

    let mut buffer = Vec::new();
    JpegEncoder::new_with_quality(&mut buffer, 85)
        .encode_image(&img)
        .map_err(|e| AppError::internal(format!("验证码图片编码失败: {e}")))?;
    Ok(buffer)
}

fn glyph(c: char) -> Option<[&'static str; 7]> {
    let rows = match c {
        '0' => [
            "01110", "10001", "10011", "10101", "11001", "10001", "01110",
        ],
        '1' => [
            "00100", "01100", "00100", "00100", "00100", "00100", "01110",
        ],
        '2' => [
            "01110", "10001", "00001", "00010", "00100", "01000", "11111",
        ],
        '3' => [
            "11111", "00010", "00100", "00010", "00001", "10001", "01110",
        ],
        '4' => [
            "00010", "00110", "01010", "10010", "11111", "00010", "00010",
        ],
        '5' => [
            "11111", "10000", "11110", "00001", "00001", "10001", "01110",
        ],
        '6' => [
            "00110", "01000", "10000", "11110", "10001", "10001", "01110",
        ],
        '7' => [
            "11111", "00001", "00010", "00100", "01000", "01000", "01000",
        ],
        '8' => [
            "01110", "10001", "10001", "01110", "10001", "10001", "01110",
        ],
        '9' => [
            "01110", "10001", "10001", "01111", "00001", "00010", "01100",
        ],
        'A' => [
            "01110", "10001", "10001", "11111", "10001", "10001", "10001",
        ],
        'B' => [
            "11110", "10001", "10001", "11110", "10001", "10001", "11110",
        ],
        'C' => [
            "01110", "10001", "10000", "10000", "10000", "10001", "01110",
        ],
        'D' => [
            "11110", "10001", "10001", "10001", "10001", "10001", "11110",
        ],
        'E' => [
            "11111", "10000", "10000", "11110", "10000", "10000", "11111",
        ],
        'F' => [
            "11111", "10000", "10000", "11110", "10000", "10000", "10000",
        ],
        'G' => [
            "01110", "10001", "10000", "10111", "10001", "10001", "01111",
        ],
        'H' => [
            "10001", "10001", "10001", "11111", "10001", "10001", "10001",
        ],
        'I' => [
            "01110", "00100", "00100", "00100", "00100", "00100", "01110",
        ],
        'J' => [
            "00111", "00010", "00010", "00010", "00010", "10010", "01100",
        ],
        'K' => [
            "10001", "10010", "10100", "11000", "10100", "10010", "10001",
        ],
        'L' => [
            "10000", "10000", "10000", "10000", "10000", "10000", "11111",
        ],
        'M' => [
            "10001", "11011", "10101", "10101", "10001", "10001", "10001",
        ],
        'N' => [
            "10001", "11001", "10101", "10011", "10001", "10001", "10001",
        ],
        'O' => [
            "01110", "10001", "10001", "10001", "10001", "10001", "01110",
        ],
        'P' => [
            "11110", "10001", "10001", "11110", "10000", "10000", "10000",
        ],
        'Q' => [
            "01110", "10001", "10001", "10001", "10101", "10010", "01101",
        ],
        'R' => [
            "11110", "10001", "10001", "11110", "10100", "10010", "10001",
        ],
        'S' => [
            "01111", "10000", "10000", "01110", "00001", "00001", "11110",
        ],
        'T' => [
            "11111", "00100", "00100", "00100", "00100", "00100", "00100",
        ],
        'U' => [
            "10001", "10001", "10001", "10001", "10001", "10001", "01110",
        ],
        'V' => [
            "10001", "10001", "10001", "10001", "10001", "01010", "00100",
        ],
        'W' => [
            "10001", "10001", "10001", "10101", "10101", "11011", "10001",
        ],
        'X' => [
            "10001", "10001", "01010", "00100", "01010", "10001", "10001",
        ],
        'Y' => [
            "10001", "10001", "01010", "00100", "00100", "00100", "00100",
        ],
        'Z' => [
            "11111", "00001", "00010", "00100", "01000", "10000", "11111",
        ],
        '+' => [
            "00000", "00100", "00100", "11111", "00100", "00100", "00000",
        ],
        '-' => [
            "00000", "00000", "00000", "11111", "00000", "00000", "00000",
        ],
        '*' => [
            "00000", "10101", "01110", "11111", "01110", "10101", "00000",
        ],
        '/' => [
            "00001", "00010", "00010", "00100", "01000", "01000", "10000",
        ],
        '=' => [
            "00000", "00000", "11111", "00000", "11111", "00000", "00000",
        ],
        '?' => [
            "01110", "10001", "00001", "00010", "00100", "00000", "00100",
        ],
        _ => return None,
    };
    Some(rows)
}
