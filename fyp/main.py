
import re
import math
import random
from typing import Any, Union, List, Tuple
from setup.readin import *
from collections import deque
from sympy import symbols, sympify
from CustomClass import CustomClass
from ConstantTable import ConstantTable
from symboltable.symboltable import *
from ConstantTable.ConstantTable import *

'''用dfs来派生example'''
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
            # 如果是terminal，直接添加到结果
            result.append(current_symbol)

    # 对生成的结果进行替换, 将symbol替换为symbol.target中的值(semantics[symbol]['target'])
    for index, symbol in enumerate(result):
        # 判断是否存在symbol.target
        if symbol in semantics and 'target' in semantics[symbol]:
            replacement = semantics[symbol]['target']
            # 判断是否存在symbol.target是否为空
            if replacement:
                result[index] = replacement

    return ' '.join(result)

"""执行函数并处理可能的后续计算
    Args:
        function_name (str): 要执行的函数名称。
        full_expr (str, optional): 完整的表达式,用于处理函数调用后的剩余部分。
        args (list, optional): 函数调用的参数列表。
"""
def execute_function(function_name: str, full_expr=None, args=None):
    # 检查函数是否存在于语法定义中
    if function_name not in grammar['functions']:
        raise ValueError(f"Function '{function_name}' not found in the provided YAML.")
    
    # 获取函数的数据
    function_data = grammar['functions'][function_name]
    params = function_data.get('params', [])
    implementation_code = function_data.get('implementation', '')

    # 处理参数
    param_values = {}
    if args:
        # 遍历函数的参数和对应的实参
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
                # 处理属性类型的参数
                if isinstance(arg, (int, float)):
                    # 如果参数是数值类型,直接赋值
                    param_values[dot_name] = param_values[underscore_name] = arg
                elif '.' in arg:
                    # 如果参数是"symbol.attribute"形式,拆分并从semantics获取值
                    symbol, attribute = arg.split('.')
                    value = semantics.get(symbol, {}).get(attribute, None)
                    param_values[dot_name] = param_values[underscore_name] = value
                elif '_' in arg:
                    # 如果参数是"symbol_attribute"形式,拆分并从semantics获取值
                    symbol, attribute = arg.split('_')
                    value = semantics.get(symbol, {}).get(attribute, None)
                    param_values[dot_name] = param_values[underscore_name] = value
                else:
                    # 如果参数是函数调用,递归执行函数并获取结果
                    if isinstance(arg, str) and '(' in arg and ')' in arg:
                        func_name = arg[:arg.index('(')]
                        if func_name in grammar["functions"]:
                            inner_args = parse_function_args(arg)
                            value = execute_function(func_name, args=inner_args)
                            param_values[dot_name] = param_values[underscore_name] = value
                    else:
                        # 其他情况直接赋值
                        param_values[dot_name] = param_values[underscore_name] = arg
            else:
                # 其他类型的参数直接赋值
                param_values[dot_name] = param_values[underscore_name] = arg
    else:
        # 无参数函数的处理
        for param in params:
            param_name = param['name']
            param_type = param.get('type', None)
            dot_name = param_name
            underscore_name = param_name.replace('.', '_')

            if param_type == "attribute":
                # 处理属性类型的参数
                if '.' in param_name:
                    symbol, attribute = param_name.split(".")
                else:
                    symbol, attribute = param_name.split("_")
                value = semantics.get(symbol, {}).get(attribute, None)
                param_values[dot_name] = param_values[underscore_name] = value
            elif param_type == "symbol_table":
                # 符号表类型的参数直接赋值
                param_values[dot_name] = param_values[underscore_name] = symbol_table
            elif param_type == "constant":
                # 常量类型的参数从ConstantTable获取值
                value = ConstantTable.get_value(param_name)
                param_values[dot_name] = param_values[underscore_name] = value
            else:
                # 其他类型的参数赋值为None
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
            # 处理函数调用后的剩余表达式
            remaining_expr = full_expr.replace(f"{function_name}()", str(result)).strip()
            if remaining_expr != str(result):
                return compute_expression(remaining_expr)
        return result
    else:
        raise ValueError(f"Function '{function_name}' could not be created.")
    
def parse_function_args(args_str: str) -> list:
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
            if symbol in semantics and attribute in semantics[symbol]:
                processed_args.append(semantics[symbol][attribute])
        elif arg.replace('.', '').isdigit():
            processed_args.append(float(arg))
        else:
            processed_args.append(arg)

    return processed_args

