"""
lesson_select.py - Lesson Selection Screen
============================================

Displayed when the player enters a monument in the overworld.  Shows all
available lessons for that monument, their completion status, star ratings,
and the minigame types available for each lesson.

Clicking a minigame icon launches the corresponding minigame with the
lesson's content.

Public interface
----------------
    screen = LessonSelectScreen()
    screen.show(monument_id, save_data)
    screen.hide()
"""

from ursina import *

from minigames.character_match import CharacterMatchMinigame
from minigames.memory_cards import MemoryCardsMinigame
from minigames.quiz_game import QuizMinigame
from minigames.typing_challenge import TypingChallengeMinigame
from minigames.sentence_builder import SentenceBuilderMinigame
from minigames.listening_game import ListeningMinigame

from content.hiragana import (
    HIRAGANA_BASIC, HIRAGANA_DAKUTEN, HIRAGANA_COMBOS, HIRAGANA_LESSONS,
    HIRAGANA_HANDAKUTEN,
)
from content.katakana import (
    KATAKANA_BASIC, KATAKANA_DAKUTEN, KATAKANA_HANDAKUTEN,
    KATAKANA_COMBOS, KATAKANA_LESSONS,
)
from content.vocabulary import (
    GREETINGS, NUMBERS, COMMON_NOUNS, COMMON_VERBS, COMMON_ADJECTIVES,
    JLPT_N5_VOCAB, VOCABULARY_LESSONS,
)
from content.grammar import (
    BASIC_GRAMMAR, INTERMEDIATE_GRAMMAR, ADVANCED_GRAMMAR,
    VERB_CONJUGATION, GRAMMAR_LESSONS,
)

try:
    from content.kanji import KANJI_N5, KANJI_INTERMEDIATE, KANJI_LESSONS
    HAS_KANJI = True
except ImportError:
    HAS_KANJI = False
    KANJI_N5 = {}
    KANJI_INTERMEDIATE = {}
    KANJI_LESSONS = []


# ---------------------------------------------------------------------------
# Monument ID -> string key mapping
# ---------------------------------------------------------------------------
MONUMENT_KEY_MAP = {
    0: 'hiragana',
    1: 'katakana',
    2: 'grammar_basic',
    3: 'vocabulary',
    4: 'verb_conjugation',
    5: 'kanji_n5',
    6: 'listening',
    7: 'grammar_intermediate',
    8: 'kanji_intermediate',
    9: 'reading',
    10: 'conversation',
    11: 'grammar_advanced',
    12: 'immersion',
}


# ---------------------------------------------------------------------------
# Colour palette (consistent with minigame base)
# ---------------------------------------------------------------------------
COLOR_BG           = color.rgb(25, 25, 40)
COLOR_PANEL        = color.rgb(42, 42, 62)
COLOR_PANEL_HOVER  = color.rgb(55, 55, 80)
COLOR_ACCENT       = color.rgb(137, 180, 250)
COLOR_GOLD         = color.rgb(255, 215, 0)
COLOR_TEXT          = color.rgb(230, 230, 250)
COLOR_TEXT_DIM      = color.rgb(150, 150, 170)
COLOR_BUTTON        = color.rgb(60, 60, 90)
COLOR_BUTTON_HOVER  = color.rgb(80, 80, 120)
COLOR_CORRECT       = color.rgb(80, 200, 120)
COLOR_PROGRESS_BG   = color.rgb(40, 40, 55)
COLOR_PROGRESS_FILL = color.rgb(100, 180, 250)
COLOR_LOCKED        = color.rgb(80, 80, 80)
COLOR_STAR_FILLED   = color.rgb(255, 215, 0)
COLOR_STAR_EMPTY    = color.rgb(60, 60, 80)

# Minigame type icons (text labels used as simple "icons")
MINIGAME_TYPES = {
    'match':   {'label': 'Match',  'color': color.rgb(120, 180, 255),
                'class': CharacterMatchMinigame},
    'memory':  {'label': 'Memory', 'color': color.rgb(180, 130, 255),
                'class': MemoryCardsMinigame},
    'quiz':    {'label': 'Quiz',   'color': color.rgb(130, 220, 170),
                'class': QuizMinigame},
    'type':    {'label': 'Type',   'color': color.rgb(255, 180, 120),
                'class': TypingChallengeMinigame},
    'build':   {'label': 'Build',  'color': color.rgb(255, 220, 100),
                'class': SentenceBuilderMinigame},
    'listen':  {'label': 'Listen', 'color': color.rgb(255, 140, 160),
                'class': ListeningMinigame},
}


# ---------------------------------------------------------------------------
# Helper functions for converting content data to minigame data
# ---------------------------------------------------------------------------

def _pad_wrong(answers, minimum=3):
    """Ensure *answers* has at least *minimum* entries, padding with 'N/A'."""
    result = list(answers)
    while len(result) < minimum:
        result.append('N/A')
    return result[:minimum]


def _chars_to_lesson_data(char_dict, keys):
    """Convert a subset of character dict entries to minigame data format."""
    chars = []
    pairs = []
    items = []
    for key in keys:
        entry = char_dict.get(key)
        if not entry:
            continue
        c = entry['character']
        r = entry['romaji']
        chars.append({'character': c, 'romaji': r})
        pairs.append({'front': c, 'back': r})
        items.append({'display': c, 'answer': r, 'alt_answers': []})
    return {'characters': chars, 'pairs': pairs, 'items': items}


def _vocab_to_lesson_data(words):
    """Convert vocabulary entries to minigame data."""
    questions = []
    pairs = []
    items = []
    for w in words:
        jp = w.get('japanese', '')
        en = w.get('english', w.get('meaning', ''))
        rom = w.get('romaji', '')
        pairs.append({'front': jp, 'back': en})
        items.append({'display': jp, 'answer': rom, 'alt_answers': []})
        # Generate quiz question
        other_meanings = [ow.get('english', ow.get('meaning', ''))
                          for ow in words if ow != w][:3]
        if len(other_meanings) >= 3:
            questions.append({
                'question': f'What does {jp} mean?',
                'correct_answer': en,
                'wrong_answers': _pad_wrong(other_meanings),
                'hint': f'Pronounced: {rom}',
                'explanation': f'{jp} ({rom}) = {en}',
            })
    return {'questions': questions, 'pairs': pairs, 'items': items}


