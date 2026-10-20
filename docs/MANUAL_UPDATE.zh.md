# 手动更新 COPR
> **注意**: 本文档以手动更新`xdg-desktop-portal-gxde`为例子。

## 第一步：确认上游标签并拉取
手动确认上游的仓库信息，例如本次我们更新的信息是：
- **目标TAG**：`1.2.5`
- **目标提交ID**：`c16a49325a5a1c36262990a560e3a5658b4cd33f`

## 第二步：取得仓库SHA256
我们还需要自行计算SHA256：
```bash
# 在本仓库根目录进行，如果没有build/source-cache/路径则需要手动创建
curl -fsSL \
  https://codeload.github.com/GXDE-OS/xdg-desktop-portal-gxde/tar.gz/c16a49325a5a1c36262990a560e3a5658b4cd33f \
  -o build/source-cache/xdg-desktop-portal-gxde-c16a49325a5a1c36262990a560e3a5658b4cd33f.tar.gz
sha256sum build/source-cache/xdg-desktop-portal-gxde-c16a49325a5a1c36262990a560e3a5658b4cd33f.tar.gz
tar -tf build/source-cache/xdg-desktop-portal-gxde-c16a49325a5a1c36262990a560e3a5658b4cd33f.tar.gz | head
```

解得目标值为`b0adce244a15c3e79f5024156dd8714692b1daaa0f34ffa7156482b32974bb5e`。

## 第三步：修改锁文件
在`packages/gxde-infra/upstream-lock.json`中，将`release`字段值自增1，把`components.xdg-desktop-portal-gxde`改为：
```json
{
  "tag": "1.2.5",
  "commit": "c16a49325a5a1c36262990a560e3a5658b4cd33f",
  "url": "https://codeload.github.com/GXDE-OS/xdg-desktop-portal-gxde/tar.gz/c16a49325a5a1c36262990a560e3a5658b4cd33f",
  "sha256": "b0adce244a15c3e79f5024156dd8714692b1daaa0f34ffa7156482b32974bb5e"
}
```

注意`gxde-infra`的`version`字段由`gxde-desktop-base`控制，截止写这份文档的时候值应该锁定`2026.10.12`，不要乱动。

有补丁的话，需要记录在`PATCHES.md`上。

## 第四步：本地编译验证
在一台Fedora设备上执行：
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

## 第五步：配置COPR并写入
确保`~/.config/copr`已经配置，若未配置则需要根据[COPR API页面](https://copr.fedorainfracloud.org/api)的指导配置此文件。不要泄露您的Token。

本机COPR环境确保OK后，执行以下指令：
```bash
copr-cli build --nowait charofstring/gxde-infra \
  build/infra-rpmbuild/SRPMS/gxde-infra-2026.10.12-14.src.rpm

# 上述操作应该会返回一个构建ID，这里以11178695为例子 你就可以用copr-cli监控构建状态了
copr-cli watch-build 11178695
copr-cli monitor charofstring/gxde-infra
```

# 第六步：更新本仓库
上述构建成功后便可以将本仓库的变更推送至远端，注意提交不要包含任何构建产物。
