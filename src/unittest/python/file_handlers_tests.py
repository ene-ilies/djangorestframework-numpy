from unittest import TestCase
from django.core.files.uploadhandler import StopFutureHandlers, StopUpload
from hamcrest import assert_that, calling, raises
from file_handlers import ImageUploadHandler
from unittest.mock import patch
from PIL import Image
from io import BytesIO
import numpy as np
from errors import InvalidImageContent

MAX_FILE_SIZE = 5 * 2 ** 20

class ImageUploadHandlerTestCase(TestCase):

    @patch('file_handlers.settings')
    def test_that_image_upload_handler_new_file_does_not_accept_files_bigger_than_limit(self, settings):
        settings.FILE_UPLOAD_MAX_MEMORY_SIZE = MAX_FILE_SIZE
        imageHandler = ImageUploadHandler()
        assert_that(calling(imageHandler.new_file).with_args(None, None, 'image/png',
                                                             settings.FILE_UPLOAD_MAX_MEMORY_SIZE + 1, 'utf-8'),
                    raises(StopUpload))

    @patch('file_handlers.settings')
    def test_that_image_upload_handler_new_file_does_accept_valid_files(self, settings):
        settings.FILE_UPLOAD_MAX_MEMORY_SIZE = MAX_FILE_SIZE
        imageHandler = ImageUploadHandler()
        assert_that(calling(imageHandler.new_file).with_args(None, None, 'image/png', 923874, 'utf-8'),
                    raises(StopFutureHandlers))

    @patch('file_handlers.settings')
    def test_that_image_upload_handler_receive_data_chunk_does_accept_valid_chunk(self, settings):
        settings.FILE_UPLOAD_MAX_MEMORY_SIZE = MAX_FILE_SIZE
        imageHandler = ImageUploadHandler()
        assert_that(calling(imageHandler.new_file).with_args(None, None, 'image/png', 923874, 'utf-8'),
                    raises(StopFutureHandlers))
        imageHandler.receive_data_chunk(b'chunk content', 0)

    @patch('file_handlers.settings')
    def test_that_image_upload_handler_receive_data_chunk_does_not_accept_chunk_bigger_than_upload_limit(self,
                                                                                                         settings):
        settings.FILE_UPLOAD_MAX_MEMORY_SIZE = MAX_FILE_SIZE
        imageHandler = ImageUploadHandler()
        assert_that(calling(imageHandler.new_file).with_args(None, None, 'image/png', 923874, 'utf-8'),
                    raises(StopFutureHandlers))
        assert_that(
            calling(imageHandler.receive_data_chunk).with_args(b'a' * int(settings.FILE_UPLOAD_MAX_MEMORY_SIZE + 1), 0),
            raises(StopUpload))

    @patch('file_handlers.settings')
    def test_that_image_upload_handler_receive_data_chunk_does_not_accept_chunk_when_total_upload_exceeds_the_limit(
            self, settings):
        settings.FILE_UPLOAD_MAX_MEMORY_SIZE = MAX_FILE_SIZE
        imageHandler = ImageUploadHandler()
        assert_that(calling(imageHandler.new_file).with_args(None, None, 'image/png', 923874, 'utf-8'),
                    raises(StopFutureHandlers))
        imageHandler.receive_data_chunk(b'a' * int(settings.FILE_UPLOAD_MAX_MEMORY_SIZE / 2), 0)
        assert_that(
            calling(imageHandler.receive_data_chunk).with_args(b'a' * int(settings.FILE_UPLOAD_MAX_MEMORY_SIZE / 2 + 1),
                                                               settings.FILE_UPLOAD_MAX_MEMORY_SIZE / 2),
            raises(StopUpload))

    @patch('file_handlers.settings')
    def test_that_image_upload_handler_file_complete_raises_error_when_size_does_not_match(self, settings):
        settings.FILE_UPLOAD_MAX_MEMORY_SIZE = MAX_FILE_SIZE
        imageHandler = ImageUploadHandler()
        assert_that(calling(imageHandler.new_file).with_args(None, None, 'image/png', 923874, 'utf-8'),
                    raises(StopFutureHandlers))
        imageHandler.receive_data_chunk(b'a' * int(settings.FILE_UPLOAD_MAX_MEMORY_SIZE / 2), 0)
        assert_that(
            calling(imageHandler.file_complete).with_args(int(settings.FILE_UPLOAD_MAX_MEMORY_SIZE / 2 + 1)),
            raises(StopUpload))

    @patch('file_handlers.settings')
    def test_that_image_upload_handler_file_complete_returns_numpy_array_for_uploaded_image(self, settings):
        image = Image.new('RGB', (640, 480), (73, 109, 137))
        imageBytesIO = BytesIO()
        image.save(imageBytesIO, 'PNG')
        imageBytes = imageBytesIO.getvalue()
        settings.FILE_UPLOAD_MAX_MEMORY_SIZE = MAX_FILE_SIZE
        imageHandler = ImageUploadHandler()
        assert_that(calling(imageHandler.new_file).with_args(None, None, 'image/png', 923874, 'utf-8'),
                    raises(StopFutureHandlers))
        imageHandler.receive_data_chunk(imageBytes, 0)
        numpyImg = imageHandler.file_complete(len(imageBytes))
        np.testing.assert_array_equal(numpyImg, np.array(image))

    @patch('file_handlers.settings')
    def test_that_image_upload_handler_file_complete_raises_error_when_invalid_bytes_sequence(self, settings):
        imageBytesIO = BytesIO(b'a' * 100)
        imageBytes = imageBytesIO.getvalue()
        settings.FILE_UPLOAD_MAX_MEMORY_SIZE = MAX_FILE_SIZE
        imageHandler = ImageUploadHandler()
        assert_that(calling(imageHandler.new_file).with_args(None, None, 'image/png', len(imageBytes), 'utf-8'),
                    raises(StopFutureHandlers))
        imageHandler.receive_data_chunk(imageBytes, 0)
        assert_that(calling(imageHandler.file_complete).with_args(len(imageBytes)), raises(InvalidImageContent))
