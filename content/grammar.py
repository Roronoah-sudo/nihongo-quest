"""
Nihongo Quest - Grammar Content Data
Japanese grammar points organized by level: basic, intermediate, advanced.
Monument IDs: 2 (Basic Grammar Gate), 7 (Intermediate), 11 (Advanced)
"""

# =============================================================================
# BASIC GRAMMAR (Monument ID: 2 - The Grammar Gate)
# =============================================================================

BASIC_GRAMMAR = [
    {
        "id": "gram_b01",
        "title": "Japanese Sentence Structure (SOV)",
        "explanation": "Japanese follows Subject-Object-Verb order, unlike English SVO. The verb always comes at the end of the sentence.",
        "pattern": "[Subject] は [Object] を [Verb]。",
        "examples": [
            {
                "japanese": "わたしはりんごをたべます。",
                "romaji": "Watashi wa ringo wo tabemasu.",
                "english": "I eat an apple.",
            },
            {
                "japanese": "たなかさんはほんをよみます。",
                "romaji": "Tanaka-san wa hon wo yomimasu.",
                "english": "Mr. Tanaka reads a book.",
            },
            {
                "japanese": "ねこがさかなをたべました。",
                "romaji": "Neko ga sakana wo tabemashita.",
                "english": "The cat ate fish.",
            },
        ],
        "monument_id": 2,
    },
    {
        "id": "gram_b02",
        "title": "Topic Marker は (wa)",
        "explanation": "は marks the topic of the sentence -- what you are talking about. It is pronounced 'wa' when used as a particle, not 'ha'.",
        "pattern": "[Topic] は [Comment]。",
        "examples": [
            {
                "japanese": "わたしはがくせいです。",
                "romaji": "Watashi wa gakusei desu.",
                "english": "I am a student.",
            },
            {
                "japanese": "きょうはいいてんきですね。",
                "romaji": "Kyou wa ii tenki desu ne.",
                "english": "Today is nice weather, isn't it.",
            },
            {
                "japanese": "にほんごはたのしいです。",
                "romaji": "Nihongo wa tanoshii desu.",
                "english": "Japanese is fun.",
            },
        ],
        "monument_id": 2,
    },
    {
        "id": "gram_b03",
        "title": "Subject Marker が (ga)",
        "explanation": "が marks the grammatical subject, often used for emphasis, new information, or with certain verbs/adjectives like すき, わかる, ある, いる.",
        "pattern": "[Subject] が [Predicate]。",
        "examples": [
            {
                "japanese": "ねこがいます。",
                "romaji": "Neko ga imasu.",
                "english": "There is a cat.",
            },
            {
                "japanese": "わたしはすしがすきです。",
                "romaji": "Watashi wa sushi ga suki desu.",
                "english": "I like sushi.",
            },
            {
                "japanese": "にほんごがわかりますか。",
                "romaji": "Nihongo ga wakarimasu ka.",
                "english": "Do you understand Japanese?",
            },
        ],
        "monument_id": 2,
    },
    {
        "id": "gram_b04",
        "title": "Object Marker を (wo)",
        "explanation": "を marks the direct object of an action verb. It indicates what receives the action. Pronounced 'o'.",
        "pattern": "[Object] を [Verb]。",
        "examples": [
            {
                "japanese": "みずをのみます。",
                "romaji": "Mizu wo nomimasu.",
                "english": "I drink water.",
            },
            {
                "japanese": "えいがをみます。",
                "romaji": "Eiga wo mimasu.",
                "english": "I watch a movie.",
            },
            {
                "japanese": "てがみをかきます。",
                "romaji": "Tegami wo kakimasu.",
                "english": "I write a letter.",
            },
        ],
        "monument_id": 2,
    },
    {
        "id": "gram_b05",
        "title": "Location/Time Marker に (ni)",
        "explanation": "に indicates location of existence, destination, time, or indirect object. It answers 'where?', 'when?', or 'to whom?'.",
        "pattern": "[Place/Time] に [Verb]。",
        "examples": [
            {
                "japanese": "がっこうにいきます。",
                "romaji": "Gakkou ni ikimasu.",
                "english": "I go to school.",
            },
            {
                "japanese": "しちじにおきます。",
                "romaji": "Shichi-ji ni okimasu.",
                "english": "I wake up at 7 o'clock.",
            },
            {
                "japanese": "ともだちにでんわします。",
                "romaji": "Tomodachi ni denwa shimasu.",
                "english": "I call my friend.",
            },
        ],
        "monument_id": 2,
    },
    {
        "id": "gram_b06",
        "title": "Location of Action で (de)",
        "explanation": "で marks the location where an action takes place, or the means/tool by which something is done.",
        "pattern": "[Place/Means] で [Action Verb]。",
        "examples": [
            {
                "japanese": "としょかんでべんきょうします。",
                "romaji": "Toshokan de benkyou shimasu.",
                "english": "I study at the library.",
            },
            {
                "japanese": "はしでたべます。",
                "romaji": "Hashi de tabemasu.",
                "english": "I eat with chopsticks.",
            },
            {
                "japanese": "バスでがっこうにいきます。",
                "romaji": "Basu de gakkou ni ikimasu.",
                "english": "I go to school by bus.",
            },
        ],
        "monument_id": 2,
    },
    {
        "id": "gram_b07",
        "title": "Direction Marker へ (e)",
        "explanation": "へ indicates direction of movement. Pronounced 'e' when used as a particle. Similar to に but emphasizes the direction rather than the destination.",
        "pattern": "[Direction] へ [Movement Verb]。",
        "examples": [
            {
                "japanese": "にほんへいきます。",
                "romaji": "Nihon e ikimasu.",
                "english": "I go to Japan.",
            },
            {
                "japanese": "みなみへあるきました。",
                "romaji": "Minami e arukimashita.",
                "english": "I walked southward.",
            },
        ],
        "monument_id": 2,
    },
    {
        "id": "gram_b08",
        "title": "Also/Too も (mo)",
        "explanation": "も replaces は, が, or を to mean 'also' or 'too'. It adds the subject/object to a previously mentioned group.",
        "pattern": "[Noun] も [Predicate]。",
        "examples": [
            {
                "japanese": "わたしもがくせいです。",
                "romaji": "Watashi mo gakusei desu.",
                "english": "I am also a student.",
            },
            {
                "japanese": "おちゃもコーヒーものみます。",
                "romaji": "Ocha mo koohii mo nomimasu.",
                "english": "I drink both tea and coffee.",
            },
        ],
        "monument_id": 2,
    },
    {
        "id": "gram_b09",
        "title": "Possessive の (no)",
        "explanation": "の connects two nouns, showing possession, affiliation, or description. Similar to English 'of' or possessive 's.",
        "pattern": "[Noun A] の [Noun B]",
        "examples": [
            {
                "japanese": "わたしのほん",
                "romaji": "Watashi no hon",
                "english": "My book",
            },
            {
                "japanese": "にほんのたべもの",
                "romaji": "Nihon no tabemono",
                "english": "Japanese food (food of Japan)",
            },
            {
                "japanese": "だいがくのせんせい",
                "romaji": "Daigaku no sensei",
                "english": "University professor",
            },
        ],
        "monument_id": 2,
    },
    {
        "id": "gram_b10",
        "title": "And (Listing) と (to)",
        "explanation": "と connects nouns in a complete list (like 'and'). It implies nothing else is included beyond what's listed.",
        "pattern": "[Noun A] と [Noun B]",
        "examples": [
            {
                "japanese": "パンとたまごをたべます。",
                "romaji": "Pan to tamago wo tabemasu.",
                "english": "I eat bread and eggs.",
            },
            {
                "japanese": "ともだちとえいがをみます。",
                "romaji": "Tomodachi to eiga wo mimasu.",
                "english": "I watch a movie with my friend.",
            },
        ],
        "monument_id": 2,
    },
    {
        "id": "gram_b11",
        "title": "Question Marker か (ka)",
        "explanation": "か at the end of a sentence turns it into a question. In polite speech, no change in word order is needed.",
        "pattern": "[Statement] か。",
        "examples": [
            {
                "japanese": "にほんじんですか。",
                "romaji": "Nihonjin desu ka.",
                "english": "Are you Japanese?",
            },
            {
                "japanese": "なにをたべますか。",
                "romaji": "Nani wo tabemasu ka.",
                "english": "What will you eat?",
            },
            {
                "japanese": "あしたがっこうにいきますか。",
                "romaji": "Ashita gakkou ni ikimasu ka.",
                "english": "Will you go to school tomorrow?",
            },
        ],
        "monument_id": 2,
    },
    {
        "id": "gram_b12",
        "title": "Sentence Ending よ (yo) and ね (ne)",
        "explanation": "よ adds emphasis or conveys new information ('you know!'). ね seeks agreement or confirmation ('right?', 'isn't it?').",
        "pattern": "[Statement] よ/ね。",
        "examples": [
            {
                "japanese": "このケーキはおいしいですよ。",
                "romaji": "Kono keeki wa oishii desu yo.",
                "english": "This cake is delicious, you know!",
            },
            {
                "japanese": "きょうはあついですね。",
                "romaji": "Kyou wa atsui desu ne.",
                "english": "It's hot today, isn't it?",
            },
            {
                "japanese": "にほんごはたのしいですよね。",
                "romaji": "Nihongo wa tanoshii desu yo ne.",
                "english": "Japanese is fun, right? (I think so!)",
            },
        ],
        "monument_id": 2,
    },
    {
        "id": "gram_b13",
        "title": "Desu/Masu (Polite Forms)",
        "explanation": "です follows nouns and adjectives to make polite statements. ます is the polite verb ending. These are essential for polite Japanese.",
        "pattern": "[Noun] です。/ [Verb stem] ます。",
        "examples": [
            {
                "japanese": "がくせいです。",
                "romaji": "Gakusei desu.",
                "english": "I am a student.",
            },
            {
                "japanese": "がくせいではありません。",
                "romaji": "Gakusei dewa arimasen.",
                "english": "I am not a student.",
            },
            {
                "japanese": "まいにちべんきょうします。",
                "romaji": "Mainichi benkyou shimasu.",
                "english": "I study every day.",
            },
        ],
        "monument_id": 2,
    },
    {
        "id": "gram_b14",
        "title": "Demonstratives: こ・そ・あ・ど",
        "explanation": "Japanese uses a ko-so-a-do system for demonstratives. こ = near speaker, そ = near listener, あ = far from both, ど = question.",
        "pattern": "この/その/あの/どの + [Noun]",
        "examples": [
            {
                "japanese": "このほんはおもしろいです。",
                "romaji": "Kono hon wa omoshiroi desu.",
                "english": "This book is interesting.",
            },
            {
                "japanese": "そのかばんはだれのですか。",
                "romaji": "Sono kaban wa dare no desu ka.",
                "english": "Whose bag is that?",
            },
            {
                "japanese": "あのやまはふじさんです。",
                "romaji": "Ano yama wa Fuji-san desu.",
                "english": "That mountain (over there) is Mt. Fuji.",
            },
            {
                "japanese": "どのくるまがすきですか。",
                "romaji": "Dono kuruma ga suki desu ka.",
                "english": "Which car do you like?",
            },
        ],
        "monument_id": 2,
    },
]

