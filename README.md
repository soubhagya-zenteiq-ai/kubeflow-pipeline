# 🏭 Scalable RAG Knowledge Factory
### *High-Throughput PDF-to-Intelligence Pipeline*

---

## 📖 Project Overview
This project is an industrial-grade **Retrieval-Augmented Generation (RAG)** ingestion engine orchestrated by **Kubeflow Pipelines (KFP)** on **Kubernetes**. It processes large-scale PDF batches into semantic embeddings using quantized **GGUF** models optimized for CPU.

### 🏛️ Documentation Map
- **[README.md](README.md)**: Your main entry point. Contains architecture overview, quick-start commands, and build instructions.
- **[INFRA.md](docs/INFRA.md)**: The technical blueprints. Details on Minikube setup, volume management (PVCs), and network port mapping.
- **[FIX.md](docs/FIX.md)**: The troubleshooting playbook. A historical log of every command used to repair the MySQL database, security contexts, and metadata connection.
- **[INFO.md](docs/INFO.md)**: The deep-dive architecture. Explains the "Logic" of the pipeline, data flow, and quantized model strategy.

---

## 🚀 Quick Start (Commands)

### 1. Ready the Environment
```bash
# Start Minikube
minikube start --driver=docker

# Load core KFP images to prevent PullBackOff
docker pull quay.io/argoproj/argoexec:v3.7.3
minikube image load quay.io/argoproj/argoexec:v3.7.3

# Apply Infrastructure (Volumes & Storage)
kubectl apply -f infra/rag-volumes.yaml
```

### 2. Prepare the Store (Mounts)
*Keep these running in separate terminals:*
```bash
minikube mount /home/zenteiq/Documents/Learnings/rag-factory-pipeline/data:/mnt/data
minikube mount /home/zenteiq/Documents/test-embed/gen_embed_prod/models:/mnt/models
```

### 3. Build & Push Components
```bash
# Build (Use the localhost:5000 registry prefix!)
docker build -t localhost:5000/rag-ingestion:latest ./components/ingestion
docker build -t localhost:5000/rag-embedding:latest ./components/embedding
docker build -t localhost:5000/rag-evaluation:latest ./components/evaluation

# Push to Registry
docker push localhost:5000/rag-ingestion:latest
docker push localhost:5000/rag-embedding:latest
docker push localhost:5000/rag-evaluation:latest
```

### 4. Compile & Launch
We use `uv` for ultra-fast dependency management and execution.
```bash
# Compile the pipeline definition
uv run --with kfp python3 pipeline/compiler.py

# Submit the run to Kubeflow
uv run --with kfp python3 pipeline/submit_run.py
```

---

## 🛠️ Technical Workflow

### 1\. Parallel Ingestion
Uses `dsl.ParallelFor` to split PDF batches into concurrent pods. Scalable and crash-tolerant.

### 2\. Semantic Embedding
Runs quantized **Qwen-VL** via `llama-cpp-python`. Optimized for CPU. Uses **HostPath PVCs** to access massive model weights without bloating images.

### 3\. LLM-as-a-Judge
Uses **LFM-1.2B** to audit semantic quality before indexing.

---

## 📂 Project Structure
```text
rag-factory-pipeline/
├── components/           # Logic for each step (Dockerized)
├── pipeline/             # KFP Orchestration logic
│   ├── pipeline_def.py   # DSL graph definition (Patched for KFP v2)
│   ├── compiler.py       # Python-to-YAML compiler
│   └── submit_run.py     # Python-to-KFP API submitter
├── infra/                # K8s configurations, PV/PVCs & MySQL fixes
├── FIX.md                # Environment recovery playbook
├── INFRA.md              # Minikube & Storage guide
└── README.md             # High-level overview
```

---

## 🧪 System Monitoring
```bash
# Follow Pipeline Pods
watch kubectl get pods -n kubeflow -l pipeline/runid

# Access UI
kubectl port-forward -n kubeflow svc/ml-pipeline-ui 8080:80
```

---

## 🧠 Resume Impact
- **Distributed Systems**: Implemented horizontal scaling for heavy ML workloads.
- **Resource Optimization**: Quantized inference on restricted CPU hardware.
- **Infrastructure**: Managed the full lifecycle from Registry bridges to PV finalizers.