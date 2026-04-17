# Kubeflow Pipeline Troubleshooting Log - April 17, 2026

This is the exact, step-by-step history of commands used to fix the RAG Factory Pipeline.

---

## 1. MySQL User & Permissions Repair
**The Problem:** Internal database user `mlpipeline` was missing and `metadb` was uninitialized.

**Exact Commands Ran:**
```bash
# Verify users
kubectl exec -it $(kubectl get pods -n kubeflow -l app=mysql -o name) -n kubeflow -- mysql -u root -e "SELECT user, host FROM mysql.user;"

# Create User and Schemas
kubectl exec -it $(kubectl get pods -n kubeflow -l app=mysql -o name) -n kubeflow -- mysql -u root -e "
CREATE USER 'mlpipeline'@'%' IDENTIFIED WITH mysql_native_password BY 'mlpipeline';
CREATE DATABASE IF NOT EXISTS mlmetadata;
GRANT ALL PRIVILEGES ON mlmetadata.* TO 'mlpipeline'@'%';
CREATE DATABASE IF NOT EXISTS mlpipeline;
GRANT ALL PRIVILEGES ON mlpipeline.* TO 'mlpipeline'@'%';
CREATE DATABASE IF NOT EXISTS metadb;
GRANT ALL PRIVILEGES ON metadb.* TO 'mlpipeline'@'%';
FLUSH PRIVILEGES;"
```

---

## 2. Infrastructure & Networking Synchronization
**The Problem:** Container image/security mismatch and SeaweedFS port conflict.

**Exact Commands Ran:**
```bash
# Sync MySQL Secret (base64 for 'mlpipeline')
kubectl patch secret mysql-secret -n kubeflow -p '{"data":{"username":"bWxwaXBlbGluZQ==","password":"bWxwaXBlbGluZQ=="}}'

# Fix Argo Executor Security (Resolving Init:CreateContainerConfigError)
kubectl patch cm workflow-controller-configmap -n kubeflow --type=merge -p '{"data":{"executor":"imagePullPolicy: IfNotPresent\nsecurityContext:\n  runAsNonRoot: false\n  runAsUser: 0\n"}}'

# Fix SeaweedFS S3 Port (9000 -> 8333)
kubectl patch svc seaweedfs -n kubeflow --type=merge -p '{"spec":{"ports":[{"name":"fixed-s3","port":9000,"protocol":"TCP","targetPort":8333}]}}'

# Restart Services
kubectl rollout restart deployment metadata-grpc-deployment -n kubeflow
kubectl rollout restart deployment ml-pipeline -n kubeflow
kubectl rollout restart deployment workflow-controller -n kubeflow
```

---

## 3. Persistent Storage & Hostpath Mounts
**The Problem:** Pods stuck in `Pending` due to missing `runAsNonRoot` compliance and missing local data.

**Exact Commands Ran (Initial Dir Creation):**
```bash
minikube ssh "sudo mkdir -p /mnt/data/batch_1 /mnt/data/batch_2 /mnt/models && sudo chmod -R 777 /mnt/data /mnt/models"
```

**Exact Mount Commands (Run in separate terminals):**
```bash
# Mount Batch Data
minikube mount /home/zenteiq/Documents/Learnings/rag-factory-pipeline/data:/mnt/data

# Mount Model Weights
minikube mount /home/zenteiq/Documents/test-embed/gen_embed_prod/models:/mnt/models
```

---

## 4. Pipeline Compilation & Submission
**Exact Commands Ran:**
```bash
# Compile with UV
uv run --with kfp python3 pipeline/compiler.py

# Submit Run
uv run --with kfp python3 pipeline/submit_run.py

# Monitor Progress
kubectl get pods -n kubeflow -l pipeline/runid -w
```

---

## 5. Summary Table

| 🧩 Component | 🛠️ Exact Fix |
| :--- | :--- |
| **Database** | Created `mlpipeline` user and `metadb` database via `kubectl exec`. |
| **Security** | Patched `workflow-controller-configmap` to allow root executor. |
| **Pipeline Code** | Hardcoded PVC strings in `ParallelFor` to assist V2 Driver. |
| **Volumes** | Recreated PV/PVCs in `kubeflow` namespace with `storageClassName: ""`. |
| **Network** | Mapped `seaweedfs` service port 9000 to internal target 8333. |

---
**Status at Close:** End-to-end pipeline STABLE and Generation logic executing on CPU.
