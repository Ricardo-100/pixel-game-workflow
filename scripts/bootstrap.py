"""Create a portable farming demo from this skill, without overwriting a project."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import shutil
import sys


def create_project(output: Path, name: str, godot: Path | None, addon: Path | None) -> dict:
    template = Path(__file__).resolve().parents[1] / "assets" / "farm-template"
    required = ["project.godot", "farm.gd", "farm.tscn", "assets/environment.png", "assets/farmer.png"]
    missing = [item for item in required if not (template / item).is_file()]
    if missing:
        raise ValueError("Incomplete template: " + ", ".join(missing))
    output = output.expanduser().resolve()
    skill_root = template.parents[1]
    if output == skill_root or skill_root in output.parents:
        raise ValueError("Output must be outside the installed skill directory")
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise ValueError("Destination must be absent or empty; refusing to overwrite: " + str(output))
    if not name.strip():
        raise ValueError("Project name cannot be empty")
    if godot is not None:
        godot = godot.expanduser().resolve()
        if not godot.is_file():
            raise ValueError("Godot executable does not exist: " + str(godot))
    if addon is not None:
        addon = addon.expanduser().resolve()
        for relative in ("plugin.cfg", "plugin.gd", "runtime/game_helper.gd"):
            if not (addon / relative).is_file():
                raise ValueError("Invalid Godot AI addon; missing: " + str(addon / relative))
        # Refuse copying a parent into its own newly-created descendant.
        if addon == output or addon in output.parents:
            raise ValueError("Addon source must not contain the output project")
    shutil.copytree(template, output, dirs_exist_ok=True)
    config_path = output / "project.godot"
    config = config_path.read_text(encoding="utf-8")
    config = config.replace('config/name="Moss & Mallow"', 'config/name=' + json.dumps(name, ensure_ascii=False), 1)
    if addon is not None:
        shutil.copytree(addon, output / "addons" / "godot_ai", ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"))
        config += '\n[autoload]\n_mcp_game_helper="*res://addons/godot_ai/runtime/game_helper.gd"\n\n[editor_plugins]\nenabled=PackedStringArray("res://addons/godot_ai/plugin.cfg")\n'
    config_path.write_text(config, encoding="utf-8")
    engine = str(godot) if godot else "godot"
    # A checked local executable or a literal PATH command; escape cmd batch expansion.
    engine = engine.replace("%", "%%")
    launcher = '@echo off\r\nsetlocal\r\nstart "Moss and Mallow" "' + engine + '" --path "%~dp0."\r\n'
    (output / "run-demo.cmd").write_bytes(launcher.encode("utf-8"))
    report = {"project": str(config_path), "godot": str(godot) if godot else "PATH:godot", "godot_ai_enabled": addon is not None, "status": "created_not_run"}
    (output / "reports").mkdir(exist_ok=True)
    (output / "reports" / "bootstrap.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--name", default="Moss & Mallow")
    parser.add_argument("--godot", type=Path)
    parser.add_argument("--godot-ai-addon", type=Path)
    args = parser.parse_args()
    try:
        result = create_project(args.output, args.name, args.godot, args.godot_ai_addon)
    except (ValueError, OSError) as exc:
        print("Bootstrap failed: " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
