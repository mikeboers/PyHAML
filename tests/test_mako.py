
from . import *

class TestMakoFeatures(Base):
    
    def test_filters(self):
        self.assertHTML('=|h "before & after"', 'before &amp; after\n')