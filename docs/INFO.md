- **[README.md](README.md)**: Main entry point & build guide.
- **[INFRA.md](INFRA.md)**: Technical guides for Volumes, Mounts, and PVCs.
- **[FIX.md](FIX.md)**: Historical troubleshooting and recovery playbook.
- **[INFO.md](INFO.md)**: (You are here) Deep-dive into architecture, data flow, and design logic.

> [!NOTE]
> **The 100-Word Blueprint:**
> This industrial-grade pipeline transforms raw PDFs into AI-ready intelligence using Kubeflow orchestration on Minikube. PDFs are processed in parallel batches (`ParallelFor`) where workers clean text and generate 1024-dimensional embeddings using CPU-optimized GGUF models. Data flows between pods as KFP CSV artifacts, stored temporarily in Persistent Volumes. Finally, a Liquid Foundation Model (LFM) audits every chunk for quality. You can monitor metadata in the Kubeflow UI and download refined vectors directly from the artifacts tab. The entire system is GPU-free, utilizing 4-bit quantization and horizontal scaling to process massive datasets on standard Ubuntu hardware.

---

## 🌊 The End-to-End Workflow

The system operates as a **Directed Acyclic Graph (DAG)** orchestrated by Kubeflow. Here is how a single document travels through the factory:

1.  **Trigger**: You define a list of folders (batches) in the Kubeflow UI.
2.  **Parallelization**: The orchestrator clones the pipeline logic across $N$ worker pods simultaneously.
3.  **Ingestion**: PDFs are cleaned and converted into structured text.
4.  **Embedding**: Text chunks are converted into 1024-dimensional vectors.
5.  **Evaluation**: An "LLM-as-a-Judge" audits the quality of the data.

---

## 📂 Project Anatomy (File-by-File)

Here is the structural breakdown of the Knowledge Factory:

```text
rag-factory-pipeline/
├── components/           # Logic for individual pipeline steps
│   ├── ingestion/        # Cleaning and extraction logic (Dockerized)
│   ├── embedding/        # GGUF vector generation (Dockerized)
│   └── evaluation/       # LLM judge quality audit (Dockerized)
├── pipeline/             # KFP Orchestration layer
│   ├── pipeline_def.py   # Python DSL defining the DAG
│   ├── compiler.py       # Converts Python DSL into YAML spec
│   ├── config.yaml       # Central configuration for paths & params
│   └── submit_run.py     # CLI tool to trigger runs programmatically
├── infra/                # Kubernetes configuration
│   └── k8s_volumes.yaml  # Persistent Volume Claims for Data/Models
├── data/                 # Sample input PDF documents
├── notebooks/            # Experimental prototyping (.ipynb)
├── pyproject.toml        # Universal Python dependency management (uv)
├── rag_factory_spec.yaml # The final compiled spec for Kubeflow
└── README.md             # High-level project overview
```

## 🛠️ Component Deep-Dive

### 1. The Ingestion Engine (The Cleaner)
*   **Input**: Raw `.pdf` files from `/mnt/data/{batch_name}`.
*   **Logic**: 
    *   Uses `pypdf` to extract text.
    *   **Cleanup**: Removes non-ASCII characters, standardizes whitespaces, and splits text into manageable "semantic chunks."
*   **Output**: A structured `.csv` file containing `chunk_id`, `text`, and `metadata`.

### 2. The Mathematician (Embedding Generation)
This is the most compute-intensive part of the system.
*   **The Model**: We use **Qwen3-VL-2B (Q4_K_M GGUF)**.
*   **The CPU Strategy**: Instead of heavy PyTorch/CUDA, we use `llama-cpp-python`. This allows us to run 4-bit quantized models that fit entirely in system RAM and utilize AVX-512 CPU instructions for math.
*   **Storage**: Each text chunk is passed through the model to generate a high-dimensional vector. These vectors represent the "meaning" of the text in mathematical space.

