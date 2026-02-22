from ursina import *
import math


# ─────────────────────────────────────────────────────────────
# Monument metadata: id -> (name_en, name_jp, description, base_color)
# ─────────────────────────────────────────────────────────────
MONUMENT_INFO = {
    0:  ('Hiragana Temple',      'ひらがな神殿',   'Master the 46 basic hiragana characters.',            color.rgb(180, 30, 30)),
    1:  ('Katakana Shrine',      'カタカナ神社',   'Learn all katakana for foreign words.',                color.rgb(100, 50, 150)),
    2:  ('Grammar Garden',       '文法の庭',       'Discover basic Japanese sentence patterns.',           color.rgb(40, 160, 60)),
    3:  ('Vocabulary Village',   '語彙の村',       'Build your first 500 words.',                         color.rgb(200, 140, 50)),
    4:  ('Verb Dojo',            '動詞道場',       'Conquer verb conjugations and forms.',                 color.rgb(60, 60, 60)),
    5:  ('Kanji Castle N5',      '漢字城 N5',      'Learn 100 essential N5 kanji.',                        color.rgb(140, 100, 60)),
    6:  ('Listening Lake',       'リスニング湖',   'Train your ear with native audio.',                   color.rgb(40, 120, 200)),
    7:  ('Grammar Grove',        '文法の森',       'Intermediate grammar structures.',                     color.rgb(30, 130, 50)),
    8:  ('Kanji Keep N4/N3',     '漢字砦 N4/N3',   'Master 350+ intermediate kanji.',                     color.rgb(160, 80, 40)),
    9:  ('Reading Realm',        '読書の国',       'Read passages and build comprehension.',               color.rgb(180, 160, 100)),
    10: ('Conversation Court',   '会話広場',       'Practice speaking and conversation.',                  color.rgb(200, 100, 150)),
    11: ('Advanced Academy',     '上級学院',       'Advanced grammar, keigo, and nuance.',                 color.rgb(80, 80, 120)),
    12: ('Immersion Island',     '没入島',         'Full immersion — reading, listening, speaking.',       color.rgb(50, 180, 180)),
}


