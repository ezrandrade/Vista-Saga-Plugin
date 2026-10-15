# Vista Saga Plugin 1.0.2 — Compatibilidade QGIS 4.x / Qt6

Esta versão corrige exclusivamente as seis referências a enums apontadas pelo verificador QGIS:

- `evaluation_task.py`, `monitoring_task.py` e `voronoi_dialog.py`: `QgsTask.Flag.CanCancel`;
- `voronoi_dialog.py`: `QgsWkbTypes.GeometryType.PointGeometry` e `QgsWkbTypes.GeometryType.PolygonGeometry`;
- `rs2_dialog.py`: `QgsProjectionSelectionWidget.CrsOption.CrsNotSet`.

Identificadores `geosaga:*` preservados; algoritmos matemáticos dos sete módulos não alterados. Enviar novo ZIP 1.0.2 ao repositório de plugins QGIS e conferir a análise de compatibilidade Qt6 e a varredura de segurança. Os testes locais verificam sintaxe, estrutura e regressão sem executar a interface Qt6.
