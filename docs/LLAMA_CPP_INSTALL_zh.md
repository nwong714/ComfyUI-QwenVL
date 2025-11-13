# llama-cpp-python 安装与 MMVQ 编译指南

> 本指南面向需要运行 **Qwen3-VL GGUF 节点** 的用户，详细说明如何从源码构建 `llama-cpp-python` 并启用 **MMVQ**。若你仅使用官方 PyPI 提供的节点，可跳过此文。

## 1. 为什么必须自行编译？
- 官方发布的 wheel 尚未包含 `qwen2_vl`/MMVQ 相关算子，无法载入 Qwen3-VL 的多模态权重。
- 只有手动设置 `CMAKE_ARGS=-DLLAMA_BUILD_MMVQ=ON` 并从源码安装，才能获得完整视觉推理能力。

## 2. 环境准备
| 操作系统 | 工具链 | 额外依赖 |
| --- | --- | --- |
| **Linux** (Ubuntu/Debian) | GCC/Clang + CMake 3.26+ | `sudo apt update && sudo apt install -y build-essential cmake python3-dev python3-venv` |
| **Windows 10/11** | Visual Studio 2022 Build Tools（含“使用 C++ 的桌面开发”） | 在 PowerShell 中启用 `cl.exe` 所在的 “x64 Native Tools” 环境，再执行安装命令 |
| **WSL2** | 与 Linux 相同 | 确保 WSL distro 的 `pip` 指向正确的 Python 版本 |

> 建议在独立的虚拟环境中操作，避免影响系统 Python。

## 3. 卸载旧版依赖
```bash
pip uninstall -y llama-cpp-python
```

## 4. 源码安装命令
### Linux / WSL2
```bash
CMAKE_ARGS="-DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_MMVQ=ON -DLLAMA_CUDA=ON" \
pip install -U "llama-cpp-python @ git+https://github.com/ggerganov/llama.cpp.git#subdirectory=bindings/python"
```

### Windows (PowerShell)
```powershell
SET CMAKE_ARGS="-DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_MMVQ=ON -DLLAMA_CUDA=ON"
pip install -U "llama-cpp-python @ git+https://github.com/ggerganov/llama.cpp.git#subdirectory=bindings/python"
```

若需 GPU 推理，可在 `CMAKE_ARGS` 中追加：
- **CUDA**：`-DLLAMA_CUDA=ON`
- **ROCm**：`-DLLAMA_HIPBLAS=ON`
- **Metal (macOS)**：`-DLLAMA_METAL=ON`

## 5. 验证是否启用 MMVQ
```bash
python - <<'PY'
from llama_cpp import Llama
features = Llama.build_info().get("general", {}).get("features", "").lower()
print("mmvq" in features)
print(features)
PY
```
输出第一行应为 `True`，并在第二行包含 `mmvq` 字样。

## 6. 常见报错排查
| 报错/现象 | 处理方法 |
| --- | --- |
| `No module named 'llama_cpp'` | 确认虚拟环境已激活，或重新执行安装命令。 |
| `undefined symbol: mmvq_...` | 说明链接到旧库，先删除 `site-packages/llama_cpp` 并重新安装。 |
| CMake 找不到编译器 | Linux 安装 `build-essential`；Windows 需在“x64 Native Tools”终端中运行。 |
| `Could NOT find Python3` | 确保 `python -m pip` 与 `pip` 指向同一版本，可使用 `python -m pip install ...`。 |
| 安装耗时过久 | 可以先 `git clone https://github.com/ggerganov/llama.cpp` 到本地，再指定 `pip install -e ./llama.cpp/bindings/python`。 |

## 7. 升级/重装提示
- 每次拉取最新的 GGUF 节点或 llama.cpp 代码后，建议重复第 3~5 步，确保本地构建与仓库同步。
- 若切换不同硬件（如从 CPU 改为 CUDA），需要重新设置 `CMAKE_ARGS` 并安装一次。

完成以上步骤后，即可回到 [GGUF 节点指南](./GGUF_zh.md) 继续运行示例工作流。
