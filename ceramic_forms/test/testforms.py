import unittest
from ceramic_forms.form import Form, Optional, Or, XOr, If, And, Use, Msg

class TestFormValidation(unittest.TestCase):

    def test_simple_map(self):
        schema = {
            'one': 'string',
            'two': 2,
            3: 'three',
            4: True
        }
        data = {
            'one': 'string',
            'two': 2,
            3: u'three',
            4: True
        }
        form = Form(schema)
        valid = form.validate(data)
        self.assertTrue(valid)
        self.assertEqual(data, form.cleaned)
        self.assertFalse(form.errors)

    def test_nested_map(self):
        schema = {
            'one': 'string',
            'two': 2,
            'three': {
                'nested_one': 'string',
                'nested_two': 22,
            }
        }
        form = Form(schema)
        valid = form.validate(schema)
        self.assertTrue(valid)
        self.assertEqual(schema, form.cleaned)
        self.assertFalse(form.errors)

    def test_blank_nested_list(self):
        schema = {
            'items': [Use(int)]
        }
        data = {
            'items': []
        }
        form = Form(schema)
        valid = form.validate(data)
        self.assertTrue(valid)
        self.assertEqual(data, form.cleaned)
        self.assertFalse(form.errors)

    def test_optional_key(self):
        schema = {Optional('key'): 'value'}
        data = {'key': 'value'}
        form = Form(schema)
        valid = form.validate(data)
        self.assertTrue(valid)
        self.assertEqual(data, form.cleaned)
        self.assertFalse(form.errors)
        data = {}
        valid = form.validate(data)
        self.assertTrue(valid)
        self.assertEqual(data, form.cleaned)
        self.assertFalse(form.errors)

    def test_conditional_key(self):
        schema = {
            'tip': 'top',
            Or: {
                1: 1,
                2: 2,
                3: 3
            },
            XOr: {
                '1': 1,
                '2': 2,
                '3': 3
            }
        }
        form = Form(schema)
        for data in [
            {'tip': 'top', 1: 1, 3: 3, '2': 2},
            {'tip': 'top', 2: 2, '1': 1},
        ]:
            valid = form.validate(data)
            self.assertTrue(valid)
            self.assertEqual(data, form.cleaned)
            self.assertFalse(form.errors)

    def test_dependant_key(self):
        schema = {
            'key': 'value',
            Optional(2): 'two',
            Or: {
                'opt1': 1,
                'opt2': 2,
                'opt3': 3,
            },
            If([[2]], "conditional"): "exists",
            If([['opt1']], "opt1_condition"): True,
            If([['opt2'], [2]], "compound_if"): True
        }
        form = Form(schema)
        for data in [
            {'key': 'value', 'opt2': 2},
            {'key': 'value', 2: 'two', 'conditional': "exists", 'opt3': 3},
            {
                'key': 'value',
                2: 'two',
                'conditional': "exists",
                'opt2': 2,
                'compound_if': True
            }
        ]:
            valid = form.validate(data)
            self.assertTrue(valid)
            self.assertEqual(data, form.cleaned)
            self.assertFalse(form.errors)
            self.assertFalse(len(form.errors.section_errors))

    def test_if_noexist(self):
        schema = {
            Optional('one'): 'value',
            If([['one']], 'two'): 2
        }
        data = {}
        form = Form(schema)
        valid = form.validate(data)
        self.assertTrue(valid)
        self.assertFalse(form.errors)
        self.assertFalse(form.errors.section_errors)

    def test_and_key(self):
        schema = {
            And(int, lambda x: x%2 == 0): 35
        }
        data = {
            12: 35,
            8: 35,
            10: 35
        }
        form = Form(schema)
        valid = form.validate(data)
        self.assertTrue(valid)
        self.assertEqual(data, form.cleaned)
        self.assertFalse(form.errors)
        self.assertFalse(form.errors.section_errors)

    def test_bare_value(self):
        form = Form(4)
        valid = form.validate(4)
        self.assertTrue(valid)
        self.assertEqual(4, form.cleaned)
        self.assertFalse(form.errors)
        self.assertFalse(form.errors.section_errors)

    def test_bare_use(self):
        form = Form(Use(int))
        valid = form.validate('4')
        self.assertTrue(valid)
        self.assertEqual(4, form.cleaned)
        self.assertFalse(form.errors)
        self.assertFalse(form.errors.section_errors)

