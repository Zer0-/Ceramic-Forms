import unittest
from ceramic_forms.form import Form, Optional, Or, XOr, If, And

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
            {1: 1, 3: 3, '2': 2},
            {2: 2, '1': 1},
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
    #TODO: test nested keys

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
        clean = {
            'three': {'nested_one': 'string'}
        }
        form = Form(schema)
        form.validate(data)
        self.assertEqual(clean, form.cleaned)
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
        form.validate(data)
        self.assertEqual({}, form.cleaned)
        self.assertTrue(form.errors)
        for key in ['one', 2, 3, 4]:
            self.assertTrue(form.errors[key])

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
            Or: {
                'one': 1,
                'two': 2,
            }
        }
        data = {}
        form = Form(schema)
        form.validate(data)
        self.assertEqual(len(form.errors.section_errors), 1)
        self.assertTrue('missing' in form.errors.section_errors[0].lower())

    def test_missing_xor(self):
        schema = {
            XOr: {
                'one': 1,
                'two': 2,
            }
        }
        data = {}
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

    #TODO: test value exists if If condition not satisfied
    #TODO: test more than one value in XOR
    #TODO: test missing If statement value (none or not all paths exist)

class TestValueValidators(unittest.TestCase):

    def test_function_pass(self):
        schema = {
            'one': len,
            'two': str,
        }
        data = {'one': [0, 1], 'two': 'asdf'}
        form = Form(schema)
        valid = form.validate(data)
        self.assertTrue(valid)
        self.assertFalse(form.errors)
        self.assertFalse(form.errors.section_errors)
        self.assertEqual(data, form.cleaned)

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
        }
        data = {'a': '12'}
        form = Form(schema)
        valid = form.validate(data)
        self.assertFalse(valid)
        self.assertTrue(len(form.errors) == 1)
        self.assertFalse(form.errors.section_errors)
        self.assertEqual({}, form.cleaned)

if __name__ == "__main__":
    unittest.main()
