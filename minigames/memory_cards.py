"""
memory_cards.py - Memory Card Minigame
=======================================

A classic flip-and-match memory game.  Cards are laid out in a grid;
each card is one half of a pair (Japanese <-> romaji / English).  The
player flips two cards at a time.  Matching pairs stay face-up.  The
game ends when every pair has been found.

Lesson data format
------------------
    {
        'pairs': [
            {'front': 'あ', 'back': 'a'},
            {'front': 'い', 'back': 'i'},
            ...
        ]
    }

Difficulty scaling
------------------
    easy   : 4x4 grid  (8 pairs)
    normal : 4x5 grid  (10 pairs)
    hard   : 5x6 grid  (15 pairs)
"""

from ursina import *
import random
import math

from .base_minigame import (
    BaseMinigame,
    COLOR_BG, COLOR_PANEL, COLOR_ACCENT, COLOR_CORRECT, COLOR_WRONG,
    COLOR_GOLD, COLOR_TEXT, COLOR_TEXT_DIM, COLOR_BUTTON, COLOR_BUTTON_HOVER,
    COLOR_CARD_BACK,
)


class MemoryCardsMinigame(BaseMinigame):
    """Flip-and-match memory card minigame."""

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------
    def setup(self):
        all_pairs = list(self.lesson_data.get('pairs', []))
        if not all_pairs:
            self.complete()
            return

        # Grid dimensions
        self.cols, self.rows = self._difficulty_value(
            (4, 4), (5, 4), (6, 5))
        num_pairs = (self.cols * self.rows) // 2

        # Select pairs (with repeats if necessary)
        if len(all_pairs) >= num_pairs:
            selected = random.sample(all_pairs, num_pairs)
        else:
            selected = (all_pairs * math.ceil(num_pairs / len(all_pairs)))[:num_pairs]

        # Build card list: two cards per pair (front and back)
        cards_data = []
        for idx, pair in enumerate(selected):
            cards_data.append({'text': pair['front'], 'pair_id': idx,
                               'side': 'front'})
            cards_data.append({'text': pair['back'],  'pair_id': idx,
                               'side': 'back'})
        random.shuffle(cards_data)

        # Scoring
        self.total_pairs = num_pairs
        self.max_score = num_pairs * 20
        self.pairs_found = 0

        # State
        self.flipped = []            # currently flipped card entities (max 2)
        self.matched_pairs = set()
        self.can_flip = True
        self.elapsed = 0.0

        # --- UI ---
        # Timer (counts up)
        self.timer_text = self._create_text(
            text='Time: 0s',
            position=(-0.38, 0.44),
            scale=1.3,
            color=COLOR_TEXT_DIM,
            z=-2,
        )

        # Score
        self.score_text = self._create_text(
            text=f'Pairs: 0 / {self.total_pairs}',
            position=(0.32, 0.44),
            scale=1.3,
            color=COLOR_GOLD,
            z=-2,
        )

        # Build card grid
        card_w = min(0.12, 0.85 / self.cols)
        card_h = card_w * 1.35
        gap = 0.012
        total_w = self.cols * (card_w + gap) - gap
        total_h = self.rows * (card_h + gap) - gap
        start_x = -total_w / 2 + card_w / 2
        start_y = total_h / 2 - card_h / 2 - 0.02  # shift down slightly

        self.card_entities = []
        for i, cd in enumerate(cards_data):
            col = i % self.cols
            row = i // self.cols
            cx = start_x + col * (card_w + gap)
            cy = start_y - row * (card_h + gap)

            # Card back (decorative)
            card = Button(
                parent=camera.ui,
                model='quad',
                scale=(card_w, card_h),
                position=(cx, cy),
                color=COLOR_CARD_BACK,
                highlight_color=color.rgb(210, 70, 70),
                radius=0.1,
                z=-2,
            )
            # Decorative pattern on back
            pattern = Text(
                text='NQ',
                parent=card,
                origin=(0, 0),
                scale=(3.5 / card_w, 3.5 / card_h),
                color=color.rgb(140, 35, 35),
                z=-0.01,
            )
            self.entities.append(pattern)

            # Hidden face text (revealed on flip)
            face_text = Text(
                text=cd['text'],
                parent=card,
                origin=(0, 0),
                scale=(4.5 / card_w, 4.5 / card_h),
                color=COLOR_TEXT,
                z=-0.01,
                enabled=False,
            )
            self.entities.append(face_text)

            # Store metadata on the entity
            card._card_data = cd
            card._face_text = face_text
            card._pattern = pattern
            card._is_flipped = False
            card._is_matched = False
            card._orig_color = COLOR_CARD_BACK
            card.on_click = lambda c=card: self._on_card_click(c)

            self.entities.append(card)
            self.card_entities.append(card)

    # ------------------------------------------------------------------
    # Card interaction
    # ------------------------------------------------------------------
    def _on_card_click(self, card):
        if not self.is_active or not self.can_flip:
            return
        if card._is_flipped or card._is_matched:
            return

        self._flip_card(card, face_up=True)
        self.flipped.append(card)

        if len(self.flipped) == 2:
            self.can_flip = False
            c1, c2 = self.flipped
            if c1._card_data['pair_id'] == c2._card_data['pair_id']:
                # Match!
                invoke(self._handle_match, c1, c2, delay=0.35)
            else:
                # No match
                invoke(self._handle_mismatch, c1, c2, delay=0.8)

    def _flip_card(self, card, face_up=True):
        """Animate a card flip by scaling x to 0, swapping content, then back."""
        card._is_flipped = face_up
        # Phase 1: scale x to 0
        card.animate_scale_x(0, duration=0.1, curve=curve.in_quad)
        invoke(lambda: self._flip_phase2(card, face_up), delay=0.1)

    def _flip_phase2(self, card, face_up):
        """Second half of the flip animation."""
        if card is None or not hasattr(card, '_face_text'):
            return
        if face_up:
            card._pattern.enabled = False
            card._face_text.enabled = True
            card.color = COLOR_PANEL
        else:
            card._pattern.enabled = True
            card._face_text.enabled = False
            card.color = COLOR_CARD_BACK
        card.animate_scale_x(card.scale_y / 1.35, duration=0.1,
                              curve=curve.out_quad)

    def _handle_match(self, c1, c2):
        """Two matching cards found."""
        c1._is_matched = True
        c2._is_matched = True
        c1.color = COLOR_CORRECT
        c2.color = COLOR_CORRECT
        c1.highlight_color = COLOR_CORRECT
        c2.highlight_color = COLOR_CORRECT

        self.score += 20
        self.pairs_found += 1
        pair = self.lesson_data['pairs'][c1._card_data['pair_id']] \
            if c1._card_data['pair_id'] < len(self.lesson_data['pairs']) else {}
        label = f"{pair.get('front', '')} = {pair.get('back', '')}"
        self.correct_items.append(label)

        self.score_text.text = f'Pairs: {self.pairs_found} / {self.total_pairs}'
        self._show_result(True, label, duration=0.4)

        self.flipped.clear()
        self.can_flip = True

        # Check for completion
        if self.pairs_found >= self.total_pairs:
            # Award time bonus
            time_bonus = max(0, int(300 - self.elapsed * 2))
            self.score += time_bonus
            self.max_score += time_bonus  # keep ratio fair
            invoke(self.complete, delay=0.6)

    def _handle_mismatch(self, c1, c2):
        """Two non-matching cards - flip them back."""
        self.score = max(0, self.score - 1)
        pair1_data = c1._card_data
        pair2_data = c2._card_data
        self.wrong_items.append(
            f'{pair1_data["text"]} != {pair2_data["text"]}')
        self._show_result(False, '', duration=0.3)

        self._flip_card(c1, face_up=False)
        self._flip_card(c2, face_up=False)
        self.flipped.clear()
        self.can_flip = True

    # ------------------------------------------------------------------
    # Frame update
    # ------------------------------------------------------------------
    def update(self):
        if not self.is_active:
            return
        self.elapsed += time.dt
        self.timer_text.text = f'Time: {int(self.elapsed)}s'
