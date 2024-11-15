# setup/readin.py

import yaml
import importlib
from typing import Dict, Any

"""分析syntax中的terminal和noterminal,通过left_symbols和right_symbols"""
def analyze_syntax(syntax_rules):
    left_symbols, right_symbols = set(), set()
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

"""自动判断start_symbol: 选择出现在左侧但从未出现在右侧的符号"""
def get_start_symbol(left_symbols, right_symbols):

    # 起点符号应是没有在右侧出现的左侧符号
    start_candidates = left_symbols - right_symbols

    if start_candidates:
        # 如果start_symbol有多个，返回任意一个候选符号
        return next(iter(start_candidates))
    else:
        raise ValueError("无法找到有效的起点符号，所有左侧符号都出现在右侧。")

"""处理语法文件加载和动态导入的类"""
class GrammarLoader:
    def __init__(self):
        self.namespace: Dict[str, Any] = {}
        
    """加载并解析 grammar.yml 文件"""
    def parse_grammar_yml(self, file_name: str) -> dict:
        with open(file_name, 'r', encoding="utf-8") as file:
            data = yaml.safe_load(file)

        # 处理grammar.yml中的imports部分
        imports = data.get('imports', [])
        self.namespace = self.dynamic_import(imports)
        
        custom_types = data.get('custom_types', [])
        
        # 在包含已导入模块的命名空间中执行自定义代码
        for custom_type in custom_types:
            code = custom_type.get('code', '')
            exec(code, self.namespace)
            
            # 将自定义类添加到模块的全局命名空间
            globals().update(self.namespace)
            
            # 如果有name字段，确保类被正确注册
            if 'name' in custom_type:
                class_name = custom_type['name']
                if class_name in self.namespace:
                    globals()[class_name] = self.namespace[class_name]
        
        return data

    """根据 grammar.yml 中的 imports 部分动态导入库
    现在支持的格式：                                        
    import xxx
    import xxx, xxx
    from xxx import xxx
    from xxx import *
    from xxx import xxx, xxx, xxx
    """                   
    def dynamic_import(self, imports: list) -> dict:
        namespace = self.namespace.copy()
        
        for item in imports:
            try:
                if isinstance(item, str):
                    if item.startswith('import '):
                        # 去掉'import'前缀
                        import_statement = item[len('import '):].strip()
                        
                        # Handle multiple imports (e.g., 'import xxx, yyy, zzz')
                        for module_spec in import_statement.split(','):
                            module_spec = module_spec.strip()
                            
                            # Handle 'import xxx as yyy'
                            parts = module_spec.split(' as ')
                            module_name = parts[0].strip()
                            alias = parts[1].strip() if len(parts) > 1 else module_name
                            
                            module = importlib.import_module(module_name)
                            namespace[alias] = module
                            globals()[alias] = module
                            
                    elif item.startswith('from '):
                        # Remove 'from ' prefix and split into module path and imports
                        _, rest = item.split('from ', 1)
                        module_path, imports_part = rest.strip().split(' import ')
                        module = importlib.import_module(module_path)
                        
                        if imports_part.strip() == '*':
                            # Handle 'from xxx import *'
                            # Get all public attributes (not starting with '_')
                            for name in dir(module):
                                if not name.startswith('_'):
                                    obj = getattr(module, name)
                                    namespace[name] = obj
                                    globals()[name] = obj
                        else:
                            # Handle regular imports and multiple imports
                            for name in imports_part.split(','):
                                name = name.strip()
                                if ' as ' in name:
                                    orig_name, alias = name.split(' as ')
                                    orig_name = orig_name.strip()
                                    alias = alias.strip()
                                else:
                                    orig_name = alias = name
                                    
                                obj = getattr(module, orig_name)
                                namespace[alias] = obj
                                globals()[alias] = obj
                                
            except ImportError as e:
                print(f"Error importing {item}: {e}")
            except Exception as e:
                print(f"Unexpected error while importing {item}: {e}")
        
        return namespace

    def get_namespace(self) -> dict:
        """返回当前命名空间"""
        return self.namespace

# 创建一个全局的GrammarLoader实例
grammar_loader = GrammarLoader()

# 导出需要的函数和变量
def parse_grammar_yml(file_name: str) -> dict:
    return grammar_loader.parse_grammar_yml(file_name)

def get_namespace() -> dict:
    return grammar_loader.get_namespace()