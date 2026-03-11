"""config.py — Loads and hot-reloads all YAML config files."""
import logging
from pathlib import Path
from typing import Any
import yaml

logger = logging.getLogger(__name__)
CONFIG_DIR = Path(__file__).parent.parent / "config"
CONFIG_FILES = ["game","vehicles","economy","map","regions","traffic","multiplayer"]

class Config:
    def __init__(self):
        self._data: dict[str, Any] = {}
        self._errors: list[str] = []
        self.reload()

    def reload(self) -> bool:
        success = True
        errors = []
        for name in CONFIG_FILES:
            path = CONFIG_DIR / f"{name}.yaml"
            try:
                with open(path) as f:
                    data = yaml.safe_load(f)
                if data is None:
                    raise ValueError(f"{name}.yaml is empty")
                self._data[name] = data
                logger.info(f"Config loaded: {name}.yaml")
            except Exception as e:
                msg = f"Error loading {name}.yaml: {e}"
                logger.error(msg)
                errors.append(msg)
                success = False
        self._errors = errors
        return success

    @property
    def errors(self): return self._errors

    def __getattr__(self, name):
        if name.startswith("_"): raise AttributeError(name)
        if name in self._data: return self._data[name]
        raise AttributeError(f"No config for '{name}'")

cfg = Config()
