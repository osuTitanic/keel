
from zipstream import ZipStream, ZIP_STORED
from typing import Generator, Iterator, Tuple
from zipfile import ZipFile, ZipInfo
from pathlib import PurePath

video_file_extensions = frozenset((
    ".wmv", ".flv", ".mp4",
    ".avi", ".m4v", ".mpg",
    ".mov", ".webm", ".mkv",
    ".ogv", ".mpeg", ".3gp"
))

class NoVideoZipIterator:
    """An iterator that streams a zip file while excluding video files"""

    def __init__(self, zip_path: str):
        self.zip_path: str = zip_path
        self.closed: bool = False

        self.zip_stream: ZipStream | None = None
        self.source_zip: ZipFile | None = None
        self.iterator: Generator | None = None

    def __iter__(self):
        return self

    def __next__(self):
        if self.closed:
            raise StopIteration

        if self.source_zip is None:
            self.source_zip, self.zip_stream = self.create_zip()

        if self.iterator is None:
            self.iterator = self.create_iterator()

        try:
            return next(self.iterator)
        except StopIteration:
            self.close()
            raise

    def create_zip(self) -> Tuple[ZipFile, ZipStream]:
        return(
            ZipFile(self.zip_path, 'r'),
            ZipStream(compress_type=ZIP_STORED)
        )

    def create_items_to_include(self) -> Iterator[ZipInfo]:
        for item in self.source_zip.infolist():
            extension = PurePath(item.filename).suffix.lower()

            if extension not in video_file_extensions:
                yield item

    def create_iterator(self) -> Generator:
        for item in self.create_items_to_include():
            self.zip_stream.add(
                self.source_zip.read(item.filename),
                arcname=item.filename,
            )

        yield from self.zip_stream

    def close(self):
        if not self.closed:
            self.closed = True

            if self.source_zip is not None:
                self.source_zip.close()

            self.zip_stream = None
            self.source_zip = None
            self.iterator = None
