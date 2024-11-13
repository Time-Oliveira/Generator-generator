
import re
import math
import random
from typing import Any, Union, List, Tuple
from setup.readin import *
from collections import deque
from sympy import symbols, sympify
from CustomClass import CustomClass
from symboltable import derivedtable
from symboltable.symboltable import *
from symboltable.derivedtable import *

def generate_example_dfs(start_symbol, rule_map, nonterminals):
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

    # 对生成的结果进行替换, 将symbol替换为symbol.target中的值(symbol_attributes[symbol]['target'])
    for i, symbol in enumerate(generated_example):
        # 判断是否存在symbol.target
        if symbol in symbol_attributes and 'target' in symbol_attributes[symbol]:
            replacement = symbol_attributes[symbol]['target']
            # 判断是否存在symbol.target是否为空
            if replacement:
                generated_example[i] = replacement

    return ' '.join(generated_example)

"""执行函数并处理可能的后续计算"""
def execute_function(function_name: str, full_expr=None, args=None):
    if function_name not in grammar_content['functions']:
        raise ValueError(f"Function '{function_name}' not found in the provided YAML.")
    
    function_data = grammar_content['functions'][function_name]
    params = function_data.get('params', [])
    implementation_code = function_data.get('implementation', '')

    # 处理参数
    param_values = {}
    if args:
        for i, (param, arg) in enumerate(zip(params, args)):
            param_name = param['name']
            param_type = param.get('type', None)
            # 同时保存点号和下划线版本的参数名
            dot_name = param_name
            underscore_name = param_name.replace('.', '_')

            # 根据参数类型处理参数值
            if param_type == "symbol_table":
                param_values[dot_name] = param_values[underscore_name] = symbol_table
            elif param_type == "attribute":
                if isinstance(arg, (int, float)):
                    param_values[dot_name] = param_values[underscore_name] = arg
                elif '.' in arg:
                    symbol, attribute = arg.split('.')
                    value = symbol_attributes.get(symbol, {}).get(attribute, None)
                    param_values[dot_name] = param_values[underscore_name] = value
                elif '_' in arg:
                    symbol, attribute = arg.split('_')
                    value = symbol_attributes.get(symbol, {}).get(attribute, None)
                    param_values[dot_name] = param_values[underscore_name] = value
                else:
                    if isinstance(arg, str) and '(' in arg and ')' in arg:
                        func_name = arg[:arg.index('(')]
                        if func_name in grammar_content["functions"]:
                            inner_args = parse_function_args(arg)
                            value = execute_function(func_name, args=inner_args)
                            param_values[dot_name] = param_values[underscore_name] = value
                    else:
                        param_values[dot_name] = param_values[underscore_name] = arg
            else:
                param_values[dot_name] = param_values[underscore_name] = arg
    else:
        # 无参数函数的处理
        for param in params:
            param_name = param['name']
            param_type = param.get('type', None)
            dot_name = param_name
            underscore_name = param_name.replace('.', '_')

            if param_type == "attribute":
                if '.' in param_name:
                    symbol, attribute = param_name.split(".")
                else:
                    symbol, attribute = param_name.split("_")
                value = symbol_attributes.get(symbol, {}).get(attribute, None)
                param_values[dot_name] = param_values[underscore_name] = value
            elif param_type == "symbol_table":
                param_values[dot_name] = param_values[underscore_name] = symbol_table
            elif param_type == "constant":
                value = derived_table.get_value(param_name)
                param_values[dot_name] = param_values[underscore_name] = value
            else:
                param_values[dot_name] = param_values[underscore_name] = None

    # 处理实现代码中的变量引用
    # 将点号版本替换为实际的下划线版本
    modified_code = implementation_code
    for param in params:
        param_name = param['name']
        dot_version = param_name
        underscore_version = param_name.replace('.', '_')
        modified_code = modified_code.replace(dot_version, underscore_version)

    # 创建函数并执行
    exec(modified_code, globals())

    func = globals().get(function_name)
    if func:
        try:
            # 使用下划线版本的参数名调用函数
            filtered_params = {k: v for k, v in param_values.items() if '_' in k}
            result = func(**filtered_params)
        except TypeError as e:
            raise ValueError(f"Function '{function_name}' returned a non-numeric value: {e}")
        except ValueError as e:
            raise ValueError(f"Error executing function '{function_name}': {e}")
        
        if full_expr:
            remaining_expr = full_expr.replace(f"{function_name}()", str(result)).strip()
            if remaining_expr != str(result):
                return compute_expression(remaining_expr)
        return result
    else:
        raise ValueError(f"Function '{function_name}' could not be created.")
    
def parse_function_args(args_str: str) -> list:
    """Parse function call arguments."""
    args = []
    current_arg = ''
    paren_count = 0

    for char in args_str:
        if char == ',' and paren_count == 0:
            args.append(current_arg.strip())
            current_arg = ''
        else:
            if char == '(':
                paren_count += 1
            elif char == ')':
                paren_count -= 1
            current_arg += char

    if current_arg:
        args.append(current_arg.strip())

    processed_args = []
    for arg in args:
        if arg == 'symbol_table':
            processed_args.append(symbol_table)
        elif '.' in arg and not any(c in arg for c in '()[]{}'):
            symbol, attribute = arg.split('.')
            if symbol in symbol_attributes and attribute in symbol_attributes[symbol]:
                processed_args.append(symbol_attributes[symbol][attribute])
        elif arg.replace('.', '').isdigit():
            processed_args.append(float(arg))
        else:
            processed_args.append(arg)

    return processed_args


