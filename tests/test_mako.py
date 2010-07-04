
from unittest import TestCase, main

from mako.template import Template
import paml


class TestTheTester(TestCase):
    
    def test_pass(self):
        self.assertTrue(True, 'It works!')

class Base(TestCase):
    
    def assertMako(self, source, expected, *args):
        node = paml.parse_string(source)
        mako = paml.generate_mako(node).replace('<%! from paml.codegen import mako_build_attr_str as __P_attrs %>\\\n', '')
        self.assertEqual(mako, expected.replace('    ', '\t'), *args)
        
    def assertHTML(self, source, expected, *args, **kwargs):
        node = paml.parse_string(source)
        mako = paml.generate_mako(node)
        html = Template(mako).render_unicode(**kwargs)
        self.assertEqual(html, expected.replace('    ', '\t'), *args)




class TestHamlTutorial(Base):
    
    def test_1(self):
        self.assertMako(
            '%strong= item.title',
            '<strong>${item.title}</strong>\n'
        )
    
    def test_2(self):
        self.assertHTML(
            '%strong(class_="code", id="message") Hello, World!',
            '<strong id="message" class="code">Hello, World!</strong>\n'
        )

    def test_2b(self):
        self.assertHTML(
            '%strong.code#message Hello, World!',
            '<strong id="message" class="code">Hello, World!</strong>\n'
        )
            
    def test_3(self):
        self.assertHTML(
            '.content Hello, World!',
            '<div class="content">Hello, World!</div>\n'
        )

    def test_4(self):
        class obj(object):
            pass
        item = obj()
        item.id = 123
        item.body = 'Hello, World!'
        self.assertHTML(
            '.item(id="item-%d" % item.id)= item.body',
            '<div id="item-123" class="item">Hello, World!</div>\n',
            item=item
        )

    def test_5(self):
        self.assertHTML(
            '''
#content
  .left.column
    %h2 Welcome to our site!
    %p Info.
  .right.column
    Right content.
            '''.strip(),
            '''
<div id="content">
	<div class="left column">
		<h2>Welcome to our site!</h2>
		<p>Info.</p>
	</div>
	<div class="right column">
		Right content.
	</div>
</div>
            '''.strip() + '\n')


class TestHamlReference(Base):
    
    def test_plain_text_escaping(self):
        self.assertHTML(
            '''
%title
  = title
  \= title
            '''.strip(),
            '''
<title>
    MyPage
    = title
</title>
            '''.strip() + '\n', title='MyPage')


if __name__ == '__main__':
    main()