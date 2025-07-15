# Librerías necesarias para el analizador y la interfaz
import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext
import ply.lex as lex
import ply.yacc as yacc
from graphviz import Digraph

# Guarda el texto fuente actual
texto_actual = ""

# Nodo principal del programa
class Programa:
    def __init__(self, sentencias):
        self.sentencias = sentencias

    def __repr__(self):
        return "Programa([\n    " + ",\n    ".join(repr(s) for s in self.sentencias) + "\n])"

# Representa una declaración (int x;)
class Declaracion:
    def __init__(self, tipo, nombre):
        self.tipo = tipo
        self.nombre = nombre

    def __repr__(self):
        return f"Declaracion('{self.tipo}', '{self.nombre}')"

# Representa una asignación (x = 5;)
class Asignacion:
    def __init__(self, nombre, valor):
        self.nombre = nombre
        self.valor = valor

    def __repr__(self):
        return f"Asignacion('{self.nombre}', {repr(self.valor)})"

# Representa un print
class Impresion:
    def __init__(self, valor):
        self.valor = valor

    def __repr__(self):
        return f"Impresion({repr(self.valor)})"

# Operaciones como +, -, *, /
class BinOp:
    def __init__(self, op, izq, der):
        self.op = op
        self.izq = izq
        self.der = der

    def __repr__(self):
        return f"BinOp('{self.op}', {repr(self.izq)}, {repr(self.der)})"

# Número entero
class Numero:
    def __init__(self, valor):
        self.valor = valor

    def __repr__(self):
        return f"Numero({self.valor})"

# Variable
class Identificador:
    def __init__(self, nombre):
        self.nombre = nombre

    def __repr__(self):
        return f"Identificador('{self.nombre}')"

# Cadena de texto
class Cadena:
    def __init__(self, valor):
        self.valor = valor

    def __repr__(self):
        return f"Cadena({repr(self.valor)})"

# Palabras reservadas
palabras_reservadas = {
    "int": "INT",
    "print": "PRINT"
}

# Tokens del lenguaje
tokens = list(palabras_reservadas.values()) + [
    'ID', 'NUM', 'STRING', 'EQUAL', 'SEMI',
    'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'LPAREN', 'RPAREN'
]

# Reglas para cada token
t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_DIVIDE = r'/'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_EQUAL = r'='
t_SEMI = r';'

# Comentarios de línea
def t_COMMENT(t):
    r'//.*'
    pass

# Cadenas entre comillas
def t_STRING(t):
    r'"[^"\n]*"'
    t.value = t.value[1:-1]
    return t

# Números enteros
def t_NUM(t):
    r'\d+'
    t.value = int(t.value)
    return t

