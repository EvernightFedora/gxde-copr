# flakewm 源码补丁登记

当前新增源码补丁：**0 项**。

## 构建适配（非源码补丁）

以下调整均通过构建参数实现，不修改上游源码：

- **CMake 参数**：与 AUR 完全一致——`-DWLCOM_EXAMPLES=OFF`、`-DWLCOM_UKUI_THEME=ON`、`-DWLCOM_WLROOTS_RENDERERS=gles2,vulkan`。
- **安装路径**：`CMAKE_INSTALL_LIBDIR` 使用 Fedora 的 `%{_libdir}`（`lib64`），AUR 用 `lib`。

若未来必须回补源码修复，先列出组件/tag、补丁内容、原因和移除条件，并向用户报告。
