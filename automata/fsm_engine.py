"""
automata/fsm_engine.py
Finite State Machine Engine for Smart City Neo-Sousse 2030

Three DFAs:
  1. SensorFSM        — Cycle de vie d'un capteur
  2. InterventionFSM  — Processus de validation d'intervention
  3. VehicleFSM       — Trajet d'un véhicule autonome

Each FSM stores:
  - states (set)
  - initial_state
  - accepting_states (set)
  - transition_table: {(state, event) → next_state}
  - actions: {(state, event) → callable}  (side effects / alerts)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Set, Optional, Callable, List, Tuple, Any
from datetime import datetime
import json


# ══════════════════════════════════════════════════════════════
# BASE FSM
# ══════════════════════════════════════════════════════════════
class InvalidTransitionError(Exception):
    pass

@dataclass
class FSMHistoryEntry:
    from_state: str
    event: str
    to_state: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)

class FSM:
    """Generic deterministic finite state machine."""

    def __init__(self,
                 name: str,
                 states: Set[str],
                 initial_state: str,
                 accepting_states: Set[str],
                 transitions: Dict[Tuple[str, str], str],
                 actions: Optional[Dict[Tuple[str, str], Callable]] = None):
        assert initial_state in states, f"Initial state '{initial_state}' not in states"
        self.name          = name
        self.states        = states
        self.initial_state = initial_state
        self.accepting_states = accepting_states
        self._transitions  = transitions
        self._actions      = actions or {}
        self.current_state = initial_state
        self.history: List[FSMHistoryEntry] = []
        self._alerts: List[str] = []

    def reset(self):
        self.current_state = self.initial_state
        self.history.clear()
        self._alerts.clear()

    def can_transition(self, event: str) -> bool:
        return (self.current_state, event) in self._transitions

    def available_events(self) -> List[str]:
        return [e for (s, e) in self._transitions if s == self.current_state]

    def trigger(self, event: str, metadata: dict = None) -> str:
        """Fire an event. Returns new state or raises InvalidTransitionError."""
        key = (self.current_state, event)
        if key not in self._transitions:
            available = self.available_events()
            raise InvalidTransitionError(
                f"[{self.name}] No transition from '{self.current_state}' on event '{event}'. "
                f"Available: {available}"
            )
        next_state = self._transitions[key]
        self.history.append(FSMHistoryEntry(
            from_state=self.current_state,
            event=event,
            to_state=next_state,
            metadata=metadata or {}
        ))

        # execute action if defined
        if key in self._actions:
            alert = self._actions[key](self, metadata or {})
            if alert:
                self._alerts.append(alert)

        self.current_state = next_state
        return next_state

    def validate_sequence(self, events: List[str]) -> Tuple[bool, str, List[str]]:
        """
        Validate a sequence of events from the initial state.
        Returns (valid, final_state, path_of_states)
        """
        state = self.initial_state
        path  = [state]
        for event in events:
            key = (state, event)
            if key not in self._transitions:
                return False, state, path
            state = self._transitions[key]
            path.append(state)
        return True, state, path

    def is_accepted(self) -> bool:
        return self.current_state in self.accepting_states

    def get_alerts(self) -> List[str]:
        return self._alerts.copy()

    def transition_table(self) -> Dict:
        """Return transition table as {state: {event: next_state}}."""
        table = {s: {} for s in self.states}
        for (state, event), next_s in self._transitions.items():
            table[state][event] = next_s
        return table

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "current_state": self.current_state,
            "states": list(self.states),
            "accepting_states": list(self.accepting_states),
            "available_events": self.available_events(),
            "is_accepted": self.is_accepted(),
            "history": [
                {"from": h.from_state, "event": h.event, "to": h.to_state,
                 "timestamp": h.timestamp.isoformat()}
                for h in self.history
            ],
            "alerts": self._alerts,
        }


# ══════════════════════════════════════════════════════════════
# 1. SENSOR FSM — Cycle de vie d'un capteur
# ══════════════════════════════════════════════════════════════
# States:   INACTIF → ACTIF → SIGNALÉ → EN_MAINTENANCE → HORS_SERVICE
# Events:   installation, detection_anomalie, reparation, panne
#
# Transition Table:
# ┌─────────────────┬──────────────────────┬───────────────────┐
# │   State         │   Event              │   Next State      │
# ├─────────────────┼──────────────────────┼───────────────────┤
# │ INACTIF         │ installation         │ ACTIF             │
# │ ACTIF           │ detection_anomalie   │ SIGNALE           │
# │ ACTIF           │ panne               │ HORS_SERVICE       │
# │ SIGNALE         │ reparation          │ EN_MAINTENANCE     │
# │ SIGNALE         │ panne               │ HORS_SERVICE       │
# │ EN_MAINTENANCE  │ reparation          │ ACTIF             │
# │ EN_MAINTENANCE  │ panne               │ HORS_SERVICE       │
# │ HORS_SERVICE    │ reparation          │ EN_MAINTENANCE     │
# └─────────────────┴──────────────────────┴───────────────────┘

def _alert_signale(fsm, meta):
    code = meta.get("code_capteur", "inconnu")
    return f"🚨 ALERTE: Capteur {code} signalé — demande d'intervention créée automatiquement"

def _alert_hors_service(fsm, meta):
    code = meta.get("code_capteur", "inconnu")
    return f"🔴 CRITIQUE: Capteur {code} hors service — escalade requise"

def _alert_repare(fsm, meta):
    code = meta.get("code_capteur", "inconnu")
    return f"✅ Capteur {code} remis en service — maintenance terminée"

def create_sensor_fsm() -> FSM:
    return FSM(
        name="SensorLifecycle",
        states={"inactif", "actif", "signale", "en_maintenance", "hors_service"},
        initial_state="inactif",
        accepting_states={"actif"},
        transitions={
            ("inactif",        "installation"):        "actif",
            ("actif",          "detection_anomalie"):  "signale",
            ("actif",          "panne"):               "hors_service",
            ("signale",        "reparation"):          "en_maintenance",
            ("signale",        "panne"):               "hors_service",
            ("en_maintenance", "reparation"):          "actif",
            ("en_maintenance", "panne"):               "hors_service",
            ("hors_service",   "reparation"):          "en_maintenance",
        },
        actions={
            ("actif",         "detection_anomalie"):  _alert_signale,
            ("signale",       "panne"):               _alert_hors_service,
            ("en_maintenance","panne"):               _alert_hors_service,
            ("actif",         "panne"):               _alert_hors_service,
            ("en_maintenance","reparation"):           _alert_repare,
        }
    )


# ══════════════════════════════════════════════════════════════
# 2. INTERVENTION FSM — Processus de validation d'intervention
# ══════════════════════════════════════════════════════════════
# States: DEMANDE → TECH1_ASSIGNÉ → TECH2_VALIDÉ → IA_VALIDÉ → TERMINÉ
# Events: assigner_tech1, valider_tech2, valider_ia, cloturer

def _alert_ia_validation(fsm, meta):
    score = meta.get("score", 0)
    if score < 60:
        return f"⚠️ IA: Score de validation faible ({score}/100) — révision recommandée"
    return f"✅ IA: Validation approuvée (score {score}/100)"

def create_intervention_fsm() -> FSM:
    return FSM(
        name="InterventionValidation",
        states={"demande", "tech1_assigne", "tech2_valide", "ia_valide", "termine"},
        initial_state="demande",
        accepting_states={"termine"},
        transitions={
            ("demande",       "assigner_tech1"): "tech1_assigne",
            ("tech1_assigne", "valider_tech2"):  "tech2_valide",
            ("tech2_valide",  "valider_ia"):     "ia_valide",
            ("ia_valide",     "cloturer"):        "termine",
            # Rejection paths
            ("tech1_assigne", "rejeter"):        "demande",
            ("tech2_valide",  "rejeter"):        "tech1_assigne",
            ("ia_valide",     "rejeter"):        "tech2_valide",
        },
        actions={
            ("tech2_valide", "valider_ia"): _alert_ia_validation,
        }
    )


# ══════════════════════════════════════════════════════════════
# 3. VEHICLE FSM — Trajet d'un véhicule autonome
# ══════════════════════════════════════════════════════════════
# States: STATIONNÉ → EN_ROUTE → EN_PANNE | ARRIVÉ
# Events: depart, arrivee, panne, reparation, retour_base

def _alert_vehicle_panne(fsm, meta):
    immat = meta.get("immatriculation", "inconnu")
    loc   = meta.get("position", "position inconnue")
    return f"🚨 PANNE VÉHICULE {immat} à {loc} — intervention d'urgence requise"

def create_vehicle_fsm() -> FSM:
    return FSM(
        name="VehicleJourney",
        states={"stationne", "en_route", "en_panne", "arrive"},
        initial_state="stationne",
        accepting_states={"arrive", "stationne"},
        transitions={
            ("stationne", "depart"):     "en_route",
            ("en_route",  "arrivee"):    "arrive",
            ("en_route",  "panne"):      "en_panne",
            ("en_panne",  "reparation"): "en_route",
            ("en_panne",  "remorquage"): "stationne",
            ("arrive",    "retour_base"):"stationne",
        },
        actions={
            ("en_route", "panne"): _alert_vehicle_panne,
        }
    )


# ══════════════════════════════════════════════════════════════
# FSM MANAGER — manages multiple FSM instances
# ══════════════════════════════════════════════════════════════
class FSMManager:
    """Manages FSM instances keyed by entity ID."""

    def __init__(self):
        self._sensors:       Dict[str, FSM] = {}
        self._interventions: Dict[int, FSM] = {}
        self._vehicles:      Dict[int, FSM] = {}

    # ── Sensors ──────────────────────────────────────────────
    def get_sensor(self, capteur_id: str, current_statut: str = "inactif") -> FSM:
        if capteur_id not in self._sensors:
            fsm = create_sensor_fsm()
            # Restore state from DB
            if current_statut in fsm.states:
                fsm.current_state = current_statut
            self._sensors[capteur_id] = fsm
        return self._sensors[capteur_id]

    def trigger_sensor(self, capteur_id: str, event: str,
                       current_statut: str = "inactif",
                       metadata: dict = None) -> dict:
        fsm = self.get_sensor(capteur_id, current_statut)
        try:
            new_state = fsm.trigger(event, metadata or {})
            return {"success": True, "new_state": new_state, "alerts": fsm.get_alerts()}
        except InvalidTransitionError as e:
            return {"success": False, "error": str(e), "current_state": fsm.current_state}

    # ── Interventions ────────────────────────────────────────
    def get_intervention(self, interv_id: int, current_statut: str = "demande") -> FSM:
        if interv_id not in self._interventions:
            fsm = create_intervention_fsm()
            if current_statut in fsm.states:
                fsm.current_state = current_statut
            self._interventions[interv_id] = fsm
        return self._interventions[interv_id]

    def trigger_intervention(self, interv_id: int, event: str,
                             current_statut: str = "demande",
                             metadata: dict = None) -> dict:
        fsm = self.get_intervention(interv_id, current_statut)
        try:
            new_state = fsm.trigger(event, metadata or {})
            return {"success": True, "new_state": new_state, "alerts": fsm.get_alerts()}
        except InvalidTransitionError as e:
            return {"success": False, "error": str(e), "current_state": fsm.current_state}

    # ── Vehicles ─────────────────────────────────────────────
    def get_vehicle(self, veh_id: int, current_statut: str = "stationne") -> FSM:
        if veh_id not in self._vehicles:
            fsm = create_vehicle_fsm()
            if current_statut in fsm.states:
                fsm.current_state = current_statut
            self._vehicles[veh_id] = fsm
        return self._vehicles[veh_id]

    def trigger_vehicle(self, veh_id: int, event: str,
                        current_statut: str = "stationne",
                        metadata: dict = None) -> dict:
        fsm = self.get_vehicle(veh_id, current_statut)
        try:
            new_state = fsm.trigger(event, metadata or {})
            return {"success": True, "new_state": new_state, "alerts": fsm.get_alerts()}
        except InvalidTransitionError as e:
            return {"success": False, "error": str(e), "current_state": fsm.current_state}

    def get_all_alerts(self) -> List[str]:
        alerts = []
        for fsm in list(self._sensors.values()) + list(self._interventions.values()) + list(self._vehicles.values()):
            alerts.extend(fsm.get_alerts())
        return alerts


# Singleton instance
fsm_manager = FSMManager()


# ══════════════════════════════════════════════════════════════
# DEMO
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=== Sensor FSM Demo ===")
    fsm = create_sensor_fsm()
    events = ["installation", "detection_anomalie", "reparation", "reparation"]
    for ev in events:
        try:
            s = fsm.trigger(ev, {"code_capteur": "C-452"})
            print(f"  Event '{ev}' → {s}")
        except InvalidTransitionError as e:
            print(f"  ❌ {e}")

    print("\nAlerts:", fsm.get_alerts())
    print("\nTransition table:")
    import json
    print(json.dumps(fsm.transition_table(), indent=2))

    print("\n=== Intervention FSM Demo ===")
    fsm2 = create_intervention_fsm()
    for ev in ["assigner_tech1", "valider_tech2", "valider_ia", "cloturer"]:
        s = fsm2.trigger(ev, {"score": 88})
        print(f"  Event '{ev}' → {s}")
    print("  Accepted:", fsm2.is_accepted())

    print("\n=== Sequence Validation ===")
    fsm3 = create_sensor_fsm()
    valid, final, path = fsm3.validate_sequence(["installation", "detection_anomalie", "reparation", "reparation"])
    print(f"  Valid: {valid}, Final: {final}, Path: {path}")
