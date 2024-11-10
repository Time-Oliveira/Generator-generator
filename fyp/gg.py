import re
import random

def parse_rules(filename):
    rules = {}
    assignments = {}
    with open(filename, 'r') as file:
        content = file.readlines()

    current_rule = None
    for line in content:
        line = line.strip()
        if not line:
            continue

        # Parse rules like E -> SF
        rule_match = re.match(r'(\w+) -> (.+)', line)
        if rule_match:
            current_rule, rule_value = rule_match.groups()
            rules[current_rule] = rule_value
            continue

        # Parse assignments like F_dif := generator difficult
        assignment_match = re.match(r'(\w+)\s*:=\s*(.+)', line)
        if assignment_match:
            var_name, var_value = assignment_match.groups()
            if current_rule:
                if current_rule not in assignments:
                    assignments[current_rule] = []
                assignments[current_rule].append((var_name, var_value))

    return rules, assignments

def generate_sample(rules, assignments, start_symbol):
    if start_symbol not in rules:
        return start_symbol

    result = []
    rule_expansion = rules[start_symbol]
    for symbol in rule_expansion.split():
        result.append(generate_sample(rules, assignments, symbol))

    # Apply assignments
    if start_symbol in assignments:
        for var_name, var_value in assignments[start_symbol]:
            if 'generator' in var_value:
                _, difficulty = var_value.split()
                generated_value = f"generated_value_based_on_{difficulty}"
                result.append(f"{var_name} = {generated_value}")
            elif 'rand' in var_value:
                parts = re.findall(r'\w+', var_value)
                random_value = random.randint(1, 100)  # Example random value generation
                result.append(f"{var_name} = random({parts[1]}, {random_value})")
            else:
                result.append(f"{var_name} = {var_value}")

    return ' '.join(result)

if __name__ == "__main__":
    rules, assignments = parse_rules('input/grammar.txt')
    start_symbol = 'E'
    sample = generate_sample(rules, assignments, start_symbol)
    print("Generated Sample:")
    print(sample)
