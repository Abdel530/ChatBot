import pytest
import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.reservas import calcular_penalizacion, buscar_reserva, confirmar_cancelacion, registrar_llegada, escalar_recepcion
from tools.acceso import generar_codigo_acceso
from tools.costos import consultar_costo_habitacion
from tools.limpieza import consultar_limpieza


class TestCalcularPenalizacion:
    def test_flexible_cancellation_free(self):
        result = calcular_penalizacion(2)
        assert "0%" in result or "0.00€" in result or "gratuita" in result.lower() or "cancelación gratuita" in result.lower()

    def test_moderada_con_penalizacion(self):
        result = calcular_penalizacion(1)
        assert "50%" in result or "penalización" in result.lower() or "penalizacion" in result.lower()

    def test_no_reembolsable(self):
        result = calcular_penalizacion(3)
        assert "100%" in result or "no reembolsable" in result.lower() or "no_reembolsable" in result.lower()

    def test_reserva_inexistente(self):
        result = calcular_penalizacion(9999)
        assert "No se encontró" in result or "no encontrada" in result.lower()

    def test_result_contains_reserva_id(self):
        result = calcular_penalizacion(1)
        assert "Reserva 1" in result or "reserva 1" in result.lower()


class TestBuscarReserva:
    def test_buscar_por_telefono_existente(self):
        result = buscar_reserva("34600123456")
        assert "Reserva encontrada" in result or "reserva" in result.lower()

    def test_buscar_por_telefono_inexistente(self):
        result = buscar_reserva("9999999999")
        assert "No se encontró" in result or "no encontrada" in result.lower()


class TestGenerarCodigoAcceso:
    def test_genera_codigo(self):
        result = generar_codigo_acceso(1)
        assert "Código" in result or "código" in result.lower() or "generado" in result.lower()

    def test_codigo_es_6_digitos(self):
        result = generar_codigo_acceso(2)
        matches = re.findall(r'\b\d{6}\b', result)
        assert len(matches) > 0, f"No se encontró un código de 6 dígitos en: {result}"

    def test_habitacion_inexistente(self):
        result = generar_codigo_acceso(9999)
        assert "No se encontró" in result or "no encontrada" in result.lower()


class TestConsultarCostoHabitacion:
    def test_retorna_costo(self):
        result = consultar_costo_habitacion(1)
        assert "Coste" in result or "costo" in result.lower() or "€" in result

    def test_habitacion_inexistente(self):
        result = consultar_costo_habitacion(9999)
        assert "No se encontró" in result or "no encontrada" in result.lower()


class TestConsultarLimpieza:
    def test_retorna_estado(self):
        result = consultar_limpieza(1)
        assert "limpieza" in result.lower() or "Habitación" in result

    def test_habitacion_inexistente(self):
        result = consultar_limpieza(9999)
        assert "No se encontró" in result or "no encontrada" in result.lower()


class TestConfirmarCancelacion:
    def test_reserva_existente(self):
        result = confirmar_cancelacion(1)
        assert "cancelada" in result.lower() or "Cancelación" in result or "confirmada" in result.lower()

    def test_reserva_inexistente(self):
        result = confirmar_cancelacion(9999)
        assert "No se encontró" in result or "no encontrada" in result.lower()


class TestRegistrarLlegada:
    def test_registrar_llegada(self):
        result = registrar_llegada(1, "18:00")
        assert "llegada" in result.lower() or "registrada" in result.lower() or "Hora" in result

    def test_reserva_inexistente(self):
        result = registrar_llegada(9999, "18:00")
        assert "No se encontró" in result or "no encontrada" in result.lower()


class TestEscalarRecepcion:
    def test_escalar(self):
        result = escalar_recepcion("34600123456", "Test de escalado")
        assert "recepción" in result.lower() or "agente" in result.lower() or "contactará" in result.lower()