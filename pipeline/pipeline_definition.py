from kfp import dsl
from kfp import kubernetes
from kfp.dsl import Dataset, Input, Output, Artifact

# --- Step 1: Component Definitions ---

@dsl.container_component
def ingestion_op(
    input_dir: str,
    output_csv: Output[Dataset]
):
    return dsl.ContainerSpec(
        image='localhost:5000/rag-ingestion:latest',
        command=['python', 'main.py'],
        args=['--input_dir', input_dir, '--output_file', output_csv.path]
    )

@dsl.container_component
def embedding_op(
    input_csv: Input[Dataset],
    model_path: str,
    output_csv: Output[Dataset]
):
    return dsl.ContainerSpec(
        image='localhost:5000/rag-embedding:latest',
        command=['python', 'main.py'],
        args=[
            '--input_csv', input_csv.path,
            '--output_csv', output_csv.path,
            '--model_path', model_path
        ]
    )

@dsl.container_component
def evaluation_op(
    input_csv: Input[Dataset],
    model_path: str,
    output_report: Output[Artifact]
):
    return dsl.ContainerSpec(
        image='localhost:5000/rag-evaluation:latest',
        command=['python', 'main.py'],
        args=[
            '--input_csv', input_csv.path,
            '--output_report', output_report.path,
            '--model_path', model_path
        ]
    )

# --- Step 2: Pipeline Orchestration ---

@dsl.pipeline(
    name='scalable-rag-knowledge-factory',
    description='A parallel pipeline for processing PDFs into vectors using Qwen and LFM models.'
)
def rag_pipeline(
    batch_list: list = ['batch_1', 'batch_2'],
    # Hardcode these to match the PVCs for maximum stability in local env
    models_pvc: str = 'rag-models-pvc',
    data_pvc: str = 'rag-data-pvc'
):
    with dsl.ParallelFor(batch_list) as batch:
        
        # 1. Ingestion
        ingest = ingestion_op(input_dir=f"/mnt/data/{batch}")
        kubernetes.set_image_pull_policy(ingest, 'IfNotPresent')
        
        # Mount the data folder
        kubernetes.mount_pvc(
            ingest,
            pvc_name='rag-data-pvc',
            mount_path='/mnt/data'
        )
        
        # 2. Embedding
        embed = embedding_op(
            input_csv=ingest.outputs['output_csv'],
            model_path='/mnt/models/qwen3-vl-embedding-2b-q4_k_m.gguf'
        )
        kubernetes.set_image_pull_policy(embed, 'IfNotPresent')
        embed.set_cpu_request("2")
        embed.set_memory_request("4Gi")
        
        # 3. Evaluation
        evaluate = evaluation_op(
            input_csv=ingest.outputs['output_csv'],
            model_path='/mnt/models/LFM2.5-1.2B-Instruct-Q8_0.gguf'
        )
        kubernetes.set_image_pull_policy(evaluate, 'IfNotPresent')
        evaluate.set_cpu_request("1")
        evaluate.set_memory_request("2Gi")

        # Shared Mount for Models
        for task in [embed, evaluate]:
            kubernetes.mount_pvc(
                task,
                pvc_name='rag-models-pvc',
                mount_path='/mnt/models'
            )