### 3. The Quality Gate (LLM-as-a-Judge)
Before data is indexed, it must pass an audit.
*   **The Model**: **LFM-2.5-1.2B (Q8_0 GGUF)**.
*   **Logic**: The judge reads the extracted text and assigns a score (1-10) based on readability, coherence, and informational density.
*   **Purpose**: Prevents "garbage-in, garbage-out" by filtering out corrupted PDF extractions or irrelevant noise.

---

## 📦 Data Handling & Persistence

### How is data passed between pods?
In Kubernetes, pods are ephemeral (they die after the task). We solve data persistence using two methods:

1.  **Persistent Volume Claims (PVC)**: 
    *   **`rag-data-pvc`**: Where your input PDFs and output CSVs live.
    *   **`rag-models-pvc`**: A massive read-only volume where the GGUF models are stored. This avoids downloading 5GB models every time a pod starts.
    *   **Pro-Tip (KFP v2 Driver)**: Within a `ParallelFor` loop, the KFP v2 driver cannot resolve parent pipeline parameters for volume names. We use hardcoded string literals for PVC names to ensure child DAGs can mount local hostpaths reliably.

2.  **KFP Artifacts (SeaweedFS)**: 
    *   Kubeflow tracks output files via S3-compatible storage (SeaweedFS). 
    *   We utilize **Port 9000** for the artifact repository to match the internal Minio/S3 standard, mapped to SeaweedFS's internal port 8333.
    *   When Component A finishes, it tells Component B: *"Here is the path to the CSV I just created."*

---

## 📊 Batch Utilization (`ParallelFor`)

The system uses **Horizontal Scaling**. If you have 1000 PDFs, you don't process them one by one. 
*   **Batching**: You divide the PDFs into sub-folders (`batch_1`, `batch_2`, etc.).
*   **Orchestration**: Kubeflow's `dsl.ParallelFor` sees these folders and spins up an unique set of pods for **each folder**.
*   **Concurrency**: If your cluster has 10 nodes, you can process 10 batches at the exact same time.

---

## 🕵️ Where to see the Output?

1.  **Kubeflow UI (Visual)**: 
    *   Click on a completed node (e.g., `evaluation-op`).
    *   Go to the **Input/Output** tab.
    *   You can see the generated `.csv` artifacts and download them directly from the UI.
2.  **Pod Logs (Technical)**:
    *   Click the **Logs** tab in the UI to see the real-time inference speed (tokens per second) of the GGUF models.
3.  **The Filesystem**:
    *   The final processed intelligence is stored back in your `rag-data-pvc`, accessible via the host machine for indexing into a Vector DB like Qdrant or Milvus.

---

## 🚀 Why this is "FAANG-Level" Design
- **Decoupled Architecture**: You can swap the Embedding model (Qwen) for any other GGUF model without changing the pipeline logic.
- **Resource Aware**: It handles multi-gigabyte models on standard CPU laptop/server hardware.
- **Lineage Tracking**: Every vector has a clear path back to the exact PDF page it came from.

---

### Key Folders & Files:
*   **`components/`**: Contains the source code, `requirements.txt`, and `Dockerfile` for each task. These are pushed as independent images to `localhost:5000`.
*   **`pipeline/compiler.py`**: Your main execution script. Run this to generate the `rag_factory_spec.yaml`.
*   **`pipeline/config.yaml`**: Stores sensitive or variable information like registry URLs and PVC names in one easy-to-edit place.
*   **`pipeline/submit_run.py`**: A power-user script that allows you to start a Kubeflow run directly from your terminal.
*   **`notebooks/`**: Contains Jupyter experiments where you can test your PDF extraction or LLM logic before moving it into a component.
*   **`infra/k8s_volumes.yaml`**: The "Glue." It defines how the host machine shares GGUF models and PDFs with the Kubernetes pods.
*   **`rag_factory_spec.yaml`**: The output artifact. This is the only file you need to upload to the Kubeflow UI to run the factory.

