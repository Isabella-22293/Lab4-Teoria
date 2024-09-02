from graphviz import Digraph

# Definición de clase para nodos del árbol sintáctico
class Nodo:
    def __init__(self, value):
        self.value = value
        self.left = None
        self.right = None

# Definición de clase para estados en el AFN
class Estado:
    def __init__(self, id):
        self.id = id
        self.transiciones = {}  # Diccionario de transiciones: símbolo -> {estados}
        self.epsilon_transiciones = set()  # Transiciones epsilon (ε)

# Clase para representar el AFN
class AFN:
    def __init__(self, start, accept):
        self.start = start
        self.accept = accept
        self.estados = {start, accept}

    def agregar_transicion(self, origen, simbolo, destino):
        origen.transiciones.setdefault(simbolo, set()).add(destino)
        self.estados.add(origen)
        self.estados.add(destino)

    def agregar_transicion_epsilon(self, origen, destino):
        origen.epsilon_transiciones.add(destino)
        self.estados.add(origen)
        self.estados.add(destino)

# Función para convertir infix a postfix utilizando el algoritmo Shunting Yard
def infix_a_postfix(infix):
    precedence = {'|': 1, '.': 2, '*': 3}
    output = []
    stack = []
    
    for char in infix:
        if char.isalnum():
            output.append(char)
        elif char == '(':
            stack.append(char)
        elif char == ')':
            while stack and stack[-1] != '(':
                output.append(stack.pop())
            stack.pop()
        else:  # operador
            while stack and stack[-1] != '(' and precedence[stack[-1]] >= precedence[char]:
                output.append(stack.pop())
            stack.append(char)
    
    while stack:
        output.append(stack.pop())
    
    return ''.join(output)

# Función para convertir de notación postfix a un Árbol Sintáctico Abstracto (AST)
def postfix_a_ast(postfix):
    stack = []
    
    for char in postfix:
        node = Nodo(char)
        if char in {'|', '.'}:  # Operadores binarios
            node.right = stack.pop()
            node.left = stack.pop()
        elif char == '*':  # Operador unario
            node.left = stack.pop()
        stack.append(node)
    
    return stack.pop()

# Construcción del AFN utilizando el algoritmo de Thompson
def construir_afn_thompson(node):
    if node.value == '|':  # Unión
        left_afn = construir_afn_thompson(node.left)
        right_afn = construir_afn_thompson(node.right)
        start = Estado(f"s{len(left_afn.estados) + len(right_afn.estados)}")
        accept = Estado(f"s{len(left_afn.estados) + len(right_afn.estados) + 1}")
        
        afn = AFN(start, accept)
        afn.agregar_transicion_epsilon(start, left_afn.start)
        afn.agregar_transicion_epsilon(start, right_afn.start)
        afn.agregar_transicion_epsilon(left_afn.accept, accept)
        afn.agregar_transicion_epsilon(right_afn.accept, accept)
        
        afn.estados.update(left_afn.estados)
        afn.estados.update(right_afn.estados)
        return afn

    elif node.value == '.':  # Concatenación
        left_afn = construir_afn_thompson(node.left)
        right_afn = construir_afn_thompson(node.right)
        
        afn = AFN(left_afn.start, right_afn.accept)
        afn.agregar_transicion_epsilon(left_afn.accept, right_afn.start)
        
        afn.estados.update(left_afn.estados)
        afn.estados.update(right_afn.estados)
        return afn

    elif node.value == '*':  # Cierre de Kleene
        sub_afn = construir_afn_thompson(node.left)
        start = Estado(f"s{len(sub_afn.estados)}")
        accept = Estado(f"s{len(sub_afn.estados) + 1}")
        
        afn = AFN(start, accept)
        afn.agregar_transicion_epsilon(start, sub_afn.start)
        afn.agregar_transicion_epsilon(sub_afn.accept, accept)
        afn.agregar_transicion_epsilon(start, accept)
        afn.agregar_transicion_epsilon(sub_afn.accept, sub_afn.start)
        
        afn.estados.update(sub_afn.estados)
        return afn

    else:  # Nodo hoja, carácter individual
        start = Estado(f"s{node.value}_start")
        accept = Estado(f"s{node.value}_accept")
        afn = AFN(start, accept)
        afn.agregar_transicion(start, node.value, accept)
        return afn

# Dibuja el AFN utilizando graphviz
def draw_afn(afn, filename='afn'):
    dot = Digraph()
    
    for estado in afn.estados:
        dot.node(estado.id, shape='doublecircle' if estado == afn.accept else 'circle')
        for simbolo, destinos in estado.transiciones.items():
            for destino in destinos:
                dot.edge(estado.id, destino.id, label=simbolo)
        for destino in estado.epsilon_transiciones:
            dot.edge(estado.id, destino.id, label='ε')
    
    dot.render(filename, format='png', cleanup=True)
    print(f"AFN generado y guardado en {filename}.png")

# Cálculo del cierre epsilon para un conjunto de estados
def epsilon_closure(states):
    stack = list(states)
    closure = set(states)

    while stack:
        state = stack.pop()
        for next_state in state.epsilon_transiciones:
            if next_state not in closure:
                closure.add(next_state)
                stack.append(next_state)

    return closure

# Simula el AFN para verificar si una cadena es aceptada
def simular_afn(afn, cadena):
    estados_actuales = epsilon_closure({afn.start})
    for simbolo in cadena:
        nuevos_estados = set()
        for estado in estados_actuales:
            if simbolo in estado.transiciones:
                for destino in estado.transiciones[simbolo]:
                    nuevos_estados.update(epsilon_closure({destino}))
        estados_actuales = nuevos_estados
    
    for estado in estados_actuales:
        if estado == afn.accept:
            return "sí"
    return "no"

# Procesamiento principal
def process_file(filename):
    with open(filename, 'r') as file:
        for line in file:
            regex = line.strip()
            if regex:
                print(f"Expresión Original: {regex}")
                postfix = infix_a_postfix(regex)
                print(f"Expresión Postfix: {postfix}")

                try:
                    ast = postfix_a_ast(postfix)
                    afn = construir_afn_thompson(ast)
                    draw_afn(afn)
                    
                    cadena = input("Ingrese la cadena a evaluar: ")
                    resultado = simular_afn(afn, cadena)
                    print(f"Resultado de la simulación: {resultado}")

                except ValueError as e:
                    print(f"Error al construir el árbol: {e}")

if __name__ == "__main__":
    process_file('input.txt')
