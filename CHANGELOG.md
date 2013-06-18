1.0.1
-----
- Fix parsing of nesting control structures; `else` would not function properly in a nested structure.

1.0.0
-----
- Switched to [SemVer](http://semver.org/); no changes here.

0.1.9
---------
- Added `!!! 5` support without putting the engine into HTML mode.
- Fixed a repr bug in HTMLComment.
- No longer process camel case in Mako tags.

0.1.8
-----
- Double quotes are escaped in tag attributes.
- `sass` and `coffeescript` filters support unicode.

0.1.7
-----
- Mixin calls can have nested function calls (e.g. `+mixin(another_function())`).

0.1.6
-----
- Filters only process Mako interpolation.
- Added several builtin filters.
- Allow dashes in tag names; XSLT is now usable.

0.1.5
-----
- Added `elif` and `else`.
- Convert `camelCase` attributes to `dash-seperated`.
- Added support for babel.
- Support unicode attributes.
- Include `haml-render` and `haml-preprocess` scripts (finally).

0.1.4
-----
- Support Python 2.5

0.1.3
-----
- Added `haml-render` and `haml-preprocess` scripts.

0.1.2
-----
- Bugfix; tag namespaces were mandatory.

0.1.1
-----
This is the start of versioned history.