"""Motor de reglas del sistema experto de asignación de aulas.

Se usa encadenamiento hacia adelante con Experta. Cada regla incluye un
comentario sobre el conocimiento del dominio que representa.
"""
import collections
import collections.abc

# Compatibilidad requerida por algunas versiones antiguas de Experta.
for _nombre in ("Mapping", "MutableMapping", "Sequence", "Iterable", "Callable"):
    if not hasattr(collections, _nombre) and hasattr(collections.abc, _nombre):
        setattr(collections, _nombre, getattr(collections.abc, _nombre))

from experta import Fact, KnowledgeEngine, Rule, MATCH, TEST, AND
from datos import AULAS, OCUPACIONES_INICIALES


def normalizar_dia(dia):
    """Normaliza el día para comparar valores con/sin tildes."""
    return (str(dia).lower().strip()
            .replace("á", "a").replace("é", "e")
            .replace("í", "i").replace("ó", "o")
            .replace("ú", "u"))


def hora_a_minutos(hora):
    h, m = map(int, hora.split(":"))
    return h * 60 + m


def separar_franja(franja):
    inicio, fin = franja.replace("–", "-").split("-")
    return inicio.strip(), fin.strip()


def se_superponen(inicio1, fin1, inicio2, fin2):
    """Dos intervalos se superponen si cada uno comienza antes de que acabe el otro."""
    return (hora_a_minutos(inicio1) < hora_a_minutos(fin2)
            and hora_a_minutos(inicio2) < hora_a_minutos(fin1))


class RegistroOcupaciones:
    """Estado de ocupaciones de la sesión, separado de los datos iniciales."""
    def __init__(self, ocupaciones=None):
        self.ocupaciones = list(OCUPACIONES_INICIALES if ocupaciones is None else ocupaciones)

    def aula_ocupada_en(self, aula, dia, inicio, fin):
        return any(
            aula_ocupada == aula
            and normalizar_dia(dia_ocupado) == normalizar_dia(dia)
            and se_superponen(inicio, fin, inicio_ocupado, fin_ocupado)
            for aula_ocupada, dia_ocupado, inicio_ocupado, fin_ocupado in self.ocupaciones
        )

    def agregar(self, aula, dia, inicio, fin):
        self.ocupaciones.append((aula, normalizar_dia(dia), inicio, fin))


# Hechos iniciales y derivados del motor de inferencia.
class Solicitud(Fact):
    """Hecho inicial: petición de asignación de aula."""


class SolicitudAnalizada(Fact):
    """Hecho derivado: solicitud lista para evaluar."""


class Aula(Fact):
    """Hecho declarativo: características de una aula."""


class CapacidadOK(Fact): pass
class CapacidadInsuficiente(Fact): pass
class RecursosOK(Fact): pass
class RecursosInsuficientes(Fact): pass
class FaltaRecurso(Fact): pass
class HorarioOK(Fact): pass
class ConflictoHorario(Fact): pass
class Candidata(Fact): pass
class Rechazo(Fact): pass
class AulaValida(Fact): pass
class CapacidadExcedente(Fact): pass
class DiagnosticoFinal(Fact): pass


