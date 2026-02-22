"""
Nihongo Quest - Dialog / Lesson Display System
================================================
Visual-novel style bottom-of-screen dialog box with typewriter effect,
furigana rendering, speaker portrait, and interactive choices.
"""

from ursina import *

from ui.components import (
    StyledButton, StyledPanel, InfoText,
    BG_DARK, ACCENT_RED, ACCENT_GOLD, TEXT_WHITE, PANEL_BG,
    ACCENT_GOLD_DIM, TEXT_GREY, ACCENT_RED_LIGHT,
)


# ═══════════════════════════════════════════════════════════════════════════════
#  FuriganaText  -- renders kanji with small reading text above
# ═══════════════════════════════════════════════════════════════════════════════
class FuriganaText(Entity):
    """
    Renders a line of Japanese text with optional furigana (readings)
    displayed as smaller text above the base characters.

    Furigana is specified inline using the notation:
        {kanji|reading}

    Example:
        "{日本語|にほんご}を{勉強|べんきょう}する"
        renders:  にほんご       べんきょう
                  日本語    を   勉強      する

    If show_furigana is False the readings are simply hidden.
    """

    def __init__(self, text='', position=(0, 0), font_size=20,
                 show_furigana=True, parent=camera.ui, **kwargs):

        super().__init__(parent=parent, position=position, **kwargs)

        self._raw = text
        self._font_size = font_size
        self._show_furigana = show_furigana
        self._entities = []

        self._render()

    def _parse(self, raw):
        """
        Parse raw text into segments.
        Returns list of (base_text, furigana_or_None).
        """
        segments = []
        i = 0
        while i < len(raw):
            if raw[i] == '{':
                end = raw.find('}', i)
                if end == -1:
                    segments.append((raw[i:], None))
                    break
                inner = raw[i + 1:end]
                if '|' in inner:
                    base, reading = inner.split('|', 1)
                    segments.append((base, reading))
                else:
                    segments.append((inner, None))
                i = end + 1
            else:
                # Collect plain text until next '{'
                j = raw.find('{', i)
                if j == -1:
                    segments.append((raw[i:], None))
                    break
                segments.append((raw[i:j], None))
                i = j
        return segments

    def _render(self):
        for e in self._entities:
            destroy(e)
        self._entities.clear()

        segments = self._parse(self._raw)

        # We lay out segments left-to-right using a cursor
        cursor_x = 0.0
        char_width = self._font_size * 0.0006  # approximate per-char width

        for base, reading in segments:
            segment_width = len(base) * char_width

            # Base text
            bt = Text(
                text=base,
                parent=self,
                font_size=self._font_size,
                color=TEXT_WHITE,
                origin=(-0.5, 0),
                position=(cursor_x, 0),
            )
            self._entities.append(bt)

            # Furigana (small reading above)
            if reading and self._show_furigana:
                furigana_size = max(9, self._font_size * 0.5)
                ft = Text(
                    text=reading,
                    parent=self,
                    font_size=furigana_size,
                    color=ACCENT_GOLD_DIM,
                    origin=(-0.5, 0),
                    position=(cursor_x, 0.018),
                )
                self._entities.append(ft)

            cursor_x += segment_width

    @property
    def text(self):
        return self._raw

    @text.setter
    def text(self, value):
        self._raw = value
        self._render()

    @property
    def show_furigana(self):
        return self._show_furigana

    @show_furigana.setter
    def show_furigana(self, value):
        self._show_furigana = bool(value)
        self._render()


