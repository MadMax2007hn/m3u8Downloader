import json
from pathlib import Path


class FavoritesManager:
    def __init__(self, file_path="data/favorites.json"):
        self.file_path = Path(file_path)
        self.favorites = {}

        self.load()

    def load(self):
        if not self.file_path.exists():
            return

        with open(
            self.file_path,
            "r",
            encoding="utf-8"
        ) as file:
            self.favorites = json.load(file)

    def save(self):
        self.file_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(
            self.file_path,
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                self.favorites,
                file,
                indent=4,
                ensure_ascii=False
            )

    def add(self, name, path):
        self.favorites[name] = str(Path(path))
        self.save()

    def remove(self, name):
        if name in self.favorites:
            del self.favorites[name]
            self.save()

    def get(self, name):
        return self.favorites.get(name)

    def get_all(self):
        return dict(self.favorites)