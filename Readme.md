# KubeRest

## Implementação de um mecanismo de escalonamento dinâmico de pods em um cluster kubernetes, utilizando o recurso ReplicaSet. 🐳

<p float="left">
 <img src="https://img.shields.io/badge/Docker-2CA5E0?style=for-the-badge&logo=docker&logoColor=white">
 <img src="https://img.shields.io/badge/Kubernetes-316192?style=for-the-badge&logo=kubernetes&logoColor=white">
 <img src="https://img.shields.io/badge/Flask-092E20?style=for-the-badge&logo=flask&logoColor=white">
 <img src="https://img.shields.io/badge/GitHub_Actions-2088FF?style=for-the-badge&logo=github-actions&logoColor=white">
</p>

## Ideia: 💡
- **_Implementar uma API REST na aplicação back-end que interaja com a API do Kubernetes para realizar operações de escalonamento (escalonar, listar, e monitorar pods)._**

- **_Definir rotas específicas, como /scale-up, /scale-down, e /status, que permitam aumentar ou diminuir o número de réplicas de pods e consultar o status atual do ReplicaSet._**

- **_Criar um Deployment simples que utilize um ReplicaSet para gerenciar a replicação de pods de uma aplicação de sua escolha._**

- **_Especificar a quantidade inicial de réplicas de pods no arquivo de configuração YAML._**

- **_Configurar o Kubernetes para monitorar métricas de uso de recursos (CPU, memória, etc.) e expor essas métricas para a aplicação back-end através de uma ferramenta de monitoramento, como o Prometheus._**

- **_Desenvolver um módulo na aplicação back-end que tome decisões de escalonamento com base nas métricas recebidas (ex: aumentar o número de réplicas se o uso de CPU exceder 80%)._**

### Licença
Este projeto é licenciado sob a licença [MIT] - veja o arquivo [LICENSE](./LICENSE) para mais detalhes.

### Contribuição
Para qualquer tipo de contribuição no código, consulte [CONTRIBUTING.md](./CONTRIBUTING.md) e saiba como contribuir para esse projeto open source.