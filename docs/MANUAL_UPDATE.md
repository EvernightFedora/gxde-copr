# Updating COPR Manually
> **Note**: This documentation is using updating `xdg-desktop-portal-gxde` as an example.

## Step 1: Pull the Upstream Repository
Lock in your tag & commit preferred:
- **Target TAG**: `1.2.5`
- **Target commit ID**: `c16a49325a5a1c36262990a560e3a5658b4cd33f`

## Step 2: Calculate SHA256 of the Repository
This step will be needed done manually:
```bash
# Exectue these command at project root of this repo.
# You'll need to create build/source-cache/ if they aren't there yet.
curl -fsSL \
  https://codeload.github.com/GXDE-OS/xdg-desktop-portal-gxde/tar.gz/c16a49325a5a1c36262990a560e3a5658b4cd33f \
  -o build/source-cache/xdg-desktop-portal-gxde-c16a49325a5a1c36262990a560e3a5658b4cd33f.tar.gz
sha256sum build/source-cache/xdg-desktop-portal-gxde-c16a49325a5a1c36262990a560e3a5658b4cd33f.tar.gz
tar -tf build/source-cache/xdg-desktop-portal-gxde-c16a49325a5a1c36262990a560e3a5658b4cd33f.tar.gz | head
```

The target's SHA256 value this time would be `b0adce244a15c3e79f5024156dd8714692b1daaa0f34ffa7156482b32974bb5e`.

## Step 3: Modify the Lock File.
In `packages/gxde-infra/upstream-lock.json`, increase 1 to the `release` field. Change `components.xdg-desktop-portal-gxde` into: 
```json
{
  "tag": "1.2.5",
  "commit": "c16a49325a5a1c36262990a560e3a5658b4cd33f",
  "url": "https://codeload.github.com/GXDE-OS/xdg-desktop-portal-gxde/tar.gz/c16a49325a5a1c36262990a560e3a5658b4cd33f",
  "sha256": "b0adce244a15c3e79f5024156dd8714692b1daaa0f34ffa7156482b32974bb5e"
}
```

Note that the `version` field is provided & controlled by `gxde-infra`'s `gxde-desktop-base` package and YOU ARE NOT SUPPOSED TO MODIFY THAT unless you're updating `gxde-desktop-base`. By Oct 20th, 2026, the value should be keep as `2026.10.12`.

Write down your patch note in `PATCHES.md`, if any.

## Step 4: Local Build
Run these command on a Fedora device:
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

## Step 5: Configure your COPR and Write to COPR
Make sure that `~/.config/copr`is configured. If not, go to [COPR API page](https://copr.fedorainfracloud.org/api) and they have the instruction you need. Remember to NOT leak your API key.

If your COPR is CLI configured then run:
```bash
copr-cli build --nowait charofstring/gxde-infra \
  build/infra-rpmbuild/SRPMS/gxde-infra-2026.10.12-14.src.rpm

# A build ID shall be returned, we're using 11178695 as an example here.
# Then, you may use copr-cli to monitor your build state.
copr-cli watch-build 11178695
copr-cli monitor charofstring/gxde-infra
```

# Step 6: Update This Repository
Once the build above is successful, you may push the changes in this repository to the remote; please ensure that your commits contains no artifacts.
