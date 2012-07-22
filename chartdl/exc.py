from __future__ import unicode_literals

class ChartDLBaseException(Exception):
    pass

class DownloadError(ChartDLBaseException):
    def __init__(self, msg):
        self.msg = msg
    
    def __str__(self):
        return self.msg
    
    @property
    def is_gema_error(self):
        return 'GEMA' in self.msg.upper()

class EncodingError(ChartDLBaseException):
    pass

