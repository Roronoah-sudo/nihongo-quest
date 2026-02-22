"""
quiz_game.py - Quiz Minigame
==============================

A multiple-choice quiz supporting grammar, vocabulary, and kanji questions.
Features a streak counter with score multipliers, an optional hint system,
a progress bar, and a detailed end-of-round review.

Lesson data format
------------------
    {
        'questions': [
            {
                'question': 'What does 食べる mean?',
                'correct_answer': 'to eat',
                'wrong_answers': ['to drink', 'to sleep', 'to run'],
                'hint': 'Related to food...',
                'explanation': '食べる (taberu) means "to eat".',
            },
            ...
        ]
    }

Difficulty scaling
------------------
    easy   : 15 questions, 15 s per question, hints free
    normal : 20 questions, 10 s per question, hints cost -5 pts
    hard   : 25 questions, 7 s per question, hints cost -10 pts
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


class QuizMinigame(BaseMinigame):
    """Multiple-choice quiz with streaks and detailed review."""

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------
    def setup(self):
        all_questions = list(self.lesson_data.get('questions', []))
        if not all_questions:
            self.complete()
            return

        # Difficulty
        self.num_questions = self._difficulty_value(15, 20, 25)
        self.time_per_q = self._difficulty_value(15, 10, 7)
        self.hint_penalty = self._difficulty_value(0, 5, 10)

        # Build queue
        if len(all_questions) >= self.num_questions:
            self.queue = random.sample(all_questions, self.num_questions)
        else:
            self.queue = (all_questions * math.ceil(
                self.num_questions / len(all_questions)))[:self.num_questions]

        self.current_index = 0
        self.max_score = self.num_questions * 10  # base (streaks can exceed)
        self.streak = 0
        self.best_streak = 0
        self.answered = False
        self.round_timer = 0.0
        self.review_data = []  # [{question, your_answer, correct_answer, correct}]

        # --- Persistent UI ---
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
            position=(0.35, 0.40),
            scale=1.2,
            color=COLOR_STREAK,
            z=-2,
        )

        # Progress bar background
        self.progress_bg = self._create_entity(
            parent=camera.ui,
            model='quad',
            color=color.rgb(40, 40, 55),
            scale=(0.6, 0.018),
            position=(0, 0.41),
            z=-1.5,
        )
        # Progress bar fill
        self.progress_fill = self._create_entity(
            parent=camera.ui,
            model='quad',
            color=COLOR_ACCENT,
            scale=(0.001, 0.014),
            position=(-0.3, 0.41),
            origin=(-0.5, 0),
            z=-2,
        )

        # Progress label
        self.progress_label = self._create_text(
            text='',
            position=(-0.38, 0.44),
            scale=1.2,
            color=COLOR_TEXT_DIM,
            z=-2,
        )

        # Question text
        self.question_text = self._create_text(
            text='',
            position=(0, 0.22),
            scale=2.2,
            color=COLOR_TEXT,
            z=-2,
            wordwrap=35,
        )

        # Answer buttons (always 4)
        self.answer_buttons = []
        for i in range(4):
            bx = -0.18 + (i % 2) * 0.36
            by = -0.05 - (i // 2) * 0.1
            btn = self._create_button(
                text='',
                position=(bx, by),
                scale=(0.34, 0.07),
                z=-2,
            )
            btn._choice_index = i
            self.answer_buttons.append(btn)

        # Hint button
        hint_label = 'Hint (free)' if self.hint_penalty == 0 else \
            f'Hint (-{self.hint_penalty}pts)'
        self.hint_btn = self._create_button(
            text=hint_label,
            position=(0, -0.3),
            scale=(0.22, 0.05),
            color=color.rgb(80, 70, 50),
            highlight_color=color.rgb(110, 100, 70),
            z=-2,
        )
        self.hint_btn.on_click = self._on_hint

        # Hint display
        self.hint_text = self._create_text(
            text='',
            position=(0, -0.37),
            scale=1.2,
            color=COLOR_TEXT_DIM,
            z=-2,
        )

        # Explanation text (shown after answering)
        self.explanation_text = self._create_text(
            text='',
            position=(0, -0.37),
            scale=1.1,
            color=COLOR_TEXT_DIM,
            z=-2,
            wordwrap=50,
        )

        # Start first question
        self._load_question()

    # ------------------------------------------------------------------
    # Per-question logic
    # ------------------------------------------------------------------
    def _load_question(self):
        if self.current_index >= len(self.queue):
            self._finish()
            return

        q = self.queue[self.current_index]
        self.current_q = q
        self.answered = False
        self.hint_shown = False
        self.round_timer = self.time_per_q

        # Update UI
        self.question_text.text = q['question']
        self.hint_text.text = ''
        self.explanation_text.text = ''
        self.hint_btn.enabled = True

        # Build choices
        wrong = list(q.get('wrong_answers', []))[:3]
        while len(wrong) < 3:
            wrong.append('---')
        choices = wrong + [q['correct_answer']]
        random.shuffle(choices)
        self.correct_btn_idx = choices.index(q['correct_answer'])

        for i, btn in enumerate(self.answer_buttons):
            btn.text = choices[i]
            btn.color = COLOR_BUTTON
            btn.highlight_color = COLOR_BUTTON_HOVER
            btn.on_click = lambda idx=i: self._on_answer(idx)

        # Progress
        frac = self.current_index / len(self.queue)
        self.progress_fill.scale_x = max(0.001, 0.6 * frac)
        self.progress_label.text = \
            f'Q {self.current_index + 1} / {len(self.queue)}'

    # ------------------------------------------------------------------
    # Answering
    # ------------------------------------------------------------------
    def _on_answer(self, index):
        if self.answered or not self.is_active:
            return
        self.answered = True
        self.hint_btn.enabled = False

        is_correct = (index == self.correct_btn_idx)
        q = self.current_q

        # Streak / scoring
        if is_correct:
            self.streak += 1
            if self.streak > self.best_streak:
                self.best_streak = self.streak
            multiplier = 1.0
            if self.streak >= 5:
                multiplier = 2.0
            elif self.streak >= 3:
                multiplier = 1.5
            points = int(10 * multiplier)
            self.score += points
            self.correct_items.append(
                f"{q['question']} -> {q['correct_answer']}")
            self.answer_buttons[index].color = COLOR_CORRECT
            self._show_result(True, f'+{points}', duration=0.45)
        else:
            self.streak = 0
            self.score = max(0, self.score - 2)
            self.wrong_items.append(
                f"{q['question']} -> {q['correct_answer']} "
                f"(you: {self.answer_buttons[index].text})")
            self.answer_buttons[index].color = COLOR_WRONG
            self.answer_buttons[self.correct_btn_idx].color = COLOR_CORRECT
            self._shake_entity(self.answer_buttons[index])
            self._show_result(False, q['correct_answer'], duration=0.45)

        # Show explanation
        expl = q.get('explanation', '')
        if expl:
            self.explanation_text.text = expl

        # Review record
        self.review_data.append({
            'question': q['question'],
            'your_answer': self.answer_buttons[index].text,
            'correct_answer': q['correct_answer'],
            'correct': is_correct,
        })

        # Update displays
        self.score_text.text = f'Score: {self.score}'
        self._update_streak_text()

        invoke(self._next_question, delay=1.2 if not is_correct else 0.6)

    def _on_hint(self):
        if self.answered or self.hint_shown or not self.is_active:
            return
        self.hint_shown = True
        self.hints_used += 1
        self.score = max(0, self.score - self.hint_penalty)
        self.score_text.text = f'Score: {self.score}'

        hint = self.current_q.get('hint', 'No hint available.')
        self.hint_text.text = f'Hint: {hint}'
        self.hint_btn.enabled = False

    def _time_expired(self):
        if self.answered:
            return
        self.answered = True
        q = self.current_q
        self.streak = 0
        self.wrong_items.append(
            f"{q['question']} -> {q['correct_answer']} (time out)")
        self.answer_buttons[self.correct_btn_idx].color = COLOR_CORRECT
        self._show_result(False, 'Time Up!', duration=0.5)
        self.review_data.append({
            'question': q['question'],
            'your_answer': '(no answer)',
            'correct_answer': q['correct_answer'],
            'correct': False,
        })
        self._update_streak_text()
        invoke(self._next_question, delay=1.2)

    def _next_question(self):
        if not self.is_active:
            return
        self.current_index += 1
        self._load_question()

    def _update_streak_text(self):
        if self.streak >= 3:
            mult = '2x' if self.streak >= 5 else '1.5x'
            self.streak_text.text = \
                f'Streak: {self.streak}  ({mult})'
        elif self.streak > 0:
            self.streak_text.text = f'Streak: {self.streak}'
        else:
            self.streak_text.text = ''

    # ------------------------------------------------------------------
    # Finish
    # ------------------------------------------------------------------
    def _finish(self):
        """Show detailed review, then the standard score card."""
        # The base class score card covers most of it;
        # we add bonus for best streak
        if self.best_streak >= 5:
            bonus = self.best_streak * 3
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
        fraction = max(0, self.round_timer / self.time_per_q)
        self._update_timer_bar(fraction)

        if self.round_timer <= 0:
            self._time_expired()
