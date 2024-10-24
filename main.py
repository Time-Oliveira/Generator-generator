from collections import deque
import yaml
import random
from symboltable import derivedtable
from symboltable.symboltable import *
from symboltable.derivedtable import *
from CustomClass import CustomClass

# 解析YAML文件
def parse_grammar_yml(file_name):
    with open(file_name, 'r', encoding="utf-8") as file:
        data = yaml.safe_load(file)
    return data

# 分析syntax中的终结符和非终结符
def analyze_syntax(syntax_rules):
    nonterminals = set()
    terminals = set()
    attributes = {}

    # 生成一个符号到规则的映射表
    rule_map = {}

    left_symbols = set()  # 左侧符号（非终结符）
    right_symbols = set()  # 右侧符号

    for rule in syntax_rules:
        # 获取规则左侧的非终结符
        left_side = rule['rule'].split("->")[0].strip()
        left_symbols.add(left_side)

        # 获取规则右侧的符号，可能包含终结符和非终结符
        right_side = rule['rule'].split("->")[1].strip().split()
        right_symbols.update(right_side)  # 记录右侧符号

        for symbol in right_side:
            if symbol not in left_symbols:
                terminals.add(symbol)

        # 将规则添加到映射表
        if left_side not in rule_map:
            rule_map[left_side] = []
        rule_map[left_side].append(right_side)

    # 确定终结符
    terminals.difference_update(left_symbols)
    nonterminals.update(left_symbols)

    return nonterminals, terminals, rule_map, left_symbols, right_symbols

# 使用BFS生成语法例子
def generate_example_bfs(start_symbol, rule_map, nonterminals, terminals):
    """
    使用广度优先搜索（BFS）生成语法例子，随机选择规则进行派生。
    """
    queue = deque([start_symbol])  # 队列用于处理非终结符
    result = []  # 存放最终结果

    while queue:
        current_symbol = queue.popleft()

        if current_symbol in nonterminals:
            # 随机选择适用规则进行展开
            if current_symbol in rule_map:
                chosen_rule = random.choice(rule_map[current_symbol])
                queue.extend(chosen_rule)  # 将右侧符号加入队列
        else:
            # 如果是终结符，直接添加到结果
            result.append(current_symbol)

    return ' '.join(result)

# 自动智能判断起点符号
def get_start_symbol(left_symbols, right_symbols):
    """
    自动判断起点符号：选择出现在左侧但从未出现在右侧的符号。
    """
    # 起点符号应是没有在右侧出现的左侧符号
    start_candidates = left_symbols - right_symbols

    if start_candidates:
        return next(iter(start_candidates))  # 返回任意一个候选符号
    else:
        raise ValueError("无法找到有效的起点符号，所有左侧符号都出现在右侧。")

if __name__ == "__main__":
    # 解析grammar.yml
    grammar_file_address = "input/grammar.yml"
    grammar_content = parse_grammar_yml(grammar_file_address)

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
    generated_example = generate_example_bfs(start_symbol, rule_map, nonterminals, terminals)

    print("生成的随机语法例子:", generated_example)