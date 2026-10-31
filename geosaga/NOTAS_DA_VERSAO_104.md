# Vista Saga Plugin 1.0.4 — versão consolidada (31/10/2026)

A versão 1.0.4 foi preparada em pacote ZIP instalável, mas o código completo desse pacote **ainda não foi sincronizado com a branch `main` do GitHub**. Até a sincronização, o arquivo `geosaga/metadata.txt` da branch `main` continuará indicando 1.0.3. Não confundir a versão consolidada do ZIP com o código atualmente baixado pelo botão **Code → Download ZIP**.

## Alterações consolidadas em relação à 1.0.3

- Internacionalização com reconhecimento automático do idioma do QGIS; português brasileiro e inglês testados e aprovados.
- Substituição do painel inicial por um único botão **Vista Saga Plugin** com submenu dos sete módulos.
- Identidade visual da mão sustentando o globo, ícones preparados para a interface clássica e apresentação na guia Complementos do QRibbonSkin.
- Mantida a posição atual da seta inferior no botão do QRibbonSkin. A eventual faixa lateral e os temas claro/escuro pertencem a uma futura edição do QRibbonSkin e **não fazem parte** do Vista Saga Plugin 1.0.4.
- Endereço institucional do projeto: https://vistasagaplugin.wordpress.com/
- Testes funcionais informados pelo mantenedor em Windows 11 e Linux/Flatpak.
- Preservados os algoritmos geoespaciais e seus IDs `geosaga:*`.
- Tradução espanhola ainda parcial.

## Pendências antes da publicação no QGIS

1. Sincronizar todo o código-fonte e os recursos binários do pacote instalável 1.0.4 com o GitHub, não apenas o número de versão.
2. Confirmar `metadata.txt`, `CHANGELOG.md`, ícones e pacotes de tradução na mesma revisão de código.
3. Executar as verificações de segurança, integridade e funcionamento da versão sincronizada.
4. Criar a referência de versão 1.0.4 e submeter o ZIP ao repositório oficial QGIS.

O histórico da versão 1.0.3 deve permanecer disponível.
