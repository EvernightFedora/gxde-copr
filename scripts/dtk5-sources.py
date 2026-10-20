#!/usr/bin/env python3
"""Resolve release tags and prepare a checksummed, offline-buildable RPM tree."""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "packages/gxde-dtk5"
CORE_MODULE = "dtk5core"
SPEC_NAME = "gxde-dtk5"
DEFAULT_OUTPUT = ROOT / "build/rpmbuild"
MODULES = ("dtk5common", "dtklog", "dtk5core", "dtk5gui", "dtk5widget",
           "dde-qt5platform-plugins", "dde-qt5integration")
TAG = re.compile(r"v?(\d+(?:\.\d+)*)(?:-?gxde(\d+)|-(\d+))?$")


def rpm_version(tag):
    match = TAG.fullmatch(tag)
    if not match:
        raise ValueError(f"Unsupported release tag: {tag}")
    return match[1] + (f".gxde{match[2]}" if match[2] else f".{match[3]}" if match[3] else "")


def tag_key(tag):
    match = TAG.fullmatch(tag)
    if not match:
        raise ValueError(f"Unsupported release tag: {tag}")
    numbers = tuple(map(int, match[1].split(".")))
    return numbers + (0,) * (8 - len(numbers)), int(match[2] or match[3] or 0)


def latest_tag(refs):
    tags = {}
    peeled = {}
    for line in refs.splitlines():
        sha, ref = line.split()
        name = ref.removeprefix("refs/tags/")
        if name.endswith("^{}"):
            peeled[name[:-3]] = sha
        elif TAG.fullmatch(name):
            tags[name] = sha
    if not tags:
        raise ValueError("No stable numeric release tags found; refusing a HEAD fallback")
    tag = max(tags, key=lambda t: (tag_key(t), t))
    return tag, peeled.get(tag, tags[tag])


def download(url, path, expected=None):
    if path.exists() and expected and hashlib.sha256(path.read_bytes()).hexdigest() == expected:
        return expected
    request = urllib.request.Request(url, headers={"User-Agent": "gxde-copr"})
    temporary = path.with_suffix(path.suffix + ".part")
    try:
        with urllib.request.urlopen(request, timeout=120) as response, temporary.open("wb") as out:
            shutil.copyfileobj(response, out)
        digest = hashlib.sha256(temporary.read_bytes()).hexdigest()
        if expected and digest != expected:
            raise ValueError(f"SHA256 mismatch: {url}")
        temporary.replace(path)
        return digest
    finally:
        temporary.unlink(missing_ok=True)


def resolve(old, cache):
    components = {}
    for name in MODULES:
        refs = subprocess.check_output(
            ["git", "ls-remote", "--tags", f"https://github.com/GXDE-OS/{name}.git"],
            text=True, timeout=120)
        tag, commit = latest_tag(refs)
        previous = old.get("components", {}).get(name)
        if previous and tag_key(tag) < tag_key(previous["tag"]):
            raise ValueError(f"{name}: upstream tag rollback requires manual review")
        if previous and previous["tag"] == tag and previous["commit"] != commit:
            raise ValueError(f"{name}: released tag moved; refusing automatic update")
        url = f"https://codeload.github.com/GXDE-OS/{name}/tar.gz/{commit}"
        component = {"tag": tag, "commit": commit, "url": url}
        component["sha256"] = download(url, cache / f"{name}-{commit}.tar.gz",
                                       previous["sha256"] if previous and previous["commit"] == commit else None)
        components[name] = component
        print(f"{name}: {tag} ({commit[:12]})")
    version = rpm_version(components[CORE_MODULE]["tag"])
    changed = components != old.get("components")
    release = old.get("release", 0) + int(changed) if version == old.get("version") else 1
    return {"version": version, "release": release, "components": components}


def prepare(lock, destination):
    for directory in ("SOURCES", "SPECS", "BUILD", "BUILDROOT", "RPMS", "SRPMS"):
        (destination / directory).mkdir(parents=True, exist_ok=True)
    definitions, sources, checks = [], [], []
    for index, name in enumerate(MODULES):
        component = lock["components"][name]
        commit = component["commit"]
        if not re.fullmatch(r"[0-9a-f]{40}", commit):
            raise ValueError(f"Invalid commit for {name}")
        filename = f"{name}-{commit}.tar.gz"
        cached = ROOT / "build/source-cache" / filename
        if cached.exists() and hashlib.sha256(cached.read_bytes()).hexdigest() == component["sha256"]:
            shutil.copyfile(cached, destination / "SOURCES" / filename)
        download(component["url"], destination / "SOURCES" / filename, component["sha256"])
        definitions.append(f"%global commit{index} {commit}")
        sources.append(f"Source{index}: {component['url']}#/{filename}")
        checks.append(f"{component['sha256']}  {filename}")
    common = lock["components"].get("dtk5common")
    common_version = TAG.fullmatch(common["tag"])[1] if common else ""
    template = (PACKAGE / f"{SPEC_NAME}.spec.in").read_text()
    replacements = {"@VERSION@": lock["version"], "@RELEASE@": str(lock["release"]),
                    "@COMMITS@": "\n".join(definitions), "@SOURCES@": "\n".join(sources),
                    "@COMMON_VERSION@": common_version}
    for key, value in replacements.items():
        template = template.replace(key, value)
    (destination / f"SPECS/{SPEC_NAME}.spec").write_text(template)
    (destination / "SOURCES/sources.sha256").write_text("\n".join(checks) + "\n")
    for name in ("build.sh", "split-files.py"):
        shutil.copyfile(PACKAGE / name, destination / "SOURCES" / name)
    for patch in PACKAGE.glob("*.patch"):
        shutil.copyfile(patch, destination / "SOURCES" / patch.name)
    shutil.copyfile(PACKAGE / "upstream-lock.json", destination / "SOURCES/upstream-lock.json")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("update", "prepare"))
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    path = PACKAGE / "upstream-lock.json"
    lock = json.loads(path.read_text()) if path.exists() else {}
    if args.command == "update":
        cache = ROOT / "build/source-cache"
        cache.mkdir(parents=True, exist_ok=True)
        updated = resolve(lock, cache)
        path.write_text(json.dumps(updated, indent=2) + "\n")
    else:
        prepare(lock, args.output.resolve())


if __name__ == "__main__":
    main()
