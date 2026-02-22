"""
Nihongo Quest - Overworld Screen
==================================
The main 3D overworld where the player navigates between learning monuments.

Features:
  - Green ground plane with a winding path of stepping stones
  - 13 monuments placed along an S-curve path
  - Player character with animated walk-to-monument movement
  - Third-person overhead camera
  - Dawn-gradient sky (pink / orange / purple)
  - Sensei NPC near the first monument
  - Monument info panel + "Enter" button on click
  - Locked monument feedback

Public interface:
    overworld = Overworld()
    overworld.show(save_data)
    overworld.hide()
"""

from ursina import *
import math
import sys
import os

# Resolve imports for both package and standalone execution
from entities.player import PlayerCharacter
from entities.monument import Monument, MONUMENT_INFO
from entities.npc import NPC

# Try to import shared UI components; fall back to local constants
try:
    from ui.components import (
        StyledButton, StyledPanel, TitleText, InfoText,
        TransitionScreen,
        BG_DARK, ACCENT_RED, ACCENT_GOLD, TEXT_WHITE, PANEL_BG,
        ACCENT_GOLD_DIM, TEXT_GREY,
    )
    _HAS_UI_COMPONENTS = True
except ImportError:
    _HAS_UI_COMPONENTS = False
    BG_DARK = color.rgb(20, 12, 28)
    ACCENT_RED = color.rgb(139, 0, 0)
    ACCENT_GOLD = color.rgb(255, 215, 0)
    TEXT_WHITE = color.rgb(240, 240, 240)
    PANEL_BG = color.rgba(0, 0, 0, 180)
    ACCENT_GOLD_DIM = color.rgb(200, 170, 0)
    TEXT_GREY = color.rgb(160, 160, 160)


# ─────────────────────────────────────────────────────────────
# Monument names and default ordering
# ─────────────────────────────────────────────────────────────
MONUMENT_NAMES = [
    'Hiragana Temple',       # 0
    'Katakana Shrine',       # 1
    'Grammar Garden',        # 2
    'Vocabulary Village',    # 3
    'Verb Dojo',             # 4
    'Kanji Castle N5',       # 5
    'Listening Lake',        # 6
    'Grammar Grove',         # 7
    'Kanji Keep N4/N3',      # 8
    'Reading Realm',         # 9
    'Conversation Court',    # 10
    'Advanced Academy',      # 11
    'Immersion Island',      # 12
]

# Lesson select monument_id mapping (keys used in LessonSelectScreen)
MONUMENT_LESSON_KEYS = {
    0: 'hiragana',
    1: 'katakana',
    2: 'grammar_basic',
    3: 'vocabulary',
    4: 'verb_conjugation',
    5: 'kanji_n5',
    6: 'listening',
    7: 'grammar_intermediate',
    8: 'kanji_intermediate',
    9: 'reading',
    10: 'conversation',
    11: 'grammar_advanced',
    12: 'immersion',
}


def _generate_path_positions(count=13, amplitude=25, wavelength=50,
                              spacing=12, start_z=-30):
    """
    Generate monument positions along a gentle S-curve.
    Returns a list of (x, 0, z) tuples.
    """
    positions = []
    for i in range(count):
        z = start_z + i * spacing
        # S-curve: sine wave along the z-axis
        x = math.sin(z / wavelength * math.pi * 2) * amplitude
        positions.append((x, 0, z))
    return positions


# Pre-compute the monument positions for the winding path layout
MONUMENT_POSITIONS = _generate_path_positions()


