from optimum.intel.openvino import OVModelForFeatureExtraction
from transformers import AutoTokenizer

model_name="sentence-transformers/paraphrase-MiniLM-L3-v2"
# Load the model
model = OVModelForFeatureExtraction.from_pretrained(
    model_name,
    export=True,              # Triggers ONNX → OpenVINO export
    compile=False,            # Prevent compiling immediately
    dtype="fp16"              # Convert to FP16 precision
)

# Save the OpenVINO model to disk
model.save_pretrained(f"{model_name.replace('/','_')}_openvino_fp16", export=True)
