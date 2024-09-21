from flask import Flask
from kubernetes import config, client

app = Flask(__name__)


def get_minikube_node_info():
    
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


if __name__ == "__main__":
    get_minikube_node_info()
    