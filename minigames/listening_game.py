"""
listening_game.py - Listening Game Minigame
============================================

Simulates a listening exercise visually: the romaji pronunciation (with
pitch-accent marks) is shown prominently, and the player selects the
matching Japanese character/word from several options.

Includes a "Speed Round" variant where items arrive in rapid succession.

Lesson data format
------------------
    {
        'items': [
            {
                'romaji': 'a',
                'correct_character': 'あ',
                'wrong_characters': ['い', 'う', 'え'],
            },
            ...
        ]
    }

Difficulty scaling
------------------
    easy   : 3 choices, 10 items, 10 s per item, no speed round
    normal : 4 choices, 15 items, 7 s per item, last 5 = speed round
    hard   : 5 choices, 20 items, 5 s per item, last 10 = speed round
"""

from ursina import *
import random
import math

from .base_minigame import (
    BaseMinigame,
    COLOR_BG, COLOR_PANEL, COLOR_ACCENT, COLOR_CORRECT, COLOR_WRONG,
    COLOR_GOLD, COLOR_TEXT, COLOR_TEXT_DIM, COLOR_BUTTON, COLOR_BUTTON_HOVER,
    COLOR_STREAK,
)

COLOR_ROMAJI     = color.rgb(255, 200, 100)
COLOR_SPEED_BG   = color.rgb(60, 30, 30)
COLOR_SPEED_TEXT  = color.rgb(255, 120, 80)


