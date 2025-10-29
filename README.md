# Captura e conversão de dados LiDAR utilizando um sensor Ouster OS1

Este projeto realiza a **captura de dados LiDAR** utilizando um sensor **Ouster OS1**, e converte automaticamente os dados do formato padrão da Ouster `.pcap` para `.las`, utilizada em diversas aplicações relacionadas à compreensão ou manipulação de nuvem de pontos.

---

## 📌 Funcionalidades

- Configuração automática do sensor Ouster OS1
- Captura de dados por tempo definido (padrão: 5 segundos, sendo possível alterar no código)
- Armazenamento dos dados em um diretório estruturado criado a partir da data e horario da captura
- Conversão dos dados de:
  - `.pcap` → `.las` (formato padrão da indústria para nuvens de pontos)
  - `.las` → `.laz` (formato padrão comprido de nuvens de pontos)

---

## ⚙️ Requisitos

O script foi criado para ser executado em um sistema operacional Linux Ubuntu, portanto os requisitos são relacionados à configurações do próprio Sistema Operacional.

É importante verificar a versão do Ubuntu utilizado, sendo necessário a versão 24.04.02 LTS codenome Noble para funcionamento.

Antes de executar o script, certifique-se de que os seguintes pacotes e ferramentas estão instalados em um ambiente virtual (virtual enviroment `.venv`):

Também foi utilizado o executável 'laszip64' na mesma pasta do código a ser testado.

Após a versão V05 é necessário a presença de PDAL para o funcionamento do código.

### Pacontes Python utilizados:
```bash
pip install ouster-sdk laspy more-itertools numpy
