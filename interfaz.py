"""Interfaz Gradio del sistema experto."""
import gradio as gr
from datos import AULAS, DIAS, FRANJAS, CAPACIDAD_MAXIMA_INSTITUCIONAL
from reglas import RegistroOcupaciones, evaluar_motor, buscar_alternativas, separar_franja

registro = RegistroOcupaciones()
ultima_solicitud_valida = {"aula": None, "dia": None, "franja": None}


def resolver_solicitud(estudiantes, dia, franja, proyector, pcs):
    global ultima_solicitud_valida
    ultima_solicitud_valida = {"aula": None, "dia": None, "franja": None}

    if estudiantes is None or not float(estudiantes).is_integer() or estudiantes <= 0:
        return (
            f"**Error de validación:** ingresá una cantidad entera entre 1 y {CAPACIDAD_MAXIMA_INSTITUCIONAL}.",
            "No se inició la inferencia porque la entrada no es válida.",
            gr.update(variant="secondary", interactive=False),
        )
    estudiantes = int(estudiantes)
    if estudiantes > CAPACIDAD_MAXIMA_INSTITUCIONAL:
        return (
            f"**Error de validación:** {estudiantes} supera la capacidad máxima institucional de {CAPACIDAD_MAXIMA_INSTITUCIONAL}.",
            "No se inició la inferencia porque ninguna aula puede albergar esa cantidad.",
            gr.update(variant="secondary", interactive=False),
        )

    motor, validas, motivos = evaluar_motor(estudiantes, dia, franja, proyector, pcs, registro)
    lineas = [
        "## Resultado de la búsqueda",
        f"- **Estudiantes:** {estudiantes}",
        f"- **Día:** {dia.capitalize()}",
        f"- **Franja:** {franja}",
        f"- **Equipamiento:** {', '.join(x for x, act in [('Proyector', proyector), ('PCs', pcs)] if act) or 'Sin requisitos especiales'}",
        "",
    ]
    if validas:
        mejor = validas[0]
        ultima_solicitud_valida = {"aula": mejor, "dia": dia, "franja": franja}
        lineas += [
            "### Aula recomendada",
            f"**{mejor}**",
            f"- Capacidad: {AULAS[mejor]['capacidad']} personas.",
            f"- Lugares excedentes: {AULAS[mejor]['capacidad'] - estudiantes}.",
            "- Cumple capacidad, equipamiento y disponibilidad horaria.",
        ]
        if len(validas) > 1:
            lineas += ["", "### Otras aulas válidas"]
            for aula in validas[1:]:
                lineas.append(
                    f"- **{aula}** (capacidad: {AULAS[aula]['capacidad']}; "
                    f"excedente: {AULAS[aula]['capacidad'] - estudiantes})"
                )
        btn = gr.update(variant="stop", interactive=True)
    else:
        lineas += ["### No hay aulas disponibles que cumplan todos los requisitos", "", "### Motivos por aula"]
        for aula in AULAS:
            lineas.append(f"- **{aula}:** " + ("; ".join(motivos[aula]) if motivos[aula] else "No se detectó un motivo específico."))
        alternativas = buscar_alternativas(estudiantes, dia, franja, proyector, pcs, registro)
        if alternativas:
            lineas += ["", "### Alternativas horarias para el mismo día"]
            for otra_franja, aula in alternativas:
                lineas.append(f"- **{otra_franja}**: {aula}")
        btn = gr.update(variant="secondary", interactive=False)

    traza = ["## Traza de inferencia (reglas disparadas)"]
    traza += [f"- {paso}" for paso in motor.traza]
    traza += ["", "## Diagnóstico por aula"]
    for aula in AULAS:
        if aula in validas:
            traza.append(f"- **{aula}: VÁLIDA**")
        else:
            traza.append(f"- **{aula}: RECHAZADA**")
            traza += [f"  - {motivo}" for motivo in motivos[aula]]
    return "\n".join(lineas), "\n".join(traza), btn


def confirmar_asignacion():
    global ultima_solicitud_valida
    if not ultima_solicitud_valida["aula"]:
        return "No hay ninguna solicitud validada para asignar.", "", gr.update(variant="secondary", interactive=False)
    aula = ultima_solicitud_valida["aula"]
    dia = ultima_solicitud_valida["dia"]
    franja = ultima_solicitud_valida["franja"]
    inicio, fin = separar_franja(franja)
    if registro.aula_ocupada_en(aula, dia, inicio, fin):
        ultima_solicitud_valida = {"aula": None, "dia": None, "franja": None}
        return "La asignación no se concretó: el aula ya figura ocupada en ese horario.", "Volvé a evaluar la solicitud.", gr.update(variant="secondary", interactive=False)
    registro.agregar(aula, dia, inicio, fin)
    ultima_solicitud_valida = {"aula": None, "dia": None, "franja": None}
    return (
        f"## Asignación concretada\n\nSe reservó **{aula}** para el **{dia.capitalize()}**, de **{franja}**. La ocupación quedó registrada en la sesión actual.",
        "La disponibilidad se volverá a evaluar al realizar una nueva búsqueda.",
        gr.update(variant="secondary", interactive=False),
    )


def crear_interfaz():
    with gr.Blocks(title="Sistema Experto de Asignación de Aulas") as demo:
        gr.Markdown(
            "# Sistema Experto de Asignación de Aulas\n"
            "Motor de inferencia Experta con encadenamiento hacia adelante. "
            "La interfaz muestra la recomendación, los motivos de rechazo y la traza de reglas."
        )
        with gr.Row():
            estudiantes = gr.Number(label="Cantidad de estudiantes", value=20, precision=0)
            dia = gr.Dropdown(label="Día de la semana", choices=DIAS, value="lunes")
            franja = gr.Dropdown(label="Franja horaria", choices=FRANJAS, value="06:00–08:00")
        with gr.Row():
            proyector = gr.Checkbox(label="Requiere proyector", value=False)
            pcs = gr.Checkbox(label="Requiere computadoras (PCs)", value=False)
        with gr.Row():
            buscar = gr.Button("1. Evaluar solicitud", variant="primary")
            btn_asignar = gr.Button("2. Confirmar y concretar asignación", variant="secondary", interactive=False)
        resultado = gr.Markdown()
        diagnostico = gr.Markdown()
        buscar.click(fn=resolver_solicitud, inputs=[estudiantes, dia, franja, proyector, pcs],
                     outputs=[resultado, diagnostico, btn_asignar])
        btn_asignar.click(fn=confirmar_asignacion, inputs=[],
                          outputs=[resultado, diagnostico, btn_asignar])
    return demo