# ═══════════════════════════════════════════════════════════════════════════════
#  DialogBox
# ═══════════════════════════════════════════════════════════════════════════════
class DialogBox(Entity):
    """
    Visual-novel / RPG-style dialog box anchored at the bottom of the screen.

    Features:
      - Speaker name plate
      - Portrait area (coloured rectangle placeholder)
      - Typewriter text reveal
      - Furigana support
      - Click / "Next" button to advance
      - Choice selection mode

    Usage:
        dlg = DialogBox()
        dlg.show_dialog('Sensei', 'Welcome to {日本|にほん}!',
                        portrait_color=color.blue)
        # later ...
        dlg.show_choices(
            ['Yes', 'No', 'Maybe'],
            callback=lambda idx, txt: print(f'Chose {idx}: {txt}'),
        )
    """

    def __init__(self, show_furigana=True, on_dialog_complete=None,
                 **kwargs):
        super().__init__(parent=camera.ui, **kwargs)

        self._show_furigana = show_furigana
        self.on_dialog_complete = on_dialog_complete

        # State
        self._full_text = ''
        self._revealed = 0
        self._typing = False
        self._type_speed = 0.035        # seconds per character
        self._type_sequence = None
        self._choice_entities = []

        self._build()
        self.enabled = False             # hidden by default

    # ── Build ────────────────────────────────────────────────────────────────
    def _build(self):
        box_height = 0.22
        box_y = -0.32

        # ── Main panel ──────────────────────────────────────────────────────
        self.panel = Entity(
            parent=self,
            model='quad',
            color=color.rgba(15, 8, 22, 230),
            scale=(0.92, box_height),
            position=(0.02, box_y),
            z=0.1,
        )
        # Gold borders
        Entity(parent=self.panel, model='quad', color=ACCENT_GOLD,
               scale=(1, 0.012), position=(0, 0.5), z=-0.01)
        Entity(parent=self.panel, model='quad', color=ACCENT_GOLD,
               scale=(1, 0.008), position=(0, -0.5), z=-0.01)

        # ── Portrait area (left side) ───────────────────────────────────────
        portrait_size = box_height * 0.8
        self.portrait = Entity(
            parent=self,
            model='quad',
            color=color.gray,
            scale=(portrait_size * 0.6, portrait_size),
            position=(-0.36, box_y),
            z=0,
        )
        # Small gold frame around portrait
        Entity(parent=self.portrait, model='quad', color=ACCENT_GOLD,
               scale=(1.08, 1.06), z=0.01)
        self.portrait_inner = Entity(
            parent=self.portrait, model='quad', color=color.gray,
            scale=(1, 1), z=-0.01,
        )

        # ── Speaker name plate ──────────────────────────────────────────────
        self.name_plate = Entity(
            parent=self,
            model='quad',
            color=ACCENT_RED,
            scale=(0.18, 0.035),
            position=(-0.18, box_y + box_height / 2 + 0.02),
            z=0,
        )
        self.speaker_text = Text(
            text='',
            parent=self.name_plate,
            font_size=15,
            color=ACCENT_GOLD,
            origin=(0, 0),
            z=-0.01,
        )

        # ── Dialog text area ────────────────────────────────────────────────
        text_x = -0.2
        text_y = box_y + 0.04
        self.dialog_text = Text(
            text='',
            parent=self,
            font_size=18,
            color=TEXT_WHITE,
            origin=(-0.5, 0.5),
            position=(text_x, text_y),
            z=-0.01,
        )
        if not hasattr(self.dialog_text, 'raw_text'):
            self.dialog_text.raw_text = ''
        self.dialog_text.wordwrap = 55

        # Furigana line (rendered above the main text when needed)
        self.furigana_entity = FuriganaText(
            text='',
            parent=self,
            position=(text_x, text_y + 0.025),
            font_size=18,
            show_furigana=self._show_furigana,
        )
        self.furigana_entity.enabled = False  # only used explicitly

        # ── "Next" indicator (small blinking triangle) ──────────────────────
        self.next_indicator = Text(
            text='>>',
            parent=self,
            font_size=14,
            color=ACCENT_GOLD,
            origin=(0.5, -0.5),
            position=(0.44, box_y - box_height / 2 + 0.025),
            z=-0.01,
        )
        self.next_indicator.enabled = False
        self._blink_seq = None

        # ── Click-catcher (transparent button over panel to capture clicks) ─
        self.click_area = Button(
            parent=self,
            model='quad',
            color=color.rgba(0, 0, 0, 0),
            highlight_color=color.rgba(0, 0, 0, 0),
            pressed_color=color.rgba(0, 0, 0, 0),
            scale=self.panel.scale,
            position=self.panel.position,
            z=-0.02,
            on_click=self.advance,
        )

    # ── Typewriter Effect ────────────────────────────────────────────────────
    def _start_typing(self, text):
        self._full_text = text
        self._revealed = 0
        self._typing = True
        self.dialog_text.text = ''
        self.next_indicator.enabled = False
        self._stop_blink()
        self._type_next_char()

    def _type_next_char(self):
        if not self._typing:
            return
        if self._revealed >= len(self._full_text):
            self._finish_typing()
            return

        self._revealed += 1
        self.dialog_text.text = self._full_text[:self._revealed]
        self._type_sequence = invoke(self._type_next_char,
                                     delay=self._type_speed)

    def _finish_typing(self):
        self._typing = False
        self.dialog_text.text = self._full_text
        self.next_indicator.enabled = True
        self._start_blink()

    def _skip_typing(self):
        """Instantly reveal all text."""
        self._typing = False
        if self._type_sequence:
            self._type_sequence = None
        self.dialog_text.text = self._full_text
        self._revealed = len(self._full_text)
        self.next_indicator.enabled = True
        self._start_blink()

    # ── Blinking next-indicator ──────────────────────────────────────────────
    def _start_blink(self):
        self._stop_blink()
        self._do_blink()

    def _do_blink(self):
        if not self.next_indicator.enabled:
            return
        self.next_indicator.animate_color(
            color.rgba(255, 215, 0, 60), duration=0.5)
        invoke(lambda: self.next_indicator.animate_color(
            ACCENT_GOLD, duration=0.5) if self.next_indicator.enabled else None,
            delay=0.5)
        self._blink_seq = invoke(self._do_blink, delay=1.0)

    def _stop_blink(self):
        self._blink_seq = None

    # ── Public API ───────────────────────────────────────────────────────────
    def show_dialog(self, speaker, text, portrait_color=None):
        """
        Show a new line of dialog.

        Parameters:
            speaker        : str  -- speaker's name (shown on name plate)
            text           : str  -- dialog text (may contain {kanji|reading})
            portrait_color : ursina Color -- colour for the portrait rectangle
        """
        self.enabled = True
        self._clear_choices()

        # Speaker
        self.speaker_text.text = speaker
        self.name_plate.enabled = bool(speaker)

        # Portrait
        if portrait_color:
            self.portrait_inner.color = portrait_color
            self.portrait.enabled = True
        else:
            self.portrait.enabled = False

        # If text contains furigana markup, render via FuriganaText
        if '{' in text and '|' in text:
            # Show furigana entity, strip markup for typewriter base text
            plain = self._strip_furigana(text)
            self.furigana_entity.text = text
            self.furigana_entity.enabled = self._show_furigana
            self._start_typing(plain)
        else:
            self.furigana_entity.enabled = False
            self._start_typing(text)

    def _strip_furigana(self, text):
        """Remove furigana markup, leaving only the base kanji/text."""
        result = []
        i = 0
        while i < len(text):
            if text[i] == '{':
                end = text.find('}', i)
                if end == -1:
                    result.append(text[i:])
                    break
                inner = text[i + 1:end]
                if '|' in inner:
                    base, _ = inner.split('|', 1)
                    result.append(base)
                else:
                    result.append(inner)
                i = end + 1
            else:
                result.append(text[i])
                i += 1
        return ''.join(result)

    def show_choices(self, choices, callback=None):
        """
        Display a set of selectable choices.

        Parameters:
            choices  : list[str]  -- choice texts
            callback : (index, text) -> None  -- called when a choice is picked
        """
        self._clear_choices()
        self.next_indicator.enabled = False
        self._stop_blink()

        start_y = -0.18
        spacing = 0.055
        for i, choice_text in enumerate(choices):
            btn = StyledButton(
                text=f'{i + 1}. {choice_text}',
                parent=self,
                position=(0.12, start_y - i * spacing),
                scale=(0.5, 0.045),
                font_size=15,
                on_click=lambda idx=i, txt=choice_text: self._choose(
                    idx, txt, callback),
            )
            self._choice_entities.append(btn)

    def _choose(self, index, text, callback):
        self._clear_choices()
        if callback:
            callback(index, text)

    def _clear_choices(self):
        for e in self._choice_entities:
            destroy(e)
        self._choice_entities.clear()

    def advance(self):
        """
        Called when the player clicks / presses next.
        If typing, skip to end.  If done, fire on_dialog_complete.
        """
        if self._typing:
            self._skip_typing()
        else:
            if self.on_dialog_complete:
                self.on_dialog_complete()

    def hide(self):
        self._typing = False
        self._stop_blink()
        self._clear_choices()
        self.enabled = False

    def show(self):
        self.enabled = True

    # Convenience property
    @property
    def show_furigana(self):
        return self._show_furigana

    @show_furigana.setter
    def show_furigana(self, value):
        self._show_furigana = bool(value)
        self.furigana_entity.show_furigana = self._show_furigana


# ═══════════════════════════════════════════════════════════════════════════════
#  Stand-alone test
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    app = Ursina(title='Nihongo Quest - Dialog Test', borderless=False)
    window.color = BG_DARK

    lines = [
        ('Sensei', 'Welcome to {日本語|にほんご}クエスト!', color.blue),
        ('Sensei', 'Today we will learn {平仮名|ひらがな}.', color.blue),
        ('Sakura', 'I am ready!  Let\'s begin!', color.pink),
        (None,     'The adventure starts now...', None),
    ]
    line_idx = [0]

    def next_line():
        idx = line_idx[0]
        if idx < len(lines):
            speaker, text, col = lines[idx]
            dlg.show_dialog(speaker, text, portrait_color=col)
            line_idx[0] += 1
        else:
            # Show choices demo
            dlg.show_choices(
                ['Start lesson', 'Explore town', 'Rest at inn'],
                callback=lambda i, t: print(f'Chose: {t}'),
            )

    dlg = DialogBox(show_furigana=True, on_dialog_complete=next_line)
    next_line()

    app.run()
