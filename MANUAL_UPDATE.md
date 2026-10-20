# 手动更新 COPR：xdg-desktop-portal-gxde 1.2.5

本次更新日期：2026-10-20。目标项目是 `charofstring/gxde-infra`；`xdg-desktop-portal-gxde` 是该 RPM 的第 14 号源码组件，当前没有独立的 COPR 项目。全过程手动执行，**不运行 `scripts/infra-sources.py update`，不启用或触发 GitHub workflow**。`update` 会同时探测并可能更新其余 15 个组件，不适合这次单组件更新。

## 1. 确认工作区和现有锁

在仓库根目录执行：

```bash
git status -sb
python3 - <<'PY'
import json
from pathlib import Path
lock = json.loads(Path('packages/gxde-infra/upstream-lock.json').read_text())
print(lock['version'], lock['release'], lock['components']['xdg-desktop-portal-gxde'])
PY
```

本次起点是 `gxde-infra 2026.10.12-13`、portal `1.2.4`（`e8f10c150a80d64f412392c1494f492e658b6b0c`），工作区没有未提交改动。

## 2. 核对上游正式标签及差异

```bash
git ls-remote --tags https://github.com/GXDE-OS/xdg-desktop-portal-gxde.git
git clone --filter=blob:none --no-checkout \
  https://github.com/GXDE-OS/xdg-desktop-portal-gxde.git /tmp/gxde-portal-manual-review
git -C /tmp/gxde-portal-manual-review log --oneline 1.2.4..1.2.5
git -C /tmp/gxde-portal-manual-review diff --stat 1.2.4 1.2.5
git -C /tmp/gxde-portal-manual-review diff 1.2.4 1.2.5 -- src/wayland/abstractpipewirestream.cpp
```

`1.2.5` 是注释标签；`git ls-remote` 的 `1.2.5^{}` 才是源码提交 **`c16a49325a5a1c36262990a560e3a5658b4cd33f`**。从 `1.2.4` 到该提交只有 `58d31d2 fix: Pipewire crashing` 和版本提交；实际代码改动在 `abstractpipewirestream.cpp`，为 PipeWire 缓冲区设置读写及 MemFd 可映射标志。构建文件未变。上游标签自带的 `patch_dmabuf_header.py` 仍在源码内。

## 3. 下载固定提交的源码并计算 SHA256

```bash
curl -fsSL \
  https://codeload.github.com/GXDE-OS/xdg-desktop-portal-gxde/tar.gz/c16a49325a5a1c36262990a560e3a5658b4cd33f \
  -o build/source-cache/xdg-desktop-portal-gxde-c16a49325a5a1c36262990a560e3a5658b4cd33f.tar.gz
sha256sum build/source-cache/xdg-desktop-portal-gxde-c16a49325a5a1c36262990a560e3a5658b4cd33f.tar.gz
tar -tf build/source-cache/xdg-desktop-portal-gxde-c16a49325a5a1c36262990a560e3a5658b4cd33f.tar.gz | head
```

本次 SHA256 是 **`b0adce244a15c3e79f5024156dd8714692b1daaa0f34ffa7156482b32974bb5e`**；归档顶层目录与上述提交一致。

## 4. 只修改 portal 锁，并登记补丁情况

在 `packages/gxde-infra/upstream-lock.json` 中，将 `release` 从 `13` 加到 `14`，只把 `components.xdg-desktop-portal-gxde` 改为：

```json
{
  "tag": "1.2.5",
  "commit": "c16a49325a5a1c36262990a560e3a5658b4cd33f",
  "url": "https://codeload.github.com/GXDE-OS/xdg-desktop-portal-gxde/tar.gz/c16a49325a5a1c36262990a560e3a5658b4cd33f",
  "sha256": "b0adce244a15c3e79f5024156dd8714692b1daaa0f34ffa7156482b32974bb5e"
}
```

`version` 仍是由 `gxde-desktop-base` 决定的 `2026.10.12`。其他 15 个组件不变。此次 **不新增 portal 源码 patch**；`packages/gxde-infra/PATCHES.md` 已记录该结论。现有 `0001-network-utils-lrelease-path.patch` 继续原样用于 `gxde-network-utils-qt6`。

## 5. 本地准备、测试和构造 SRPM

```bash
python3 scripts/infra-sources.py prepare --output build/infra-rpmbuild
python3 -m unittest discover -s tests -q
git diff --check
rpmbuild -bs \
  --define '_topdir /home/char/Desktop/gxde-copr/build/infra-rpmbuild' \
  build/infra-rpmbuild/SPECS/gxde-infra.spec
rpmbuild -bp --nodeps --define '_tmppath /tmp' \
  --define '_topdir /home/char/Desktop/gxde-copr/build/infra-rpmbuild' \
  build/infra-rpmbuild/SPECS/gxde-infra.spec
```

本次结果：75 个测试通过；SRPM 为 `build/infra-rpmbuild/SRPMS/gxde-infra-2026.10.12-14.src.rpm`；`%prep` 校验并解包全部 16 份源码成功，现有 network-utils patch 无冲突。`_tmppath /tmp` 用于本机 `/var/tmp` 不可写的构建沙箱。

## 6. 手动提交 COPR 并核验四个目标

使用本机已配置的 `~/.config/copr`，不要把凭据写入仓库或聊天。执行：

```bash
copr-cli build --nowait charofstring/gxde-infra \
  build/infra-rpmbuild/SRPMS/gxde-infra-2026.10.12-14.src.rpm
copr-cli watch-build 11178695
copr-cli monitor charofstring/gxde-infra
```

本次构建编号：**[11178695](https://copr.fedorainfracloud.org/coprs/charofstring/gxde-infra/build/11178695/)**。提交目标是 Fedora 44/45 的 `x86_64` 和 `aarch64`。四个目标均为 `succeeded`：`fedora-44-x86_64`、`fedora-44-aarch64`、`fedora-45-x86_64`、`fedora-45-aarch64`。逐一读取各自的 `builder-live.log.gz` 后，确认日志包含 `xdg-desktop-portal-gxde` 文件安装和 `Finish: rpmbuild gxde-infra-2026.10.12-14...src.rpm`。任何未来的失败应先读对应日志、修复、提高 Release 并重新提交，不可把失败构建记为完成。

## 7. 发布仓库记录

构建通过后再次执行 `git diff --check` 和 `git status -sb`，确认只包含本次锁、补丁登记和本文件，再提交并推送：

```bash
git add packages/gxde-infra/upstream-lock.json packages/gxde-infra/PATCHES.md MANUAL_UPDATE.md
git commit -m "build: update xdg-desktop-portal-gxde to 1.2.5 in infra"
git push origin main
```

该步骤只保存人工审核过的构建输入和记录，不依赖 GitHub Actions。客户端若暂时看不到新 RPM，使用 `sudo dnf upgrade --refresh gxde-infra` 更新 COPR 元数据；已运行的 portal 服务需要重启后才会加载新二进制。
