import yaml
import importlib

def dynamic_import(imports):
    """根据 grammar.yml 中的 imports 部分动态导入库"""
    namespace = {}
    
    for item in imports:
        try:
            if isinstance(item, str):  # 确保item是字符串
                if item.startswith('import '):
                    # 处理 'import xxx' 和 'import xxx as yyy'
                    parts = item[len('import '):].strip().split(' as ')
                    module_name = parts[0].strip()
                    alias = parts[1].strip() if len(parts) > 1 else module_name
                    
                    module = importlib.import_module(module_name)
                    namespace[alias] = module
                    globals()[alias] = module
                    
                elif item.startswith('from '):
                    # 处理 'from xxx import yyy'
                    _, rest = item.split('from ', 1)
                    module_path, imports = rest.strip().split(' import ')
                    
                    module = importlib.import_module(module_path)
                    for name in imports.split(', '):
                        name = name.strip()
                        if ' as ' in name:
                            name, alias = name.split(' as ')
                        else:
                            alias = name
                            
                        obj = getattr(module, name)
                        namespace[alias] = obj
                        globals()[alias] = obj
                        
        except ImportError as e:
            print(f"Error importing {item}: {e}")
        except Exception as e:
            print(f"Unexpected error while importing {item}: {e}")
    
    return namespace