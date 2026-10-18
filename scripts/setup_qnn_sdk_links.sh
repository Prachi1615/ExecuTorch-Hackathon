#!/bin/bash
# The VENTUNO Q image installs the QNN SDK system-wide (/usr/include/QNN,
# /usr/lib/libQnn*.so). ExecuTorch's export tools require QNN_SDK_ROOT and then
# look for $QNN_SDK_ROOT/lib/x86_64-linux-clang/libQnnHtp.so (an x86 layout).
# This builds a small fake SDK root of symlinks pointing at the real files.
# Nothing in /usr is modified. Run once.
set -e
mkdir -p "$HOME/qnn_sdk/lib"
ln -sfn /usr/lib "$HOME/qnn_sdk/lib/x86_64-linux-clang"
ln -sfn /usr/include "$HOME/qnn_sdk/include"
ls -l "$HOME/qnn_sdk/lib/x86_64-linux-clang/libQnnHtp.so"
echo "OK: export QNN_SDK_ROOT=\$HOME/qnn_sdk  (already in scripts/qnn_env.sh)"