class TestFormValidationFailure(unittest.TestCase):

    def test_wrong_values(self):
        schema = {
            'one': 'string',
            'two': 2,
            'three': {
                'nested_one': 'string',
                'nested_two': 22,
            }
        }
        data = {
            'one': False,
            'two': 'two',
            'three': {
                'nested_one': 'string',
                'nested_two': 21,
            }
        }
        form = Form(schema)
        form.validate(data)
        self.assertTrue(form.errors)
        self.assertTrue(form.errors['one'])
        self.assertTrue(form.errors['two'])
        self.assertTrue(form.errors['three']['nested_two'])

    def test_wrong_value_inside_container(self):
        schema = {
            Optional('one'): 'one',
            If([['one']], 2): 'two',
            Or: {
                'three': 3,
                3: 'three'
            },
            XOr: {
                'four': 4,
                4: 'four'
            }
        }
        data = {
            'one': 1,
            2: 2,
            3: 3,
            4: 4,
        }
        form = Form(schema)
        valid = form.validate(data)
        self.assertFalse(valid)
        self.assertTrue(form.errors)
        for key in ['one', 2, 3, 4]:
            self.assertTrue(form.errors[key])

    def test_optional_strictness(self):
        schema = {
            Optional('one'): And(str, lambda x: len(x) == 6)
        }
        data = {'one': '12345'}
        form = Form(schema)
        valid = form.validate(data)
        self.assertFalse(valid)
        self.assertEqual({}, form.cleaned)
        self.assertFalse(form.errors.section_errors)
        self.assertEqual(len(form.errors), 1)

    def test_or_strictness(self):
        schema = {
            Or: {
                'one': 1,
                'two': 2,
                'three': And(Use(str), len, lambda x: x.upper() == x)
            }
        }
        data = {'one': 1, 'three': 'BAm'}
        form = Form(schema)
        valid = form.validate(data)
        self.assertFalse(valid)
        self.assertEqual({'one': 1}, form.cleaned)
        self.assertFalse(form.errors.section_errors)
        self.assertEqual(len(form.errors), 1)

    def test_missing_key(self):
        schema = {
            'one': 1,
            'two': 2,
            'three': {
                'four': 4,
                'five': 5
            }
        }
        data = {
            'two': 2
        }
        form = Form(schema)
        form.validate(data)
        self.assertEqual(len(form.errors.section_errors), 2)
        for sectionerr in form.errors.section_errors:
            self.assertTrue("missing" in sectionerr.lower())

    def test_missing_or(self):
        schema = {
            'pre': 'a',
            Or: {
                'one': 1,
                'two': 2,
            }
        }
        data = {'pre': 'a'}
        form = Form(schema)
        valid = form.validate(data)
        self.assertFalse(valid)
        self.assertEqual(len(form.errors.section_errors), 1)
        self.assertTrue('missing' in form.errors.section_errors[0].lower())

    def test_failed_or(self):
        schema = {
            'pre': 'a',
            Or: {
                'one': Use(int),
                'two': lambda x: x.type in [1, 2]
            }
        }
        data = {'pre': 'a', 'one': 'asdf', 'two': 'asdf'}
        form = Form(schema)
        valid = form.validate(data)
        self.assertFalse(valid)

    def test_failed_xor(self):
        schema = {
            'pre': 'a',
            XOr: {
                'one': Use(int),
                'two': lambda x: x.type in [1, 2]
            }
        }
        data = {'pre': 'a', 'one': 'asdf', 'two': 'asdf'}
        form = Form(schema)
        valid = form.validate(data)
        self.assertFalse(valid)


    def test_missing_xor(self):
        schema = {
            'pre': 'a',
            XOr: {
                'one': 1,
                'two': 2,
            }
        }
        data = {'pre': 'a'}
        form = Form(schema)
        form.validate(data)
        self.assertEqual(len(form.errors.section_errors), 1)
        self.assertTrue('missing' in form.errors.section_errors[0].lower())

    def test_missing_in_if(self):
        schema = {
            Optional('one'): 1,
            If([['one']], 'two'): 2
        }
        data = {'one': 1}
        form = Form(schema)
        form.validate(data)
        self.assertEqual(len(form.errors.section_errors), 1)
        self.assertTrue('missing' in form.errors.section_errors[0].lower())

    def test_and_key_fail(self):
        schema = {
            And(int, lambda x: x%2 == 0): 35
        }
        data = {
            '6': 35,
            3: 34,
            2: 34
        }
        form = Form(schema)
        valid = form.validate(data)
        self.assertFalse(valid)
        self.assertEqual(form.cleaned, {})
        self.assertEqual(len(form.errors[3]), 1)
        self.assertEqual(len(form.errors.section_errors), 2)

    #TODO: test value exists if If condition not satisfied
    #TODO: test more than one value in XOR
    #TODO: test missing If statement value (none or not all paths exist)

