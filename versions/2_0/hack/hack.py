from optimum.intel.openvino import OVModelForFeatureExtraction
from transformers import AutoTokenizer
from openvino.runtime import Core
import numpy as np

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

# === 1. Export to OpenVINO FP16 (if not already done) ===
model_id = "sentence-transformers/paraphrase-MiniLM-L3-v2"
export_dir = "./openvino_model_fp16"

model = OVModelForFeatureExtraction.from_pretrained(
    model_id,
    export=True,
    compile=False,
    dtype="fp16",
    export_kwargs={
        "input": "input_ids[1,128],attention_mask[1,128]"
    }
)
model.save_pretrained(export_dir)

# === 2. Load Tokenizer ===
tokenizer = AutoTokenizer.from_pretrained(model_id)

# === 3. Tokenize input ===
text = ["The quick brown fox jumps over the lazy dog."]
tokens = tokenizer(text, padding="max_length", truncation=True, max_length=128, return_tensors="np")

# === 4. Run Inference with OpenVINO Runtime on NPU ===
core = Core()
model = core.read_model(f"{export_dir}/openvino_model.xml")
compiled_model = core.compile_model(model, "AUTO")  # try "AUTO" if NPU fails

infer_request = compiled_model.create_infer_request()

# === 5. Prepare Input Tensors ===
input_ids_tensor = tokens["input_ids"]
attention_mask_tensor = tokens["attention_mask"]

infer_request.set_tensor(compiled_model.input("input_ids"), input_ids_tensor)
infer_request.set_tensor(compiled_model.input("attention_mask"), attention_mask_tensor)

# === 6. Inference ===
infer_request.infer()
output_tensor = infer_request.get_tensor(compiled_model.output(0))
output = output_tensor.data  # shape: [1, seq_len, hidden_size]

# === 7. Extract [CLS] Embedding ===
cls_embedding = output[0][0]  # assuming [CLS] is at index 0
print("CLS Embedding (first 5 dims):", cls_embedding[:5])
