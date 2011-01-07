# Pythonic HAML

This is an implementation of [HAML](http://haml-lang.com/) for Python.

I have kept as much of the same syntax as I could, but there are some Rubyisms built into HAML that I simply cannot replicate. I have tried to stay true to the original features while adapting them to be Pythonic.

This package essentially cross-compiles PyHAML code into a [Mako](http://www.makotemplates.org/) template. Ergo, all of your standard Mako syntax also applies to content which does not match any of the HAML syntax.

## Basic Example

Simple HAML (no variables passed in):

    %head
        %title My super awesome example!
        %link(rel='stylesheet', href='/css/screen.css')
    %body
        #header
            %img#logo(src='/img/logo.png')
            %ul#top-nav.nav
                - for i in range(2):
                    %li= 'Item %02d' % i
        #content
            %p
                The content goes in here.
                This is another line of the content.
            %p.warning
                This is a warning.

... results in:

    <head>
    	<title>My super awesome example!</title>
    	<link href="/css/screen.css" rel="stylesheet" />
    </head>
    <body>
    	<div id="header">
    		<img id="logo" src="/img/logo.png" />
    		<ul id="top-nav" class="nav">
    			<li>Item 00</li>
    			<li>Item 01</li>
    		</ul>
    	</div>
    	<div id="content">
    		<p>
    			The content goes in here.
    			This is another line of the content.
    		</p>
    		<p class="warning">
    			This is a warning.
    		</p>
    	</div>
    </body>

## API Example

    import haml
    import mako.template
    
    if your_templates_are_in_a_directory:
    
        # Build the template lookup.
        lookup = mako.lookup.TemplateLookup(["various", "template", "paths"],
            preprocessor=haml.preprocessor
        )
        
        # Retrieve a template.
        template = lookup.get_template('example_template.haml')
    
    else: # You have some strings...
    
        # Write your HAML.
        haml_source = '.content Hello, World!'
    
        # Build your template.
        template = mako.template.Template(haml_source,
            preprocessor=haml.preprocessor
        )
    
    # Render!
    print template.render()

    
## Reference

Herein lies our differences to the [HAML reference](http://haml-lang.com/docs/yardoc/file.HAML_REFERENCE.html).

### [Attributes: ()](http://haml-lang.com/docs/yardoc/file.HAML_REFERENCE.html#attributes)

Python syntax must be used as if calling a function that takes keyword arguments. Eg.:

    %ul
        - for i in range(5):
            %li(id=['item', str(i)]) ITEM ${i}
    
renders to:
    
    <ul>
        <li id="item_0">ITEM 0</li>
        <li id="item_1">ITEM 1</li>
        <li id="item_2">ITEM 2</li>
        <li id="item_3">ITEM 3</li>
        <li id="item_4">ITEM 4</li>
    </ul>

If you want to pass in a class, use the keyword "class_". If you want to pass in any other non-identifier attribute names, you can expand a mapping in place. Eg.:

    %div(class_='content', **{'not-valid-python': 'value'}) content

renders to:

    <div class='content', not-valid-python="value">content</div

You can also pass in mapping objects as positional objects. Eg.:

    - attrs = dict(a='one', b='two')
    %a(attrs)/

renders to:
    
    <a a="one" b="two" />


#### [Boolean Attributes](http://haml-lang.com/docs/yardoc/file.HAML_REFERENCE.html#boolean_attributes)

We only output the XHTML style attribute. Eg.:
    
    %input(type='checkbox', checked=True)

to
    
    <input type="checkbox" checked="checked" />
    
### [Python Evaluation: =](http://haml-lang.com/docs/yardoc/file.HAML_REFERENCE.html#ruby_evaluation)
### [Running Python: -](http://haml-lang.com/docs/yardoc/file.HAML_REFERENCE.html#running_ruby_)

Clearly this is now evaluating Python. It is evaluated in the Mako runtime context.

### [Python Interpolation: ${}](http://haml-lang.com/docs/yardoc/file.HAML_REFERENCE.html#ruby_interpolation_)

We are using Mako to do the heavy lifting here.

### [Filters](http://haml-lang.com/docs/yardoc/file.HAML_REFERENCE.html#filters)

We don't supply any filters, but the mechanism is there to take callables from the runtime globals to use as a filter. Eg.:

    -! def to_upper(x):
        return x.upper()
    :to_upper
        %p The syntaxes, they do nothing!
        #id x
        .class x
        - statement
        / comment

### [Doctype: !!!](http://haml-lang.com/docs/yardoc/file.HAML_REFERENCE.html#doctype_)
### [Whitespace Preservation](http://haml-lang.com/docs/yardoc/file.HAML_REFERENCE.html#tilde)
### [Helpers](http://haml-lang.com/docs/yardoc/file.HAML_REFERENCE.html#helpers)

Haven't gotten around to these yet...