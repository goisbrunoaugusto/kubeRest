"""Códigos para as funçoes de listar, escalonar, monitorar"""
from flask import Flask
from kubernetes import config, client
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

if __name__ == "__main__":
    #get_minikube_pod_info()
    create_new_pod()
    get_minikube_pod_info()