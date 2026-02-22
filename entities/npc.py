from ursina import *
import math


# ─────────────────────────────────────────────────────────────
# Preset NPC definitions
# ─────────────────────────────────────────────────────────────
NPC_PRESETS = {
    'sensei': {
        'name': 'Sensei',
        'name_jp': '先生',
        'skin_color': color.rgb(240, 210, 175),
        'hair_color': color.rgb(230, 230, 235),       # White/silver hair
        'hair_style': 'long',
        'eye_color': color.rgb(60, 50, 40),
        'outfit_color': color.rgb(60, 60, 90),         # Traditional dark blue
        'outfit_accent': color.rgb(180, 160, 120),     # Gold sash
        'indicator': '!',
        'indicator_color': color.yellow,
        'dialog': [
            'Welcome to Nihongo Quest, young learner!',
            'I am Sensei. I will guide you on your journey.',
            'Each monument represents a stage of mastery.',
            'Begin at the Hiragana Temple and work your way forward.',
            'Ganbatte kudasai! — Do your best!',
        ],
    },
    'sakura': {
        'name': 'Sakura',
        'name_jp': 'さくら',
        'skin_color': color.rgb(255, 225, 200),
        'hair_color': color.rgb(230, 140, 170),        # Pink hair
        'hair_style': 'ponytail',
        'eye_color': color.rgb(100, 60, 120),
        'outfit_color': color.rgb(240, 160, 180),      # Pink outfit
        'outfit_accent': color.rgb(255, 255, 255),     # White accent
        'indicator': '?',
        'indicator_color': color.rgb(255, 180, 200),
        'dialog': [
            'Hi there! I\'m Sakura!',
            'Need help? I know lots of tips and tricks.',
            'Did you know? Practicing every day is the best strategy!',
            'Ganbare! — You can do it!',
        ],
    },
}


