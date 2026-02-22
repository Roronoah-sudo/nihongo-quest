"""
Nihongo Quest - Settings Screen
=================================
Volume sliders, difficulty, text size, romaji/furigana toggles.
Persists to a JSON file in the user's app-data directory.
"""

from ursina import *
import json
import os
import sys

from ui.components import (
    StyledButton, StyledPanel, TitleText, InfoText, TransitionScreen,
    BG_DARK, ACCENT_RED, ACCENT_GOLD, TEXT_WHITE, PANEL_BG,
    ACCENT_RED_LIGHT, ACCENT_GOLD_DIM, TEXT_GREY, PANEL_BG_LIGHT,
)


# ── Default settings ─────────────────────────────────────────────────────────
DEFAULT_SETTINGS = {
    'master_volume': 0.8,
    'music_volume': 0.7,
    'sfx_volume': 0.9,
    'difficulty': 'Normal',       # Easy / Normal / Hard
    'text_size': 'Medium',        # Small / Medium / Large
    'show_romaji': True,
    'show_furigana': True,
}

_SETTINGS_DIR = os.path.join(
    os.environ.get('APPDATA', os.path.expanduser('~/.config')),
    'NihongoQuest',
)
_SETTINGS_PATH = os.path.join(_SETTINGS_DIR, 'settings.json')


