"""Install the two sibling skills (scivis, the shared style/colour/layout layer, ships inside sim-plot). Default is a dry run; never overwrite an existing skill."""
from __future__ import annotations
import argparse
from pathlib import Path
import shutil


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--target", choices=["omp", "codex", "claude"], default="omp")
    p.add_argument("--scope", choices=["user", "project"], default="user")
    p.add_argument("--root", type=Path, help="Required project root for project-scoped installation.")
    p.add_argument("--apply", action="store_true", help="Actually copy files after printing the destination.")
    a = p.parse_args()
    if a.scope == "project":
        if a.root is None:
            p.error("--scope project requires --root")
        roots = {"omp": ".omp/skills", "codex": ".agents/skills", "claude": ".claude/skills"}
        target = a.root.expanduser().resolve() / roots[a.target]
    else:
        roots = {"omp": ".omp/agent/skills", "codex": ".agents/skills", "claude": ".claude/skills"}
        target = Path.home() / roots[a.target]
    source = Path(__file__).resolve().parent / "skills"
    names = ["sim-plot", "sim-field"]
    for name in names:
        if not (source / name / "SKILL.md").is_file():
            raise FileNotFoundError(f"Incomplete kit: {name}")
        if (target / name).exists():
            raise FileExistsError(f"Existing installation left untouched: {target / name}. "
                                  "Back up/reconcile it explicitly before installing this version.")
    print(f"Destination: {target}")
    print("Skills: sim-plot (hosts the shared scivis layer), sim-field; both must remain siblings.")
    if not a.apply:
        print("Dry run only. Add --apply to copy. No environment changes are made; the calling rules live in each SKILL.md.")
        return
    target.mkdir(parents=True, exist_ok=True)
    for name in names:
        shutil.copytree(source / name, target / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "out"))
    print("Installed. Discover/reload skills in your agent. No dependencies or fonts were installed.")

if __name__ == "__main__":
    main()
