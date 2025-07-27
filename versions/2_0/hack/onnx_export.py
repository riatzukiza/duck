from optimum.exporters.onnx import main_export

model_id = "sentence-transformers/paraphrase-MiniLM-L3-v2"
output_path = "./onnx_model"

main_export(
    model_name_or_path=model_id,
    output=output_path,
    task="feature-extraction",
    dtype="fp32",  # ONNX must be FP32 initially
    pad_token_id=0,
    max_length=128
)
