# Qwen3-VL GGUF 节点指南

**Qwen3-VL GGUF (2B Thinking)** 节点通过 [`llama-cpp-python`](https://github.com/ggerganov/llama.cpp/tree/master/bindings/python) 运行 [`Qwen/Qwen3-VL-2B-Thinking-GGUF`](https://huggingface.co/Qwen/Qwen3-VL-2B-Thinking-GGUF)，专为 CPU 与轻量 GPU 场景打造。

## 环境要求
- 必须从源码编译、且启用了 **MMVQ** 的 `llama-cpp-python`（官方 wheel 暂未包含 Qwen3-VL 视觉算子）。详见 [llama-cpp-python 安装与 MMVQ 编译指南](./LLAMA_CPP_INSTALL_zh.md)。
- Python 3.10+，以及可编译 llama.cpp 的本地工具链（Linux: GCC/Clang，Windows: MSVC）。

## 安装步骤
1. 卸载不兼容的 wheel：
   ```bash
   pip uninstall -y llama-cpp-python
   ```
2. 重新编译并启用 MMVQ：
   ```bash
   CMAKE_ARGS="-DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_MMVQ=ON" \
   pip install -U "llama-cpp-python @ git+https://github.com/ggerganov/llama.cpp.git#subdirectory=bindings/python"
   ```
3. （可选）验证构建信息：
   ```bash
   python - <<'PY'
   from llama_cpp import Llama
   print("mmvq" in Llama.build_info().get("general", {}).get("features", {}).lower())
   PY
   ```

## 使用方式
1. 在 🧪AILab/QwenVL 分类中添加 **Qwen3-VL GGUF (2B Thinking)** 节点。
2. 从下拉菜单选择任意 `.gguf` 量化文件（节点会实时读取 Hugging Face 的清单）。
3. 选择图像（可选）并输入提示词后运行工作流。
4. 如需多次复用同一模型，请启用 `keep_model_loaded` 以避免重复下载与初始化。

节点会自动获取 `.gguf` 以及匹配的 projector 权重，缓存到 `models/LLM/Qwen-VL/GGUF/` 下，并基于 llama.cpp 的 `qwen2_vl` 模板执行多模态推理。

## 常见问题
- **“缺少 MMVQ Kernel”**：请使用上述命令重新编译 `llama-cpp-python`。
- **CPU 推理过慢**：可尝试更激进的量化（如 `Q3_K_M`）并保持较小的 batch。
- **提示 projector 不匹配**：删除缓存的 `projector.bin`，让节点重新下载对应文件。
