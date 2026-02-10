
from zipstream import ZipStream
from typing import Generator
from pathlib import PurePath
from zipfile import ZipFile

video_file_extensions = frozenset((
    ".wmv", ".flv", ".mp4",
    ".avi", ".m4v", ".mpg",
    ".mov", ".webm", ".mkv",
    ".ogv", ".mpeg", ".3gp"
))

class NoVideoZipIterator:
    """An iterator that streams a zip file while excluding video files"""

    def __init__(self, zip_path: str) -> None:
        self.zip_path: str = zip_path
        self.closed: bool = False

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
