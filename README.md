This **README.md** is designed to look professional for your GitHub and portfolio. It clearly explains the technical complexity of building an asynchronous, parallel AI pipeline on Ubuntu.

-----

# 🏭 Scalable RAG Knowledge Factory

### *High-Throughput PDF-to-Intelligence Pipeline*

## 📖 Project Overview

This project is an industrial-grade **Retrieval-Augmented Generation (RAG)** ingestion engine. Instead of a simple script that reads one PDF at a time, this is a **distributed factory** built on **Kubernetes (Minikube)** and orchestrated by **Kubeflow Pipelines (KFP)**.

The system takes hundreds of unstructured PDFs, processes them in parallel across multiple containerized workers, generates high-quality semantic embeddings using quantized **GGUF** models, and passes them through an **LLM-as-a-Judge** quality gate.

-----

## 🛠️ Technical Stack

| Category | Tools / Frameworks |
| :--- | :--- |
| **OS** | Ubuntu 22.04 LTS |
| **Orchestrator** | Kubeflow Pipelines (KFP) |
| **Containerization** | Docker, Minikube (Local Registry @ port 5000) |
| **AI Runtime** | `llama-cpp-python` (GGUF optimized) |
| **Models** | **Embedding:** `Qwen3-VL-2B-Q4_K_M` <br> **Judge:** `LFM-2.5-1.2B-Instruct-Q8_0` |
| **Package Manager** | `uv` (Fastest Python resolver/installer) |
| **Data Logic** | `PyPDF`, `Pandas`, `NumPy` |

-----

## 🏗️ Architecture & Workflow

### 🗺️ System Blueprint
```text
User → Kubeflow UI → KFP Orchestrator → Argo Workflow
                                             ↓
                                    [ Parallel Worker Pods ]
                                             ↓
        [ Local Registry @ 5000 ] ←------- Port Forwarding
                                             ↓
        [ Data/Model Storage ] ←---------- PVC (Persistent Vol)
```

### 1\. Parallel Ingestion (The Slicer)

  * **What:** Uses `dsl.ParallelFor` to split PDF batches into concurrent pods.
  * **Why:** Scalability. If one PDF is corrupted, the rest of the pipeline continues.
  * **Logic:** Extracts raw text, removes non-ASCII artifacts, and standardizes whitespace.

### 2\. Semantic Embedding (The Mathematician)

  * **What:** Runs a quantized Qwen-VL model via `llama-cpp-python`.
  * **Why:** Optimized for **CPU-only** Ubuntu environments. It converts text chunks into high-dimensional vectors.
  * **Feature:** Uses **HostPath Volume Mounts** to allow pods to access massive model files (GGUF) stored on the host drive without bloating Docker images.

### 3\. LLM-as-a-Judge (The Quality Gate)

  * **What:** Uses the **Liquid Foundation Model (LFM 1.2B)** to audit data quality.
  * **Why:** Ensures only high-quality, readable text enters the vector database. It assigns a "quality score" to each chunk.

### 4\. Local Development Lifecycle

  * **Build:** Multi-stage Docker builds with `build-essential` and `uv` for speed.
  * **Push:** Syncs images to the local `localhost:5000` registry.
  * **Compile:** Uses a Python-based compiler to generate Kubernetes YAML specs.

-----

## 📂 Project Structure

```text
rag-factory-pipeline/
├── components/           # Logic for each step (Dockerized)
│   ├── ingestion/        # PDF cleaning & extraction
│   ├── embedding/        # Qwen-VL GGUF vector generation
│   └── evaluation/       # LFM-1.2B Quality Judge
├── pipeline/             # KFP Orchestration logic
│   ├── pipeline_def.py   # The DSL graph definition
│   └── compiler.py       # Python-to-YAML compiler
├── infra/                # K8s configurations & secrets
├── DAEMON.md             # Docker/Registry setup commands
└── README.md             # You are here
```

-----

## 🚀 Key Highlights for Your Resume

  * **Distributed Computing:** Built a parallel processing system that scales horizontally across Kubernetes nodes.
  * **Resource Optimization:** Implemented 4-bit and 8-bit quantized (GGUF) models to run complex LLM tasks on standard CPU hardware.
  * **Infrastructure as Code (IaC):** Managed the full DevOps lifecycle from Dockerizing Python components to deploying via KFP YAML specs.
  * **Data Quality Engineering:** Integrated an automated LLM evaluation step to ensure data lineage and index integrity.

-----

## 🛠️ How to Run the Intelligence Factory

Follow these steps to initialize the environment and run your first parallel ingestion pipeline.

### 1. Initialize the Infrastructure
Ensure Minikube and the local registry are ready:
```bash
# Start Minikube with Docker driver
minikube start --driver=docker

# Enable the registry addon
minikube addons enable registry

# Port-forward registry (keep this running in separate terminal)
kubectl port-forward -n kube-system service/registry 5000:80

> [!WARNING]
> **Keep the port-forward process running!** If it stops, Kubernetes will lose the connection to your local registry and fail with `ImagePullBackOff`.

# Apply the model/data storage configuration
kubectl apply -f infra/k8s_volumes.yaml
```

> [!IMPORTANT]
> **Do NOT use localhost:32000 or socat bridge.**
> Minikube runs inside a separate VM/container. "localhost" inside Kubernetes is NOT your host machine. Use the built-in Minikube registry (localhost:5000 via port-forward) to ensure images are accessible to pods.

