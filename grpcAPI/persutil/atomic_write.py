import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, List, Tuple


@dataclass
class WritePackage:
    parent_dir: str
    clear_parent: bool
    contents: List[Tuple[str, str]]  # List of (content, path)

    def __iter__(self) -> Iterator[Tuple[str, str]]:
        full_path = [
            (content, f"{self.parent_dir}/{path_str}")
            for content, path_str in self.contents
        ]
        return iter(full_path)


def write_atomic(base_path: Path, content_path: List[WritePackage]) -> None:

    temp_dir = base_path / "temp"
    try:
        temp_dir.mkdir(parents=True, exist_ok=True)

        for package in content_path:
            for content, rel_path in package:
                temp_path: Path = temp_dir / rel_path
                temp_path.parent.mkdir(parents=True, exist_ok=True)
                with open(temp_path, "w", encoding="utf-8") as f:
                    f.write(content)

        for package in content_path:
            target_dir: Path = base_path / package.parent_dir
            temp_subdir: Path = temp_dir / package.parent_dir

            if package.clear_parent and target_dir.exists():
                shutil.rmtree(target_dir)

            target_dir.mkdir(parents=True, exist_ok=True)

            for temp_file in temp_subdir.rglob("*"):
                if temp_file.is_file():
                    relative_path: Path = temp_file.relative_to(temp_subdir)
                    final_path: Path = target_dir / relative_path
                    final_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(temp_file), str(final_path))

    except OSError as e:
        raise e

    finally:
        if temp_dir.exists():
            try:
                if temp_dir.is_dir():
                    shutil.rmtree(temp_dir)
                else:
                    temp_dir.unlink()
            except Exception:
                pass
