import os


PROMPT_DIR = os.path.dirname(__file__)

_loaded_prompts = {}


def load_prompt(name: str) -> str:
    """
    作用: 根据输入的 name，加载并缓存对应的 prompt markdown 文件内容。
    如果已缓存则直接返回内容。
    :param name: 不含扩展名的 prompt 文件名
    :return: prompt string
    :raises FileNotFoundError: 指定的 prompt 文件不存在
    """
    if name in _loaded_prompts:
        return _loaded_prompts[name]

    path = os.path.join(PROMPT_DIR, f"{name}.md")
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Prompt file '{name}.md' not found in prompts/ directory.")

    with open(path, "r", encoding="utf-8") as f:
        content = f.read().strip()
        _loaded_prompts[name] = content
        return content