### 2. Pre-load KFP "Engine" Images
To ensure the pipeline runs smoothly offline, load the core engine images into Minikube:
```bash
# Pull and load the Argo executor
docker pull quay.io/argoproj/argoexec:v3.4.16
minikube image load quay.io/argoproj/argoexec:v3.4.16
# Tag locally if needed for specific KFP versions
# minikube ssh "docker tag quay.io/argoproj/argoexec:v3.4.16 gcr.io/ml-pipeline/argoexec:v3.4.16-license-compliance"
```

### 3. Build & Push Your Components
Each worker is containerized. Build and push them to your local registry (`localhost:5000`):

```bash
# 1. Build ALL components (DO NOT skip the localhost:5000/ prefix)
docker build -t localhost:5000/rag-ingestion:latest ./components/ingestion
docker build -t localhost:5000/rag-embedding:latest ./components/embedding
docker build -t localhost:5000/rag-evaluation:latest ./components/evaluation

# 2. Verify images exist in your local daemon BEFORE pushing
docker images | grep rag

# 3. Push to registry (ensure port-forward to 5000 is running)
docker push localhost:5000/rag-ingestion:latest
docker push localhost:5000/rag-embedding:latest
docker push localhost:5000/rag-evaluation:latest
```

> [!CAUTION]
> **CRITICAL:** If you build images without the `localhost:5000/` prefix, Kubernetes WILL FAIL with `ImagePullBackOff` or `ImageInspectError`. The prefix tells Kubernetes to look for the image in your local registry bridge.


### 4. Compile & Launch the Pipeline
1.  **Compile**: Turn the Python DSL into a Kubernetes spec:
    ```bash
    uv run pipeline/compiler.py
    ```
2.  **Access Dashboard**: Open a "tunnel" to reach the UI:
    ```bash
    kubectl port-forward -n kubeflow svc/ml-pipeline-ui 8080:80
    ```
3.  **Run**: Open `http://localhost:8080`, upload `rag_factory_spec.yaml`, and follow the **UI Guide** below.

*Tip: If `kubectl` errors out with "microk8s not found", use `./kubectl` (the binary in this folder) instead.*

-----

## 🖥️ Kubeflow UI Guide (Step-by-Step)

Follow these steps to launch your first RAG ingestion run:

1.  **Pipelines**: On the left sidebar, click **Pipelines**.
2.  **Upload**: Click **[+ Upload pipeline]** -> **Upload a file** -> Select `rag_factory_spec.yaml`.
3.  **Create Run**: Once uploaded, click the **[+ Create run]** button.
4.  **Configuration**:
    *   **Experiment**: Create a new one named `RAG-Factory-Tests`.
    *   **Parameters**: Keep the defaults unless you have specific data folders in your PVC.
5.  **Start**: Click **Start**. The graph will turn green as each AI component finishes.

### 5. Monitoring
To watch the pods spinning up in real-time:
```bash
watch ./kubectl get pods -n kubeflow | grep "scalable-rag"
```

-----

## 🧪 Debugging Image Issues

If pods fail with `ImagePullBackOff` or `ImageInspectError`:

1. **Check Events**:
   ```bash
   ./kubectl describe pod <pod-name> -n kubeflow
   ```
2. **Verify Registry State**:
   Check if the registry actually contains your images:
   ```bash
   curl http://localhost:5000/v2/_catalog
   ```
3. **Check Inside Minikube**:
   Ssh into the cluster to see if the images were successfully pulled:
   ```bash
   minikube ssh "docker images | grep rag"
   ```
4. **Re-Push**: Ensure the port-forward to port 5000 is still running, then push again:
   ```bash
   docker push localhost:5000/rag-ingestion:latest
   ```

> [!TIP]
> **Why am I seeing "Cannot find context" (MLMD error) in the UI?**
> This usually happens because your image failed to pull. If the pod never runs, it never writes metadata to the database. Kubeflow UI crashes when it tries to read metadata from a run that never technically started. **Fix your images first!**


### ❗ Common Failure Modes

| Error | Likely Cause |
| :--- | :--- |
| `ImagePullBackOff` | Registry port-forward isn't running. |
| `ImageInspectError` | Image not built or wrong tag in code. |
| `Pending` | Missing PVCs or not enough CPU/RAM in Minikube. |
| `CrashLoopBackOff` | KFP Driver/Argo mismatch or Python script crash. |

-----

## 🧠 Big Picture & Resume Impact

By building this, you have implemented several "FAANG-level" infrastructure patterns:
- **Distributed Pipelines**: Horizontal scaling for heavy ML workloads.
- **IaC (Infrastructure as Code)**: Managing clusters and registries via scripts.
- **Resource Optimization**: Quantized inference on restricted hardware.

**Resume Bullet Point:**
> *Built a distributed RAG ingestion system using Kubeflow Pipelines and Kubernetes, enabling parallel processing of unstructured data with local container registry integration and CPU-optimized LLM inference.*

-----

## 🚀 Alternative: Build Directly in Minikube (No Registry Mode)

Instead of pushing to a registry, you can build images directly inside Minikube's Docker environment. This avoids the registry system entirely:

1. **Point Docker to Minikube**:
   ```bash
   eval $(minikube docker-env)
   ```
2. **Build**:
   ```bash
   docker build -t rag-ingestion:latest ./components/ingestion
   docker build -t rag-embedding:latest ./components/embedding
   docker build -t rag-evaluation:latest ./components/evaluation
   ```
3. **Usage**: In your `pipeline_definition.py`, remove the `localhost:5000/` prefix and set `image_pull_policy` to `Never`.