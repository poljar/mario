<link href="http://kevinburke.bitbucket.org/markdowncss/markdown.css" rel="stylesheet"></link>

Meaningful sentences
====================

Incomplete.

[] and <> are metasymbols. [] signifies multiple choices, <> signifies
categories (types?).

    kind        is                      [url, file, raw]
    data        [is, istype, matches]   [<string>]
    {<var>}     [is, istype, matches]   [<string>]


Kind-specific objects
=====================

Objects (or variables?) we would need to pre-exist for a specific kind if we
choose not to have kind objects and corresponding functions. The list is
possibly incomplete.

### kind url

* data
* url


### kind file

* data
* path
* directory
* filename


### kind raw

* data

If we adopt only [functions](#object-variable-functions), the only object we
need is `data`. If we also adopt [kind objects](#kind-objects), the situation
then looks like this:

### kind raw

* data

### kind file

* data
* file

### kind url

* data
* url


Ideas
=====

kind mail
---------

Relatively obvious, possibly unbaked.

file literals
-------------

A special syntax for referring to files and creating values of type File
on-the-fly. A token corresponding to the path of an existing file would be
lifted to a value of type File which can be passed to functions accepting a File
argument.

### Example

The following things would work if there is a file with the path
`/home/user/foo`:

* `groupReadable /home/user/foo`
* `plumb load /home/user/foo`


variable objects
----------------

Variables could be promoted to objects (does this terminology make sense?) by
using the `{var}` syntax. This would probably obviate the need for `arg`. What
would the type(s) of this expression be?

Variables and objects are [potentially just different
namespaces](#objects-variables) for language-level identifiers (with somewhat
different syntax for accessing them).


kind objects
------------

Every kind (except raw?) creates a special object with the same name as the
kind. This object refers to the target of the message in a high-level way and
is used as a target for functions such as filesize or pathof (for kind file) or
schema or domain (for kind url).


types
-----

All values should probably have types. This will increase type-safety and help
ensure everything is meaningful during design of new features. [Kind
objects](#kind-objects) should have a type named after their kind (but
uppercase). Other types we need include String and possibly a number type
(filesizes?). We also need to think how we handle permissions (perhaps via
a set of functions, e.g. userReadable, groupWriteable, ownerOf, etc.)


object (variable?) functions
----------------------------

Functions operating on objects and variables (preferably typed).  Examples
include filesize, pathof, directory, schema, domain, tld, etc.  These would be
naturally combined with the idea of [kind objects](#kind-objects) by having
functions specific to some kind object.

### Examples (with type signatures)

* filesize :: File -> Int?
* filename :: File -> String
* pathof :: File -> String
* directory :: File -> String
* tld :: Url -> String
* schema :: Url -> String
* domain :: Url -> String

Functions would probably make any verb other than `is` and `matches` useless.


objects = variables
-------------------

If we add [types](#types), objects and variables become equivalent things,
differing only in their namespaces (and possibly syntax for accessing
variables, see [variable objects](#variable-objects)).


default kind promotion rules
----------------------------

    [file-promotion]
    kind is raw
    isfile data
    set kind file
    # set filename
    # set path
    # set directory
    .
    .
    .
    replumb

Bad: Supplying default rules could have unwanted interactions with user rules,
the most obvious one being that it's not possible to replumb anymore if there
is a 1-replumb restriction in place and this is not special-cased.
