import shutil
from pathlib import Path
from typing import List, Tuple


def create_temp_dir(base_path: Path) -> Path:
    temp_dir = base_path / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


def write_atomic(base_path: Path, content_path: List[Tuple[str, str]]) -> None:
    temp_dir = create_temp_dir(base_path)

    try:
        # Escreve tudo na pasta temp
        for content, path_str in content_path:
            path = temp_dir / path_str
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

        # Se chegou aqui, escreve tudo ok, vamos mover para o destino

        # Remove tudo que existe em base_path, exceto a pasta temp
        for child in base_path.iterdir():
            if child == temp_dir:
                continue
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()

        # Agora move os arquivos da temp para base_path
        for item in temp_dir.iterdir():
            target = base_path / item.name
            shutil.move(str(item), str(target))

        # Por fim, remove a pasta temp vazia
        temp_dir.rmdir()

    except Exception as e:
        # Se deu erro, tenta limpar a pasta temp para não deixar lixo
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        raise e
