import { AutoTokenizer } from '@huggingface/transformers';
import { addon as ov } from "openvino-node";


const model_name = "sentence-transformers/paraphrase-MiniLM-L3-v2"
try {

    const tokenizer = await AutoTokenizer.from_pretrained(model_name);
    const tokens = await tokenizer(["testing testing what is up"], {
        padding: true,
        truncation: true,
        return_tensor: "np"
    });
    console.log(tokens);

    // Setup
    const core = new ov.Core();
    console.log(core.getAvailableDevices());

    const model = await core.readModel(`./${model_name.replace("/","_")}_openvino_fp16/openvino_model.xml`);

    // console.log(core.queryModel(model, "NPU"));
    console.log("Model loaded successfully");
    console.log(core.getVersions("NPU")) 
    console.log(core.getProperty("NPU","SUPPORTED_PROPERTIES"))
    console.log(core.getProperty("NPU", "FULL_DEVICE_NAME"))
    console.log(core.getProperty("NPU", "CACHE_DIR"))
    console.log(core.getProperty("CPU", "CACHE_DIR"))
    console.log(core.getProperty("NPU", "RANGE_FOR_ASYNC_INFER_REQUESTS"))

    // core.setProperty({ "ENABLE_DEVICE_NPU": "true"});
    const compiled = await core.compileModel(model, "MULTI:NPU,CPU");


    console.log("Model compiled successfully");
    const infer = compiled.createInferRequest();

    // Tokenized input
    // const inputIds = Array.from(tokens.input_ids.data);
    console.log("Input IDs:", tokens.input_ids.data);
    console.log("Attention Mask:", tokens.attention_mask.data);
    // const inputIds = BigInt64Array.from(tokens.input_ids.tolist().flat(), Number);
    // const attentionMask = BigInt64Array.from(tokens.attention_mask.tolist().flat(), Number);

    const flatIds = Array.from(tokens.input_ids.tolist().flat(), Number);
    const flatMask = Array.from(tokens.attention_mask.tolist().flat(), Number);


    // const inputIds = tokens.input_ids.data
    // const attentionMask = tokens.input_ids.data;
    const inputShape = tokens.input_ids.dims;
    console.log("Input shape:", inputShape);
    const batch = inputShape[0];
    const seqLen = inputShape[1];

    console.log(`Batch: ${batch}, Sequence Length: ${seqLen}`)
    console.log("Input IDs:", flatIds);
    console.log("Attention Mask:", flatMask);
    console.log("Input IDs shape:", tokens.input_ids.dims);
    console.log("Attention Mask shape:", tokens.attention_mask.dims);
    console.log("batch:", batch);

    console.log("seqLen:", seqLen);

    const idsArray = new BigInt64Array(flatIds.map(BigInt));       // `flatIds` is a normal JS array of numbers
    const maskArray = new BigInt64Array(flatMask.map(BigInt));     // same for attention mask

    const idsTensor = new ov.Tensor("i64", [batch, seqLen], idsArray);
    const maskTensor = new ov.Tensor("i64", [batch, seqLen], maskArray);

    // Convert to OV tensors
    // const idsTensor = new ov.Tensor("i32", [batch, seqLen], inputIds);
    // const maskTensor = new ov.Tensor("i32", [batch, seqLen], attentionMask);

    // Inference
    await infer.setInputTensor(0, idsTensor);
    await infer.setInputTensor(1, maskTensor);
    const tokenTypeArray = new BigInt64Array(batch * seqLen).fill(0n);
    const tokenTypeTensor = new ov.Tensor("i64", [batch, seqLen], tokenTypeArray);
    infer.setInputTensor(2, tokenTypeTensor);
    await infer.infer();

    // Output tensor
    const output = await infer.getOutputTensor(0); // shape: [batch, seqLen, hiddenSize]
    console.log("Output shape:", output);

    // Mean pooling
    const outData = output.data;
    console.log("Output data:", outData);
    const hiddenSize = output.dims[2];
    const embeddings = [];

    for (let b = 0; b < batch; b++) {
        const emb = new Float32Array(hiddenSize);
        let valid = 0;

        for (let t = 0; t < seqLen; t++) {
            if (attentionMask[b][t] === 0) continue;
            valid++;
            for (let h = 0; h < hiddenSize; h++) {
                const idx = b * seqLen * hiddenSize + t * hiddenSize + h;
                emb[h] += outData[idx];
            }
        }
        embeddings.push(emb.map(v => v / valid));
    }
    console.log("hi")

    console.log({ embeddings });
} catch (error) {
    console.error("Error:", error);
}
