import yaml

def verify_config_structure(config, template):
    validated_config = {}
    for key, value in template.items():
        if key not in config:
            return False, {}
        if isinstance(value, dict) and not isinstance(config[key], dict):
            return False, {}
        if isinstance(value, dict):
            valid, sub_config = verify_config_structure(config[key], value)
            if not valid:
                return False, {}
            validated_config[key] = sub_config
        else:
            validated_config[key] = config[key]

    return True, validated_config

def get_validated_fields(file_path, fields):
    try:
        with open(file_path, 'r') as file:
            config_data = yaml.safe_load(file)
            valid_structure, validated_fields = verify_config_structure(config_data, fields)

            if valid_structure:
                return validated_fields, ''  # Return the validated fields
            else:
                return None, 'Config structure doesn\'t match the template.'
    except FileNotFoundError:
        return None, 'File not found'