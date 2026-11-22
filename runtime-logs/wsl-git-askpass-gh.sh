#!/usr/bin/env bash
# @description 为 WSL git HTTPS 推送提供本地缓存 token，避免账号选择弹框。
# @author AI Assistant
# @date 2026-11-23
# @usage GIT_ASKPASS=... git push
# @dependencies /home/dev/.gh_token_wsl，仅当前用户可读，token 不打印。
if [[ "$1" == *Username* ]]; then
  printf '%s\n' 'kai-cn'
elif [[ "$1" == *Password* ]]; then
  cat /home/dev/.gh_token_wsl
else
  printf '\n'
fi
