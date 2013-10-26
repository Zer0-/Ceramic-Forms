class Optional:
    def __init__(self, key):
        self.key = key

class Or:
    pass

class XOr:
    pass

class If:
    def __init__(self, paths, key):
        self.paths = paths
        self.key = key

class FormErr(dict):
    def __init__(self, *args, **kwargs):
        self.section_errors = []
        dict.__init__(self, *args, **kwargs)

    def __getitem__(self, key):
        value = self.get(key)
        if value is None:
            value = []
            self[key] = value
        return value

def path_exists(path, structure):
    pass

def validate_key(key, suspicious, reference_value, cleaned, errors):
    if isinstance(key, Optional):
        key = key.key
        if key in suspicious:
            validate_key(key, suspicious, reference_value, cleaned, errors)
    elif key == Or:
        validated = False
        for orkey, orvalue in reference_value.items():
            if orkey in suspicious:
                validate_key(orkey, suspicious, orvalue, cleaned, errors)
                validated = True
        if not validated:
            errors.section_errors.append(
                "Missing any of {}".format(reference_value.keys()))
    elif key == XOr:
        validated = 0
        for orkey, orvalue in reference_value.items():
            if orkey in suspicious:
                validate_key(orkey, suspicious, orvalue, cleaned, errors)
                validated += 1
        if validated == 0:
            errors.section_errors.append(
                "Missing one of {}".format(reference_value.keys()))
        elif validated > 1:
            errors.section_errors.append(
                "Only one of {} permitted".format(reference_value.keys()))
    elif isinstance(key, If):
        validate_key(key.key, suspicious, reference_value, cleaned, errors)
    elif key in suspicious:
        validate_value(key, suspicious[key], reference_value, cleaned, errors)
    else:
        #missing key error!
        print("missing key error")

def validate_value(key, value, reference_value, cleaned, errors):
    is_valid = True
    if isinstance(reference_value, dict):
        next_level_errors = FormErr()
        next_level_cleaned = {}
        validate(reference_value, value, next_level_cleaned, next_level_errors)
        if next_level_errors:
            errors[key] = next_level_errors
            is_valid = False
        if next_level_cleaned:
            cleaned[key] = next_level_cleaned
    else:
        if value != reference_value:
            is_valid = False
            errors[key].append('{} should equal {}'.format(
                    value, reference_value
            ))
        else:
            cleaned[key] = value
    return is_valid

def validate(schema, suspicious, cleaned, errors):
    for key, reference_value in schema.items():
        validate_key(key, suspicious, reference_value, cleaned, errors)

class Form:
    def __init__(self, schema):
        self.schema = schema

    def validate(self, suspicious):
        self.cleaned = {}
        self.errors = FormErr()
        validate(self.schema, suspicious, self.cleaned, self.errors)

