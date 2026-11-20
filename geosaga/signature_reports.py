"""Relatórios TXT e CSV da Assinatura (1.5.0), sempre em português (regra do plugin)."""
import csv
from datetime import datetime

from .signature_model import CONFLICT_KEY, NO_CLASS_KEY, SPECIAL_LABELS

CSV_FIELDS = ['RECORTE', 'ID_FEICAO', 'NOME_FEICAO', 'MAPA', 'CODIGO', 'CLASSE', 'TOTAL_PIXELS',
              'TOTAL_HA', 'PIXELS_ASN', 'AREA_ASN_HA', 'PCT_AREA_ASN', 'PCT_CATEGORIA']


def _dec(value, places=6):
    return '' if value is None else f'{float(value):.{places}f}'


def _cut_rows(cut, kind):
    for msig in cut.maps:
        for row in msig.rows:
            yield {
                'RECORTE': 'UNIAO' if kind == 'UNIAO' else 'FEICAO',
                'ID_FEICAO': '' if kind == 'UNIAO' else str(cut.key),
                'NOME_FEICAO': cut.name,
                'MAPA': msig.name,
                'CODIGO': row.code_text,
                'CLASSE': row.label,
                'TOTAL_PIXELS': '' if row.total_cells is None else row.total_cells,
                'TOTAL_HA': _dec(row.total_ha),
                'PIXELS_ASN': '' if row.asn_cells is None else row.asn_cells,
                'AREA_ASN_HA': _dec(row.asn_ha),
                'PCT_AREA_ASN': _dec(row.pct_area),
                'PCT_CATEGORIA': _dec(row.pct_category),
            }


def write_csv(path, result):
    """Uma linha por recorte, mapa e classe; ``;`` e UTF-8 com BOM, como os demais CSV do plugin."""
    with open(path, 'w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS, delimiter=';')
        writer.writeheader()
        writer.writerows(_cut_rows(result.union, 'UNIAO'))
        for cut in result.features:
            writer.writerows(_cut_rows(cut, 'FEICAO'))


def _table(stream, msig, raster):
    stream.write(f'\nResultado da assinatura do mapa {msig.name}\n')
    if raster:
        stream.write('Cat. - Legendas | Total pixels | Total ha | Pixels asn. | Área asn. ha | '
                     '% Área asn. | % Categoria\n')
    else:
        stream.write('Cat. - Legendas | Total ha | Área asn. ha | % Área asn. | % Categoria\n')
    for row in msig.rows:
        name = row.display
        category = '' if row.pct_category is None else f'{row.pct_category:.2f}'
        if raster:
            stream.write(f'{name} | {row.total_cells} | {row.total_ha:.2f} | {row.asn_cells} | '
                         f'{row.asn_ha:.2f} | {row.pct_area:.2f}% | {category}\n')
        else:
            stream.write(f'{name} | {row.total_ha:.4f} | {row.asn_ha:.4f} | {row.pct_area:.2f}% | '
                         f'{category}\n')
    if raster:
        stream.write(f'Total | {msig.total_cells} ({msig.total_ha:.2f} ha) | '
                     f'{msig.asn_cells} ({msig.asn_ha:.2f} ha)\n')
    else:
        stream.write(f'Total | {msig.total_ha:.4f} ha | {msig.asn_ha:.4f} ha\n')


def write_txt(path, result, *, title='', maps_detail=None, overlap=''):
    raster = result.kind == 'raster'
    with open(path, 'w', encoding='utf-8') as stream:
        stream.write('Vista Saga Plugin - Assinatura\n')
        if title:
            stream.write(f'Título: {title}\n')
        stream.write(f'Data: {datetime.now():%d/%m/%Y %H:%M}\n')
        stream.write(f'Guia: {"Raster" if raster else "Vetorial"}\n')
        stream.write(f'SRC: {result.srs_name}\n')
        stream.write(f'Mapa de referência: {result.reference}\n')
        names = [m.name for m in result.union.maps]
        stream.write(f'Mapas assinados (na ordem da lista): {", ".join(names)}\n')
        if maps_detail:
            for line in maps_detail:
                stream.write(f'  {line}\n')
        what = 'Classes selecionadas' if raster else 'Feições selecionadas'
        stream.write(f'{what} ({len(result.selection)}): {"; ".join(result.selection)}\n')
        if raster:
            stream.write(f'Área da célula: {result.cell_ha * 10000:.6f} m²\n')
            stream.write('Método: contagem de células. Feição = classe inteira da referência; FUNDO e NoData '
                         'contam como classe.\n')
        else:
            stream.write('Método: interseção geométrica exata no SRC dos mapas (área planimétrica). Polígonos '
                         'da mesma classe são dissolvidos.\n')
            if overlap:
                stream.write(f'Sobreposição entre classes diferentes: {overlap}.\n')
            stream.write(f'"{SPECIAL_LABELS[NO_CLASS_KEY]}": parte do limite sem polígono no mapa. '
                         f'"{SPECIAL_LABELS[CONFLICT_KEY]}": região com classes diferentes sobrepostas.\n')
        stream.write('% Área asn. = área da classe no limite / área do limite. '
                     '% Categoria = área da classe no limite / área da classe no mapa inteiro.\n')
        if result.warnings:
            stream.write('Avisos:\n')
            for warning in result.warnings:
                stream.write(f'  - {warning}\n')
        stream.write('\n' + '=' * 70 + '\nUNIÃO DA SELEÇÃO\n' + '=' * 70 + '\n')
        for msig in result.union.maps:
            _table(stream, msig, raster)
        for cut in result.features:
            label = 'CLASSE' if raster else 'FEIÇÃO'
            ident = '' if raster else f' (ID {cut.key})'
            stream.write('\n' + '=' * 70 + f'\n{label}: {cut.name}{ident}\n' + '=' * 70 + '\n')
            for msig in cut.maps:
                _table(stream, msig, raster)

