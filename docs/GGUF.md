# Qwen3-VL GGUF Node Guide

The **Qwen3-VL GGUF (2B Thinking)** node targets CPU users and lightweight GPUs by running [`Qwen/Qwen3-VL-2B-Thinking-GGUF`](https://huggingface.co/Qwen/Qwen3-VL-2B-Thinking-GGUF) through [`llama-cpp-python`](https://github.com/ggerganov/llama.cpp/tree/master/bindings/python).

## Requirements
- `llama-cpp-python` built from source with **MMVQ** enabled (official wheels currently miss the Qwen3-VL vision kernels).
- Python 3.10+ and a compiler toolchain that can build llama.cpp (GCC/Clang on Linux, MSVC on Windows).

## Installation Steps
1. Remove any incompatible wheels:
   ```bash
   pip uninstall -y llama-cpp-python
   ```
2. Build from source with MMVQ:
   ```bash
   CMAKE_ARGS="-DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_MMVQ=ON" \
   pip install -U "llama-cpp-python @ git+https://github.com/ggerganov/llama.cpp.git#subdirectory=bindings/python"
   ```
3. (Optional) Verify the build exposes MMVQ kernels:
   ```bash
   python - <<'PY'
   from llama_cpp import Llama
   print("mmvq" in Llama.build_info().get("general", {}).get("features", {}).lower())
   PY
   ```

## Using the Node
1. Add **Qwen3-VL GGUF (2B Thinking)** from the 🧪AILab/QwenVL category.
2. Choose any `.gguf` quantization from the dropdown; the node pulls the live list from Hugging Face.
3. Provide an image (optional) plus your prompt, then execute the workflow.
4. Enable `keep_model_loaded` when reusing the same checkpoint to avoid repeated downloads and initialization.

The node automatically fetches the `.gguf` file and the matching projector weights, persists them under `models/LLM/Qwen-VL/GGUF/`, and streams chat completions through llama.cpp with the `qwen2_vl` template.

## Troubleshooting
- **"MMVQ kernels missing"**: rebuild `llama-cpp-python` with the command above.
- **Slow CPU inference**: try a more aggressive quantization (e.g., `Q3_K_M`) and keep batch sizes small.
- **Projector mismatch**: delete the cached `projector.bin` so the node can redownload the pair.
