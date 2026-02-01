#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Optional


@dataclass
class ItemResult:
    path: Path
    created: bool
    kind: str   # "dir" | "file"
    action: str # "created" | "exists" | "skipped" | "overwritten" | "dry-run"


def strip_comment(line: str) -> str:
    if "#" in line:
        line = line.split("#", 1)[0]
    return line.rstrip("\n").rstrip()


def parse_lines(spec_text: str, indent_size: int = 2) -> List[Tuple[int, str]]:
    """
    Devuelve lista de (nivel, contenido).
    Nivel = espacios_indentation // indent_size (por defecto 2).
    """
    items: List[Tuple[int, str]] = []
    for raw in spec_text.splitlines():
        line = strip_comment(raw)
        if not line.strip():
            continue

        # contar espacios iniciales
        stripped = line.lstrip(" ")
        indent = len(line) - len(stripped)

        level = indent // indent_size
        content = stripped.strip()
        if content:
            items.append((level, content))
    return items


def build_paths(items: List[Tuple[int, str]], out_dir: Path) -> List[Tuple[Path, str]]:
    stack: List[Path] = [out_dir]
    built: List[Tuple[Path, str]] = []

    for level, name in items:
        # ajustar stack al nivel actual (stack[0] es out_dir)
        while len(stack) - 1 > level:
            stack.pop()

        # si el spec “salta” niveles, anclamos al último nivel existente
        if level > len(stack) - 1:
            level = len(stack) - 1

        is_dir = name.endswith("/")
        clean = name[:-1] if is_dir else name

        target = stack[-1] / clean
        kind = "dir" if is_dir else "file"
        built.append((target, kind))

        if is_dir:
            stack.append(target)

    return built


def apply_structure(
    built: List[Tuple[Path, str]],
    create_files: bool,
    force: bool,
    dry_run: bool
) -> List[ItemResult]:
    results: List[ItemResult] = []

    for path, kind in built:
        if kind == "dir":
            if dry_run:
                results.append(ItemResult(path, created=not path.exists(), kind="dir",
                                          action="dry-run"))
                continue

            if path.exists():
                results.append(ItemResult(path, created=False, kind="dir", action="exists"))
            else:
                path.mkdir(parents=True, exist_ok=True)
                results.append(ItemResult(path, created=True, kind="dir", action="created"))
            continue

        # kind == "file"
        if not create_files:
            results.append(ItemResult(path, created=False, kind="file", action="skipped"))
            continue

        if dry_run:
            action = "dry-run"
            results.append(ItemResult(path, created=not path.exists(), kind="file", action=action))
            continue

        path.parent.mkdir(parents=True, exist_ok=True)

        if path.exists():
            if force:
                path.write_bytes(path.read_bytes())  # no-op seguro, pero dejamos acción clara
                results.append(ItemResult(path, created=False, kind="file", action="overwritten"))
            else:
                results.append(ItemResult(path, created=False, kind="file", action="exists"))
        else:
            path.touch(exist_ok=True)
            results.append(ItemResult(path, created=True, kind="file", action="created"))

    return results


def report(results: List[ItemResult]) -> None:
    created_dirs = sum(1 for r in results if r.kind == "dir" and r.action in ("created", "dry-run") and r.created)
    created_files = sum(1 for r in results if r.kind == "file" and r.action in ("created", "dry-run") and r.created)
    skipped_files = sum(1 for r in results if r.kind == "file" and r.action == "skipped")
    existed = sum(1 for r in results if r.action == "exists")
    overwritten = sum(1 for r in results if r.action == "overwritten")
    dry = any(r.action == "dry-run" for r in results)

    print("\n=== Reporte ===")
    if dry:
        print("Modo: DRY-RUN (no se ha escrito nada)")
    print(f"Dirs creados:   {created_dirs}")
    print(f"Files creados:  {created_files}")
    print(f"Ya existían:    {existed}")
    print(f"Sobrescritos:   {overwritten}")
    print(f"Files omitidos: {skipped_files}\n")

    for r in results:
        prefix = {
            "created": "+",
            "exists": "=",
            "skipped": "-",
            "overwritten": "!",
            "dry-run": "~",
        }.get(r.action, "?")
        print(f"{prefix} [{r.kind}] {r.path}")


def main():
    ap = argparse.ArgumentParser(
        description="Genera carpetas/archivos desde un árbol con indentación (formato ChatGPT)."
    )
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--spec", type=str, help="Ruta a un archivo .txt con el árbol")
    g.add_argument("--text", type=str, help="Árbol en un string (usa \\n para saltos)")

    ap.add_argument("--out", type=str, required=True, help="Directorio destino (base)")
    ap.add_argument("--indent", type=int, default=2, choices=[2, 4], help="Tamaño de indentación (2 o 4 espacios)")
    ap.add_argument("--no-files", action="store_true", help="Solo crea carpetas, no archivos")
    ap.add_argument("--force", action="store_true", help="Marca archivos existentes como 'overwritten' (no borra contenido)")
    ap.add_argument("--dry-run", action="store_true", help="Simula sin crear nada")

    args = ap.parse_args()

    out_dir = Path(args.out).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.spec:
        spec_path = Path(args.spec).expanduser().resolve()
        spec_text = spec_path.read_text(encoding="utf-8")
    else:
        spec_text = args.text.replace("\\n", "\n")

    items = parse_lines(spec_text, indent_size=args.indent)
    built = build_paths(items, out_dir)

    results = apply_structure(
        built=built,
        create_files=not args.no_files,
        force=args.force,
        dry_run=args.dry_run,
    )

    report(results)


if __name__ == "__main__":
    main()
