from unittest import TestCase, main

from mako.template import Template
import haml

class Base(TestCase):
    
    def assertMako(self, source, expected, *args):
        node = haml.parse_string(source)
        mako = haml.generate_mako(node).replace('<%! from haml import runtime as __HAML %>\\\n', '')
        self.assertEqual(
            mako.replace('    ', '\t'),
            expected.replace('    ', '\t'),
            *args
        )
        
    def assertHTML(self, source, expected, *args, **kwargs):
        node = haml.parse_string(source)
        mako = haml.generate_mako(node)
        html = Template(mako).render_unicode(**kwargs)
        self.assertEqual(
            html.replace('    ', '\t'),
            expected.replace('    ', '\t'),
            *args
        )
