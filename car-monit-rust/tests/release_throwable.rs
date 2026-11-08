// release 冒烟：确认 release 构建保留本 crate 的调试信息，throwable 能输出应用栈帧。
// 单元测试里调用点一定落在 `car_monit_rust::logging::tests`，会被 `backtrace_text`
// 的前缀过滤器吃掉，断言恒真；集成测试 crate 的探针帧不受该过滤影响。
// 只在 `cargo test --release --test release_throwable` 下有意义。
#![cfg(not(debug_assertions))]

use std::error::Error;
use std::fmt;

#[derive(Debug)]
struct Boom;

impl fmt::Display for Boom {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "boom")
    }
}

impl Error for Boom {}

#[test]
fn throwable_has_app_frame_in_release() {
    let boom = Boom;
    // 通过 black_box 后的函数指针间接调用，阻止 LTO 把探针内联进测试闭包。
    let probe: fn(&(dyn Error + 'static), &'static str) -> String =
        std::hint::black_box(car_monit_rust::test_support::throwable_probe);
    let text = probe(&boom, "Boom");

    let frames: Vec<&str> = text
        .lines()
        .map(str::trim)
        .filter(|line| line.starts_with("at "))
        .collect();
    assert!(
        !frames.is_empty(),
        "release 构建缺少栈帧（符号被 strip？）: {text}"
    );

    let has_real_frame = frames.iter().any(|line| {
        let Some((file, number)) = line.rsplit_once(':') else {
            return false;
        };
        let number = number.trim_end_matches(')');
        !file.contains("<unknown>")
            && number.parse::<u32>().map(|value| value > 0).unwrap_or(false)
    });
    assert!(has_real_frame, "release 构建没有可用的文件行号帧: {text}");

    // 本 crate 的应用帧必须出现（探针在 car_monit_rust::test_support，不在 logging 前缀下）。
    assert!(
        text.contains("test_support::throwable_probe"),
        "release 构建缺少本 crate 的应用栈帧: {text}"
    );
}
