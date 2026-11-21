// 轨迹几何那批纯函数的单测。
//
// 分层原则与 INFLATE/SigV4 一样：**能被独立实现校验的**（GpsUtil、桩号归一化、
// setScale+intValue、腾讯签名串）用参照值钉死；只能对着 Java 读的（回退链、分组规则）
// 交给 scripts/verify_trail_geo.py 在真实库上跑。
#include "cm/base/service/TrailGeometry.hpp"
#include "cm/base/util/GpsUtil.hpp"

#include <cmath>
#include <cstdio>
#include <string>

using cm::base::GpsUtil;
using cm::base::TrailGeometry;

extern int g_fails;
#define fails g_fails
#define CK(x)                                                       \
    do {                                                            \
        if (!(x)) {                                                 \
            std::printf("FAIL %s:%d %s\n", __FILE__, __LINE__, #x); \
            ++fails;                                                \
        }                                                           \
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
#define CK_NEAR(a, b, eps)                          \
    do {                                            \
        if (std::fabs((a) - (b)) > (eps)) {         \
            std::printf("FAIL %s:%d  %s !~ %s\n", __FILE__, __LINE__, #a, #b); \
            ++fails;                                \
        }                                           \
    } while (0)

// 由 scripts/gps_ref.py（Python 独立实现的同一套公式）产出，不是本工程自己的输出。
// 每行 {原始 lat, 原始 lon, gcj lat, gcj lon, gcj->wgs84 反算 lat, 反算 lon}
static const double kGpsRef[][6] = {
    {29.262412097999999, 117.758344803, 29.259688768279801, 117.76362747329951,
     29.262416127086869, 117.75834909936671},
    {39.983454999999999, 116.326612, 39.984766740945382, 116.33275220774442,
     39.983443172725494, 116.32659773002877},
    {22.543099999999999, 114.0579, 22.540382814222461, 114.06301399856547,
     22.543091702131264, 114.05789476861025},
    {0, 0, 0, 0, 0, 0},
    {48, 10, 48, 10, 48, 10},
    {26.701453255000001, 116.038089826, 26.698158275948849, 116.04304919502017,
     26.701441556143724, 116.03807904577511},
};

/** 坐标系转换：钉死"返回 [lat, lon]"这个最容易抄反的约定 */
static void testGpsUtil() {
    for (const auto& r : kGpsRef) {
        const auto gcj = GpsUtil::gps84ToGcj02(r[0], r[1]);
        CK_NEAR(gcj.first, r[2], 1e-9);
        CK_NEAR(gcj.second, r[3], 1e-9);
        const auto back = GpsUtil::gcj02ToGps84(gcj.first, gcj.second);
        // 反算是"两次减法"的近似，绝对值不到 1e-6 才算对（Java 也到这个精度）
        CK_NEAR(back.first, r[4], 1e-9);
        CK_NEAR(back.second, r[5], 1e-9);
    }
    // outOfChina 短路：范围外原样返回，不做任何偏移
    CK_NEAR(GpsUtil::gps84ToGcj02(48.0, 10.0).first, 48.0, 0.0);
    CK(GpsUtil::outOfChina(29.0, 71.9) == true);
    CK(GpsUtil::outOfChina(29.0, 137.9) == true);
    CK(GpsUtil::outOfChina(56.0, 100.0) == true);
    CK(GpsUtil::outOfChina(29.0, 117.0) == false);
}

/** pileno 归一化：+→. ，再按 ZK / YK / K 的顺序整体删除 */
static void testNormalizePileno() {
    std::string out;
    CK(TrailGeometry::normalizePileno("K123+456", out));
    CK_EQ(out, std::string("123.456"));
    CK(TrailGeometry::normalizePileno("ZK10+1", out));
    CK_EQ(out, std::string("10.1"));
    CK(TrailGeometry::normalizePileno("YK455+460", out));
    CK_EQ(out, std::string("455.460"));
    // replace 是全量替换：中间的 K 也会被删掉（Java 用的就是 String.replace）
    CK(TrailGeometry::normalizePileno("K1K2+3", out));
    CK_EQ(out, std::string("12.3"));
    // 非法文本 ⇒ false，对应 new BigDecimal(...) 抛 NumberFormatException
    CK(!TrailGeometry::normalizePileno("abc", out));
    CK(!TrailGeometry::normalizePileno("", out));
    // BigDecimal 的文法里 ".5" 是合法的（Significand 允许 '.' FractionPart），
    // 一开始我把它当成非法 —— 记在这里防止再改回去
    CK(TrailGeometry::normalizePileno(".5", out));
    CK_EQ(out, std::string(".5"));
    CK(!TrailGeometry::normalizePileno("1.2.3", out));
    CK(!TrailGeometry::normalizePileno("+", out));
    CK(TrailGeometry::normalizePileno("439.8030090332031", out));
    CK_EQ(out, std::string("439.8030090332031"));
}

/** BigDecimal.setScale(4, HALF_UP).intValue()：先舍入再向零截断 */
static void testScale4ThenTrunc() {
    CK(TrailGeometry::scale4ThenTrunc("123.456") == 123);
    CK(TrailGeometry::scale4ThenTrunc("123.45678") == 123);
    // 舍入进位改变整数部分的情形
    CK(TrailGeometry::scale4ThenTrunc("123.99999") == 124);
    CK(TrailGeometry::scale4ThenTrunc("0.5") == 0);
    CK(TrailGeometry::scale4ThenTrunc("1119.500") == 1119);
    // 负数：HALF_UP 按大小舍、intValue 向零截断
    CK(TrailGeometry::scale4ThenTrunc("-123.5") == -123);
    CK(TrailGeometry::scale4ThenTrunc("-123.99999") == -124);
    CK(TrailGeometry::scale4ThenTrunc("1119") == 1119);
}

/** 腾讯 sig() 的原文串。顺序是 Arrays.sort 后的 from,key,to,waypoints；
 *  heading 传空串 ⇒ 既不进 map，也就不会有 "&heading="，但分隔符数量照旧。 */
static void testTxSignatureSource() {
    // Arrays.sort 后是 from,key,to,waypoints；分隔符按"非最后一项"加，与值是否为空无关
    const std::string s = TrailGeometry::txSignatureSource("116.1,29.1", "116.2,29.2", "", "");
    CK_EQ(s, std::string("/ws/direction/v1/driving/?from=116.1,29.1&"
                         "key=UVUBZ-6AY3V-FEGP2-UJSJP-SBJAJ-UTBT6&to=116.2,29.2"));
    const std::string w = TrailGeometry::txSignatureSource("1.0", "2.0", "", "3.0,4.0;5.0,6.0");
    CK_EQ(w, std::string("/ws/direction/v1/driving/?from=1.0&"
                         "key=UVUBZ-6AY3V-FEGP2-UJSJP-SBJAJ-UTBT6&to=2.0"
                         "&waypoints=3.0,4.0;5.0,6.0"));
    // ⚠️ 值空白时"名=值"整段不写，但分隔符照样写 ⇒ 留下一个光秃秃的 &。
    //    from/to 是无条件 put 进 map 的（heading/waypoints 才有 isNotBlank 守卫），
    //    所以这条只在 from 为空时可见 —— 正常调用不会走到，照抄行为本身。
    CK_EQ(TrailGeometry::txSignatureSource("", "2.0", "", ""),
          std::string("/ws/direction/v1/driving/?&"
                      "key=UVUBZ-6AY3V-FEGP2-UJSJP-SBJAJ-UTBT6&to=2.0"));
    // 值两侧空白会被 trim（Java 用的是 param.get(str).trim()）
    const std::string t = TrailGeometry::txSignatureSource(" 1.0 ", "2.0", "", "");
    CK(t.find("?from=1.0&") != std::string::npos);
    // heading 非空才进 map（进 map 后排序位置在 from 之后）
    CK_EQ(TrailGeometry::txSignatureSource("1.0", "2.0", "90", ""),
          std::string("/ws/direction/v1/driving/?from=1.0&heading=90&"
                      "key=UVUBZ-6AY3V-FEGP2-UJSJP-SBJAJ-UTBT6&to=2.0"));
}

void run_trail_geo_tests() {
    testGpsUtil();
    testNormalizePileno();
    testScale4ThenTrunc();
    testTxSignatureSource();
}
