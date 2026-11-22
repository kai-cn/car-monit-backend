#!/usr/bin/env bash
# @description 验证重建 jar 中的 GeometryMapper.xml 是否仍含 geometry_copy1 遗留表名。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:36:07
# @usage bash /mnt/d/work/IdeaProjects/car-monit-backend-new/runtime-logs/verify-fixed-jar.sh
# @dependencies unzip、本机 jar。
DST=/home/dev/local-package/backend-master
SRC=/mnt/d/work/IdeaProjects/car-monit-backend-new
echo "SRC_XML"
grep -n 'geometry_copy1\|FROM geometry group' "$SRC/ruoyi-system/src/main/resources/mapper/base/GeometryMapper.xml" || true
echo "DST_XML"
grep -n 'geometry_copy1\|FROM geometry group' "$DST/ruoyi-system/src/main/resources/mapper/base/GeometryMapper.xml" || true
echo "DST_CLASSES_XML"
grep -n 'geometry_copy1\|FROM geometry group' "$DST/ruoyi-system/target/classes/mapper/base/GeometryMapper.xml" 2>/dev/null || true
echo "JAR_TIME"
stat -c '%y %s' "$DST/ruoyi-admin/target/ruoyi-admin.jar"
echo "JAR_XML"
unzip -p "$DST/ruoyi-admin/target/ruoyi-admin.jar" BOOT-INF/classes/mapper/base/GeometryMapper.xml 2>/dev/null | grep -n 'geometry_copy1\|FROM geometry group' || true