def load_settings() -> dict:
    """Load settings from disk, falling back to defaults."""
    try:
        with open(_SETTINGS_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Merge with defaults so new keys are always present
        merged = {**DEFAULT_SETTINGS, **data}
        return merged
    except (FileNotFoundError, json.JSONDecodeError):
        return dict(DEFAULT_SETTINGS)


def save_settings(settings: dict):
    """Persist settings dict to JSON on disk."""
    os.makedirs(_SETTINGS_DIR, exist_ok=True)
    with open(_SETTINGS_PATH, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2)


# ═══════════════════════════════════════════════════════════════════════════════
#  Helpers: small custom widgets
# ═══════════════════════════════════════════════════════════════════════════════

class _LabeledSlider(Entity):
    """A labelled horizontal slider with a value readout."""

    def __init__(self, label_text, value=0.5, position=(0, 0),
                 parent=camera.ui, on_change=None, **kwargs):
        super().__init__(parent=parent, position=position, **kwargs)

        self._on_change = on_change

        self.label = Text(
            text=label_text,
            parent=self,
            font_size=16,
            color=TEXT_WHITE,
            origin=(-0.5, 0),
            position=(-0.22, 0),
        )

        self.slider = Slider(
            parent=self,
            min=0, max=100, default=int(value * 100),
            step=1,
            dynamic=True,
            position=(0.03, 0),
            scale=(0.8, 0.8),
            color=ACCENT_RED,
            on_value_changed=self._value_changed,
        )
        # Style the knob
        self.slider.knob.color = ACCENT_GOLD
        self.slider.knob.highlight_color = color.rgb(255, 235, 120)

        self.value_text = Text(
            text=f'{int(value * 100)}%',
            parent=self,
            font_size=14,
            color=ACCENT_GOLD_DIM,
            origin=(-0.5, 0),
            position=(0.32, 0),
        )

    def _value_changed(self):
        v = self.slider.value
        self.value_text.text = f'{int(v)}%'
        if self._on_change:
            self._on_change(v / 100.0)

    @property
    def value(self):
        return self.slider.value / 100.0

    @value.setter
    def value(self, v):
        self.slider.value = int(v * 100)
        self.value_text.text = f'{int(v * 100)}%'


class _OptionSelector(Entity):
    """A horizontal selector that cycles through a list of options."""

    def __init__(self, label_text, options, current=None,
                 position=(0, 0), parent=camera.ui, on_change=None,
                 **kwargs):
        super().__init__(parent=parent, position=position, **kwargs)

        self._options = options
        self._index = 0
        self._on_change = on_change

        if current and current in options:
            self._index = options.index(current)

        self.label = Text(
            text=label_text,
            parent=self,
            font_size=16,
            color=TEXT_WHITE,
            origin=(-0.5, 0),
            position=(-0.22, 0),
        )

        # Left arrow
        self.left_btn = Button(
            text='◀',
            parent=self,
            scale=(0.03, 0.035),
            position=(0.06, 0),
            color=ACCENT_RED,
            highlight_color=ACCENT_RED_LIGHT,
            text_color=ACCENT_GOLD,
            on_click=self._prev,
        )

        # Value display
        self.value_text = Text(
            text=self._options[self._index],
            parent=self,
            font_size=16,
            color=ACCENT_GOLD,
            origin=(0, 0),
            position=(0.16, 0),
        )

        # Right arrow
        self.right_btn = Button(
            text='▶',
            parent=self,
            scale=(0.03, 0.035),
            position=(0.26, 0),
            color=ACCENT_RED,
            highlight_color=ACCENT_RED_LIGHT,
            text_color=ACCENT_GOLD,
            on_click=self._next,
        )

    def _prev(self):
        self._index = (self._index - 1) % len(self._options)
        self._update()

    def _next(self):
        self._index = (self._index + 1) % len(self._options)
        self._update()

    def _update(self):
        self.value_text.text = self._options[self._index]
        if self._on_change:
            self._on_change(self.current)

    @property
    def current(self):
        return self._options[self._index]

    @current.setter
    def current(self, value):
        if value in self._options:
            self._index = self._options.index(value)
            self.value_text.text = value


class _Toggle(Entity):
    """A simple on/off toggle button."""

    def __init__(self, label_text, value=True, position=(0, 0),
                 parent=camera.ui, on_change=None, **kwargs):
        super().__init__(parent=parent, position=position, **kwargs)

        self._value = value
        self._on_change = on_change

        self.label = Text(
            text=label_text,
            parent=self,
            font_size=16,
            color=TEXT_WHITE,
            origin=(-0.5, 0),
            position=(-0.22, 0),
        )

        self.toggle_btn = Button(
            parent=self,
            scale=(0.08, 0.035),
            position=(0.14, 0),
            color=ACCENT_RED if not value else color.rgb(0, 120, 60),
            highlight_color=ACCENT_RED_LIGHT if not value else color.rgb(0, 150, 75),
            text='ON' if value else 'OFF',
            text_color=ACCENT_GOLD,
            on_click=self._flip,
        )
        self.toggle_btn.text_entity.font_size = 14

    def _flip(self):
        self._value = not self._value
        self._refresh()
        if self._on_change:
            self._on_change(self._value)

    def _refresh(self):
        if self._value:
            self.toggle_btn.color = color.rgb(0, 120, 60)
            self.toggle_btn.highlight_color = color.rgb(0, 150, 75)
            self.toggle_btn.text = 'ON'
        else:
            self.toggle_btn.color = ACCENT_RED
            self.toggle_btn.highlight_color = ACCENT_RED_LIGHT
            self.toggle_btn.text = 'OFF'

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, v):
        self._value = bool(v)
        self._refresh()


