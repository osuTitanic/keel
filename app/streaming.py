
from zipstream import ZipStream
from typing import Generator
from pathlib import PurePath
from zipfile import ZipFile
from io import BufferedReader
import os

video_file_extensions = frozenset((
    ".wmv", ".flv", ".mp4",
    ".avi", ".m4v", ".mpg",
    ".mov", ".webm", ".mkv",
    ".ogv", ".mpeg", ".3gp"
))

class ZipIterator:
    """An iterator that streams a zip file directly"""

    def __init__(self, zip_path: str, chunk_size: int = 1024 * 64) -> None:
        self.file: BufferedReader = open(zip_path, 'rb')
        self.chunk_size: int = chunk_size
        self.zip_path: str = zip_path
        self.closed: bool = False

    def __len__(self) -> int:
        return os.path.getsize(self.zip_path)

    def __iter__(self) -> Generator:
        return self

    def __del__(self) -> None:
        self.close()

    def __next__(self) -> bytes:
        if self.closed:
            raise StopIteration

        chunk = self.file.read(self.chunk_size)

        if not chunk:
            self.close()
            raise StopIteration

        return chunk

    def close(self):
        if self.closed:
            return

        self.closed = True

        if self.file is not None:
            self.file.close()
            self.file = None

class NoVideoZipIterator:
    """An iterator that streams a zip file while excluding video files"""

    def __init__(self, zip_path: str) -> None:
        self.closed: bool = False
        self.zip_path: str = zip_path
        self.source_zip = ZipFile(self.zip_path, 'r')
        self.zip_stream = ZipStream(sized=True)
        self.iterator: Generator | None = None
        self.prepare_stream()

    def __len__(self) -> int:
        return len(self.zip_stream)

    def __iter__(self) -> Generator:
        return self

    def __del__(self) -> None:
        self.close()

    def __next__(self) -> bytes:
        if self.closed:
            raise StopIteration

        if self.iterator is None:
            self.iterator = iter(self.zip_stream)

        try:
            return next(self.iterator)
        except StopIteration:
            self.close()
            raise

    def prepare_stream(self):
        for item in self.source_zip.infolist():
            extension = PurePath(item.filename).suffix.lower()

            if extension in video_file_extensions:
                continue

            self.zip_stream.add(
                self.source_zip.read(item.filename),
                arcname=item.filename,
            )

    def close(self):
        if self.closed:
            return

        self.closed = True

        if self.source_zip is not None:
            self.source_zip.close()

        self.zip_stream = None
        self.source_zip = None
        self.iterator = None