# =============================================================================
# INTERMEDIATE GRAMMAR (Monument ID: 7 - The Intermediate Pagoda)
# =============================================================================

INTERMEDIATE_GRAMMAR = [
    {
        "id": "gram_i01",
        "title": "Te-form Uses: Requests (~てください)",
        "explanation": "The te-form + ください makes polite requests. The te-form is one of the most versatile verb forms in Japanese.",
        "pattern": "[Verb te-form] ください。",
        "examples": [
            {
                "japanese": "ちょっとまってください。",
                "romaji": "Chotto matte kudasai.",
                "english": "Please wait a moment.",
            },
            {
                "japanese": "にほんごではなしてください。",
                "romaji": "Nihongo de hanashite kudasai.",
                "english": "Please speak in Japanese.",
            },
            {
                "japanese": "ここにすわってください。",
                "romaji": "Koko ni suwatte kudasai.",
                "english": "Please sit here.",
            },
        ],
        "monument_id": 7,
    },
    {
        "id": "gram_i02",
        "title": "Te-form: Progressive (~ている)",
        "explanation": "Te-form + いる describes an ongoing action (progressive) or a resulting state.",
        "pattern": "[Verb te-form] いる/います。",
        "examples": [
            {
                "japanese": "いまごはんをたべています。",
                "romaji": "Ima gohan wo tabete imasu.",
                "english": "I am eating a meal right now.",
            },
            {
                "japanese": "とうきょうにすんでいます。",
                "romaji": "Toukyou ni sunde imasu.",
                "english": "I live in Tokyo. (state)",
            },
            {
                "japanese": "あにはけっこんしています。",
                "romaji": "Ani wa kekkon shite imasu.",
                "english": "My brother is married. (resulting state)",
            },
        ],
        "monument_id": 7,
    },
    {
        "id": "gram_i03",
        "title": "Te-form: Connecting Actions (~て、~て)",
        "explanation": "The te-form connects sequential actions in a sentence, like 'and' between clauses.",
        "pattern": "[Verb1 te-form]、[Verb2 te-form]、[Verb3]。",
        "examples": [
            {
                "japanese": "あさおきて、シャワーをあびて、あさごはんをたべます。",
                "romaji": "Asa okite, shawaa wo abite, asagohan wo tabemasu.",
                "english": "In the morning, I wake up, take a shower, and eat breakfast.",
            },
            {
                "japanese": "えきにいって、きっぷをかいました。",
                "romaji": "Eki ni itte, kippu wo kaimashita.",
                "english": "I went to the station and bought a ticket.",
            },
        ],
        "monument_id": 7,
    },
    {
        "id": "gram_i04",
        "title": "Conditional: たら (tara)",
        "explanation": "たら expresses 'if/when' conditions. Formed by adding ら to the past tense. Most versatile conditional.",
        "pattern": "[Past form] ら、[Result]。",
        "examples": [
            {
                "japanese": "あめがふったら、いえにいます。",
                "romaji": "Ame ga futtara, ie ni imasu.",
                "english": "If it rains, I'll stay home.",
            },
            {
                "japanese": "やすかったら、かいます。",
                "romaji": "Yasukattara, kaimasu.",
                "english": "If it's cheap, I'll buy it.",
            },
            {
                "japanese": "にほんにいったら、ふじさんをみたいです。",
                "romaji": "Nihon ni ittara, Fuji-san wo mitai desu.",
                "english": "If I go to Japan, I want to see Mt. Fuji.",
            },
        ],
        "monument_id": 7,
    },
    {
        "id": "gram_i05",
        "title": "Conditional: ば (ba)",
        "explanation": "ば expresses a general/hypothetical condition. Often used for advice or stating general truths.",
        "pattern": "[Verb ba-form] 、[Result]。",
        "examples": [
            {
                "japanese": "べんきょうすれば、しけんにうかります。",
                "romaji": "Benkyou sureba, shiken ni ukarimasu.",
                "english": "If you study, you will pass the exam.",
            },
            {
                "japanese": "やすければ、かいます。",
                "romaji": "Yasukereba, kaimasu.",
                "english": "If it's cheap, I'll buy it.",
            },
        ],
        "monument_id": 7,
    },
    {
        "id": "gram_i06",
        "title": "Conditional: と (to)",
        "explanation": "と conditional describes natural/automatic consequences, habitual results, or discoveries. 'Whenever X, Y happens.'",
        "pattern": "[Dictionary form] と、[Result]。",
        "examples": [
            {
                "japanese": "はるになると、さくらがさきます。",
                "romaji": "Haru ni naru to, sakura ga sakimasu.",
                "english": "When spring comes, cherry blossoms bloom.",
            },
            {
                "japanese": "このボタンをおすと、ドアがあきます。",
                "romaji": "Kono botan wo osu to, doa ga akimasu.",
                "english": "When you press this button, the door opens.",
            },
        ],
        "monument_id": 7,
    },
    {
        "id": "gram_i07",
        "title": "Conditional: なら (nara)",
        "explanation": "なら is used when the condition is based on what someone else said or a given situation. 'If that's the case...'",
        "pattern": "[Noun/Statement] なら、[Advice/Comment]。",
        "examples": [
            {
                "japanese": "にほんにいくなら、きょうとにいってください。",
                "romaji": "Nihon ni iku nara, Kyouto ni itte kudasai.",
                "english": "If you're going to Japan, please go to Kyoto.",
            },
            {
                "japanese": "すしなら、あのみせがおいしいですよ。",
                "romaji": "Sushi nara, ano mise ga oishii desu yo.",
                "english": "If it's sushi (you want), that shop is delicious.",
            },
        ],
        "monument_id": 7,
    },
    {
        "id": "gram_i08",
        "title": "Passive Form (~られる/~れる)",
        "explanation": "The passive voice indicates an action done to the subject. Can express suffering or inconvenience (adversative passive).",
        "pattern": "[Subject] は [Agent] に [Verb passive]。",
        "examples": [
            {
                "japanese": "わたしはせんせいにほめられました。",
                "romaji": "Watashi wa sensei ni homeraremashita.",
                "english": "I was praised by the teacher.",
            },
            {
                "japanese": "あめにふられました。",
                "romaji": "Ame ni furaremashita.",
                "english": "I got rained on. (adversative passive)",
            },
            {
                "japanese": "このほんはたくさんのひとによまれています。",
                "romaji": "Kono hon wa takusan no hito ni yomarete imasu.",
                "english": "This book is read by many people.",
            },
        ],
        "monument_id": 7,
    },
    {
        "id": "gram_i09",
        "title": "Causative Form (~させる/~せる)",
        "explanation": "The causative form means 'to make/let someone do something'. Used by authority figures or when granting permission.",
        "pattern": "[Causer] は [Person] に/を [Verb causative]。",
        "examples": [
            {
                "japanese": "せんせいはがくせいにほんをよませました。",
                "romaji": "Sensei wa gakusei ni hon wo yomasemashita.",
                "english": "The teacher made the students read a book.",
            },
            {
                "japanese": "おかあさんはこどもにやさいをたべさせます。",
                "romaji": "Okaasan wa kodomo ni yasai wo tabesasemasu.",
                "english": "The mother makes her child eat vegetables.",
            },
        ],
        "monument_id": 7,
    },
    {
        "id": "gram_i10",
        "title": "Giving and Receiving: あげる・もらう・くれる",
        "explanation": "Japanese has specific verbs for giving and receiving based on social relationships and perspective.",
        "pattern": "[Giver] が [Receiver] に [Thing] を あげる/もらう/くれる。",
        "examples": [
            {
                "japanese": "わたしはともだちにプレゼントをあげました。",
                "romaji": "Watashi wa tomodachi ni purezento wo agemashita.",
                "english": "I gave a present to my friend.",
            },
            {
                "japanese": "わたしはせんせいにほんをもらいました。",
                "romaji": "Watashi wa sensei ni hon wo moraimashita.",
                "english": "I received a book from the teacher.",
            },
            {
                "japanese": "ともだちがわたしにケーキをくれました。",
                "romaji": "Tomodachi ga watashi ni keeki wo kuremashita.",
                "english": "My friend gave me cake.",
            },
        ],
        "monument_id": 7,
    },
    {
        "id": "gram_i11",
        "title": "Relative Clauses",
        "explanation": "In Japanese, relative clauses come before the noun they modify. No relative pronoun is needed.",
        "pattern": "[Clause modifying noun] + [Noun]",
        "examples": [
            {
                "japanese": "きのうかったほんはおもしろいです。",
                "romaji": "Kinou katta hon wa omoshiroi desu.",
                "english": "The book I bought yesterday is interesting.",
            },
            {
                "japanese": "にほんごをおしえているせんせいはやさしいです。",
                "romaji": "Nihongo wo oshiete iru sensei wa yasashii desu.",
                "english": "The teacher who teaches Japanese is kind.",
            },
        ],
        "monument_id": 7,
    },
    {
        "id": "gram_i12",
        "title": "と思う (to omou) - 'I think that...'",
        "explanation": "と思う expresses one's opinion or thought. The quoted thought comes before と.",
        "pattern": "[Plain form] と おもう/おもいます。",
        "examples": [
            {
                "japanese": "あしたはあめがふるとおもいます。",
                "romaji": "Ashita wa ame ga furu to omoimasu.",
                "english": "I think it will rain tomorrow.",
            },
            {
                "japanese": "このえいがはおもしろいとおもいます。",
                "romaji": "Kono eiga wa omoshiroi to omoimasu.",
                "english": "I think this movie is interesting.",
            },
        ],
        "monument_id": 7,
    },
    {
        "id": "gram_i13",
        "title": "ことができる - Ability/Possibility",
        "explanation": "ことができる expresses ability or possibility, like 'can' in English.",
        "pattern": "[Dictionary form] ことができる/できます。",
        "examples": [
            {
                "japanese": "にほんごをはなすことができます。",
                "romaji": "Nihongo wo hanasu koto ga dekimasu.",
                "english": "I can speak Japanese.",
            },
            {
                "japanese": "ここでおよぐことができますか。",
                "romaji": "Koko de oyogu koto ga dekimasu ka.",
                "english": "Can you swim here?",
            },
        ],
        "monument_id": 7,
    },
    {
        "id": "gram_i14",
        "title": "たい Form - Want to do",
        "explanation": "The たい form expresses the speaker's desire to do something. Formed by replacing ます with たい.",
        "pattern": "[Verb stem] たい/たいです。",
        "examples": [
            {
                "japanese": "にほんにいきたいです。",
                "romaji": "Nihon ni ikitai desu.",
                "english": "I want to go to Japan.",
            },
            {
                "japanese": "あたらしいくるまがかいたいです。",
                "romaji": "Atarashii kuruma ga kaitai desu.",
                "english": "I want to buy a new car.",
            },
            {
                "japanese": "なにがたべたいですか。",
                "romaji": "Nani ga tabetai desu ka.",
                "english": "What do you want to eat?",
            },
        ],
        "monument_id": 7,
    },
]

