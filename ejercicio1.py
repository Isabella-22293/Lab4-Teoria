from graphviz import Digraph
import networkx as nx
import matplotlib.pyplot as plt

def get_precedence(op):
    precedences = {
        '(': 1,
        '|': 2,
        '.': 3,
        '?': 4,
        '*': 4,
        '+': 4,
    }
    return precedences.get(op, 0)

def format_reg_ex(regex):
    formatted = []
    escaped = False

    i = 0
    while i < len(regex):
        c1 = regex[i]

        if escaped:
            formatted.append('\\' + c1)
            escaped = False
        elif c1 == '\\':
            escaped = True
        else:
            if c1 == '+' or c1 == '?':
                if len(formatted) > 0:
                    formatted.append(c1)
            elif c1 == '*':
                if len(formatted) > 0 and formatted[-1] != '|':
                    formatted.append(c1)
            else:
                if i + 1 < len(regex):
                    c2 = regex[i + 1]
                    formatted.append(c1)
                    if c1 not in ('(', '|') and c2 not in (')', '|', '?', '*', '+', '('):
                        formatted.append('.')
                else:
                    formatted.append(c1)

        i += 1

    return ''.join(formatted)

def infix_a_postfix(regex):
    postfix = []
    stack = []
    regex_formateado = format_reg_ex(regex)

    print(f"Expresión Formateada: {regex_formateado}")

    for c in regex_formateado:
        if c == '(':
            stack.append(c)
        elif c == ')':
            while stack and stack[-1] != '(':
                postfix.append(stack.pop())
            if stack:
                stack.pop()
        elif c not in ('|', '?', '+', '*', '.'):
            postfix.append(c)
        else:
            while stack and get_precedence(stack[-1]) >= get_precedence(c):
                postfix.append(stack.pop())
            stack.append(c)

    while stack:
        postfix.append(stack.pop())

    return ''.join(postfix)

class Node:
    def __init__(self, value):
        self.value = value
        self.left = None
        self.right = None

def postfix_a_ast(postfix):
    stack = []
    for char in postfix:
        if char in ('|', '.', '*', '+', '?'):
            if char in ('|', '.'):
                if len(stack) < 2:
                    raise ValueError(f"Error en la expresión postfix: falta operandos para el operador '{char}'")
                node = Node(char)
                node.right = stack.pop()
                node.left = stack.pop()
            elif char in ('*', '+', '?'):
                if len(stack) < 1:
                    raise ValueError(f"Error en la expresión postfix: falta operando para el operador '{char}'")
                node = Node(char)
                node.left = stack.pop()
            stack.append(node)
        else:
            stack.append(Node(char))

    if len(stack) != 1:
        raise ValueError(f"Error en la conversión postfix: la expresión no es válida. Stack final: {stack}")

    return stack.pop()


def add_edges(dot, node):
    if node:
        node_id = str(id(node))
        dot.node(node_id, node.value)
        if node.left:
            left_id = str(id(node.left))
            dot.edge(node_id, left_id)
            add_edges(dot, node.left)
        if node.right:
            right_id = str(id(node.right))
            dot.edge(node_id, right_id)
            add_edges(dot, node.right)

def draw_ast(root, index):
    dot = Digraph()
    add_edges(dot, root)
    filename = f'ast{index}.png'
    dot.render(filename, format='png', cleanup=True)
    print(f"Árbol sintáctico guardado en {filename}")

class AFN:
    def __init__(self):
        self.states = []
        self.transitions = {}
        self.initial_state = None
        self.accepting_states = set()

    def add_state(self):
        state = len(self.states)
        self.states.append(state)
        self.transitions[state] = []
        return state

    def add_transition(self, from_state, to_state, symbol):
        self.transitions[from_state].append((symbol, to_state))

    def set_initial_state(self, state):
        self.initial_state = state

    def add_accepting_state(self, state):
        self.accepting_states.add(state)