class Monument(Entity):
    """
    A learning-stage landmark on the overworld.
    Each monument_id produces a distinct 3D structure built from primitives.
    """

    def __init__(self, monument_id, name, position, is_unlocked=False,
                 completion=0.0, on_click_callback=None, **kwargs):
        super().__init__(position=position, **kwargs)

        self.monument_id = monument_id
        self.monument_name = name
        self._is_unlocked = is_unlocked
        self._completion = max(0.0, min(1.0, completion))
        self._on_click_callback = on_click_callback

        # Visual containers
        self._structure_parts = []
        self._decorations = []
        self._lock_icon = None
        self._glow = None
        self._star = None
        self._label = None
        self._completion_bar_bg = None
        self._completion_bar_fill = None
        self._tooltip_panel = None

        # Hover state
        self._base_scale = Vec3(1, 1, 1)
        self._hovered = False

        # Info from metadata
        info = MONUMENT_INFO.get(monument_id, ('Unknown', '???', '', color.gray))
        self._name_en = info[0]
        self._name_jp = info[1]
        self._description = info[2]
        self._base_color = info[3]

        # Build everything
        self._build_structure()
        self._build_label()
        self._build_completion_bar()
        self._apply_visual_state()

    # ─────────────────────────────────────────────
    # Structure builders — one per monument type
    # ─────────────────────────────────────────────

    def _build_structure(self):
        """Dispatch to the correct builder based on monument_id."""
        builders = {
            0:  self._build_torii_gate,
            1:  self._build_shrine,
            2:  self._build_garden_arch,
            3:  self._build_house,
            4:  self._build_dojo,
            5:  self._build_castle_small,
            6:  self._build_listening_lake,
            7:  self._build_tree,
            8:  self._build_castle_large,
            9:  self._build_book,
            10: self._build_pavilion,
            11: self._build_academy,
            12: self._build_island,
        }
        builder = builders.get(self.monument_id, self._build_default)
        builder()

        # Clickable collider covering the whole monument area
        self._click_collider = Entity(
            parent=self,
            model='cube',
            scale=(3, 4, 3),
            position=(0, 2, 0),
            color=color.clear,
            collider='box',
        )
        self._click_collider.on_click = self._handle_click

    # 0 — Hiragana Temple: Red torii gate
    def _build_torii_gate(self):
        c = self._base_color
        # Left pillar
        self._mp(model='cube', color=c, scale=(0.3, 3.0, 0.3), pos=(-1.2, 1.5, 0))
        # Right pillar
        self._mp(model='cube', color=c, scale=(0.3, 3.0, 0.3), pos=(1.2, 1.5, 0))
        # Top beam (kasagi)
        self._mp(model='cube', color=c, scale=(3.4, 0.25, 0.4), pos=(0, 3.2, 0))
        # Second beam (nuki)
        self._mp(model='cube', color=c, scale=(2.8, 0.18, 0.3), pos=(0, 2.6, 0))
        # Pillar caps
        self._mp(model='cube', color=color.rgb(60, 30, 20), scale=(0.4, 0.12, 0.4), pos=(-1.2, 3.05, 0))
        self._mp(model='cube', color=color.rgb(60, 30, 20), scale=(0.4, 0.12, 0.4), pos=(1.2, 3.05, 0))
        # Top curved overhang ends
        self._mp(model='cube', color=c, scale=(0.35, 0.2, 0.35), pos=(-1.7, 3.35, 0),
                 rot=(0, 0, 15))
        self._mp(model='cube', color=c, scale=(0.35, 0.2, 0.35), pos=(1.7, 3.35, 0),
                 rot=(0, 0, -15))
        # Stone base
        self._mp(model='cube', color=color.rgb(150, 150, 140), scale=(3.5, 0.15, 2.0), pos=(0, 0.08, 0))

    # 1 — Katakana Shrine: cube base + pyramid roof
    def _build_shrine(self):
        c = self._base_color
        # Platform
        self._mp(model='cube', color=color.rgb(160, 150, 140), scale=(2.5, 0.2, 2.0), pos=(0, 0.1, 0))
        # Main body
        self._mp(model='cube', color=color.rgb(230, 220, 200), scale=(1.8, 1.5, 1.5), pos=(0, 0.95, 0))
        # Door
        self._mp(model='cube', color=color.rgb(80, 50, 30), scale=(0.5, 0.8, 0.05), pos=(0, 0.6, 0.76))
        # Pyramid roof
        self._mp(model='cube', color=c, scale=(2.2, 0.15, 1.8), pos=(0, 1.8, 0))
        self._mp(model='cube', color=c, scale=(1.8, 0.15, 1.5), pos=(0, 2.1, 0))
        self._mp(model='cube', color=c, scale=(1.3, 0.15, 1.1), pos=(0, 2.4, 0))
        self._mp(model='cube', color=c, scale=(0.7, 0.15, 0.6), pos=(0, 2.7, 0))
        self._mp(model='cube', color=c, scale=(0.25, 0.15, 0.2), pos=(0, 2.95, 0))
        # Roof ornament
        self._mp(model='sphere', color=color.gold, scale=(0.2, 0.3, 0.2), pos=(0, 3.2, 0))

    # 2 — Grammar Garden: arch with greenery
    def _build_garden_arch(self):
        c = self._base_color
        wood = color.rgb(130, 90, 50)
        # Left pillar
        self._mp(model='cube', color=wood, scale=(0.25, 2.8, 0.25), pos=(-1.0, 1.4, 0))
        # Right pillar
        self._mp(model='cube', color=wood, scale=(0.25, 2.8, 0.25), pos=(1.0, 1.4, 0))
        # Arch top (curved approximation)
        for i in range(7):
            t = i / 6.0
            x = lerp(-1.0, 1.0, t)
            y = 2.8 + math.sin(t * math.pi) * 0.8
            self._mp(model='cube', color=wood, scale=(0.35, 0.2, 0.25), pos=(x, y, 0))
        # Greenery — leaf cubes
        for i in range(12):
            t = i / 11.0
            x = lerp(-1.3, 1.3, t)
            y = 2.9 + math.sin(t * math.pi) * 0.9 + random.uniform(-0.1, 0.2)
            z = random.uniform(-0.3, 0.3)
            shade = color.rgb(
                int(30 + random.uniform(0, 40)),
                int(140 + random.uniform(0, 60)),
                int(30 + random.uniform(0, 30)),
            )
            self._mp(model='cube', color=shade,
                     scale=(0.35, 0.35, 0.35), pos=(x, y, z))
        # Flower accents
        for side in [-1, 1]:
            self._mp(model='sphere', color=color.rgb(240, 100, 140),
                     scale=0.2, pos=(side * 0.8, 0.3, 0.3))
            self._mp(model='sphere', color=color.rgb(255, 200, 80),
                     scale=0.15, pos=(side * 1.1, 0.2, -0.2))
        # Stone path
        self._mp(model='cube', color=color.rgb(160, 155, 145),
                 scale=(2.5, 0.08, 1.2), pos=(0, 0.04, 0))

    # 3 — Vocabulary Village: small house
    def _build_house(self):
        c = self._base_color
        # Foundation
        self._mp(model='cube', color=color.rgb(140, 130, 120), scale=(2.2, 0.15, 2.0), pos=(0, 0.08, 0))
        # Walls
        self._mp(model='cube', color=color.rgb(235, 225, 200), scale=(2.0, 1.5, 1.8), pos=(0, 0.9, 0))
        # Door
        self._mp(model='cube', color=color.rgb(100, 65, 35), scale=(0.5, 0.9, 0.05), pos=(0, 0.6, 0.91))
        # Window left
        self._mp(model='cube', color=color.rgb(180, 220, 255), scale=(0.35, 0.35, 0.05), pos=(-0.6, 1.1, 0.91))
        # Window right
        self._mp(model='cube', color=color.rgb(180, 220, 255), scale=(0.35, 0.35, 0.05), pos=(0.6, 1.1, 0.91))
        # Roof — triangle approximation with stacked cubes
        self._mp(model='cube', color=c, scale=(2.4, 0.2, 2.2), pos=(0, 1.75, 0))
        self._mp(model='cube', color=c, scale=(2.0, 0.2, 1.9), pos=(0, 1.95, 0))
        self._mp(model='cube', color=c, scale=(1.5, 0.2, 1.5), pos=(0, 2.15, 0))
        self._mp(model='cube', color=c, scale=(0.9, 0.2, 1.0), pos=(0, 2.35, 0))
        self._mp(model='cube', color=c, scale=(0.3, 0.15, 0.5), pos=(0, 2.5, 0))
        # Chimney
        self._mp(model='cube', color=color.rgb(160, 80, 60), scale=(0.3, 0.6, 0.3), pos=(0.6, 2.5, -0.4))

    # 4 — Verb Dojo: wide building with flat roof
    def _build_dojo(self):
        c = self._base_color
        # Elevated platform
        self._mp(model='cube', color=color.rgb(130, 115, 90), scale=(3.5, 0.3, 2.5), pos=(0, 0.15, 0))
        # Main building
        self._mp(model='cube', color=c, scale=(3.0, 1.8, 2.2), pos=(0, 1.2, 0))
        # Flat roof with overhang
        self._mp(model='cube', color=color.rgb(50, 50, 55), scale=(3.5, 0.15, 2.6), pos=(0, 2.2, 0))
        self._mp(model='cube', color=color.rgb(40, 40, 45), scale=(3.6, 0.08, 2.7), pos=(0, 2.32, 0))
        # Sliding doors (front)
        self._mp(model='cube', color=color.rgb(200, 190, 170), scale=(0.7, 1.2, 0.05), pos=(-0.6, 0.9, 1.11))
        self._mp(model='cube', color=color.rgb(210, 200, 180), scale=(0.7, 1.2, 0.05), pos=(0.6, 0.9, 1.11))
        # Banner (noren)
        self._mp(model='cube', color=color.rgb(220, 220, 240), scale=(1.0, 0.4, 0.04), pos=(0, 1.7, 1.12))
        # Kanji accent on banner
        self._mp(model='cube', color=color.rgb(30, 30, 30), scale=(0.15, 0.25, 0.02), pos=(0, 1.7, 1.15))
        # Steps
        self._mp(model='cube', color=color.rgb(150, 145, 135), scale=(1.2, 0.1, 0.3), pos=(0, 0.35, 1.35))

    # 5 — Kanji Castle N5: stacked cubes getting smaller
    def _build_castle_small(self):
        c = self._base_color
        stone = color.rgb(160, 150, 130)
        # Base wall
        self._mp(model='cube', color=stone, scale=(2.8, 0.8, 2.8), pos=(0, 0.4, 0))
        # Level 1
        self._mp(model='cube', color=color.rgb(240, 235, 220), scale=(2.2, 1.0, 2.2), pos=(0, 1.2, 0))
        self._mp(model='cube', color=c, scale=(2.6, 0.15, 2.6), pos=(0, 1.8, 0))
        # Level 2
        self._mp(model='cube', color=color.rgb(240, 235, 220), scale=(1.6, 0.8, 1.6), pos=(0, 2.2, 0))
        self._mp(model='cube', color=c, scale=(2.0, 0.15, 2.0), pos=(0, 2.7, 0))
        # Level 3 (top)
        self._mp(model='cube', color=color.rgb(240, 235, 220), scale=(1.0, 0.6, 1.0), pos=(0, 3.05, 0))
        self._mp(model='cube', color=c, scale=(1.4, 0.12, 1.4), pos=(0, 3.4, 0))
        # Spire
        self._mp(model='cube', color=color.gold, scale=(0.08, 0.5, 0.08), pos=(0, 3.7, 0))
        self._mp(model='sphere', color=color.gold, scale=0.15, pos=(0, 4.0, 0))

    # 6 — Listening Lake: circular platform with waves
    def _build_listening_lake(self):
        c = self._base_color
        # Water surface (flat sphere)
        self._mp(model='sphere', color=c, scale=(4.0, 0.15, 4.0), pos=(0, 0.08, 0))
        # Inner lighter water
        self._mp(model='sphere', color=color.rgb(80, 160, 240), scale=(3.2, 0.17, 3.2), pos=(0, 0.1, 0))
        # Wave rings
        for i in range(3):
            radius = 1.0 + i * 0.8
            segments = 16
            for j in range(segments):
                angle = (j / segments) * math.pi * 2
                x = math.cos(angle) * radius
                z = math.sin(angle) * radius
                wave_h = 0.12 + math.sin(j * 0.8) * 0.04
                self._mp(model='cube',
                         color=color.rgb(120, 190, 255),
                         scale=(0.25, wave_h, 0.12),
                         pos=(x, 0.18 + i * 0.03, z),
                         rot=(0, math.degrees(angle), 0))
        # Central platform / lily pad
        self._mp(model='sphere', color=color.rgb(60, 140, 60), scale=(0.8, 0.08, 0.8), pos=(0, 0.2, 0))
        # Lotus flower
        self._mp(model='sphere', color=color.rgb(255, 180, 200), scale=(0.3, 0.2, 0.3), pos=(0, 0.35, 0))
        self._mp(model='sphere', color=color.rgb(255, 230, 100), scale=(0.1, 0.15, 0.1), pos=(0, 0.45, 0))

    # 7 — Grammar Grove: tree shape
    def _build_tree(self):
        c = self._base_color
        trunk_col = color.rgb(100, 70, 40)
        # Trunk
        self._mp(model='cube', color=trunk_col, scale=(0.5, 2.5, 0.5), pos=(0, 1.25, 0))
        # Roots
        for angle in [0, 90, 180, 270]:
            rad = math.radians(angle)
            self._mp(model='cube', color=trunk_col, scale=(0.2, 0.15, 0.6),
                     pos=(math.sin(rad) * 0.4, 0.08, math.cos(rad) * 0.4),
                     rot=(0, angle, 0))
        # Canopy spheres (lush)
        self._mp(model='sphere', color=c, scale=(2.0, 1.8, 2.0), pos=(0, 3.0, 0))
        self._mp(model='sphere', color=color.rgb(40, 150, 60), scale=(1.5, 1.3, 1.5), pos=(0.5, 3.3, 0.3))
        self._mp(model='sphere', color=color.rgb(50, 160, 50), scale=(1.3, 1.1, 1.3), pos=(-0.4, 2.8, -0.3))
        self._mp(model='sphere', color=color.rgb(35, 140, 45), scale=(1.0, 0.9, 1.0), pos=(0.2, 3.6, -0.2))
        # Small blossoms
        for i in range(5):
            angle = i * 72
            rad = math.radians(angle)
            self._mp(model='sphere', color=color.rgb(255, 180, 200),
                     scale=0.15,
                     pos=(math.sin(rad) * 0.9, 3.2 + (i % 3) * 0.3, math.cos(rad) * 0.9))

    # 8 — Kanji Keep N4/N3: bigger stacked castle
    def _build_castle_large(self):
        c = self._base_color
        stone = color.rgb(140, 130, 110)
        wall = color.rgb(235, 230, 215)
        # Grand base
        self._mp(model='cube', color=stone, scale=(4.0, 1.0, 4.0), pos=(0, 0.5, 0))
        # Level 1
        self._mp(model='cube', color=wall, scale=(3.2, 1.2, 3.2), pos=(0, 1.6, 0))
        self._mp(model='cube', color=c, scale=(3.8, 0.18, 3.8), pos=(0, 2.3, 0))
        # Level 2
        self._mp(model='cube', color=wall, scale=(2.5, 1.0, 2.5), pos=(0, 2.9, 0))
        self._mp(model='cube', color=c, scale=(3.0, 0.18, 3.0), pos=(0, 3.5, 0))
        # Level 3
        self._mp(model='cube', color=wall, scale=(1.8, 0.9, 1.8), pos=(0, 4.05, 0))
        self._mp(model='cube', color=c, scale=(2.3, 0.15, 2.3), pos=(0, 4.6, 0))
        # Level 4 (top)
        self._mp(model='cube', color=wall, scale=(1.2, 0.7, 1.2), pos=(0, 5.0, 0))
        self._mp(model='cube', color=c, scale=(1.6, 0.12, 1.6), pos=(0, 5.4, 0))
        # Spire
        self._mp(model='cube', color=color.gold, scale=(0.1, 0.8, 0.1), pos=(0, 5.85, 0))
        self._mp(model='sphere', color=color.gold, scale=0.2, pos=(0, 6.3, 0))
        # Corner towers (simplified)
        for sx, sz in [(-1.4, -1.4), (1.4, -1.4), (-1.4, 1.4), (1.4, 1.4)]:
            self._mp(model='cube', color=stone, scale=(0.6, 1.8, 0.6), pos=(sx, 0.9, sz))

    # 9 — Reading Realm: open book shape
    def _build_book(self):
        c = self._base_color
        # Left page
        self._mp(model='cube', color=color.rgb(245, 240, 230),
                 scale=(1.5, 2.0, 0.1), pos=(-0.8, 1.2, 0), rot=(0, 0, 10))
        # Right page
        self._mp(model='cube', color=color.rgb(250, 245, 235),
                 scale=(1.5, 2.0, 0.1), pos=(0.8, 1.2, 0), rot=(0, 0, -10))
        # Spine
        self._mp(model='cube', color=c, scale=(0.2, 2.1, 0.3), pos=(0, 1.2, 0))
        # Cover backs
        self._mp(model='cube', color=c,
                 scale=(1.55, 2.05, 0.08), pos=(-0.82, 1.2, -0.06), rot=(0, 0, 10))
        self._mp(model='cube', color=c,
                 scale=(1.55, 2.05, 0.08), pos=(0.82, 1.2, -0.06), rot=(0, 0, -10))
        # Text lines (decorative)
        for i in range(5):
            y = 0.6 + i * 0.35
            self._mp(model='cube', color=color.rgb(80, 70, 60),
                     scale=(0.9, 0.03, 0.03), pos=(-0.75, y, 0.06), rot=(0, 0, 10))
            self._mp(model='cube', color=color.rgb(80, 70, 60),
                     scale=(0.9, 0.03, 0.03), pos=(0.75, y, 0.06), rot=(0, 0, -10))
        # Base / bookstand
        self._mp(model='cube', color=color.rgb(100, 70, 40), scale=(2.0, 0.15, 1.0), pos=(0, 0.08, 0))

    # 10 — Conversation Court: circular pavilion
    def _build_pavilion(self):
        c = self._base_color
        wood = color.rgb(140, 100, 55)
        # Circular base
        self._mp(model='sphere', color=color.rgb(180, 170, 155), scale=(3.5, 0.2, 3.5), pos=(0, 0.1, 0))
        # Pillars around the circle
        num_pillars = 8
        for i in range(num_pillars):
            angle = (i / num_pillars) * math.pi * 2
            x = math.cos(angle) * 1.4
            z = math.sin(angle) * 1.4
            self._mp(model='cube', color=wood, scale=(0.15, 2.5, 0.15), pos=(x, 1.35, z))
        # Dome / roof — stacked spheres
        self._mp(model='sphere', color=c, scale=(3.2, 0.6, 3.2), pos=(0, 2.7, 0))
        self._mp(model='sphere', color=c, scale=(2.4, 0.5, 2.4), pos=(0, 3.1, 0))
        self._mp(model='sphere', color=c, scale=(1.2, 0.4, 1.2), pos=(0, 3.4, 0))
        # Finial
        self._mp(model='sphere', color=color.gold, scale=0.2, pos=(0, 3.7, 0))
        # Bench inside
        self._mp(model='cube', color=wood, scale=(1.0, 0.15, 0.4), pos=(0, 0.5, 0))
        self._mp(model='cube', color=wood, scale=(0.08, 0.35, 0.08), pos=(-0.45, 0.3, 0))
        self._mp(model='cube', color=wood, scale=(0.08, 0.35, 0.08), pos=(0.45, 0.3, 0))

    # 11 — Advanced Academy: grand building with columns
    def _build_academy(self):
        c = self._base_color
        wall = color.rgb(230, 225, 215)
        # Steps
        self._mp(model='cube', color=color.rgb(180, 175, 165), scale=(4.0, 0.15, 1.5), pos=(0, 0.08, 1.5))
        self._mp(model='cube', color=color.rgb(175, 170, 160), scale=(3.8, 0.15, 1.2), pos=(0, 0.23, 1.3))
        # Main building
        self._mp(model='cube', color=wall, scale=(4.0, 2.5, 3.0), pos=(0, 1.5, 0))
        # Columns (front)
        for i in range(5):
            x = -1.6 + i * 0.8
            self._mp(model='cube', color=color.rgb(210, 205, 195),
                     scale=(0.2, 2.5, 0.2), pos=(x, 1.5, 1.51))
        # Roof / pediment
        self._mp(model='cube', color=c, scale=(4.4, 0.2, 3.4), pos=(0, 2.85, 0))
        # Triangle pediment
        self._mp(model='cube', color=c, scale=(3.5, 0.18, 2.8), pos=(0, 3.1, 0))
        self._mp(model='cube', color=c, scale=(2.5, 0.18, 2.0), pos=(0, 3.3, 0))
        self._mp(model='cube', color=c, scale=(1.5, 0.18, 1.2), pos=(0, 3.5, 0))
        self._mp(model='cube', color=c, scale=(0.5, 0.15, 0.5), pos=(0, 3.7, 0))
        # Door
        self._mp(model='cube', color=color.rgb(80, 60, 40), scale=(0.8, 1.4, 0.05), pos=(0, 0.95, 1.52))
        # Kanji plaque
        self._mp(model='cube', color=color.rgb(200, 180, 140), scale=(1.2, 0.35, 0.04), pos=(0, 2.3, 1.52))

    # 12 — Immersion Island: island with palm trees
    def _build_island(self):
        c = self._base_color
        # Water around
        self._mp(model='sphere', color=color.rgb(40, 100, 200), scale=(5.0, 0.1, 5.0), pos=(0, 0.02, 0))
        # Island land mass
        self._mp(model='sphere', color=color.rgb(200, 180, 120), scale=(3.0, 0.4, 3.0), pos=(0, 0.15, 0))
        # Grass top
        self._mp(model='sphere', color=c, scale=(2.6, 0.2, 2.6), pos=(0, 0.3, 0))
        # Palm tree 1
        self._mp(model='cube', color=color.rgb(130, 90, 40), scale=(0.2, 2.5, 0.2), pos=(0.5, 1.5, 0.3),
                 rot=(5, 0, -8))
        # Palm fronds
        for angle in range(0, 360, 60):
            rad = math.radians(angle)
            self._mp(model='cube', color=color.rgb(30, 150, 40),
                     scale=(0.15, 0.08, 1.0),
                     pos=(0.5 + math.sin(rad) * 0.5, 2.8, 0.3 + math.cos(rad) * 0.5),
                     rot=(20, angle, 0))
        # Palm tree 2 (smaller)
        self._mp(model='cube', color=color.rgb(130, 90, 40), scale=(0.15, 1.8, 0.15), pos=(-0.7, 1.2, -0.5),
                 rot=(-5, 0, 10))
        for angle in range(0, 360, 72):
            rad = math.radians(angle)
            self._mp(model='cube', color=color.rgb(40, 160, 50),
                     scale=(0.12, 0.06, 0.8),
                     pos=(-0.7 + math.sin(rad) * 0.4, 2.2, -0.5 + math.cos(rad) * 0.4),
                     rot=(25, angle, 0))
        # Small hut
        self._mp(model='cube', color=color.rgb(200, 180, 140), scale=(0.8, 0.7, 0.8), pos=(-0.2, 0.7, -0.1))
        self._mp(model='cube', color=color.rgb(160, 100, 50), scale=(1.0, 0.1, 1.0), pos=(-0.2, 1.1, -0.1))
        # Coconuts
        self._mp(model='sphere', color=color.rgb(100, 70, 30), scale=0.12, pos=(0.6, 2.65, 0.2))
        self._mp(model='sphere', color=color.rgb(100, 70, 30), scale=0.1, pos=(0.4, 2.7, 0.4))

    # Default fallback
    def _build_default(self):
        self._mp(model='cube', color=self._base_color, scale=(1.5, 2.0, 1.5), pos=(0, 1.0, 0))

    # ─────────────────────────────────────────────
    # Helper to create a child part and track it
    # ─────────────────────────────────────────────

    def _mp(self, model='cube', color=color.white, scale=1, pos=(0, 0, 0), rot=(0, 0, 0)):
        """Make Part — create a child entity and add it to the structure list."""
        if isinstance(scale, (int, float)):
            scale = (scale, scale, scale)
        e = Entity(
            parent=self,
            model=model,
            color=color,
            scale=scale,
            position=pos,
            rotation=rot,
        )
        self._structure_parts.append(e)
        return e

    # ─────────────────────────────────────────────
    # Label + completion bar
    # ─────────────────────────────────────────────

    def _build_label(self):
        """Floating name label above the monument."""
        label_y = self._get_top_y() + 1.0
        self._label = Text(
            text=self.monument_name,
            parent=self,
            position=(0, label_y, 0),
            scale=(8, 8),
            color=color.white,
            origin=(0, 0),
            billboard=True,
            background=True,
            background_color=color.rgba(0, 0, 0, 150),
        )

    def _build_completion_bar(self):
        """Completion percentage bar below the name label."""
        bar_y = self._get_top_y() + 0.5
        bar_width = 1.5

        # Background bar
        self._completion_bar_bg = Entity(
            parent=self,
            model='cube',
            color=color.rgb(60, 60, 60),
            scale=(bar_width, 0.12, 0.05),
            position=(0, bar_y, 0),
            billboard=True,
        )

        # Fill bar
        fill_width = bar_width * self._completion
        self._completion_bar_fill = Entity(
            parent=self,
            model='cube',
            color=color.rgb(80, 220, 100),
            scale=(max(fill_width, 0.01), 0.1, 0.06),
            position=(-(bar_width - fill_width) / 2, bar_y, 0.01),
            billboard=True,
        )

    def _get_top_y(self):
        """Estimate the top Y position of the monument structure."""
        max_y = 2.0
        for part in self._structure_parts:
            top = part.y + (part.scale_y / 2 if hasattr(part, 'scale_y') else 0.5)
            if top > max_y:
                max_y = top
        return max_y

    # ─────────────────────────────────────────────
    # Visual states
    # ─────────────────────────────────────────────

    def _apply_visual_state(self):
        """Apply locked / unlocked / completed visual states."""
        if not self._is_unlocked:
            self._apply_locked_state()
        elif self._completion >= 1.0:
            self._apply_completed_state()
        else:
            self._apply_unlocked_state()

    def _apply_locked_state(self):
        """Grayscale / dark appearance with lock icon."""
        for part in self._structure_parts:
            original = part.color
            gray = (original.r * 0.3 + original.g * 0.3 + original.b * 0.3) * 0.5
            part.color = color.rgb(
                int(gray * 255),
                int(gray * 255),
                int(gray * 255),
            )

        # Lock icon — small cube with keyhole
        lock_y = self._get_top_y() * 0.5
        self._lock_icon = Entity(parent=self, position=(0, lock_y, 1.5))
        # Lock body
        Entity(
            parent=self._lock_icon,
            model='cube',
            color=color.rgb(100, 100, 100),
            scale=(0.5, 0.5, 0.15),
            position=(0, 0, 0),
            billboard=True,
        )
        # Lock shackle (arch)
        Entity(
            parent=self._lock_icon,
            model='cube',
            color=color.rgb(80, 80, 80),
            scale=(0.35, 0.15, 0.1),
            position=(0, 0.3, 0),
            billboard=True,
        )
        Entity(
            parent=self._lock_icon,
            model='cube',
            color=color.rgb(80, 80, 80),
            scale=(0.1, 0.3, 0.1),
            position=(-0.12, 0.3, 0),
            billboard=True,
        )
        Entity(
            parent=self._lock_icon,
            model='cube',
            color=color.rgb(80, 80, 80),
            scale=(0.1, 0.3, 0.1),
            position=(0.12, 0.3, 0),
            billboard=True,
        )
        # Keyhole
        Entity(
            parent=self._lock_icon,
            model='sphere',
            color=color.rgb(40, 40, 40),
            scale=(0.1, 0.1, 0.08),
            position=(0, 0.05, 0.08),
            billboard=True,
        )
        Entity(
            parent=self._lock_icon,
            model='cube',
            color=color.rgb(40, 40, 40),
            scale=(0.05, 0.12, 0.08),
            position=(0, -0.08, 0.08),
            billboard=True,
        )

        if self._label:
            self._label.color = color.rgb(150, 150, 150)

    def _apply_unlocked_state(self):
        """Full color with subtle glow effect."""
        # Remove lock if present
        if self._lock_icon:
            destroy(self._lock_icon)
            self._lock_icon = None

        # Glow — a soft transparent sphere around the base
        self._glow = Entity(
            parent=self,
            model='sphere',
            color=color.rgba(255, 255, 200, 30),
            scale=(3.5, 0.5, 3.5),
            position=(0, 0.2, 0),
        )

    def _apply_completed_state(self):
        """Full color + golden aura + star on top."""
        # Remove lock if present
        if self._lock_icon:
            destroy(self._lock_icon)
            self._lock_icon = None

        # Golden aura
        self._glow = Entity(
            parent=self,
            model='sphere',
            color=color.rgba(255, 215, 0, 40),
            scale=(4.0, 1.0, 4.0),
            position=(0, 0.5, 0),
        )

        # Star on top
        star_y = self._get_top_y() + 0.3
        self._star = Entity(parent=self, position=(0, star_y, 0))
        # Star made of two overlapping cubes rotated 45 degrees
        Entity(
            parent=self._star,
            model='cube',
            color=color.gold,
            scale=(0.5, 0.5, 0.15),
            rotation=(0, 0, 0),
        )
        Entity(
            parent=self._star,
            model='cube',
            color=color.gold,
            scale=(0.5, 0.5, 0.15),
            rotation=(0, 0, 45),
        )

    # ─────────────────────────────────────────────
    # Interaction
    # ─────────────────────────────────────────────

    def _handle_click(self):
        """Called when the monument's collider is clicked."""
        if self._on_click_callback:
            self._on_click_callback(self.monument_id)

    def on_mouse_enter(self):
        """Hover effect: slight scale up + show tooltip."""
        self._hovered = True
        self.animate_scale(self._base_scale * 1.08, duration=0.2)
        self._show_tooltip()

    def on_mouse_exit(self):
        """Revert hover effect and hide tooltip."""
        self._hovered = False
        self.animate_scale(self._base_scale, duration=0.2)
        self._hide_tooltip()

    def _show_tooltip(self):
        """Display a tooltip panel with monument info."""
        if self._tooltip_panel:
            return

        info = MONUMENT_INFO.get(self.monument_id, ('', '', '', color.gray))
        status = 'Locked' if not self._is_unlocked else f'{int(self._completion * 100)}% Complete'

        tooltip_text = f'{info[0]}\n{info[1]}\n{info[2]}\n{status}'

        self._tooltip_panel = Text(
            text=tooltip_text,
            parent=self,
            position=(0, self._get_top_y() + 2.0, 0),
            scale=(6, 6),
            color=color.white,
            origin=(0, 0),
            billboard=True,
            background=True,
            background_color=color.rgba(20, 20, 40, 200),
        )

    def _hide_tooltip(self):
        """Hide the tooltip panel."""
        if self._tooltip_panel:
            destroy(self._tooltip_panel)
            self._tooltip_panel = None

    # ─────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────

    def set_unlocked(self, unlocked):
        """Update the locked/unlocked state and refresh visuals."""
        self._is_unlocked = unlocked
        self._refresh_visuals()

    def set_completion(self, completion):
        """Update completion (0.0 to 1.0) and refresh visuals."""
        self._completion = max(0.0, min(1.0, completion))
        self._update_completion_bar()
        self._refresh_visuals()

    def _update_completion_bar(self):
        """Update the fill of the completion bar."""
        if self._completion_bar_fill and self._completion_bar_bg:
            bar_width = 1.5
            fill_width = bar_width * self._completion
            self._completion_bar_fill.scale_x = max(fill_width, 0.01)
            self._completion_bar_fill.x = -(bar_width - fill_width) / 2

            # Color gradient: red -> yellow -> green
            if self._completion < 0.5:
                r = 220
                g = int(self._completion * 2 * 220)
            else:
                r = int((1 - self._completion) * 2 * 220)
                g = 220
            self._completion_bar_fill.color = color.rgb(r, g, 60)

    def _refresh_visuals(self):
        """Rebuild visual state after a state change."""
        # Reset structure colors by rebuilding
        for part in self._structure_parts:
            destroy(part)
        self._structure_parts.clear()

        if self._lock_icon:
            destroy(self._lock_icon)
            self._lock_icon = None
        if self._glow:
            destroy(self._glow)
            self._glow = None
        if self._star:
            destroy(self._star)
            self._star = None

        builders = {
            0:  self._build_torii_gate,
            1:  self._build_shrine,
            2:  self._build_garden_arch,
            3:  self._build_house,
            4:  self._build_dojo,
            5:  self._build_castle_small,
            6:  self._build_listening_lake,
            7:  self._build_tree,
            8:  self._build_castle_large,
            9:  self._build_book,
            10: self._build_pavilion,
            11: self._build_academy,
            12: self._build_island,
        }
        builder = builders.get(self.monument_id, self._build_default)
        builder()

        self._apply_visual_state()

    def show(self):
        """Show the monument."""
        self.enabled = True

    def hide(self):
        """Hide the monument."""
        self.enabled = False

    def destroy_monument(self):
        """Clean up all entities."""
        for part in self._structure_parts:
            destroy(part)
        self._structure_parts.clear()
        for dec in self._decorations:
            destroy(dec)
        self._decorations.clear()
        if self._lock_icon:
            destroy(self._lock_icon)
        if self._glow:
            destroy(self._glow)
        if self._star:
            destroy(self._star)
        if self._label:
            destroy(self._label)
        if self._completion_bar_bg:
            destroy(self._completion_bar_bg)
        if self._completion_bar_fill:
            destroy(self._completion_bar_fill)
        if self._tooltip_panel:
            destroy(self._tooltip_panel)
        if self._click_collider:
            destroy(self._click_collider)
        destroy(self)
