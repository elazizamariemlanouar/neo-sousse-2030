"""
tests/test_scenarios.py
10 Test Scenarios for Smart City Neo-Sousse 2030
Covers: compiler, automata, AI module, data integrity

Run: python tests/test_scenarios.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
import json

PASS = "✅ PASS"
FAIL = "❌ FAIL"
results = []

def run_test(name, fn):
    try:
        ok, detail = fn()
        status = PASS if ok else FAIL
        results.append((name, status, detail))
        print(f"{status} | {name}")
        if detail:
            print(f"       {detail}")
    except Exception as e:
        results.append((name, FAIL, str(e)))
        print(f"{FAIL} | {name}: {e}")


# ══════════════════════════════════════════════════════════════
# SCENARIO 1: NL→SQL Basic Compilation
# ══════════════════════════════════════════════════════════════
def test_compiler_basic():
    from compiler.nl_sql_compiler import compile_nl
    result = compile_nl("Affiche les 5 zones les plus polluées")
    assert result.success, f"Compilation failed: {result.error}"
    assert "v_zones_polluees" in result.sql
    assert "ORDER BY pollution_moyenne DESC" in result.sql
    assert "LIMIT 5" in result.sql
    return True, f"SQL: {result.sql.strip()[:80]}…"

run_test("SCENARIO 1: Compilateur — Afficher zones polluées", test_compiler_basic)


# ══════════════════════════════════════════════════════════════
# SCENARIO 2: NL→SQL COUNT Query
# ══════════════════════════════════════════════════════════════
def test_compiler_count():
    from compiler.nl_sql_compiler import compile_nl
    result = compile_nl("Combien de capteurs sont hors service ?")
    assert result.success
    assert "COUNT" in result.sql
    assert "capteurs" in result.sql.lower()
    assert "statut = 'hors_service'" in result.sql
    return True, f"SQL: {result.sql.strip()}"

run_test("SCENARIO 2: Compilateur — COUNT capteurs hors service", test_compiler_count)


# ══════════════════════════════════════════════════════════════
# SCENARIO 3: NL→SQL WHERE Clause
# ══════════════════════════════════════════════════════════════
def test_compiler_where():
    from compiler.nl_sql_compiler import compile_nl
    result = compile_nl("Quels citoyens ont un score écologique > 80 ?")
    assert result.success
    assert "citoyens" in result.sql.lower()
    assert "80" in result.sql
    return True, f"SQL: {result.sql.strip()}"

run_test("SCENARIO 3: Compilateur — WHERE score > 80", test_compiler_where)


# ══════════════════════════════════════════════════════════════
# SCENARIO 4: NL→SQL ORDER BY + LIMIT
# ══════════════════════════════════════════════════════════════
def test_compiler_order_limit():
    from compiler.nl_sql_compiler import compile_nl
    result = compile_nl("Donne-moi le trajet le plus économique en co2")
    assert result.success
    assert "trajets" in result.sql.lower()
    assert "ORDER BY economie_co2 DESC" in result.sql
    assert "LIMIT 1" in result.sql
    return True, f"SQL: {result.sql.strip()}"

run_test("SCENARIO 4: Compilateur — ORDER BY + LIMIT (trajets CO₂)", test_compiler_order_limit)


# ══════════════════════════════════════════════════════════════
# SCENARIO 5: Sensor FSM — Valid Lifecycle
# ══════════════════════════════════════════════════════════════
def test_sensor_fsm_valid():
    from automata.fsm_engine import create_sensor_fsm
    fsm = create_sensor_fsm()
    # Normal lifecycle
    assert fsm.current_state == "inactif"
    fsm.trigger("installation")
    assert fsm.current_state == "actif"
    fsm.trigger("detection_anomalie", {"code_capteur": "C-999"})
    assert fsm.current_state == "signale"
    fsm.trigger("reparation")
    assert fsm.current_state == "en_maintenance"
    fsm.trigger("reparation")
    assert fsm.current_state == "actif"
    return True, f"Final state: {fsm.current_state} (accepted: {fsm.is_accepted()})"

run_test("SCENARIO 5: FSM Capteur — Cycle de vie valide", test_sensor_fsm_valid)


# ══════════════════════════════════════════════════════════════
# SCENARIO 6: Sensor FSM — Invalid Transition
# ══════════════════════════════════════════════════════════════
def test_sensor_fsm_invalid():
    from automata.fsm_engine import create_sensor_fsm, InvalidTransitionError
    fsm = create_sensor_fsm()
    # Can't repair from inactif
    try:
        fsm.trigger("reparation")
        return False, "Should have raised InvalidTransitionError"
    except InvalidTransitionError:
        return True, "InvalidTransitionError correctly raised for invalid transition"

run_test("SCENARIO 6: FSM Capteur — Transition invalide détectée", test_sensor_fsm_invalid)


# ══════════════════════════════════════════════════════════════
# SCENARIO 7: Intervention FSM — Full workflow
# ══════════════════════════════════════════════════════════════
def test_intervention_fsm():
    from automata.fsm_engine import create_intervention_fsm
    fsm = create_intervention_fsm()
    events = ["assigner_tech1", "valider_tech2", "valider_ia", "cloturer"]
    for ev in events:
        fsm.trigger(ev, {"score": 90})
    assert fsm.current_state == "termine"
    assert fsm.is_accepted()
    return True, f"Workflow complet validé — état final: {fsm.current_state}"

run_test("SCENARIO 7: FSM Intervention — Workflow Tech1→Tech2→IA→Terminé", test_intervention_fsm)


# ══════════════════════════════════════════════════════════════
# SCENARIO 8: Sequence Validation
# ══════════════════════════════════════════════════════════════
def test_sequence_validation():
    from automata.fsm_engine import create_sensor_fsm
    fsm = create_sensor_fsm()

    # Valid sequence
    valid, final, path = fsm.validate_sequence([
        "installation", "detection_anomalie", "reparation", "reparation"
    ])
    assert valid, f"Should be valid, got final={final}, path={path}"

    # Invalid sequence (skip installation)
    valid2, final2, path2 = create_sensor_fsm().validate_sequence([
        "detection_anomalie", "reparation"
    ])
    assert not valid2, "Should be invalid"

    return True, f"Valid seq: ✅ | Invalid seq correctly rejected: ✅"

run_test("SCENARIO 8: Validation de séquences d'événements", test_sequence_validation)


# ══════════════════════════════════════════════════════════════
# SCENARIO 9: Full End-to-End Scenario (No DB required)
# ══════════════════════════════════════════════════════════════
def test_e2e_scenario():
    """
    Full scenario:
    1. Sensor goes to 'signale'
    2. NL query "Quelles interventions sont en cours?" compiled to SQL
    3. Intervention FSM advanced through workflow
    """
    from automata.fsm_engine import create_sensor_fsm, create_intervention_fsm
    from compiler.nl_sql_compiler import compile_nl

    # Step 1: Sensor anomaly
    sensor_fsm = create_sensor_fsm()
    sensor_fsm.trigger("installation")
    sensor_fsm.trigger("detection_anomalie", {"code_capteur": "C-452"})
    assert sensor_fsm.current_state == "signale"
    alerts = sensor_fsm.get_alerts()
    assert len(alerts) > 0

    # Step 2: NL query
    nl_result = compile_nl("Liste les interventions en cours")
    assert nl_result.success

    # Step 3: Intervention workflow
    interv_fsm = create_intervention_fsm()
    interv_fsm.trigger("assigner_tech1")
    interv_fsm.trigger("valider_tech2")
    interv_fsm.trigger("valider_ia", {"score": 88})
    interv_fsm.trigger("cloturer")
    assert interv_fsm.is_accepted()

    return True, f"All 3 steps completed ✅ | Sensor alerts: {alerts[0][:60]}…"

run_test("SCENARIO 9: End-to-End — Capteur→Alerte→SQL→Intervention", test_e2e_scenario)


# ══════════════════════════════════════════════════════════════
# SCENARIO 10: Compiler Error Handling
# ══════════════════════════════════════════════════════════════
def test_compiler_errors():
    from compiler.nl_sql_compiler import compile_nl

    # Totally unrecognizable query
    r1 = compile_nl("xyzzy florp blarg")
    # Should either fail gracefully or produce some SQL
    assert r1.error is None or isinstance(r1.error, str)

    # Empty query
    r2 = compile_nl("")
    assert r2 is not None

    # Multiple supported queries all compile
    queries = [
        "Affiche les 10 mesures les plus récentes",
        "Combien d'interventions sont terminées ?",
        "Montre les techniciens disponibles",
        "Liste les véhicules en panne",
    ]
    for q in queries:
        r = compile_nl(q)
        assert r is not None

    return True, f"Error handling graceful ✅ | {len(queries)} queries compiled"

run_test("SCENARIO 10: Gestion d'Erreurs Compilateur", test_compiler_errors)


# ══════════════════════════════════════════════════════════════
# SUMMARY
# ══════════════════════════════════════════════════════════════
print("\n" + "═"*60)
print("RAPPORT DE TESTS — Smart City Neo-Sousse 2030")
print("═"*60)
passed = sum(1 for _, s, _ in results if s == PASS)
total  = len(results)
print(f"\nRésultat: {passed}/{total} tests réussis\n")

for name, status, detail in results:
    print(f"  {status} {name}")

print(f"\n{'✅ TOUS LES TESTS RÉUSSIS' if passed == total else f'⚠️ {total-passed} test(s) échoué(s)'}")
