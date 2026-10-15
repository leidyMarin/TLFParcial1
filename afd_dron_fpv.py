"""
Parcial 1 - Parte B: Simulación funcional del AFD del dron FPV
================================================================
Lenguaje L = { ARM, DISARM, "SET " E Signo N, "RPM M" N }
    E     in {P, R, Y}
    Signo in {+, -, epsilon}
    N     in D+   (uno o más dígitos)

Restricciones cumplidas:
  - No se usa el módulo `re` ni ninguna librería de expresiones regulares.
  - La función de transición δ(q, a) se implementa explícitamente.
  - CLI con traza paso a paso + batería de pruebas (válidas e inválidas).
"""

MUERTO = "qMuerto"  # estado trampa (las celdas "-" de la tabla del PDF)

LETRAS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
DIGITOS = set("0123456789")
SIGNOS = {"+", "-"}
ALFABETO = LETRAS | DIGITOS | SIGNOS | {" "}


class AFD:
    """Autómata Finito Determinista M = (Q, Σ, δ, q0, F)."""

    def __init__(self, estados, alfabeto, delta, inicial, finales):
        self.Q = estados
        self.sigma = alfabeto
        self.delta_tabla = delta
        self.q0 = inicial
        self.F = finales

    def delta(self, q, a):
        """Función de transición δ(q, a). Total: lo no definido va a qMuerto."""
        if a not in self.sigma:
            return MUERTO
        return self.delta_tabla.get((q, a), MUERTO)

    def ejecutar(self, w):
        """Procesa w símbolo a símbolo. Devuelve (traza, aceptada, estado_final)."""
        q = self.q0
        traza = []
        for i, a in enumerate(w, start=1):
            q_sig = self.delta(q, a)
            traza.append((i, q, a, q_sig))
            q = q_sig
            if q == MUERTO:  # absorbente: ya no se puede aceptar
                break
        return traza, q in self.F, q


def construir_afd_dron():
    """Construye el AFD del lenguaje del dron FPV."""
    d = {}

    def add(q, simbolos, destino):
        for s in simbolos:
            d[(q, s)] = destino

    # --- Rama ARM -----------------------------------------------------
    add("q0", "A", "qA")
    add("qA", "R", "qAR")
    add("qAR", "M", "qOK")

    # --- Rama DISARM --------------------------------------------------
    add("q0", "D", "qD")
    add("qD", "I", "qDI")
    add("qDI", "S", "qDIS")
    add("qDIS", "A", "qDISA")
    add("qDISA", "R", "qDISAR")
    add("qDISAR", "M", "qOK")

    # --- Rama SET <eje><signo?><dígitos+> -----------------------------
    add("q0", "S", "qS")
    add("qS", "E", "qSE")
    add("qSE", "T", "qSET")
    add("qSET", " ", "qSETE")           # espacio obligatorio
    add("qSETE", "PRY", "qSETE_S")      # eje P, R o Y
    add("qSETE_S", SIGNOS, "qSETE_SG")  # signo opcional (nuevo estado)
    add("qSETE_S", DIGITOS, "qSETE_N")  # o directo un dígito
    add("qSETE_SG", DIGITOS, "qSETE_N") # tras el signo, al menos un dígito
    add("qSETE_N", DIGITOS, "qSETE_N")  # más dígitos

    # --- Rama RPM M<dígitos+> -----------------------------------------
    add("q0", "R", "qR")                # faltaba en la tabla del PDF
    add("qR", "P", "qRP")               # faltaba en la tabla del PDF
    add("qRP", "M", "qRPM")
    add("qRPM", " ", "qRPMM")
    add("qRPMM", "M", "qRPMM_M")        # lee la etiqueta M (nuevo estado)
    add("qRPMM_M", DIGITOS, "qRPMM_N")  # exige al menos un dígito
    add("qRPMM_N", DIGITOS, "qRPMM_N")

    estados = {
        "q0", "qA", "qAR", "qD", "qDI", "qDIS", "qDISA", "qDISAR",
        "qS", "qSE", "qSET", "qSETE", "qSETE_S", "qSETE_SG", "qSETE_N",
        "qR", "qRP", "qRPM", "qRPMM", "qRPMM_M", "qRPMM_N", "qOK", MUERTO,
    }
    finales = {"qOK", "qSETE_N", "qRPMM_N"}
    return AFD(estados, ALFABETO, d, "q0", finales)


# ----------------------------------------------------------------------
# Presentación
# ----------------------------------------------------------------------
def mostrar_simbolo(a):
    return "' '" if a == " " else a


