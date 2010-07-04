from unittest import TestCase, main

from mako.template import Template
import paml

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