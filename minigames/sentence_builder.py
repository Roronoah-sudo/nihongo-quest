"""
sentence_builder.py - Sentence Builder Minigame
=================================================

Given an English sentence, the player rearranges scrambled Japanese word
tiles into the correct order.  Tiles are clicked to move them between the
answer area and the pool.  Visual feedback highlights correct (green),
mis-positioned (yellow), and wrong (red) tiles upon checking.

Lesson data format
------------------
    {
        'sentences': [
            {
                'english': 'I eat sushi.',
                'japanese_words': ['私は', '寿司を', '食べます', '。'],
                'hint': 'Subject comes first.',
            },
            ...
        ]
    }

Difficulty scaling
------------------
    easy   : 10 sentences, hints free
    normal : 12 sentences, hints -5 pts
    hard   : 15 sentences, hints -10 pts, timer added
"""

from ursina import *
import random
import math
import copy

from .base_minigame import (
    BaseMinigame,
    COLOR_BG, COLOR_PANEL, COLOR_ACCENT, COLOR_CORRECT, COLOR_WRONG,
    COLOR_GOLD, COLOR_TEXT, COLOR_TEXT_DIM, COLOR_BUTTON, COLOR_BUTTON_HOVER,
)

COLOR_MISPLACED = color.rgb(230, 200, 50)
COLOR_TILE      = color.rgb(60, 60, 100)
COLOR_TILE_HL   = color.rgb(85, 85, 130)
COLOR_ANSWER_BG = color.rgb(40, 40, 60)


