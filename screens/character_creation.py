"""
Nihongo Quest - Character Creation Screen
==========================================
A fully interactive 3D character creation screen built with Ursina primitives.
The player can customize skin tone, hair style/color, eye color, outfit color,
and name before embarking on their Japanese-learning adventure.

Layout:
  - Left 60%: 3D character preview rotating on a lit circular platform
  - Right 40%: Scrollable customization panel with all options
  - Top: Bilingual title
  - Bottom: "Start Adventure" and "Back" buttons
"""

from ursina import *
import math

# ---------------------------------------------------------------------------
# Color Palette Constants
# ---------------------------------------------------------------------------

SKIN_TONES = [
    color.rgb(255, 224, 196),   # Very light / porcelain
    color.rgb(245, 214, 186),   # Light
    color.rgb(224, 172, 134),   # Medium-light
    color.rgb(198, 134, 66),    # Medium
    color.rgb(141, 85, 36),     # Medium-dark
    color.rgb(82, 46, 22),      # Dark
]

HAIR_COLORS = {
    "Black":   color.rgb(26, 26, 26),
    "Brown":   color.rgb(74, 47, 27),
    "Blonde":  color.rgb(200, 160, 112),
    "Red":     color.rgb(178, 50, 40),
    "Blue":    color.rgb(50, 80, 168),
    "Pink":    color.rgb(220, 120, 160),
    "White":   color.rgb(235, 235, 235),
    "Purple":  color.rgb(107, 63, 160),
}

EYE_COLORS = {
    "Brown":  color.rgb(80, 50, 20),
    "Blue":   color.rgb(45, 80, 160),
    "Green":  color.rgb(42, 122, 64),
    "Hazel":  color.rgb(148, 116, 52),
    "Gray":   color.rgb(140, 140, 150),
    "Purple": color.rgb(120, 60, 160),
}

OUTFIT_COLORS = {
    "Red":     color.rgb(185, 30, 50),
    "Blue":    color.rgb(40, 70, 160),
    "Green":   color.rgb(40, 120, 60),
    "White":   color.rgb(240, 240, 240),
    "Black":   color.rgb(35, 35, 35),
    "Purple":  color.rgb(100, 40, 140),
    "Orange":  color.rgb(220, 130, 30),
    "Yellow":  color.rgb(220, 200, 40),
}

# Japanese-aesthetic UI accent colors
_GOLD = color.rgb(212, 175, 55)
_CRIMSON = color.rgb(185, 30, 50)
_DARK_BG = color.rgb(20, 15, 30)
_PANEL_BG = color.rgb(30, 25, 45)
_PANEL_BORDER = color.rgb(60, 50, 80)
_TEXT_LIGHT = color.rgb(240, 235, 220)
_TEXT_DIM = color.rgb(180, 170, 155)
_BUTTON_NORMAL = color.rgb(50, 40, 65)
_BUTTON_HOVER = color.rgb(70, 55, 90)
_BUTTON_SELECTED = color.rgb(100, 70, 40)


