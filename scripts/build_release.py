"""Cria o ZIP instalável para QGIS a partir da árvore do repositório.

Executar na raiz: python scripts/build_release.py
"""
from configparser import ConfigParser
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "geosaga"
if not (PLUGIN / "metadata.txt").is_file() or not (PLUGIN / "__init__.py").is_file():
    raise SystemExit("Diretório instalável geosaga inválido.")

metadata = ConfigParser(interpolation=None)
metadata.read(PLUGIN / "metadata.txt", encoding="utf-8")
version = metadata.get("general", "version").strip()
if not version or "/" in version or "\\" in version:
    raise SystemExit("Número de versão inválido no metadata.txt.")

OUT = ROOT / "dist" / f"Vista_Saga_Plugin_QGIS4_v{version}.zip"
OUT.parent.mkdir(parents=True, exist_ok=True)
release_notes = f"NOTAS_DA_VERSAO_{version.replace('.', '')}.md"

with ZipFile(OUT, "w", ZIP_DEFLATED) as z:
    for path in sorted(PLUGIN.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if ("tests" in rel.parts or "__pycache__" in rel.parts or
                path.suffix in {".pyc", ".pyo"}):
            continue
        if path.suffix == ".md" and path.name not in {
            "README.md", "CHANGELOG.md", "LICENSE.md", release_notes
        }:
            continue
        z.write(path, rel.as_posix())

print(f"Pacote criado: {OUT}")
