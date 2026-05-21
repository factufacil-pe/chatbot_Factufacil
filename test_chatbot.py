"""
Tests funcionales del chatbot FactuFácil.
Requiere que el servidor esté corriendo: python main.py
"""
import json
import sys
import requests

BASE_URL = "http://localhost:8000"

TESTS = [
    {
        "group": "Información general",
        "queries": [
            "¿Qué es FactuFácil?",
            "¿Para qué tipo de negocios sirve FactuFácil?",
        ],
    },
    {
        "group": "Planes y precios",
        "queries": [
            "¿Cuánto cuesta el plan básico?",
            "¿Qué diferencia hay entre el plan Básico y el PRO?",
            "¿Cuál es el precio anual del plan PRO?",
        ],
    },
    {
        "group": "Funcionalidades",
        "queries": [
            "¿FactuFácil se integra con SUNAT?",
            "¿Puedo usar FactuFácil desde mi celular?",
            "¿Tiene modo offline para cuando no hay internet?",
            "¿Puedo tener varias sucursales?",
        ],
    },
    {
        "group": "Memoria conversacional",
        "queries": [
            "Necesito un plan para mi ferretería",
            "¿El plan que mencionaste incluye inventario?",
            "¿Y soporte técnico?",
        ],
    },
    {
        "group": "Manejo de alucinaciones",
        "queries": [
            "¿FactuFácil tiene integración con Mercado Libre?",
            "¿Cuánto cuesta el plan Enterprise?",
        ],
    },
]


def check_server() -> bool:
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        return r.status_code == 200
    except requests.ConnectionError:
        return False


def run_tests() -> None:
    print("=" * 65)
    print("  TEST — Chatbot FactuFácil")
    print("=" * 65)

    if not check_server():
        print("\n❌  Servidor no disponible. Ejecutá primero: python main.py\n")
        sys.exit(1)

    print("✓  Servidor activo\n")

    total = passed = 0
    session_id: str | None = None

    for group in TESTS:
        print(f"\n{'─' * 65}")
        print(f"  {group['group']}")
        print(f"{'─' * 65}")

        # Grupo de memoria conversacional: reutiliza la misma sesión
        if group["group"] == "Memoria conversacional":
            session_id = None  # empieza sesión nueva para este grupo

        for query in group["queries"]:
            total += 1
            payload: dict = {"message": query}

            if group["group"] == "Memoria conversacional" and session_id:
                payload["session_id"] = session_id

            try:
                r = requests.post(f"{BASE_URL}/chat", json=payload, timeout=30)
                data = r.json()

                if r.status_code == 200 and data.get("answer"):
                    passed += 1
                    status = "✓"

                    # Capturar session_id del primer mensaje del grupo de memoria
                    if group["group"] == "Memoria conversacional" and not session_id:
                        session_id = data["session_id"]
                else:
                    status = "✗"

                print(f"\n  {status} Q: {query}")
                print(f"    A: {data.get('answer', 'ERROR')[:200]}")

                if data.get("sources"):
                    topics = [s["topic"] for s in data["sources"]]
                    print(f"    Fuentes: {', '.join(topics)}")

            except Exception as e:
                total += 1
                print(f"\n  ✗ Q: {query}")
                print(f"    Error: {e}")

    print(f"\n{'=' * 65}")
    print(f"  Resultado: {passed}/{total} tests pasaron")
    print("=" * 65)

    if passed == total:
        print("  🎉  Todos los tests pasaron.")
    else:
        print(f"  ⚠️   {total - passed} tests fallaron.")


if __name__ == "__main__":
    run_tests()
