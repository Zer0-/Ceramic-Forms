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
