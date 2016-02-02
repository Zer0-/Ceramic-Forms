# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

class Optional:
    def __init__(self, key):
        self.key = key

class Or:
    def __init__(self, *conditions):
        self.conditions = conditions

class XOr:
    def __init__(self, *conditions):
        self.conditions = conditions

class If:
    def __init__(self, paths, key):
        self.paths = paths
        self.key = key

class And:
    def __init__(self, *conditions):
        self.conditions = conditions

class Use:
    def __init__(self, fn):
        self.fn = fn

class Msg:
    def __init__(self, validator, errmsg):
        self.validator = validator
        self.errmsg = errmsg

class SectionErrors(list):
    def __init__(self, parent):
        self.parent = parent

    def append(self, *args, **kwargs):
        self.parent['__section_errors__'] = self
        list.append(self, *args, **kwargs)


class FormErr(dict):
    def __init__(self, *args, **kwargs):
        self.section_errors = SectionErrors(self)
        dict.__init__(self, *args, **kwargs)

    def __getitem__(self, key):
        value = self.get(key)
        if value is None:
            value = []
            self[key] = value
        return value

    #TODO: len should calculate all errors recursively? at least include section_errors?

def path_exists(path, structure):
    place = structure
    for key in path:
        try:
            place = place[key]
        except (KeyError, IndexError):
            return False
    return True

def validate_key(
        key,
        suspicious,
        reference_value,
        errors,
        entire_structure,
        validated_keys):
    validated = False
    cleaned = []
    if isinstance(key, Optional):
        validated = True
        key = key.key
        if key in suspicious:
            validated, clean = validate_key(
                key,
                suspicious,
                reference_value,
                errors,
                entire_structure,
                validated_keys
            )
            cleaned.extend(clean)
    elif key == Or:
        validated = True
        none_exist = True
        for orkey, orvalue in reference_value.items():
            if orkey in suspicious:
                none_exist = False
                cleaned_key = orkey
                valid, clean = validate_key(
                    orkey,
                    suspicious,
                    orvalue,
                    errors,
                    entire_structure,
                    validated_keys
                )
                if valid:
                    cleaned.extend(clean)
                validated = validated and valid
        if none_exist:
            validated = False
            errors.section_errors.append(
                "Missing any of {}".format(reference_value.keys()))
    elif key == XOr:
        validated = 0
        for orkey, orvalue in reference_value.items():
            if orkey in suspicious:
                valid, clean = validate_key(
                    orkey,
                    suspicious,
                    orvalue,
                    errors,
                    entire_structure,
                    validated_keys
                )
                if valid:
                    cleaned.extend(clean)
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
    elif isinstance(key, And):
        validated = True
        for raw_key in suspicious:
            err = FormErr()
            valid_key, clean_key = validate_value(
                0,
                raw_key,
                key,
                err,
                entire_structure
            )
            validated = validated and valid_key
            if not valid_key:
                errors.section_errors.extend(err[0])
            valid_value, clean = validate_value(
                raw_key,
                suspicious[raw_key],
                reference_value,
                errors,
                entire_structure
            )
            validated = validated and valid_value
            validated_keys.add(raw_key)
            if valid_key and valid_value:
                cleaned.append((clean_key, clean))
    elif isinstance(key, If):
        exists = True
        validated = True
        for path in key.paths:
            if not path_exists(path, entire_structure):
                exists = False
                break
        if exists:
            validated, clean = validate_key(
                key.key,
                suspicious,
                reference_value,
                errors,
                entire_structure,
                validated_keys
            )
            cleaned.extend(clean)
        #TODO: what happens if the key exists, but paths weren't found?
    elif isinstance(key, Msg):
        validated, clean = validate_key(
            key.validator,
            suspicious,
            reference_value,
            FormErr(),
            entire_structure,
            validated_keys
        )
        if not validated:
            errors.section_errors.append(key.errmsg)
        else:
            cleaned.extend(clean)
    elif key in suspicious:
        validated_keys.add(key)
        validated, clean = validate_value(
            key,
            suspicious[key],
            reference_value,
            errors,
            entire_structure
        )
        if validated:
            cleaned.append((key, clean))
    else:
        errors.section_errors.append("Missing {}".format(key))
        validated = False
    return validated, cleaned

