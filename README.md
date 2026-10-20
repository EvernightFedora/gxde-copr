# GXDE Copr
Welcome. This repository stores GXDE Fedora packaging.

GXDE on COPR is maintained by [@CharOfString](https://github.com/CharOfString).

## License
All material in this repository EXCEPT GIT PATCH FILES (`.patch` files) are licensed under [MIT](./LICENSE).

All git patch files are licensed under the same license of their corresponding repositor(ies).

## Fedora 44/45 包拆分

COPR 项目按 AUR 的包边界维护：`gxde-dtk5`、`gxde-dtk2`、
`gxde-dtk6`、`gxde-dtk2-qt6`、`gxde-infra`、`gxde-core`、
`gxde-display-manager` 与 `gxde-flakewm` 分别提供基础依赖；
其余 25 个 AUR 应用以各自 RPM 名称放在
[gxde-extra](https://copr.fedorainfracloud.org/coprs/charofstring/gxde-extra/)。
`gxde-extra` 另含非 AUR 的 `gio-qt6`、`libimagevisualresult6`，
分别供 Clipboard/Log Viewer、Camera 构建。

`packages/gxde-extra/manifest.json` 列出来源和构建方式；
`upstream-lock.json` 固定最新正式 tag 对应的提交与源码 SHA256。
`python3 scripts/gxde-extra-sources.py update` 检查上游 tag，
`prepare --package 包名` 生成相应 SRPM 构建树。
`.github/workflows/gxde-extra.yml` 定期检查新 tag，在 Fedora 44/45
构建并提交 COPR，成功后才更新锁定文件。自动提交复用其他工作流的
GitHub Actions secret `COPR_CONFIG`（COPR API 配置全文）；
凭据不要提交到 Git。
所有构建树内源码改动记录在
[packages/gxde-extra/PATCHES.md](packages/gxde-extra/PATCHES.md)。
