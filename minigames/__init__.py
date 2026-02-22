"""
Nihongo Quest - Minigame Framework
===================================
A collection of educational minigames for learning Japanese.

Available minigames:
    - CharacterMatchMinigame: Match Japanese characters to romaji
    - MemoryCardsMinigame: Flip-and-match memory card game
    - QuizMinigame: Multiple-choice quiz with streaks
    - TypingChallengeMinigame: Type romaji as words fall
    - SentenceBuilderMinigame: Arrange tiles into correct sentences
    - ListeningMinigame: Identify characters from romaji pronunciation
"""

from .base_minigame import BaseMinigame
from .character_match import CharacterMatchMinigame
from .memory_cards import MemoryCardsMinigame
from .quiz_game import QuizMinigame
from .typing_challenge import TypingChallengeMinigame
from .sentence_builder import SentenceBuilderMinigame
from .listening_game import ListeningMinigame

__all__ = [
    'BaseMinigame',
    'CharacterMatchMinigame',
    'MemoryCardsMinigame',
    'QuizMinigame',
    'TypingChallengeMinigame',
    'SentenceBuilderMinigame',
    'ListeningMinigame',
]
