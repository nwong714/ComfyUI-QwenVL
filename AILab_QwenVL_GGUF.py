import base64
import gc
import importlib
import inspect
import io
from pathlib import Path
from typing import List

import numpy as np
from huggingface_hub import HfApi, snapshot_download
from PIL import Image

import folder_paths

GGUF_REPO_ID = "Qwen/Qwen3-VL-2B-Thinking-GGUF"
VISION_PROJECTOR_FILENAME = "mmproj-model-f16.gguf"
DEFAULT_PROMPT = "Describe the visual content in detail."
DEFAULT_SYSTEM_PROMPT = (
    "You are Qwen3-VL-2B-Thinking, a helpful multimodal assistant that reasons carefully about every detail."
)
GGUF_BASE_DIR = Path(folder_paths.models_dir) / "LLM" / "Qwen-VL-GGUF"
_LLAMA_CLASS = None
MMVQ_INSTALL_HINT = (
    'Reinstall llama-cpp-python from source with MMVQ enabled:\n'
    'CMAKE_ARGS="-DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_MMVQ=ON" '
    'pip install -U "llama-cpp-python@git+https://github.com/ggerganov/llama.cpp.git#subdirectory=bindings/python"'
)


def _resolve_llama_class():
    global _LLAMA_CLASS
    if _LLAMA_CLASS is not None:
        return _LLAMA_CLASS
    try:
        module = importlib.import_module("llama_cpp")
    except ImportError as exc:
        raise RuntimeError(
            "llama-cpp-python with Qwen-VL support is required. " + MMVQ_INSTALL_HINT
        ) from exc
    llama_class = getattr(module, "Llama", None)
    if llama_class is None:
        raise RuntimeError("Installed llama-cpp-python package is missing the Llama class.")
    try:
        signature = inspect.signature(llama_class.__init__)
    except (TypeError, ValueError):
        signature = None
    if not signature or "vision_model_path" not in signature.parameters:
        raise RuntimeError(
            "This llama-cpp-python build was compiled without multimodal/MMVQ support. "
            + MMVQ_INSTALL_HINT
        )
    _LLAMA_CLASS = llama_class
    return llama_class


def _discover_gguf_files() -> List[str]:
    try:
        files = HfApi().list_repo_files(GGUF_REPO_ID)
        variants = [
            file
            for file in files
            if file.lower().endswith(".gguf") and file != VISION_PROJECTOR_FILENAME
        ]
        if variants:
            return sorted(variants)
    except Exception as exc:
        print(f"[QwenVL][GGUF] Failed to fetch variants list: {exc}")
    return [
        "Qwen3-VL-2B-Thinking-Q4_K_M.gguf",
        "Qwen3-VL-2B-Thinking-Q5_K_M.gguf",
        "Qwen3-VL-2B-Thinking-Q6_K.gguf",
        "Qwen3-VL-2B-Thinking-Q8_0.gguf",
        "Qwen3-VL-2B-Thinking-F16.gguf",
    ]


AVAILABLE_GGUF_VARIANTS = _discover_gguf_files()


def _ensure_local_files(filename: str) -> Path:
    GGUF_BASE_DIR.mkdir(parents=True, exist_ok=True)
    local_dir = GGUF_BASE_DIR / GGUF_REPO_ID.split("/")[-1]
    local_dir.mkdir(parents=True, exist_ok=True)
    try:
        snapshot_download(
            repo_id=GGUF_REPO_ID,
            local_dir=str(local_dir),
            local_dir_use_symlinks=False,
            allow_patterns=[filename, VISION_PROJECTOR_FILENAME],
        )
    except Exception as exc:
        raise RuntimeError(f"Failed to download {filename}: {exc}")
    model_file = local_dir / filename
    projector_file = local_dir / VISION_PROJECTOR_FILENAME
    if not model_file.exists():
        raise FileNotFoundError(f"Missing GGUF file {filename}")
    if not projector_file.exists():
        raise FileNotFoundError(f"Missing projector file {VISION_PROJECTOR_FILENAME}")
    return model_file


def _tensor_to_pil(tensor):
    if tensor is None:
        return None
    if hasattr(tensor, "dim") and tensor.dim() == 4:
        tensor = tensor[0]
    array = tensor
    if hasattr(tensor, "detach"):
        array = tensor.detach().cpu().numpy()
    array = (np.clip(array, 0, 1) * 255).astype(np.uint8)
    return Image.fromarray(array)


def _encode_image(image: Image.Image) -> str:
    with io.BytesIO() as buffer:
        image.save(buffer, format="PNG")
        data = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{data}"


