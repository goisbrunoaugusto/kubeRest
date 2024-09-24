"""Códigos para as funçoes de listar, escalonar, monitorar"""
from flask import Flask, jsonify, Response, request
from kubernetes import config, client, watch
import kubernetes.client

app = Flask(__name__)

@app.route("/list", methods=['GET'])
def get_minikube_pod_info():
    """
    Funçao para listar os pods de todos os namespaces
    """
    config.load_kube_config()
    v1 = client.CoreV1Api()
    pod_list = []

    try:
        pods = v1.list_pod_for_all_namespaces()

        for pod in pods.items:
            pod_info = {
                "pod_name" : pod.metadata.name,
                "pod_phase" : pod.status.phase,
                "pod_creation_time" : pod.metadata.creation_timestamp,
                "pod_namespace" : pod.metadata.namespace,
                "pod_image" : pod.spec.containers[0].image
            }

            pod_list.append(pod_info)
        return jsonify(pod_list)

    except client.exceptions.ApiException:
        return Response("Erro ao listar pods", status=500)

@app.route("/scale-up", methods=['POST'])
def scale_up():
    """Método responsável por aumentar o número de réplicas de pods"""
    data = request.get_json()

    config.load_kube_config()
    v1 = client.AppsV1Api()
    try:
        deployment = v1.read_namespaced_deployment(
            name=data.get("deployment-name"),
            namespace=data.get("deployment-namespace")
        )
        deployment.spec.replicas = int(data.get("replicas"))
        v1.patch_namespaced_deployment(
            name=data.get("deployment-name"),
            namespace=data.get("deployment-namespace"),
            body=deployment
        )

        return Response(status=200)

    except client.exceptions.ApiException:
        return Response("Erro ao escalonar deploy", status=500)

@app.route("/scale-down", methods=['POST'])
def scale_down():
    """Método reponsável por diminuir o número de réplicas de pods"""
    data = request.get_json()

    config.load_kube_config()
    v1 = client.AppsV1Api()
    try:
        deployment = v1.read_namespaced_deployment(
            name=data.get("deployment-name"),
            namespace=data.get("deployment-namespace")
        )
        deployment.spec.replicas = 1
        v1.patch_namespaced_deployment(
            name=data.get("deployment-name"),
            namespace=data.get("deployment-namespace"),
            body=deployment
        )

        return Response(status=200)

    except client.exceptions.ApiException:
        return Response("Erro ao diminuir replicas", status=500)

@app.route("/status", methods=['GET'])
def monitor_pods():
    """Funçao para monitorar os pods de um namespace"""
    data = request.get_json()

    config.load_kube_config()
    v1 = client.CoreV1Api()
    w = watch.Watch()
    namespace = data.get('namespace')

    try:
        for event in w.stream(v1.list_namespaced_pod, namespace=namespace, timeout_seconds=60):
            pod = event['object']
            pod_name = pod.metadata.name
            pod_status = pod.status.phase
            event_type = event['type']
            print(f"Event: {event_type} - Pod: {pod_name} - Status: {pod_status}")
    except client.exceptions.ApiException as e:
        print(f"Error no monitoramento de pods: {e}")


def monitor_pods_resources():
    """Funçao para monitorar os recursos dos pods"""
    #Tem que ativar : minikube addons enable metrics-server
    config.load_kube_config()
    custom_metrics_api = client.CustomObjectsApi()
    namespace = 'namespace-example'

    try:
        metrics = custom_metrics_api.list_namespaced_custom_object(
            group="metrics.k8s.io", version="v1beta1", namespace=namespace, plural="pods"
        )
        for item in metrics["items"]:
            pod_name = item["metadata"]["name"]
            cpu_usage = item["containers"][0]["usage"]["cpu"]
            memory_usage = item["containers"][0]["usage"]["memory"]
            print(f"Pod: {pod_name} - CPU Usage: {cpu_usage} - Memory Usage: {memory_usage}")
    except client.exceptions.ApiException as e:
        print(f"Error fetching resource metrics: {e}")


if __name__ == "__main__":
    app.run(debug=True)