# ═══════════════════════════════════════════════════════════════════════════════
#  SettingsScreen
# ═══════════════════════════════════════════════════════════════════════════════
class SettingsScreen(Entity):
    """
    Full settings screen.

    Parameters:
        on_back : callback()  -- return to the previous screen
    """

    def __init__(self, on_back=None, **kwargs):
        super().__init__(parent=camera.ui, **kwargs)

        self.on_back = on_back
        self.settings = load_settings()

        self._build()

    # ── Build ────────────────────────────────────────────────────────────────
    def _build(self):
        # Background
        self.bg = Entity(
            parent=self, model='quad', color=BG_DARK,
            scale=(2, 2), z=1,
        )

        # Title
        self.title = TitleText(
            text='Settings',
            position=(0, 0.41),
            font_size=36,
            parent=self,
        )

        # Central panel
        self.panel = StyledPanel(
            parent=self,
            position=(0, 0.02),
            scale=(0.65, 0.62),
            panel_color=color.rgba(20, 12, 30, 220),
        )

        # ── Volume Sliders ───────────────────────────────────────────────────
        section_y = 0.27
        heading_audio = InfoText(
            text='--- Audio ---',
            parent=self, position=(0, section_y + 0.02),
            font_size=14, text_color=ACCENT_GOLD_DIM,
        )

        self.master_slider = _LabeledSlider(
            'Master', value=self.settings['master_volume'],
            parent=self, position=(0, section_y - 0.04),
            on_change=lambda v: self._set('master_volume', v),
        )

        self.music_slider = _LabeledSlider(
            'Music', value=self.settings['music_volume'],
            parent=self, position=(0, section_y - 0.1),
            on_change=lambda v: self._set('music_volume', v),
        )

        self.sfx_slider = _LabeledSlider(
            'SFX', value=self.settings['sfx_volume'],
            parent=self, position=(0, section_y - 0.16),
            on_change=lambda v: self._set('sfx_volume', v),
        )

        # ── Difficulty ───────────────────────────────────────────────────────
        section_y2 = 0.04
        heading_gameplay = InfoText(
            text='--- Gameplay ---',
            parent=self, position=(0, section_y2 + 0.02),
            font_size=14, text_color=ACCENT_GOLD_DIM,
        )

        self.difficulty_sel = _OptionSelector(
            'Difficulty', ['Easy', 'Normal', 'Hard'],
            current=self.settings['difficulty'],
            parent=self, position=(0, section_y2 - 0.04),
            on_change=lambda v: self._set('difficulty', v),
        )

        # ── Text Size ────────────────────────────────────────────────────────
        self.textsize_sel = _OptionSelector(
            'Text Size', ['Small', 'Medium', 'Large'],
            current=self.settings['text_size'],
            parent=self, position=(0, section_y2 - 0.1),
            on_change=lambda v: self._set('text_size', v),
        )

        # ── Toggles ─────────────────────────────────────────────────────────
        section_y3 = -0.15
        heading_display = InfoText(
            text='--- Display ---',
            parent=self, position=(0, section_y3 + 0.02),
            font_size=14, text_color=ACCENT_GOLD_DIM,
        )

        self.romaji_toggle = _Toggle(
            'Show Romaji', value=self.settings['show_romaji'],
            parent=self, position=(0, section_y3 - 0.04),
            on_change=lambda v: self._set('show_romaji', v),
        )

        self.furigana_toggle = _Toggle(
            'Furigana', value=self.settings['show_furigana'],
            parent=self, position=(0, section_y3 - 0.1),
            on_change=lambda v: self._set('show_furigana', v),
        )

        # ── Back Button ─────────────────────────────────────────────────────
        self.back_btn = StyledButton(
            text='Back',
            position=(0, -0.39),
            scale=(0.2, 0.055),
            on_click=self._handle_back,
            parent=self,
            font_size=16,
        )

        # Transition
        self.transition = TransitionScreen(parent=self)
        self.transition.z = -1

    # ── Helpers ──────────────────────────────────────────────────────────────
    def _set(self, key, value):
        self.settings[key] = value
        self._save()

    def _save(self):
        save_settings(self.settings)

    def _handle_back(self):
        self._save()
        if self.on_back:
            self.on_back()

    # ── Public API ───────────────────────────────────────────────────────────
    def show(self):
        self.enabled = True
        self.settings = load_settings()
        self._sync_widgets()
        self.transition.fade_in(duration=0.35)

    def hide(self):
        self._save()

        def _do_hide():
            self.enabled = False

        self.transition.fade_out(duration=0.25, on_complete=_do_hide)

    def _sync_widgets(self):
        """Synchronise widget state with the current settings dict."""
        self.master_slider.value = self.settings['master_volume']
        self.music_slider.value = self.settings['music_volume']
        self.sfx_slider.value = self.settings['sfx_volume']
        self.difficulty_sel.current = self.settings['difficulty']
        self.textsize_sel.current = self.settings['text_size']
        self.romaji_toggle.value = self.settings['show_romaji']
        self.furigana_toggle.value = self.settings['show_furigana']


# ═══════════════════════════════════════════════════════════════════════════════
#  Stand-alone test
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    app = Ursina(title='Nihongo Quest - Settings', borderless=False)
    window.color = BG_DARK

    screen = SettingsScreen(on_back=lambda: print('Back pressed'))
    screen.show()

    app.run()
