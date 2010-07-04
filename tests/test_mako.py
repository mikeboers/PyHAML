
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




class TestHamlTutorial(Base):
    
    def test_HowToConvert(self):
        self.assertMako(
            '%strong= item.title',
'''<strong>
    ${item.title}
</strong>
'''
        )


if __name__ == '__main__':
    main()