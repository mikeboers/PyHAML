
from unittest import main
from base import Base



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

    def test_expr_blocks(self):
        self.assertHTML(
            '''
= 'inline expr'
=
    'block expr 1'
    'block expr 2'
    a
        b
        c
            '''.strip(),
            '''
inline expr
    block expr 1
    block expr 2
    one
        two
        three
            '''.strip() + '\n',
        a='one', b='two', c='three')


    def test_expr_blocks_filters(self):
        self.assertHTML(
            '''
-! to_title = lambda x: x.title()
= 'inline expr'
=|to_title
    'block expr 1'
    'block expr 2'
    a
        b
        c
            '''.strip(),
            '''
inline expr
    Block Expr 1
    Block Expr 2
    One
        Two
        Three
            '''.strip() + '\n',
        a='one', b='two', c='three')  

    def test_empty_line_handling(self):
        self.assertHTML(
            '''
- content = """
    before
    
    after""".strip()
= content
            '''.strip(),
            '''
    before
    
    after
            '''.strip() + '\n') 

    def test_empty_line_handling_2(self):
        self.assertHTML(
            '''
- content = """
    before
    
        after""".strip()
= content
            '''.strip(),
            '''
    before
    
        after
            '''.strip() + '\n')

    def test_empty_line_handling_3(self):
        '''A blank line should not affect indentation level.'''
        self.assertHTML(
            '''
%a
    %b

        %c
            '''.strip(),
            '''
<a>
    <b>
        <c></c>
    </b>
</a>
            '''.strip() + '\n')

if __name__ == "__main__":
    main()