# =============================================================================
# ADVANCED GRAMMAR (Monument ID: 11 - The Advanced Sanctuary)
# =============================================================================

ADVANCED_GRAMMAR = [
    {
        "id": "gram_a01",
        "title": "Keigo: Polite Language (丁寧語 teineigo)",
        "explanation": "Teineigo is the basic level of polite Japanese, using です and ます forms. It is used in most formal and semi-formal situations.",
        "pattern": "[Verb masu-form] / [Noun] です",
        "examples": [
            {
                "japanese": "わたしはたなかともうします。",
                "romaji": "Watashi wa Tanaka to moushimasu.",
                "english": "My name is Tanaka. (polite self-introduction)",
            },
            {
                "japanese": "こちらはたなかさんでございます。",
                "romaji": "Kochira wa Tanaka-san de gozaimasu.",
                "english": "This is Mr./Ms. Tanaka. (very polite)",
            },
        ],
        "monument_id": 11,
    },
    {
        "id": "gram_a02",
        "title": "Keigo: Honorific Language (尊敬語 sonkeigo)",
        "explanation": "Sonkeigo elevates the actions of others to show respect. Used for superiors, customers, or people you want to honor.",
        "pattern": "お/ご + [Verb stem] + になる / Special honorific verbs",
        "examples": [
            {
                "japanese": "せんせいはもうおかえりになりました。",
                "romaji": "Sensei wa mou okaeri ni narimashita.",
                "english": "The teacher has already gone home. (honorific)",
            },
            {
                "japanese": "しゃちょうはなにをめしあがりますか。",
                "romaji": "Shachou wa nani wo meshiagarimasu ka.",
                "english": "What will the president eat? (honorific for taberu)",
            },
            {
                "japanese": "おきゃくさまがいらっしゃいました。",
                "romaji": "Okyaku-sama ga irasshaimashita.",
                "english": "The customer has arrived. (honorific for kuru)",
            },
        ],
        "monument_id": 11,
    },
    {
        "id": "gram_a03",
        "title": "Keigo: Humble Language (謙譲語 kenjougo)",
        "explanation": "Kenjougo lowers your own actions to show respect to others. Used when talking about your own actions to superiors.",
        "pattern": "お/ご + [Verb stem] + する / Special humble verbs",
        "examples": [
            {
                "japanese": "しゃちょうにおでんわいたします。",
                "romaji": "Shachou ni odenwa itashimasu.",
                "english": "I will call the president. (humble for suru)",
            },
            {
                "japanese": "わたしがごあんないいたします。",
                "romaji": "Watashi ga goannai itashimasu.",
                "english": "I will guide you. (humble)",
            },
            {
                "japanese": "せんせいのほんをはいけんしました。",
                "romaji": "Sensei no hon wo haiken shimashita.",
                "english": "I looked at the teacher's book. (humble for miru)",
            },
        ],
        "monument_id": 11,
    },
    {
        "id": "gram_a04",
        "title": "Literary/Written Forms (~である)",
        "explanation": "である is the literary/formal equivalent of です, used in essays, academic writing, and formal documents.",
        "pattern": "[Noun] である。/ [Na-adj] である。",
        "examples": [
            {
                "japanese": "にほんはしまぐにである。",
                "romaji": "Nihon wa shimaguni de aru.",
                "english": "Japan is an island country. (literary)",
            },
            {
                "japanese": "このもんだいはふくざつである。",
                "romaji": "Kono mondai wa fukuzatsu de aru.",
                "english": "This problem is complex. (literary)",
            },
        ],
        "monument_id": 11,
    },
    {
        "id": "gram_a05",
        "title": "~ようにする - Make an effort to",
        "explanation": "ようにする means to make an effort to do something regularly, or to try to ensure something happens.",
        "pattern": "[Dictionary form / ない form] ようにする。",
        "examples": [
            {
                "japanese": "まいにちうんどうするようにしています。",
                "romaji": "Mainichi undou suru you ni shite imasu.",
                "english": "I try to exercise every day.",
            },
            {
                "japanese": "おそくならないようにします。",
                "romaji": "Osoku naranai you ni shimasu.",
                "english": "I'll make sure not to be late.",
            },
        ],
        "monument_id": 11,
    },
    {
        "id": "gram_a06",
        "title": "~ことにする - Decide to",
        "explanation": "ことにする means to decide to do something. It emphasizes a conscious decision made by the speaker.",
        "pattern": "[Dictionary form / ない form] ことにする。",
        "examples": [
            {
                "japanese": "にほんにりゅうがくすることにしました。",
                "romaji": "Nihon ni ryuugaku suru koto ni shimashita.",
                "english": "I decided to study abroad in Japan.",
            },
            {
                "japanese": "あしたからはやくおきることにします。",
                "romaji": "Ashita kara hayaku okiru koto ni shimasu.",
                "english": "I'll decide to wake up early starting tomorrow.",
            },
        ],
        "monument_id": 11,
    },
    {
        "id": "gram_a07",
        "title": "~わけ - Reason/Meaning",
        "explanation": "わけ expresses reason, meaning, or conclusion. わけだ = 'that means/no wonder'. わけがない = 'there's no way'. わけではない = 'it's not that...'.",
        "pattern": "[Plain form] わけだ / わけがない / わけではない。",
        "examples": [
            {
                "japanese": "さんねんにほんにいたのだから、にほんごがじょうずなわけだ。",
                "romaji": "San-nen Nihon ni ita no dakara, nihongo ga jouzu na wake da.",
                "english": "Since he was in Japan for 3 years, no wonder his Japanese is good.",
            },
            {
                "japanese": "そんなかんたんにできるわけがない。",
                "romaji": "Sonna kantan ni dekiru wake ga nai.",
                "english": "There's no way it can be done that easily.",
            },
            {
                "japanese": "にほんごがきらいなわけではありません。",
                "romaji": "Nihongo ga kirai na wake dewa arimasen.",
                "english": "It's not that I dislike Japanese.",
            },
        ],
        "monument_id": 11,
    },
    {
        "id": "gram_a08",
        "title": "~はず - Expected/Should be",
        "explanation": "はず expresses an expectation or belief based on evidence or logic. 'It should be...' or 'It's expected that...'.",
        "pattern": "[Plain form] はず だ/です。",
        "examples": [
            {
                "japanese": "かれはもうつくはずです。",
                "romaji": "Kare wa mou tsuku hazu desu.",
                "english": "He should arrive soon.",
            },
            {
                "japanese": "あのレストランはおいしいはずです。",
                "romaji": "Ano resutoran wa oishii hazu desu.",
                "english": "That restaurant should be delicious.",
            },
            {
                "japanese": "きのうメールをおくったはずですが。",
                "romaji": "Kinou meeru wo okutta hazu desu ga.",
                "english": "I should have sent the email yesterday, but...",
            },
        ],
        "monument_id": 11,
    },
]

