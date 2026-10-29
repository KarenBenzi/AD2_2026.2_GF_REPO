"""Datos de ejemplo del sistema experto de asignación de aulas.

El catálogo y las ocupaciones son datos ficticios para demostración. En una
implementación institucional deberían reemplazarse por datos autorizados.
"""

AULAS = {
    "Aula 101": {"capacidad": 20, "recursos": {"proyector"}},
    "Aula 102": {"capacidad": 30, "recursos": {"proyector", "pcs"}},
    "Aula 103": {"capacidad": 40, "recursos": {"proyector"}},
    "Laboratorio 1": {"capacidad": 25, "recursos": {"pcs"}},
    "Aula 201": {"capacidad": 60, "recursos": {"proyector", "pcs"}},
    "Aula 202": {"capacidad": 80, "recursos": set()},
}

# Cada ocupación tiene la forma: (aula, día, hora de inicio, hora de fin).
OCUPACIONES_INICIALES = [
    ("Aula 102", "lunes", "08:00", "12:00"),
    ("Aula 103", "lunes", "09:00", "11:00"),
    ("Laboratorio 1", "martes", "13:00", "17:00"),
    ("Aula 201", "miercoles", "18:00", "22:00"),
    ("Aula 202", "martes", "10:00", "12:00"),
]

DIAS = ["lunes", "martes", "miercoles", "jueves", "viernes"]
FRANJAS = [
    "06:00–08:00", "08:00–10:00", "10:00–12:00", "12:00–14:00",
    "14:00–16:00", "16:00–18:00", "18:00–20:00", "20:00–22:00",
]
CAPACIDAD_MAXIMA_INSTITUCIONAL = max(
    aula["capacidad"] for aula in AULAS.values()
)
