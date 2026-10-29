# Sistema experto de asignación de aulas

**Repositorio:** `AD2_2026.2_GF_REPO`  
**Materia:** Análisis de Datos II — Sistemas Expertos y Redes de Conocimiento  
**Grupo proveedor:** Grupo F  
**Grupo cliente:** Grupo E

## Integrantes

**Grupo F (proveedor)**
- Melina Larramendy
- Karen Benzi
- Lucas Gabriel Seguro
- Azucarena del Rosario Paez Campos
- Ignacio Agustin Leonetti

**Grupo E (cliente)**
- Daniel García
- Francisco Possamai
- Mauricio Chambi
- Gabriela Martinez Soliz
- Gabriela Pari Vaca

## Descripción

El sistema recibe una solicitud con cantidad de estudiantes, día, franja horaria y necesidades de proyector y/o computadoras. Evalúa la capacidad, los recursos y la disponibilidad de cada aula. Si existen aulas válidas, recomienda la que tenga el menor excedente de capacidad. También informa motivos de rechazo, alternativas horarias cuando no hay una opción válida y una traza de las reglas disparadas.

Los datos de aulas y ocupaciones incluidos son **datos de ejemplo**, no un registro institucional real. Las asignaciones confirmadas se guardan solo en la sesión de ejecución y no persisten al cerrar el programa.

## Estructura

```text
AD2_2026.2_GF_REPO/
├── README.md
├── requirements.txt
├── main.py
├── reglas.py
├── interfaz.py
├── datos.py
└── .gitignore
```

## Requisitos

- Python 3.10 recomendado para compatibilidad con Experta 1.9.4.
- `pip`.

La versión exacta de Python usada para validar la entrega debe registrarse aquí después de probarla en el entorno definitivo.

## Instalación

Desde la carpeta raíz del repositorio:

```bash
python -m venv .venv
```

Activar el entorno virtual:

**Windows (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
```

**macOS/Linux:**
```bash
source .venv/bin/activate
```

Instalar dependencias:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Ejecución de la aplicación

```bash
python main.py
```

Gradio mostrará en la terminal la dirección local para abrir la interfaz en el navegador. No se activa un enlace público compartido por defecto.

## Ejecutar los casos de prueba

Desde la carpeta raíz:

```bash
python -m unittest discover -s pruebas -v
```

Las pruebas verifican criterios principales del motor. Antes de la entrega, el equipo debe contrastar sus resultados con los casos oficiales CP-01 a CP-08 del cliente y agregar cualquier escenario que no esté cubierto.

## Motor de reglas y trazabilidad

El motor usa Experta con encadenamiento hacia adelante: parte de hechos iniciales (`Solicitud` y `Aula`), dispara reglas que derivan hechos intermedios y continúa hasta generar clasificación y diagnósticos. Las reglas R01–R24 están documentadas en `reglas.py`. Cada ejecución conserva `motor.traza`, que registra el identificador y la descripción de las reglas disparadas.

Ejemplo de cadena de inferencia: R01 deriva `SolicitudAnalizada`; R02/R04/R08 evalúan capacidad, recursos y disponibilidad; R10 deriva `Candidata`; R11 genera `AulaValida`; R12 calcula el excedente; R23 produce una explicación final.

## Limitaciones conocidas

- Catálogo y ocupaciones de ejemplo.
- No optimiza el horario global del cuatrimestre ni prioriza automáticamente solicitudes simultáneas.
- No gestiona eventos o exámenes ni integra sistemas académicos externos.
- Las ocupaciones agregadas por el botón de confirmación existen solo durante la sesión actual.
- Las versiones de dependencias deben probarse en un entorno limpio antes de considerar la ejecución plenamente reproducible.

## Equipo y responsabilidad

El Grupo F es responsable del desarrollo. El Grupo E actúa como cliente del sistema. La aplicación y los casos de prueba deben ser revisados por el equipo antes de la entrega final.
