"""Pruebas automatizadas básicas del motor de reglas.

Ejecutar desde la raíz con:
python -m unittest discover -s pruebas -v

Estas pruebas son comprobaciones internas iniciales. Comparar además con los
casos CP-01 a CP-08 oficiales del grupo cliente.
"""
import unittest
from reglas import RegistroOcupaciones, evaluar_motor
from datos import AULAS, OCUPACIONES_INICIALES


class PruebasMotorAulas(unittest.TestCase):
    def setUp(self):
        self.registro = RegistroOcupaciones(list(OCUPACIONES_INICIALES))

    def test_recomienda_aula_valida_y_menor_excedente(self):
        # Lunes 06-08: 18 estudiantes sin recursos requeridos.
        _, validas, _ = evaluar_motor(18, "lunes", "06:00–08:00", False, False, self.registro)
        self.assertTrue(validas)
        self.assertEqual(validas[0], "Aula 101")
        self.assertEqual(AULAS[validas[0]]["capacidad"] - 18, 2)

    def test_detecta_conflicto_de_horario(self):
        # Aula 102 está ocupada el lunes de 08 a 12.
        _, validas, motivos = evaluar_motor(20, "lunes", "08:00–10:00", False, False, self.registro)
        self.assertNotIn("Aula 102", validas)
        self.assertTrue(any("Ocupada" in motivo for motivo in motivos["Aula 102"]))

    def test_recurso_requerido(self):
        # El aula 101 tiene proyector pero no PCs.
        _, validas, motivos = evaluar_motor(15, "jueves", "06:00–08:00", False, True, self.registro)
        self.assertNotIn("Aula 101", validas)
        self.assertTrue(any("Faltan recursos" in motivo for motivo in motivos["Aula 101"]))

    def test_capacidad_insuficiente(self):
        # Con 50 estudiantes, aulas con capacidad menor no pueden ser válidas.
        _, validas, motivos = evaluar_motor(50, "jueves", "06:00–08:00", False, False, self.registro)
        self.assertNotIn("Aula 101", validas)
        self.assertTrue(any("Capacidad insuficiente" in motivo for motivo in motivos["Aula 101"]))

    def test_encadenamiento_y_traza(self):
        motor, validas, _ = evaluar_motor(18, "lunes", "06:00–08:00", False, False, self.registro)
        self.assertTrue(validas)
        texto = "\n".join(motor.traza)
        for regla in ("R01", "R02", "R04", "R08", "R10", "R11", "R12", "R23"):
            self.assertIn(regla, texto)

    def test_asignacion_actualizada_detecta_ocupacion(self):
        self.registro.agregar("Aula 101", "jueves", "06:00", "08:00")
        _, validas, motivos = evaluar_motor(10, "jueves", "06:00–08:00", False, False, self.registro)
        self.assertNotIn("Aula 101", validas)
        self.assertTrue(any("Ocupada" in motivo for motivo in motivos["Aula 101"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
