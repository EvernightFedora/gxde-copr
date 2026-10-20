# gxde-extra 源码修改登记

当前没有独立的 `.patch` 文件，也不使用 tag 之后的 Git 提交。

## 构建树内修改

`build.sh` 在 RPM `%build` 中仅修改解包后的构建树，不回写上游仓库：

- 对 `upstream/**/*.sh` 内硬编码的 `/usr/lib/qt6/bin/`、
  `/usr/lib/x86_64-linux-gnu/qt6/bin/` 和 `/usr/bin/deepin-desktop-ts-convert`
  路径进行字符串替换，改为当前构建目录的 `toolbin/`。Fedora 的 Qt6 工具以
  `lrelease-qt6` 等名称安装，不提供这些 Arch/Debian 路径；
  `deepin-desktop-ts-convert` 则从 `gxde-infra` 锁定的
  `deepin-gettext-tools` 正式 tag 中提取，作为 SRPM Source105 携带。
  同源的 `deepin-policy-ts-convert` 作为 Source104 携带。
  当上游改用可配置的工具路径或 Fedora 提供相同路径时，可移除此替换。

其余 Fedora 路径、依赖和构建选项适配在 spec 与 `build.sh` 中实现；
如后续必须增添其他源码修改，需在这里记下涉及的包、tag、修改原因与移除条件，
并向用户报告。
