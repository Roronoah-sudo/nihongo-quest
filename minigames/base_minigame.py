"""
base_minigame.py - Abstract base class for all Nihongo Quest minigames.

Provides shared infrastructure: entity tracking, scoring, timer management,
difficulty scaling, visual feedback (correct/wrong flashes), and the
score-card overlay shown after every round.

Subclasses must implement:
    setup()   - create entities / UI for the minigame
    update()  - per-frame logic (called only while self.is_active)
"""

from ursina import *
from abc import ABC, abstractmethod
import math


# ---------------------------------------------------------------------------
# Colour palette (shared across all minigames)
# ---------------------------------------------------------------------------
COLOR_BG           = color.rgb(30, 30, 46)
COLOR_PANEL        = color.rgb(45, 45, 65)
COLOR_ACCENT       = color.rgb(137, 180, 250)
COLOR_CORRECT      = color.rgb(80, 200, 120)
COLOR_WRONG        = color.rgb(235, 87, 87)
COLOR_GOLD         = color.rgb(255, 215, 0)
COLOR_SILVER       = color.rgb(192, 192, 192)
COLOR_BRONZE       = color.rgb(205, 127, 50)
COLOR_TEXT          = color.rgb(230, 230, 250)
COLOR_TEXT_DIM      = color.rgb(160, 160, 180)
COLOR_BUTTON        = color.rgb(60, 60, 90)
COLOR_BUTTON_HOVER  = color.rgb(80, 80, 120)
COLOR_TIMER_BAR     = color.rgb(250, 180, 50)
COLOR_TIMER_LOW     = color.rgb(235, 87, 87)
COLOR_STREAK        = color.rgb(255, 170, 50)
COLOR_CARD_BACK     = color.rgb(180, 50, 50)


