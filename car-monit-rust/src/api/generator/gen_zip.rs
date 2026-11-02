// 来源: GenTableServiceImpl.downloadCode（java.util.zip.ZipOutputStream）
// 职责: 代码生成 zip。条目名/顺序/内容对齐 Java；压缩方式用 STORE——
//       Java 走 DEFLATE，两端字节永远不可能一致，可比的是解压后的文件集合。

use chrono::{Datelike, Local, Timelike};

const LOCAL_SIG: u32 = 0x0403_4B50;
const CENTRAL_SIG: u32 = 0x0201_4B50;
const EOCD_SIG: u32 = 0x0605_4B50;
const VERSION: u16 = 20;
const FLAG_UTF8: u16 = 0x0800;
const METHOD_STORED: u16 = 0;

const fn crc_table() -> [u32; 256] {
    let mut table = [0u32; 256];
    let mut index = 0usize;
    while index < 256 {
        let mut crc = index as u32;
        let mut bit = 0;
        while bit < 8 {
            crc = if crc & 1 == 1 {
                (crc >> 1) ^ 0xEDB8_8320
            } else {
                crc >> 1
            };
            bit += 1;
        }
        table[index] = crc;
        index += 1;
    }
    table
}

static CRC_TABLE: [u32; 256] = crc_table();

fn crc32(data: &[u8]) -> u32 {
    let mut crc = 0xFFFF_FFFFu32;
    for byte in data {
        crc = (crc >> 8) ^ CRC_TABLE[((crc ^ *byte as u32) & 0xFF) as usize];
    }
    !crc
}

fn push_u16(out: &mut Vec<u8>, value: u16) {
    out.extend_from_slice(&value.to_le_bytes());
}

fn push_u32(out: &mut Vec<u8>, value: u32) {
    out.extend_from_slice(&value.to_le_bytes());
}

/// Java ZipEntry 用本地时间填充 DOS time/date。
fn dos_stamp() -> (u16, u16) {
    let now = Local::now();
    let time =
        ((now.hour() as u16) << 11) | ((now.minute() as u16) << 5) | (now.second() as u16 / 2);
    let year = now.year().max(1980) as u16;
    let date = ((year - 1980) << 9) | ((now.month() as u16) << 5) | now.day() as u16;
    (time, date)
}

/// 按给定顺序打包条目；同名条目由调用方先行去重（Java 会在 putNextEntry 抛 ZipException）。
pub fn build(entries: &[(String, Vec<u8>)]) -> Vec<u8> {
    let (time, date) = dos_stamp();
    let mut out: Vec<u8> = Vec::new();
    let mut central: Vec<u8> = Vec::new();
    let mut offset: u32 = 0;
    for (name, data) in entries {
        let name_bytes = name.as_bytes();
        let flag = if name.is_ascii() { 0 } else { FLAG_UTF8 };
        let size = data.len() as u32;

        push_u32(&mut out, LOCAL_SIG);
        push_u16(&mut out, VERSION);
        push_u16(&mut out, flag);
        push_u16(&mut out, METHOD_STORED);
        push_u16(&mut out, time);
        push_u16(&mut out, date);
        push_u32(&mut out, crc32(data));
        push_u32(&mut out, size);
        push_u32(&mut out, size);
        push_u16(&mut out, name_bytes.len() as u16);
        push_u16(&mut out, 0);
        out.extend_from_slice(name_bytes);
        out.extend_from_slice(data);

        push_u32(&mut central, CENTRAL_SIG);
        push_u16(&mut central, VERSION); // version made by（Java 对 DOS 条目写 20）
        push_u16(&mut central, VERSION); // version needed
        push_u16(&mut central, flag);
        push_u16(&mut central, METHOD_STORED);
        push_u16(&mut central, time);
        push_u16(&mut central, date);
        push_u32(&mut central, crc32(data));
        push_u32(&mut central, size);
        push_u32(&mut central, size);
        push_u16(&mut central, name_bytes.len() as u16);
        push_u16(&mut central, 0); // extra
        push_u16(&mut central, 0); // comment
        push_u16(&mut central, 0); // disk number
        push_u16(&mut central, 0); // internal attributes
        push_u32(&mut central, 0); // external attributes
        push_u32(&mut central, offset);
        central.extend_from_slice(name_bytes);

        offset += 30 + name_bytes.len() as u32 + size;
    }
    let central_start = out.len() as u32;
    let central_len = central.len() as u32;
    out.extend_from_slice(&central);

    push_u32(&mut out, EOCD_SIG);
    push_u16(&mut out, 0);
    push_u16(&mut out, 0);
    push_u16(&mut out, entries.len() as u16);
    push_u16(&mut out, entries.len() as u16);
    push_u32(&mut out, central_len);
    push_u32(&mut out, central_start);
    push_u16(&mut out, 0);
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn crc32_matches_known_vector() {
        assert_eq!(crc32(b"123456789"), 0xCBF4_3926);
        assert_eq!(crc32(b""), 0);
    }

    #[test]
    fn archive_round_trips_through_zip_crate() {
        let entries = vec![
            (
                "main/java/com/ruoyi/domain/Car.java".to_string(),
                b"class Car {}".to_vec(),
            ),
            (
                "vue/api/manager/car.js".to_string(),
                "export function list() {}".as_bytes().to_vec(),
            ),
        ];
        let bytes = build(&entries);
        let mut reader = zip::ZipArchive::new(std::io::Cursor::new(bytes)).unwrap();
        assert_eq!(reader.len(), 2);
        for (index, (name, data)) in entries.iter().enumerate() {
            let mut file = reader.by_index(index).unwrap();
            assert_eq!(&file.name(), name);
            let mut text = String::new();
            std::io::Read::read_to_string(&mut file, &mut text).unwrap();
            assert_eq!(text.as_bytes(), data.as_slice());
        }
    }

    #[test]
    fn empty_archive_is_valid() {
        let bytes = build(&[]);
        assert_eq!(bytes.len(), 22);
        assert!(zip::ZipArchive::new(std::io::Cursor::new(bytes)).is_ok());
    }
}