# =============================================================================
# VERB CONJUGATION RULES (Monument ID: 4 - The Verb Dojo)
# =============================================================================

VERB_CONJUGATION = {
    "godan_rules": {
        "description": "Godan (Group I / u-verbs): The final kana changes row based on conjugation.",
        "monument_id": 4,
        "endings": {
            "dictionary": "u-ending (う, く, す, つ, ぬ, ぶ, む, る)",
            "masu": "Change u -> i + ます (e.g., かく -> かきます)",
            "nai": "Change u -> a + ない (e.g., かく -> かかない). Exception: う -> わない",
            "te_form": {
                "description": "Te-form depends on the ending consonant",
                "rules": [
                    {"ending": "う, つ, る", "te_form": "って", "example": "かう -> かって, まつ -> まって, とる -> とって"},
                    {"ending": "く", "te_form": "いて", "example": "かく -> かいて (exception: いく -> いって)"},
                    {"ending": "ぐ", "te_form": "いで", "example": "およぐ -> およいで"},
                    {"ending": "す", "te_form": "して", "example": "はなす -> はなして"},
                    {"ending": "ぬ, ぶ, む", "te_form": "んで", "example": "しぬ -> しんで, あそぶ -> あそんで, のむ -> のんで"},
                ],
            },
            "past": "Same sound changes as te-form but with た/だ instead of て/で",
            "potential": "Change u -> e + る (e.g., かく -> かける)",
            "volitional": "Change u -> o + う (e.g., かく -> かこう)",
            "passive": "Change u -> a + れる (e.g., かく -> かかれる)",
            "causative": "Change u -> a + せる (e.g., かく -> かかせる)",
            "imperative": "Change u -> e (e.g., かく -> かけ)",
            "conditional_ba": "Change u -> e + ば (e.g., かく -> かけば)",
        },
    },
    "ichidan_rules": {
        "description": "Ichidan (Group II / ru-verbs): Simply drop る and add the conjugation ending.",
        "monument_id": 4,
        "endings": {
            "dictionary": "る ending (after i or e sound)",
            "masu": "Drop る + ます (e.g., たべる -> たべます)",
            "nai": "Drop る + ない (e.g., たべる -> たべない)",
            "te_form": "Drop る + て (e.g., たべる -> たべて)",
            "past": "Drop る + た (e.g., たべる -> たべた)",
            "potential": "Drop る + られる (e.g., たべる -> たべられる)",
            "volitional": "Drop る + よう (e.g., たべる -> たべよう)",
            "passive": "Drop る + られる (e.g., たべる -> たべられる)",
            "causative": "Drop る + させる (e.g., たべる -> たべさせる)",
            "imperative": "Drop る + ろ (e.g., たべる -> たべろ)",
            "conditional_ba": "Drop る + れば (e.g., たべる -> たべれば)",
        },
    },
    "irregular_rules": {
        "description": "Irregular verbs: する (to do) and くる (to come) have unique conjugation patterns.",
        "monument_id": 4,
        "suru": {
            "dictionary": "する",
            "masu": "します",
            "nai": "しない",
            "te_form": "して",
            "past": "した",
            "potential": "できる",
            "volitional": "しよう",
            "passive": "される",
            "causative": "させる",
            "imperative": "しろ",
            "conditional_ba": "すれば",
        },
        "kuru": {
            "dictionary": "くる",
            "masu": "きます",
            "nai": "こない",
            "te_form": "きて",
            "past": "きた",
            "potential": "こられる",
            "volitional": "こよう",
            "passive": "こられる",
            "causative": "こさせる",
            "imperative": "こい",
            "conditional_ba": "くれば",
        },
    },
}

