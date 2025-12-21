import re
from .profiler import *

class PFSParser:
    def __init__(self, filename):
        self.filename = filename
        self.areas = {}   # {area_name: {subarea_name: [point_ids]}}
        self.points = {}  # {id: {'pos': (x,y,z), 'area': ..., 'subarea': ...}}
        self.graph = {}   # {id: [neighbor_ids]}

    @profile
    def load(self):
        # Regex adaptées au nouveau format
        re_brackets = re.compile(r"\[(.*?)\]")
        re_point = re.compile(r"<Point>\s*{(\d+)}\s*{([\d\.\-\+, ]+)}")
        re_crossroad = re.compile(r"<Crossroad>\s*{(\d+)}")
        re_peripheral = re.compile(r"<Peripheral>\s*{([\d, ]+)}")

        current_area = None
        current_subarea = None
        crossroad_id = None
        in_connections = False

        with open(self.filename, "r", encoding="utf-8", errors="ignore") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line:
                    continue

                # --- Détection des zones principales ---
                if line.startswith("<Area>"):
                    match = re_brackets.search(line)
                    if match:
                        current_area = match.group(1)
                        self.areas.setdefault(current_area, {})
                    continue

                if line.startswith("<SubArea>"):
                    match = re_brackets.search(line)
                    if match:
                        current_subarea = match.group(1)
                        self.areas[current_area].setdefault(current_subarea, [])
                    continue

                # --- Lecture d’un point (nouveau format compact) ---
                match = re_point.match(line)
                if match:
                    pid = int(match.group(1))
                    coords = [float(c.strip()) for c in match.group(2).split(",")]
                    self.points[pid] = {
                        'pos': tuple(coords),
                        'tag': None,
                        'area': current_area,
                        'subarea': current_subarea
                    }
                    self.graph.setdefault(pid, [])
                    self.areas[current_area][current_subarea].append(pid)
                    continue

                # --- Connexions ---
                if line.startswith("<Connections>"):
                    in_connections = True
                    continue
                if in_connections and line == "}":
                    in_connections = False
                    crossroad_id = None
                    continue

                match_cross = re_crossroad.match(line)
                if match_cross:
                    crossroad_id = int(match_cross.group(1))
                    self.graph.setdefault(crossroad_id, [])
                    continue

                match_periph = re_peripheral.match(line)
                if match_periph and crossroad_id is not None:
                    pids = [int(x.strip()) for x in match_periph.group(1).split(",") if x.strip()]
                    for pid in pids:
                        if pid not in self.graph[crossroad_id]:
                            self.graph[crossroad_id].append(pid)
                        self.graph.setdefault(pid, [])
                        if crossroad_id not in self.graph[pid]:
                            self.graph[pid].append(crossroad_id)

        return self.areas, self.points, self.graph