#!/usr/bin/env bash
# setup.sh - 首次使用依赖检测与安装
# Usage: bash scripts/setup.sh

set -e

echo "🔍 检测依赖..."

MISSING=0

if ! python3 -c "import requests" 2>/dev/null; then
  echo "📦 安装 requests..."
  pip install -q requests
  MISSING=1
fi

if [ "$MISSING" -eq 0 ]; then
  echo "✅ 所有依赖已就绪"
else
  echo "✅ 依赖安装完成"
fi

# 最终验证
python3 -c "import requests; print('验证通过: requests')"
echo "🎉 setup 完成，可以正常使用"
