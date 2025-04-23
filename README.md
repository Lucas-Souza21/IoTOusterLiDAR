# Captura e conversão de dados LiDAR utilizando um sensor Ouster OS1

Este projeto realiza a **captura de dados LiDAR** utilizando um sensor **Ouster OS1**, e converte automaticamente os dados do formato padrão da Ouster `.pcap` para `.osf`, sendo um formato intermediário, e por fim para a extensão `.las`, utilizada em diversas aplicações relacionadas à compreensão ou manipulação de nuvem de pontos.

---

## 📌 Funcionalidades

- Configuração automática do sensor Ouster OS1
- Captura de dados por tempo definido (padrão: 5 segundos, sendo possível alterar no código)
- Armazenamento dos dados em um diretório estruturado criado a partir da data e horario da captura
- Conversão dos dados de:
  - `.pcap` → `.osf` (formato intermediário Ouster)
  - `.osf` → `.las` (formato padrão da indústria para nuvens de pontos)

---

## ⚙️ Requisitos

O script foi criado para ser executado em um sistema operacional Linux Ubuntu, portanto os requisitos são relacionados à configurações do próprio Sistema Operacional.

É importante verificar a versão do Ubuntu utilizado, sendo necessário a versão 24.04.02 LTS codenome Noble para funcionamento.

Antes de executar o script, certifique-se de que os seguintes pacotes e ferramentas estão instalados em um ambiente virtual (virtual enviroment `.venv`):

### Pacontes Python utilizados:
```bash
pip install ouster-sdk laspy more-itertools numpy
