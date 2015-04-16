# Copyright (c) 2015 Damir Jelić, Denis Kasak
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import unittest

from mario.core import arg_rewrite_func, Kind
from mario.parser import make_parser, parse_rule_string

# PARSER TESTS

simple_rule = '''[test]
arg matches {data} regex_string
plumb run firefox'''

simple_res = [
    ['test', (
        [
            ['arg', 'matches', '{data}', ['regex_string']]
        ],
        [
            ['plumb', 'run', 'firefox']
        ]
    )]
]


multiple_margs_rule = '''[test]
arg matches {data} regex_string
                   regex_inbetween
plumb run firefox'''

multiple_margs_res = [
    ['test', (
        [
            ['arg', 'matches', '{data}', ['regex_string', 'regex_inbetween']]
        ],
        [
            ['plumb', 'run', 'firefox']
        ]
    )]
]


multiple_rules = '''[test]
arg matches {data} regex_string
                   regex_inbetween
plumb run firefox
[test2]
arg is {data} something
plumb run echo {data}'''

multiple_res = [
    ['test', (
        [
            ['arg', 'matches', '{data}', ['regex_string', 'regex_inbetween']]
        ],
        [
            ['plumb', 'run', 'firefox']
        ]
    )],
    ['test2', (
        [
            ['arg', 'is', '{data}', ['something']]
        ],
        [
            ['plumb', 'run', 'echo {data}']
        ]
    )]
]

rule_with_comment = '''# this is a comment
[test] # even here?
# another one
    
arg matches {data} regex_string # commenting is fun

   # maybe here with some whitespace?

plumb run firefox # inline commenting wherever I want

#even here ?'''


rule_complex_variable = '''[test]
arg matches /bla/{data}/bla.py regex_string
plumb run firefox'''

complex_var_res = [
    ['test', (
        [
            ['arg', 'matches', '/bla/{data}/bla.py', ['regex_string']]
        ],
        [
            ['plumb', 'run', 'firefox']
        ]
    )]
]


rule_utf8_names = '''[čest]
arg matches /bla/{data}/ćla.py regex_stringić # comments ¹²³
plumb run firefȭx'''

res_utf8_names = [
    ['čest', (
        [
            ['arg', 'matches', '/bla/{data}/ćla.py', ['regex_stringić']]
        ],
        [
            ['plumb', 'run', 'firefȭx']
        ]
    )]
]


multiple_variables_rule = '''[test]
arg matches /bla/{data}/{another} regex_string
plumb run firefox'''

multiple_variables_res = [
    ['test', (
        [
            ['arg', 'matches', '/bla/{data}/{another}', ['regex_string']]
        ],
        [
            ['plumb', 'run', 'firefox']
        ]
    )]
]


liberal_whitespace = '''[test] # co
arg     matches         {data}         regex_string      #   white      space    
plumb     run        firefox'''


data_object_rule = '''[test]
data matches regex_string
plumb run firefox'''


data_multiple_margs_rule = '''[test]
data matches regex_string
             regex_inbetween
plumb run firefox'''


class ParserTest(unittest.TestCase):
    def parser_test_helper(self, rule, result):
        parser = make_parser()
        res = parse_rule_string(parser, rule)
        self.assertEqual(result, res)

    def test_validate_parser(self):
        parser = make_parser()
        parser.validate()

    def test_simple_rule(self):
        self.parser_test_helper(simple_rule, simple_res)

    def test_multiple_match_args(self):
        self.parser_test_helper(multiple_margs_rule, multiple_margs_res)

    def test_multiple_rules(self):
        self.parser_test_helper(multiple_rules, multiple_res)

    def test_rule_with_comment(self):
        self.parser_test_helper(rule_with_comment, simple_res)

    def test_complex_var(self):
        self.parser_test_helper(rule_complex_variable, complex_var_res)

    def test_utf8(self):
        self.parser_test_helper(rule_utf8_names, res_utf8_names)

    def test_multiple_variables(self):
        self.parser_test_helper(multiple_variables_rule, multiple_variables_res)

    def test_whitespace(self):
        self.parser_test_helper(liberal_whitespace, simple_res)

    def test_data_object(self):
        self.parser_test_helper(data_object_rule, simple_res)

    def test_data_multiple_marg(self):
        self.parser_test_helper(data_multiple_margs_rule, multiple_margs_res)

# CORE TESTS

class CoreTest(unittest.TestCase):
    def test_arg_rewrite_simple(self):
        self.assertEqual(
            arg_rewrite_func({'data' : 'oolong',
                              'kind' : Kind['raw']
                             },
                             ['{data}', ['oo,', 'g,g jing']],
                             (), {}),
            (True, {'data': 'long jing', 'kind': Kind['raw']}, (), {})
        )

    def test_get_var_references_basic(self):
        self.assertListEqual(
            list(get_var_references('{0}')),
            ['{0}']
        )

    def test_get_var_references_basic_spaces(self):
        self.assertListEqual(
            list(get_var_references('   {0} \t  ')),
            ['{0}']
        )

    def test_get_var_references_multiple_vars(self):
        self.assertListEqual(
            list(get_var_references("{0}www{1}foo {abc}")),
            ['{0}', '{1}', '{abc}']
        )


if __name__ == '__main__':
        unittest.main()