class TestValueValidators(unittest.TestCase):

    def test_function_pass(self):
        schema = {
            'one': len,
            'two': str,
            'three': int
        }
        data = {'one': [0, 1], 'two': 'asdf', 'three': 0}
        form = Form(schema)
        valid = form.validate(data)
        self.assertTrue(valid)
        self.assertFalse(form.errors)
        self.assertFalse(form.errors.section_errors)
        self.assertEqual(data, form.cleaned)

    def test_function_fail(self):
        schema = {
            'two': str,
            'three': int,
            '4': lambda x: x.type in ['one', 'two']
        }
        data = {'two': 5, 'three': '0', '4': 10}
        form = Form(schema)
        valid = form.validate(data)
        self.assertFalse(valid)
        self.assertEqual(len(form.errors), 3)
        self.assertFalse(form.errors.section_errors)

    def test_And_pass(self):
        schema = {
            'a': And(len, str),
            'b': And(str, len, 'bee')
        }
        data = {'a': 'eh', 'b': 'bee'}
        form = Form(schema)
        valid = form.validate(data)
        self.assertTrue(valid)
        self.assertFalse(form.errors)
        self.assertFalse(form.errors.section_errors)
        self.assertEqual(data, form.cleaned)

    def test_And_fail(self):
        schema = {
            'a': And(str, lambda x: len(x) == 3),
            'b': And(int, 4),
        }
        data = {'a': '12', 'b': '4'}
        form = Form(schema)
        valid = form.validate(data)
        self.assertFalse(valid)
        self.assertEqual(len(form.errors), 2)
        self.assertFalse(form.errors.section_errors)

    def test_and_invalid(self):
        schema = [And(Use(str), len, lambda x: x.upper() == x)]
        data = ['BAm']
        form = Form(schema)
        valid = form.validate(data)
        self.assertFalse(valid)

    def test_Or_pass(self):
        schema = {
            'n': Or('a', 1, 3)
        }
        data = {'n': 3}
        form = Form(schema)
        valid = form.validate(data)
        self.assertTrue(valid)
        self.assertFalse(form.errors)
        self.assertFalse(form.errors.section_errors)
        self.assertEqual(data, form.cleaned)

    def test_Or_fail(self):
        schema = {
            'n': Or('a', 1, 3)
        }
        data = {'n': 4}
        form = Form(schema)
        valid = form.validate(data)
        self.assertFalse(valid)
        self.assertTrue(form.errors)
        self.assertFalse(form.errors.section_errors)