class NPC(Entity):
    """
    Non-player character entity for tutorials and guidance.
    Built from the same primitive style as PlayerCharacter but with
    distinct colors, a floating name tag, and speech bubble indicator.
    """

    def __init__(self, preset=None, npc_data=None, position=(0, 0, 0),
                 on_click_callback=None, **kwargs):
        super().__init__(position=position, **kwargs)

        # Load from preset or custom data
        if preset and preset in NPC_PRESETS:
            data = NPC_PRESETS[preset].copy()
        elif npc_data:
            data = npc_data.copy()
        else:
            data = NPC_PRESETS['sensei'].copy()

        self._data = data
        self._npc_name = data.get('name', 'NPC')
        self._npc_name_jp = data.get('name_jp', '')
        self._dialog_lines = data.get('dialog', [])
        self._on_click_callback = on_click_callback

        # Visual parts
        self._parts = {}
        self._name_tag = None
        self._indicator = None
        self._indicator_text = None

        # Animation state
        self._anim_time = 0.0
        self._bob_speed = 2.5
        self._bob_height = 0.02
        self._indicator_bob_speed = 3.0

        # Build
        self._build_body()
        self._build_name_tag()
        self._build_indicator()
        self._build_collider()

    # ─────────────────────────────────────────────
    # Body construction (same structure as player)
    # ─────────────────────────────────────────────

    def _build_body(self):
        """Construct the NPC body from primitives."""
        data = self._data
        skin = data.get('skin_color', color.rgb(240, 210, 175))
        hair_col = data.get('hair_color', color.rgb(230, 230, 235))
        hair_style = data.get('hair_style', 'short')
        eye_col = data.get('eye_color', color.rgb(60, 50, 40))
        outfit_col = data.get('outfit_color', color.rgb(60, 60, 90))
        accent_col = data.get('outfit_accent', color.rgb(180, 160, 120))

        # Body (torso)
        self._parts['body'] = Entity(
            parent=self,
            model='cube',
            color=outfit_col,
            scale=(0.6, 0.7, 0.35),
            position=(0, 0.7, 0),
        )

        # Belt / sash
        self._parts['belt'] = Entity(
            parent=self,
            model='cube',
            color=accent_col,
            scale=(0.62, 0.1, 0.36),
            position=(0, 0.45, 0),
        )

        # Head
        self._parts['head'] = Entity(
            parent=self,
            model='sphere',
            color=skin,
            scale=(0.45, 0.45, 0.45),
            position=(0, 1.35, 0),
        )

        # Eyes
        self._parts['eye_white_left'] = Entity(
            parent=self._parts['head'],
            model='sphere',
            color=color.white,
            scale=(0.2, 0.2, 0.06),
            position=(-0.2, 0.05, 0.42),
        )
        self._parts['eye_white_right'] = Entity(
            parent=self._parts['head'],
            model='sphere',
            color=color.white,
            scale=(0.2, 0.2, 0.06),
            position=(0.2, 0.05, 0.42),
        )
        self._parts['eye_left'] = Entity(
            parent=self._parts['head'],
            model='sphere',
            color=eye_col,
            scale=(0.15, 0.15, 0.08),
            position=(-0.2, 0.05, 0.45),
        )
        self._parts['eye_right'] = Entity(
            parent=self._parts['head'],
            model='sphere',
            color=eye_col,
            scale=(0.15, 0.15, 0.08),
            position=(0.2, 0.05, 0.45),
        )

        # Hair
        self._build_hair(hair_col, hair_style)

        # Arms
        self._parts['arm_left'] = Entity(
            parent=self,
            model='cube',
            color=outfit_col,
            scale=(0.18, 0.55, 0.18),
            position=(-0.4, 0.72, 0),
            origin_y=0.5,
        )
        self._parts['hand_left'] = Entity(
            parent=self._parts['arm_left'],
            model='sphere',
            color=skin,
            scale=(0.6, 0.3, 0.6),
            position=(0, -0.55, 0),
        )
        self._parts['arm_right'] = Entity(
            parent=self,
            model='cube',
            color=outfit_col,
            scale=(0.18, 0.55, 0.18),
            position=(0.4, 0.72, 0),
            origin_y=0.5,
        )
        self._parts['hand_right'] = Entity(
            parent=self._parts['arm_right'],
            model='sphere',
            color=skin,
            scale=(0.6, 0.3, 0.6),
            position=(0, -0.55, 0),
        )

        # Legs
        self._parts['leg_left'] = Entity(
            parent=self,
            model='cube',
            color=color.rgb(40, 40, 55),
            scale=(0.22, 0.5, 0.22),
            position=(-0.15, 0.25, 0),
            origin_y=0.5,
        )
        self._parts['foot_left'] = Entity(
            parent=self._parts['leg_left'],
            model='cube',
            color=color.rgb(80, 50, 30),
            scale=(0.8, 0.25, 1.2),
            position=(0, -0.55, 0.05),
        )
        self._parts['leg_right'] = Entity(
            parent=self,
            model='cube',
            color=color.rgb(40, 40, 55),
            scale=(0.22, 0.5, 0.22),
            position=(0.15, 0.25, 0),
            origin_y=0.5,
        )
        self._parts['foot_right'] = Entity(
            parent=self._parts['leg_right'],
            model='cube',
            color=color.rgb(80, 50, 30),
            scale=(0.8, 0.25, 1.2),
            position=(0, -0.55, 0.05),
        )

    def _build_hair(self, hair_col, hair_style):
        """Build hair based on style."""
        head = self._parts['head']

        if hair_style == 'short':
            self._parts['hair_top'] = Entity(
                parent=head, model='sphere', color=hair_col,
                scale=(1.08, 0.6, 1.05), position=(0, 0.3, -0.05),
            )
        elif hair_style == 'long':
            self._parts['hair_top'] = Entity(
                parent=head, model='sphere', color=hair_col,
                scale=(1.1, 0.6, 1.1), position=(0, 0.3, -0.05),
            )
            self._parts['hair_back'] = Entity(
                parent=head, model='cube', color=hair_col,
                scale=(0.85, 1.6, 0.4), position=(0, -0.3, -0.35),
            )
        elif hair_style == 'spiky':
            self._parts['hair_top'] = Entity(
                parent=head, model='sphere', color=hair_col,
                scale=(1.15, 0.75, 1.1), position=(0, 0.35, -0.05),
            )
            for i, angle in enumerate(range(0, 360, 45)):
                rad = math.radians(angle)
                self._parts[f'hair_spike_{i}'] = Entity(
                    parent=head, model='cube', color=hair_col,
                    scale=(0.12, 0.3, 0.12),
                    position=(math.sin(rad) * 0.35, 0.55, math.cos(rad) * 0.35),
                )
        elif hair_style == 'ponytail':
            self._parts['hair_top'] = Entity(
                parent=head, model='sphere', color=hair_col,
                scale=(1.08, 0.55, 1.05), position=(0, 0.3, -0.05),
            )
            self._parts['hair_tie'] = Entity(
                parent=head, model='sphere', color=color.rgb(200, 50, 50),
                scale=(0.2, 0.2, 0.2), position=(0, 0.15, -0.5),
            )
            self._parts['hair_tail'] = Entity(
                parent=head, model='cube', color=hair_col,
                scale=(0.25, 1.0, 0.2), position=(0, -0.4, -0.5),
            )
        else:
            self._parts['hair_top'] = Entity(
                parent=head, model='sphere', color=hair_col,
                scale=(1.05, 0.4, 1.02), position=(0, 0.35, -0.05),
            )

    # ─────────────────────────────────────────────
    # Name tag and indicator
    # ─────────────────────────────────────────────

    def _build_name_tag(self):
        """Floating name tag above head."""
        display_name = f'{self._npc_name}  {self._npc_name_jp}' if self._npc_name_jp else self._npc_name
        self._name_tag = Text(
            text=display_name,
            parent=self,
            position=(0, 2.0, 0),
            scale=(7, 7),
            color=color.white,
            origin=(0, 0),
            billboard=True,
            background=True,
            background_color=color.rgba(0, 0, 0, 140),
        )

    def _build_indicator(self):
        """Speech bubble indicator (! or ?) above head."""
        indicator_char = self._data.get('indicator', '!')
        indicator_col = self._data.get('indicator_color', color.yellow)

        # Indicator bubble background
        self._indicator = Entity(
            parent=self,
            position=(0, 2.5, 0),
        )

        # Bubble background
        Entity(
            parent=self._indicator,
            model='sphere',
            color=color.rgb(255, 255, 240),
            scale=(0.45, 0.45, 0.15),
            billboard=True,
        )

        # Indicator character
        self._indicator_text = Text(
            text=indicator_char,
            parent=self._indicator,
            position=(0, 0.0, 0.1),
            scale=(12, 12),
            color=indicator_col,
            origin=(0, 0),
            billboard=True,
        )

        # Small triangle "tail" pointing down
        Entity(
            parent=self._indicator,
            model='cube',
            color=color.rgb(255, 255, 240),
            scale=(0.1, 0.15, 0.1),
            position=(0, -0.25, 0),
            rotation=(0, 0, 45),
            billboard=True,
        )

    def _build_collider(self):
        """Clickable collider for the whole NPC."""
        self._collider_entity = Entity(
            parent=self,
            model='cube',
            scale=(1.0, 2.2, 0.8),
            position=(0, 1.0, 0),
            color=color.clear,
            collider='box',
        )
        self._collider_entity.on_click = self._handle_click

    # ─────────────────────────────────────────────
    # Animation
    # ─────────────────────────────────────────────

    def update(self):
        """Idle animation: subtle bobbing + indicator float."""
        self._anim_time += time.dt

        # Body bob
        bob = math.sin(self._anim_time * self._bob_speed) * self._bob_height
        if 'body' in self._parts:
            self._parts['body'].y = 0.7 + bob
        if 'head' in self._parts:
            self._parts['head'].y = 1.35 + bob

        # Indicator float
        if self._indicator:
            indicator_bob = math.sin(self._anim_time * self._indicator_bob_speed) * 0.08
            self._indicator.y = 2.5 + indicator_bob

    # ─────────────────────────────────────────────
    # Interaction
    # ─────────────────────────────────────────────

    def _handle_click(self):
        """Called when the NPC is clicked."""
        if self._on_click_callback:
            self._on_click_callback(self)
        else:
            self.on_click()

    def on_click(self):
        """Default click handler — can be overridden."""
        if self._dialog_lines:
            print(f'[{self._npc_name}]: {self._dialog_lines[0]}')

    def set_dialog(self, dialog_lines):
        """Set or update the NPC's dialog lines."""
        self._dialog_lines = dialog_lines if dialog_lines else []

    @property
    def dialog_lines(self):
        """Get the current dialog lines."""
        return self._dialog_lines

    @property
    def npc_name(self):
        return self._npc_name

    def set_indicator(self, char, col=None):
        """Change the indicator character and optionally its color."""
        if self._indicator_text:
            self._indicator_text.text = char
            if col:
                self._indicator_text.color = col

    # ─────────────────────────────────────────────
    # Visibility
    # ─────────────────────────────────────────────

    def show(self):
        """Show the NPC."""
        self.enabled = True

    def hide(self):
        """Hide the NPC."""
        self.enabled = False

    def destroy_npc(self):
        """Clean up all entities."""
        for part in self._parts.values():
            if part is not None:
                destroy(part)
        self._parts.clear()
        if self._name_tag:
            destroy(self._name_tag)
        if self._indicator:
            destroy(self._indicator)
        if hasattr(self, '_collider_entity') and self._collider_entity:
            destroy(self._collider_entity)
        destroy(self)
