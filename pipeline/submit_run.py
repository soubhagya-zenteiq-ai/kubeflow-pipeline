import kfp
from kfp import dsl

def submit_pipeline():
    # Connect to the local API server we just port-forwarded
    client = kfp.Client(host='http://localhost:8080')
    
    pipeline_spec = 'rag_factory_spec.yaml'
    
    print(f"🚀 Submitting pipeline {pipeline_spec} to Kubeflow...")
    
    try:
        run = client.create_run_from_pipeline_package(
            pipeline_file=pipeline_spec,
            arguments={
                'batch_list': ['batch_1', 'batch_2'],
                'models_pvc': 'rag-models-pvc',
                'data_pvc': 'rag-data-pvc'
            },
            run_name='rag-factory-fixed-run'
        )
        print(f"✅ Success! Run created with ID: {run.run_id}")
        print(f"🔗 You can monitor the run status via CLI or once the UI is fixed.")
    except Exception as e:
        print(f"❌ Failed to submit run: {e}")

if __name__ == "__main__":
    submit_pipeline()
