# -*- coding: utf-8 -*-
from unittest import main
from base import Base

class TestMixins(Base):

    
    def test_basic(self):
        self.assertHTML('''
@basic
    Content
%div
    +basic
'''.strip(),
'''
<div>
Content
</div>\n''')

    def test_parens(self):
        self.assertHTML('''
@basic(x)
    ${repr(x)}
%div
    +basic(dict(key='value'))
'''.strip(),
'''
<div>
{'key': 'value'}
</div>\n''')

    
    
if __name__ == "__main__":
    main()
