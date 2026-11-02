#pragma once
// 复刻 Java HashMap/HashSet 的迭代顺序（仅用于 JSON 输出字段顺序）
//
// Jackson 序列化 HashMap / HashSet 时使用 Map/Set 的迭代顺序，而 Java 8 的
// HashMap 是"桶数组 + 链"：迭代顺序 = 桶索引升序，同桶内保持插入顺序。
// 桶索引 = (h ^ (h >>> 16)) & (capacity - 1)，capacity 为 >= size/0.75 的 2 的幂。
#include <algorithm>
#include <cstdint>
#include <string>
#include <vector>

namespace cm::utils {

int javaStringHash(const std::string& s);

/** 计算 HashMap 桶号；capacity 默认 16 */
int javaBucketIndex(const std::string& key, int capacity = 16);

/** 给定键集合，返回按 Java HashMap 迭代顺序重排后的键（保持同桶插入顺序） */
std::vector<std::string> javaMapOrder(const std::vector<std::string>& keys);

/** 对应 HashSet 的迭代顺序（初始容量 16，扩容阈值 0.75） */
std::vector<std::string> javaSetOrder(const std::vector<std::string>& keys);

} // namespace cm::utils
