# -*- coding: utf-8 -*-
from unittest import main
from base import Base

class TestAttributes(Base):

    
    def test_raw_attribute_names(self):
        self.assertHTML(
            '%({"b-dash": "two"}, a="one", **{"c-dash": "three"}) content',
            '<div a="one" b-dash="two" c-dash="three">content</div>\n'
        )
    
    def test_camelcase_attributes(self):
        self.assertHTML(
            '%({"positionalDict":"xxx"}, keywordArgument="xxx", **{"expandedDict":"xxx"}) content',
            '<div expanded-dict="xxx" keyword-argument="xxx" positional-dict="xxx">content</div>\n'
        )
    
    def test_camelcase_override(self):
        self.assertHTML(
            '%({"positionalDict":"xxx"}, keywordArgument="xxx", __adapt_camelcase=False, **{"expandedDict":"xxx"}) content',
            '<div expandedDict="xxx" keywordArgument="xxx" positionalDict="xxx">content</div>\n'
        )

    def test_unicode_arguments(self):
        self.assertHTML(
            u'%(a=u"España") content',
            u'<div a="España">content</div>\n'
        )
    
if __name__ == "__main__":
    main()
