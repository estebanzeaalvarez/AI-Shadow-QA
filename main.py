import os, json, re, subprocess
from typing import List
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live

load_dotenv()
console = Console()

# --- MODELOS DE DATOS PARA ANÁLISIS ---
class CodeFunction(BaseModel):
    name: str = Field(description="Nombre de la función")
    potential_risks: List[str] = Field(description="Riesgos detectados (ej: división por cero, null pointer)")

class CodeAnalysis(BaseModel):
    summary: str = Field(description="Resumen de lo que hace el código")
    functions: List[CodeFunction]

# --- UTILIDADES ---
def clean_ai_code(text: str) -> str:
    """Extracción limpia de código Python."""
    match = re.search(r"```python\s*(.*?)\s*```", text, re.DOTALL)
    if match: return match.group(1).strip()
    # Si no hay bloques, filtramos líneas que no parezcan código
    lines = text.replace("```python", "").replace("```", "").splitlines()
    keywords = ('import', 'from', 'def', 'class', 'return', 'if', 'else', 'elif', 'try', 'except', 'with', 'print', 'assert', 'raise')
    return "\n".join([l for l in lines if l.startswith(keywords) or l.startswith(('    ', '\t')) or not l.strip()]).strip()

# --- CEREBROS DE LA IA ---
class ShadowQA:
    def __init__(self):
        self.llm_json = ChatOllama(model="llama3", temperature=0)
        self.llm_code = ChatOllama(model="llama3", temperature=0)

    def analyze(self, code: str):
        # Usamos doble llave {{ }} para que LangChain no crea que son variables
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Eres un Senior QA. Analiza el código y detecta fallos lógicos. Responde SOLO con un JSON que tenga esta estructura: {{'summary': '...', 'functions': [{{'name': '...', 'potential_risks': []}}]}}"),
            ("user", "Analiza este código:\n{source_code}")
        ])
        # Pasamos la variable explícitamente en el invoke
        res = (prompt | self.llm_json).invoke({"source_code": code})
        try:
            clean_json = re.search(r"\{.*\}", res.content, re.DOTALL).group()
            return json.loads(clean_json.replace("'", '"')) # Aseguramos comillas dobles para JSON
        except:
            return {"summary": "Error analizando", "functions": []}

    def generate_tests(self, code: str, analysis: str) -> str:
        # Usamos doble llave {{ }} para que LangChain ignore los ejemplos de texto
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Eres un QA de Élite. Tu objetivo es DESTRUIR el código con casos de borde. 
            Escribe tests que FALLEN si el código no maneja errores de forma elegante.
            REGLAS:
            1. Si una lista puede estar vacía, el test debe esperar un mensaje controlado o una excepción específica, NO un IndexError genérico.
            2. Si un número puede ser negativo, el test debe esperar una validación.
            3. No uses 'try/except' en los tests para ocultar errores. Usa 'pytest.raises' si esperas un error.
            4. Usa 'from example_code import *'. Solo código Python."""),
            ("user", "Código a testear:\n{source_code}\n\nAnálisis de riesgos:\n{analysis_result}")
        ])
        res = (prompt | self.llm_code).invoke({
            "source_code": code, 
            "analysis_result": analysis
        })
        return clean_ai_code(res.content)

    def heal(self, code: str, errors: str) -> str:
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Eres un Senior Developer paranoico y obsesivo. Tu misión es arreglar el código para que sea INDESTRUCTIBLE y pase todos los tests.
            REGLAS DE ORO:
            1. ANALIZA EL ERROR: Lee cuidadosamente el log de Pytest y soluciona la causa raíz (si falta un import, si un tipo de dato falla, o si falta una validación).
            2. VALIDACIÓN TOTAL: No te limites a las listas. Valida que cada elemento de una lista sea del tipo esperado si el error lo sugiere.
            3. CONSISTENCIA: Si el test espera que el código maneje errores sin explotar (ej: devolviendo un mensaje o None), asegúrate de que el código haga eso.
            4. DEVUELVE EL ARCHIVO COMPLETO: Solo código Python, sin explicaciones, manteniendo la estructura original pero reforzada.
            5. PROHIBIDO incluir tests dentro del código."""),
            ("user", "Código actual con fallos:\n{source_code}\n\nErrores reportados por Pytest:\n{error_log}")
        ])
        res = (prompt | self.llm_code).invoke({
            "source_code": code, 
            "error_log": errors
        })
        return clean_ai_code(res.content)

