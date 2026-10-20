#!/usr/bin/env bash
set -euo pipefail
testdir=$(mktemp -d)
trap 'rm -rf "$testdir"' EXIT
pkg-config --exists dtk2widget dtk6core
cat > "$testdir/consumer.pro" <<'EOF'
QT += widgets dtk2widget
CONFIG += c++17 console
SOURCES += main.cpp
EOF
cat > "$testdir/main.cpp" <<'EOF'
#include <QApplication>
#include <DPushButton>
int main(int argc, char **argv) {
    QApplication app(argc, argv);
    Dtk::Widget::DPushButton button("GXDE DTK2 Qt6 smoke test");
    return button.text().isEmpty();
}
EOF
(cd "$testdir" && qmake6 consumer.pro && make)
QT_QPA_PLATFORM=offscreen "$testdir/consumer"
