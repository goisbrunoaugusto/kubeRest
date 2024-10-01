# pylint: skip-file
"""Códigos para as funçoes de listar, escalonar, monitorar"""
import sys
import os
import time
import requests
from flask import Flask, jsonify, Response, request
from kubernetes import config, client
import kubernetes.client
from prometheus_client import start_http_server, Gauge
from prometheus_client.parser import text_string_to_metric_families

# Inicializando a aplicação Flask
app = Flask(__name__)

# Métricas para Prometheus
# Gauge é uma métrica que pode subir ou descer, usada aqui para CPU e memória dos pods
cpu_usage_metric = Gauge('k8s_pod_cpu_usage', 'CPU usage of a Kubernetes pod', ['pod_name'])
memory_usage_metric = Gauge('k8s_pod_memory_usage', 'Memory usage of a Kubernetes pod', ['pod_name'])

# Rota para listar o status dos pods em todos os namespaces
@app.route("/status", methods=['GET'])
def get_minikube_pod_info():
    """
    Função que lista os pods em todos os namespaces, incluindo seus nomes, status, tempo de criação,
    namespace e a imagem que está sendo executada.
    """
    # Carrega as configurações do kubeconfig se não estiver em um ambiente de CI
    if os.getenv("CI_ENVIRONMENT") != "true":
        config.load_kube_config()
    else:
        print("Ambiente de CI detectado, não carregando configuração do Kubernetes.")
        sys.exit()

    v1 = client.CoreV1Api()
    pod_list = []

    try:
        # Obtém todos os pods de todos os namespaces
        pods = v1.list_pod_for_all_namespaces()

        # Itera sobre cada pod e coleta informações relevantes
        for pod in pods.items:
            pod_info = {
                "pod_name": pod.metadata.name,
                "pod_phase": pod.status.phase,
                "pod_creation_time": pod.metadata.creation_timestamp,
                "pod_namespace": pod.metadata.namespace,
                "pod_image": pod.spec.containers[0].image
            }
            pod_list.append(pod_info)

        return jsonify(pod_list)

    except client.exceptions.ApiException:
        return Response("Erro ao listar pods", status=500)

# Rota para escalar (aumentar) o número de réplicas de um deployment
@app.route("/scale-up", methods=['POST'])
def scale_up():
    """
    Função que aumenta o número de réplicas de um deployment baseado nos dados enviados via JSON.
    Requer os parâmetros "deployment-name", "deployment-namespace", e "replicas".
    """
    data = request.get_json()

    # Carrega as configurações do Kubernetes
    config.load_kube_config()
    v1 = client.AppsV1Api()
    
    try:
        # Lê as informações do deployment especificado
        deployment = v1.read_namespaced_deployment(
            name=data.get("deployment-name"),
            namespace=data.get("deployment-namespace")
        )
        # Aumenta o número de réplicas
        deployment.spec.replicas += int(data.get("replicas"))
        v1.patch_namespaced_deployment(
            name=data.get("deployment-name"),
            namespace=data.get("deployment-namespace"),
            body=deployment
        )

        return Response(status=200)

    except client.exceptions.ApiException:
        return Response("Erro ao escalonar deploy", status=500)

# Rota para diminuir o número de réplicas de um deployment
@app.route("/scale-down", methods=['POST'])
def scale_down():
    """
    Função que diminui o número de réplicas de um deployment baseado nos dados enviados via JSON.
    Requer os parâmetros "deployment-name", "deployment-namespace", e "replicas".
    """
    data = request.get_json()

    # Carrega as configurações do Kubernetes
    config.load_kube_config()
    v1 = client.AppsV1Api()
    
    try:
        # Lê as informações do deployment especificado
        deployment = v1.read_namespaced_deployment(
            name=data.get("deployment-name"),
            namespace=data.get("deployment-namespace")
        )
        # Verifica se o número de réplicas que está sendo removido é maior que o atual
        if int(data.get("replicas")) > deployment.spec.replicas:
            return Response("Valor maior que o número de réplicas existentes!", status=400)
        # Diminui o número de réplicas
        deployment.spec.replicas -= int(data.get("replicas"))

        v1.patch_namespaced_deployment(
            name=data.get("deployment-name"),
            namespace=data.get("deployment-namespace"),
            body=deployment
        )

        return Response(status=200)

    except client.exceptions.ApiException:
        return Response("Erro ao diminuir replicas", status=500)

