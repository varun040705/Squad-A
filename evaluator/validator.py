import json


REQUIRED_ELEMENTS = ["walls", "doors", "windows", "rooms"]


def load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def validate_schema(data):
    errors = []

    if not isinstance(data, dict):
        errors.append("Root must be a JSON object.")
        return errors

    if "project" not in data:
        errors.append("Missing 'project'.")
        return errors

    project = data["project"]

    if "levels" not in project:
        errors.append("Missing 'project.levels'.")
    elif not isinstance(project["levels"], list):
        errors.append("'project.levels' must be a list.")
    elif len(project["levels"]) == 0:
        errors.append("'project.levels' cannot be empty.")
    else:
        for index, level in enumerate(project["levels"]):
            if not isinstance(level, dict):
                errors.append(f"Level {index} must be an object.")
                continue

            for element in REQUIRED_ELEMENTS:
                if element not in level:
                    errors.append(
                        f"Missing 'project.levels[{index}].{element}'."
                    )
                elif not isinstance(level[element], list):
                    errors.append(
                        f"'project.levels[{index}].{element}' must be a list."
                    )

    if "scale" not in project:
        errors.append("Missing 'project.scale'.")
    else:
        scale = project["scale"]

        if not isinstance(scale, dict):
            errors.append("'project.scale' must be an object.")
        elif "mm_per_pixel" not in scale:
            errors.append("Missing 'project.scale.mm_per_pixel'.")
        elif not isinstance(scale["mm_per_pixel"], (int, float)):
            errors.append("'mm_per_pixel' must be a number.")
        elif scale["mm_per_pixel"] <= 0:
            errors.append("'mm_per_pixel' must be greater than 0.")

    return errors


def validate_file(file_path):
    try:
        data = load_json(file_path)
    except json.JSONDecodeError as error:
        return [f"Invalid JSON: {error}"]
    except FileNotFoundError:
        return [f"File not found: {file_path}"]

    return validate_schema(data)