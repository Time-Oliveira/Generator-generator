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

def analyze_syntax(syntax_rules):
    nonterminals = set()
    terminals = set()
    attributes = {}

    for rule in syntax_rules:
        # 获取规则左侧的非终结符
        left_side = rule['rule'].split("->")[0].strip()
        nonterminals.add(left_side)

        # 获取规则右侧的符号，可能包含终结符和非终结符
        right_side = rule['rule'].split("->")[1].strip().split()

        for symbol in right_side:
            # 如果符号不是非终结符，则视为终结符
            if symbol not in nonterminals:
                terminals.add(symbol)

        # 处理actions部分，提取属性
        if 'actions' in rule:
            for action in rule['actions']:
                parts = action.split(":=")
                left_part = parts[0].strip()
                if "." in left_part:
                    symbol_name, attr = left_part.split(".")
                    if symbol_name not in attributes:
                        attributes[symbol_name] = []
                    if attr not in attributes[symbol_name]:
                        attributes[symbol_name].append(attr)

    # 确定终结符
    terminals.difference_update(nonterminals)
    
    return nonterminals, terminals, attributes

if __name__ == "__main__":
    # 解析grammar.yml
    grammar_file_address = "input/grammar.yml"
    grammar_content = parse_grammar_yml(grammar_file_address)

    load_constants_into_derivedtable(grammar_content['constants'])

    # 加载attributes到符号表
    load_attributes_into_symboltable(grammar_content['attributes'])

    # 加载tables到符号表
    if 'tables' in grammar_content and grammar_content['tables']: 
        load_tables_into_symboltable(grammar_content['tables'])


    syntax_rules = grammar_content['syntax']

    # 分析终结符、非终结符及其属性
    nonterminals, terminals, attributes = analyze_syntax(syntax_rules)

    # 输出分析结果
    print("非终结符 (Nonterminals):", nonterminals)
    print("终结符 (Terminals):", terminals)
    print("符号属性 (Attributes):", attributes)
