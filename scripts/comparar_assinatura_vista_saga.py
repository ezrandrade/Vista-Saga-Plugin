"""Compara a Assinatura raster do plugin com um relatório de mensurações do Vista SAGA original.

Uso (o primeiro mapa é a referência; os dados do autor nunca vão para o repositório):

    python3 scripts/comparar_assinatura_vista_saga.py --relatorio assinatura01.txt --src EPSG:31985 \
        --classes 1,7,8,17 Bairros.rs2 UsoSolo.rs2 Escolaridade.rs2

    python3 scripts/comparar_assinatura_vista_saga.py --relatorio assinatura02.txt --src EPSG:31985 \
        --todas Bairros.rs2 UsoSolo.rs2 Escolaridade.rs2

Compara, para cada mapa e classe, o total de pixels e os pixels assinados (exatos) e as duas
porcentagens (tolerância de 0,01). Diferença esperada e aceita pelo autor (20/11/2026): o balde do
Vista SAGA marca a região conexa por 4 vizinhos, e o plugin marca a classe inteira; células da classe
ligadas só pela diagonal entram no plugin e ficam fora no Vista SAGA.
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from geosaga.signature_raster import (  # noqa: E402
    open_raster_map, run_raster_signature, scan_reference_classes,
)

ROW = re.compile(r'^\s*(-?\d+)\s+-\s+(.*?)\s*\t\s*(\d+)\s*\t\s*([\d.,]+)\s*\t\s*(\d+)\s*\t\s*([\d.,]+)'
                 r'\s*\t\s*([\d.,]+)%\s*\t\s*([\d.,]+)')


def _num(text):
    return float(text.replace('.', '').replace(',', '.')) if ',' in text else float(text)


def read_report(path):
    """{nome do mapa (minúsculas): {código: (total_pix, asn_pix, pct_area, pct_cat, legenda)}}."""
    maps, current = {}, None
    for line in Path(path).read_text(encoding='cp1252').splitlines():
        header = re.match(r'\s*Resultado da assinatura do mapa\s+(.+?)\s*$', line)
        if header:
            current = maps.setdefault(header.group(1).strip().lower(), {})
            continue
        row = ROW.match(line)
        if row and current is not None:
            current[int(row.group(1))] = (int(row.group(3)), int(row.group(5)), _num(row.group(7)),
                                          _num(row.group(8)), row.group(2).strip())
    if not maps:
        raise SystemExit(f'Nenhum bloco "Resultado da assinatura do mapa" em {path}.')
    return maps


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--relatorio', required=True, help='relatório TXT do Vista SAGA')
    parser.add_argument('--src', required=True, help='SRC dos RS2 (ex.: EPSG:31985); o RS2 não registra SRC')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--classes', help='códigos marcados na referência, separados por vírgula')
    group.add_argument('--todas', action='store_true', help='todas as classes (= "Assinar o mapa inteiro")')
    parser.add_argument('mapas', nargs='+', help='RS2 ou GeoTIFF; o primeiro é a referência')
    args = parser.parse_args(argv)

    report = read_report(args.relatorio)
    maps = [open_raster_map(p, crs=args.src) for p in args.mapas]
    selected = ([k for k, _n, _c in scan_reference_classes(maps[0])] if args.todas
                else [int(c) for c in args.classes.split(',') if c.strip()])
    result = run_raster_signature(maps, selected, per_feature=False)

    checked = equal = 0
    for msig in result.union.maps:
        theirs = report.get(msig.name.lower())
        if theirs is None:
            print(f'{msig.name}: ausente do relatório do Vista SAGA (não comparado)')
            continue
        diffs = []
        for row in msig.rows:
            if not isinstance(row.key, int) or row.key not in theirs:
                diffs.append(f'  classe {row.code_text or row.label}: ausente do relatório')
                continue
            tot, asn, pa, pc, _label = theirs[row.key]
            checked += 1
            same = (tot == row.total_cells and asn == row.asn_cells and abs(pa - row.pct_area) <= 0.01
                    and abs(pc - row.pct_category) <= 0.01)
            equal += same
            if not same:
                diffs.append(f'  classe {row.key} ({row.label}): Vista SAGA total={tot} asn={asn} '
                             f'%área={pa:.2f} %cat={pc:.2f} | plugin total={row.total_cells} '
                             f'asn={row.asn_cells} %área={row.pct_area:.2f} %cat={row.pct_category:.2f}')
        mask_vs = sum(v[1] for v in theirs.values())
        print(f'{msig.name}: limite Vista SAGA = {mask_vs} células; plugin = {msig.asn_cells} células')
        print('\n'.join(diffs) if diffs else '  todas as classes coincidem')
    print(f'\nClasses coincidentes: {equal} de {checked} ({100.0 * equal / checked if checked else 0:.2f}%)')
    return 0 if checked and equal == checked else 1


if __name__ == '__main__':
    sys.exit(main())