class BaseMinigame(ABC):
    """Base class for all minigames in Nihongo Quest."""

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------
    def __init__(self, lesson_data, difficulty='normal', on_complete=None):
        """
        Parameters
        ----------
        lesson_data : dict
            Content for this minigame (characters, words, pairs, etc.).
        difficulty : str
            One of 'easy', 'normal', 'hard'.
        on_complete : callable or None
            Signature: on_complete(score, max_score, correct_items, wrong_items)
        """
        self.lesson_data = lesson_data
        self.difficulty = difficulty
        self.on_complete = on_complete

        # Scoring
        self.score = 0
        self.max_score = 0
        self.correct_items = []
        self.wrong_items = []

        # Entity management
        self.entities = []          # every entity created via helpers
        self._ui_entities = []      # subset: HUD / overlay elements

        # State
        self.is_active = False
        self.is_paused = False
        self.time_limit = self._get_time_limit()
        self.timer = 0.0
        self.hints_used = 0

        # Background overlay (dims the 3-D world)
        self._bg = None

    # ------------------------------------------------------------------
    # Difficulty helpers
    # ------------------------------------------------------------------
    def _get_time_limit(self):
        """Return time limit in seconds based on difficulty."""
        limits = {'easy': 120, 'normal': 90, 'hard': 60}
        return limits.get(self.difficulty, 90)

    def _difficulty_value(self, easy, normal, hard):
        """Return *easy*, *normal*, or *hard* depending on self.difficulty."""
        return {'easy': easy, 'normal': normal, 'hard': hard}.get(
            self.difficulty, normal)

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------
    @abstractmethod
    def setup(self):
        """Create all game entities and UI.  Must be overridden."""

    @abstractmethod
    def update(self):
        """Called every frame while the minigame is active."""

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def show(self):
        """Activate the minigame and run setup()."""
        self.is_active = True
        self._create_background()
        self.setup()

    def hide(self):
        """Tear down all created entities."""
        self.is_active = False
        for e in self.entities:
            if e is not None:
                destroy(e)
        self.entities.clear()
        self._ui_entities.clear()
        if self._bg:
            destroy(self._bg)
            self._bg = None

    def complete(self):
        """Finish the minigame: show score card, then fire callback."""
        self.is_active = False
        self._show_score_card()

    # ------------------------------------------------------------------
    # Entity / UI creation helpers
    # ------------------------------------------------------------------
    def _create_entity(self, **kwargs):
        """Create a generic Entity, track it, and return it."""
        e = Entity(**kwargs)
        self.entities.append(e)
        return e

    def _create_text(self, text='', **kwargs):
        """Create a Text entity, track it, and return it."""
        defaults = dict(
            parent=camera.ui,
            origin=(0, 0),
            color=COLOR_TEXT,
        )
        defaults.update(kwargs)
        # Extract wordwrap to set after creation (avoids Ursina raw_text bug)
        ww = defaults.pop('wordwrap', None)
        t = Text(text=text, **defaults)
        if ww is not None:
            if not hasattr(t, 'raw_text'):
                t.raw_text = ''
            t.wordwrap = ww
        self.entities.append(t)
        self._ui_entities.append(t)
        return t

    def _create_button(self, text='', on_click=None, **kwargs):
        """Create a stylised Button, track it, and return it."""
        defaults = dict(
            parent=camera.ui,
            scale=(0.35, 0.065),
            color=COLOR_BUTTON,
            highlight_color=COLOR_BUTTON_HOVER,
            text_color=COLOR_TEXT,
            radius=0.25,
        )
        defaults.update(kwargs)
        b = Button(text=text, **defaults)
        if on_click:
            b.on_click = on_click
        self.entities.append(b)
        self._ui_entities.append(b)
        return b

    def _create_panel(self, **kwargs):
        """Create a rounded-rectangle panel (Entity with quad model)."""
        defaults = dict(
            parent=camera.ui,
            model='quad',
            color=COLOR_PANEL,
            scale=(0.8, 0.6),
        )
        defaults.update(kwargs)
        p = Entity(**defaults)
        self.entities.append(p)
        self._ui_entities.append(p)
        return p

    def _create_background(self):
        """Full-screen dark overlay behind all minigame UI."""
        self._bg = Entity(
            parent=camera.ui,
            model='quad',
            color=color.rgba(10, 10, 20, 220),
            scale=(2, 2),
            z=1,
        )
        self.entities.append(self._bg)

    # ------------------------------------------------------------------
    # Timer bar
    # ------------------------------------------------------------------
    def _create_timer_bar(self):
        """Create a horizontal timer bar at the top of the screen."""
        bg = Entity(
            parent=camera.ui,
            model='quad',
            color=color.rgb(40, 40, 55),
            scale=(0.9, 0.025),
            position=(0, 0.47),
            z=-0.1,
        )
        self.entities.append(bg)

        bar = Entity(
            parent=camera.ui,
            model='quad',
            color=COLOR_TIMER_BAR,
            scale=(0.9, 0.02),
            position=(0, 0.47),
            origin=(-0.5, 0),
            z=-0.2,
        )
        self.entities.append(bar)
        self._timer_bar = bar
        return bar

    def _update_timer_bar(self, fraction):
        """Set the timer bar width (0..1) and colour."""
        if not hasattr(self, '_timer_bar'):
            return
        self._timer_bar.scale_x = 0.9 * max(0, min(1, fraction))
        if fraction < 0.25:
            self._timer_bar.color = COLOR_TIMER_LOW
        elif fraction < 0.5:
            self._timer_bar.color = color.rgb(250, 210, 80)
        else:
            self._timer_bar.color = COLOR_TIMER_BAR

    # ------------------------------------------------------------------
    # Visual feedback
    # ------------------------------------------------------------------
    def _show_result(self, is_correct, item_text='', duration=0.5):
        """Flash the screen green/red and show a small label."""
        flash_color = COLOR_CORRECT if is_correct else COLOR_WRONG
        label_text = 'Correct!' if is_correct else 'Wrong'

        flash = Entity(
            parent=camera.ui,
            model='quad',
            color=color.rgba(flash_color.r * 255, flash_color.g * 255,
                             flash_color.b * 255, 100),
            scale=(2, 2),
            z=-5,
        )
        self.entities.append(flash)
        flash.animate('color', color.rgba(0, 0, 0, 0), duration=duration,
                       curve=curve.out_expo)
        destroy(flash, delay=duration + 0.1)

        lbl = Text(
            text=f'{label_text}  {item_text}',
            parent=camera.ui,
            origin=(0, 0),
            scale=2.5 if is_correct else 2,
            color=flash_color,
            z=-6,
        )
        self.entities.append(lbl)
        lbl.animate('y', lbl.y + 0.05, duration=duration,
                     curve=curve.out_expo)
        lbl.animate('color', color.rgba(0, 0, 0, 0), duration=duration,
                     curve=curve.out_expo)
        destroy(lbl, delay=duration + 0.1)

    def _shake_entity(self, entity, magnitude=0.01, duration=0.3):
        """Quick horizontal shake animation on *entity*."""
        if entity is None:
            return
        orig_x = entity.x
        seq = Sequence(
            Func(setattr, entity, 'x', orig_x + magnitude),
            Wait(duration / 6),
            Func(setattr, entity, 'x', orig_x - magnitude),
            Wait(duration / 6),
            Func(setattr, entity, 'x', orig_x + magnitude * 0.6),
            Wait(duration / 6),
            Func(setattr, entity, 'x', orig_x - magnitude * 0.6),
            Wait(duration / 6),
            Func(setattr, entity, 'x', orig_x + magnitude * 0.2),
            Wait(duration / 6),
            Func(setattr, entity, 'x', orig_x),
        )
        seq.start()

    # ------------------------------------------------------------------
    # Score card overlay
    # ------------------------------------------------------------------
    def _get_star_rating(self):
        """Return 1-5 star rating based on score / max_score."""
        if self.max_score == 0:
            return 0
        pct = self.score / self.max_score
        if pct >= 0.95:
            return 5
        elif pct >= 0.80:
            return 4
        elif pct >= 0.65:
            return 3
        elif pct >= 0.45:
            return 2
        elif pct >= 0.20:
            return 1
        return 0

    def _show_score_card(self):
        """Display the end-of-round score card with stars, retry, continue."""
        # Dim background a bit more
        overlay = Entity(
            parent=camera.ui,
            model='quad',
            color=color.rgba(5, 5, 15, 200),
            scale=(2, 2),
            z=-8,
        )
        self.entities.append(overlay)

        # Card panel
        card = Entity(
            parent=camera.ui,
            model='quad',
            color=COLOR_PANEL,
            scale=(0.7, 0.7),
            z=-9,
        )
        self.entities.append(card)

        # Title
        pct = int((self.score / self.max_score * 100) if self.max_score else 0)
        title_text = 'Perfect!' if pct >= 95 else (
            'Great Job!' if pct >= 70 else (
            'Good Effort!' if pct >= 40 else 'Keep Practicing!'))
        title = Text(
            text=title_text,
            parent=camera.ui,
            origin=(0, 0),
            y=0.25,
            scale=3,
            color=COLOR_ACCENT,
            z=-10,
        )
        self.entities.append(title)

        # Stars
        stars = self._get_star_rating()
        star_colors = [COLOR_GOLD] * stars + [color.rgb(60, 60, 80)] * (5 - stars)
        for i in range(5):
            sx = -0.12 + i * 0.06
            star = Text(
                text='*',
                parent=camera.ui,
                origin=(0, 0),
                position=(sx, 0.17),
                scale=4,
                color=star_colors[i],
                z=-10,
            )
            self.entities.append(star)

        # Score / stats
        score_label = Text(
            text=f'Score:  {self.score} / {self.max_score}  ({pct}%)',
            parent=camera.ui,
            origin=(0, 0),
            y=0.08,
            scale=1.8,
            color=COLOR_TEXT,
            z=-10,
        )
        self.entities.append(score_label)

        correct_label = Text(
            text=f'Correct: {len(self.correct_items)}    '
                 f'Wrong: {len(self.wrong_items)}    '
                 f'Hints: {self.hints_used}',
            parent=camera.ui,
            origin=(0, 0),
            y=0.02,
            scale=1.3,
            color=COLOR_TEXT_DIM,
            z=-10,
        )
        self.entities.append(correct_label)

        # Wrong items review (scrollable area, up to 6 shown)
        if self.wrong_items:
            review_title = Text(
                text='Review these:',
                parent=camera.ui,
                origin=(0, 0),
                y=-0.06,
                scale=1.3,
                color=COLOR_WRONG,
                z=-10,
            )
            self.entities.append(review_title)
            for idx, item in enumerate(self.wrong_items[:6]):
                line = item if isinstance(item, str) else str(item)
                row = Text(
                    text=line,
                    parent=camera.ui,
                    origin=(0, 0),
                    y=-0.11 - idx * 0.035,
                    scale=1.1,
                    color=COLOR_TEXT_DIM,
                    z=-10,
                )
                self.entities.append(row)

        # Buttons
        retry_btn = Button(
            text='Retry',
            parent=camera.ui,
            scale=(0.18, 0.055),
            position=(-0.12, -0.28),
            color=COLOR_BUTTON,
            highlight_color=COLOR_BUTTON_HOVER,
            text_color=COLOR_TEXT,
            radius=0.25,
            z=-10,
        )
        retry_btn.on_click = self._on_retry
        self.entities.append(retry_btn)

        continue_btn = Button(
            text='Continue',
            parent=camera.ui,
            scale=(0.18, 0.055),
            position=(0.12, -0.28),
            color=COLOR_ACCENT,
            highlight_color=color.rgb(170, 200, 255),
            text_color=color.rgb(20, 20, 40),
            radius=0.25,
            z=-10,
        )
        continue_btn.on_click = self._on_continue
        self.entities.append(continue_btn)

    def _on_retry(self):
        """Reset state and re-run the minigame."""
        self.score = 0
        self.max_score = 0
        self.correct_items.clear()
        self.wrong_items.clear()
        self.hints_used = 0
        self.timer = 0
        self.hide()
        self.show()

    def _on_continue(self):
        """Fire the on_complete callback, then tear down."""
        callback_data = (self.score, self.max_score,
                         list(self.correct_items), list(self.wrong_items))
        self.hide()
        if self.on_complete:
            self.on_complete(*callback_data)