class SentenceBuilderMinigame(BaseMinigame):
    """Rearrange tiles to form the correct Japanese sentence."""

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------
    def setup(self):
        all_sentences = list(self.lesson_data.get('sentences', []))
        if not all_sentences:
            self.complete()
            return

        self.num_sentences = self._difficulty_value(10, 12, 15)
        self.hint_penalty = self._difficulty_value(0, 5, 10)
        self.use_timer = self.difficulty == 'hard'
        self.time_per_sentence = 30  # only used on hard

        if len(all_sentences) >= self.num_sentences:
            self.queue = random.sample(all_sentences, self.num_sentences)
        else:
            self.queue = (all_sentences * math.ceil(
                self.num_sentences / len(all_sentences)))[:self.num_sentences]

        self.current_index = 0
        self.max_score = self.num_sentences * 10
        self.round_timer = 0.0

        # Dynamic entities (rebuilt each sentence)
        self.pool_tiles = []     # tiles in the bottom pool
        self.answer_tiles = []   # tiles placed in the answer area
        self.tile_entities = {}  # word -> entity mapping

        # --- Persistent UI ---
        if self.use_timer:
            self._create_timer_bar()

        # Score
        self.score_text = self._create_text(
            text='Score: 0',
            position=(0.35, 0.44),
            scale=1.5,
            color=COLOR_GOLD,
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

        # English sentence
        self.english_text = self._create_text(
            text='',
            position=(0, 0.33),
            scale=1.8,
            color=COLOR_ACCENT,
            z=-2,
            wordwrap=40,
        )

        # Answer area background
        self.answer_area_bg = self._create_entity(
            parent=camera.ui,
            model='quad',
            color=COLOR_ANSWER_BG,
            scale=(0.85, 0.08),
            position=(0, 0.15),
            z=-1.5,
        )

        # Label above answer area
        self._create_text(
            text='Your answer:',
            position=(-0.38, 0.21),
            scale=1.0,
            color=COLOR_TEXT_DIM,
            z=-2,
        )

        # Hint button
        hint_label = 'Hint (free)' if self.hint_penalty == 0 else \
            f'Hint (-{self.hint_penalty}pts)'
        self.hint_btn = self._create_button(
            text=hint_label,
            position=(-0.25, -0.35),
            scale=(0.2, 0.05),
            color=color.rgb(80, 70, 50),
            highlight_color=color.rgb(110, 100, 70),
            z=-2,
        )
        self.hint_btn.on_click = self._on_hint

        # Check button
        self.check_btn = self._create_button(
            text='Check',
            position=(0.05, -0.35),
            scale=(0.2, 0.05),
            color=COLOR_ACCENT,
            highlight_color=color.rgb(170, 200, 255),
            z=-2,
        )
        self.check_btn.on_click = self._on_check

        # Clear button
        self.clear_btn = self._create_button(
            text='Clear',
            position=(0.28, -0.35),
            scale=(0.15, 0.05),
            color=color.rgb(100, 55, 55),
            highlight_color=color.rgb(140, 75, 75),
            z=-2,
        )
        self.clear_btn.on_click = self._on_clear

        # Hint text
        self.hint_text = self._create_text(
            text='',
            position=(0, -0.42),
            scale=1.1,
            color=COLOR_TEXT_DIM,
            z=-2,
        )

        # Feedback text
        self.feedback_text = self._create_text(
            text='',
            position=(0, 0.07),
            scale=1.3,
            color=COLOR_TEXT,
            z=-2,
        )

        self._load_sentence()

    # ------------------------------------------------------------------
    # Per-sentence
    # ------------------------------------------------------------------
    def _load_sentence(self):
        if self.current_index >= len(self.queue):
            self.complete()
            return

        s = self.queue[self.current_index]
        self.current_sentence = s
        self.correct_order = list(s['japanese_words'])
        self.hint_shown = False
        self.checked = False
        self.round_timer = self.time_per_sentence if self.use_timer else 0

        # Clear previous tile entities
        self._clear_tiles()

        self.answer_tiles = []
        self.pool_tiles = list(range(len(self.correct_order)))
        random.shuffle(self.pool_tiles)

        # Update text
        self.english_text.text = s['english']
        self.hint_text.text = ''
        self.feedback_text.text = ''
        self.progress_text.text = \
            f'{self.current_index + 1} / {len(self.queue)}'

        # Create tile buttons
        self.tile_entities = {}
        self._layout_tiles()

    def _clear_tiles(self):
        """Remove all tile entities."""
        for idx, ent in list(self.tile_entities.items()):
            if ent in self.entities:
                self.entities.remove(ent)
            destroy(ent)
        self.tile_entities.clear()

    def _layout_tiles(self):
        """Create / reposition tiles in pool and answer areas."""
        # Remove old tile entities
        self._clear_tiles()

        tile_h = 0.055
        gap = 0.01

        # --- Answer area tiles (top row) ---
        if self.answer_tiles:
            total_w = sum(self._tile_width(i) + gap
                          for i in self.answer_tiles) - gap
            sx = -total_w / 2
            for idx in self.answer_tiles:
                tw = self._tile_width(idx)
                btn = Button(
                    parent=camera.ui,
                    text=self.correct_order[idx],
                    scale=(tw, tile_h),
                    position=(sx + tw / 2, 0.15),
                    color=COLOR_TILE,
                    highlight_color=COLOR_TILE_HL,
                    text_color=COLOR_TEXT,
                    radius=0.15,
                    z=-3,
                )
                btn.on_click = lambda i=idx: self._remove_from_answer(i)
                self.entities.append(btn)
                self.tile_entities[idx] = btn
                sx += tw + gap

        # --- Pool tiles (bottom area, multi-row) ---
        max_row_w = 0.8
        rows = self._wrap_tiles(self.pool_tiles, max_row_w, gap)
        for r_idx, row in enumerate(rows):
            row_w = sum(self._tile_width(i) + gap for i in row) - gap
            sx = -row_w / 2
            for idx in row:
                tw = self._tile_width(idx)
                by = -0.1 - r_idx * (tile_h + gap)
                btn = Button(
                    parent=camera.ui,
                    text=self.correct_order[idx],
                    scale=(tw, tile_h),
                    position=(sx + tw / 2, by),
                    color=COLOR_TILE,
                    highlight_color=COLOR_TILE_HL,
                    text_color=COLOR_TEXT,
                    radius=0.15,
                    z=-3,
                )
                btn.on_click = lambda i=idx: self._add_to_answer(i)
                self.entities.append(btn)
                self.tile_entities[idx] = btn
                sx += tw + gap

    def _tile_width(self, idx):
        """Calculate tile width based on text length."""
        txt = self.correct_order[idx]
        return max(0.07, len(txt) * 0.025 + 0.03)

    def _wrap_tiles(self, indices, max_w, gap):
        """Wrap a list of tile indices into rows that fit max_w."""
        rows = []
        current_row = []
        current_w = 0
        for idx in indices:
            tw = self._tile_width(idx) + gap
            if current_w + tw > max_w + gap and current_row:
                rows.append(current_row)
                current_row = [idx]
                current_w = tw
            else:
                current_row.append(idx)
                current_w += tw
        if current_row:
            rows.append(current_row)
        return rows

    # ------------------------------------------------------------------
    # Tile interaction
    # ------------------------------------------------------------------
    def _add_to_answer(self, idx):
        if self.checked or not self.is_active:
            return
        if idx in self.pool_tiles:
            self.pool_tiles.remove(idx)
            self.answer_tiles.append(idx)
            self._layout_tiles()

    def _remove_from_answer(self, idx):
        if self.checked or not self.is_active:
            return
        if idx in self.answer_tiles:
            self.answer_tiles.remove(idx)
            self.pool_tiles.append(idx)
            self._layout_tiles()

    def _on_clear(self):
        if self.checked or not self.is_active:
            return
        self.pool_tiles = self.pool_tiles + self.answer_tiles
        self.answer_tiles = []
        self._layout_tiles()

    # ------------------------------------------------------------------
    # Checking
    # ------------------------------------------------------------------
    def _on_check(self):
        if self.checked or not self.is_active:
            return
        if len(self.answer_tiles) != len(self.correct_order):
            self.feedback_text.text = 'Place all tiles first!'
            self.feedback_text.color = COLOR_WRONG
            return

        self.checked = True
        player_order = [self.correct_order[i] for i in self.answer_tiles]
        correct_list = list(self.correct_order)
        is_perfect = (player_order == correct_list)

        # Colour each tile
        for pos, idx in enumerate(self.answer_tiles):
            ent = self.tile_entities.get(idx)
            if ent is None:
                continue
            if self.correct_order[idx] == correct_list[pos]:
                ent.color = COLOR_CORRECT            # right word, right place
            elif self.correct_order[idx] in correct_list:
                ent.color = COLOR_MISPLACED          # right word, wrong place
            else:
                ent.color = COLOR_WRONG              # shouldn't happen

        sent_str = ' '.join(correct_list)
        if is_perfect:
            self.score += 10
            self.correct_items.append(sent_str)
            self._show_result(True, '', duration=0.5)
            self.feedback_text.text = 'Perfect!'
            self.feedback_text.color = COLOR_CORRECT
        else:
            self.score = max(0, self.score - 2)
            self.wrong_items.append(sent_str)
            self._show_result(False, '', duration=0.5)
            self.feedback_text.text = f'Correct: {sent_str}'
            self.feedback_text.color = COLOR_WRONG

        self.score_text.text = f'Score: {self.score}'
        invoke(self._next_sentence, delay=1.8 if not is_perfect else 0.8)

    def _next_sentence(self):
        if not self.is_active:
            return
        self.current_index += 1
        self._load_sentence()

    # ------------------------------------------------------------------
    # Hint
    # ------------------------------------------------------------------
    def _on_hint(self):
        if self.hint_shown or self.checked or not self.is_active:
            return
        self.hint_shown = True
        self.hints_used += 1
        self.score = max(0, self.score - self.hint_penalty)
        self.score_text.text = f'Score: {self.score}'

        # Show textual hint
        hint = self.current_sentence.get('hint', '')
        first_word = self.correct_order[0]
        if hint:
            self.hint_text.text = f'Hint: {hint}  |  First word: {first_word}'
        else:
            self.hint_text.text = f'Hint: First word is  {first_word}'

        # Highlight the first-word tile in the pool
        target_idx = self.correct_order.index(first_word) \
            if first_word in self.correct_order else 0
        ent = self.tile_entities.get(target_idx)
        if ent:
            ent.color = COLOR_ACCENT

    # ------------------------------------------------------------------
    # Timer (hard mode only)
    # ------------------------------------------------------------------
    def _time_expired(self):
        if self.checked:
            return
        self.checked = True
        sent_str = ' '.join(self.correct_order)
        self.wrong_items.append(f'{sent_str} (time out)')
        self.feedback_text.text = f'Time up!  {sent_str}'
        self.feedback_text.color = COLOR_WRONG
        self._show_result(False, 'Time Up!', duration=0.5)
        invoke(self._next_sentence, delay=1.5)

    # ------------------------------------------------------------------
    # Frame update
    # ------------------------------------------------------------------
    def update(self):
        if not self.is_active:
            return
        if self.use_timer and not self.checked:
            self.round_timer -= time.dt
            frac = max(0, self.round_timer / self.time_per_sentence)
            self._update_timer_bar(frac)
            if self.round_timer <= 0:
                self._time_expired()
