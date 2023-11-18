import yaml

def verify_config_structure(config, template):
    for key, value in template.items():
        if key not in config:
            return False
        if isinstance(value, dict) and not isinstance(config[key], dict):
            return False
        if isinstance(value, dict) and not verify_config_structure(config[key], value):
            return False
        if not isinstance(value, dict) and not isinstance(config[key], value):
            return False
    return True

def validate(template):
    with open('dsc_config.yaml', 'r') as file:
        config = yaml.safe_load(file)

    if verify_config_structure(config, template):
        print("Configuration matches the desired structure.")
        return True
    else:
        print("Configuration doesn't match the desired structure.")
        return False
