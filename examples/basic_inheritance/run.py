
import os

import haml
import mako.lookup

# Build the template lookup.
lookup = mako.lookup.TemplateLookup([os.path.dirname(__file__)],
    preprocessor=haml.preprocessor
)

# Retrieve a template.
template = lookup.get_template('page.haml')
print template.render_unicode()