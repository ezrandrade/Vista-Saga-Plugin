"""Publicação transacional do GeoTIFF e de seus arquivos auxiliares.

Evita deixar .aux.xml/.tfw/.tifw/.rs2.json antigos após substituir o
GeoTIFF. Em caso de falha, restaura o conjunto anterior sempre que possível.
"""
from pathlib import Path
import os
import shutil
import tempfile

from .rs2_format import RS2Error


def output_family(tiff):
    """Arquivos associados criados pelo conversor ou pelo GDAL.

    Um .xml genérico (<stem>.xml) não é apagado por segurança, pois pode
    conter metadados externos não pertencentes ao plugin.
    """
    p = Path(tiff)
    return [p, Path(str(p) + '.rs2.json'), Path(str(p) + '.aux.xml'),
            Path(str(p) + '.xml'), p.with_suffix('.tfw'),
            Path(str(p) + 'w')]


def output_conflicts(tiff):
    return [p for p in output_family(tiff) if p.exists()]


def publish_geotiff(staged, final):
    """Move TIFF e auxiliares de stage para final com backup e rollback.

    O chamador deve fechar o dataset GDAL antes de chamar. Não altera .xml
    genérico ou arquivos auxiliares de outra extensão desconhecida.
    """
    staged, final = Path(staged), Path(final)
    stage_family = output_family(staged)
    final_family = output_family(final)
    if not staged.is_file():
        raise RS2Error('GeoTIFF temporário não foi produzido.')
    if staged.resolve() == final.resolve():
        raise RS2Error('O raster temporário e a saída devem ser distintos.')
    final.parent.mkdir(parents=True, exist_ok=True)
    backup_dir = Path(tempfile.mkdtemp(prefix='.vista_rs2_backup_', dir=final.parent))
    moved_old, published = [], []
    keep_backup = False
    try:
        for index, target in enumerate(final_family):
            if target.is_dir():
                raise RS2Error(f'Um arquivo auxiliar esperado é uma pasta: {target}')
            if target.exists():
                backup = backup_dir / f'{index}.bak'
                os.replace(target, backup)
                moved_old.append((backup, target))
        for incoming, outgoing in zip(stage_family, final_family):
            if incoming.exists():
                os.replace(incoming, outgoing)
                published.append(outgoing)
    except Exception as exc:
        for published_file in reversed(published):
            try:
                published_file.unlink(missing_ok=True)
            except OSError:
                pass
        errors = []
        for old, target in reversed(moved_old):
            try:
                os.replace(old, target)
            except OSError as rollback_exc:
                errors.append(str(rollback_exc))
        keep_backup = bool(errors)
        suffix = (' Falha ao restaurar arquivos originais; backups em ' +
                  str(backup_dir) + ': ' + '; '.join(errors)) if errors else ''
        raise RS2Error('Falha na substituição do GeoTIFF/auxiliares: ' + str(exc) + suffix) from exc
    finally:
        if not keep_backup:
            shutil.rmtree(backup_dir, ignore_errors=True)
        for leftover in stage_family:
            try:
                leftover.unlink(missing_ok=True)
            except OSError:
                pass
    return final


def write_worldfile(tiff, x_min, y_max, pixel_x, pixel_y):
    """Cria .tfw junto ao TIFF temporário, com centros dos pixels."""
    tiff = Path(tiff)
    p = tiff.with_suffix('.tfw')
    p.write_text('\n'.join(f'{v:.12g}' for v in (
        pixel_x, 0.0, 0.0, -pixel_y,
        x_min + pixel_x / 2, y_max - pixel_y / 2)) + '\n', encoding='ascii')
    return p
