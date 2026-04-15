from kfp import compiler
from pipeline_definition import rag_pipeline

if __name__ == "__main__":
    # This compiles the Python code into a Kubernetes-compatible YAML spec
    pipeline_filename = "rag_factory_spec.yaml"
    compiler.Compiler().compile(
        pipeline_func=rag_pipeline,
        package_path=pipeline_filename
    )
    print(f"✅ Success! Pipeline compiled to {pipeline_filename}")