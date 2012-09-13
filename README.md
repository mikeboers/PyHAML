# Pythonic HAML

[![Test Status](https://secure.travis-ci.org/mikeboers/PyHAML.png)](http://travis-ci.org/mikeboers/PyHAML)

This is an implementation of [HAML](http://haml-lang.com/) for Python (2.5 through 2.7).

I have kept as much of the same syntax as I could, but there are some Rubyisms built into HAML that I simply cannot replicate. I have tried to stay true to the original features while adapting them to be Pythonic.

This package essentially cross-compiles PyHAML code into a [Mako](http://www.makotemplates.org/) template. Ergo, all of your standard Mako syntax also applies to content which does not match any of the HAML syntax.

## Markup Example

A simple PyHAML template:

    #profile
      .left.column
        #date= print_date
        #address= current_user.address
      .right.column
        #email= current_user.email
        #bio= current_user.bio
    
A Mako template to do the same thing:

    <div id="profile">
        <div class="left column">
            <div id="date">${print_date}</div>
            <div id="address">${current_user.address}</div>
        </div>
        <div class="right column">
            <div id="email">${current_user.email}</div>
            <div id="bio">${current_user.bio}</div>
        </div>
    </div>

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

If you want to pass in a class, use the keyword "class_". If you want to use attribute names with dashes, use camel case instead and it will be converted for you:

    %meta(httpEquiv="Content-Type", content="text/html;charset=UTF-8")

renders to:

    <meta http-equiv="Content-Type" content="text/html;charset=UTF-8">

If you want to pass in any other non-identifier attribute names, you can expand a mapping in place. Eg.:

    %div(class_='content', **{'not-valid-python': 'value'}) content

renders to:

    <div class='content', not-valid-python="value">content</div>

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

### Mixins

We have function delaration/calling syntax similar to [SASS-style mixins](http://sass-lang.com/docs/yardoc/file.INDENTED_SYNTAX.html#mixin_directives). E.g.:

    @make_ol(*args)
        %ol - for arg in args:
            %li ${arg}
    
    +make_ol(1, 2, 3)

renders to:

    <ol>
        <li>1</li>
        <li>2</li>
        <li>3</li>
    </ul>

### [Filters](http://haml-lang.com/docs/yardoc/file.HAML_REFERENCE.html#filters)

Several filters present in Haml are defined in PyHaml. These include
:plain
:escaped
:cdata
:javascript
:css
:sass (requires `sass` executable)
:scss (requires `sass` executable)
:coffeescript (requires `coffee` executable)

We can also take callables from the runtime globals to use as a filter, and we can also use Mako expression interpolation. Eg.:

    -! def to_upper(x):
        return x.upper()
    - value = 123
    :to_upper
        %p The syntaxes, they do nothing!
        #id x
        .class x
        - statement
        / comment
        ${value}

### [Doctype: !!!](http://haml-lang.com/docs/yardoc/file.HAML_REFERENCE.html#doctype_)

There is currently only very basic support for doctypes. In the future these commands should modify the current `format` of the generator to determine if it should create XML or HTML style tags (only closing when nessesary, etc.).

    !!! 5

renders to:

    <!DOCTYPE html>

### [Whitespace Preservation](http://haml-lang.com/docs/yardoc/file.HAML_REFERENCE.html#tilde)
### [Helpers](http://haml-lang.com/docs/yardoc/file.HAML_REFERENCE.html#helpers)

Haven't gotten around to these yet...
