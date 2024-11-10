
import re
import math
import yaml
import random
from collections import deque
from sympy import symbols, sympify
from CustomClass import CustomClass
from symboltable import derivedtable
from symboltable.symboltable import *
from symboltable.derivedtable import *

def parse_grammar_yml(file_name):
    """加载并解析 grammar.yml 文件"""
    with open(file_name, 'r', encoding="utf-8") as file:
        data = yaml.safe_load(file)
    return data

def dynamic_import(imports):
    """根据 grammar.yml 中的 imports 部分动态导入库"""
    for item in imports:
        # 判断导入格式
        try:
            if item.startswith('import '):
                # 支持 'import xxx' 和 'import xxx as yyy' 形式
                parts = item[len('import '):].split(' as ')
                module = parts[0]
                alias = parts[1] if len(parts) > 1 else None
                globals()[module] = __import__(module)
                if alias:
                    globals()[alias] = globals()[module]
            elif item.startswith('from '):
                # 支持 'from xxx import yyy' 形式
                module, components = item[len('from '):].split(' import ')
                components_list = components.split(', ')
                module_ref = __import__(module, fromlist=components_list)
                for comp in components_list:
                    globals()[comp] = getattr(module_ref, comp)
            else:
                print(f"Unsupported import format: {item}")
        except ImportError as e:
            print(f"Error importing {item}: {e}")


# 分析syntax中的终结符和非终结符,通过left_symbols和right_symbols
def analyze_syntax(syntax_rules):
    left_symbols = set()
    right_symbols = set()
    rule_map = {}

    for rule in syntax_rules:
        left_side, right_side = rule['rule'].split("->")
        left_side = left_side.strip()
        right_side = right_side.strip().split()

        left_symbols.add(left_side)
        right_symbols.update(right_side)

        # 添加规则和对应的动作到映射表
        rule_entry = {
            "rules": right_side,
            "actions": rule.get("actions", [])  # 处理可能没有 actions 的情况
        }
        rule_map.setdefault(left_side, []).append(rule_entry)

    terminals = right_symbols - left_symbols  # 终结符是右侧符号减去左侧符号
    nonterminals = left_symbols
    return nonterminals, terminals, rule_map, left_symbols, right_symbols


def generate_example_dfs(start_symbol, rule_map, nonterminals, terminals):
    stack = [start_symbol]  # 栈用于处理非终结符

    while stack:
        current_symbol = stack.pop()

        if current_symbol in nonterminals:
            # 随机选择适用规则进行展开
            if current_symbol in rule_map:
                chosen_rule = random.choice(rule_map[current_symbol])
                right_side = chosen_rule['rules'][::-1]  # 逆序加入栈以保持顺序
                stack.extend(right_side)

                # 处理语义动作部分
                actions = chosen_rule.get('actions', [])
                for action in actions:
                    execute_action(action)       
        else:
            # 如果是终结符，直接添加到结果
            generated_example.append(current_symbol)

    # 对生成的结果进行替换
    for i, symbol in enumerate(generated_example):
        if symbol in symbol_attributes and 'target' in symbol_attributes[symbol]:
            replacement = symbol_attributes[symbol]['target']
            if replacement:  # 只在替代值不为空时进行替换
                generated_example[i] = replacement

    return ' '.join(generated_example)


def execute_function(function_name: str):
    # Check if the specified function exists
    if function_name not in grammar_content['functions']:
        raise ValueError(f"Function '{function_name}' not found in the provided YAML.")
    
    function_data = grammar_content['functions'][function_name]
    params = function_data.get('params', [])
    implementation_code = function_data.get('implementation', '')

    # Prepare a mapping to replace '.' with a valid character
    converted_params = []
    param_replacements = {}

    for param in params:
        original_name = param['name']
        converted_name = original_name.replace('.', '_DOT_')
        param_replacements[original_name] = converted_name
        converted_params.append({'name': converted_name, 'type': param.get('type', None)})

    # Replace parameter names in the implementation code
    for original_name, converted_name in param_replacements.items():
        implementation_code = implementation_code.replace(original_name, converted_name)

    # Create function dynamically using exec with modified parameter names
    exec(implementation_code, globals())

    # Prepare parameter values with modified parameter names
    param_values = {}
    for param in converted_params:
        param_name = param['name']
        param_type = param.get('type', None)

        # Handle 'attribute' type
        if param_type == "attribute":
            symbol, attribute = param_name.replace('_DOT_', '.').split(".")
            param_values[param_name] = symbol_attributes.get(symbol, {}).get(attribute, None)
        
        # Handle 'symbol_table' type - use global symbol_table directly
        elif param_type == "symbol_table":
            param_values[param_name] = symbol_table  # Use the global symbol_table
        
        else:
            param_values[param_name] = None

    # Dynamically call the function with prepared values
    func = globals().get(function_name)
    if func:
        # Convert param_values keys back to original names
        converted_param_values = {
            param_replacements.get(key, key): value for key, value in param_values.items()
        }
        result = func(**converted_param_values)  # Call the function with the prepared parameter values
        return result
    else:
        raise ValueError(f"Function '{function_name}' could not be created.")
    