'''计算表达式的值'''
def compute_expression(expr: str):
    # 替换替换表达式
    def evaluate_replacement(match):
        replacement_expr = match.group(1)
        return str(compute_expression(replacement_expr))

    expr = re.sub(r'\{(.*?)\}', evaluate_replacement, expr)

    # 从内到外处理嵌套函数调用
    while True:
        # 查找最内层的函数调用
        match = re.search(r'(\w+)\((([^()]*|\([^()]*\))*)\)', expr)
        if not match:
            break
            
        func_name = match.group(1)
        args_str = match.group(2)
        
        # 检查自定义函数名与Python math模块的名称冲突
        if func_name in grammar['functions'] and hasattr(math, func_name):
            raise ValueError(f"Function name '{func_name}' conflicts with Python math module")
        
        # 首先评估参数中的任何嵌套表达式
        args = []
        if args_str:
            # 分割参数并保留括号结构
            curr_arg = ""
            paren_count = 0
            for char in args_str + ',':
                if char == ',' and paren_count == 0:
                    if curr_arg.strip():
                        # 递归评估每个参数
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
                # 如果是math模块中的函数,将所有参数转换为浮点型
                float_args = [float(arg) for arg in args]
                result = getattr(math, func_name)(*float_args)
            else:
                # 否则递归执行函数
                result = execute_function(func_name, args=args)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Error in function '{func_name}': {str(e)}")

        # 用结果替换函数调用
        start, end = match.span()
        expr = expr[:start] + str(result) + expr[end:]

    # 处理symbol.attribute
    def evaluate_attribute(match):
        symbol, attribute = match.group(1), match.group(2)
        if symbol in semantics and attribute in semantics[symbol]:
            # 如果是"symbol.attribute"形式,从semantics获取值
            return str(semantics[symbol][attribute])
        return match.group(0)

    expr = re.sub(r'(\w+)\.(\w+)', evaluate_attribute, expr)

    # 处理constant
    def evaluate_constant(match):
        constant = match.group(0)
        if ConstantTable.has_value(constant):
            # 如果是常量,从ConstantTable获取值
            return str(ConstantTable.get_value(constant))
        return constant

    expr = re.sub(r'\b\w+\b', evaluate_constant, expr)

    try:
        # 尝试使用sympify计算表达式结果
        result = float(sympify(expr).evalf())
        return result
    except:
        # 如果计算失败,返回表达式本身
        return expr

"""执行actions语句"""
def execute_action(action: str):
    # actions语句分为赋值语句和不赋值语句（函数执行语句）
    if ":=" in action:
        left, right = map(str.strip, action.split(":="))
        
        # 计算右侧表达式的值
        result = compute_expression(right)
        
        # 更新semantics
        symbol, attribute = left.split(".")
        semantics.setdefault(symbol, {})[attribute] = result
    else:
        # 处理不包含赋值的动作
        compute_expression(action)

if __name__ == "__main__":
    # 生成的最终语句
    result = []

    # 用于保存symbol.attribute
    semantics = {}

    # 加载语法文件
    grammar_file_address = "input/grammar1.yml"
    grammar = parse_grammar_yml(grammar_file_address)
    
    # 获取命名空间，确保所有类都可用
    namespace = get_namespace()
    
    # 将命名空间中的类添加到全局命名空间
    globals().update(namespace)
    
    # 加载constants到派生表
    if 'constants' in grammar and grammar['constants']:
        load_constants_into_derivedtable(grammar['constants'])

    # 加载columns到symbol table
    if 'columns' in grammar and grammar['columns']:
        load_columns_into_symboltable(grammar['columns'])

    # 加载tables到symbol table
    if 'tables' in grammar and grammar['tables']: 
        load_tables_into_symboltable(grammar['tables'])

    # 获取syntax规则
    syntax_rules = grammar['syntax']

    # 分析终结符、非终结符及其属性，并生成规则映射表
    nonterminals, terminals, rule_map, left_symbols, right_symbols = analyze_syntax(syntax_rules)

    # 自动智能判断起点符号
    start_symbol = get_start_symbol(left_symbols, right_symbols)
    
    # 从起点符号开始生成派生例子
    generate_example_dfs(start_symbol, rule_map, nonterminals)

    # 打印最终的example
    print("result:", ' '.join(result))

    # 以下为测试用的语句

    # 打印symbol_table
    # print(symbol_table)

    # 打印所有的xxx.xxx
    # print(semantics)

    # 打印所有的Table.value
    # print(semantics['Table']['value'])

    # print(semantics['Attribute']['dif'])

    # print(semantics['Attribute']['target'])

    # print(symbol_table.get_symbol(random.choice(symbol_table.get_symbol(semantics['Table']['target'])['value'].split(','))))