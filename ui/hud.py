"""
Nihongo Quest - In-Game HUD Overlay
=====================================
Top-bar stats, XP bar, monument indicator, pause menu,
and a notification toast system.
"""

from ursina import *
from collections import deque

from ui.components import (
    StyledButton, StyledPanel, TitleText, InfoText,
    ProgressBar, TransitionScreen,
    BG_DARK, ACCENT_RED, ACCENT_GOLD, TEXT_WHITE, PANEL_BG,
    ACCENT_GOLD_DIM, TEXT_GREY, ACCENT_RED_LIGHT, PANEL_BG_LIGHT,
)


# ═══════════════════════════════════════════════════════════════════════════════
#  Notification Toast
# ═══════════════════════════════════════════════════════════════════════════════
class _NotificationToast(Entity):
    """A single notification message that slides in, waits, then fades out."""

    def __init__(self, text, duration=3.0, y_pos=0.3, parent=camera.ui,
                 **kwargs):
        super().__init__(parent=parent, **kwargs)

        self.panel = Entity(
            parent=self,
            model='quad',
            color=color.rgba(20, 12, 28, 220),
            scale=(0.42, 0.05),
            position=(0, y_pos),
            z=-0.3,
        )
        # Gold accent top line
        Entity(
            parent=self.panel, model='quad', color=ACCENT_GOLD,
            scale=(1, 0.04), position=(0, 0.5), z=-0.01,
        )
        self.label = Text(
            text=text,
            parent=self.panel,
            font_size=16,
            color=ACCENT_GOLD,
            origin=(0, 0),
            z=-0.01,
        )

        # Slide-in animation
        self.panel.x = 0.6
        self.panel.animate_x(0, duration=0.35, curve=curve.out_expo)

        # Schedule fade-out and destruction
        invoke(self._fade_out, delay=duration)

    def _fade_out(self):
        self.panel.animate_x(0.6, duration=0.35, curve=curve.in_expo)
        destroy(self, delay=0.4)


# ═══════════════════════════════════════════════════════════════════════════════
#  PauseMenu
# ═══════════════════════════════════════════════════════════════════════════════
class _PauseMenu(Entity):
    """Overlay pause menu with Resume / Save / Settings / Main Menu."""

    def __init__(self, on_resume=None, on_save=None,
                 on_settings=None, on_main_menu=None,
                 parent=camera.ui, **kwargs):
        super().__init__(parent=parent, **kwargs)

        self.on_resume = on_resume
        self.on_save = on_save
        self.on_settings = on_settings
        self.on_main_menu = on_main_menu

        # Dim overlay
        self.overlay = Entity(
            parent=self, model='quad',
            color=color.rgba(0, 0, 0, 160),
            scale=(2, 2), z=0.1,
        )

        # Panel
        self.panel = StyledPanel(
            parent=self,
            scale=(0.38, 0.42),
            panel_color=color.rgba(25, 15, 35, 240),
            z=0,
        )

        # Title
        self.title = Text(
            text='Paused',
            parent=self,
            font_size=30,
            color=ACCENT_GOLD,
            origin=(0, 0),
            position=(0, 0.14),
            z=-0.01,
        )

        # Buttons
        btn_data = [
            ('Resume',            self._click_resume),
            ('Save Game',         self._click_save),
            ('Settings',          self._click_settings),
            ('Return to Menu',    self._click_main_menu),
        ]

        start_y = 0.06
        spacing = 0.065
        for i, (label, cb) in enumerate(btn_data):
            StyledButton(
                text=label,
                parent=self,
                position=(0, start_y - i * spacing),
                scale=(0.28, 0.05),
                font_size=15,
                on_click=cb,
            )

    def _click_resume(self):
        if self.on_resume:
            self.on_resume()
        destroy(self)

    def _click_save(self):
        if self.on_save:
            self.on_save()

    def _click_settings(self):
        if self.on_settings:
            self.on_settings()

    def _click_main_menu(self):
        if self.on_main_menu:
            self.on_main_menu()
        destroy(self)