def execute_action(action):
    """根据 grammar.yml 动作执行相应的操作"""
    if ":=" in action:
        # 处理带 := 的动作 (赋值)
        left, right = map(str.strip, action.split(":="))

        func_name = next((name for name in grammar_content["functions"].keys() if name in right), None)

        if func_name:
            # 如果右侧是一个函数，调用执行函数并将结果赋值给左侧
            result = execute_function(func_name)
        else:
            # 处理常量赋值或符号间属性赋值运算
            result = compute_expression(right)

        # 更新符号表
        symbol_left, attribute_left = left.split(".")
        symbol_attributes.setdefault(symbol_left, {})[attribute_left] = result

    else:
        # 处理没有 := 的动作，调用函数
        func_name = next((name for name in grammar_content["functions"].keys() if name in action), None)
        if func_name:
            execute_function(func_name)

# 自定义一个函数来支持所有操作符和函数
def compute_expression(expr):    
    # 替换表达式中的symbol.attribute为其对应的值
    def evaluate_attribute(match):
        symbol, attribute = match.group(1), match.group(2)
        if symbol in symbol_attributes and attribute in symbol_attributes[symbol]:
            return str(symbol_attributes[symbol][attribute])
        return match.group(0)
    
    # 替换常量值
    def evaluate_constant(match):
        constant = match.group(0)
        if derived_table.has_value(constant):
            return str(derived_table.get_value(constant)['value'])
        return constant  # 如果常量不存在于 derived_table 中，保留原值

    # 替换常量
    expr = re.sub(r'\b\w+\b', evaluate_constant, expr)

    # 替换表达式中的symbol.attribute结构
    expr = re.sub(r'(\w+)\.(\w+)', evaluate_attribute, expr)

    # 对于包含数学函数（如sin, cos, sqrt等）的表达式，可以用sympy解析
    expr = sympify(expr)  # sympy可以处理各种操作符、函数以及数学表达式
    
    # 计算表达式的值
    result = expr.evalf()
    return result

# 自动判断起点符号：选择出现在左侧但从未出现在右侧的符号。
def get_start_symbol(left_symbols, right_symbols):

    # 起点符号应是没有在右侧出现的左侧符号
    start_candidates = left_symbols - right_symbols

    # 返回任意一个候选符号
    return next(iter(start_candidates))  

    # if start_candidates:
    #     return next(iter(start_candidates))  # 返回任意一个候选符号
    # else:
    #     raise ValueError("无法找到有效的起点符号，所有左侧符号都出现在右侧。")

if __name__ == "__main__":
    generated_example = []
    symbol_attributes = {}
    # 解析grammar.yml
    grammar_file_address = "input/grammar.yml"
    grammar_content = parse_grammar_yml(grammar_file_address)
    imports = grammar_content.get('imports', [])
    dynamic_import(imports)
    # 加载constants到派生表
    load_constants_into_derivedtable(grammar_content['constants'])

    # 加载attributes到符号表
    load_attributes_into_symboltable(grammar_content['attributes'])

    # 加载tables到符号表
    if 'tables' in grammar_content and grammar_content['tables']: 
        load_tables_into_symboltable(grammar_content['tables'])

    # 获取syntax规则
    syntax_rules = grammar_content['syntax']

    # 分析终结符、非终结符及其属性，并生成规则映射表
    nonterminals, terminals, rule_map, left_symbols, right_symbols = analyze_syntax(syntax_rules)

    # 自动智能判断起点符号
    start_symbol = get_start_symbol(left_symbols, right_symbols)

    # 从起点符号开始生成派生例子
    generate_example_dfs(start_symbol, rule_map, nonterminals, terminals)

    print("生成的随机语法例子:", ' '.join(generated_example))

    # print(show(generated_example, symbol_attributes['Table']['type'], symbol_attributes['Attribute']['type']))
    # print(symbol_table)
    # print(symbol_attributes)
    # print(symbol_attributes['Attribute']['target'])
    # # print(symbol_attributes['Attribute']['dif'])
    # print(symbol_attributes['Table']['value'])
    # print(symbol_table.get_symbol(random.choice(symbol_table.get_symbol(symbol_attributes['Table']['target'])['value'].split(','))))