def thompson_construction(ast_node):
    afn = AFN()

    print(f"Procesando nodo: {ast_node.value}")

    if ast_node.value == '|':
        left_afn = thompson_construction(ast_node.left)
        right_afn = thompson_construction(ast_node.right)

        start_state = afn.add_state()
        end_state = afn.add_state()

        afn.set_initial_state(start_state)
        afn.add_transition(start_state, left_afn.initial_state, 'ε')
        afn.add_transition(start_state, right_afn.initial_state, 'ε')

        afn.transitions.update(left_afn.transitions)
        afn.transitions.update(right_afn.transitions)

        if left_afn.accepting_states:
            for state in left_afn.accepting_states:
                afn.add_transition(state, end_state, 'ε')
        if right_afn.accepting_states:
            for state in right_afn.accepting_states:
                afn.add_transition(state, end_state, 'ε')

        afn.add_accepting_state(end_state)

    elif ast_node.value == '.':
        left_afn = thompson_construction(ast_node.left)
        right_afn = thompson_construction(ast_node.right)

        afn.set_initial_state(left_afn.initial_state)
        afn.transitions.update(left_afn.transitions)
        afn.transitions.update(right_afn.transitions)

        if left_afn.accepting_states:
            for state in left_afn.accepting_states:
                afn.add_transition(state, right_afn.initial_state, 'ε')
        afn.add_accepting_state(right_afn.accepting_states.pop())

    elif ast_node.value == '*':
        inner_afn = thompson_construction(ast_node.left)

        start_state = afn.add_state()
        end_state = afn.add_state()

        afn.set_initial_state(start_state)
        afn.add_transition(start_state, inner_afn.initial_state, 'ε')
        afn.add_transition(start_state, end_state, 'ε')
        afn.transitions.update(inner_afn.transitions)

        if inner_afn.accepting_states:
            for state in inner_afn.accepting_states:
                afn.add_transition(state, inner_afn.initial_state, 'ε')
                afn.add_transition(state, end_state, 'ε')

        afn.add_accepting_state(end_state)

    elif ast_node.value == '+':
        inner_afn = thompson_construction(ast_node.left)

        start_state = afn.add_state()
        end_state = afn.add_state()

        afn.set_initial_state(start_state)
        afn.add_transition(start_state, inner_afn.initial_state, 'ε')
        afn.transitions.update(inner_afn.transitions)

        if inner_afn.accepting_states:
            for state in inner_afn.accepting_states:
                afn.add_transition(state, inner_afn.initial_state, 'ε')
                afn.add_transition(state, end_state, 'ε')

        afn.add_accepting_state(end_state)

    elif ast_node.value == '?':
        inner_afn = thompson_construction(ast_node.left)

        start_state = afn.add_state()
        end_state = afn.add_state()

        afn.set_initial_state(start_state)
        afn.add_transition(start_state, inner_afn.initial_state, 'ε')
        afn.add_transition(start_state, end_state, 'ε')
        afn.transitions.update(inner_afn.transitions)

        if inner_afn.accepting_states:
            for state in inner_afn.accepting_states:
                afn.add_transition(state, end_state, 'ε')

        afn.add_accepting_state(end_state)

    else:
        start_state = afn.add_state()
        end_state = afn.add_state()

        afn.set_initial_state(start_state)
        afn.add_transition(start_state, end_state, ast_node.value)
        afn.add_accepting_state(end_state)

    print(f"Estados de aceptación después de construir AFN: {afn.accepting_states}")

    return afn

def simulate_afn(afn, string):
    current_states = {afn.initial_state}

    for char in string:
        next_states = set()
        for state in current_states:
            for symbol, next_state in afn.transitions.get(state, []):
                if symbol == char or symbol == 'ε':
                    next_states.add(next_state)
        current_states = next_states

    if current_states & afn.accepting_states:
        return "sí"
    else:
        return "no"
def draw_afn_networkx(afn, index):
    G = nx.DiGraph()

    for state in afn.states:
        shape = 'doublecircle' if state in afn.accepting_states else 'circle'
        G.add_node(state, shape=shape)

    for from_state, transitions in afn.transitions.items():
        for symbol, to_state in transitions:
            G.add_edge(from_state, to_state, label=symbol)

    pos = nx.spring_layout(G)
    labels = nx.get_edge_attributes(G, 'label')

    plt.figure(figsize=(8, 6))
    nx.draw(G, pos, with_labels=True, node_size=500, node_color='lightblue', font_size=10, font_weight='bold')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=labels)
    
    filename = f'grafo{index}.png'
    plt.savefig(filename)
    plt.show()
    print(f"AFN guardado en {filename}")

def procesar_expresion_regular(exp, index):
    postfix = infix_a_postfix(exp)
    print(f"Postfix: {postfix}")

    ast = postfix_a_ast(postfix)
    draw_ast(ast, index)

    afn = thompson_construction(ast)
    draw_afn_networkx(afn, index)

    return afn

expresion = "(a*|b*)+"
afn = procesar_expresion_regular(expresion, 1)
expresion = "((ε|a)|b ∗) ∗"
afn = procesar_expresion_regular(expresion, 2)
expresion = "(a|b) ∗ abb(a|b) ∗"
afn = procesar_expresion_regular(expresion, 3)
expresion = "0? (1? )? 0 ∗"
afn = procesar_expresion_regular(expresion, 4)

cadena = "aabb"
resultado = simulate_afn(afn, cadena)
print(f"La cadena '{cadena}' es aceptada: {resultado}")


