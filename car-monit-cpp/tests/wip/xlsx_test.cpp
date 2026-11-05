// xlsx 读取器单测：
//   1) 自产自消 —— 用本工程的 xlsx 写出器（store 打包）生成再读回，验列对齐/空单元格；
//   2) 真实文件 —— 读 Java 侧的模板 xlsx（deflate 打包，由 python 生成），
//      这条同时证明 zip + inflate + sharedStrings + 表头文本都是对的。
#include "cm/common/utils/Xlsx.hpp"

#include <cstdio>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>

#include "cm/common/utils/Excel.hpp"

extern int g_fails;
#define fails g_fails
#define CK(x)                                                              \
    do {                                                                   \
        if (!(x)) {                                                        \
            std::printf("FAIL %s:%d %s\n", __FILE__, __LINE__, #x);        \
            ++fails;                                                       \
        }                                                                  \
    } while (0)
#define CK_EQ(a, b)                                                            \
    do {                                                                       \
        auto _va = (a);                                                        \
        auto _vb = (b);                                                        \
        if (!(_va == _vb)) {                                                   \
            std::printf("FAIL %s:%d  %s != %s\n", __FILE__, __LINE__, #a, #b); \
            ++fails;                                                           \
        }                                                                      \
    } while (0)

using cm::utils::Xlsx;
using cm::utils::ZipEntry;
using cm::utils::readZip;

static std::string slurp(const std::string& path, bool& ok) {
    std::ifstream f(path, std::ios::binary);
    if (!f) { ok = false; return ""; }
    std::ostringstream o;
    o << f.rdbuf();
    ok = true;
    return o.str();
}

static void testRoundTripThroughOurWriter() {
    std::vector<cm::common::utils::ExcelColumn> cols = {
        {"车牌号", "carNo", false, 16}, {"轴数", "carNum", true, 16}, {"备注", "remark", false, 16}};
    cm::Json rows = cm::Json::array();
    rows.push_back({{"carNo", "赣O6202警"}, {"carNum", 2}, {"remark", ""}});
    rows.push_back({{"carNo", "A1"}, {"carNum", 10}, {"remark", "x"}});
    const std::string bytes = cm::common::utils::Excel::exportXlsx(cols, rows, "Sheet1");
    CK(!bytes.empty());

    Xlsx x;
    std::string err;
    CK(Xlsx::load(bytes, false, x, &err));
    if (x.rows().empty()) { std::printf("  load err: %s\n", err.c_str()); }
    CK_EQ(x.rows().size(), std::vector<std::vector<std::string>>::size_type(3));
    if (x.rows().size() == 3) {
        CK_EQ(x.rows()[0][0], std::string("车牌号"));
        CK_EQ(x.rows()[0][2], std::string("备注"));
        CK_EQ(x.rows()[1][0], std::string("赣O6202警"));
        // 数字单元格：DecimalFormat("#.##") 会去掉尾随 0（10 不写成 10.0）
        CK_EQ(x.rows()[1][1], std::string("2"));
        CK_EQ(x.rows()[2][1], std::string("10"));
        CK_EQ(x.rows()[1][2], std::string(""));   // 空串备注读回来还是空
    }
}

static void testRealDeflatedTemplate() {
    bool ok = false;
    // Java 侧模板：python 生成的 xlsx，成员是 deflate 压缩的 ⇒ 这条走 inflate 分支
    std::string bytes = slurp("../../ruoyi-admin/src/main/resources/templates/export/carSuspicious.xlsx", ok);
    if (!ok) bytes = slurp("../ruoyi-admin/src/main/resources/templates/export/carSuspicious.xlsx", ok);
    if (!ok) {
        std::printf("SKIP  找不到 carSuspicious.xlsx（模板对拍需要 Java 侧资源）\n");
        return;
    }
    std::vector<ZipEntry> entries;
    std::string err;
    CK(readZip(bytes, entries, &err));
    bool hasWorkbook = false;
    for (const auto& e : entries) {
        if (e.name == "xl/workbook.xml") hasWorkbook = true;
        if (e.name.rfind("xl/worksheets/", 0) == 0) CK(e.method == 8);   // 确实是 deflate
    }
    CK(hasWorkbook);

    Xlsx x;
    CK(Xlsx::load(bytes, false, x, &err));
    if (x.rows().size() < 2) { std::printf("  load err: %s\n", err.c_str()); }
    CK_EQ(x.rows().size(), std::vector<std::vector<std::string>>::size_type(2));
    if (x.rows().size() >= 2) {
        // 表头取自 Java 模板第一行；第二行是 easypoi 的 {{$fe:entitylist ...}} 标记
        CK_EQ(x.rows()[0][0], std::string("车牌颜色"));
        CK_EQ(x.rows()[0][1], std::string("车牌号"));
        CK_EQ(x.rows()[0][13], std::string("录入时间"));
        CK(x.rows()[1][0].find("{{$fe:entitylist") != std::string::npos);
        CK(x.rows()[1][0].find("t.plateColor") != std::string::npos);
    }
}

static void testZipRejectsGarbage() {
    std::vector<ZipEntry> entries;
    std::string err;
    CK(!readZip("not a zip at all", entries, &err));
    CK(!err.empty());
    CK(!readZip(std::string(300, '\0'), entries, &err));
}

void run_xlsx_tests() {
    testRoundTripThroughOurWriter();
    testRealDeflatedTemplate();
    testZipRejectsGarbage();
}