def _grammar_to_lesson_data(grammar_points):
    """Convert grammar points to quiz questions and sentences."""
    questions = []
    sentences = []
    all_examples = [(gp, ex)
                    for gp in grammar_points
                    for ex in gp.get('examples', [])]
    for gp in grammar_points:
        for ex in gp.get('examples', []):
            wrong = [other_ex['japanese']
                     for other_gp in grammar_points
                     for other_ex in other_gp.get('examples', [])
                     if other_ex['japanese'] != ex['japanese']][:3]
            wrong = _pad_wrong(wrong)
            explanation_text = gp.get('explanation', '')
            questions.append({
                'question': f'Translate: {ex["english"]}',
                'correct_answer': ex['japanese'],
                'wrong_answers': wrong,
                'hint': gp.get('pattern', ''),
                'explanation': f'{gp["title"]}: {explanation_text[:60]}...',
            })
            # Build sentence data from example
            words = ex['japanese'].replace('\u3002', ' \u3002').split()
            if len(words) >= 2:
                sentences.append({
                    'english': ex['english'],
                    'japanese_words': words,
                    'hint': gp.get('pattern', ''),
                })
    return {'questions': questions, 'sentences': sentences}


# ---------------------------------------------------------------------------
# Build comprehensive monument data from content modules
# ---------------------------------------------------------------------------

