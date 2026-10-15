"""Cria o ZIP instalável para QGIS a partir da árvore do repositório.

Executar na raiz: python scripts/build_release.py
"""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "geosaga"
OUT = ROOT / "dist" / "Vista_Saga_Plugin_QGIS4_v0.9.0.zip"
OUT.parent.mkdir(parents=True, exist_ok=True)
if not (PLUGIN / "metadata.txt").is_file() or not (PLUGIN / "__init__.py").is_file():
    raise SystemExit("Diretório instalável geosaga inválido.")

with ZipFile(OUT, "w", ZIP_DEFLATED) as z:
    for path in sorted(PLUGIN.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if ("tests" in rel.parts or "__pycache__" in rel.parts or
                path.suffix in {".pyc", ".pyo"}):
            continue
        if path.suffix == ".md" and path.name not in {
            "README.md", "CHANGELOG.md", "LICENSE.md", "NOTAS_DA_VERSAO_090.md"
        }:
            continue
        z.write(path, rel.as_posix())

print(f"Pacote criado: {OUT}")
