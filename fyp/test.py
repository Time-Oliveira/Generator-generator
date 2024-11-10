# File path: main.py
import yaml
import os

def load_yaml_and_execute_function(file_path: str, function_name: str):
    # Load YAML file
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")
    
    with open(file_path, 'r', encoding = 'utf-8') as file:
        data = yaml.safe_load(file)
    
    # Check if the specified function exists
    if function_name not in data['functions']:
        raise ValueError(f"Function '{function_name}' not found in the provided YAML.")
    
    function_data = data['functions'][function_name]
    params = function_data.get('params', [])
    implementation_code = function_data.get('implementation', '')

    # Create function dynamically
    exec(implementation_code, globals())

    # Prepare parameter names
    param_names = [param['name'] for param in params]

    # Generate sample values for demonstration (you can replace these with actual values as needed)
    sample_values = {name: None for name in param_names}

    # Dynamically call the function with sample values (replace with real data as needed)
    if function_name in globals():
        func = globals()[function_name]
        result = func(**sample_values)  # Modify this line if sample_values do not match expected arguments
        return result
    else:
        raise ValueError(f"Function '{function_name}' could not be created.")

# Usage example
if __name__ == "__main__":
    result = load_yaml_and_execute_function('input/grammar.yml', 'select')
    print(result)
