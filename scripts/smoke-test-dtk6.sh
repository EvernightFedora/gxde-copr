#!/usr/bin/env bash
set -euo pipefail
testdir=$(mktemp -d)
trap 'rm -rf "$testdir"' EXIT
for module in dtk6log dtk6core dtk6gui dtk6widget; do
    test -d "$(pkg-config --variable=libdir "$module")"
    test -d "$(pkg-config --variable=includedir "$module")"
done
cat > "$testdir/CMakeLists.txt" <<'EOF'
cmake_minimum_required(VERSION 3.25)
project(dtk6_consumer LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
find_package(Dtk6 REQUIRED COMPONENTS Core Gui Widget)
add_executable(consumer main.cpp)
target_link_libraries(consumer PRIVATE Dtk6::Widget Dtk6::Gui Dtk6::Core)
EOF
cat > "$testdir/main.cpp" <<'EOF'
#include <DApplication>
#include <DPushButton>
int main(int argc, char **argv) {
    Dtk::Widget::DApplication app(argc, argv);
    Dtk::Widget::DPushButton button("GXDE Fedora smoke test");
    return button.text().isEmpty();
}
EOF
cmake -S "$testdir" -B "$testdir/build"
cmake --build "$testdir/build"
QT_QPA_PLATFORM=offscreen "$testdir/build/consumer"
