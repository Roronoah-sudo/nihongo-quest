"""
typing_challenge.py - Typing Challenge Minigame
=================================================

Words (Japanese characters / vocabulary) fall from the top of the screen.
The player types the romaji / English equivalent to clear them before they
reach the bottom.  Features a combo counter for consecutive correct answers.

Lesson data format
------------------
    {
        'items': [
            {
                'display': 'あ',
                'answer': 'a',
                'alt_answers': [],   # optional alternative spellings
            },
            ...
        ]
    }

Difficulty scaling
------------------
    easy   : slow fall speed, 20 items, 8 s per word
    normal : medium speed,   25 items, 5 s per word
    hard   : fast speed,     30 items, 3 s per word
"""

from ursina import *
import random
import math
import string

from .base_minigame import (
    BaseMinigame,
    COLOR_BG, COLOR_PANEL, COLOR_ACCENT, COLOR_CORRECT, COLOR_WRONG,
    COLOR_GOLD, COLOR_TEXT, COLOR_TEXT_DIM, COLOR_BUTTON, COLOR_BUTTON_HOVER,
    COLOR_STREAK,
)


class TypingChallengeMinigame(BaseMinigame):
    """Falling-word typing challenge with combos."""

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------
    def setup(self):
        all_items = list(self.lesson_data.get('items', []))
        if not all_items:
            self.complete()
            return

        # Difficulty
        self.num_items = self._difficulty_value(20, 25, 30)
        self.time_per_word = self._difficulty_value(8, 5, 3)
        self.fall_speed = self._difficulty_value(0.04, 0.065, 0.09)
        self.spawn_interval = self._difficulty_value(3.0, 2.2, 1.5)

        # Build item queue
        if len(all_items) >= self.num_items:
            self.queue = random.sample(all_items, self.num_items)
        else:
            self.queue = (all_items * math.ceil(
                self.num_items / len(all_items)))[:self.num_items]

        self.max_score = self.num_items * 10
        self.combo = 0
        self.best_combo = 0
        self.items_spawned = 0
        self.items_cleared = 0
        self.spawn_timer = 0.0         # counts down to next spawn
        self.active_words = []         # list of dicts with entity refs
        self.typed_text = ''
        self.game_over = False

        # --- UI ---

        # Score
        self.score_text = self._create_text(
            text='Score: 0',
            position=(0.35, 0.44),
            scale=1.5,
            color=COLOR_GOLD,
            z=-2,
        )

        # Combo
        self.combo_text = self._create_text(
            text='',
            position=(0.35, 0.39),
            scale=1.3,
            color=COLOR_STREAK,
            z=-2,
        )

        # Progress
        self.progress_text = self._create_text(
            text=f'0 / {self.num_items}',
            position=(-0.38, 0.44),
            scale=1.3,
            color=COLOR_TEXT_DIM,
            z=-2,
        )

        # Input area (bottom panel)
        self.input_bg = self._create_entity(
            parent=camera.ui,
            model='quad',
            color=color.rgb(35, 35, 55),
            scale=(0.7, 0.06),
            position=(0, -0.4),
            z=-2,
        )

        self.input_text = self._create_text(
            text='|',
            position=(0, -0.4),
            scale=2.0,
            color=COLOR_ACCENT,
            z=-3,
        )

        # Deadline line
        self.deadline = self._create_entity(
            parent=camera.ui,
            model='quad',
            color=color.rgb(235, 87, 87),
            scale=(0.9, 0.003),
            position=(0, -0.33),
            z=-1.5,
        )

        # Instructions
        self._create_text(
            text='Type the romaji and press Enter',
            position=(0, -0.46),
            scale=1.0,
            color=COLOR_TEXT_DIM,
            z=-2,
        )

        # Spawn first word immediately
        self.spawn_timer = 0.1

    # ------------------------------------------------------------------
    # Word spawning
    # ------------------------------------------------------------------
    def _spawn_word(self):
        """Spawn a new falling word entity."""
        if self.items_spawned >= self.num_items:
            return

        item = self.queue[self.items_spawned]
        self.items_spawned += 1

        # Random horizontal position
        x_pos = random.uniform(-0.35, 0.35)

        # Container entity
        word_panel = Entity(
            parent=camera.ui,
            model='quad',
            color=color.rgb(50, 50, 75),
            scale=(0.14, 0.06),
            position=(x_pos, 0.5),
            z=-2,
        )
        self.entities.append(word_panel)

        # Japanese text
        display_text = Text(
            text=item['display'],
            parent=word_panel,
            origin=(0, 0),
            scale=(5 / 0.14, 5 / 0.06),
            color=COLOR_TEXT,
            z=-0.01,
        )
        self.entities.append(display_text)

        word_data = {
            'entity': word_panel,
            'display_text': display_text,
            'item': item,
            'answer': item['answer'].lower().strip(),
            'alt_answers': [a.lower().strip()
                            for a in item.get('alt_answers', [])],
            'speed': self.fall_speed + random.uniform(-0.005, 0.005),
        }
        self.active_words.append(word_data)

    # ------------------------------------------------------------------
    # Input handling
    # ------------------------------------------------------------------
    def _handle_input(self):
        """Process keyboard input for typing."""
        if self.game_over or not self.is_active:
            return

        # Collect typed characters
        for key in string.ascii_lowercase + string.digits + "'-":
            if held_keys[key] and not hasattr(self, f'_key_held_{key}'):
                setattr(self, f'_key_held_{key}', True)
                self.typed_text += key
            elif not held_keys[key] and hasattr(self, f'_key_held_{key}'):
                delattr(self, f'_key_held_{key}')

        # Space
        if held_keys['space'] and not hasattr(self, '_key_held_space'):
            self._key_held_space = True
            self.typed_text += ' '
        elif not held_keys['space'] and hasattr(self, '_key_held_space'):
            del self._key_held_space

        # Backspace
        if held_keys['backspace'] and not hasattr(self, '_key_held_bs'):
            self._key_held_bs = True
            self.typed_text = self.typed_text[:-1]
        elif not held_keys['backspace'] and hasattr(self, '_key_held_bs'):
            del self._key_held_bs

        # Enter -> submit
        if held_keys['enter'] and not hasattr(self, '_key_held_enter'):
            self._key_held_enter = True
            self._submit()
        elif not held_keys['enter'] and hasattr(self, '_key_held_enter'):
            del self._key_held_enter

        # Update display
        self.input_text.text = self.typed_text + '|'

    def _submit(self):
        """Check typed text against active words."""
        answer = self.typed_text.lower().strip()
        self.typed_text = ''

        if not answer:
            return

        # Find the first matching active word (lowest on screen = most urgent)
        matched = None
        for wd in sorted(self.active_words,
                         key=lambda w: -w['entity'].y):
            all_answers = [wd['answer']] + wd['alt_answers']
            if answer in all_answers:
                matched = wd
                break

        if matched:
            self._clear_word(matched, correct=True)
        else:
            # Wrong answer flash
            self.combo = 0
            self._update_combo()
            self._show_result(False, answer, duration=0.3)

    def _clear_word(self, word_data, correct=True):
        """Remove a word from the field (correct match or missed)."""
        if correct:
            self.score += self._combo_points()
            self.combo += 1
            if self.combo > self.best_combo:
                self.best_combo = self.combo
            self.items_cleared += 1
            self.correct_items.append(
                f"{word_data['item']['display']} = {word_data['answer']}")
            self._show_result(True,
                              f"+{self._combo_points()} "
                              f"{word_data['item']['display']}",
                              duration=0.35)
        else:
            self.combo = 0
            self.wrong_items.append(
                f"{word_data['item']['display']} = {word_data['answer']}")
            self._show_result(False,
                              f"{word_data['item']['display']}"
                              f" = {word_data['answer']}",
                              duration=0.5)

        # Remove entities
        if word_data in self.active_words:
            self.active_words.remove(word_data)
        if word_data['entity'] in self.entities:
            self.entities.remove(word_data['entity'])
        if word_data['display_text'] in self.entities:
            self.entities.remove(word_data['display_text'])
        destroy(word_data['display_text'])
        destroy(word_data['entity'])

        # Update displays
        self.score_text.text = f'Score: {self.score}'
        self._update_combo()
        self.progress_text.text = \
            f'{self.items_cleared} / {self.num_items}'

    def _combo_points(self):
        """Points for the current combo level."""
        if self.combo >= 10:
            return 25
        elif self.combo >= 5:
            return 15
        elif self.combo >= 3:
            return 12
        return 10

    def _update_combo(self):
        if self.combo >= 3:
            self.combo_text.text = f'Combo x{self.combo}!'
        elif self.combo > 0:
            self.combo_text.text = f'Combo: {self.combo}'
        else:
            self.combo_text.text = ''

    # ------------------------------------------------------------------
    # Frame update
    # ------------------------------------------------------------------
    def update(self):
        if not self.is_active or self.game_over:
            return

        dt = time.dt
        self._handle_input()

        # Spawn timer
        self.spawn_timer -= dt
        if self.spawn_timer <= 0 and self.items_spawned < self.num_items:
            self._spawn_word()
            self.spawn_timer = self.spawn_interval

        # Move words down
        to_remove = []
        for wd in self.active_words:
            wd['entity'].y -= wd['speed'] * dt
            # Check deadline
            if wd['entity'].y <= -0.33:
                to_remove.append(wd)

        for wd in to_remove:
            self._clear_word(wd, correct=False)

        # Check if game is over
        if (self.items_spawned >= self.num_items
                and len(self.active_words) == 0):
            self.game_over = True
            # Bonus for best combo
            if self.best_combo >= 5:
                bonus = self.best_combo * 2
                self.score += bonus
                self.max_score += bonus
            invoke(self.complete, delay=0.8)
