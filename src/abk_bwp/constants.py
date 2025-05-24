"""Constants for the abk_bwp package."""

from pathlib import Path
from importlib.metadata import version as get_version, PackageNotFoundError
import tomllib


class _Const:
    _version: str
    _name: str
    _license: dict
    _keywords: list[str]
    _authors: list[dict]
    _maintainers: list[dict]

    def __init__(self):
        try:
            self._version = get_version("abk_bwp")
            self._name = "abk_bwp"
        except PackageNotFoundError:
            self._version = "0.0.0-dev"
            self._name = "unknown"

        self._license = {"text": "unknown"}
        self._keywords = ["unknown"]
        self._authors = [{"name": "ABK", "email": "unknown"}]
        self._maintainers = [{"name": "ABK", "email": "unknown"}]

        self._load_from_pyproject()

    def _find_project_root(self, start: Path = Path.cwd()) -> Path:  # noqa: B008
        for parent in [start, *start.parents]:
            if (parent / "pyproject.toml").exists():
                return parent
        raise FileNotFoundError("pyproject.toml not found")

    def _load_from_pyproject(self):
        try:
            root = self._find_project_root()
            pyproject_path = root / "pyproject.toml"

            with pyproject_path.open("rb") as f:
                project = tomllib.load(f).get("project", {})
                object.__setattr__(self, "_version", project.get("version", self._version))
                object.__setattr__(self, "_name", project.get("name", self._name))
                object.__setattr__(self, "_license", project.get("license", self._license))
                object.__setattr__(self, "_keywords", project.get("keywords", self._keywords))
                object.__setattr__(self, "_authors", project.get("authors", self._authors))
                object.__setattr__(
                    self, "_maintainers", project.get("maintainers", self._maintainers)
                )
        except Exception as e:
            print(f"Warning: failed to load pyproject.toml metadata: {e}")

    @property
    def VERSION(self) -> str:
        return self._version

    @property
    def NAME(self) -> str:
        return self._name

    @property
    def LICENSE(self) -> str:
        return self._license.get("text", "unknown")

    @property
    def KEYWORDS(self) -> list[str]:
        return self._keywords

    @property
    def AUTHORS(self) -> list[dict]:
        return self._authors

    @property
    def MAINTAINERS(self) -> list[dict]:
        return self._maintainers

    def __setattr__(self, key, value):
        if hasattr(self, key):
            raise AttributeError(f"{key} is read-only")
        super().__setattr__(key, value)


CONST = _Const()
