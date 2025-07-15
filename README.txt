ScoobyLang - Analizador Léxico - Sintáctico


ScoobyLang es un lenguaje diseñado para la declaración y uso de variables enteras, 
evaluación de expresiones aritméticas y la entrada/salida de datos simples mediante instrucciones.


Características

- Análisis léxico utilizando PLY (Python Lex-Yacc
- Análisis sintáctico con construcción del AST
- Evaluación de expresiones y ejecución de sentencias
- Visualización del AST con Graphviz
- Interfaz gráfica con Tkinter
- Manejo de errores léxicos, sintácticos y semánticos
- Tabla de símbolos y de variables en tiempo de ejecución
- Soporte para expresiones aritméticas, declaraciones, asignaciones y print


Tecnologías y herramientas utilizadas

| Componente        | Herramienta              |
|----------------   |------------------------- |
| Lenguaje          | Python 3.9+              |
| Lexer/Parser      | PLY (Lex/Yacc en Python) |
| GUI               | Tkinter                  |
| Visualización AST | Graphviz                 |


Estructura del proyecto

ScoobyLang-Analizador/
├──analizador.py # Archivo principal con lexer, parser, GUI e intérprete
├── tests/
│ ├── Validos-Sintactico # Codigo válido
│ └── Invalidos-Sintactico # Codigo con errores léxicos/sintácticos
├── README.md # Documentacion del proyecto
├── requirements.txt # Dependencias Python
