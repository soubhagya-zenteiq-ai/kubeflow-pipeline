# 🛠️ Infrastructure & Environment Guide

This document details the underlying Kubernetes environment for the Scalable RAG Knowledge Factory.

---

## 🏗️ Storage Architecture (Minikube)

We use **HostPath** Persistent Volumes to allow high-speed access to massive `.gguf` model files and large PDF datasets without bundling them into Docker images.

### 1. Volume Definition (`infra/rag-volumes.yaml`)
We skip the default StorageClass to force binding to our local host machine.

```yaml
# Data Volume: /mnt/data
# Model Volume: /mnt/models
kubectl apply -f infra/rag-volumes.yaml
```

### 2. Host-Side Initialization
Before running the pipeline, you must prepare the directories inside the Minikube node:
```bash
minikube ssh "sudo mkdir -p /mnt/data/batch_1 /mnt/data/batch_2 /mnt/models && sudo chmod -R 777 /mnt/data /mnt/models"
```

### 3. Mounting Local Data
Run these in separate terminals to "tunnel" your local machine files into the cluster:
```bash
# Sync local PDFs
minikube mount /home/zenteiq/Documents/Learnings/rag-factory-pipeline/data:/mnt/data

# Sync local GGUF Models
minikube mount /home/zenteiq/Documents/test-embed/gen_embed_prod/models:/mnt/models
```

---

## 🛰️ Networking & Services

### Local Registry (@Port 5000)
Used to bridge your local Docker daemon with the internal Kubernetes image puller.
```bash
# Enable & Forward
minikube addons enable registry
kubectl port-forward -n kube-system service/registry 5000:80
```

### SeaweedFS Artifact Storage
The pipeline stores artifacts (CSVs, logs) in SeaweedFS. We patched the service to ensure KFP can communicate over port 9000.
```bash
# Port mapping for S3 compatibility
kubectl patch svc seaweedfs -n kubeflow --type=merge -p '{"spec":{"ports":[{"name":"fixed-s3","port":9000,"protocol":"TCP","targetPort":8333}]}}'
```

---

## 🛡️ Security Policies

### Argo Global Policy
Modified to allow system containers (init/wait) to run while adhering to `runAsNonRoot` policies.
```bash
kubectl patch cm workflow-controller-configmap -n kubeflow --type=merge -p '{"data":{"executor":"imagePullPolicy: IfNotPresent\nsecurityContext:\n  runAsNonRoot: false\n  runAsUser: 0\n"}}'
```

### Pod Level Security
All components in `pipeline_definition.py` are configured with:
- `run_as_non_root=True`
- `run_as_user=1000`