class MotorAulas(KnowledgeEngine):
    """Evalúa una solicitud y conserva la traza de reglas activadas."""

    def __init__(self, registro=None):
        super().__init__()
        self.traza = []
        self.registro = registro or RegistroOcupaciones()

    def registrar(self, regla, texto):
        self.traza.append(f"{regla}: {texto}")

    # R01. Conocimiento: toda solicitud recibida se normaliza como hecho analizable.
    @Rule(Solicitud(estudiantes=MATCH.n, dia=MATCH.d, inicio=MATCH.i, fin=MATCH.f,
                    proyector=MATCH.p, pcs=MATCH.pc))
    def r01_analizar_solicitud(self, n, d, i, f, p, pc):
        self.declare(SolicitudAnalizada(estudiantes=n, dia=d, inicio=i, fin=f,
                                        proyector=p, pcs=pc))
        self.registrar("R01", "Solicitud recibida y preparada para evaluación.")

    # R02. Conocimiento: un aula sirve si su capacidad es igual o mayor a la demanda.
    @Rule(AND(SolicitudAnalizada(estudiantes=MATCH.n),
              Aula(nombre=MATCH.a, capacidad=MATCH.c),
              TEST(lambda n, c: c >= n)))
    def r02_capacidad_ok(self, n, a, c):
        self.declare(CapacidadOK(aula=a))
        self.registrar("R02", f"{a}: capacidad suficiente ({c} >= {n}).")

    # R03. Conocimiento: un aula menor que la demanda no puede ser asignada.
    @Rule(AND(SolicitudAnalizada(estudiantes=MATCH.n),
              Aula(nombre=MATCH.a, capacidad=MATCH.c),
              TEST(lambda n, c: c < n)))
    def r03_capacidad_insuficiente(self, n, a, c):
        self.declare(CapacidadInsuficiente(aula=a, capacidad=c, requeridos=n))
        self.registrar("R03", f"{a}: capacidad insuficiente ({c} < {n}).")

    # R04. Conocimiento: el aula debe incluir todos los recursos solicitados.
    @Rule(AND(SolicitudAnalizada(proyector=MATCH.p, pcs=MATCH.pc),
              Aula(nombre=MATCH.a, recursos=MATCH.rec),
              TEST(lambda p, pc, rec:
                   (not p or "proyector" in rec) and (not pc or "pcs" in rec))))
    def r04_recursos_ok(self, p, pc, a, rec):
        self.declare(RecursosOK(aula=a))
        self.registrar("R04", f"{a}: dispone de todos los recursos solicitados.")

    # R05. Conocimiento: si falta algún recurso requerido, el aula se descarta por equipamiento.
    @Rule(AND(SolicitudAnalizada(proyector=MATCH.p, pcs=MATCH.pc),
              Aula(nombre=MATCH.a, recursos=MATCH.rec),
              TEST(lambda p, pc, rec:
                   (p and "proyector" not in rec) or (pc and "pcs" not in rec))))
    def r05_recursos_insuficientes(self, p, pc, a, rec):
        faltantes = []
        if p and "proyector" not in rec:
            faltantes.append("proyector")
        if pc and "pcs" not in rec:
            faltantes.append("PCs")
        self.declare(RecursosInsuficientes(aula=a, faltantes=tuple(faltantes)))
        self.registrar("R05", f"{a}: faltan recursos ({', '.join(faltantes)}).")

    # R06. Conocimiento: si se solicita proyector y el aula no lo tiene, registrar la carencia.
    @Rule(AND(SolicitudAnalizada(proyector=True),
              Aula(nombre=MATCH.a, recursos=MATCH.rec),
              TEST(lambda rec: "proyector" not in rec)))
    def r06_falta_proyector(self, a, rec):
        self.declare(FaltaRecurso(aula=a, recurso="proyector"))
        self.registrar("R06", f"{a}: se deriva falta de proyector.")

    # R07. Conocimiento: si se solicitan PCs y el aula no tiene PCs, registrar la carencia.
    @Rule(AND(SolicitudAnalizada(pcs=True),
              Aula(nombre=MATCH.a, recursos=MATCH.rec),
              TEST(lambda rec: "pcs" not in rec)))
    def r07_falta_pcs(self, a, rec):
        self.declare(FaltaRecurso(aula=a, recurso="PCs"))
        self.registrar("R07", f"{a}: se deriva falta de computadoras.")

    # R08. Conocimiento: una franja sin superposición está disponible.
    @Rule(SolicitudAnalizada(dia=MATCH.d, inicio=MATCH.i, fin=MATCH.f),
              Aula(nombre=MATCH.a))
    def r08_horario_ok(self, d, i, f, a):
        if not self.registro.aula_ocupada_en(a, d, i, f):
            self.declare(HorarioOK(aula=a))
            self.registrar("R08", f"{a}: no se detectan superposiciones horarias.")