class Overworld:
    """
    The main overworld screen for Nihongo Quest.

    Usage:
        ow = Overworld()
        ow.show(save_data_dict)
        # ...later...
        ow.hide()
    """

    def __init__(self, on_enter_monument=None, on_back=None):
        """
        Parameters
        ----------
        on_enter_monument : callable(monument_id) or None
            Fired when the player enters a monument.
        on_back : callable() or None
            Fired when the player presses Back / Escape.
        """
        self.on_enter_monument = on_enter_monument
        self.on_back = on_back

        # State
        self._visible = False
        self._save_data = {}
        self._current_monument_id = 0

        # Entity collections
        self._world_entities = []       # ground, sky, path, ambient
        self._monuments = {}            # id -> Monument
        self._player = None
        self._npc_sensei = None
        self._camera_pivot = None
        self._info_panel = None         # currently shown monument panel
        self._info_panel_entities = []

        # Interaction state
        self._selected_monument_id = None
        self._player_walking = False

    # ─────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────

    def show(self, save_data=None):
        """Build and display the overworld using the given save data."""
        self.hide()  # clean up any previous state
        self._visible = True
        self._save_data = save_data or {}
        self._current_monument_id = self._save_data.get('current_monument', 0)

        self._create_world()
        self._place_monuments(self._save_data)
        self._create_player(self._save_data)
        self._create_npcs()
        self._setup_camera()

    def hide(self):
        """Tear down all entities and reset state."""
        self._visible = False
        self._dismiss_info_panel()

        # Destroy monuments
        for mid, mon in self._monuments.items():
            mon.destroy_monument()
        self._monuments.clear()

        # Destroy player
        if self._player:
            self._player.destroy_character()
            self._player = None

        # Destroy NPC
        if self._npc_sensei:
            self._npc_sensei.destroy_npc()
            self._npc_sensei = None

        # Destroy world entities
        for ent in self._world_entities:
            destroy(ent)
        self._world_entities.clear()

        # Reset camera
        if self._camera_pivot:
            destroy(self._camera_pivot)
            self._camera_pivot = None

    def update(self):
        """Called each frame — drives player animation and camera follow."""
        if not self._visible:
            return

        # Player updates handled by its own update() method via Ursina
        # Camera follow
        if self._player and self._camera_pivot:
            target = self._player.position + Vec3(0, 0, 0)
            self._camera_pivot.position = lerp(
                self._camera_pivot.position, target, time.dt * 3
            )

    # ─────────────────────────────────────────────
    # World creation
    # ─────────────────────────────────────────────

    def _create_world(self):
        """Build terrain, sky, path, and ambient lighting."""

        # ── Sky background (dawn gradient) ──
        # Ursina's window.color as base sky
        window.color = color.rgb(60, 30, 70)

        # Large sky sphere for gradient feel
        sky_sphere = Entity(
            model='sphere',
            scale=500,
            color=color.rgb(70, 40, 90),
            double_sided=True,
        )
        self._world_entities.append(sky_sphere)

        # Horizon glow band (large flat disc far away, warm color)
        horizon_glow = Entity(
            model='sphere',
            color=color.rgb(200, 120, 80),
            scale=(600, 30, 600),
            position=(0, -15, 100),
            double_sided=True,
        )
        self._world_entities.append(horizon_glow)

        # Upper sky accent
        sky_top = Entity(
            model='sphere',
            color=color.rgb(40, 20, 60),
            scale=(550, 200, 550),
            position=(0, 80, 0),
            double_sided=True,
        )
        self._world_entities.append(sky_top)

        # ── Ground plane ──
        ground = Entity(
            model='cube',
            color=color.rgb(60, 130, 55),
            scale=(200, 0.5, 300),
            position=(0, -0.25, 60),
            collider='box',
        )
        self._world_entities.append(ground)

        # Subtle grid lines on ground (decorative)
        for i in range(-5, 6):
            line_x = Entity(
                model='cube',
                color=color.rgb(55, 120, 50),
                scale=(200, 0.52, 0.15),
                position=(0, -0.01, 60 + i * 20),
            )
            self._world_entities.append(line_x)

            line_z = Entity(
                model='cube',
                color=color.rgb(55, 120, 50),
                scale=(0.15, 0.52, 300),
                position=(i * 20, -0.01, 60),
            )
            self._world_entities.append(line_z)

        # ── Path (winding stepping stones) ──
        self._create_path()

        # ── Ambient scenery ──
        self._create_scenery()

        # ── Lighting ──
        # Directional light (warm sunlight from dawn angle)
        sun = DirectionalLight(y=10, x=5, z=-5)
        sun.look_at(Vec3(0, 0, 50))
        self._world_entities.append(sun)

        # Ambient fill light
        ambient = AmbientLight(color=color.rgb(80, 70, 90))
        self._world_entities.append(ambient)

    def _create_path(self):
        """
        Create a winding path of small flat stone cubes connecting
        all monument positions.
        """
        positions = MONUMENT_POSITIONS
        path_color_1 = color.rgb(180, 170, 150)
        path_color_2 = color.rgb(160, 150, 135)

        for i in range(len(positions) - 1):
            start = Vec3(*positions[i])
            end = Vec3(*positions[i + 1])
            direction = end - start
            dist = direction.length()
            num_stones = int(dist / 1.5)

            for j in range(num_stones + 1):
                t = j / max(num_stones, 1)
                pos = lerp(start, end, t)

                # Slight random offset for natural feel
                offset_x = math.sin(j * 2.7) * 0.3
                offset_z = math.cos(j * 3.1) * 0.2

                stone = Entity(
                    model='cube',
                    color=path_color_1 if j % 2 == 0 else path_color_2,
                    scale=(1.2 + math.sin(j) * 0.2,
                           0.08,
                           1.0 + math.cos(j) * 0.15),
                    position=(pos.x + offset_x, 0.04, pos.z + offset_z),
                    rotation_y=math.sin(j * 1.3) * 15,
                )
                self._world_entities.append(stone)

    def _create_scenery(self):
        """Add decorative trees, rocks, and lanterns around the path."""
        import random as _rng
        _rng.seed(42)  # Deterministic scenery

        # ── Cherry blossom trees ──
        tree_positions = [
            (-18, 0, -20), (22, 0, 0), (-20, 0, 25),
            (25, 0, 50), (-15, 0, 70), (20, 0, 95),
            (-22, 0, 115), (18, 0, 140), (-25, 0, 10),
            (30, 0, 75), (-28, 0, 55), (28, 0, 30),
        ]

        for tx, ty, tz in tree_positions:
            # Trunk
            trunk_h = _rng.uniform(2.5, 4.0)
            trunk = Entity(
                model='cube',
                color=color.rgb(100 + _rng.randint(-10, 10),
                                70 + _rng.randint(-10, 10),
                                40 + _rng.randint(-5, 5)),
                scale=(0.4, trunk_h, 0.4),
                position=(tx, trunk_h / 2, tz),
            )
            self._world_entities.append(trunk)

            # Canopy — cherry blossom pink or green
            is_sakura = _rng.random() < 0.4
            canopy_col = (
                color.rgb(255, 180 + _rng.randint(-20, 20),
                          200 + _rng.randint(-15, 15))
                if is_sakura else
                color.rgb(40 + _rng.randint(0, 30),
                          130 + _rng.randint(0, 40),
                          40 + _rng.randint(0, 20))
            )
            canopy_size = _rng.uniform(2.0, 3.5)
            canopy = Entity(
                model='sphere',
                color=canopy_col,
                scale=(canopy_size, canopy_size * 0.7, canopy_size),
                position=(tx, trunk_h + canopy_size * 0.3, tz),
            )
            self._world_entities.append(canopy)

        # ── Stone lanterns (ishidourou) ──
        lantern_positions = [
            (-8, 0, -25), (8, 0, 15), (-10, 0, 45),
            (10, 0, 80), (-12, 0, 110), (12, 0, 130),
        ]

        for lx, ly, lz in lantern_positions:
            # Base
            Entity(
                model='cube',
                color=color.rgb(150, 145, 135),
                scale=(0.6, 0.3, 0.6),
                position=(lx, 0.15, lz),
            )
            # Pillar
            pillar = Entity(
                model='cube',
                color=color.rgb(160, 155, 145),
                scale=(0.25, 1.2, 0.25),
                position=(lx, 0.9, lz),
            )
            self._world_entities.append(pillar)
            # Light housing
            housing = Entity(
                model='cube',
                color=color.rgb(170, 165, 150),
                scale=(0.5, 0.4, 0.5),
                position=(lx, 1.7, lz),
            )
            self._world_entities.append(housing)
            # Warm glow inside
            glow = Entity(
                model='sphere',
                color=color.rgb(255, 200, 100),
                scale=(0.25, 0.25, 0.25),
                position=(lx, 1.7, lz),
            )
            self._world_entities.append(glow)
            # Roof
            roof = Entity(
                model='cube',
                color=color.rgb(120, 115, 105),
                scale=(0.65, 0.1, 0.65),
                position=(lx, 1.95, lz),
            )
            self._world_entities.append(roof)

        # ── Small rocks ──
        for _ in range(20):
            rx = _rng.uniform(-35, 35)
            rz = _rng.uniform(-30, 150)
            rock_size = _rng.uniform(0.3, 0.8)
            rock = Entity(
                model='sphere',
                color=color.rgb(130 + _rng.randint(-20, 20),
                                125 + _rng.randint(-15, 15),
                                115 + _rng.randint(-10, 10)),
                scale=(rock_size, rock_size * 0.5, rock_size * 0.8),
                position=(rx, rock_size * 0.15, rz),
            )
            self._world_entities.append(rock)

    # ─────────────────────────────────────────────
    # Monuments
    # ─────────────────────────────────────────────

    def _place_monuments(self, save_data):
        """Create and position all 13 monuments."""
        monuments_data = save_data.get('monuments', {})
        current_monument = save_data.get('current_monument', 0)

        for i in range(13):
            pos = MONUMENT_POSITIONS[i]
            name = MONUMENT_NAMES[i]
            mon_data = monuments_data.get(str(i), monuments_data.get(i, {}))

            # Unlocking logic: monument is unlocked if its index <= current_monument
            # or if explicitly unlocked in save data
            is_unlocked = mon_data.get('unlocked', i <= current_monument)
            completion = mon_data.get('completion', 0.0)

            monument = Monument(
                monument_id=i,
                name=name,
                position=pos,
                is_unlocked=is_unlocked,
                completion=completion,
                on_click_callback=self._on_monument_click,
            )
            self._monuments[i] = monument

    # ─────────────────────────────────────────────
    # Player
    # ─────────────────────────────────────────────

    def _create_player(self, save_data):
        """Create the player character at their current monument."""
        appearance = save_data.get('appearance', None)
        current = save_data.get('current_monument', 0)
        start_pos = MONUMENT_POSITIONS[min(current, len(MONUMENT_POSITIONS) - 1)]

        # Position player slightly in front of monument
        player_pos = (start_pos[0], 0, start_pos[2] - 3)

        self._player = PlayerCharacter(
            appearance_data=appearance,
            position=player_pos,
        )

    # ─────────────────────────────────────────────
    # NPCs
    # ─────────────────────────────────────────────

    def _create_npcs(self):
        """Place Sensei NPC near the first monument."""
        first_pos = MONUMENT_POSITIONS[0]
        sensei_pos = (first_pos[0] + 4, 0, first_pos[2] - 2)

        self._npc_sensei = NPC(
            preset='sensei',
            position=sensei_pos,
            on_click_callback=self._on_npc_click,
        )
        self._npc_sensei.rotation_y = -30

    # ─────────────────────────────────────────────
    # Camera
    # ─────────────────────────────────────────────

    def _setup_camera(self):
        """Third-person overhead angled camera."""
        current = self._save_data.get('current_monument', 0)
        start_pos = MONUMENT_POSITIONS[min(current, len(MONUMENT_POSITIONS) - 1)]

        self._camera_pivot = Entity(position=(start_pos[0], 0, start_pos[2]))
        self._world_entities.append(self._camera_pivot)

        camera.parent = self._camera_pivot
        camera.position = (0, 30, -30)
        camera.rotation = (45, 0, 0)

        # Disable default camera controller
        if hasattr(camera, 'org_parent'):
            pass  # Ursina sometimes sets this
        mouse.locked = False

    # ─────────────────────────────────────────────
    # Monument interaction
    # ─────────────────────────────────────────────

    def _on_monument_click(self, monument_id):
        """Handle click on a monument."""
        monument = self._monuments.get(monument_id)
        if not monument:
            return

        if not monument._is_unlocked:
            # Show locked message
            self._show_locked_message(monument_id)
            return

        self._selected_monument_id = monument_id

        # Walk the player to the monument
        target_pos = MONUMENT_POSITIONS[monument_id]
        walk_target = (target_pos[0], 0, target_pos[2] - 3)

        if self._player:
            self._player.move_to(walk_target, speed=8)
            self._player_walking = True

            # Show the info panel after a brief delay (time to walk)
            dist = (Vec3(*walk_target) - self._player.position).length()
            walk_time = max(dist / 8, 0.3)
            invoke(self._show_monument_panel, monument_id, delay=walk_time)

    def _show_locked_message(self, monument_id):
        """Show a brief 'locked' message for a locked monument."""
        self._dismiss_info_panel()

        prev_name = MONUMENT_NAMES[monument_id - 1] if monument_id > 0 else 'nothing'
        msg_text = f'Complete "{prev_name}" to unlock!'

        # Dim overlay
        overlay = Entity(
            parent=camera.ui,
            model='quad',
            color=color.rgba(0, 0, 0, 120),
            scale=(2, 2),
            z=0.5,
        )
        self._info_panel_entities.append(overlay)

        # Message background
        panel_bg = Entity(
            parent=camera.ui,
            model='quad',
            color=color.rgba(40, 20, 50, 240),
            scale=(0.6, 0.12),
            position=(0, 0),
            z=-0.1,
        )
        self._info_panel_entities.append(panel_bg)

        # Gold border top
        border = Entity(
            parent=camera.ui,
            model='quad',
            color=ACCENT_GOLD,
            scale=(0.6, 0.003),
            position=(0, 0.06),
            z=-0.2,
        )
        self._info_panel_entities.append(border)

        # Lock emoji and text
        lock_text = Text(
            text=msg_text,
            parent=camera.ui,
            origin=(0, 0),
            position=(0, 0),
            scale=1.5,
            color=TEXT_WHITE,
            z=-0.2,
        )
        self._info_panel_entities.append(lock_text)

        # Auto-dismiss after 2 seconds
        invoke(self._dismiss_info_panel, delay=2.5)

    def _show_monument_panel(self, monument_id):
        """Show the info panel for an unlocked monument."""
        self._dismiss_info_panel()
        self._selected_monument_id = monument_id

        monument = self._monuments.get(monument_id)
        if not monument:
            return

        info = MONUMENT_INFO.get(monument_id, ('Unknown', '???', '', color.gray))
        name_en = info[0]
        name_jp = info[1]
        description = info[2]
        completion = monument._completion

        # ── Panel background ──
        overlay = Entity(
            parent=camera.ui,
            model='quad',
            color=color.rgba(0, 0, 0, 100),
            scale=(2, 2),
            z=0.5,
        )
        self._info_panel_entities.append(overlay)
        # Click overlay to dismiss
        overlay_btn = Button(
            parent=camera.ui,
            model='quad',
            color=color.rgba(0, 0, 0, 0),
            scale=(2, 2),
            z=0.49,
            highlight_color=color.rgba(0, 0, 0, 0),
            pressed_color=color.rgba(0, 0, 0, 0),
        )
        overlay_btn.on_click = self._dismiss_info_panel
        self._info_panel_entities.append(overlay_btn)

        panel_bg = Entity(
            parent=camera.ui,
            model='quad',
            color=color.rgba(25, 15, 35, 245),
            scale=(0.55, 0.38),
            position=(0, 0),
            z=-0.1,
        )
        self._info_panel_entities.append(panel_bg)

        # Gold border top
        border_top = Entity(
            parent=camera.ui,
            model='quad',
            color=ACCENT_GOLD,
            scale=(0.55, 0.004),
            position=(0, 0.19),
            z=-0.2,
        )
        self._info_panel_entities.append(border_top)

        # ── Title ──
        title_en = Text(
            text=name_en,
            parent=camera.ui,
            origin=(0, 0),
            position=(0, 0.14),
            scale=2.0,
            color=ACCENT_GOLD,
            z=-0.2,
        )
        self._info_panel_entities.append(title_en)

        title_jp = Text(
            text=name_jp,
            parent=camera.ui,
            origin=(0, 0),
            position=(0, 0.10),
            scale=1.4,
            color=ACCENT_GOLD_DIM,
            z=-0.2,
        )
        self._info_panel_entities.append(title_jp)

        # ── Description ──
        desc = Text(
            text=description,
            parent=camera.ui,
            origin=(0, 0),
            position=(0, 0.04),
            scale=1.2,
            color=TEXT_WHITE,
            z=-0.2,
        )
        self._info_panel_entities.append(desc)

        # ── Completion bar ──
        comp_label = Text(
            text=f'Completion: {int(completion * 100)}%',
            parent=camera.ui,
            origin=(0, 0),
            position=(0, -0.02),
            scale=1.0,
            color=TEXT_GREY,
            z=-0.2,
        )
        self._info_panel_entities.append(comp_label)

        # Bar background
        bar_bg = Entity(
            parent=camera.ui,
            model='quad',
            color=color.rgb(50, 50, 60),
            scale=(0.4, 0.018),
            position=(0, -0.05),
            z=-0.2,
        )
        self._info_panel_entities.append(bar_bg)

        # Bar fill
        fill_w = max(0.4 * completion, 0.002)
        bar_fill_color = color.rgb(80, 220, 100) if completion >= 1.0 else color.rgb(100, 180, 250)
        bar_fill = Entity(
            parent=camera.ui,
            model='quad',
            color=bar_fill_color,
            scale=(fill_w, 0.015),
            position=(-0.2 + fill_w / 2, -0.05),
            z=-0.3,
        )
        self._info_panel_entities.append(bar_fill)

        # ── Buttons ──
        if _HAS_UI_COMPONENTS:
            enter_btn = StyledButton(
                text='Enter',
                position=(0.1, -0.12),
                scale=(0.16, 0.05),
                on_click=lambda: self._enter_monument(monument_id),
                parent=camera.ui,
                font_size=16,
            )
        else:
            enter_btn = Button(
                text='Enter',
                parent=camera.ui,
                position=(0.1, -0.12),
                scale=(0.16, 0.05),
                color=ACCENT_RED,
                highlight_color=color.rgb(180, 30, 30),
                text_color=ACCENT_GOLD,
                z=-0.2,
            )
            enter_btn.on_click = lambda: self._enter_monument(monument_id)
        self._info_panel_entities.append(enter_btn)

        if _HAS_UI_COMPONENTS:
            close_btn = StyledButton(
                text='Close',
                position=(-0.1, -0.12),
                scale=(0.16, 0.05),
                on_click=self._dismiss_info_panel,
                parent=camera.ui,
                font_size=16,
            )
        else:
            close_btn = Button(
                text='Close',
                parent=camera.ui,
                position=(-0.1, -0.12),
                scale=(0.16, 0.05),
                color=color.rgb(60, 50, 70),
                highlight_color=color.rgb(80, 65, 90),
                text_color=TEXT_WHITE,
                z=-0.2,
            )
            close_btn.on_click = self._dismiss_info_panel
        self._info_panel_entities.append(close_btn)

    def _dismiss_info_panel(self):
        """Remove the monument info panel."""
        for ent in self._info_panel_entities:
            if ent:
                destroy(ent)
        self._info_panel_entities.clear()
        self._selected_monument_id = None

    def _enter_monument(self, monument_id):
        """Transition to the lesson selection for this monument."""
        self._dismiss_info_panel()
        self._current_monument_id = monument_id

        if self.on_enter_monument:
            self.on_enter_monument(monument_id)
        else:
            # Default behavior: try to show the lesson select screen
            print(f'[Overworld] Entering monument {monument_id}: '
                  f'{MONUMENT_NAMES[monument_id]}')
            self._launch_lesson_select(monument_id)

    def _launch_lesson_select(self, monument_id):
        """Launch the lesson select screen for the given monument."""
        try:
            from screens.lesson_select import LessonSelectScreen
            lesson_key = MONUMENT_LESSON_KEYS.get(monument_id, 'hiragana')
            screen = LessonSelectScreen()
            screen.show(lesson_key, self._save_data)
        except ImportError:
            print(f'[Overworld] LessonSelectScreen not available. '
                  f'Monument {monument_id} entered.')

    # ─────────────────────────────────────────────
    # NPC interaction
    # ─────────────────────────────────────────────

    def _on_npc_click(self, npc):
        """Handle NPC click — show dialog."""
        self._dismiss_info_panel()
        self._show_npc_dialog(npc)

    def _show_npc_dialog(self, npc):
        """Display NPC dialog box."""
        dialog_lines = npc.dialog_lines
        if not dialog_lines:
            return

        self._dialog_index = 0
        self._dialog_lines = dialog_lines
        self._dialog_npc_name = npc.npc_name

        self._show_dialog_line()

    def _show_dialog_line(self):
        """Show the current dialog line."""
        self._dismiss_info_panel()

        if self._dialog_index >= len(self._dialog_lines):
            return

        line = self._dialog_lines[self._dialog_index]
        speaker = self._dialog_npc_name

        # Dialog background
        dialog_bg = Entity(
            parent=camera.ui,
            model='quad',
            color=color.rgba(20, 12, 30, 235),
            scale=(0.8, 0.14),
            position=(0, -0.35),
            z=-0.1,
        )
        self._info_panel_entities.append(dialog_bg)

        # Gold top border
        border = Entity(
            parent=camera.ui,
            model='quad',
            color=ACCENT_GOLD,
            scale=(0.8, 0.003),
            position=(0, -0.28),
            z=-0.2,
        )
        self._info_panel_entities.append(border)

        # Speaker name
        name_text = Text(
            text=speaker,
            parent=camera.ui,
            origin=(-0.5, 0),
            position=(-0.37, -0.29),
            scale=1.4,
            color=ACCENT_GOLD,
            z=-0.2,
        )
        self._info_panel_entities.append(name_text)

        # Dialog text
        dialog_text = Text(
            text=line,
            parent=camera.ui,
            origin=(-0.5, 0),
            position=(-0.37, -0.34),
            scale=1.2,
            color=TEXT_WHITE,
            z=-0.2,
        )
        dialog_text.wordwrap = 60
        self._info_panel_entities.append(dialog_text)

        # "Next" / "Close" button
        is_last = self._dialog_index >= len(self._dialog_lines) - 1
        btn_text = 'Close' if is_last else 'Next >'

        next_btn = Button(
            text=btn_text,
            parent=camera.ui,
            position=(0.32, -0.39),
            scale=(0.1, 0.04),
            color=ACCENT_RED,
            highlight_color=color.rgb(180, 30, 30),
            text_color=ACCENT_GOLD,
            z=-0.2,
        )
        if is_last:
            next_btn.on_click = self._dismiss_info_panel
        else:
            next_btn.on_click = self._advance_dialog
        self._info_panel_entities.append(next_btn)

    def _advance_dialog(self):
        """Move to the next dialog line."""
        self._dialog_index += 1
        self._show_dialog_line()


# ═══════════════════════════════════════════════════════════════════════════════
#  Standalone test harness
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    app = Ursina(title='Nihongo Quest - Overworld', borderless=False)

    # Mock save data for testing
    test_save_data = {
        'player_name': 'Tanuki',
        'current_monument': 3,
        'appearance': {
            'skin_color': color.rgb(245, 214, 186),
            'hair_color': color.rgb(74, 47, 27),
            'hair_style': 'short',
            'eye_color': color.rgb(80, 50, 20),
            'outfit_color': color.rgb(40, 70, 160),
            'outfit_accent': color.rgb(185, 30, 50),
        },
        'monuments': {
            '0': {'unlocked': True, 'completion': 1.0},
            '1': {'unlocked': True, 'completion': 0.8},
            '2': {'unlocked': True, 'completion': 0.5},
            '3': {'unlocked': True, 'completion': 0.2},
            '4': {'unlocked': False, 'completion': 0.0},
        },
    }

    overworld = Overworld(
        on_enter_monument=lambda mid: print(
            f'[Test] Entering monument {mid}: {MONUMENT_NAMES[mid]}'),
    )
    overworld.show(test_save_data)

    def update():
        overworld.update()

    app.run()
