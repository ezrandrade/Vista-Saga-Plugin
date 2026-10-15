"""Validação prévia de conversão em lote: mesmas dimensões e resolução.

Independente do QGIS para permitir testes de regressão.
"""
from dataclasses import dataclass
from pathlib import Path
import math

from .rs2_format import RS2Reader, RS2Error


@dataclass(frozen=True)
class Grid:
    columns: int
    rows: int
    dx: float
    dy: float
    extent: tuple | None


def source_mode(filename):
    suffix = Path(filename).suffix.lower()
    if suffix == '.rs2':
        return 0
    if suffix in ('.tif', '.tiff'):
        return 1
    raise RS2Error(f'Entrada não suportada: {Path(filename).name}. Use RS2 ou TIFF.')


def inspect_grid(filename, manual_bounds=None):
    path = Path(filename)
    if not path.is_file():
        raise RS2Error(f'Arquivo não encontrado: {path}')
    if source_mode(filename) == 0:
        h = RS2Reader(path).header
        return Grid(h.width, h.height, h.pixel_x, h.pixel_y,
                    (h.xmin, h.ymin, h.xmax, h.ymax))
    from .rs2_converter import _gdal, _parse_bounds
    gdal, _ = _gdal()
    ds = gdal.Open(str(path), gdal.GA_ReadOnly)
    if ds is None:
        raise RS2Error(f'Não foi possível abrir o TIFF: {path}')
    try:
        cols, rows = ds.RasterXSize, ds.RasterYSize
        gt = ds.GetGeoTransform(can_return_null=True)
        if gt is None:
            if manual_bounds:
                bbox = _parse_bounds(manual_bounds, cols, rows)
                return Grid(cols, rows,
                            (bbox[2] - bbox[0]) / cols,
                            (bbox[3] - bbox[1]) / rows, bbox)
            return Grid(cols, rows, math.nan, math.nan, None)
        if abs(gt[2]) > 1e-10 or abs(gt[4]) > 1e-10 or gt[1] <= 0 or gt[5] >= 0:
            raise RS2Error(f'Raster rotacionado ou grade inválida: {path.name}')
        bbox = (gt[0], gt[3] + rows * gt[5], gt[0] + cols * gt[1], gt[3])
        return Grid(cols, rows, float(gt[1]), float(-gt[5]), bbox)
    finally:
        ds = None


def compatible_grids(a, b, require_alignment=True):
    if (a.columns, a.rows) != (b.columns, b.rows):
        return False, 'dimensões matriciais diferentes'
    if a.extent is None or b.extent is None:
        return False, 'grade sem coordenadas; informe extensão manual comprovada'
    for k in ('dx', 'dy'):
        if not math.isclose(getattr(a, k), getattr(b, k), rel_tol=1e-8, abs_tol=1e-7):
            return False, 'resolução espacial diferente'
    if require_alignment:
        for x, y in zip(a.extent, b.extent):
            if not math.isclose(x, y, rel_tol=0, abs_tol=1e-5):
                return False, 'origem/extensão diferentes (grades desalinhadas)'
    return True, ''


def prepare_batch(sources, folder, manual_bounds=None, operation=None, vector_extension=".gpkg"):
    """Valida todos ANTES do primeiro arquivo ser processado.

    Rejeita arquivos sem grade, dimensões/resoluções diferentes e nomes duplicados.
    Desalinhamento não bloqueia conversões independentes; use alignment_warnings.
    """
    sources = [Path(s) for s in sources]
    if not sources:
        raise RS2Error('Adicione pelo menos um arquivo ao lote.')
    if len({p.resolve() for p in sources}) != len(sources):
        raise RS2Error('O lote contém arquivos repetidos.')
    input_mode = source_mode(sources[0])
    mode = input_mode if operation is None else operation
    if mode not in (0, 1, 2, 3) or (mode in (1, 3)) != (input_mode == 1):
        raise RS2Error('A operação selecionada não corresponde ao tipo de entrada.')
    if mode in (2, 3):
        from .rs2_vector import vector_format
        vector_format(vector_extension)
    base_grid = None
    plans, used_targets = [], set()
    output_folder = Path(folder)
    if not output_folder.is_dir():
        raise RS2Error('Selecione uma pasta de saída existente para o lote.')
    for path in sources:
        if source_mode(path) != input_mode:
            raise RS2Error('Não misture RS2 e TIFF no mesmo lote; execute operações separadas.')
        grid = inspect_grid(path, manual_bounds if mode in (1, 3) else None)
        if base_grid is None:
            base_grid = grid
            if mode in (1, 3) and grid.extent is None:
                raise RS2Error('O primeiro TIFF não possui coordenadas. Informe extensão manual.')
        else:
            valid, why = compatible_grids(base_grid, grid, require_alignment=False)
            if not valid:
                raise RS2Error(f'{path.name}: {why}. Corrija o lote ou converta separadamente.')
        name = path.stem + ('_categorias.tif' if mode == 0 else
                            '_convertido.rs2' if mode == 1 else
                            '_poligonos' + vector_extension)
        dest = output_folder / name
        key = str(dest.resolve()).casefold()
        if key in used_targets:
            raise RS2Error('Dois arquivos de origem possuem o mesmo nome de saída: ' + name)
        used_targets.add(key)
        if path.resolve() == dest.resolve():
            raise RS2Error('A saída não pode sobrescrever o arquivo de entrada: ' + name)
        plans.append((path, dest))
    return mode, plans, base_grid


def alignment_warnings(sources, manual_bounds=None):
    """Avisos não bloqueantes: o lote converte mapas individualmente.

    Grades deslocadas NÃO devem ser corrigidas automaticamente na conversão,
    mas precisam ser revistas antes de operações espaciais entre os mapas.
    """
    sources = [Path(p) for p in sources]
    if len(sources) < 2:
        return []
    reference = inspect_grid(sources[0], manual_bounds)
    warnings = []
    for path in sources[1:]:
        other = inspect_grid(path, manual_bounds)
        valid, reason = compatible_grids(reference, other)
        if not valid and reason == 'origem/extensão diferentes (grades desalinhadas)':
            warnings.append(f'{path.name}: {reason}; limites {other.extent}')
    return warnings
