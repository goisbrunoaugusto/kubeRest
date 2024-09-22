"""Códigos para as funçoes de listar, escalonar, monitorar"""
from flask import Flask
from kubernetes import config, client, watch
import kubernetes.client

app = Flask(__name__)


def get_minikube_pod_info():
    """
    Funçao para listar os pods de todos os namespaces
    """
    config.load_kube_config()
    v1 = client.CoreV1Api()

    try:
        pods = v1.list_pod_for_all_namespaces()

        for pod in pods.items:
            pod_name = pod.metadata.name
            pod_status = pod.status.conditions[-1].type
            pod_creation_time = pod.metadata.creation_timestamp

            print(f"\nNode Name: {pod_name}")
            print(f"Status: {pod_status}")
            print(f"Creation Time: {pod_creation_time}")

    except client.exceptions.ApiException as e:
        print(f"An error occurred while retrieving nodes: {e}")

def create_new_pod():
    """
    Funçao para criar um novo pod
    """
    config.load_kube_config()
    pod = client.V1Pod(
    metadata=client.V1ObjectMeta(name="my-python-pod"),
    spec=client.V1PodSpec(
        containers=[
            client.V1Container(
                name="my-python-container",
                image="nginx",  # Example image
                ports=[client.V1ContainerPort(container_port=80)],
            )
        ]
    ),
    )
    try:
        response = client.CoreV1Api().create_namespaced_pod(
            body=pod, namespace="namespace-example"
        )
    except client.exceptions.ApiException as e:
        print(f"An error occurred while creating a pod: {e}")

def monitorar_pods():
    """Funçao para monitorar os pods de um namespace"""
    config.load_kube_config()
    v1 = client.CoreV1Api()
    w = watch.Watch()
    namespace = 'namespace-example'
    print(f"Monitorando os pods: {namespace}")
    
    try:
        for event in w.stream(v1.list_namespaced_pod, namespace=namespace, timeout_seconds=60):
            pod = event['object']
            pod_name = pod.metadata.name
            pod_status = pod.status.phase
            event_type = event['type']
            print(f"Event: {event_type} - Pod: {pod_name} - Status: {pod_status}")
    except Exception as e:
        print(f"Error monitoring pods: {e}")
        
def monitorar_recursos_dos_pods():
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
    except Exception as e:
        print(f"Error fetching resource metrics: {e}")


if __name__ == "__main__":
    #get_minikube_pod_info()
    # create_new_pod()
    # get_minikube_pod_info()
    #monitorar_pods()
    monitorar_recursos_dos_pods()
