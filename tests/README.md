# Testes complementares (1.0.5)

Complementam a suíte histórica `geosaga/tests` (unittest). Não entram no ZIP de instalação.

| Pasta | Conteúdo | Requer |
|---|---|---|
| `tests/unit` | 35 testes pytest: núcleo de avaliação/monitoria, Mann–Kendall exato, Voronoi contra força bruta, atrito composto, GIF, catálogos de tradução | Python do QGIS + `pytest` |
| `tests/qgis/smoke_qgis.py` | 45 verificações em QGIS real sem interface: carga/descarga, 7 diálogos, 3 algoritmos Processing, todos os motores, cancelamento sem resíduos, entradas inválidas, estado global do GDAL | PyQGIS |
| `tests/qgis/gui_monkey.py` | Estresse de interface: clica em todos os botões dos 7 módulos | PyQGIS |

Execução na raiz do repositório (Windows: **OSGeo4W Shell**, trocando `export` por `set`):

```bash
python -m unittest discover -s geosaga/tests -p 'test_*.py'
python -m pytest -q tests/unit
export QT_QPA_PLATFORM=offscreen
python tests/qgis/smoke_qgis.py . /tmp/vsp_smoke
VSP_GDAL_EXCEPTIONS=off python tests/qgis/smoke_qgis.py . /tmp/vsp_smoke_off
python tests/qgis/gui_monkey.py . /tmp/vsp_smoke en_US
```

Resultado esperado: todos aprovados e `exceções não tratadas = 0`.
