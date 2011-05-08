from . import Base

class TestAttributes(Base):
    
    def test_dashes_in_kwargs(self):
        self.assertHTML(
            '%({"b-dash": "two"}, a="one", **{"c-dash": "three"}) content',
            '<div a="one" b-dash="two" c-dash="three">content</div>\n'
        )