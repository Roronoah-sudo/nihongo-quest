"""
character_match.py - Character Match Minigame
=============================================

Shows a large Japanese character in the centre of the screen.  The player
picks the correct romaji from several answer buttons below.

Lesson data format
------------------
    {
        'characters': [
            {'character': 'あ', 'romaji': 'a'},
            {'character': 'い', 'romaji': 'i'},
            ...
        ]
    }

Difficulty scaling
------------------
    easy   : 3 choices, 10 characters, generous timer
    normal : 4 choices, 15 characters, standard timer
    hard   : 5 choices, 20 characters, tight timer
"""

from ursina import *
import random
import math

from .base_minigame import (
    BaseMinigame,
    COLOR_BG, COLOR_PANEL, COLOR_ACCENT, COLOR_CORRECT, COLOR_WRONG,
    COLOR_GOLD, COLOR_TEXT, COLOR_TEXT_DIM, COLOR_BUTTON, COLOR_BUTTON_HOVER,
    COLOR_TIMER_BAR,
)


class CharacterMatchMinigame(BaseMinigame):
    """Match Japanese characters to their romaji readings."""

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------
    def setup(self):
        all_chars = list(self.lesson_data.get('characters', []))
        if not all_chars:
            self.complete()
            return

        # Difficulty parameters
        self.num_choices = self._difficulty_value(3, 4, 5)
        self.num_rounds = self._difficulty_value(10, 15, 20)
        self.time_per_char = self._difficulty_value(12, 8, 5)

        # Build the round queue (sample with possible repeats if pool is small)
        if len(all_chars) >= self.num_rounds:
            self.queue = random.sample(all_chars, self.num_rounds)
        else:
            self.queue = (all_chars * math.ceil(self.num_rounds / len(all_chars)))[:self.num_rounds]

        self.all_chars = all_chars
        self.current_index = 0
        self.max_score = self.num_rounds * 10
        self.answered = False
        self.round_timer = 0.0
        self.show_correct_timer = 0.0
        self.showing_correct = False

        # --- UI elements (persistent across rounds) ---

        # Timer bar
        self._create_timer_bar()

        # Score display
        self.score_text = self._create_text(
            text='Score: 0',
            position=(0.38, 0.44),
            scale=1.5,
            color=COLOR_GOLD,
            z=-2,
        )

        # Progress display
        self.progress_text = self._create_text(
            text=f'1 / {self.num_rounds}',
            position=(-0.38, 0.44),
            scale=1.3,
            color=COLOR_TEXT_DIM,
            z=-2,
        )

        # Central character
        self.char_display = self._create_text(
            text='',
            position=(0, 0.15),
            scale=8,
            color=COLOR_TEXT,
            z=-2,
        )

        # Answer buttons (we create them once and reuse)
        self.answer_buttons = []
        btn_width = 0.7 / self.num_choices
        start_x = -0.35 + btn_width / 2
        for i in range(self.num_choices):
            bx = start_x + i * (0.7 / self.num_choices)
            btn = self._create_button(
                text='',
                position=(bx, -0.15),
                scale=(btn_width - 0.01, 0.07),
                z=-2,
            )
            btn._choice_index = i
            self.answer_buttons.append(btn)

        # Feedback label (below buttons)
        self.feedback_label = self._create_text(
            text='',
            position=(0, -0.28),
            scale=1.8,
            color=COLOR_TEXT,
            z=-2,
        )

        # Start first round
        self._load_round()

    # ------------------------------------------------------------------
    # Per-round logic
    # ------------------------------------------------------------------
    def _load_round(self):
        """Populate the display and buttons for the current character."""
        if self.current_index >= len(self.queue):
            self.complete()
            return

        item = self.queue[self.current_index]
        self.current_char = item['character']
        self.current_romaji = item['romaji']
        self.answered = False
        self.showing_correct = False
        self.round_timer = self.time_per_char
        self.feedback_label.text = ''

        # Update character display
        self.char_display.text = self.current_char
        self.char_display.color = COLOR_TEXT

        # Build choices: 1 correct + (num_choices-1) wrong
        wrong_pool = [c['romaji'] for c in self.all_chars
                      if c['romaji'] != self.current_romaji]
        if len(wrong_pool) < self.num_choices - 1:
            # pad with dummy romaji if pool is too small
            wrong_pool += ['--'] * (self.num_choices - 1 - len(wrong_pool))
        wrong = random.sample(wrong_pool, self.num_choices - 1)
        choices = wrong + [self.current_romaji]
        random.shuffle(choices)

        self.correct_button_index = choices.index(self.current_romaji)

        for i, btn in enumerate(self.answer_buttons):
            btn.text = choices[i]
            btn.color = COLOR_BUTTON
            btn.highlight_color = COLOR_BUTTON_HOVER
            btn.on_click = lambda idx=i: self._on_answer(idx)

        # Update progress
        self.progress_text.text = f'{self.current_index + 1} / {self.num_rounds}'

    # ------------------------------------------------------------------
    # Answer handling
    # ------------------------------------------------------------------
    def _on_answer(self, index):
        """Called when the player clicks an answer button."""
        if self.answered or not self.is_active:
            return

        self.answered = True
        is_correct = (index == self.correct_button_index)

        if is_correct:
            self.score += 10
            self.correct_items.append(
                f'{self.current_char} = {self.current_romaji}')
            self.answer_buttons[index].color = COLOR_CORRECT
            self._show_result(True, self.current_romaji)
            self.score_text.text = f'Score: {self.score}'
            # Advance after short delay
            invoke(self._next_round, delay=0.6)
        else:
            penalty = 2
            self.score = max(0, self.score - penalty)
            self.wrong_items.append(
                f'{self.current_char} = {self.current_romaji}')
            self.answer_buttons[index].color = COLOR_WRONG
            self._shake_entity(self.answer_buttons[index])
            # Highlight the correct answer
            self.answer_buttons[self.correct_button_index].color = COLOR_CORRECT
            self.feedback_label.text = (
                f'Correct answer: {self.current_romaji}')
            self.feedback_label.color = COLOR_WRONG
            self._show_result(False, self.current_romaji)
            self.score_text.text = f'Score: {self.score}'
            # Show correct answer briefly
            self.showing_correct = True
            self.show_correct_timer = 1.5
            invoke(self._next_round, delay=1.5)

    def _time_expired(self):
        """Handle round timeout (counts as wrong)."""
        if self.answered:
            return
        self.answered = True
        self.wrong_items.append(
            f'{self.current_char} = {self.current_romaji} (time out)')
        self.answer_buttons[self.correct_button_index].color = COLOR_CORRECT
        self.feedback_label.text = f'Time up!  Answer: {self.current_romaji}'
        self.feedback_label.color = COLOR_WRONG
        self._show_result(False, 'Time Up!')
        invoke(self._next_round, delay=1.5)

    def _next_round(self):
        """Move to the next character or finish the minigame."""
        if not self.is_active:
            return
        self.current_index += 1
        self._load_round()

    # ------------------------------------------------------------------
    # Frame update
    # ------------------------------------------------------------------
    def update(self):
        if not self.is_active or self.answered:
            return

        self.round_timer -= time.dt
        fraction = max(0, self.round_timer / self.time_per_char)
        self._update_timer_bar(fraction)

        if self.round_timer <= 0:
            self._time_expired()
