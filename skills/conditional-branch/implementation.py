"""conditional-branch 技能实现"""

import os
import json
import re
import ast
import operator


def execute_conditional_branch(params):
    """执行条件分支"""
    condition = params.get('condition')
    branches = params.get('branches', [])
    default_branch = params.get('default_branch', [])
    variables = params.get('variables', {})
    
    # 验证参数
    if not branches:
        return {"error": "请指定分支配置"}
    
    # 执行条件判断
    executed_branch = None
    branch_results = []
    
    for branch in branches:
        branch_condition = branch.get('condition')
        branch_tasks = branch.get('tasks', [])
        
        if not branch_condition:
            continue
        
        # 替换变量
        evaluated_condition = replace_variables(branch_condition, variables)
        
        # 评估条件
        try:
            condition_result = evaluate_condition(evaluated_condition)
        except Exception as e:
            return {"error": f"条件表达式评估失败: {str(e)}"}
        
        if condition_result:
            # 执行分支任务
            executed_branch = branch_condition
            
            # 模拟执行任务
            # 实际应用中，这里应该调用 task-runner 技能
            for task in branch_tasks:
                skill_name = task.get("skill")
                task_params = task.get("params", {})
                print(f"执行分支任务: {skill_name}, 参数: {task_params}")
                branch_results.append({"skill": skill_name, "result": "执行成功"})
            
            break
    
    # 如果没有分支被执行，执行默认分支
    if not executed_branch and default_branch:
        executed_branch = "default"
        for task in default_branch:
            skill_name = task.get("skill")
            task_params = task.get("params", {})
            print(f"执行默认分支任务: {skill_name}, 参数: {task_params}")
            branch_results.append({"skill": skill_name, "result": "执行成功"})
    
    return {
        "success": True,
        "executed_branch": executed_branch,
        "branch_results": branch_results
    }

def replace_variables(condition, variables):
    """替换条件表达式中的变量"""
    # 查找 ${var} 格式的变量
    pattern = r"\$\{([^}]+)\}"
    
    def replace_var(match):
        var_name = match.group(1)
        return str(variables.get(var_name, match.group(0)))
    
    return re.sub(pattern, replace_var, condition)

def evaluate_condition(condition):
    """安全地评估条件表达式
    
    支持的操作：
    - 比较操作符: ==, !=, >, <, >=, <=
    - 逻辑操作符: and, or, not
    - 字面值: 数字, 字符串, True, False, None
    
    Args:
        condition: 条件表达式字符串
        
    Returns:
        bool: 条件评估结果
        
    Raises:
        Exception: 如果表达式无法安全评估
    """
    # 定义支持的操作符
    operators = {
        ast.Eq: operator.eq,
        ast.NotEq: operator.ne,
        ast.Gt: operator.gt,
        ast.Lt: operator.lt,
        ast.GtE: operator.ge,
        ast.LtE: operator.le,
        ast.And: lambda a, b: a and b,
        ast.Or: lambda a, b: a or or,
        ast.Not: lambda a: not a,
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
    }
    
    def eval_node(node):
        """递归评估AST节点"""
        # 字面值
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.Str):
            return node.s
        elif isinstance(node, ast.NameConstant):
            return node.value
        
        # 变量名（不安全，拒绝）
        elif isinstance(node, ast.Name):
            if node.id in ('True', 'False', 'None'):
                return eval(ast.literal_eval(node.id))
            raise Exception(f"不允许使用变量: {node.id}")
        
        # 二元操作
        elif isinstance(node, ast.BinOp):
            left = eval_node(node.left)
            right = eval_node(node.right)
            op_type = type(node.op)
            if op_type in operators:
                return operators[op_type](left, right)
            else:
                raise Exception(f"不支持的操作符: {op_type}")
        
        # 布尔操作
        elif isinstance(node, ast.BoolOp):
            values = [eval_node(v) for v in node.values]
            if isinstance(node.op, ast.And):
                return all(values)
            elif isinstance(node.op, ast.Or):
                return any(values)
        
        # 比较操作
        elif isinstance(node, ast.Compare):
            left = eval_node(node.left)
            result = True
            for op, comparator in zip(node.ops, node.comparators):
                right = eval_node(comparator)
                op_type = type(op)
                if op_type in operators:
                    result = result and operators[op_type](left, right)
                    left = right
                else:
                    raise Exception(f"不支持的比较操作符: {op_type}")
            return result
        
        # 一元操作
        elif isinstance(node, ast.UnaryOp):
            operand = eval_node(node.operand)
            if isinstance(node.op, ast.Not):
                return not operand
            elif isinstance(node.op, ast.UAdd):
                return +operand
            elif isinstance(node.op, ast.USub):
                return -operand
        
        # 列表/元组
        elif isinstance(node, (ast.List, ast.Tuple)):
            return [eval_node(e) for e in node.elts]
        
        # 不支持的节点类型
        else:
            raise Exception(f"不支持的表达式类型: {type(node).__name__}")
    
    try:
        # 解析表达式为AST
        tree = ast.parse(condition, mode='eval')
        # 评估AST
        result = eval_node(tree.body)
        return bool(result)
    except SyntaxError as e:
        raise Exception(f"条件表达式语法错误: {str(e)}")
    except Exception as e:
        raise Exception(f"条件表达式评估错误: {str(e)}")

def execute_skill(params):
    """执行技能"""
    return execute_conditional_branch(params)
