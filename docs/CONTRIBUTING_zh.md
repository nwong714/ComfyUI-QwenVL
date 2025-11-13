## 第一次使用与提交流程

面向第一次接触本仓库的贡献者，下面按照「确定 ComfyUI 目录 → 获取仓库 → 安装依赖 → 本地测试 → 提交 PR」的顺序给出操作步骤。请严格在 ComfyUI 根目录下的 `custom_nodes/ComfyUI-QwenVL/` 中执行所有命令。

### 0. 准备 ComfyUI 目录
1. **找到 ComfyUI 的根路径**
   - Windows 默认路径通常是 `D:/ComfyUI/` 或你自己解压的任意目录。
   - macOS/Linux 可通过 `pwd` 或 Finder/文件管理器确认。
2. **确保存在 `custom_nodes` 文件夹**
   - 如果没有，手动创建：`mkdir -p ComfyUI/custom_nodes`。
3. **打开终端或命令行**
   - Windows 建议使用 PowerShell；macOS/Linux 使用系统自带 Terminal，切换到 `ComfyUI/custom_nodes`。

### 1. 获取仓库
1. **Fork（计划提 PR 时使用）**
   - 在浏览器打开 [仓库主页](https://github.com/1038lab/ComfyUI-QwenVL)，点击右上角 `Fork`。
   - Fork 完成后，浏览器地址会变成 `https://github.com/<你的 GitHub 用户名>/ComfyUI-QwenVL`。
2. **克隆到本地**
   ```bash
   cd ComfyUI/custom_nodes
   git clone https://github.com/<你的 GitHub 用户名>/ComfyUI-QwenVL.git
   cd ComfyUI-QwenVL
   ```
   > 只是想本地测试、不打算提 PR，也可以直接克隆上游：`git clone https://github.com/1038lab/ComfyUI-QwenVL.git`。
3. **不会用 Git？使用 ZIP**
   - 在 GitHub 仓库页面点击 `Code → Download ZIP`。
   - 解压后把文件夹重命名为 `ComfyUI-QwenVL` 并放入 `ComfyUI/custom_nodes/`。
   - 之后可照常运行依赖安装与测试命令（无需 Git 也能执行 Python/ComfyUI 部分）。

### 2. 安装依赖
1. **常规节点**
   ```bash
   pip install -r requirements.txt
   ```
2. **准备 GGUF 依赖**
   - 需要测试 GGUF 节点时，先卸载旧版 `llama-cpp-python`，再设置 MMVQ 选项安装：
     ```bash
     pip uninstall -y llama-cpp-python
     export CMAKE_ARGS="-DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_MMVQ=ON"
     pip install -r requirements.txt
     ```
   - 安装完可运行以下脚本验证 `mmvq` 是否启用：
     ```python
     from llama_cpp import llama_mmvq_supported
     print("MMVQ:", llama_mmvq_supported())
     ```
3. **准备模型缓存**
   - README 的“模型下载”章节列出了官方权重，直接把模型放进 `ComfyUI/models/LLM/Qwen-VL/`，或让节点首次运行时自动下载。
   - GGUF 节点会从 `Qwen/Qwen3-VL-2B-Thinking-GGUF` 自动列出 `.gguf` 文件，并把 projector 缓存到 `models/LLM/Qwen-VL/projectors/`。

### 3. 本地测试
1. **启动 ComfyUI**
   ```bash
   cd ComfyUI
   python main.py --auto-launch
   ```
   - 浏览器打开的 ComfyUI 页面确认左下角节点分类中出现 🧪AILab/QwenVL。
2. **常规 QwenVL 节点**
   - 在 ComfyUI 菜单 `Queue → Load`，导入 `custom_nodes/ComfyUI-QwenVL/example_workflows/qwenvl_basic_workflow.json`。
   - 替换提示词、接入图像或视频，点击 `Queue Prompt`，确认能输出文本/多模态结果。
3. **GGUF 节点**
   - 从相同分类拖入 “Qwen3-VL GGUF (2B Thinking)” 节点，选择量化文件（建议先用 `Q4_K_M`）。
   - 勾选 `keep_model_loaded`，多次执行以确认模型复用、projector 下载与缓存无异常。
4. **基础检查**
   ```bash
   python -m compileall AILab_QwenVL_GGUF.py
   python -m compileall AILab_QwenVL.py
   ```
   通过后即可进入提交流程。

### 4. 提交变更
1. **创建分支并提交**
   ```bash
   git checkout -b feature/<简要描述>
   git status
   git add <修改的文件>
   git commit -m "feat: <概述改动>"
   ```
2. **推送到自己的仓库**
   ```bash
   git push origin feature/<简要描述>
   ```
3. **创建 Pull Request**
   - 打开 GitHub，进入你 Fork 的仓库，点击 “Compare & pull request”。
   - 在 PR 描述中列出：修改摘要、测试命令（含结果）、是否涉及 GGUF/常规节点。
   - 确认 CI 通过或在描述里说明无法运行的原因。

完成以上步骤，就能在本地完成首次部署、测试，并把通过验证的代码以 PR 形式提交到上游仓库。如需更多细节，可参照 `README_zh.md` 与 `docs/GGUF_zh.md` 的安装与排错章节。
