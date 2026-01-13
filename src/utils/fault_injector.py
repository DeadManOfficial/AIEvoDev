"""
Fault Injector - AST-based code mutation for adversarial testing.
"""
import ast
import random
from typing import List


class FaultInjector(ast.NodeTransformer):
    """
    A class to inject simple, deterministic faults into Python AST nodes.
    This is a very basic, illustrative fault injector.
    """
    def __init__(self, target_fault_count=1):
        self.target_fault_count = target_fault_count
        self.faults_injected = 0
        self.possible_fault_locations = []

    def visit(self, node):
        # Collect possible fault injection locations
        if isinstance(node, (ast.BinOp, ast.Compare, ast.BoolOp, ast.If, ast.While, ast.Return)):
            self.possible_fault_locations.append(node)
        return super().visit(node)

    def inject_faults(self, tree: ast.AST) -> ast.AST:
        # First pass to identify potential fault locations
        self.visit(tree)

        if not self.possible_fault_locations:
            print("No suitable fault injection locations found.")
            return tree

        # Select a subset of locations to inject faults
        random.seed(0) # For deterministic fault injection for a given run
        locations_to_fault = random.sample(self.possible_fault_locations, min(self.target_fault_count, len(self.possible_fault_locations)))
        
        # Second pass to actually inject faults at selected locations
        self.faults_injected = 0
        self._inject_faults_in_tree(tree, locations_to_fault)
        return tree

    def _inject_faults_in_tree(self, tree: ast.AST, locations_to_fault: List[ast.AST]):
        for node in ast.walk(tree):
            if node in locations_to_fault and self.faults_injected < self.target_fault_count:
                if isinstance(node, ast.BinOp):
                    self._mutate_binop(node)
                elif isinstance(node, ast.Compare):
                    self._mutate_compare(node)
                elif isinstance(node, ast.BoolOp):
                    self._mutate_boolop(node)
                elif isinstance(node, ast.If):
                    self._mutate_if_condition(node)
                elif isinstance(node, ast.Return):
                    self._mutate_return_value(node)
                
                self.faults_injected += 1
                if self.faults_injected == self.target_fault_count:
                    break

    def _mutate_binop(self, node: ast.BinOp):
        operators = [ast.Add(), ast.Sub(), ast.Mult(), ast.Div(), ast.Mod()]
        current_op_type = type(node.op)
        
        # Try to change the operator to a different one
        new_op = random.choice([op for op in operators if type(op) != current_op_type])
        if new_op:
            node.op = new_op
            # print(f"Injected fault: Mutated BinOp at line {node.lineno}")

    def _mutate_compare(self, node: ast.Compare):
        comparators = [ast.Eq(), ast.NotEq(), ast.Lt(), ast.LtE(), ast.Gt(), ast.GtE()]
        if node.ops:
            current_comp_type = type(node.ops[0])
            new_comp = random.choice([comp for comp in comparators if type(comp) != current_comp_type])
            if new_comp:
                node.ops[0] = new_comp
                # print(f"Injected fault: Mutated Compare at line {node.lineno}")
    
    def _mutate_boolop(self, node: ast.BoolOp):
        bool_ops = [ast.And(), ast.Or()]
        current_bool_op_type = type(node.op)
        new_bool_op = random.choice([op for op in bool_ops if type(op) != current_bool_op_type])
        if new_bool_op:
            node.op = new_bool_op
            # print(f"Injected fault: Mutated BoolOp at line {node.lineno}")

    def _mutate_if_condition(self, node: ast.If):
        # Invert the condition of an if statement (e.g., `if x:` becomes `if not x:`)
        if isinstance(node.test, ast.UnaryOp) and isinstance(node.test.op, ast.Not):
            node.test = node.test.operand # Remove 'not'
        else:
            node.test = ast.UnaryOp(op=ast.Not(), operand=node.test) # Add 'not'
        # print(f"Injected fault: Mutated If condition at line {node.lineno}")

    def _mutate_return_value(self, node: ast.Return):
        # Change a return value to a constant, e.g., `return x` to `return 0`
        if node.value:
            node.value = ast.Constant(value=0) # Simple mutation to return 0
            # print(f"Injected fault: Mutated Return value at line {node.lineno}")


def inject_simple_fault(code: str, num_faults: int = 1) -> str:
    """
    Injects a specified number of simple faults into Python code.
    Returns the mutated code string.
    """
    try:
        tree = ast.parse(code)
        injector = FaultInjector(target_fault_count=num_faults)
        mutated_tree = injector.inject_faults(tree)
        
        # Ensure that the injector actually injected faults as requested,
        # otherwise, the mutated code might be identical to the original,
        # leading to misleading test results.
        if injector.faults_injected < num_faults and injector.faults_injected > 0:
            print(f"Warning: Only {injector.faults_injected} out of {num_faults} faults injected.")
        elif injector.faults_injected == 0 and num_faults > 0:
            print(f"Warning: No faults could be injected for the given code structure.")


        return ast.unparse(mutated_tree)
    except SyntaxError as e:
        print(f"Syntax error in code during fault injection: {e}")
        return code # Return original code if syntax error
    except Exception as e:
        print(f"An unexpected error occurred during fault injection: {e}")
        return code  # Return original code on other errors
