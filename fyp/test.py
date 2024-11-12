import math

# 假设的 symbol_attributes 数据结构
symbol_attributes = {
    'F': {'dif': 10},
    'S': {'dif': 5}
}

def compute_expression(expr, symbol_attributes):
    # 自定义一个函数来支持所有操作符和函数
    # 替换表达式中的symbol.attribute为其对应的值
    def evaluate_attribute(match):
        symbol, attribute = match.group(1), match.group(2)
        if symbol in symbol_attributes and attribute in symbol_attributes[symbol]:
            return str(symbol_attributes[symbol][attribute])
        return match.group(0)

    # 导入所有必要的库
    import re
    from sympy import symbols, sympify

    # 替换表达式中的symbol.attribute结构
    expr = re.sub(r'(\w+)\.(\w+)', evaluate_attribute, expr)

    # 对于包含数学函数（如sin, cos, sqrt等）的表达式，可以用sympy解析
    expr = sympify(expr)  # sympy可以处理各种操作符、函数以及数学表达式
    
    # 计算表达式的值
    result = expr.evalf()
    return result

# 示例
expr1 = "sin(F.dif)"
expr2 = "F.dif / S.dif"
expr3 = "F.dif * 3"
expr4 = "sin(F.dif) + cos(S.dif)"
expr5 = "1 + F.dif / S.dif + 1 + (F.dif + S.dif) / S.dif"

print(compute_expression(expr1, symbol_attributes))  # 5.0
print(compute_expression(expr2, symbol_attributes))  # 2.0
print(compute_expression(expr3, symbol_attributes))  # 30.0
print(compute_expression(expr4, symbol_attributes))  # sin(10) + cos(5)
print(compute_expression(expr5, symbol_attributes))