class CharacterCreation:
    """
    Full 3D character creation screen.

    Usage:
        cc = CharacterCreation()
        cc.show(save_slot=0)
        # ...later...
        data = cc.get_character_data()
        cc.hide()
    """

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------
    def __init__(self):
        # State
        self._save_slot = 0
        self._visible = False
        self._rotation_speed = 20          # degrees per second
        self._platform_angle = 0

        # Customization state
        self._player_name = ""
        self._skin_tone_index = 1
        self._hair_style_index = 0
        self._hair_color_name = "Black"
        self._eye_color_name = "Brown"
        self._outfit_color_name = "Blue"

        # Entity collections for cleanup
        self._entities = []                # all managed entities
        self._character_parts = {}         # named character body parts
        self._ui_elements = []             # 2D UI entities
        self._option_buttons = {}          # category -> list of button entities

        # Build everything hidden; show() makes them visible
        self._build_background()
        self._build_platform()
        self._create_character_model()
        self._build_particle_ring()
        self._build_ui()
        self.hide()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def show(self, save_slot=0):
        """Display the character creation screen for the given save slot."""
        self._save_slot = save_slot
        self._visible = True
        for ent in self._entities:
            if ent and hasattr(ent, 'enabled'):
                ent.enabled = True
        for ent in self._ui_elements:
            if ent and hasattr(ent, 'enabled'):
                ent.enabled = True
        self._update_preview()

    def hide(self):
        """Hide every entity owned by this screen."""
        self._visible = False
        for ent in self._entities:
            if ent and hasattr(ent, 'enabled'):
                ent.enabled = False
        for ent in self._ui_elements:
            if ent and hasattr(ent, 'enabled'):
                ent.enabled = False

    def get_character_data(self):
        """Return a dict containing all current customization choices."""
        hair_styles = ["Short", "Long", "Spiky", "Ponytail", "Bun"]
        return {
            "save_slot":    self._save_slot,
            "name":         self._player_name,
            "skin_tone":    self._skin_tone_index,
            "hair_style":   hair_styles[self._hair_style_index],
            "hair_color":   self._hair_color_name,
            "eye_color":    self._eye_color_name,
            "outfit_color": self._outfit_color_name,
        }

    def update(self):
        """Call once per frame (from the game loop) to rotate the platform."""
        if not self._visible:
            return
        dt = time.dt if hasattr(time, 'dt') else 0
        self._platform_angle += self._rotation_speed * dt
        pivot = self._character_parts.get("_pivot")
        if pivot:
            pivot.rotation_y = self._platform_angle
        # Animate particle ring glow
        ring = self._character_parts.get("_particle_ring")
        if ring:
            t = self._platform_angle * 0.02
            pulse = 0.85 + 0.15 * math.sin(t)
            ring.scale = Vec3(1.8 * pulse, 0.02, 1.8 * pulse)

    # ------------------------------------------------------------------
    # Background
    # ------------------------------------------------------------------
    def _build_background(self):
        """Dark background quad that covers the screen."""
        bg = Entity(
            model='quad',
            color=_DARK_BG,
            scale=(200, 200),
            z=50,
            parent=camera.ui,
        )
        self._entities.append(bg)

    # ------------------------------------------------------------------
    # Platform
    # ------------------------------------------------------------------
    def _build_platform(self):
        """Circular platform with subtle glow for the character to stand on."""
        # Main platform disc
        platform = Entity(
            model='cylinder',
            color=color.rgb(45, 35, 55),
            scale=(2, 0.08, 2),
            position=(0, -1.2, 6),
        )
        self._entities.append(platform)
        self._character_parts["_platform"] = platform

        # Platform rim glow
        rim = Entity(
            model='cylinder',
            color=color.rgb(212, 175, 55),
            scale=(2.08, 0.03, 2.08),
            position=(0, -1.17, 6),
        )
        self._entities.append(rim)

        # Platform inner highlight
        highlight = Entity(
            model='cylinder',
            color=color.rgb(60, 50, 75),
            scale=(1.75, 0.09, 1.75),
            position=(0, -1.19, 6),
        )
        self._entities.append(highlight)

    # ------------------------------------------------------------------
    # Particle Ring (subtle glow around platform)
    # ------------------------------------------------------------------
    def _build_particle_ring(self):
        """A pulsating ring around the platform for visual flair."""
        ring = Entity(
            model='torus',
            color=color.rgba(212, 175, 55, 80),
            scale=(1.8, 0.02, 1.8),
            position=(0, -1.12, 6),
            double_sided=True,
        )
        self._entities.append(ring)
        self._character_parts["_particle_ring"] = ring

        # Floating sparkle dots around platform
        for i in range(8):
            angle = math.radians(i * 45)
            sparkle = Entity(
                model='sphere',
                color=color.rgba(212, 175, 55, 100),
                scale=(0.04, 0.04, 0.04),
                position=(
                    math.cos(angle) * 1.6,
                    -1.0 + math.sin(i * 0.7) * 0.15,
                    6 + math.sin(angle) * 1.6
                ),
            )
            self._entities.append(sparkle)

    # ------------------------------------------------------------------
    # 3D Character Model (Procedural from Ursina Primitives)
    # ------------------------------------------------------------------
    def _create_character_model(self):
        """Build the full 3D character from primitive shapes."""
        # Rotation pivot - the whole character is a child of this so we can
        # spin it in update().
        pivot = Entity(position=(0, 0, 6))
        self._entities.append(pivot)
        self._character_parts["_pivot"] = pivot

        skin = SKIN_TONES[self._skin_tone_index]
        hair_col = HAIR_COLORS[self._hair_color_name]
        eye_col = EYE_COLORS[self._eye_color_name]
        outfit_col = OUTFIT_COLORS[self._outfit_color_name]

        # --- Head ---
        head = Entity(
            parent=pivot,
            model='sphere',
            color=skin,
            scale=(0.42, 0.46, 0.42),
            position=(0, 0.45, 0),
        )
        self._entities.append(head)
        self._character_parts["head"] = head

        # --- Eyes ---
        # Left eye (white)
        eye_l_white = Entity(
            parent=head,
            model='sphere',
            color=color.rgb(245, 245, 245),
            scale=(0.28, 0.22, 0.15),
            position=(-0.3, 0.05, -0.8),
        )
        self._entities.append(eye_l_white)
        self._character_parts["eye_l_white"] = eye_l_white

        # Left eye (iris)
        eye_l = Entity(
            parent=head,
            model='sphere',
            color=eye_col,
            scale=(0.16, 0.16, 0.12),
            position=(-0.3, 0.03, -0.88),
        )
        self._entities.append(eye_l)
        self._character_parts["eye_l"] = eye_l

        # Left eye (pupil)
        pupil_l = Entity(
            parent=head,
            model='sphere',
            color=color.rgb(10, 10, 10),
            scale=(0.08, 0.08, 0.10),
            position=(-0.3, 0.03, -0.92),
        )
        self._entities.append(pupil_l)
        self._character_parts["pupil_l"] = pupil_l

        # Right eye (white)
        eye_r_white = Entity(
            parent=head,
            model='sphere',
            color=color.rgb(245, 245, 245),
            scale=(0.28, 0.22, 0.15),
            position=(0.3, 0.05, -0.8),
        )
        self._entities.append(eye_r_white)
        self._character_parts["eye_r_white"] = eye_r_white

        # Right eye (iris)
        eye_r = Entity(
            parent=head,
            model='sphere',
            color=eye_col,
            scale=(0.16, 0.16, 0.12),
            position=(0.3, 0.03, -0.88),
        )
        self._entities.append(eye_r)
        self._character_parts["eye_r"] = eye_r

        # Right eye (pupil)
        pupil_r = Entity(
            parent=head,
            model='sphere',
            color=color.rgb(10, 10, 10),
            scale=(0.08, 0.08, 0.10),
            position=(0.3, 0.03, -0.92),
        )
        self._entities.append(pupil_r)
        self._character_parts["pupil_r"] = pupil_r

        # --- Mouth (small dark ellipse) ---
        mouth = Entity(
            parent=head,
            model='sphere',
            color=color.rgb(140, 60, 60),
            scale=(0.15, 0.06, 0.08),
            position=(0, -0.28, -0.85),
        )
        self._entities.append(mouth)
        self._character_parts["mouth"] = mouth

        # --- Body (Torso) ---
        body = Entity(
            parent=pivot,
            model='cube',
            color=outfit_col,
            scale=(0.55, 0.6, 0.3),
            position=(0, -0.15, 0),
        )
        self._entities.append(body)
        self._character_parts["body"] = body

        # Collar / neckline accent
        collar = Entity(
            parent=pivot,
            model='cube',
            color=color.rgb(
                min(255, int(outfit_col.r * 255) + 40),
                min(255, int(outfit_col.g * 255) + 40),
                min(255, int(outfit_col.b * 255) + 40),
            ),
            scale=(0.48, 0.08, 0.32),
            position=(0, 0.15, 0),
        )
        self._entities.append(collar)
        self._character_parts["collar"] = collar

        # Belt / waist accent
        belt = Entity(
            parent=pivot,
            model='cube',
            color=color.rgb(40, 30, 25),
            scale=(0.56, 0.06, 0.31),
            position=(0, -0.38, 0),
        )
        self._entities.append(belt)
        self._character_parts["belt"] = belt

        # --- Arms ---
        # Left arm
        arm_l = Entity(
            parent=pivot,
            model='cube',
            color=outfit_col,
            scale=(0.16, 0.5, 0.18),
            position=(-0.36, -0.12, 0),
            rotation_z=5,
        )
        self._entities.append(arm_l)
        self._character_parts["arm_l"] = arm_l

        # Left hand
        hand_l = Entity(
            parent=pivot,
            model='sphere',
            color=skin,
            scale=(0.1, 0.1, 0.1),
            position=(-0.38, -0.4, 0),
        )
        self._entities.append(hand_l)
        self._character_parts["hand_l"] = hand_l

        # Right arm
        arm_r = Entity(
            parent=pivot,
            model='cube',
            color=outfit_col,
            scale=(0.16, 0.5, 0.18),
            position=(0.36, -0.12, 0),
            rotation_z=-5,
        )
        self._entities.append(arm_r)
        self._character_parts["arm_r"] = arm_r

        # Right hand
        hand_r = Entity(
            parent=pivot,
            model='sphere',
            color=skin,
            scale=(0.1, 0.1, 0.1),
            position=(0.38, -0.4, 0),
        )
        self._entities.append(hand_r)
        self._character_parts["hand_r"] = hand_r

        # --- Legs ---
        # Left leg
        leg_l = Entity(
            parent=pivot,
            model='cube',
            color=color.rgb(50, 45, 60),
            scale=(0.2, 0.55, 0.22),
            position=(-0.14, -0.72, 0),
        )
        self._entities.append(leg_l)
        self._character_parts["leg_l"] = leg_l

        # Left shoe
        shoe_l = Entity(
            parent=pivot,
            model='cube',
            color=color.rgb(60, 40, 30),
            scale=(0.22, 0.1, 0.28),
            position=(-0.14, -1.02, -0.02),
        )
        self._entities.append(shoe_l)
        self._character_parts["shoe_l"] = shoe_l

        # Right leg
        leg_r = Entity(
            parent=pivot,
            model='cube',
            color=color.rgb(50, 45, 60),
            scale=(0.2, 0.55, 0.22),
            position=(0.14, -0.72, 0),
        )
        self._entities.append(leg_r)
        self._character_parts["leg_r"] = leg_r

        # Right shoe
        shoe_r = Entity(
            parent=pivot,
            model='cube',
            color=color.rgb(60, 40, 30),
            scale=(0.22, 0.1, 0.28),
            position=(0.14, -1.02, -0.02),
        )
        self._entities.append(shoe_r)
        self._character_parts["shoe_r"] = shoe_r

        # --- Hair (default to style 0 = Short) ---
        self._build_hair(pivot, hair_col)

    # ------------------------------------------------------------------
    # Hair Styles
    # ------------------------------------------------------------------
    def _clear_hair(self):
        """Remove existing hair entities."""
        for key in list(self._character_parts.keys()):
            if key.startswith("hair_"):
                ent = self._character_parts.pop(key)
                if ent:
                    self._entities.remove(ent) if ent in self._entities else None
                    destroy(ent)

    def _build_hair(self, pivot, hair_col):
        """Build hair entities for the currently selected style index."""
        self._clear_hair()
        head = self._character_parts.get("head")
        if not head:
            return

        style = self._hair_style_index

        if style == 0:
            # --- Short: small flattened sphere on top of head ---
            h = Entity(
                parent=pivot,
                model='sphere',
                color=hair_col,
                scale=(0.46, 0.2, 0.46),
                position=(0, 0.72, 0),
            )
            self._entities.append(h)
            self._character_parts["hair_top"] = h

            # Side coverage
            h_back = Entity(
                parent=pivot,
                model='sphere',
                color=hair_col,
                scale=(0.44, 0.35, 0.35),
                position=(0, 0.55, 0.08),
            )
            self._entities.append(h_back)
            self._character_parts["hair_back"] = h_back

        elif style == 1:
            # --- Long: elongated cube behind head ---
            h_top = Entity(
                parent=pivot,
                model='sphere',
                color=hair_col,
                scale=(0.46, 0.22, 0.46),
                position=(0, 0.72, 0),
            )
            self._entities.append(h_top)
            self._character_parts["hair_top"] = h_top

            h_long = Entity(
                parent=pivot,
                model='cube',
                color=hair_col,
                scale=(0.42, 0.75, 0.18),
                position=(0, 0.2, 0.2),
            )
            self._entities.append(h_long)
            self._character_parts["hair_long"] = h_long

            # Hair tips (tapered bottom)
            h_tips = Entity(
                parent=pivot,
                model='sphere',
                color=hair_col,
                scale=(0.38, 0.15, 0.16),
                position=(0, -0.18, 0.2),
            )
            self._entities.append(h_tips)
            self._character_parts["hair_tips"] = h_tips

        elif style == 2:
            # --- Spiky: cone on top ---
            h_spike_main = Entity(
                parent=pivot,
                model='cone',
                color=hair_col,
                scale=(0.3, 0.45, 0.3),
                position=(0, 0.88, 0),
            )
            self._entities.append(h_spike_main)
            self._character_parts["hair_spike_main"] = h_spike_main

            # Additional side spikes
            h_spike_l = Entity(
                parent=pivot,
                model='cone',
                color=hair_col,
                scale=(0.15, 0.3, 0.15),
                position=(-0.2, 0.75, 0),
                rotation_z=-25,
            )
            self._entities.append(h_spike_l)
            self._character_parts["hair_spike_l"] = h_spike_l

            h_spike_r = Entity(
                parent=pivot,
                model='cone',
                color=hair_col,
                scale=(0.15, 0.3, 0.15),
                position=(0.2, 0.75, 0),
                rotation_z=25,
            )
            self._entities.append(h_spike_r)
            self._character_parts["hair_spike_r"] = h_spike_r

            # Base coverage
            h_base = Entity(
                parent=pivot,
                model='sphere',
                color=hair_col,
                scale=(0.44, 0.2, 0.44),
                position=(0, 0.68, 0),
            )
            self._entities.append(h_base)
            self._character_parts["hair_base"] = h_base

        elif style == 3:
            # --- Ponytail: sphere on head + small cylinder behind ---
            h_top = Entity(
                parent=pivot,
                model='sphere',
                color=hair_col,
                scale=(0.46, 0.22, 0.46),
                position=(0, 0.72, 0),
            )
            self._entities.append(h_top)
            self._character_parts["hair_top"] = h_top

            # Ponytail cylinder
            h_tail = Entity(
                parent=pivot,
                model='cube',
                color=hair_col,
                scale=(0.14, 0.5, 0.14),
                position=(0, 0.35, 0.28),
                rotation_x=-15,
            )
            self._entities.append(h_tail)
            self._character_parts["hair_tail"] = h_tail

            # Ponytail bulb at end
            h_tail_end = Entity(
                parent=pivot,
                model='sphere',
                color=hair_col,
                scale=(0.12, 0.12, 0.12),
                position=(0, 0.08, 0.32),
            )
            self._entities.append(h_tail_end)
            self._character_parts["hair_tail_end"] = h_tail_end

            # Hair tie
            h_tie = Entity(
                parent=pivot,
                model='sphere',
                color=_CRIMSON,
                scale=(0.06, 0.06, 0.06),
                position=(0, 0.58, 0.25),
            )
            self._entities.append(h_tie)
            self._character_parts["hair_tie"] = h_tie

        elif style == 4:
            # --- Bun: small sphere on top ---
            h_base = Entity(
                parent=pivot,
                model='sphere',
                color=hair_col,
                scale=(0.46, 0.2, 0.46),
                position=(0, 0.72, 0),
            )
            self._entities.append(h_base)
            self._character_parts["hair_base"] = h_base

            h_bun = Entity(
                parent=pivot,
                model='sphere',
                color=hair_col,
                scale=(0.2, 0.2, 0.2),
                position=(0, 0.88, 0),
            )
            self._entities.append(h_bun)
            self._character_parts["hair_bun"] = h_bun

            # Decorative pin
            h_pin = Entity(
                parent=pivot,
                model='cube',
                color=_GOLD,
                scale=(0.02, 0.15, 0.02),
                position=(0.08, 0.92, -0.05),
                rotation_z=20,
            )
            self._entities.append(h_pin)
            self._character_parts["hair_pin"] = h_pin

            # Pin ornament
            h_ornament = Entity(
                parent=pivot,
                model='sphere',
                color=_CRIMSON,
                scale=(0.04, 0.04, 0.04),
                position=(0.1, 1.0, -0.05),
            )
            self._entities.append(h_ornament)
            self._character_parts["hair_ornament"] = h_ornament

    # ------------------------------------------------------------------
    # Preview Updater
    # ------------------------------------------------------------------
    def _update_preview(self):
        """Refresh every part of the 3D character to match current selections."""
        skin = SKIN_TONES[self._skin_tone_index]
        hair_col = HAIR_COLORS[self._hair_color_name]
        eye_col = EYE_COLORS[self._eye_color_name]
        outfit_col = OUTFIT_COLORS[self._outfit_color_name]

        # Skin
        for key in ("head", "hand_l", "hand_r"):
            part = self._character_parts.get(key)
            if part:
                part.color = skin

        # Eyes
        for key in ("eye_l", "eye_r"):
            part = self._character_parts.get(key)
            if part:
                part.color = eye_col

        # Outfit
        for key in ("body", "arm_l", "arm_r"):
            part = self._character_parts.get(key)
            if part:
                part.color = outfit_col

        # Collar (lighter version of outfit)
        collar = self._character_parts.get("collar")
        if collar:
            collar.color = color.rgb(
                min(255, int(outfit_col.r * 255) + 40),
                min(255, int(outfit_col.g * 255) + 40),
                min(255, int(outfit_col.b * 255) + 40),
            )

        # Hair - rebuild for the chosen style/color
        pivot = self._character_parts.get("_pivot")
        if pivot:
            self._build_hair(pivot, hair_col)

        # Update selection highlights in UI
        self._refresh_button_highlights()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------
    def _build_ui(self):
        """Build the entire 2D overlay UI (title, panel, buttons)."""

        # ---- Title Bar ----
        title_bg = Entity(
            parent=camera.ui,
            model='quad',
            color=color.rgba(20, 15, 30, 220),
            scale=(2, 0.12),
            position=(0, 0.44),
        )
        self._ui_elements.append(title_bg)

        title_en = Text(
            text="Create Your Character",
            parent=camera.ui,
            scale=1.8,
            color=_GOLD,
            origin=(0, 0),
            position=(-0.06, 0.45),
        )
        self._ui_elements.append(title_en)

        title_jp = Text(
            text="キャラクター作成",
            parent=camera.ui,
            scale=1.2,
            color=_TEXT_DIM,
            origin=(0, 0),
            position=(-0.06, 0.41),
        )
        self._ui_elements.append(title_jp)

        # Decorative gold lines under title
        line_l = Entity(
            parent=camera.ui,
            model='quad',
            color=_GOLD,
            scale=(0.35, 0.002),
            position=(-0.28, 0.385),
        )
        self._ui_elements.append(line_l)

        line_r = Entity(
            parent=camera.ui,
            model='quad',
            color=_GOLD,
            scale=(0.35, 0.002),
            position=(0.16, 0.385),
        )
        self._ui_elements.append(line_r)

        # ---- Right Panel Background ----
        panel_bg = Entity(
            parent=camera.ui,
            model='quad',
            color=_PANEL_BG,
            scale=(0.52, 0.85),
            position=(0.38, -0.02),
        )
        self._ui_elements.append(panel_bg)

        # Panel border (left edge gold line)
        panel_border = Entity(
            parent=camera.ui,
            model='quad',
            color=_GOLD,
            scale=(0.003, 0.85),
            position=(0.12, -0.02),
        )
        self._ui_elements.append(panel_border)

        # ---- Scrollable Panel Content ----
        # We use a simple y-offset approach since Ursina's built-in scrolling
        # is limited; we pack everything into the available space.
        panel_x = 0.18       # left edge of option area
        panel_w = 0.44       # available width
        y_cursor = 0.32      # starting y (top of panel)

        # ----- Player Name -----
        y_cursor = self._add_section_label("Player Name / 名前", panel_x, y_cursor)
        y_cursor = self._add_name_input(panel_x, y_cursor)

        # ----- Skin Tone -----
        y_cursor -= 0.01
        y_cursor = self._add_section_label("Skin Tone / 肌の色", panel_x, y_cursor)
        y_cursor = self._add_skin_tone_buttons(panel_x, y_cursor)

        # ----- Hair Style -----
        y_cursor -= 0.01
        y_cursor = self._add_section_label("Hair Style / 髪型", panel_x, y_cursor)
        y_cursor = self._add_hair_style_buttons(panel_x, y_cursor)

        # ----- Hair Color -----
        y_cursor -= 0.01
        y_cursor = self._add_section_label("Hair Color / 髪の色", panel_x, y_cursor)
        y_cursor = self._add_color_buttons("hair_color", HAIR_COLORS, panel_x, y_cursor)

        # ----- Eye Color -----
        y_cursor -= 0.01
        y_cursor = self._add_section_label("Eye Color / 目の色", panel_x, y_cursor)
        y_cursor = self._add_color_buttons("eye_color", EYE_COLORS, panel_x, y_cursor)

        # ----- Outfit Color -----
        y_cursor -= 0.01
        y_cursor = self._add_section_label("Outfit / 衣装の色", panel_x, y_cursor)
        y_cursor = self._add_color_buttons("outfit_color", OUTFIT_COLORS, panel_x, y_cursor)

        # ---- Bottom Buttons ----
        self._build_bottom_buttons()

    # ------------------------------------------------------------------
    # UI Helpers
    # ------------------------------------------------------------------
    def _add_section_label(self, text_str, x, y):
        """Add a section header label. Returns new y position."""
        label = Text(
            text=text_str,
            parent=camera.ui,
            scale=0.9,
            color=_GOLD,
            origin=(-0.5, 0),
            position=(x, y),
        )
        self._ui_elements.append(label)
        return y - 0.04

    def _add_name_input(self, x, y):
        """Add a name text input field. Returns new y position."""
        # Background for the input
        input_bg = Entity(
            parent=camera.ui,
            model='quad',
            color=color.rgb(40, 35, 55),
            scale=(0.38, 0.04),
            position=(x + 0.19, y - 0.005),
        )
        self._ui_elements.append(input_bg)

        # Border
        input_border = Entity(
            parent=camera.ui,
            model='quad',
            color=_PANEL_BORDER,
            scale=(0.385, 0.045),
            position=(x + 0.19, y - 0.005),
            z=0.01,
        )
        self._ui_elements.append(input_border)

        # Ursina InputField
        name_field = InputField(
            default_value='Adventurer',
            limit_content_to=20,
            color=color.rgb(40, 35, 55),
            parent=camera.ui,
            scale=(0.6, 0.8),
            position=(x + 0.19, y - 0.005),
            active=True,
        )
        self._ui_elements.append(name_field)
        self._character_parts["_name_field"] = name_field

        # Register on-change callback
        original_input = name_field.input
        screen = self

        def patched_input(key):
            original_input(key)
            screen._player_name = name_field.text[:20] if name_field.text else ""

        name_field.input = patched_input
        self._player_name = "Adventurer"

        return y - 0.06

    def _add_skin_tone_buttons(self, x, y):
        """Add skin tone color swatch buttons. Returns new y position."""
        buttons = []
        btn_size = 0.038
        spacing = 0.048
        for i, tone in enumerate(SKIN_TONES):
            bx = x + 0.025 + i * spacing

            # Selection ring (slightly larger, behind the swatch)
            ring = Entity(
                parent=camera.ui,
                model='quad',
                color=_GOLD if i == self._skin_tone_index else color.rgba(0, 0, 0, 0),
                scale=(btn_size + 0.008, btn_size + 0.008),
                position=(bx, y),
                z=0.001,
            )
            self._ui_elements.append(ring)

            btn = Button(
                parent=camera.ui,
                model='quad',
                color=tone,
                scale=(btn_size, btn_size),
                position=(bx, y),
                highlight_color=tone,
                pressed_color=tone,
            )
            idx = i  # capture

            def make_cb(index):
                def cb():
                    self._skin_tone_index = index
                    self._update_preview()
                return cb

            btn.on_click = make_cb(idx)
            self._ui_elements.append(btn)
            buttons.append((btn, ring, i))

        self._option_buttons["skin_tone"] = buttons
        return y - 0.06

    def _add_hair_style_buttons(self, x, y):
        """Add hair style name buttons. Returns new y position."""
        styles = ["Short", "Long", "Spiky", "Ponytail", "Bun"]
        buttons = []
        btn_w = 0.07
        spacing = 0.075
        row_y = y

        for i, style_name in enumerate(styles):
            # Wrap to second row after 3
            col = i % 3
            row = i // 3
            bx = x + 0.04 + col * spacing
            by = row_y - row * 0.045

            btn = Button(
                parent=camera.ui,
                model='quad',
                color=_BUTTON_SELECTED if i == self._hair_style_index else _BUTTON_NORMAL,
                highlight_color=_BUTTON_HOVER,
                scale=(btn_w, 0.035),
                position=(bx, by),
                text=style_name,
            )
            btn.text_entity.scale = 0.6
            btn.text_entity.color = _TEXT_LIGHT
            idx = i

            def make_cb(index):
                def cb():
                    self._hair_style_index = index
                    self._update_preview()
                return cb

            btn.on_click = make_cb(idx)
            self._ui_elements.append(btn)
            buttons.append((btn, None, i))

        self._option_buttons["hair_style"] = buttons
        # Adjust for rows used
        rows_used = (len(styles) - 1) // 3 + 1
        return row_y - rows_used * 0.045 - 0.015

    def _add_color_buttons(self, category, color_dict, x, y):
        """Add color swatch buttons for a generic color category. Returns new y."""
        buttons = []
        btn_size = 0.032
        spacing = 0.042
        items = list(color_dict.items())
        row_y = y

        for i, (name, col) in enumerate(items):
            col_idx = i % 4
            row = i // 4
            bx = x + 0.025 + col_idx * spacing
            by = row_y - row * 0.044

            # Determine if this is the currently selected one
            is_selected = False
            if category == "hair_color" and name == self._hair_color_name:
                is_selected = True
            elif category == "eye_color" and name == self._eye_color_name:
                is_selected = True
            elif category == "outfit_color" and name == self._outfit_color_name:
                is_selected = True

            # Selection ring
            ring = Entity(
                parent=camera.ui,
                model='quad',
                color=_GOLD if is_selected else color.rgba(0, 0, 0, 0),
                scale=(btn_size + 0.007, btn_size + 0.007),
                position=(bx, by),
                z=0.001,
            )
            self._ui_elements.append(ring)

            btn = Button(
                parent=camera.ui,
                model='quad',
                color=col,
                highlight_color=col,
                pressed_color=col,
                scale=(btn_size, btn_size),
                position=(bx, by),
                text='',
            )

            # Tooltip-style label on hover
            btn.tooltip = Tooltip(name, color=color.rgba(30, 25, 40, 200))

            c_name = name  # capture

            def make_cb(cat, col_name):
                def cb():
                    if cat == "hair_color":
                        self._hair_color_name = col_name
                    elif cat == "eye_color":
                        self._eye_color_name = col_name
                    elif cat == "outfit_color":
                        self._outfit_color_name = col_name
                    self._update_preview()
                return cb

            btn.on_click = make_cb(category, c_name)
            self._ui_elements.append(btn)
            buttons.append((btn, ring, name))

        self._option_buttons[category] = buttons
        rows_used = (len(items) - 1) // 4 + 1
        return row_y - rows_used * 0.044 - 0.01

    def _build_bottom_buttons(self):
        """Build the Start Adventure and Back buttons at the bottom."""
        # --- "Start Adventure" button (gold, prominent) ---
        start_bg_glow = Entity(
            parent=camera.ui,
            model='quad',
            color=color.rgba(212, 175, 55, 60),
            scale=(0.36, 0.065),
            position=(0.12, -0.44),
            z=0.01,
        )
        self._ui_elements.append(start_bg_glow)

        start_btn = Button(
            parent=camera.ui,
            model='quad',
            color=_GOLD,
            highlight_color=color.rgb(235, 200, 80),
            pressed_color=color.rgb(180, 145, 40),
            scale=(0.32, 0.055),
            position=(0.12, -0.44),
            text="Start Adventure   冒険開始",
        )
        start_btn.text_entity.scale = 0.7
        start_btn.text_entity.color = color.rgb(30, 20, 10)
        start_btn.on_click = self._on_start_adventure
        self._ui_elements.append(start_btn)
        self._character_parts["_start_btn"] = start_btn

        # --- "Back" button ---
        back_btn = Button(
            parent=camera.ui,
            model='quad',
            color=color.rgb(60, 50, 70),
            highlight_color=color.rgb(80, 65, 90),
            pressed_color=color.rgb(45, 35, 55),
            scale=(0.12, 0.045),
            position=(-0.14, -0.44),
            text="← Back",
        )
        back_btn.text_entity.scale = 0.65
        back_btn.text_entity.color=_TEXT_LIGHT
        back_btn.on_click = self._on_back
        self._ui_elements.append(back_btn)
        self._character_parts["_back_btn"] = back_btn

    # ------------------------------------------------------------------
    # Button Highlight Refresh
    # ------------------------------------------------------------------
    def _refresh_button_highlights(self):
        """Update visual selection indicators across all option groups."""

        # Skin tone rings
        for btn, ring, idx in self._option_buttons.get("skin_tone", []):
            if ring:
                ring.color = _GOLD if idx == self._skin_tone_index else color.rgba(0, 0, 0, 0)

        # Hair style buttons
        for btn, ring, idx in self._option_buttons.get("hair_style", []):
            btn.color = _BUTTON_SELECTED if idx == self._hair_style_index else _BUTTON_NORMAL

        # Hair color rings
        for btn, ring, name in self._option_buttons.get("hair_color", []):
            if ring:
                ring.color = _GOLD if name == self._hair_color_name else color.rgba(0, 0, 0, 0)

        # Eye color rings
        for btn, ring, name in self._option_buttons.get("eye_color", []):
            if ring:
                ring.color = _GOLD if name == self._eye_color_name else color.rgba(0, 0, 0, 0)

        # Outfit color rings
        for btn, ring, name in self._option_buttons.get("outfit_color", []):
            if ring:
                ring.color = _GOLD if name == self._outfit_color_name else color.rgba(0, 0, 0, 0)

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------
    def _on_start_adventure(self):
        """Handle Start Adventure click: finalize name, emit character data."""
        # Finalize name from input field
        name_field = self._character_parts.get("_name_field")
        if name_field and hasattr(name_field, 'text') and name_field.text:
            self._player_name = name_field.text[:20]

        if not self._player_name.strip():
            self._player_name = "Adventurer"

        data = self.get_character_data()
        print(f"[CharacterCreation] Starting adventure with: {data}")

        # Fire a custom event that the game manager can listen for.
        # In a full game this triggers saving + scene transition.
        try:
            from ursina import invoke
            invoke(setattr, application, 'character_data', data, delay=0)
        except Exception:
            pass

        # Hide this screen and call the on_start callback if set
        self.hide()

        if hasattr(self, 'on_start') and callable(self.on_start):
            self.on_start()

    def _on_back(self):
        """Handle Back button click: return to previous screen."""
        print("[CharacterCreation] Back button pressed.")
        self.hide()

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------
    def destroy(self):
        """Permanently destroy all entities owned by this screen."""
        for ent in self._ui_elements:
            if ent:
                try:
                    destroy(ent)
                except Exception:
                    pass
        for ent in self._entities:
            if ent:
                try:
                    destroy(ent)
                except Exception:
                    pass
        self._entities.clear()
        self._ui_elements.clear()
        self._character_parts.clear()
        self._option_buttons.clear()
        self._visible = False


# ---------------------------------------------------------------------------
# Standalone Test Harness
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    app = Ursina(
        title='Nihongo Quest - Character Creation',
        borderless=False,
        size=(1280, 720),
        development_mode=False,
    )

    # Dark ambient background
    window.color = color.rgb(15, 10, 25)

    # Position camera to see the character nicely
    camera.position = (0, 0.2, 0)
    camera.rotation = (0, 0, 0)

    # Subtle directional light
    dl = DirectionalLight(
        shadow_map_resolution=(1024, 1024),
        y=3, x=1, z=-2,
    )
    dl.look_at(Vec3(0, 0, 6))

    # Ambient light stand-in (bright sphere far away for fill)
    ambient = PointLight(position=(0, 5, 4), color=color.rgb(180, 170, 200))

    cc = CharacterCreation()
    cc.show(save_slot=0)

    def update():
        cc.update()

    app.run()