def append_dict_or_list(collection, key, val):
    try:
        collection[key] = val
    except IndexError:
        collection.append(val)

def validate_value(key, value, reference_value, errors, entire_structure):
    valid = False
    clean = None
    if isinstance(reference_value, dict):
        next_level_errors = FormErr()
        valid, clean = validate_map(
            reference_value,
            value,
            next_level_errors,
            entire_structure
        )
        if not valid:
            errors[key] = next_level_errors
    elif isinstance(reference_value, list):
        next_level_errors = FormErr()
        valid, clean = validate_sequence(reference_value, value,
                             next_level_errors, entire_structure)
        if not valid:
            errors[key] = next_level_errors
    elif isinstance(reference_value, Use):
        valid = True
        try:
            result = reference_value.fn(value)
        except Exception as e:
            errors[key].append(str(e))
            return False, None
        clean = result
    elif isinstance(reference_value, And):
        valid = True
        for condition in reference_value.conditions:
            _valid, clean = validate_value(key, value, condition,
                                  errors, entire_structure)
            value = clean
            valid = valid and _valid
            if not valid:
                break
    elif isinstance(reference_value, Or):
        valid = False
        dummy_err = FormErr()
        for condition in reference_value.conditions:
            valid, clean = validate_value(key, value, condition,
                                  dummy_err, entire_structure)
            if valid:
                break
        if not valid:
            errors[key].append('{} is not valid for any {}'.format(
                value,
                reference_value.conditions
            ))
    elif isinstance(reference_value, Msg):
        valid, clean = validate_value(key, value, reference_value.validator,
                                  FormErr(), entire_structure)
        if not valid:
            errors[key].append(reference_value.errmsg)
    elif type(reference_value) is type:
        if type(value) is reference_value:
            valid = True
            clean = value
        else:
            errors[key].append("{} must be of type {}".format(
                repr(value), reference_value.__name__
            ))
            valid = False
    elif callable(reference_value):
        try:
            result = reference_value(value)
        except Exception as e:
            #Bug hunting might have just gotten harder with a catchall Exception.
            errors[key].append(str(e))
            return False, None
        if result:
            valid = True
            clean = value
        else:
            valid = False
            errors[key].append("{} did not match {}".format(
                reference_value.__name__,
                value
            ))
    else:
        valid = value == reference_value
        clean = value
        if not valid:
            errors[key].append('{} should equal {}'.format(
                    repr(value), repr(reference_value)
            ))
            clean = None
    return valid, clean

def validate_sequence(schema, suspicious, errors, entire_structure):
    all_valid = True
    cleaned = []
    for i, value in enumerate(suspicious):
        valid = False
        for validator in schema:
            valid, clean = validate_value(
                i,
                value,
                validator,
                errors,
                entire_structure
            )
            cleaned.append(clean)
            if valid:
                break
        if valid and i in errors:
            del errors[i]
        all_valid = all_valid and valid
    return all_valid, cleaned

def validate_map(schema, suspicious, errors, entire_structure):
    all_valid = True
    cleaned = {}
    keys_validated = set()
    for key, reference_value in schema.items():
        valid, clean = validate_key(
            key,
            suspicious,
            reference_value,
            errors,
            entire_structure,
            keys_validated
        )
        for key, value in clean:
            cleaned[key] = value
        all_valid = all_valid and valid

    extra_keys = suspicious.keys() - keys_validated
    if extra_keys:
        all_valid = False
        for extra_key in extra_keys:
            errors.section_errors.append('Unexpected key {}'.format(extra_key))
    return all_valid, cleaned

#TODO: Optional, If as key.
#TODO: Optional should check existence, not validation.
class Form:
    def __init__(self, schema):
        self.schema = schema

    def validate(self, suspicious):
        self.errors = FormErr()
        if isinstance(self.schema, dict):
            valid, clean = validate_map(
                self.schema,
                suspicious, 
                self.errors,
                suspicious
            )
        elif isinstance(self.schema, list):
            valid, clean = validate_sequence(
                self.schema,
                suspicious,
                self.errors,
                suspicious
            )
        else:
            err = FormErr()
            valid, clean = validate_value(
                0,
                suspicious,
                self.schema,
                err,
                None
            )
            self.errors.section_errors.extend(err[0])
        self.cleaned = clean
        return valid