def imprimir_traza(afd, w):
    """Muestra la ruta paso a paso y el veredicto final."""
    print(f"\nCadena analizada: '{w}'  (|w| = {len(w)})")
    print("-" * 62)
    print(f"{'Paso':<6}{'Estado actual':<16}{'Símbolo':<10}{'δ(q, a) =':<16}")
    print("-" * 62)

    if w == "":
        print(f"{'-':<6}{afd.q0:<16}{'ε':<10}{afd.q0:<16}")

    traza, aceptada, q_final = afd.ejecutar(w)
    for i, q, a, q_sig in traza:
        nota = ""
        if a not in afd.sigma:
            nota = "  <- símbolo fuera de Σ"
        elif q_sig == MUERTO:
            nota = "  <- sin transición"
        print(f"{i:<6}{q:<16}{mostrar_simbolo(a):<10}{q_sig:<16}{nota}")

    if q_final == MUERTO and len(traza) < len(w):
        print(f"      (se descartan los {len(w) - len(traza)} símbolos restantes)")

    print("-" * 62)
    print(f"Estado final: {q_final}   ¿Es de aceptación? {'SI' if aceptada else 'NO'}")
    print(f"Resultado: {'ACEPTADA' if aceptada else 'RECHAZADA'}")
    return aceptada


def imprimir_tabla(afd):
    """Lista δ agrupando los símbolos que llevan al mismo destino."""
    print("\nFunción de transición δ (las no listadas van a qMuerto)")
    print("-" * 62)
    orden = sorted(afd.Q - {MUERTO}, key=lambda s: (s != "q0", s))
    for q in orden:
        grupos = {}
        for (origen, a), destino in afd.delta_tabla.items():
            if origen == q:
                grupos.setdefault(destino, []).append(a)
        marca = "*" if q in afd.F else " "
        if q == "q0":
            marca = "->"
        for destino, simbolos in grupos.items():
            if set(simbolos) == DIGITOS:
                txt = "D (0-9)"
            else:
                txt = ", ".join(mostrar_simbolo(s) for s in sorted(simbolos))
            print(f"{marca:>2} δ({q}, {txt}) = {destino}")
    print("\nEstado inicial: q0")
    print("Estados de aceptación F =", sorted(afd.F))


# ----------------------------------------------------------------------
# Batería de pruebas
# ----------------------------------------------------------------------
PRUEBAS_VALIDAS = [
    "ARM",
    "DISARM",
    "SET P+15",
    "SET R-10",
    "SET Y0",
    "RPM M8500",
    "SET P20",       # signo opcional (ε)
    "RPM M0",
]

PRUEBAS_INVALIDAS = [
    "SET Z+10",      # eje Z no existe
    "SET P++15",     # doble signo
    "RPM 8500",      # falta la etiqueta M
    "ARMED",         # comando no reconocido
    "SET P+",        # signo sin dígitos
    "RPM M",         # etiqueta sin dígitos
    "arm",           # minúsculas fuera de Σ
    "SET P 15",      # espacio donde no corresponde
    "",              # cadena vacía
    "ARM DISARM",    # dos comandos juntos
]


def correr_pruebas(afd, detalle=False):
    print("\n" + "=" * 62)
    print("BATERÍA DE PRUEBAS")
    print("=" * 62)
    ok = 0
    total = 0

    print("\n[Casos que DEBEN ser ACEPTADAS]")
    for w in PRUEBAS_VALIDAS:
        _, acepta, _ = afd.ejecutar(w)
        total += 1
        ok += acepta
        print(f"  {'OK ' if acepta else 'FALLO'}  '{w}' -> {'ACEPTADA' if acepta else 'RECHAZADA'}")
        if detalle:
            imprimir_traza(afd, w)

    print("\n[Casos que DEBEN ser RECHAZADAS]")
    for w in PRUEBAS_INVALIDAS:
        _, acepta, _ = afd.ejecutar(w)
        total += 1
        ok += (not acepta)
        print(f"  {'OK ' if not acepta else 'FALLO'}  '{w}' -> {'ACEPTADA' if acepta else 'RECHAZADA'}")
        if detalle:
            imprimir_traza(afd, w)

    print("\n" + "-" * 62)
    print(f"Pruebas superadas: {ok}/{total}")
    return ok == total


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------
def menu():
    afd = construir_afd_dron()
    while True:
        print("\n" + "=" * 62)
        print(" SIMULADOR AFD - LENGUAJE DE COMANDOS DRON FPV")
        print("=" * 62)
        print(" 1) Ingresar una cadena y ver la traza")
        print(" 2) Ejecutar la batería de pruebas")
        print(" 3) Ejecutar la batería con traza detallada")
        print(" 4) Ver la función de transición δ")
        print(" 5) Salir")
        opcion = input("Opción: ").strip()

        if opcion == "1":
            w = input("Cadena (se respetan espacios y mayúsculas): ")
            imprimir_traza(afd, w)
        elif opcion == "2":
            correr_pruebas(afd)
        elif opcion == "3":
            correr_pruebas(afd, detalle=True)
        elif opcion == "4":
            imprimir_tabla(afd)
        elif opcion == "5":
            print("Hasta luego.")
            break
        else:
            print("Opción no válida.")


if __name__ == "__main__":
    menu()
