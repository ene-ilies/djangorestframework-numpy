from django.core.files.uploadhandler import FileUploadHandler, StopUpload, StopFutureHandlers
from django.conf import settings
from io import BytesIO
import numpy as np
from PIL import Image
from errors import InvalidImageContent


class ImageUploadHandler(FileUploadHandler):
    """
    File upload handler to stream image uploads into numpy array.
    """

    def new_file(self, *args, **kwargs):
        """
        Use the content_length to signal if the file is too large to be handled in memory.
        """
        _, _, content_type, content_length, _ = args
        assert content_type, 'content_type not set.'
        assert content_length, 'content_length not set.'
        assert content_length > 0, 'invalid content_length'
        assert settings.FILE_UPLOAD_MAX_MEMORY_SIZE, 'missing FILE_UPLOAD_MAX_MEMORY_SIZE setting.'
        if content_length > settings.FILE_UPLOAD_MAX_MEMORY_SIZE:
            raise StopUpload(connection_reset=True)

        self._file = BytesIO()
        self._length = 0
        raise StopFutureHandlers

    def receive_data_chunk(self, raw_data, start):
        """Accumulates the data into memory."""
        length_after_chunk = self._length + len(raw_data)
        if length_after_chunk > settings.FILE_UPLOAD_MAX_MEMORY_SIZE:
            raise StopUpload(connection_reset=True)

        self._file.write(raw_data)
        self._length = length_after_chunk

    def file_complete(self, file_size):
        """Return a numpy array containing the accumulated image."""
        if not self._length == file_size:
            raise StopUpload(connection_reset=True)

        self._file.seek(0)
        try:
            return np.array(Image.open(self._file))
        except IOError as e:
            raise InvalidImageContent('Given content does not contain a valid image.')