# R09. Conocimiento: una superposición con una ocupación existente impide la asignación.
    @Rule(
        SolicitudAnalizada(dia=MATCH.d, inicio=MATCH.i, fin=MATCH.f),
        Aula(nombre=MATCH.a)
    )
    def r09_conflicto_horario(self, a, d, i, f):
        ocupaciones = [
            (ini, fin) for au, dia_oc, ini, fin in self.registro.ocupaciones
            if au == a and normalizar_dia(dia_oc) == normalizar_dia(d)
            and se_superponen(i, f, ini, fin)
        ]
        if ocupaciones:
            detalle = ", ".join(f"{ini}-{fin}" for ini, fin in ocupaciones)
            self.declare(ConflictoHorario(aula=a, detalle=detalle))
            self.registrar("R09", f"{a}: conflicto horario con {detalle}.")
    # R10. Conocimiento: capacidad, recursos y horario positivos hacen candidata a un aula.
    @Rule(AND(CapacidadOK(aula=MATCH.a), RecursosOK(aula=MATCH.a), HorarioOK(aula=MATCH.a)))
    def r10_generar_candidata(self, a):
        self.declare(Candidata(aula=a))
        self.registrar("R10", f"{a}: cumple las tres condiciones y es candidata.")

    # R11. Conocimiento: las candidatas que superan los filtros se clasifican como válidas.
    @Rule(Candidata(aula=MATCH.a))
    def r11_aula_valida(self, a):
        self.declare(AulaValida(aula=a))
        self.registrar("R11", f"{a}: clasificada como aula válida.")

    # R12. Conocimiento: calcular cuántas plazas sobran en cada aula válida.
    @Rule(AND(AulaValida(aula=MATCH.a), SolicitudAnalizada(estudiantes=MATCH.n),
              Aula(nombre=MATCH.a, capacidad=MATCH.c)))
    def r12_excedente(self, a, n, c):
        self.declare(CapacidadExcedente(aula=a, excedente=c-n))
        self.registrar("R12", f"{a}: excedente de capacidad calculado ({c-n} lugares).")

    # R13. Conocimiento: informar rechazo únicamente por capacidad cuando los otros filtros pasan.
    @Rule(AND(CapacidadInsuficiente(aula=MATCH.a), RecursosOK(aula=MATCH.a), HorarioOK(aula=MATCH.a)))
    def r13_rechazo_capacidad(self, a):
        self.declare(Rechazo(aula=a, causa="capacidad"))
        self.registrar("R13", f"{a}: rechazada únicamente por capacidad.")

    # R14. Conocimiento: informar rechazo únicamente por recursos cuando los otros filtros pasan.
    @Rule(AND(CapacidadOK(aula=MATCH.a), RecursosInsuficientes(aula=MATCH.a), HorarioOK(aula=MATCH.a)))
    def r14_rechazo_recursos(self, a):
        self.declare(Rechazo(aula=a, causa="recursos"))
        self.registrar("R14", f"{a}: rechazada únicamente por equipamiento.")

    # R15. Conocimiento: informar rechazo únicamente por horario cuando los otros filtros pasan.
    @Rule(AND(CapacidadOK(aula=MATCH.a), RecursosOK(aula=MATCH.a), ConflictoHorario(aula=MATCH.a)))
    def r15_rechazo_horario(self, a):
        self.declare(Rechazo(aula=a, causa="horario"))
        self.registrar("R15", f"{a}: rechazada únicamente por conflicto horario.")

    # R16. Conocimiento: registrar rechazo por capacidad y recursos.
    @Rule(AND(CapacidadInsuficiente(aula=MATCH.a), RecursosInsuficientes(aula=MATCH.a), HorarioOK(aula=MATCH.a)))
    def r16_rechazo_capacidad_recursos(self, a):
        self.declare(Rechazo(aula=a, causa="capacidad y recursos"))
        self.registrar("R16", f"{a}: rechazada por capacidad y equipamiento.")

    # R17. Conocimiento: registrar rechazo por capacidad y horario.
    @Rule(AND(CapacidadInsuficiente(aula=MATCH.a), RecursosOK(aula=MATCH.a), ConflictoHorario(aula=MATCH.a)))
    def r17_rechazo_capacidad_horario(self, a):
        self.declare(Rechazo(aula=a, causa="capacidad y horario"))
        self.registrar("R17", f"{a}: rechazada por capacidad y horario.")

    # R18. Conocimiento: registrar rechazo por recursos y horario.
    @Rule(AND(CapacidadOK(aula=MATCH.a), RecursosInsuficientes(aula=MATCH.a), ConflictoHorario(aula=MATCH.a)))
    def r18_rechazo_recursos_horario(self, a):
        self.declare(Rechazo(aula=a, causa="recursos y horario"))
        self.registrar("R18", f"{a}: rechazada por equipamiento y horario.")

    # R19. Conocimiento: registrar rechazo cuando fallan los tres criterios.
    @Rule(AND(CapacidadInsuficiente(aula=MATCH.a), RecursosInsuficientes(aula=MATCH.a), ConflictoHorario(aula=MATCH.a)))
    def r19_rechazo_total(self, a):
        self.declare(Rechazo(aula=a, causa="capacidad, recursos y horario"))
        self.registrar("R19", f"{a}: rechazada por capacidad, equipamiento y horario.")

    # R20. Conocimiento: convertir el hecho de capacidad insuficiente en un diagnóstico legible.
    @Rule(CapacidadInsuficiente(aula=MATCH.a, capacidad=MATCH.c, requeridos=MATCH.n))
    def r20_diagnostico_capacidad(self, a, c, n):
        self.declare(DiagnosticoFinal(aula=a, detalle=f"Capacidad insuficiente: {c} plazas para {n} estudiantes."))
        self.registrar("R20", f"{a}: diagnóstico final de capacidad registrado.")

    # R21. Conocimiento: convertir el hecho de recursos faltantes en un diagnóstico legible.
    @Rule(RecursosInsuficientes(aula=MATCH.a, faltantes=MATCH.f))
    def r21_diagnostico_recursos(self, a, f):
        self.declare(DiagnosticoFinal(aula=a, detalle=f"Faltan recursos: {', '.join(f)}."))
        self.registrar("R21", f"{a}: diagnóstico final de equipamiento registrado.")

    # R22. Conocimiento: convertir un conflicto horario en un diagnóstico legible.
    @Rule(ConflictoHorario(aula=MATCH.a, detalle=MATCH.d))
    def r22_diagnostico_horario(self, a, d):
        self.declare(DiagnosticoFinal(aula=a, detalle=f"Conflicto horario: {d}."))
        self.registrar("R22", f"{a}: diagnóstico final de disponibilidad registrado.")

    # R23. Conocimiento: generar explicación final para cada aula válida con su excedente.
    @Rule(AND(AulaValida(aula=MATCH.a), CapacidadExcedente(aula=MATCH.a, excedente=MATCH.e)))
    def r23_explicar_aula_valida(self, a, e):
        self.declare(DiagnosticoFinal(aula=a, detalle=f"Aula válida; excedente de capacidad: {e}."))
        self.registrar("R23", f"{a}: explicación final de aula válida generada.")

    # R24. Conocimiento: registrar el cierre del procesamiento de la solicitud.
    @Rule(SolicitudAnalizada(estudiantes=MATCH.n, dia=MATCH.d, inicio=MATCH.i, fin=MATCH.f))
    def r24_cierre_evaluacion(self, n, d, i, f):
        self.registrar("R24", f"Evaluación procesada para {n} estudiantes, {d}, {i}-{f}.")


