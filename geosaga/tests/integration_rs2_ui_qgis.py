"""Verificação interativa de interface Qt6; executar no console Python do QGIS.

Uso:
    from geosaga.tests.integration_rs2_ui_qgis import run
    run()
"""

def run():
    from qgis.utils import iface
    from qgis.core import Qgis
    from qgis.gui import QgsProjectionSelectionWidget, QgsMapLayerComboBox
    from geosaga.rs2_dialog import RS2ConverterDialog

    widget = RS2ConverterDialog(iface, iface.mainWindow())
    try:
        if not isinstance(widget.crs_widget, QgsProjectionSelectionWidget):
            raise RuntimeError('Seletor de SRC não inicializado.')
        if not isinstance(widget.loaded_layers, QgsMapLayerComboBox):
            raise RuntimeError('Seletor de camadas do QGIS não inicializado.')
        if widget.crs_widget.crs().isValid():
            raise RuntimeError('SRC deve iniciar não definido: não inventar EPSG.')
        if widget.mode.count() != 4:
            raise RuntimeError('Devem existir 4 operações raster/vetor.')
        widget.mode.setCurrentIndex(2)
        if widget.vector_format.count() < 4:
            raise RuntimeError('Formatos vetoriais incompletos.')
        widget.batch.setChecked(True)
        if not widget.batch_folder.isEnabled():
            raise RuntimeError('Seleção de pasta não habilitada no modo lote.')
        widget.batch.setChecked(False)
        widget.mode.setCurrentIndex(3)
        if widget.use_loaded.isHidden():
            raise RuntimeError('Modo TIFF → Vetor não mostrou camadas do QGIS.')
        widget.batch.setChecked(True)
        widget.mode.setCurrentIndex(1)
        if widget.reference.isEnabled():
            raise RuntimeError('RS2 de referência não deve ser usado no modo lote.')
        widget.batch.setChecked(False)
        if not widget.use_loaded.isEnabled():
            raise RuntimeError('Seleção da camada do QGIS não foi habilitada.')
        widget.mode.setCurrentIndex(3)
        if widget._epsg() != '':
            raise RuntimeError('O modo TIFF → Vetor deve herdar o SRC por padrão.')
        print('Vista Saga 0.3.6: 4 operações e interface PyQGIS/Qt6 inicializadas.')
        return True
    finally:
        widget.close()
        widget.deleteLater()