# Rota para criar um novo deployment
@app.route("/deploy", methods=['POST'])
def criar_deployment():
    """
    Função que cria um novo deployment no Kubernetes. Os dados do deployment, como nome, imagem,
    réplicas, namespace e porta, devem ser enviados via JSON.
    """
    config.load_kube_config()
    v1 = client.AppsV1Api()
    data = request.get_json()

    deployment_name = data.get("deployment-name")
    deployment_image = data.get("deployment-image")
    deployment_replicas = data.get("deployment-replicas")
    deployment_namespace = data.get("deployment-namespace")
    deployment_port = data.get("deployment-port")

    try:
        # Cria um novo deployment com os parâmetros fornecidos
        v1.create_namespaced_deployment(
            namespace=deployment_namespace,
            body=kubernetes.client.V1Deployment(
                metadata=kubernetes.client.V1ObjectMeta(name=deployment_name),
                spec=kubernetes.client.V1DeploymentSpec(
                    replicas=int(deployment_replicas),
                    selector=kubernetes.client.V1LabelSelector(
                        match_labels={"app": deployment_name}
                    ),
                    template=kubernetes.client.V1PodTemplateSpec(
                        metadata=kubernetes.client.V1ObjectMeta(labels={"app": deployment_name}),
                        spec=kubernetes.client.V1PodSpec(
                            containers=[
                                kubernetes.client.V1Container(
                                    name=deployment_name,
                                    image=deployment_image,
                                    ports=[kubernetes.client.V1ContainerPort(
                                        container_port=int(deployment_port)
                                    )]
                                )
                            ]
                        )
                    )
                )
            )
        )
        return Response(status=201)
    except client.exceptions.ApiException as e:
        return Response("Erro ao criar deployment", status=400)

# Função para monitorar o uso de recursos (CPU e memória) dos pods e expor para o Prometheus
def monitor_pods_resources():
    """
    Função que coleta as métricas de CPU e memória dos pods e atualiza as métricas expostas
    via Prometheus.
    """
    config.load_kube_config()
    custom_metrics_api = client.CustomObjectsApi()
    namespace = 'default'  # Substitua pelo namespace correto

    try:
        # Obtém as métricas dos pods no namespace especificado
        metrics = custom_metrics_api.list_namespaced_custom_object(
            group="metrics.k8s.io", version="v1beta1", namespace=namespace, plural="pods"
        )
        for item in metrics["items"]:
            pod_name = item["metadata"]["name"]
            cpu_usage = item["containers"][0]["usage"]["cpu"]
            memory_usage = item["containers"][0]["usage"]["memory"]

            # Atualiza as métricas no Prometheus
            cpu_usage_metric.labels(pod_name=pod_name).set(cpu_usage)
            memory_usage_metric.labels(pod_name=pod_name).set(memory_usage)

    except client.exceptions.ApiException as e:
        print(f"Erro ao buscar métricas dos recursos: {e}")

# Função para escalar um deployment
def scale_deployment(deployment_name, namespace, replicas):
    """
    Função que escala (aumenta ou diminui o número de réplicas) de um deployment.
    """
    config.load_kube_config()
    v1 = client.AppsV1Api()

    deployment = v1.read_namespaced_deployment(
        name=deployment_name,
        namespace=namespace
    )
    deployment.spec.replicas = replicas
    v1.patch_namespaced_deployment(
        name=deployment_name,
        namespace=namespace,
        body=deployment
    )
    print(f"Escalonamento de {deployment_name} para {replicas} réplicas realizado com sucesso.")

# Função que monitora as métricas e realiza escalonamento com base no uso de CPU
def monitor_and_scale():
    """
    Monitora o uso de CPU de cada pod exposto via Prometheus e, caso o uso de CPU de qualquer pod
    exceda 80%, aumenta o número de réplicas do deployment.
    """
    url = 'http://localhost:8000/metrics'
    response = requests.get(url)

    for family in text_string_to_metric_families(response.text):
        for sample in family.samples:
            if sample.name == 'k8s_pod_cpu_usage':
                pod_name = sample.labels['pod_name']
                cpu_usage = float(sample.value)

                print(f"Pod: {pod_name}, CPU Usage: {cpu_usage}")

                if cpu_usage > 0.8:  # 80% de uso de CPU
                    print(f"CPU alta detectada para o pod {pod_name}. Escalonando deployment.")
                    scale_deployment('my-deployment', 'default', 5)  # Ajuste o nome e namespace do seu deployment

# Ponto de entrada principal da aplicação
if __name__ == "__main__":
    # Inicia o servidor HTTP para expor as métricas no Prometheus na porta 8000
    start_http_server(8000)

    # Monitora os pods e realiza escalonamento a cada 30 segundos
    while True:
        monitor_pods_resources()
        monitor_and_scale()
        time.sleep(30)  # Verifica a cada 30 segundos

    # Inicia a aplicação Flask
    app.run(debug=True)