class AILab_Qwen3_VL_GGUF:
    def __init__(self):
        self.llm = None
        self.current_signature = None

    def unload(self):
        self.llm = None
        self.current_signature = None
        gc.collect()

    def _load(self, filename, n_ctx, n_threads, n_gpu_layers, seed):
        signature = (filename, n_ctx, n_threads, n_gpu_layers)
        if self.llm is not None and self.current_signature == signature:
            if hasattr(self.llm, "set_seed"):
                self.llm.set_seed(seed)
            return
        self.unload()
        model_path = _ensure_local_files(filename)
        projector_path = model_path.parent / VISION_PROJECTOR_FILENAME
        llama_cls = _resolve_llama_class()
        kwargs = {
            "model_path": str(model_path),
            "n_ctx": n_ctx,
            "chat_format": "qwen2_vl",
            "logits_all": False,
            "seed": seed,
            "n_threads": max(0, n_threads),
            "n_gpu_layers": n_gpu_layers,
            "vision_model_path": str(projector_path),
        }
        if kwargs["n_threads"] == 0:
            kwargs.pop("n_threads")
        try:
            self.llm = llama_cls(**kwargs)
        except TypeError as exc:
            raise RuntimeError(
                "llama-cpp-python rejected the provided vision arguments. " + MMVQ_INSTALL_HINT
            ) from exc
        except RuntimeError as exc:
            message = str(exc)
            if "vision" in message.lower() or "mmvq" in message.lower():
                raise RuntimeError(
                    "llama-cpp-python was built without the required multimodal kernels. "
                    + MMVQ_INSTALL_HINT
                ) from exc
            raise
        self.current_signature = signature

    @classmethod
    def INPUT_TYPES(cls):
        variants = AVAILABLE_GGUF_VARIANTS or ["Qwen3-VL-2B-Thinking-Q4_K_M.gguf"]
        return {
            "required": {
                "gguf_variant": (variants, {"default": variants[0]}),
                "prompt": ("STRING", {"default": DEFAULT_PROMPT, "multiline": True}),
                "system_prompt": ("STRING", {"default": DEFAULT_SYSTEM_PROMPT, "multiline": True}),
                "max_tokens": ("INT", {"default": 512, "min": 32, "max": 2048}),
                "temperature": ("FLOAT", {"default": 0.6, "min": 0.0, "max": 1.5}),
                "top_p": ("FLOAT", {"default": 0.9, "min": 0.0, "max": 1.0}),
                "n_ctx": ("INT", {"default": 4096, "min": 1024, "max": 16384}),
                "n_gpu_layers": ("INT", {"default": 0, "min": -1, "max": 128}),
                "n_threads": ("INT", {"default": 0, "min": 0, "max": 64}),
                "seed": ("INT", {"default": 1, "min": 0, "max": 2**31 - 1}),
                "keep_model_loaded": ("BOOLEAN", {"default": True}),
            },
            "optional": {"image": ("IMAGE",)},
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("RESPONSE",)
    FUNCTION = "process"
    CATEGORY = "🧪AILab/QwenVL"

    def _build_messages(self, prompt, system_prompt, image_tensor):
        messages = []
        system_prompt = system_prompt.strip()
        if system_prompt:
            messages.append({"role": "system", "content": [{"type": "text", "text": system_prompt}]})
        user_content = []
        if image_tensor is not None:
            pil = _tensor_to_pil(image_tensor)
            if pil is not None:
                user_content.append(
                    {
                        "type": "image_url",
                        "image_url": {"url": _encode_image(pil)},
                    }
                )
        prompt = prompt.strip()
        if prompt:
            user_content.append({"type": "text", "text": prompt})
        if not user_content:
            raise ValueError("Prompt or image must be provided")
        messages.append({"role": "user", "content": user_content})
        return messages

    def process(
        self,
        gguf_variant,
        prompt,
        system_prompt,
        max_tokens,
        temperature,
        top_p,
        n_ctx,
        n_gpu_layers,
        n_threads,
        seed,
        keep_model_loaded,
        image=None,
    ):
        self._load(gguf_variant, n_ctx, n_threads, n_gpu_layers, seed)
        messages = self._build_messages(prompt, system_prompt, image)
        response = self.llm.create_chat_completion(
            messages=messages,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
        )
        text = response["choices"][0]["message"]["content"].strip()
        if not keep_model_loaded:
            self.unload()
        return (text,)


NODE_CLASS_MAPPINGS = {
    "AILab_Qwen3_VL_GGUF": AILab_Qwen3_VL_GGUF,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "AILab_Qwen3_VL_GGUF": "Qwen3-VL GGUF (2B Thinking)",
}