def _build_monument_data():
    """Generate the full MONUMENT_DATA dict from content modules."""
    data = {}

    # -----------------------------------------------------------------------
    # Monument 0 - Hiragana
    # -----------------------------------------------------------------------
    all_hira = {}
    all_hira.update(HIRAGANA_BASIC)
    all_hira.update(HIRAGANA_DAKUTEN)
    all_hira.update(HIRAGANA_HANDAKUTEN)
    all_hira.update(HIRAGANA_COMBOS)

    hira_lessons = []
    for ldef in HIRAGANA_LESSONS:
        keys = ldef['characters_taught']
        ld = _chars_to_lesson_data(all_hira, keys)
        hira_lessons.append({
            'id': ldef['lesson_id'],
            'title': ldef['title'],
            'description': ldef['description'],
            'minigame_types': ['match', 'memory', 'type', 'listen'],
            'data': ld,
        })

    data['hiragana'] = {
        'title_jp': '\u3072\u3089\u304c\u306a\u306e\u5854',
        'title_en': 'Hiragana Tower',
        'lessons': hira_lessons,
    }

    # -----------------------------------------------------------------------
    # Monument 1 - Katakana
    # -----------------------------------------------------------------------
    all_kata = {}
    all_kata.update(KATAKANA_BASIC)
    all_kata.update(KATAKANA_DAKUTEN)
    all_kata.update(KATAKANA_HANDAKUTEN)
    all_kata.update(KATAKANA_COMBOS)

    kata_lessons = []
    for ldef in KATAKANA_LESSONS:
        keys = ldef['characters_taught']
        ld = _chars_to_lesson_data(all_kata, keys)
        kata_lessons.append({
            'id': ldef['lesson_id'],
            'title': ldef['title'],
            'description': ldef['description'],
            'minigame_types': ['match', 'memory', 'type', 'listen'],
            'data': ld,
        })

    data['katakana'] = {
        'title_jp': '\u30ab\u30bf\u30ab\u30ca\u306e\u5854',
        'title_en': 'Katakana Tower',
        'lessons': kata_lessons,
    }

    # -----------------------------------------------------------------------
    # Monument 2 - Grammar Basic
    # -----------------------------------------------------------------------
    basic_grammar_lessons = []
    for ldef in GRAMMAR_LESSONS:
        if ldef.get('monument_id') != 2:
            continue
        # Resolve grammar point objects
        gp_ids = ldef.get('grammar_points', [])
        gps = [gp for gp in BASIC_GRAMMAR if gp['id'] in gp_ids]
        if not gps:
            continue
        ld = _grammar_to_lesson_data(gps)
        basic_grammar_lessons.append({
            'id': ldef['lesson_id'],
            'title': ldef['title'],
            'description': ldef['description'],
            'minigame_types': ['quiz', 'build'],
            'data': ld,
        })

    data['grammar_basic'] = {
        'title_jp': '\u6587\u6cd5\u306e\u57ce',
        'title_en': 'Grammar Castle',
        'lessons': basic_grammar_lessons,
    }

    # -----------------------------------------------------------------------
    # Monument 3 - Vocabulary
    # -----------------------------------------------------------------------
    vocab_lessons = []

    # Greetings lessons
    greetings_data = _vocab_to_lesson_data(GREETINGS[:11])
    vocab_lessons.append({
        'id': 'vocab_greetings_1',
        'title': 'Essential Greetings',
        'description': 'Learn the most common Japanese greetings.',
        'minigame_types': ['quiz', 'type', 'memory'],
        'data': greetings_data,
    })
    if len(GREETINGS) > 11:
        greetings_data_2 = _vocab_to_lesson_data(GREETINGS[11:])
        vocab_lessons.append({
            'id': 'vocab_greetings_2',
            'title': 'More Greetings & Expressions',
            'description': 'Everyday expressions and social phrases.',
            'minigame_types': ['quiz', 'type', 'memory'],
            'data': greetings_data_2,
        })

    # Nouns by category
    for cat_key, cat_words in COMMON_NOUNS.items():
        cat_title = cat_key.replace('_', ' ').title()
        vdata = _vocab_to_lesson_data(cat_words)
        vocab_lessons.append({
            'id': f'vocab_nouns_{cat_key}',
            'title': f'Nouns: {cat_title}',
            'description': f'Learn {cat_title.lower()}-related vocabulary.',
            'minigame_types': ['quiz', 'type', 'memory'],
            'data': vdata,
        })

    # Verbs (split into two groups)
    mid = len(COMMON_VERBS) // 2
    verbs_1 = [{'japanese': v['dictionary_form'], 'romaji': v.get('masu_form', ''),
                'english': v['meaning']} for v in COMMON_VERBS[:mid]]
    verbs_2 = [{'japanese': v['dictionary_form'], 'romaji': v.get('masu_form', ''),
                'english': v['meaning']} for v in COMMON_VERBS[mid:]]
    vocab_lessons.append({
        'id': 'vocab_verbs_1',
        'title': 'Essential Verbs (Part 1)',
        'description': 'Learn the most important action words.',
        'minigame_types': ['quiz', 'type', 'memory'],
        'data': _vocab_to_lesson_data(verbs_1),
    })
    vocab_lessons.append({
        'id': 'vocab_verbs_2',
        'title': 'Essential Verbs (Part 2)',
        'description': 'More everyday verbs to expand your vocabulary.',
        'minigame_types': ['quiz', 'type', 'memory'],
        'data': _vocab_to_lesson_data(verbs_2),
    })

    # Adjectives
    i_adj = [{'japanese': a['japanese'], 'romaji': a['romaji'],
              'english': a['english']}
             for a in COMMON_ADJECTIVES.get('i_adjectives', [])]
    na_adj = [{'japanese': a['japanese'], 'romaji': a['romaji'],
               'english': a['english']}
              for a in COMMON_ADJECTIVES.get('na_adjectives', [])]
    if i_adj:
        vocab_lessons.append({
            'id': 'vocab_i_adj',
            'title': 'I-Adjectives',
            'description': 'Descriptive words ending in -i.',
            'minigame_types': ['quiz', 'type', 'memory'],
            'data': _vocab_to_lesson_data(i_adj),
        })
    if na_adj:
        vocab_lessons.append({
            'id': 'vocab_na_adj',
            'title': 'Na-Adjectives',
            'description': 'Descriptive words that use na before nouns.',
            'minigame_types': ['quiz', 'type', 'memory'],
            'data': _vocab_to_lesson_data(na_adj),
        })

    # JLPT N5 (split into chunks of ~20)
    chunk_size = 20
    for ci, start in enumerate(range(0, len(JLPT_N5_VOCAB), chunk_size)):
        chunk = JLPT_N5_VOCAB[start:start + chunk_size]
        vocab_lessons.append({
            'id': f'vocab_n5_{ci + 1}',
            'title': f'JLPT N5 Vocab (Set {ci + 1})',
            'description': f'Essential words for the JLPT N5 exam (set {ci + 1}).',
            'minigame_types': ['quiz', 'type', 'memory'],
            'data': _vocab_to_lesson_data(chunk),
        })

    data['vocabulary'] = {
        'title_jp': '\u8a9e\u5f59\u306e\u795e\u6bbf',
        'title_en': 'Vocabulary Shrine',
        'lessons': vocab_lessons,
    }

    # -----------------------------------------------------------------------
    # Monument 4 - Verb Conjugation
    # -----------------------------------------------------------------------
    conj_lessons = []
    # Build lessons from COMMON_VERBS grouped by verb type
    verb_groups = {}
    for v in COMMON_VERBS:
        vtype = v.get('verb_type', 'other')
        verb_groups.setdefault(vtype, []).append(v)

    for vtype, verbs in verb_groups.items():
        type_label = vtype.title()
        questions = []
        items = []
        for v in verbs:
            dict_form = v['dictionary_form']
            meaning = v['meaning']
            # masu-form question
            other_masu = [ov['masu_form'] for ov in verbs if ov != v][:3]
            questions.append({
                'question': f'What is the masu-form of {dict_form} ({meaning})?',
                'correct_answer': v['masu_form'],
                'wrong_answers': _pad_wrong(other_masu),
                'hint': f'Verb type: {vtype}',
                'explanation': f'{dict_form} -> {v["masu_form"]}',
            })
            # te-form question
            other_te = [ov['te_form'] for ov in verbs if ov != v][:3]
            questions.append({
                'question': f'What is the te-form of {dict_form} ({meaning})?',
                'correct_answer': v['te_form'],
                'wrong_answers': _pad_wrong(other_te),
                'hint': f'Verb type: {vtype}',
                'explanation': f'{dict_form} -> {v["te_form"]}',
            })
            # past-form question
            other_past = [ov['past_form'] for ov in verbs if ov != v][:3]
            questions.append({
                'question': f'What is the past form of {dict_form} ({meaning})?',
                'correct_answer': v['past_form'],
                'wrong_answers': _pad_wrong(other_past),
                'hint': f'Verb type: {vtype}',
                'explanation': f'{dict_form} -> {v["past_form"]}',
            })
            items.append({
                'display': f'{dict_form} (masu)',
                'answer': v['masu_form'],
                'alt_answers': [],
            })
            items.append({
                'display': f'{dict_form} (te)',
                'answer': v['te_form'],
                'alt_answers': [],
            })

        conj_lessons.append({
            'id': f'conj_{vtype}',
            'title': f'{type_label} Verb Conjugation',
            'description': f'Practice conjugating {vtype} verbs.',
            'minigame_types': ['quiz', 'type'],
            'data': {'questions': questions, 'items': items},
        })

    data['verb_conjugation'] = {
        'title_jp': '\u52d5\u8a5e\u306e\u9053\u5834',
        'title_en': 'Verb Dojo',
        'lessons': conj_lessons,
    }

    # -----------------------------------------------------------------------
    # Monument 5 - Kanji N5
    # -----------------------------------------------------------------------
    kanji_n5_lessons = []
    if HAS_KANJI and KANJI_N5:
        kanji_keys = list(KANJI_N5.keys())
        group_size = 8
        for ci, start in enumerate(range(0, len(kanji_keys), group_size)):
            group_keys = kanji_keys[start:start + group_size]
            chars = []
            pairs = []
            questions = []
            for kk in group_keys:
                entry = KANJI_N5[kk]
                kanji_char = entry.get('character', kk)
                # Extract reading from readings_kun or readings_on
                reading = (entry.get('readings_kun', ['']) or [''])[0]
                if not reading:
                    reading = (entry.get('readings_on', ['']) or [''])[0]
                meaning = entry.get('meaning', '')
                chars.append({'character': kanji_char, 'romaji': reading})
                pairs.append({'front': kanji_char, 'back': meaning})
                # quiz question
                other_meanings = [KANJI_N5[ok].get('meaning', '')
                                  for ok in kanji_keys if ok != kk][:3]
                questions.append({
                    'question': f'What does {kanji_char} mean?',
                    'correct_answer': meaning,
                    'wrong_answers': _pad_wrong(other_meanings),
                    'hint': f'Reading: {reading}',
                    'explanation': f'{kanji_char} = {meaning} ({reading})',
                })
            kanji_n5_lessons.append({
                'id': f'kanji_n5_{ci + 1}',
                'title': f'Kanji N5 (Set {ci + 1})',
                'description': f'Learn kanji characters (set {ci + 1}).',
                'minigame_types': ['match', 'memory', 'quiz'],
                'data': {'characters': chars, 'pairs': pairs, 'questions': questions},
            })
    else:
        # Placeholder if kanji module not available
        kanji_n5_lessons.append({
            'id': 'kanji_n5_placeholder',
            'title': 'Kanji N5 (Coming Soon)',
            'description': 'Kanji content is being prepared.',
            'minigame_types': ['quiz'],
            'data': {'questions': [{
                'question': 'Kanji content coming soon!',
                'correct_answer': 'OK',
                'wrong_answers': ['N/A', 'N/A', 'N/A'],
                'hint': '',
                'explanation': 'Kanji lessons are being developed.',
            }]},
        })

    data['kanji_n5'] = {
        'title_jp': '\u6f22\u5b57N5\u306e\u5bae',
        'title_en': 'Kanji N5 Shrine',
        'lessons': kanji_n5_lessons,
    }

    # -----------------------------------------------------------------------
    # Monument 6 - Listening
    # -----------------------------------------------------------------------
    listen_lessons = []

    # Listening: Hiragana basic sounds
    hira_vowels = _chars_to_lesson_data(HIRAGANA_BASIC,
                                        ['a', 'i', 'u', 'e', 'o'])
    listen_lessons.append({
        'id': 'listen_hira_vowels',
        'title': 'Hiragana Vowel Sounds',
        'description': 'Identify hiragana vowels from their pronunciation.',
        'minigame_types': ['listen', 'match'],
        'data': hira_vowels,
    })

    # Listening: Hiragana consonant rows
    hira_rows = {
        'k': ['ka', 'ki', 'ku', 'ke', 'ko'],
        's': ['sa', 'shi', 'su', 'se', 'so'],
        't': ['ta', 'chi', 'tsu', 'te', 'to'],
        'n': ['na', 'ni', 'nu', 'ne', 'no'],
        'h': ['ha', 'hi', 'fu', 'he', 'ho'],
        'm': ['ma', 'mi', 'mu', 'me', 'mo'],
        'r': ['ra', 'ri', 'ru', 're', 'ro'],
    }
    for row_name, row_keys in hira_rows.items():
        ld = _chars_to_lesson_data(HIRAGANA_BASIC, row_keys)
        listen_lessons.append({
            'id': f'listen_hira_{row_name}',
            'title': f'Hiragana {row_name.upper()}-Row Sounds',
            'description': f'Identify {row_name}-row hiragana from pronunciation.',
            'minigame_types': ['listen', 'match'],
            'data': ld,
        })

    # Listening: Katakana vowels
    kata_vowels = _chars_to_lesson_data(KATAKANA_BASIC,
                                        ['a', 'i', 'u', 'e', 'o'])
    listen_lessons.append({
        'id': 'listen_kata_vowels',
        'title': 'Katakana Vowel Sounds',
        'description': 'Identify katakana vowels from their pronunciation.',
        'minigame_types': ['listen', 'match'],
        'data': kata_vowels,
    })

    # Listening: Vocabulary
    listen_vocab = _vocab_to_lesson_data(GREETINGS[:10])
    listen_lessons.append({
        'id': 'listen_vocab_greetings',
        'title': 'Listening: Greetings',
        'description': 'Listen and identify common greetings.',
        'minigame_types': ['listen', 'match'],
        'data': listen_vocab,
    })

    data['listening'] = {
        'title_jp': '\u8074\u89e3\u306e\u9928',
        'title_en': 'Listening Hall',
        'lessons': listen_lessons,
    }

    # -----------------------------------------------------------------------
    # Monument 7 - Grammar Intermediate
    # -----------------------------------------------------------------------
    inter_grammar_lessons = []
    for ldef in GRAMMAR_LESSONS:
        if ldef.get('monument_id') != 7:
            continue
        gp_ids = ldef.get('grammar_points', [])
        gps = [gp for gp in INTERMEDIATE_GRAMMAR if gp['id'] in gp_ids]
        if not gps:
            continue
        ld = _grammar_to_lesson_data(gps)
        inter_grammar_lessons.append({
            'id': ldef['lesson_id'],
            'title': ldef['title'],
            'description': ldef['description'],
            'minigame_types': ['quiz', 'build'],
            'data': ld,
        })

    data['grammar_intermediate'] = {
        'title_jp': '\u6587\u6cd5\u306e\u5854',
        'title_en': 'Intermediate Grammar Pagoda',
        'lessons': inter_grammar_lessons,
    }

    # -----------------------------------------------------------------------
    # Monument 8 - Kanji Intermediate
    # -----------------------------------------------------------------------
    kanji_inter_lessons = []
    if HAS_KANJI and KANJI_INTERMEDIATE:
        kanji_keys = list(KANJI_INTERMEDIATE.keys())
        group_size = 8
        for ci, start in enumerate(range(0, len(kanji_keys), group_size)):
            group_keys = kanji_keys[start:start + group_size]
            chars = []
            pairs = []
            questions = []
            for kk in group_keys:
                entry = KANJI_INTERMEDIATE[kk]
                kanji_char = entry.get('character', kk)
                # Extract reading from readings_kun or readings_on
                reading = (entry.get('readings_kun', ['']) or [''])[0]
                if not reading:
                    reading = (entry.get('readings_on', ['']) or [''])[0]
                meaning = entry.get('meaning', '')
                chars.append({'character': kanji_char, 'romaji': reading})
                pairs.append({'front': kanji_char, 'back': meaning})
                other_meanings = [KANJI_INTERMEDIATE[ok].get('meaning', '')
                                  for ok in kanji_keys if ok != kk][:3]
                questions.append({
                    'question': f'What does {kanji_char} mean?',
                    'correct_answer': meaning,
                    'wrong_answers': _pad_wrong(other_meanings),
                    'hint': f'Reading: {reading}',
                    'explanation': f'{kanji_char} = {meaning} ({reading})',
                })
            kanji_inter_lessons.append({
                'id': f'kanji_inter_{ci + 1}',
                'title': f'Intermediate Kanji (Set {ci + 1})',
                'description': f'Learn intermediate kanji characters (set {ci + 1}).',
                'minigame_types': ['match', 'memory', 'quiz'],
                'data': {'characters': chars, 'pairs': pairs, 'questions': questions},
            })
    else:
        kanji_inter_lessons.append({
            'id': 'kanji_inter_placeholder',
            'title': 'Intermediate Kanji (Coming Soon)',
            'description': 'Intermediate kanji content is being prepared.',
            'minigame_types': ['quiz'],
            'data': {'questions': [{
                'question': 'Kanji content coming soon!',
                'correct_answer': 'OK',
                'wrong_answers': ['N/A', 'N/A', 'N/A'],
                'hint': '',
                'explanation': 'Intermediate kanji lessons are being developed.',
            }]},
        })

    data['kanji_intermediate'] = {
        'title_jp': '\u6f22\u5b57\u4e2d\u7d1a\u306e\u5bae',
        'title_en': 'Intermediate Kanji Shrine',
        'lessons': kanji_inter_lessons,
    }

    # -----------------------------------------------------------------------
    # Monument 9 - Reading
    # -----------------------------------------------------------------------
    reading_lessons = []

    # Reading comprehension from grammar examples
    all_grammar_for_reading = BASIC_GRAMMAR + INTERMEDIATE_GRAMMAR
    reading_chunk_size = 4
    for ci, start in enumerate(range(0, len(all_grammar_for_reading),
                                     reading_chunk_size)):
        chunk = all_grammar_for_reading[start:start + reading_chunk_size]
        ld = _grammar_to_lesson_data(chunk)
        reading_lessons.append({
            'id': f'reading_{ci + 1}',
            'title': f'Reading Practice {ci + 1}',
            'description': f'Read and understand Japanese sentences (set {ci + 1}).',
            'minigame_types': ['quiz', 'build'],
            'data': ld,
        })

    # Reading from vocabulary
    all_vocab_for_reading = GREETINGS + [
        {'japanese': v['dictionary_form'], 'romaji': v.get('masu_form', ''),
         'english': v['meaning']}
        for v in COMMON_VERBS[:10]
    ]
    rd = _vocab_to_lesson_data(all_vocab_for_reading[:15])
    reading_lessons.append({
        'id': 'reading_vocab',
        'title': 'Reading: Vocabulary in Context',
        'description': 'Read and understand vocabulary in sentences.',
        'minigame_types': ['quiz', 'build'],
        'data': rd,
    })

    data['reading'] = {
        'title_jp': '\u8aad\u89e3\u306e\u9053',
        'title_en': 'Reading Path',
        'lessons': reading_lessons,
    }

    # -----------------------------------------------------------------------
    # Monument 10 - Conversation
    # -----------------------------------------------------------------------
    conv_lessons = []

    # Conversation from greetings
    conv_greetings = _vocab_to_lesson_data(GREETINGS[:10])
    conv_lessons.append({
        'id': 'conv_greetings',
        'title': 'Daily Greetings',
        'description': 'Practice greeting people in everyday situations.',
        'minigame_types': ['quiz', 'build', 'listen'],
        'data': conv_greetings,
    })

    # Conversation from basic grammar (dialogue-style)
    conv_grammar_gps = BASIC_GRAMMAR[:4]
    conv_gram_data = _grammar_to_lesson_data(conv_grammar_gps)
    conv_lessons.append({
        'id': 'conv_basic_sentences',
        'title': 'Basic Conversation Patterns',
        'description': 'Practice forming basic conversational sentences.',
        'minigame_types': ['quiz', 'build', 'listen'],
        'data': conv_gram_data,
    })

    # Conversation from vocabulary categories
    for cat_key in ['food', 'school', 'time']:
        cat_words = COMMON_NOUNS.get(cat_key, [])
        if cat_words:
            cat_title = cat_key.replace('_', ' ').title()
            cd = _vocab_to_lesson_data(cat_words)
            conv_lessons.append({
                'id': f'conv_{cat_key}',
                'title': f'Talking About {cat_title}',
                'description': f'Conversational practice about {cat_title.lower()}.',
                'minigame_types': ['quiz', 'build', 'listen'],
                'data': cd,
            })

    data['conversation'] = {
        'title_jp': '\u4f1a\u8a71\u306e\u5e83\u5834',
        'title_en': 'Conversation Plaza',
        'lessons': conv_lessons,
    }

    # -----------------------------------------------------------------------
    # Monument 11 - Grammar Advanced
    # -----------------------------------------------------------------------
    adv_grammar_lessons = []
    for ldef in GRAMMAR_LESSONS:
        if ldef.get('monument_id') != 11:
            continue
        gp_ids = ldef.get('grammar_points', [])
        gps = [gp for gp in ADVANCED_GRAMMAR if gp['id'] in gp_ids]
        if not gps:
            continue
        ld = _grammar_to_lesson_data(gps)
        adv_grammar_lessons.append({
            'id': ldef['lesson_id'],
            'title': ldef['title'],
            'description': ldef['description'],
            'minigame_types': ['quiz', 'build'],
            'data': ld,
        })

    data['grammar_advanced'] = {
        'title_jp': '\u6587\u6cd5\u306e\u8056\u57df',
        'title_en': 'Advanced Grammar Sanctuary',
        'lessons': adv_grammar_lessons,
    }

    # -----------------------------------------------------------------------
    # Monument 12 - Immersion
    # -----------------------------------------------------------------------
    immersion_lessons = []

    # Mix of hiragana + katakana characters
    mixed_chars_keys = ['a', 'i', 'u', 'e', 'o', 'ka', 'ki', 'ku', 'ke', 'ko']
    hira_mix = _chars_to_lesson_data(HIRAGANA_BASIC, mixed_chars_keys)
    kata_mix = _chars_to_lesson_data(KATAKANA_BASIC, mixed_chars_keys)
    combined_chars = {
        'characters': hira_mix['characters'] + kata_mix['characters'],
        'pairs': hira_mix['pairs'] + kata_mix['pairs'],
        'items': hira_mix['items'] + kata_mix['items'],
    }
    immersion_lessons.append({
        'id': 'immersion_kana_mix',
        'title': 'Mixed Kana Challenge',
        'description': 'Test yourself on both hiragana and katakana.',
        'minigame_types': ['quiz', 'type', 'build', 'listen'],
        'data': combined_chars,
    })

    # Mix of vocabulary
    immersion_vocab_words = GREETINGS[:5] + [
        {'japanese': v['dictionary_form'], 'romaji': v.get('masu_form', ''),
         'english': v['meaning']}
        for v in COMMON_VERBS[:5]
    ] + JLPT_N5_VOCAB[:5]
    immersion_vocab = _vocab_to_lesson_data(immersion_vocab_words)
    immersion_lessons.append({
        'id': 'immersion_vocab_mix',
        'title': 'Vocabulary Immersion',
        'description': 'A mix of greetings, verbs, and essential words.',
        'minigame_types': ['quiz', 'type', 'build', 'listen'],
        'data': immersion_vocab,
    })

    # Mix of grammar
    immersion_grammar = BASIC_GRAMMAR[:2] + INTERMEDIATE_GRAMMAR[:2]
    if ADVANCED_GRAMMAR:
        immersion_grammar += ADVANCED_GRAMMAR[:1]
    ig_data = _grammar_to_lesson_data(immersion_grammar)
    immersion_lessons.append({
        'id': 'immersion_grammar_mix',
        'title': 'Grammar Immersion',
        'description': 'Test your grammar knowledge across all levels.',
        'minigame_types': ['quiz', 'type', 'build', 'listen'],
        'data': ig_data,
    })

    # Full immersion challenge
    full_words = GREETINGS[:3] + JLPT_N5_VOCAB[:7]
    full_data = _vocab_to_lesson_data(full_words)
    full_gram = _grammar_to_lesson_data(BASIC_GRAMMAR[:3])
    full_data['sentences'] = full_gram.get('sentences', [])
    full_data['questions'] = full_data.get('questions', []) + full_gram.get('questions', [])
    immersion_lessons.append({
        'id': 'immersion_full',
        'title': 'Full Immersion Challenge',
        'description': 'The ultimate test combining all content types.',
        'minigame_types': ['quiz', 'type', 'build', 'listen'],
        'data': full_data,
    })

    data['immersion'] = {
        'title_jp': '\u6ca1\u5165\u306e\u6bbf\u5802',
        'title_en': 'Immersion Hall',
        'lessons': immersion_lessons,
    }

    return data