class ListeningMinigame(BaseMinigame):
    """Identify the correct Japanese character from its romaji pronunciation."""

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------
    def setup(self):
        all_items = list(self.lesson_data.get('items', []))
        if not all_items:
            self.complete()
            return

        # Difficulty
        self.num_choices = self._difficulty_value(3, 4, 5)
        self.num_items = self._difficulty_value(10, 15, 20)
        self.time_per_item = self._difficulty_value(10, 7, 5)
        self.speed_round_start = self._difficulty_value(
            self.num_items + 1,         # never on easy
            self.num_items - 5,         # last 5 on normal
            self.num_items - 10,        # last 10 on hard
        )
        self.speed_time = 3  # seconds in speed round

        # Queue
        if len(all_items) >= self.num_items:
            self.queue = random.sample(all_items, self.num_items)
        else:
            self.queue = (all_items * math.ceil(
                self.num_items / len(all_items)))[:self.num_items]

        self.all_items = all_items
        self.current_index = 0
        self.max_score = self.num_items * 10
        self.answered = False
        self.round_timer = 0.0
        self.streak = 0
        self.is_speed_round = False

        # --- UI ---
        self._create_timer_bar()

        # Score
        self.score_text = self._create_text(
            text='Score: 0',
            position=(0.35, 0.44),
            scale=1.5,
            color=COLOR_GOLD,
            z=-2,
        )

        # Streak
        self.streak_text = self._create_text(
            text='',
            position=(0.35, 0.39),
            scale=1.2,
            color=COLOR_STREAK,
            z=-2,
        )

        # Progress
        self.progress_text = self._create_text(
            text='',
            position=(-0.38, 0.44),
            scale=1.3,
            color=COLOR_TEXT_DIM,
            z=-2,
        )

        # Speed-round banner
        self.speed_banner = self._create_text(
            text='',
            position=(0, 0.37),
            scale=1.5,
            color=COLOR_SPEED_TEXT,
            z=-2,
        )

        # "Listen" label
        self.listen_label = self._create_text(
            text='What character is this?',
            position=(0, 0.27),
            scale=1.3,
            color=COLOR_TEXT_DIM,
            z=-2,
        )

        # Romaji display (big, prominent)
        self.romaji_display = self._create_text(
            text='',
            position=(0, 0.15),
            scale=7,
            color=COLOR_ROMAJI,
            z=-2,
        )

        # Pitch accent indicator
        self.pitch_display = self._create_text(
            text='',
            position=(0, 0.05),
            scale=2,
            color=COLOR_TEXT_DIM,
            z=-2,
        )

        # Answer buttons
        self.answer_buttons = []
        btn_w = min(0.16, 0.75 / self.num_choices)
        total_w = self.num_choices * btn_w + (self.num_choices - 1) * 0.015
        start_x = -total_w / 2 + btn_w / 2
        for i in range(self.num_choices):
            bx = start_x + i * (btn_w + 0.015)
            btn = self._create_button(
                text='',
                position=(bx, -0.1),
                scale=(btn_w, 0.09),
                z=-2,
            )
            btn._choice_index = i
            self.answer_buttons.append(btn)

        # Feedback label
        self.feedback_label = self._create_text(
            text='',
            position=(0, -0.23),
            scale=1.5,
            color=COLOR_TEXT,
            z=-2,
        )

        self._load_round()

    # ------------------------------------------------------------------
    # Per-item logic
    # ------------------------------------------------------------------
    def _load_round(self):
        if self.current_index >= len(self.queue):
            self._finish()
            return

        item = self.queue[self.current_index]
        self.current_item = item
        self.answered = False
        self.feedback_label.text = ''

        # Speed round check
        self.is_speed_round = (self.current_index >= self.speed_round_start)
        if self.is_speed_round:
            self.round_timer = self.speed_time
            self.speed_banner.text = '--- SPEED ROUND ---'
        else:
            self.round_timer = self.time_per_item
            self.speed_banner.text = ''

        # Display romaji
        romaji = item['romaji']
        self.romaji_display.text = romaji

        # Generate a simple pitch accent display
        self.pitch_display.text = self._generate_pitch_display(romaji)

        # Build choices
        correct = item['correct_character']
        wrong_pool = list(item.get('wrong_characters', []))
        # Supplement wrong answers from other items if needed
        if len(wrong_pool) < self.num_choices - 1:
            extra = [it['correct_character'] for it in self.all_items
                     if it['correct_character'] != correct
                     and it['correct_character'] not in wrong_pool]
            random.shuffle(extra)
            wrong_pool.extend(extra[:self.num_choices - 1 - len(wrong_pool)])
        while len(wrong_pool) < self.num_choices - 1:
            wrong_pool.append('?')

        wrong = random.sample(wrong_pool,
                              min(self.num_choices - 1, len(wrong_pool)))
        choices = wrong + [correct]
        random.shuffle(choices)
        self.correct_btn_idx = choices.index(correct)

        for i, btn in enumerate(self.answer_buttons):
            btn.text = choices[i]
            btn.color = COLOR_BUTTON
            btn.highlight_color = COLOR_BUTTON_HOVER
            btn.on_click = lambda idx=i: self._on_answer(idx)
            # Make text larger for Japanese characters
            if hasattr(btn, 'text_entity') and btn.text_entity:
                btn.text_entity.scale *= 1.0  # keep default

        # Update progress
        self.progress_text.text = \
            f'{self.current_index + 1} / {len(self.queue)}'

    def _generate_pitch_display(self, romaji):
        """Generate a simple pitch accent visualisation string."""
        # Simple heuristic pitch pattern for display
        vowels = set('aeiou')
        morae = []
        i = 0
        while i < len(romaji):
            if romaji[i] in vowels:
                morae.append(romaji[i])
                i += 1
            elif i + 1 < len(romaji) and romaji[i + 1] in vowels:
                morae.append(romaji[i:i + 2])
                i += 2
            else:
                morae.append(romaji[i])
                i += 1

        if len(morae) <= 1:
            return ''
        # Standard flat pattern with initial rise
        accents = []
        for j, m in enumerate(morae):
            if j == 0:
                accents.append(f'{m}')
            elif j == 1:
                accents.append(f'{m}')
            else:
                accents.append(f'{m}')
        return '  '.join(accents)

    # ------------------------------------------------------------------
    # Answer handling
    # ------------------------------------------------------------------
    def _on_answer(self, index):
        if self.answered or not self.is_active:
            return
        self.answered = True

        item = self.current_item
        is_correct = (index == self.correct_btn_idx)
        correct_char = item['correct_character']

        if is_correct:
            self.streak += 1
            # Speed round bonus
            speed_bonus = 5 if self.is_speed_round else 0
            points = 10 + speed_bonus
            self.score += points
            self.correct_items.append(
                f'{item["romaji"]} = {correct_char}')
            self.answer_buttons[index].color = COLOR_CORRECT
            self._show_result(True,
                              f'+{points}  {correct_char}',
                              duration=0.4)
        else:
            self.streak = 0
            self.score = max(0, self.score - 2)
            self.wrong_items.append(
                f'{item["romaji"]} = {correct_char} '
                f'(you: {self.answer_buttons[index].text})')
            self.answer_buttons[index].color = COLOR_WRONG
            self.answer_buttons[self.correct_btn_idx].color = COLOR_CORRECT
            self._shake_entity(self.answer_buttons[index])
            self.feedback_label.text = \
                f'Correct: {correct_char}'
            self.feedback_label.color = COLOR_WRONG
            self._show_result(False, correct_char, duration=0.4)

        self.score_text.text = f'Score: {self.score}'
        self._update_streak()

        delay = 0.5 if is_correct else 1.2
        if self.is_speed_round:
            delay *= 0.6  # faster transitions in speed round
        invoke(self._next_round, delay=delay)

    def _time_expired(self):
        if self.answered:
            return
        self.answered = True
        item = self.current_item
        correct_char = item['correct_character']
        self.streak = 0
        self.wrong_items.append(
            f'{item["romaji"]} = {correct_char} (time out)')
        self.answer_buttons[self.correct_btn_idx].color = COLOR_CORRECT
        self.feedback_label.text = f'Time up!  {correct_char}'
        self.feedback_label.color = COLOR_WRONG
        self._show_result(False, 'Time Up!', duration=0.4)
        self._update_streak()
        invoke(self._next_round, delay=1.0)

    def _next_round(self):
        if not self.is_active:
            return
        self.current_index += 1
        self._load_round()

    def _update_streak(self):
        if self.streak >= 3:
            self.streak_text.text = f'Streak: {self.streak}'
        else:
            self.streak_text.text = ''

    # ------------------------------------------------------------------
    # Finish
    # ------------------------------------------------------------------
    def _finish(self):
        # Streak bonus
        if self.streak >= 5:
            bonus = self.streak * 2
            self.score += bonus
            self.max_score += bonus
        self.complete()

    # ------------------------------------------------------------------
    # Frame update
    # ------------------------------------------------------------------
    def update(self):
        if not self.is_active or self.answered:
            return

        self.round_timer -= time.dt
        limit = self.speed_time if self.is_speed_round else self.time_per_item
        fraction = max(0, self.round_timer / limit)
        self._update_timer_bar(fraction)

        # Pulse effect on romaji during speed round
        if self.is_speed_round and hasattr(self, 'romaji_display'):
            pulse = 7 + math.sin(time.time() * 8) * 0.5
            self.romaji_display.scale = Vec2(pulse, pulse)

        if self.round_timer <= 0:
            self._time_expired()
