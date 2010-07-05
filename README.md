# Pythonic HAML

This is an implementation of [HAML](http://haml-lang.com/) for Python.

I have kept as much of the same syntax as I could, but there are some Rubyisms built into HAML that I simply cannot replicate. I have tried to stay true to the original features while adapting them to be Pythonic.

This package essentially cross-compiles PyHAML code into a [Mako](http://www.makotemplates.org/) template. Ergo, all of your standard Mako syntax also applies to content which does not match any of the HAML syntax.

## Differences

### Attributes: ()

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

You can also pass in mapping objects as positional objects. Eg.:

    - attrs = dict(a='one', b='two')
    %a(attrs)/

renders to:
    
    <a a="one" b="two" />

### Python Evaluation (used to be Ruby): =
### Running Python: -

Clearly this is now evaluating Python. It is evaluated in the Mako runtime context.

### Interpolation: ${}

We are using Mako to do the heavy lifting here.

### Filters

We don't supply any filters, but the mechanism is there to take callables from the runtime globals to use as a filter.

### Boolean Attributes
### Object References: []
### Doctype: !!!
### Whitespace Preservation
### Helpers

Haven't gotten around to these yet... I'm not really sure if I can do the object references anyways