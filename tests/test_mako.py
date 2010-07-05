
from . import *

class TestMakoFeatures(Base):
    
    def test_filters(self):
        self.assertHTML('=|h "before & after"', 'before &amp; after\n')

    def test_source_inline(self):
        self.assertHTML(
            '''
before
- i = 1
= i
after
            '''.strip(),
            '''
before
1
after
            '''.strip() + '\n')   

    def test_mod_source_inline(self):
        self.assertHTML(
            '''
before
= i
-! i = 1
after
            '''.strip(),
            '''
before
1
after
            '''.strip() + '\n')   

    def test_source(self):
        self.assertHTML(
            '''
before
-
    a = 1
    b = 2
    def go():
        return a + b
= go()
after
            '''.strip(),
            '''
before
3
after
            '''.strip() + '\n')   

    def test_mod_source(self):
        self.assertHTML(
            '''
before
= add(3, 4)
-!
    def add(a, b):
        return a + b

after
            '''.strip(),
            '''
before
7
after
            '''.strip() + '\n')

    def test_source_with_paml_commands(self):
        self.assertHTML(
            '''
before
-
    a = ('1' + """
    -
    """.strip() + """
    #id.class
    """.strip())
= a
after
            '''.strip(),
            '''
before
1-#id.class
after
            '''.strip() + '\n')   








