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

class And:
    def __init__(self, *conditions):
        self.conditions = conditions

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

    def __repr__(self):
        return "<[{}]{{{}}}>".format(
            ", ".join(self.section_errors),
            "\n".join(["{}:{}".format(key, value) for key, value in self.items()])
        )

    #TODO: len should calculate all errors recursively? at least include section_errors

def path_exists(path, structure):
    place = structure
    for key in path:
        try:
            place = place[key]
        except (KeyError, IndexError):
            return False
    return True

def validate_key(key, suspicious, reference_value, cleaned, errors, entire_structure):
    validated = True
    if isinstance(key, Optional):
        key = key.key
        if key in suspicious:
            validated = validate_key(key, suspicious, reference_value,
                                     cleaned, errors, entire_structure)
    elif key == Or:
        validated = False
        for orkey, orvalue in reference_value.items():
            if orkey in suspicious:
                validate_key(orkey, suspicious, orvalue, cleaned,
                             errors, entire_structure)
                validated = True
        if not validated:
            errors.section_errors.append(
                "Missing any of {}".format(reference_value.keys()))
    elif key == XOr:
        validated = 0
        for orkey, orvalue in reference_value.items():
            if orkey in suspicious:
                validate_key(orkey, suspicious, orvalue, cleaned, errors, entire_structure)
                validated += 1
        if validated == 0:
            errors.section_errors.append(
                "Missing one of {}".format(reference_value.keys()))
            validated = False
        elif validated > 1:
            errors.section_errors.append(
                "Only one of {} permitted".format(reference_value.keys()))
            validated = False
        else:
            validated = True
    elif isinstance(key, If):
        exists = True
        for path in key.paths:
            if not path_exists(path, entire_structure):
                exists = False
                break
        if exists:
            validated = validate_key(key.key, suspicious, reference_value,
                                     cleaned, errors, entire_structure)
        #TODO: what happens if the key exists, but paths weren't found?
    elif key in suspicious:
        validated = validate_value(key, suspicious[key], reference_value,
                                   cleaned, errors, entire_structure)
    else:
        errors.section_errors.append("Missing {}".format(key))
        validated = False
    return validated

def validate_value(key, value, reference_value, cleaned, errors, entire_structure):
    valid = True
    if isinstance(reference_value, dict):
        next_level_errors = FormErr()
        next_level_cleaned = {}
        valid = validate(reference_value, value, next_level_cleaned,
                         next_level_errors, entire_structure)
        if not valid:
            errors[key] = next_level_errors
        if next_level_cleaned:
            cleaned[key] = next_level_cleaned
    elif isinstance(reference_value, And):
        for condition in reference_value.conditions:
            if not validate_value(key, value, condition, cleaned,
                                  errors, entire_structure):
                valid = False
            if not valid:
                del cleaned[key]
    elif callable(reference_value):
        try:
            result = reference_value(value)
        except Exception as e:
            errors[key].append(str(e))
            return False
        if result:
            cleaned[key] = value
        else:
            errors[key].append("{} did not match {}".format(
                reference_value.__name__,
                value
            ))
            valid = False
    else:
        if value != reference_value:
            errors[key].append('{} should equal {}'.format(
                    value, reference_value
            ))
            valid = False
        else:
            cleaned[key] = value
    return valid

def validate(schema, suspicious, cleaned, errors, entire_structure):
    #TODO: modify the whole thing to return True for validated and False for invalid.
    valid = True
    for key, reference_value in schema.items():
        if not validate_key(key,
                            suspicious,
                            reference_value,
                            cleaned,
                            errors,
                            entire_structure):
            valid = False
    return valid

class Form:
    def __init__(self, schema):
        self.schema = schema

    def validate(self, suspicious):
        self.cleaned = {}
        self.errors = FormErr()
        return validate(self.schema, suspicious, self.cleaned,
                        self.errors, suspicious)

