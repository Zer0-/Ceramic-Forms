import unittest
from ceramic_forms.form import Form, Optional, Or, XOr, If

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
        form.validate(data)
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
        form.validate(schema)
        self.assertEqual(schema, form.cleaned)
        self.assertFalse(form.errors)

    def test_optional_key(self):
        schema = {Optional('key'): 'value'}
        data = {'key': 'value'}
        form = Form(schema)
        form.validate(data)
        self.assertEqual(data, form.cleaned)
        self.assertFalse(form.errors)
        data = {}
        form.validate(data)
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
            form.validate(data)
            self.assertEqual(data, form.cleaned)
            self.assertFalse(form.errors)

    def test_dependant_key(self):
        schema = {
            'key': 'value',
            Optional(2): 'two',
            Or: {
                'opt1': 1,
                'opt2': 2,
            },
            If([[2]], "conditional"): "exists",
            If([['opt1']], "opt1_condition"): True,
            If([['opt2'], [2]], "compound_if"): True
        }
        form = Form(schema)
        for data in [
            {'key': 'value', 'opt2': 2},
            {'key': 'value', 2: 'two', 'conditional': "exists"},
            {
                'key': 'value',
                2: 'two',
                'conditional': "exists",
                'opt2': 2,
                'compound_if': True
            }
        ]:
            form.validate(data)
            self.assertEqual(data, form.cleaned)
            self.assertFalse(form.errors)

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

if __name__ == "__main__":
    unittest.main()