# ═══════════════════════════════════════════════════════════════════════════════
#  GameHUD
# ═══════════════════════════════════════════════════════════════════════════════
class GameHUD(Entity):
    """
    Persistent in-game heads-up display.

    Shows player name, level, XP bar, current monument, pause button,
    and supports temporary notification toasts.

    Parameters:
        on_save       : callback for pause menu "Save Game"
        on_settings   : callback for pause menu "Settings"
        on_main_menu  : callback for pause menu "Return to Menu"
    """

    def __init__(self, on_save=None, on_settings=None,
                 on_main_menu=None, **kwargs):
        super().__init__(parent=camera.ui, **kwargs)

        self.on_save = on_save
        self.on_settings = on_settings
        self.on_main_menu = on_main_menu
        self._pause_menu = None
        self._notification_queue = deque()
        self._notification_active = False
        self._notification_y_offset = 0

        self._build()

    # ── Build ────────────────────────────────────────────────────────────────
    def _build(self):
        # ── Top-left: Player Name & Level ────────────────────────────────────
        self.tl_panel = Entity(
            parent=self, model='quad',
            color=color.rgba(0, 0, 0, 150),
            scale=(0.3, 0.065),
            position=(-0.35, 0.46),
            origin=(-0.5, 0),
            z=0.1,
        )
        # Gold top accent
        Entity(
            parent=self.tl_panel, model='quad', color=ACCENT_GOLD,
            scale=(1, 0.035), position=(0, 0.5), z=-0.01,
        )

        self.player_name_text = Text(
            text='Player',
            parent=self,
            font_size=16,
            color=TEXT_WHITE,
            origin=(-0.5, 0),
            position=(-0.49, 0.47),
            z=-0.01,
        )
        self.level_text = Text(
            text='Lv. 1',
            parent=self,
            font_size=13,
            color=ACCENT_GOLD_DIM,
            origin=(-0.5, 0),
            position=(-0.49, 0.445),
            z=-0.01,
        )

        # ── Top-right: XP Bar ───────────────────────────────────────────────
        self.tr_panel = Entity(
            parent=self, model='quad',
            color=color.rgba(0, 0, 0, 150),
            scale=(0.34, 0.065),
            position=(0.35, 0.46),
            origin=(0.5, 0),
            z=0.1,
        )
        Entity(
            parent=self.tr_panel, model='quad', color=ACCENT_GOLD,
            scale=(1, 0.035), position=(0, 0.5), z=-0.01,
        )

        self.xp_label = Text(
            text='XP',
            parent=self,
            font_size=13,
            color=TEXT_WHITE,
            origin=(0.5, 0),
            position=(0.48, 0.475),
            z=-0.01,
        )

        self.xp_bar = ProgressBar(
            parent=self,
            position=(0.28, 0.45),
            scale=(0.22, 0.015),
            value=0.0,
            show_text=False,
        )

        self.xp_value_text = Text(
            text='0 / 100',
            parent=self,
            font_size=11,
            color=ACCENT_GOLD_DIM,
            origin=(0.5, 0),
            position=(0.48, 0.44),
            z=-0.01,
        )

        # ── Bottom: Current Monument ────────────────────────────────────────
        self.bot_panel = Entity(
            parent=self, model='quad',
            color=color.rgba(0, 0, 0, 140),
            scale=(0.4, 0.045),
            position=(0, -0.46),
            z=0.1,
        )
        Entity(
            parent=self.bot_panel, model='quad', color=ACCENT_GOLD,
            scale=(1, 0.04), position=(0, -0.5), z=-0.01,
        )

        self.monument_text = Text(
            text='---',
            parent=self,
            font_size=14,
            color=ACCENT_GOLD,
            origin=(0, 0),
            position=(0, -0.46),
            z=-0.01,
        )

        # ── Pause Button (top-right corner) ─────────────────────────────────
        self.pause_btn = Button(
            parent=self,
            text='||',
            scale=(0.04, 0.04),
            position=(0.47, 0.46),
            color=ACCENT_RED,
            highlight_color=ACCENT_RED_LIGHT,
            text_color=ACCENT_GOLD,
            on_click=self._toggle_pause,
            z=-0.01,
        )
        self.pause_btn.text_entity.font_size = 18

    # ── Pause Menu ───────────────────────────────────────────────────────────
    def _toggle_pause(self):
        if self._pause_menu:
            destroy(self._pause_menu)
            self._pause_menu = None
            application.paused = False
            return

        application.paused = True
        self._pause_menu = _PauseMenu(
            on_resume=self._resume,
            on_save=self.on_save,
            on_settings=self.on_settings,
            on_main_menu=self._go_main_menu,
            parent=self,
        )
        self._pause_menu.z = -0.5

    def _resume(self):
        self._pause_menu = None
        application.paused = False

    def _go_main_menu(self):
        self._pause_menu = None
        application.paused = False
        if self.on_main_menu:
            self.on_main_menu()

    # ── Notification System ──────────────────────────────────────────────────
    def show_notification(self, text, duration=3.0):
        """
        Display a temporary notification toast.
        Multiple notifications stack vertically.
        """
        y_pos = 0.32 - self._notification_y_offset * 0.06
        _NotificationToast(
            text=text, duration=duration, y_pos=y_pos, parent=self,
        )
        self._notification_y_offset += 1
        # Reset offset after the toast disappears
        invoke(self._decrement_offset, delay=duration + 0.5)

    def _decrement_offset(self):
        self._notification_y_offset = max(0, self._notification_y_offset - 1)

    # ── Public API ───────────────────────────────────────────────────────────
    def update_stats(self, save_data: dict):
        """
        Refresh all HUD elements from a save-data dictionary.

        Expected keys:
            player_name  : str
            level        : int
            xp           : int
            xp_next      : int
            monument_name: str
        """
        self.player_name_text.text = save_data.get('player_name', 'Player')
        self.level_text.text = f'Lv. {save_data.get("level", 1)}'

        xp = save_data.get('xp', 0)
        xp_next = save_data.get('xp_next', 100)
        self.xp_bar.value = xp / max(xp_next, 1)
        self.xp_value_text.text = f'{xp} / {xp_next}'

        monument = save_data.get('monument_name', '---')
        self.monument_text.text = monument

    def show(self):
        self.enabled = True

    def hide(self):
        self.enabled = False
        if self._pause_menu:
            destroy(self._pause_menu)
            self._pause_menu = None
            application.paused = False


# ═══════════════════════════════════════════════════════════════════════════════
#  Stand-alone test
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    app = Ursina(title='Nihongo Quest - HUD Test', borderless=False)
    window.color = BG_DARK

    hud = GameHUD(
        on_save=lambda: print('[HUD] Save Game'),
        on_settings=lambda: print('[HUD] Settings'),
        on_main_menu=lambda: print('[HUD] Return to Menu'),
    )
    hud.update_stats({
        'player_name': 'Sakura',
        'level': 5,
        'xp': 340,
        'xp_next': 500,
        'monument_name': 'Fushimi Inari Shrine',
    })
    hud.show()

    # Demo notifications
    invoke(lambda: hud.show_notification('Welcome back, Sakura!'), delay=1.0)
    invoke(lambda: hud.show_notification('New character learned: \u3042 !'), delay=3.0)
    invoke(lambda: hud.show_notification('+50 XP'), delay=5.0)

    app.run()


# ═══════════════════════════════════════════════════════════════════════════════
#  Alias for backward-compatible import: `from ui.hud import HUD`
# ═══════════════════════════════════════════════════════════════════════════════
HUD = GameHUD
