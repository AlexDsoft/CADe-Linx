from collections import defaultdict
from components.base import ElectricalComponent, Wire
from components.library import (
    PowerSupply1P, PowerSupply3P, PowerSupply3PN,
    Contactor3P, AuxContactNO, AuxContactNC,
    ThermalRelay3P, AuxThermalNO, AuxThermalNC,
    ContactorCoil, TimerCoilTON, TimerCoilTOF,
    TimerContactTON_NO, TimerContactTON_NC,
    TimerContactTOF_NO, TimerContactTOF_NC,
    PilotLamp
)


def pt_key(pt):
    return (round(pt.x() / 5) * 5, round(pt.y() / 5) * 5)


class CircuitSimulator:
    def __init__(self, scene):
        self.scene = scene

    def reset(self):
        for item in self.scene.items():
            if isinstance(item, ElectricalComponent):
                item.is_simulating = False
                item.energized = False
                if not item.__class__.__name__.startswith("Fuse"):
                    item.active_state = False
                if hasattr(item, "delay_sec"):
                    item.remaining_sec = float(item.delay_sec)
                for t in item.terminals:
                    t.potential = None
                item.update()
            elif isinstance(item, Wire):
                item.energized = False
                item.potential = None
                item.update()

    def step(self, dt_sec: float = 0.1):
        comps = [
            it for it in self.scene.items()
            if isinstance(it, ElectricalComponent) and not getattr(it, "_is_ghost", False)
        ]
        wires = [it for it in self.scene.items() if isinstance(it, Wire)]

        for c in comps:
            c.is_simulating = True
            for t in c.terminals:
                t.potential = None

        for w in wires:
            w.energized = False
            w.potential = None

        # 1. Construir grafo de conectividad por coordenadas e interconexiones internas
        adj = defaultdict(set)
        coord_to_terms = defaultdict(list)
        coord_to_wires = defaultdict(list)

        for c in comps:
            for t in c.terminals:
                k = pt_key(t.scene_pos())
                coord_to_terms[k].append(t)
            for t1, t2 in c.internal_connections():
                k1, k2 = pt_key(t1.scene_pos()), pt_key(t2.scene_pos())
                adj[k1].add(k2)
                adj[k2].add(k1)

        for w in wires:
            k1, k2 = pt_key(w.p1), pt_key(w.p2)
            adj[k1].add(k2)
            adj[k2].add(k1)
            coord_to_wires[k1].append(w)
            coord_to_wires[k2].append(w)

        # 2. Propagar potenciales desde las fuentes de alimentación
        sources = []
        for c in comps:
            if isinstance(c, PowerSupply1P):
                sources.append((pt_key(c.t_l.scene_pos()), "L1"))
                sources.append((pt_key(c.t_n.scene_pos()), "N"))
            elif isinstance(c, PowerSupply3P):
                sources.append((pt_key(c.t_l1.scene_pos()), "L1"))
                sources.append((pt_key(c.t_l2.scene_pos()), "L2"))
                sources.append((pt_key(c.t_l3.scene_pos()), "L3"))
            elif isinstance(c, PowerSupply3PN):
                sources.append((pt_key(c.t_l1.scene_pos()), "L1"))
                sources.append((pt_key(c.t_l2.scene_pos()), "L2"))
                sources.append((pt_key(c.t_l3.scene_pos()), "L3"))
                sources.append((pt_key(c.t_n.scene_pos()), "N"))
                sources.append((pt_key(c.t_pe.scene_pos()), "PE"))

        node_potentials = defaultdict(set)
        for start_node, pot in sources:
            visited = set()
            queue = [start_node]
            while queue:
                curr = queue.pop(0)
                if curr in visited:
                    continue
                visited.add(curr)
                node_potentials[curr].add(pot)
                for nxt in adj[curr]:
                    if nxt not in visited:
                        queue.append(nxt)

        # Asignar potenciales a bornes y cables
        priority = ("L1", "L2", "L3", "N", "PE")
        for k, pots in node_potentials.items():
            chosen = next((p for p in priority if p in pots), None)
            for t in coord_to_terms.get(k, []):
                t.potential = chosen
            for w in coord_to_wires.get(k, []):
                k1, k2 = pt_key(w.p1), pt_key(w.p2)
                common = node_potentials.get(k1, set()) & node_potentials.get(k2, set())
                if common:
                    w_pot = next((p for p in priority if p in common), None)
                    w.potential = w_pot
                    w.energized = w_pot in ("L1", "L2", "L3", "N")

        # 3. Evaluar bobinas, temporizadores y pilotos luminosos (requieren diferencia de potencial ej. L y N o entre fases)
        active_coils = set()
        active_ton = set()
        active_tof = set()

        for c in comps:
            if isinstance(c, (ContactorCoil, PilotLamp)):
                p1 = c.terminals[0].potential
                p2 = c.terminals[1].potential
                has_diff = (
                    p1 is not None and p2 is not None and p1 != p2
                    and "PE" not in (p1, p2)
                )
                c.energized = has_diff

                if isinstance(c, TimerCoilTON):
                    if c.energized:
                        c.remaining_sec = max(0.0, c.remaining_sec - dt_sec)
                        if c.remaining_sec <= 0.01:
                            active_ton.add(c.label.strip().upper())
                    else:
                        c.remaining_sec = float(c.delay_sec)
                elif isinstance(c, TimerCoilTOF):
                    if c.energized:
                        c.remaining_sec = float(c.delay_sec)
                        active_tof.add(c.label.strip().upper())
                    else:
                        if c.remaining_sec > 0.0:
                            c.remaining_sec = max(0.0, c.remaining_sec - dt_sec)
                            if c.remaining_sec > 0.01:
                                active_tof.add(c.label.strip().upper())
                elif isinstance(c, ContactorCoil):
                    if c.energized:
                        active_coils.add(c.label.strip().upper())

        # 4. Actualizar contactos asociados a bobinas, relés térmicos y temporizadores
        tripped_thermals = {
            c.label.strip().upper() for c in comps
            if isinstance(c, ThermalRelay3P) and c.active_state
        }

        for c in comps:
            lbl = c.label.strip().upper()
            if isinstance(c, (TimerContactTON_NO, TimerContactTON_NC)):
                c.active_state = (lbl in active_ton)
            elif isinstance(c, (TimerContactTOF_NO, TimerContactTOF_NC)):
                c.active_state = (lbl in active_tof)
            elif isinstance(c, (AuxThermalNO, AuxThermalNC)):
                c.active_state = (lbl in tripped_thermals)
            elif isinstance(c, (Contactor3P, AuxContactNO, AuxContactNC)):
                c.active_state = (lbl in active_coils)
            c.update()

        for w in wires:
            w.update()