class TestSequenceValidation(unittest.TestCase):

    def test_simple_sequence(self):
        schema = [1]
        form = Form(schema)
        for data in [
            [1],
            [1, 1, 1],
            [1 for i in range(10)]
        ]:
            valid = form.validate(data)
            self.assertTrue(valid)
            self.assertEqual(form.cleaned, data)
            self.assertFalse(form.errors)
            self.assertFalse(form.errors.section_errors)

    def test_multiple_val_sequence(self):
        schema = [1, '1']
        form = Form(schema)
        for data in [
            [1],
            [1, 1, 1],
            ['1'],
            [1, '1'],
            [1, 1, '1', '1', 1]
        ]:
            valid = form.validate(data)
            self.assertTrue(valid)
            self.assertFalse(form.errors)
            self.assertFalse(form.errors.section_errors)

    def test_wrong_value(self):
        schema = [1]
        form = Form(schema)
        for data in [
            ['1'],
            ['1' for i in range(10)],
            [2, 3, 4],
            [1, 1, 1, 2]
        ]:
            valid = form.validate(data)
            self.assertFalse(valid)
            self.assertTrue(form.errors)
            self.assertFalse(form.errors.section_errors)

    def test_combinations_of_values(self):
        pairs = [
            ([[1]], [[1], [1], [1, 1]]),
            ([And(str, lambda x: len(x) == 3)], ['the', 'ick', 'tan']),
            ([{'a': int}], [{'a': 1}, {'a': 2}]),
            ({'a': [int]}, {'a': range(10)})
        ]
        for schema, data in pairs:
            form = Form(schema)
            valid = form.validate(data)
            self.assertTrue(valid)
            self.assertFalse(form.errors)
            self.assertFalse(form.errors.section_errors)

    def test_nested_lists(self):
        data = [[str(i), 2*i] for i in range(5)]
        schema = [And([Use(int)], lambda x: len(x) == 2)]
        form = Form(schema)
        valid = form.validate(data)
        self.assertTrue(valid)
        self.assertFalse(form.errors)
        self.assertFalse(form.errors.section_errors)

    #TODO: If path with sequences... what to do?

class TestUseValidator(unittest.TestCase):

    def test_use_int(self):
        schema = {'use': Use(int)}
        data = {'use': '666'}
        form = Form(schema)
        valid = form.validate(data)
        self.assertEqual({'use': 666}, form.cleaned)
        self.assertTrue(valid)
        self.assertFalse(form.errors)
        self.assertFalse(form.errors.section_errors)

    def test_use_sequence(self):
        schema = [Use(int)]
        data = [1, '2', '34']
        form = Form(schema)
        valid = form.validate(data)
        self.assertEqual([1, 2, 34], form.cleaned)
        self.assertTrue(valid)
        self.assertFalse(form.errors)
        self.assertFalse(form.errors.section_errors)

    def test_use_fail(self):
        schema = [Use(lambda x: x + 10)]
        data = [1, 2, '3']
        form = Form(schema)
        valid = form.validate(data)
        self.assertFalse(valid)
        self.assertTrue(len(form.errors)==1)
        self.assertTrue(form.errors[2])
        self.assertFalse(form.errors.section_errors)

    def test_use_with_and(self):
        schema = {'u': And(Use(int), lambda x: x%2 == 0)}
        data = {'u': '666'}
        form = Form(schema)
        valid = form.validate(data)
        self.assertTrue(valid)
        self.assertEqual({'u': 666}, form.cleaned)
        self.assertFalse(form.errors)
        self.assertFalse(form.errors.section_errors)

class TestMsgWrapper(unittest.TestCase):

    def test_msg_val(self):
        msg = 'not b'
        data = {'a': 'c'}
        for validator in [
            'b',
            int,
            lambda x: x.upper() == x,
            Msg('b', 'what')
        ]:
            schema = {'a': Msg(validator, msg)}
            form = Form(schema)
            self.assertFalse(form.validate(data))
            self.assertEqual(form.errors['a'][0], msg)
            self.assertTrue(len(form.errors)==1)

    def test_key_wrap_if(self):
        msg = 'oh no!'
        schema = {
            1: 1,
            Msg(If([(1,)], 2), msg): 2,
        }
        data = {1: 1}
        form = Form(schema)
        valid = form.validate(data)
        self.assertFalse(valid)
        self.assertEqual(form.errors.section_errors[0], msg)
        self.assertFalse(form.errors)

    def test_key_wrap_or(self):
        msg = 'noooooor'
        schema = {
            Msg(Or, msg): {
                'a': 0,
                'b': 2
            }
        }
        data = {}
        form = Form(schema)
        valid = form.validate(data)
        self.assertFalse(valid)
        self.assertEqual(form.errors.section_errors[0], msg)
        self.assertFalse(form.errors)

#TODO: make sure msg wrap doesn't screw up any nested validation.

if __name__ == "__main__":
    unittest.main()
