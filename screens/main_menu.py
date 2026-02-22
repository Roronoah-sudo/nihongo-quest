"""
Nihongo Quest - Main Menu Screen
=================================
Beautiful title screen with cherry blossom particle effects,
animated background, and full menu navigation.
"""

from ursina import *
import random
import math
import sys

from ui.components import (
    StyledButton, StyledPanel, TitleText, InfoText,
    TransitionScreen,
    BG_DARK, ACCENT_RED, ACCENT_GOLD, TEXT_WHITE, PANEL_BG,
    SAKURA_PINK, ACCENT_GOLD_DIM, TEXT_GREY,
)

# ── Cherry-blossom pink palette for particles ────────────────────────────────
_PETAL_COLORS = [
    color.rgb(255, 183, 197),   # sakura pink
    color.rgb(255, 200, 210),
    color.rgb(255, 170, 190),
    color.rgb(245, 160, 180),
    color.rgb(255, 220, 230),
]


# ═══════════════════════════════════════════════════════════════════════════════
#  CherryBlossomPetal  (single petal particle)
# ═══════════════════════════════════════════════════════════════════════════════
class CherryBlossomPetal(Entity):
    """A single petal that drifts downward with gentle swaying."""

    def __init__(self, **kwargs):
        super().__init__(
            parent=camera.ui,
            model='quad',
            color=random.choice(_PETAL_COLORS),
            scale=(random.uniform(0.006, 0.012),
                   random.uniform(0.006, 0.012)),
            position=(random.uniform(-0.9, 0.9),
                      random.uniform(0.55, 0.85)),
            rotation_z=random.uniform(0, 360),
            z=0.5,
            **kwargs,
        )
        self.fall_speed = random.uniform(0.02, 0.06)
        self.sway_speed = random.uniform(0.8, 2.0)
        self.sway_amount = random.uniform(0.05, 0.15)
        self.spin_speed = random.uniform(30, 120) * random.choice([-1, 1])
        self._age = random.uniform(0, 6.28)   # phase offset

    def update(self):
        self._age += time.dt * self.sway_speed
        self.y -= self.fall_speed * time.dt
        self.x += math.sin(self._age) * self.sway_amount * time.dt
        self.rotation_z += self.spin_speed * time.dt

        # Reset when off-screen
        if self.y < -0.6:
            self.y = random.uniform(0.55, 0.75)
            self.x = random.uniform(-0.9, 0.9)


# ═══════════════════════════════════════════════════════════════════════════════
#  BackgroundOrb  (slow-rotating ambient 3D-ish element)
# ═══════════════════════════════════════════════════════════════════════════════
class BackgroundOrb(Entity):
    """Slowly rotating, faintly glowing decorative element."""

    def __init__(self, **kwargs):
        super().__init__(
            parent=camera.ui,
            model='circle',
            color=color.rgba(139, 0, 0, 25),
            scale=random.uniform(0.15, 0.4),
            position=(random.uniform(-0.7, 0.7),
                      random.uniform(-0.4, 0.4)),
            z=0.8,
            **kwargs,
        )
        self.orbit_speed = random.uniform(0.1, 0.3) * random.choice([-1, 1])
        self.orbit_radius = random.uniform(0.02, 0.08)
        self._cx, self._cy = self.x, self.y
        self._phase = random.uniform(0, 6.28)

    def update(self):
        self._phase += time.dt * self.orbit_speed
        self.x = self._cx + math.cos(self._phase) * self.orbit_radius
        self.y = self._cy + math.sin(self._phase) * self.orbit_radius