# Identificadores y palabras reservadas
def t_ID(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = palabras_reservadas.get(t.value, 'ID')
    return t

# Ignorar espacios y tabs
t_ignore = ' \t'

# Contar saltos de línea
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# Manejo de errores léxicos
def t_error(t):
    print(f"Carácter ilegal '{t.value[0]}' en línea {t.lineno}")
    t.lexer.skip(1)

# Devuelve la columna del token
def encontrar_columna(input_texto, token):
    last_cr = input_texto.rfind('\n', 0, token.lexpos)
    if last_cr < 0:
        last_cr = -1
    return token.lexpos - last_cr

# Programa compuesto por sentencias
def p_programa(p):
    '''programa : sentencias'''
    p[0] = Programa(p[1])

# Lista de sentencias
def p_sentencias(p):
    '''sentencias : sentencia sentencias
                  | sentencia'''
    if len(p) == 3:
        p[0] = [p[1]] + p[2]
    else:
        p[0] = [p[1]]

# Declaraciones con o sin asignación
def p_sentencia_declaracion(p):
    '''sentencia : INT ID SEMI
                 | INT ID EQUAL expresion SEMI'''
    if len(p) == 4:
        p[0] = Declaracion('int', p[2])
    else:
        p[0] = Asignacion(p[2], p[4])
    
    # Agregar a tabla de símbolos si no existe
    if not any(s["nombre"] == p[2] for s in tabla_simbolos):
        tabla_simbolos.append({"nombre": p[2], "tipo": "int", "linea": p.lineno(2)})

# Asignación
def p_sentencia_asignacion(p):
    'sentencia : ID EQUAL expresion SEMI'
    verificar_declaracion(p[1], p.lineno(1))
    p[0] = Asignacion(p[1], p[3])

# Print de valor o cadena
def p_sentencia_print(p):
    '''sentencia : PRINT expresion SEMI
                 | PRINT STRING SEMI
                 | PRINT LPAREN expresion RPAREN SEMI
                 | PRINT LPAREN STRING RPAREN SEMI'''
    if len(p) == 4:
        if isinstance(p[2], str):
            p[0] = Impresion(Cadena(p[2]))
        else:
            p[0] = Impresion(p[2])
    else:
        if isinstance(p[3], str):
            p[0] = Impresion(Cadena(p[3]))
        else:
            p[0] = Impresion(p[3])

# Operaciones aritméticas
def p_expresion_binaria(p):
    '''expresion : expresion PLUS expresion
                 | expresion MINUS expresion
                 | expresion TIMES expresion
                 | expresion DIVIDE expresion'''
    p[0] = BinOp(p[2], p[1], p[3])

# Paréntesis
def p_expresion_parentesis(p):
    'expresion : LPAREN expresion RPAREN'
    p[0] = p[2]

# Números y variables
def p_expresion_numero(p):
    'expresion : NUM'
    p[0] = Numero(p[1])

def p_expresion_id(p):
    'expresion : ID'
    verificar_declaracion(p[1], p.lineno(1))
    p[0] = Identificador(p[1])

# Manejo de errores de sintaxis
def p_error(p):
    global texto_actual
    if p:
        error_msg = f"Error de sintaxis en línea {p.lineno}, columna {encontrar_columna(texto_actual, p)}:\n"
        error_msg += f"Token inesperado: '{p.value}' (tipo: {p.type})\n"
        error_msg += "Se esperaba: declaración (ej: 'int x;') o asignación (ej: 'x = 5;')"
    else:
        error_msg = "Error: Fin inesperado del código. ¿Falta un punto y coma?"
    
    mostrar_parser.delete('1.0', tk.END)
    mostrar_parser.insert(tk.END, error_msg)


# === FUNCIONES AUXILIARES ===
# Verifica que una variable haya sido declarada
def verificar_declaracion(nombre, lineno):
    if not any(sim["nombre"] == nombre for sim in tabla_simbolos):
        raise Exception(f"Error Semántico: variable '{nombre}' no declarada (línea {lineno})")

# === INTERFAZ GRÁFICA ===
ventana = tk.Tk()
ventana.title("Analizador ScoobyLang")
ventana.geometry("1200x800")

# Variables globales
lexer = lex.lex()
parser = yacc.yacc()
tabla_simbolos = []
resultado_tokens = []
ast_resultado = []

# Clase que ejecuta el codigo interpretando el AST
class Interprete:
    def __init__(self):
        self.variables = {}
        self.salida = []
    
    def limpiar(self):
        self.variables.clear()
        self.salida.clear()
    
    def evaluar(self, nodo):
        if isinstance(nodo, Programa):
            for sentencia in nodo.sentencias:
                self.evaluar(sentencia)
        elif isinstance(nodo, Declaracion):
            self.variables[nodo.nombre] = 0
        elif isinstance(nodo, Asignacion):
            valor = self.evaluar(nodo.valor)
            self.variables[nodo.nombre] = valor
        elif isinstance(nodo, Impresion):
            valor = self.evaluar(nodo.valor)
            self.salida.append(str(valor))
        elif isinstance(nodo, BinOp):
            izq = self.evaluar(nodo.izq)
            der = self.evaluar(nodo.der)
            if nodo.op == '+': return izq + der
            elif nodo.op == '-': return izq - der
            elif nodo.op == '*': return izq * der
            elif nodo.op == '/': return izq // der
        elif isinstance(nodo, Numero):
            return nodo.valor
        elif isinstance(nodo, Identificador):
            if nodo.nombre in self.variables:
                return self.variables[nodo.nombre]
            raise ValueError(f"Variable '{nodo.nombre}' no definida")
        elif isinstance(nodo, Cadena):
            return nodo.valor
        return None

interprete = Interprete()

# Componentes de la interfaz
frame_botones = tk.Frame(ventana)
frame_botones.pack(pady=5)

frame_contenido = tk.Frame(ventana)
frame_contenido.pack(fill="both", expand=True, padx=10, pady=10)

# Código fuente
tk.Label(frame_contenido, text="Código fuente", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky="w")
mostrar_archivo = scrolledtext.ScrolledText(frame_contenido, width=40, height=20)
mostrar_archivo.grid(row=1, column=0, padx=5, sticky="n")

# AST
tk.Label(frame_contenido, text="Parser", font=("Arial", 12, "bold")).grid(row=2, column=0, sticky="w")
mostrar_parser = scrolledtext.ScrolledText(frame_contenido, width=40, height=8)
mostrar_parser.grid(row=3, column=0, padx=5, sticky="w")

# Tokens
tk.Label(frame_contenido, text="Tokens", font=("Arial", 12, "bold")).grid(row=0, column=1, sticky="w")
frame_tabla = tk.Frame(frame_contenido)
frame_tabla.grid(row=1, column=1, sticky="n")
scroll_y = tk.Scrollbar(frame_tabla, orient="vertical")
scroll_x = tk.Scrollbar(frame_tabla, orient="horizontal")
mostrar_tabla = ttk.Treeview(frame_tabla, show="headings", height=10, yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
scroll_y.config(command=mostrar_tabla.yview)
scroll_y.pack(side="right", fill="y")
scroll_x.config(command=mostrar_tabla.xview)
scroll_x.pack(side="bottom", fill="x")
mostrar_tabla.pack(fill="both", expand=True)
mostrar_tabla["columns"] = ("Token", "Tipo", "Línea")
for col in mostrar_tabla["columns"]:
    mostrar_tabla.heading(col, text=col)
    mostrar_tabla.column(col, width=100, anchor="center")

# Tabla de símbolos
tk.Label(frame_contenido, text="Tabla de Símbolos", font=("Arial", 12, "bold")).grid(row=2, column=1, sticky="w")
frame_simbolos = tk.Frame(frame_contenido)
frame_simbolos.grid(row=3, column=1, sticky="n")
scroll_y2 = tk.Scrollbar(frame_simbolos, orient="vertical")
scroll_x2 = tk.Scrollbar(frame_simbolos, orient="horizontal")
simbolos_tabla = ttk.Treeview(frame_simbolos, show="headings", height=8, yscrollcommand=scroll_y2.set, xscrollcommand=scroll_x2.set)
scroll_y2.config(command=simbolos_tabla.yview)
scroll_y2.pack(side="right", fill="y")
scroll_x2.config(command=simbolos_tabla.xview)
scroll_x2.pack(side="bottom", fill="x")
simbolos_tabla.pack(fill="both", expand=True)
simbolos_tabla["columns"] = ("Identificador", "Tipo", "Línea")
for col in simbolos_tabla["columns"]:
    simbolos_tabla.heading(col, text=col)
    simbolos_tabla.column(col, width=100, anchor="center")

# Resultados
tk.Label(frame_contenido, text="Resultados", font=("Arial", 12, "bold")).grid(row=0, column=2, sticky="w")
mostrar_resultados = scrolledtext.ScrolledText(frame_contenido, width=40, height=20)
mostrar_resultados.grid(row=1, column=2, padx=5, sticky="n")

# Variables
tk.Label(frame_contenido, text="Variables", font=("Arial", 12, "bold")).grid(row=2, column=2, sticky="w")
frame_variables = tk.Frame(frame_contenido)
frame_variables.grid(row=3, column=2, sticky="n")
scroll_y3 = tk.Scrollbar(frame_variables, orient="vertical")
scroll_x3 = tk.Scrollbar(frame_variables, orient="horizontal")
variables_tabla = ttk.Treeview(frame_variables, show="headings", height=8, yscrollcommand=scroll_y3.set, xscrollcommand=scroll_x3.set)
scroll_y3.config(command=variables_tabla.yview)
scroll_y3.pack(side="right", fill="y")
scroll_x3.config(command=variables_tabla.xview)
scroll_x3.pack(side="bottom", fill="x")
variables_tabla.pack(fill="both", expand=True)
variables_tabla["columns"] = ("Variable", "Valor")
for col in variables_tabla["columns"]:
    variables_tabla.heading(col, text=col)
    variables_tabla.column(col, width=100, anchor="center")

# Funciones de la interfaz

# Muestra los tokens en la tabla
def mostrar_tokens():
    mostrar_tabla.delete(*mostrar_tabla.get_children())
    for token in resultado_tokens:
        mostrar_tabla.insert("", tk.END, values=(token["token"], token["tipo"], token["linea"]))

# Muestra la tabla de simbolos
def mostrar_tabla_simbolos():
    simbolos_tabla.delete(*simbolos_tabla.get_children())
    for simbolo in tabla_simbolos:
        simbolos_tabla.insert("", tk.END, values=(simbolo["nombre"], simbolo["tipo"], simbolo["linea"]))

# Muestra las variables despues de ejecutar
def mostrar_variables():
    variables_tabla.delete(*variables_tabla.get_children())
    for var, val in interprete.variables.items():
        variables_tabla.insert("", tk.END, values=(var, val))

# Limpia todos los campos de la interfaz
def limpiar():
    mostrar_archivo.delete("1.0", tk.END)
    mostrar_parser.delete("1.0", tk.END)
    mostrar_resultados.delete("1.0", tk.END)
    mostrar_tabla.delete(*mostrar_tabla.get_children())
    simbolos_tabla.delete(*simbolos_tabla.get_children())
    variables_tabla.delete(*variables_tabla.get_children())
    resultado_tokens.clear()
    tabla_simbolos.clear()
    ast_resultado.clear()
    interprete.limpiar()

# Permite seleccionar un archivo y cargar su contenido
def seleccionar_archivo():
    filetypes = [('Archivos de texto', '*.txt'), ('Todos los archivos', '*.*')]
    archivo = filedialog.askopenfilename(filetypes=filetypes)
    if archivo:
        try:
            with open(archivo, 'r', encoding='utf-8') as f:
                contenido = f.read()
                mostrar_archivo.delete("1.0", tk.END)
                mostrar_archivo.insert(tk.END, contenido)
            messagebox.showinfo("Éxito", "Archivo cargado correctamente")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el archivo:\n{str(e)}")

# Analisis lexico
def analizar_texto_pegado():
    global texto_actual
    resultado_tokens.clear()
    tabla_simbolos.clear()
    mostrar_tabla.delete(*mostrar_tabla.get_children())
    simbolos_tabla.delete(*simbolos_tabla.get_children())
    mostrar_parser.delete("1.0", tk.END)
    
    texto = mostrar_archivo.get("1.0", tk.END)
    texto_actual = texto
    if not texto.strip():
        messagebox.showwarning("Advertencia", "No hay código para analizar")
        return
    
    # Crear lexer nuevo para análisis limpio
    lexer_local = lex.lex()
    lexer_local.input(texto)
    
    try:
        while True:
            tok = lexer_local.token()
            if not tok:
                break
            resultado_tokens.append({
                "token": tok.value,
                "tipo": tok.type,
                "linea": tok.lineno
            })
        mostrar_tokens()

        # Resetear tabla de símbolos antes de analizar
        tabla_simbolos.clear()
        parser.parse(texto, lexer=lex.lex())
        mostrar_tabla_simbolos()

    except Exception as e:
        messagebox.showerror("Error Léxico", f"Ocurrió un error durante el análisis:\n{str(e)}")

def analizar_parser():
    global texto_actual
    mostrar_parser.delete("1.0", tk.END)
    resultado_tokens.clear()
    tabla_simbolos.clear()
    ast_resultado.clear()

    codigo = mostrar_archivo.get("1.0", tk.END)
    texto_actual = codigo
    if not codigo.strip():
        messagebox.showwarning("Advertencia", "No hay código para analizar")
        return
    
    try:
        # Crear lexer nuevo para análisis
        lexer_local = lex.lex()
        lexer_local.input(codigo)
        
        while True:
            tok = lexer_local.token()
            if not tok:
                break
            resultado_tokens.append({
                "token": tok.value,
                "tipo": tok.type,
                "linea": tok.lineno
            })
        
        mostrar_tokens()
        
        # Es mejor crear un nuevo lexer para el parser (no compartir lexer)
        ast = parser.parse(codigo, lexer=lex.lex())
        if ast:
            ast_resultado.append(ast)
            mostrar_parser.insert(tk.END, "Analisis Sintáctico Exitoso\n")
            mostrar_parser.insert(tk.END, repr(ast) + "\n")
        else:
            mostrar_parser.insert(tk.END, "No se generó AST (codigo vacío o solo comentarios)\n")
        
        mostrar_tabla_simbolos()

    except Exception as e:
        mostrar_parser.insert(tk.END, f"Error: {str(e)}\n")


def ejecutar_codigo():
    mostrar_resultados.delete("1.0", tk.END)
    interprete.limpiar()
    
    if not ast_resultado:
        mostrar_resultados.insert(tk.END, "Error: Primero ejecuta 'Analizar Parser'\n")
        return
    
    try:
        interprete.evaluar(ast_resultado[0])
        if interprete.salida:
            mostrar_resultados.insert(tk.END, "=== SALIDA ===\n")
            for linea in interprete.salida:
                mostrar_resultados.insert(tk.END, f"{linea}\n")
        else:
            mostrar_resultados.insert(tk.END, "Ejecucion exitosa (sin salida)\n")
        
        mostrar_variables()
    except Exception as e:
        mostrar_resultados.insert(tk.END, f"Error en ejecucion: {str(e)}\n")

def generar_arbol():
    if not ast_resultado:
        messagebox.showwarning("Advertencia", "Primero ejecuta 'Analizar Parser' para generar el AST")
        return
    
    try:
        dot = Digraph(comment='AST')
        
        # Construir el árbol
        def agregar_nodo(nodo, padre=None):
            nodo_id = str(id(nodo))
            if isinstance(nodo, Programa):
                dot.node(nodo_id, 'Programa', shape='ellipse')
                for sentencia in nodo.sentencias:
                    agregar_nodo(sentencia, nodo_id)
            elif isinstance(nodo, Declaracion):
                dot.node(nodo_id, f'Declaración\n{nodo.tipo} {nodo.nombre}', shape='box')
            elif isinstance(nodo, Asignacion):
                dot.node(nodo_id, f'Asignación\n{nodo.nombre} =', shape='box')
                agregar_nodo(nodo.valor, nodo_id)
            elif isinstance(nodo, Impresion):
                dot.node(nodo_id, 'Print', shape='box')
                agregar_nodo(nodo.valor, nodo_id)
            elif isinstance(nodo, BinOp):
                dot.node(nodo_id, f'Operación\n{nodo.op}', shape='diamond')
                agregar_nodo(nodo.izq, nodo_id)
                agregar_nodo(nodo.der, nodo_id)
            elif isinstance(nodo, (Numero, Identificador, Cadena)):
                dot.node(nodo_id, str(nodo), shape='oval')
            
            if padre:
                dot.edge(padre, nodo_id)
        
        agregar_nodo(ast_resultado[0])
        
        dot.render('arbol_ast', view=True, format='png')
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo generar el árbol: {str(e)}")

# Botones
tk.Button(frame_botones, text="Cargar Archivo", command=seleccionar_archivo).grid(row=0, column=0, padx=5)
tk.Button(frame_botones, text="Analizar Lexico", command=analizar_texto_pegado).grid(row=0, column=1, padx=5)
tk.Button(frame_botones, text="Analizar Parser", command=analizar_parser).grid(row=0, column=2, padx=5)
tk.Button(frame_botones, text="Ejecutar", command=ejecutar_codigo).grid(row=0, column=3, padx=5)
tk.Button(frame_botones, text="Generar Arbol", command=generar_arbol).grid(row=0, column=4, padx=5)
tk.Button(frame_botones, text="Limpiar", command=limpiar).grid(row=0, column=6, padx=5)
tk.Button(frame_botones, text="Salir", command=ventana.quit).grid(row=0, column=7, padx=5)

ventana.mainloop()