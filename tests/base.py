from unittest import TestCase, main
import os

from mako.template import Template
import haml


def skip(func):
    def test(*args, **kwargs):
        from nose.exc import SkipTest
        raise SkipTest()
    return test


def skip_on_travis(func):
    if os.environ.get('TRAVIS') == 'true':
        def test(*args, **kwargs):
            from nose.exc import SkipTest
            raise SkipTest()
        return test
    else:
        return func


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
