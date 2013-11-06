#Ceramic Forms
Is a lightweight form validation library aimed at helping parse html forms server-side.

##Basic Usage

Create a structure out of dictionaries and lists, make a Form and validate unsafe data...
```python
from ceramic_forms import Form, Use

schema = {
    'firstname': str,
    'lastname': str,
    'choices': [Use(int)]#Use keeps the values returned by the given function.
}

data = {
    'firstname': 'Teddy',
    'lastname': 'Bear',
    'choices': ['1', '2', '3']
}

form = Form(schema)
form.validate(data)
print(form.cleaned)
#>>>{'lastname': 'Bear', 'choices': [1, 2, 3], 'firstname': 'Teddy'}
#Notice how the choices were converted to integers...
```

##Or

The `Or` type by itself can be used as a dictionary key. When used this way the corresponding value must be a dictionary.
Your data must have at *at least one* key, value pair that is valid by any of the key, value pairs in
this nested dictionary. An example:

```python
schema = {
    'status': Use(int),
    Or: {
        'body': And(str, lambda x: len(x) > 3),
        'head': str
    }
}

data = {
    'status': '3',
    'body': 'hello world'
}

form = Form(schema)
form.validate(data)
print(form.cleaned)
#>>>{'status': 3, 'body': 'hello world'}
```

`XOr` may be used similarly though your data may have *exactly one* matching key, value pair.

`Or` may also be used in the following manner:

```python
schema = {'a': Or(1, 'asdf')}
```

As you can guess this will validate "a" being either one or the string "asdf"

##Errors

When things go wrong Ceramic does not throw exceptions - rather it saves all the errors in a structure.
The FormErr structure matches the schema structure and you can navigate it to view the errors for a given field:

```python
schema = {
    'customer_id': int,
    'name': str,
    Optional('phone_numbers'): [
        {
            'number': Msg(And(str, lambda x: len(x) > 6),
                          'Invalid phone number!'),
            'type': Or('cell', 'home')
        }
    ],
    Or: {
        'street_address': str,
        'postal_code': And(str, lambda x: len(x)==6)
    },
    If([['phone_numbers'], ['postal_code']], 'special_condition'): And(
        Use(int),
        lambda x: x%2 == 0
    )
}

data = {
    'customer_id': '9001',
    'name': 'Eenis',
    'phone_numbers': [{'number': '666', 'type': 'cell'}],
    'postal_code': '123456'
}

form = Form(schema)
print(form.validate(data))
#>>>False
print(form.errors['customer_id'])
#>>>['9001 must be of type int']
#errors that pertain to the entire map/sequence are stored in section_errors
print(form.errors.section_errors)
#>>>['Missing special_condition']
print(form.errors['phone_numbers'])
#>>><[]{0: <[]{number: ['Invalid phone number!']}>}>
#Since phone numbers is a structure itself and not a value we get a structure
#as an error...
```

###Thanks to

[Schema](https://github.com/halst/schema) as it heavily influenced the development of Ceramic (though I think Schema
itself may be based on another lib, I can't find it right now)
