#!/usr/bin/env python3
"""
LEGACY-SCRIPT-ANNOTATION
文件：check_bcrypt.py
用途：只读检查/诊断。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：通常只读；若脚本内有明确写操作以其自身说明为准。
"""
import os
import bcrypt

h = b"$2a$10$9tckZpKOvuczFb8U1WPEX.ChznLKIw3Gj.QtfvjUbh7AnHm1mjl5."
pw = os.environ.pop("SECRET_VALUE", "").encode()
print("bcrypt match:", bcrypt.checkpw(pw, h))