# =============================================================================
# GRAMMAR LESSONS
# =============================================================================

GRAMMAR_LESSONS = [
    {
        "lesson_id": "gram_l01",
        "title": "Your First Japanese Sentence",
        "description": "Learn SOV word order and the topic marker は.",
        "grammar_points": ["gram_b01", "gram_b02"],
        "monument_id": 2,
    },
    {
        "lesson_id": "gram_l02",
        "title": "Essential Particles: が, を, に",
        "description": "Master the three most important particles for basic sentences.",
        "grammar_points": ["gram_b03", "gram_b04", "gram_b05"],
        "monument_id": 2,
    },
    {
        "lesson_id": "gram_l03",
        "title": "More Particles: で, へ, も, の",
        "description": "Expand your particle knowledge for more complex expressions.",
        "grammar_points": ["gram_b06", "gram_b07", "gram_b08", "gram_b09"],
        "monument_id": 2,
    },
    {
        "lesson_id": "gram_l04",
        "title": "Questions and Sentence Endings",
        "description": "Learn to ask questions and add nuance with sentence-ending particles.",
        "grammar_points": ["gram_b10", "gram_b11", "gram_b12"],
        "monument_id": 2,
    },
    {
        "lesson_id": "gram_l05",
        "title": "Polite Speech and Demonstratives",
        "description": "Master desu/masu and the ko-so-a-do demonstrative system.",
        "grammar_points": ["gram_b13", "gram_b14"],
        "monument_id": 2,
    },
    {
        "lesson_id": "gram_l06",
        "title": "The Versatile Te-form",
        "description": "Unlock the te-form for requests, progressive actions, and connecting sentences.",
        "grammar_points": ["gram_i01", "gram_i02", "gram_i03"],
        "monument_id": 7,
    },
    {
        "lesson_id": "gram_l07",
        "title": "Expressing Conditions",
        "description": "Learn all four conditional forms and when to use each one.",
        "grammar_points": ["gram_i04", "gram_i05", "gram_i06", "gram_i07"],
        "monument_id": 7,
    },
    {
        "lesson_id": "gram_l08",
        "title": "Voice: Passive and Causative",
        "description": "Express what happens to you and what you make/let others do.",
        "grammar_points": ["gram_i08", "gram_i09"],
        "monument_id": 7,
    },
    {
        "lesson_id": "gram_l09",
        "title": "Giving, Receiving, and Opinions",
        "description": "Navigate Japanese gift-giving verbs and express your thoughts.",
        "grammar_points": ["gram_i10", "gram_i11", "gram_i12"],
        "monument_id": 7,
    },
    {
        "lesson_id": "gram_l10",
        "title": "Ability and Desire",
        "description": "Express what you can do and what you want to do.",
        "grammar_points": ["gram_i13", "gram_i14"],
        "monument_id": 7,
    },
    {
        "lesson_id": "gram_l11",
        "title": "Keigo: The Art of Polite Japanese",
        "description": "Master honorific, humble, and polite speech levels.",
        "grammar_points": ["gram_a01", "gram_a02", "gram_a03"],
        "monument_id": 11,
    },
    {
        "lesson_id": "gram_l12",
        "title": "Advanced Expressions",
        "description": "Learn literary forms and nuanced expressions for fluency.",
        "grammar_points": ["gram_a04", "gram_a05", "gram_a06", "gram_a07", "gram_a08"],
        "monument_id": 11,
    },
]