def compute_expression(expr: str):
    # Replace replacement expressions
    def evaluate_replacement(match):
        replacement_expr = match.group(1)
        return str(compute_expression(replacement_expr))

    expr = re.sub(r'\{(.*?)\}', evaluate_replacement, expr)

    # Handle nested function calls from inside out
    while True:
        # Find innermost function call
        match = re.search(r'(\w+)\((([^()]*|\([^()]*\))*)\)', expr)
        if not match:
            break
            
        func_name = match.group(1)
        args_str = match.group(2)
        
        # Check for name conflicts with custom functions
        if func_name in grammar_content['functions'] and hasattr(math, func_name):
            raise ValueError(f"Function name '{func_name}' conflicts with Python math module")
        
        # First evaluate any nested expressions in the arguments
        args = []
        if args_str:
            # Split args but preserve parentheses structure
            curr_arg = ""
            paren_count = 0
            for char in args_str + ',':
                if char == ',' and paren_count == 0:
                    if curr_arg.strip():
                        # Recursively evaluate each argument
                        evaluated_arg = compute_expression(curr_arg.strip())
                        args.append(evaluated_arg)
                    curr_arg = ""
                else:
                    if char == '(':
                        paren_count += 1
                    elif char == ')':
                        paren_count -= 1
                    curr_arg += char
        
        try:
            if hasattr(math, func_name):
                # Convert all arguments to float for math functions
                float_args = [float(arg) for arg in args]
                result = getattr(math, func_name)(*float_args)
            else:
                result = execute_function(func_name, args=args)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Error in function '{func_name}': {str(e)}")

        # Replace function call with result
        start, end = match.span()
        expr = expr[:start] + str(result) + expr[end:]

    # Handle symbol.attribute values and constants
    def evaluate_attribute(match):
        symbol, attribute = match.group(1), match.group(2)
        if symbol in symbol_attributes and attribute in symbol_attributes[symbol]:
            return str(symbol_attributes[symbol][attribute])
        return match.group(0)

    expr = re.sub(r'(\w+)\.(\w+)', evaluate_attribute, expr)

    def evaluate_constant(match):
        constant = match.group(0)
        if derived_table.has_value(constant):
            return str(derived_table.get_value(constant))
        return constant

    expr = re.sub(r'\b\w+\b', evaluate_constant, expr)

    try:
        result = float(sympify(expr).evalf())
        return result
    except:
        return expr

"""执行actions语句"""
def execute_action(action: str):
    # actions语句分为赋值语句和不赋值语句（函数执行语句）
    if ":=" in action:
        left, right = map(str.strip, action.split(":="))
        
        # 计算右侧表达式的值
        result = compute_expression(right)
        
        # 更新符号属性表
        symbol, attribute = left.split(".")
        symbol_attributes.setdefault(symbol, {})[attribute] = result
    else:
        # 处理不包含赋值的动作
        compute_expression(action)

if __name__ == "__main__":
    # 生成的最终语句
    generated_example = []

    # 用于保存symbol.attribute
    symbol_attributes = {}

    # 加载语法文件
    grammar_file_address = "input/grammar1.yml"
    grammar_content = parse_grammar_yml(grammar_file_address)
    
    # 获取命名空间，确保所有类都可用
    namespace = get_namespace()
    
    # 将命名空间中的类添加到全局命名空间
    globals().update(namespace)
    
    # 加载constants到派生表
    if 'constants' in grammar_content and grammar_content['constants']:
        load_constants_into_derivedtable(grammar_content['constants'])

    # 加载attributes到symbol table
    if 'attributes' in grammar_content and grammar_content['attributes']:
        load_attributes_into_symboltable(grammar_content['attributes'])

    # 加载tables到symbol table
    if 'tables' in grammar_content and grammar_content['tables']: 
        load_tables_into_symboltable(grammar_content['tables'])

    # 获取syntax规则
    syntax_rules = grammar_content['syntax']

    # 分析终结符、非终结符及其属性，并生成规则映射表
    nonterminals, terminals, rule_map, left_symbols, right_symbols = analyze_syntax(syntax_rules)

    # 自动智能判断起点符号
    start_symbol = get_start_symbol(left_symbols, right_symbols)
    
    # 从起点符号开始生成派生例子
    generate_example_dfs(start_symbol, rule_map, nonterminals)

    print("result:", ' '.join(generated_example))

    print(symbol_attributes)
    # print(show(generated_example, symbol_attributes['Table']['type'], symbol_attributes['Attribute']['type']))
    # print(symbol_table)
    # print(symbol_attributes)
    # print(symbol_attributes['Attribute']['target'])
    # # print(symbol_attributes['Attribute']['dif'])
    # print(symbol_attributes['Table']['value'])
    # print(symbol_table.get_symbol(random.choice(symbol_table.get_symbol(symbol_attributes['Table']['target'])['value'].split(','))))