# Build the data once at module load time
MONUMENT_DATA = _build_monument_data()


class LessonSelectScreen:
    """
    Full-screen lesson-selection overlay.

    Usage
    -----
        screen = LessonSelectScreen()
        screen.show('hiragana', save_data_dict)
        # ... player interacts ...
        screen.hide()
    """

    def __init__(self, monument_id=None, save_data=None, on_back=None,
                 on_minigame_complete=None):
        self.entities = []
        self.is_visible = False
        self.current_monument = None
        self.save_data = save_data or {}
        self.active_minigame = None
        self._scroll_offset = 0
        self._on_back_callback = on_back
        self._on_complete_callback = on_minigame_complete

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def show(self, monument_id, save_data=None):
        """Display the lesson-select screen for *monument_id*."""
        self.hide()  # clean previous
        self.is_visible = True
        # Convert integer monument_id to string key
        if isinstance(monument_id, int):
            monument_id = MONUMENT_KEY_MAP.get(monument_id, 'hiragana')
        self.current_monument = monument_id
        self.save_data = save_data or self.save_data or {}
        self._scroll_offset = 0

        monument = self._load_lessons(monument_id)
        if monument is None:
            return

        self._build_ui(monument)

    def hide(self):
        """Tear down all UI entities."""
        self.is_visible = False
        for e in self.entities:
            if e is not None:
                destroy(e)
        self.entities.clear()

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------
    def _load_lessons(self, monument_id):
        """Return monument dict from MONUMENT_DATA (or None)."""
        return MONUMENT_DATA.get(monument_id)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self, monument):
        lessons = monument.get('lessons', [])

        # Full-screen background
        bg = Entity(
            parent=camera.ui,
            model='quad',
            color=COLOR_BG,
            scale=(2, 2),
            z=0.5,
        )
        self.entities.append(bg)

        # Title bar
        title_bar = Entity(
            parent=camera.ui,
            model='quad',
            color=COLOR_PANEL,
            scale=(1.2, 0.09),
            position=(0, 0.43),
            z=-0.1,
        )
        self.entities.append(title_bar)

        title_jp = Text(
            text=monument['title_jp'],
            parent=camera.ui,
            origin=(0, 0),
            position=(-0.15, 0.435),
            scale=2.5,
            color=COLOR_ACCENT,
            z=-0.2,
        )
        self.entities.append(title_jp)

        title_en = Text(
            text=monument['title_en'],
            parent=camera.ui,
            origin=(0, 0),
            position=(0.18, 0.435),
            scale=1.5,
            color=COLOR_TEXT_DIM,
            z=-0.2,
        )
        self.entities.append(title_en)

        # Back button
        back_btn = Button(
            parent=camera.ui,
            text='◀ Back',
            scale=(0.12, 0.045),
            position=(-0.5, 0.435),
            color=COLOR_BUTTON,
            highlight_color=COLOR_BUTTON_HOVER,
            text_color=COLOR_TEXT,
            radius=0.25,
            z=-0.2,
        )
        back_btn.on_click = self._on_back_pressed
        self.entities.append(back_btn)

        # Overall progress bar
        completed = sum(1 for l in lessons
                        if self._lesson_status(l['id']) == 'completed')
        total = len(lessons)
        prog_frac = completed / total if total else 0

        prog_bg = Entity(
            parent=camera.ui,
            model='quad',
            color=COLOR_PROGRESS_BG,
            scale=(0.8, 0.015),
            position=(0, 0.385),
            z=-0.1,
        )
        self.entities.append(prog_bg)

        prog_fill = Entity(
            parent=camera.ui,
            model='quad',
            color=COLOR_PROGRESS_FILL,
            scale=(max(0.001, 0.8 * prog_frac), 0.012),
            position=(-0.4, 0.385),
            origin=(-0.5, 0),
            z=-0.2,
        )
        self.entities.append(prog_fill)

        prog_label = Text(
            text=f'{completed} / {total} lessons completed',
            parent=camera.ui,
            origin=(0, 0),
            position=(0, 0.365),
            scale=1.0,
            color=COLOR_TEXT_DIM,
            z=-0.2,
        )
        self.entities.append(prog_label)

        # Lesson cards
        card_h = 0.105
        gap = 0.015
        start_y = 0.30

        for idx, lesson in enumerate(lessons):
            cy = start_y - idx * (card_h + gap)
            self._build_lesson_card(lesson, cy)

    # ------------------------------------------------------------------
    # Individual lesson card
    # ------------------------------------------------------------------
    def _build_lesson_card(self, lesson, y_pos):
        lesson_id = lesson['id']
        status = self._lesson_status(lesson_id)
        stars = self._lesson_stars(lesson_id)
        best_score = self._lesson_best_score(lesson_id)

        # Card background
        card_color = COLOR_PANEL if status != 'not_started' else \
            color.rgb(38, 38, 55)
        card = Entity(
            parent=camera.ui,
            model='quad',
            color=card_color,
            scale=(0.85, 0.095),
            position=(0, y_pos),
            z=-0.3,
        )
        self.entities.append(card)

        # Status indicator (left edge)
        status_colors = {
            'not_started': COLOR_TEXT_DIM,
            'in_progress': COLOR_ACCENT,
            'completed': COLOR_CORRECT,
        }
        indicator = Entity(
            parent=camera.ui,
            model='quad',
            color=status_colors.get(status, COLOR_TEXT_DIM),
            scale=(0.008, 0.085),
            position=(-0.42, y_pos),
            z=-0.4,
        )
        self.entities.append(indicator)

        # Lesson title
        title = Text(
            text=lesson['title'],
            parent=camera.ui,
            origin=(-0.5, 0),
            position=(-0.39, y_pos + 0.022),
            scale=1.5,
            color=COLOR_TEXT,
            z=-0.4,
        )
        self.entities.append(title)

        # Description
        desc = Text(
            text=lesson['description'],
            parent=camera.ui,
            origin=(-0.5, 0),
            position=(-0.39, y_pos - 0.005),
            scale=0.9,
            color=COLOR_TEXT_DIM,
            z=-0.4,
        )
        self.entities.append(desc)

        # Stars (if completed)
        if status == 'completed':
            for s in range(5):
                sx = -0.39 + s * 0.025
                star_color = COLOR_STAR_FILLED if s < stars else \
                    COLOR_STAR_EMPTY
                star = Text(
                    text='*',
                    parent=camera.ui,
                    origin=(0, 0),
                    position=(sx, y_pos - 0.027),
                    scale=2.0,
                    color=star_color,
                    z=-0.4,
                )
                self.entities.append(star)

            score_lbl = Text(
                text=f'Best: {best_score}',
                parent=camera.ui,
                origin=(-0.5, 0),
                position=(-0.25, y_pos - 0.027),
                scale=0.9,
                color=COLOR_GOLD,
                z=-0.4,
            )
            self.entities.append(score_lbl)

        # Minigame type buttons (right side)
        mg_types = lesson.get('minigame_types', [])
        btn_w = 0.07
        btn_gap = 0.008
        total_mg_w = len(mg_types) * (btn_w + btn_gap) - btn_gap
        mg_start_x = 0.42 - total_mg_w

        for i, mg_type in enumerate(mg_types):
            info = MINIGAME_TYPES.get(mg_type, {})
            bx = mg_start_x + i * (btn_w + btn_gap)
            mg_btn = Button(
                parent=camera.ui,
                text=info.get('label', mg_type),
                scale=(btn_w, 0.035),
                position=(bx, y_pos),
                color=info.get('color', COLOR_BUTTON),
                highlight_color=color.rgb(
                    min(255, int(info.get('color', COLOR_BUTTON).r * 255) + 40),
                    min(255, int(info.get('color', COLOR_BUTTON).g * 255) + 40),
                    min(255, int(info.get('color', COLOR_BUTTON).b * 255) + 40),
                ),
                text_color=color.rgb(20, 20, 40),
                radius=0.3,
                z=-0.4,
            )
            mg_btn.text_entity.scale *= 0.8
            mg_btn.on_click = lambda lid=lesson_id, mt=mg_type: \
                self._start_minigame(lid, mt)
            self.entities.append(mg_btn)

    # ------------------------------------------------------------------
    # Back button handler
    # ------------------------------------------------------------------
    def _on_back_pressed(self):
        """Handle the back button press."""
        if self._on_back_callback:
            self._on_back_callback()
        else:
            self.hide()

    # ------------------------------------------------------------------
    # Save-data helpers
    # ------------------------------------------------------------------
    def _lesson_status(self, lesson_id):
        """Return 'not_started', 'in_progress', or 'completed'."""
        ld = self.save_data.get('lessons', {}).get(lesson_id, {})
        return ld.get('status', 'not_started')

    def _lesson_stars(self, lesson_id):
        ld = self.save_data.get('lessons', {}).get(lesson_id, {})
        return ld.get('stars', 0)

    def _lesson_best_score(self, lesson_id):
        ld = self.save_data.get('lessons', {}).get(lesson_id, {})
        return ld.get('best_score', 0)

    # ------------------------------------------------------------------
    # Minigame launching
    # ------------------------------------------------------------------
    def _start_minigame(self, lesson_id, minigame_type):
        """Instantiate and show the chosen minigame for *lesson_id*."""
        # Find the lesson data
        monument = self._load_lessons(self.current_monument)
        if monument is None:
            return

        lesson = None
        for l in monument.get('lessons', []):
            if l['id'] == lesson_id:
                lesson = l
                break
        if lesson is None:
            return

        lesson_content = lesson.get('data', {})

        # Prepare lesson_data in the format each minigame expects
        mg_data = self._prepare_minigame_data(lesson_content, minigame_type)

        info = MINIGAME_TYPES.get(minigame_type)
        if info is None:
            return

        mg_class = info['class']

        def on_complete(score, max_score, correct, wrong):
            """Handle minigame completion."""
            self._on_minigame_complete(lesson_id, score, max_score,
                                       correct, wrong)

        # Hide the lesson screen
        self.hide()

        # Create and show minigame
        self.active_minigame = mg_class(
            lesson_data=mg_data,
            difficulty='normal',
            on_complete=on_complete,
        )
        self.active_minigame.show()

    def _prepare_minigame_data(self, content, mg_type):
        """
        Reshape raw lesson content into the dict expected by each minigame.

        Each minigame type looks for specific keys:
            match  -> 'characters'
            memory -> 'pairs'
            quiz   -> 'questions'
            type   -> 'items'
            build  -> 'sentences'
            listen -> 'items' (listening format)
        """
        if mg_type == 'match':
            chars = content.get('characters', [])
            # Fall back: build from pairs if characters absent
            if not chars and content.get('pairs'):
                chars = [{'character': p['front'], 'romaji': p['back']}
                         for p in content['pairs']]
            return {'characters': chars}

        elif mg_type == 'memory':
            pairs = content.get('pairs', [])
            if not pairs and content.get('characters'):
                pairs = [{'front': c['character'], 'back': c['romaji']}
                         for c in content['characters']]
            return {'pairs': pairs}

        elif mg_type == 'quiz':
            return {'questions': content.get('questions', [])}

        elif mg_type == 'type':
            items = content.get('items', [])
            # Try to build from characters if items missing
            if not items and content.get('characters'):
                items = [{'display': c['character'],
                          'answer': c['romaji'],
                          'alt_answers': []}
                         for c in content['characters']]
            return {'items': items}

        elif mg_type == 'build':
            return {'sentences': content.get('sentences', [])}

        elif mg_type == 'listen':
            items = content.get('items', [])
            # Build from characters if listening items missing
            if not items and content.get('characters'):
                all_chars = content['characters']
                items = []
                for c in all_chars:
                    wrong = [x['character'] for x in all_chars
                             if x['character'] != c['character']][:3]
                    items.append({
                        'romaji': c['romaji'],
                        'correct_character': c['character'],
                        'wrong_characters': wrong,
                    })
            return {'items': items}

        return content  # fallback

    # ------------------------------------------------------------------
    # Minigame completion
    # ------------------------------------------------------------------
    def _on_minigame_complete(self, lesson_id, score, max_score,
                               correct, wrong):
        """Update save data and re-show the lesson screen."""
        # Calculate stars
        pct = score / max_score if max_score else 0
        if pct >= 0.95:
            stars = 5
        elif pct >= 0.80:
            stars = 4
        elif pct >= 0.65:
            stars = 3
        elif pct >= 0.45:
            stars = 2
        elif pct >= 0.20:
            stars = 1
        else:
            stars = 0

        # Update save data
        if 'lessons' not in self.save_data:
            self.save_data['lessons'] = {}
        if lesson_id not in self.save_data['lessons']:
            self.save_data['lessons'][lesson_id] = {}

        ld = self.save_data['lessons'][lesson_id]
        ld['status'] = 'completed' if pct >= 0.20 else 'in_progress'
        if score > ld.get('best_score', 0):
            ld['best_score'] = score
        if stars > ld.get('stars', 0):
            ld['stars'] = stars

        self.active_minigame = None

        # Notify external callback
        if self._on_complete_callback:
            self._on_complete_callback(score, max_score, correct, wrong)

        # Re-show the lesson screen
        self.show(self.current_monument, self.save_data)
