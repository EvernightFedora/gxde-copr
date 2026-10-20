# GXDE Display Manager 源码补丁登记

当前新增源码补丁：**0 项**。

## Fedora 适配（非源码补丁）

以下调整均通过构建参数、独立 PAM 文件或 spec 安装规则实现，不修改上游源码：

- **PAM 配置**：上游 `services/gxdm.pam` 和 `gxdm-autologin.pam` 使用 Arch 的 `system-login`；Fedora 的 PAM 栈基于 `password-auth`/`postlogin`/`pam_selinux`。构建时 `-DINSTALL_PAM_CONFIGURATION=OFF` 禁用上游 PAM 安装，spec 提供 4 个 Fedora 专用 PAM 文件（`gxdm.pam`、`gxdm-autologin.pam`、`gxdm-greeter.pam`、`gxdm-rescue.pam`），基于 Fedora sddm 包的 PAM 文件适配。`gxdm-greeter.pam` 与上游模板生成的文件一致，已是通用的。
- **Rust 依赖 vendor**：`gxdm-emergency-mode` 上游未 vendor 依赖（无 `vendor/` 目录），AUR 用 `cargo fetch` 预下载。COPR 构建无网络，因此在 source prepare 阶段（本机有网络和 cargo）运行 `cargo vendor --locked --versioned-dirs`，生成 `vendor/` 目录和 `.cargo/config.toml`，打包为 `Source2`。构建时 `cargo build --offline --frozen` 使用 vendored crates。
- **`/usr/sbin`→`/usr/bin`**：`gxdm-emergency-mode` 的 systemd service 文件引用 `/usr/sbin/gxdm-emergency-mode`；Debian 布局 `/usr/sbin` 在 Fedora 是 `/usr/bin` 的符号链接。build.sh 用 `sed` 修复 service 文件路径，与 AUR 一致。spec 的 `%install` 段也处理二进制文件位置。
- **MavenPro 字体许可**：AUR 从 googlefonts/mavenproFont 固定 commit 下载 `OFL.txt`。sources 脚本以相同 commit 和 SHA256 下载，作为 `Source3` 打包到 license 目录。不打包字体数据本身。
- **SELinux 子包**：Fedora 的 targeted 策略对 display manager 有额外要求。spec 声明 `gxde-display-manager-selinux` 子包（当前为占位，无独立策略模块；后续可能需要为 gxdm 编写 selinux 策略模块）。运行包通过 `Requires` 引用，确保安装时提示。

若未来必须回补源码修复，先列出组件/tag、补丁内容、原因和移除条件，并向用户报告。
