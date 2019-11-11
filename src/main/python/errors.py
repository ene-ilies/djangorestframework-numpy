class InvalidImageContent(Exception):
    """
    Exception raised in case of invalid image content.
    """
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return "%s" % self.msg