def run_shadow_qa():
    qa = ShadowQA()
    FILE = "example_code.py"
    analysis = {"summary": "No se realizó análisis", "functions": []} # Inicialización limpia
    
    console.print(Panel.fit("[bold cyan]🛡️ SHADOW-QA v2.1: REFORZADO[/bold cyan]", border_style="cyan"))

    for i in range(1, 6):
        console.print(f"\n[bold yellow]🔍 CICLO {i}: ANALIZANDO SEGURIDAD...[/bold yellow]")
        if not os.path.exists(FILE): break
        with open(FILE, "r") as f: source = f.read()

        # 1. Análisis de Riesgos (Ahora más flexible)
        analysis = qa.analyze(source)
        
        table = Table(title="Riesgos Detectados", show_header=True, header_style="bold magenta")
        table.add_column("Función"), table.add_column("Riesgos")
        
        # Manejo ultra-seguro de la respuesta de la IA
        functions = analysis.get("functions", [])
        for fn in functions:
            name = str(fn.get("name", "N/A"))
            
            # Extraemos los riesgos y forzamos que cada uno sea un string
            raw_risks = fn.get("potential_risks", ["Desconocido"])
            clean_risks_list = []
            
            for r in raw_risks:
                if isinstance(r, dict):
                    # Si la IA mandó un diccionario, sacamos sus valores
                    clean_risks_list.append(" ".join(str(v) for v in r.values()))
                else:
                    clean_risks_list.append(str(r))
            
            risks = ", ".join(clean_risks_list)
            table.add_row(name, risks)
        
        console.print(table)

        # 2. Generación de Tests
        test_code = qa.generate_tests(source, json.dumps(analysis))
        with open("test_generated.py", "w", encoding="utf-8") as f: f.write(test_code)
        
        console.print("[blue]🚀 Ejecutando batería de pruebas...[/blue]")
        res = subprocess.run(["py", "-m", "pytest", "test_generated.py"], capture_output=True, text=True)

        if res.returncode == 0:
            console.print(Panel(f"[bold green]✅ INTENTO {i}: CÓDIGO ASEGURADO.[/bold green]"))
            # --- AGREGA ESTA LÍNEA AQUÍ ---
            generate_audit_report(analysis, i)
            return
        else:
            console.print("[red]❌ FALLO DETECTADO. Curando...[/red]")
            fixed_code = qa.heal(source, res.stdout)
            if fixed_code:
                with open(FILE, "w", encoding="utf-8") as f: f.write(fixed_code)
            
    # --- FUERA DEL BUCLE FOR ---
    # Si el bucle termina y no entramos al 'return' de arriba, es que fallamos
    console.print(Panel("[bold red]🚫 No se pudo asegurar el código tras 5 intentos.[/bold red]"))
    generate_audit_report(analysis, 5)
    
    # Limpieza final de seguridad
    if os.path.exists("test_generated.py"):
        os.remove("test_generated.py")

def generate_audit_report(analysis, attempts):
    """Genera un archivo Markdown con el resumen de la auditoría."""
    # Calculamos el estado de forma limpia
    estado = "✅ SEGURO" if attempts < 5 or (attempts == 5 and "Error" not in analysis.get("summary", "")) else "❌ INSEGURO"
    
    report_content = f"""# 🛡️ Reporte de Auditoría Shadow-QA
    
## 📊 Resumen de la Ejecución
- **Estado Final:** {estado}
- **Ciclos consumidos:** {attempts}
- **Fecha:** {os.popen('date /t').read().strip()}

## 🔍 Hallazgos de Seguridad
"""
    # ... resto de la función igual
    functions = analysis.get("functions", [])
    if not functions:
        report_content += "\nNo se detectaron riesgos críticos iniciales o el análisis falló.\n"
    else:
        for fn in functions:
            name = fn.get("name", "N/A")
            risks = fn.get("potential_risks", ["N/A"])
            report_content += f"### 🛠️ Función: `{name}`\n"
            for risk in risks:
                report_content += f"- [x] {risk}\n"
            report_content += "\n"

    report_content += """
## 📝 Notas del Auditor
El código ha sido procesado por el motor heurístico. Se recomienda una revisión manual para casos de lógica de negocio compleja.
"""
    
    with open("AUDIT_REPORT.md", "w", encoding="utf-8") as f:
        f.write(report_content)
    console.print("\n[bold green]📄 Reporte de auditoría generado: AUDIT_REPORT.md[/bold green]")

if __name__ == "__main__":
    # Simplemente llamamos a la función principal. 
    # Ella ya tiene el 'analysis' y llama al reporte internamente.
    run_shadow_qa()