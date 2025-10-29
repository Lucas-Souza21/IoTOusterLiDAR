# CapturaDadosLiDARv07.py
## Correção de movimentos angulares 29/10/2025
ouster-sdk v0.15

Inclusão de ferramentas de correção do movimento angular.
Remoção temporária das ferramentas PDAL.
Remoção do arquivo CSV e extensão intermediaria .osf.

# CapturaDadosLiDARv06.py
## Geração de CSVs
ouster-sdk v0.15

Inclusão da geração de arquivos csvs para melhorar a interação com PDAL.

# CapturaDadosLiDARv05.py
## Inclusão do PDAL
ouster-sdk v0.15

Inclusão da ferramenta PDAL para utilização de manipulações futuras.

# CapturaDadosLiDARv04.py
## Inclusão de controle de voxel-size
ouster-sdk v0.15

Incluida linha de código de voxel-size para conseguir controlar melhor qual a distancia dos pontos utilizados durante o SLAM, tornando as imagens .laz finais mais nítidas

# CapturaDadosLiDARv03.py
## Conversão para .laz através do laszip64 e remoção dos arquivos intermediários
ouster-sdk v0.15

Incluida função que converge os arquivos .las para .laz, uma forma comprimida de nuvens de pontos que não necessita descompactação para utilização. Alem da remoção dos arquivos .pcap, .osf e .las em caso de conversão com sucesso.

# CapturaDadosLiDARv02.py
## Atualização para a versão ouster-sdk v0.15:
ouster-sdk v0.15

Funções de criação da pasta de diretorios, gravação, armazenamento e conversão dos arquivos, de .pcap para .osf e para .las atualizadas para a versão 0.15.

# CapturaDadosLiDARv01.py
## Primeira versão:
ouster-sdk v0.14

Funções de criação da pasta de diretorios, gravação, armazenamento e conversão dos arquivos, de .pcap para .osf e para .las