# ═══════════════════════════════════════════════════════════════════════════════
#  MainMenu
# ═══════════════════════════════════════════════════════════════════════════════
class MainMenu(Entity):
    """
    Full main-menu screen for Nihongo Quest.

    Usage:
        menu = MainMenu(
            on_new_game  = lambda: print('new game'),
            on_continue  = lambda: print('continue'),
            on_load_game = lambda: print('load'),
            on_settings  = lambda: print('settings'),
            on_quit      = lambda: application.quit(),
        )
        menu.show()
    """

    VERSION = 'v0.1.0-alpha'

    def __init__(self, on_new_game=None, on_continue=None,
                 on_load_game=None, on_settings=None, on_quit=None,
                 **kwargs):
        super().__init__(parent=camera.ui, **kwargs)

        self.on_new_game  = on_new_game
        self.on_continue  = on_continue
        self.on_load_game = on_load_game
        self.on_settings  = on_settings
        self.on_quit      = on_quit

        self._children_entities = []   # track for show/hide
        self._build()

    # ── Build ────────────────────────────────────────────────────────────────
    def _build(self):
        # Full-screen dark background
        bg = Entity(
            parent=self, model='quad', color=BG_DARK,
            scale=(2, 2), z=1,
        )
        self._children_entities.append(bg)

        # Ambient orbs (rotating background accents)
        for _ in range(6):
            orb = BackgroundOrb()
            orb.parent = self
            self._children_entities.append(orb)

        # Cherry-blossom particles
        self._petals = []
        for _ in range(35):
            p = CherryBlossomPetal()
            p.parent = self
            self._petals.append(p)
            self._children_entities.append(p)

        # ── Title ────────────────────────────────────────────────────────────
        self.title_jp = TitleText(
            text='\u65e5\u672c\u8a9e\u30af\u30a8\u30b9\u30c8',
            position=(0, 0.36),
            font_size=52,
            parent=self,
        )
        self._children_entities.append(self.title_jp)

        self.title_en = InfoText(
            text='Nihongo Quest',
            position=(0, 0.27),
            font_size=22,
            text_color=ACCENT_GOLD_DIM,
            parent=self,
        )
        self._children_entities.append(self.title_en)

        # Decorative divider line below subtitle
        divider = Entity(
            parent=self, model='quad', color=ACCENT_GOLD,
            scale=(0.3, 0.002), position=(0, 0.235), z=-0.01,
        )
        self._children_entities.append(divider)

        # ── Menu Buttons ─────────────────────────────────────────────────────
        btn_data = [
            ('New Game',  self._click_new_game),
            ('Continue',  self._click_continue),
            ('Load Game', self._click_load_game),
            ('Settings',  self._click_settings),
            ('Quit',      self._click_quit),
        ]

        start_y = 0.12
        spacing = 0.08
        self._buttons = []

        for i, (label, callback) in enumerate(btn_data):
            btn = StyledButton(
                text=label,
                position=(0, start_y - i * spacing),
                scale=(0.35, 0.06),
                on_click=callback,
                parent=self,
                font_size=18,
            )
            self._buttons.append(btn)
            self._children_entities.append(btn)

        # ── Version Text (bottom-right corner) ──────────────────────────────
        self.version_text = InfoText(
            text=self.VERSION,
            position=(0.44, -0.46),
            font_size=12,
            text_color=TEXT_GREY,
            parent=self,
            origin=(0.5, 0),
        )
        self._children_entities.append(self.version_text)

        # ── Copyright / flavour text (bottom-left) ──────────────────────────
        self.credit_text = InfoText(
            text='\u00a9 2026 Nihongo Quest Project',
            position=(-0.44, -0.46),
            font_size=12,
            text_color=TEXT_GREY,
            parent=self,
            origin=(-0.5, 0),
        )
        self._children_entities.append(self.credit_text)

        # Transition helper
        self.transition = TransitionScreen(parent=self)
        self.transition.z = -1
        self._children_entities.append(self.transition)

    # ── Button Callbacks ─────────────────────────────────────────────────────
    def _click_new_game(self):
        if self.on_new_game:
            self.transition.fade_out(on_complete=self.on_new_game)

    def _click_continue(self):
        if self.on_continue:
            self.transition.fade_out(on_complete=self.on_continue)

    def _click_load_game(self):
        if self.on_load_game:
            self.transition.fade_out(on_complete=self.on_load_game)

    def _click_settings(self):
        if self.on_settings:
            self.on_settings()

    def _click_quit(self):
        if self.on_quit:
            self.on_quit()
        else:
            application.quit()

    # ── Show / Hide ──────────────────────────────────────────────────────────
    def show(self):
        self.enabled = True
        for child in self._children_entities:
            child.enabled = True
        self.transition.fade_in(duration=0.5)

    def hide(self):
        def _do_hide():
            self.enabled = False
            for child in self._children_entities:
                child.enabled = False

        self.transition.fade_out(duration=0.35, on_complete=_do_hide)


# ═══════════════════════════════════════════════════════════════════════════════
#  Stand-alone test
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    app = Ursina(title='Nihongo Quest - Main Menu', borderless=False)
    window.color = BG_DARK

    menu = MainMenu(
        on_new_game=lambda: print('[MainMenu] New Game clicked'),
        on_continue=lambda: print('[MainMenu] Continue clicked'),
        on_load_game=lambda: print('[MainMenu] Load Game clicked'),
        on_settings=lambda: print('[MainMenu] Settings clicked'),
        on_quit=lambda: application.quit(),
    )
    menu.show()

    app.run()