def evaluar_motor(estudiantes, dia, franja, proyector=False, pcs=False, registro=None):
    """Ejecuta la inferencia y devuelve motor, aulas válidas ordenadas y motivos."""
    inicio, fin = separar_franja(franja)
    motor = MotorAulas(registro=registro)
    motor.reset()
    motor.declare(Solicitud(
        estudiantes=int(estudiantes), dia=normalizar_dia(dia),
        inicio=inicio, fin=fin, proyector=bool(proyector), pcs=bool(pcs)
    ))
    for nombre, datos in AULAS.items():
        motor.declare(Aula(nombre=nombre, capacidad=datos["capacidad"],
                           recursos=tuple(sorted(datos["recursos"]))))
    motor.run()
    hechos = list(motor.facts.values())

    candidatas = {f["aula"] for f in hechos if isinstance(f, AulaValida)}
    excedentes = {f["aula"]: f["excedente"] for f in hechos if isinstance(f, CapacidadExcedente)}
    ordenadas = sorted(candidatas, key=lambda aula: (excedentes.get(aula, 9999), aula))

    motivos = {aula: [] for aula in AULAS}
    for hecho in hechos:
        if isinstance(hecho, CapacidadInsuficiente):
            motivos[hecho["aula"]].append(
                f"Capacidad insuficiente: admite {hecho['capacidad']} y se requieren {hecho['requeridos']}."
            )
        elif isinstance(hecho, RecursosInsuficientes):
            motivos[hecho["aula"]].append("Faltan recursos: " + ", ".join(hecho["faltantes"]) + ".")
        elif isinstance(hecho, ConflictoHorario):
            motivos[hecho["aula"]].append("Ocupada en la franja solicitada (" + hecho["detalle"] + ").")
    return motor, ordenadas, motivos


def buscar_alternativas(estudiantes, dia, franja, proyector=False, pcs=False, registro=None):
    """Busca otras franjas del mismo día que tengan al menos un aula válida."""
    alternativas = []
    for otra_franja in __import__("datos").FRANJAS:
        if otra_franja == franja:
            continue
        _, validas, _ = evaluar_motor(estudiantes, dia, otra_franja, proyector, pcs, registro)
        if validas:
            alternativas.append((otra_franja, validas[0]))
    return alternativas
