"""Local category bank used when no live LLM is available."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations


MAX_VARIANTS_PER_POOL = 80


@dataclass(frozen=True, slots=True)
class CategoryTemplate:
    category: str
    words: tuple[str, str, str, str]
    difficulty: str
    strategy: str
    explanation: str


CATEGORY_BANK: tuple[CategoryTemplate, ...] = (
    CategoryTemplate("Art materials", ("PAINT", "CLAY", "INK", "CHARCOAL"), "yellow", "semantic", "Each is a common material used to make visual art."),
    CategoryTemplate("___ LIGHT", ("GREEN", "RED", "STAGE", "TRAFFIC"), "green", "phrase_completion", "Each word commonly precedes LIGHT."),
    CategoryTemplate("Tea varieties", ("JASMINE", "OOLONG", "CHAI", "MATCHA"), "yellow", "semantic", "Each is a common kind of tea."),
    CategoryTemplate("Browser actions", ("BACK", "FORWARD", "REFRESH", "BOOKMARK"), "green", "semantic", "These are common actions in a web browser."),
    CategoryTemplate("Severe weather", ("BLIZZARD", "CYCLONE", "HAIL", "TORNADO"), "green", "semantic", "Each is a severe weather event or condition."),
    CategoryTemplate("Class standings", ("FRESHMAN", "SOPHOMORE", "JUNIOR", "SENIOR"), "yellow", "semantic", "Each is a common school-year standing."),
    CategoryTemplate("Units of time", ("SECOND", "MINUTE", "HOUR", "DAY"), "yellow", "semantic", "Each is a unit of time."),
    CategoryTemplate("Musical instruments", ("PIANO", "FLUTE", "DRUM", "GUITAR"), "yellow", "semantic", "Each is a common musical instrument."),
    CategoryTemplate("Pasta shapes", ("PENNE", "RIGATONI", "FUSILLI", "FARFALLE"), "yellow", "semantic", "Each is a pasta shape."),
    CategoryTemplate("Audio controls", ("VOLUME", "BALANCE", "BASS", "TREBLE"), "green", "semantic", "Each is a common audio setting or control."),
    CategoryTemplate("___ CAKE", ("CARROT", "CHEESE", "COFFEE", "POUND"), "green", "phrase_completion", "Each word forms a common compound or phrase with CAKE."),
    CategoryTemplate("Legal documents", ("CONTRACT", "DEED", "LEASE", "WILL"), "blue", "semantic", "Each is a legal document or legal instrument."),
    CategoryTemplate("Street types", ("AVENUE", "BOULEVARD", "LANE", "DRIVE"), "yellow", "semantic", "Each is a kind of road or street label."),
    CategoryTemplate("Newspaper sections", ("ARTS", "BUSINESS", "OPINION", "SPORTS"), "yellow", "semantic", "Each is a common newspaper section."),
    CategoryTemplate("___ BOX", ("JUICE", "LUNCH", "MAIL", "TOOL"), "green", "phrase_completion", "Each word forms a common compound with BOX."),
    CategoryTemplate("Palindromes", ("LEVEL", "RADAR", "CIVIC", "KAYAK"), "purple", "wordplay", "Each word reads the same backward and forward."),
    CategoryTemplate("Flowers", ("IRIS", "TULIP", "DAISY", "VIOLET"), "yellow", "semantic", "Each is a flower."),
    CategoryTemplate("Camera settings", ("FOCUS", "EXPOSURE", "ISO", "SHUTTER"), "green", "semantic", "Each is a camera or photography setting."),
    CategoryTemplate("___BOARD compounds", ("DASH", "KEY", "SCORE", "SKATE"), "green", "phrase_completion", "Each word forms a familiar one-word compound ending in BOARD."),
    CategoryTemplate("Tiny amounts", ("DASH", "PINCH", "TRACE", "DROP"), "blue", "semantic", "Each can mean a small amount."),
    CategoryTemplate("Theater features", ("AISLE", "BALCONY", "CURTAIN", "STAGE"), "yellow", "semantic", "Each is a familiar theater feature."),
    CategoryTemplate("Computer file actions", ("COPY", "PASTE", "SAVE", "DELETE"), "yellow", "semantic", "Each is a common file or editing action."),
    CategoryTemplate("Words ending in -IGHT", ("BRIGHT", "FLIGHT", "NIGHT", "SIGHT"), "purple", "wordplay", "Each word ends with the same pronounced letter pattern."),
    CategoryTemplate("Breakfast staples", ("BACON", "CEREAL", "OMELET", "TOAST"), "yellow", "semantic", "Each is commonly associated with breakfast."),
    CategoryTemplate("___ RING", ("CLASS", "ENGAGEMENT", "MOOD", "WEDDING"), "blue", "phrase_completion", "Each word forms a familiar phrase with RING."),
    CategoryTemplate("Weather measures", ("HUMIDITY", "PRESSURE", "TEMPERATURE", "VISIBILITY"), "green", "semantic", "Each is a weather measurement or reported condition."),
    CategoryTemplate("Keyboard keys", ("ESCAPE", "OPTION", "RETURN", "SHIFT"), "green", "semantic", "Each names a keyboard key."),
    CategoryTemplate("Book parts", ("COVER", "INDEX", "PREFACE", "SPINE"), "yellow", "semantic", "Each is a part of a book."),
    CategoryTemplate("___ MARK", ("BOOK", "CHECK", "QUESTION", "TRADE"), "green", "phrase_completion", "Each word forms a common compound or phrase with MARK."),
    CategoryTemplate("Card suits", ("CLUB", "DIAMOND", "HEART", "SPADE"), "yellow", "semantic", "Each is a suit in a standard deck of cards."),
    CategoryTemplate("Programming languages", ("BASIC", "GO", "JAVA", "RUST"), "blue", "wordplay", "Each word is also the name of a programming language."),
    CategoryTemplate("Kitchen tools", ("LADLE", "PEELER", "TONGS", "WHISK"), "yellow", "semantic", "Each is a common kitchen utensil."),
    CategoryTemplate("US coins", ("PENNY", "NICKEL", "DIME", "QUARTER"), "yellow", "semantic", "Each is a United States coin denomination."),
    CategoryTemplate("Paint finishes", ("MATTE", "GLOSS", "SATIN", "EGGSHELL"), "green", "semantic", "Each is a common paint finish."),
    CategoryTemplate("Map elements", ("BORDER", "LEGEND", "ROUTE", "SCALE"), "green", "semantic", "Each can appear on or around a map."),
    CategoryTemplate("Bakery items", ("BAGEL", "MUFFIN", "SCONE", "CROISSANT"), "yellow", "semantic", "Each is a common bakery item."),
    CategoryTemplate("Phone gestures", ("TAP", "SWIPE", "PINCH", "SCROLL"), "green", "semantic", "Each is a common touch-screen gesture."),
    CategoryTemplate("Fireplace parts", ("MANTEL", "HEARTH", "FLUE", "GRATE"), "blue", "semantic", "Each is part of a fireplace or chimney setup."),
    CategoryTemplate("Track events", ("HURDLES", "MILE", "RELAY", "SPRINT"), "green", "semantic", "Each is a track event."),
    CategoryTemplate("Fabric types", ("COTTON", "DENIM", "LINEN", "VELVET"), "yellow", "semantic", "Each is a common fabric."),
    CategoryTemplate("Chess pieces", ("KING", "QUEEN", "BISHOP", "ROOK"), "yellow", "semantic", "Each is a chess piece."),
    CategoryTemplate("___LINE compounds", ("AIR", "DEAD", "HEAD", "SKY"), "green", "phrase_completion", "Each word forms a familiar one-word compound ending in LINE."),
    CategoryTemplate("___ SCHOOL", ("HIGH", "LAW", "MEDICAL", "MIDDLE"), "green", "phrase_completion", "Each word forms a familiar phrase or compound with SCHOOL."),
    CategoryTemplate("___ STAR", ("GUEST", "MOVIE", "POP", "ROCK"), "green", "phrase_completion", "Each word forms a familiar phrase with STAR."),
    CategoryTemplate("Royal titles", ("DUKE", "EARL", "KING", "QUEEN"), "blue", "semantic", "Each is a royal or noble title."),
    CategoryTemplate("___BIRD compounds", ("BLACK", "BLUE", "HUMMING", "MOCKING"), "blue", "phrase_completion", "Each word forms a familiar one-word compound ending in BIRD."),
    CategoryTemplate("___ PRESS", ("BENCH", "FRENCH", "GARLIC", "PRINTING"), "blue", "phrase_completion", "Each word forms a familiar phrase or compound with PRESS."),
    CategoryTemplate("___ SERVICE", ("CIVIL", "CUSTOMER", "ROOM", "SECRET"), "green", "phrase_completion", "Each word forms a familiar phrase with SERVICE."),
    CategoryTemplate("Homophones of letters", ("BEE", "EYE", "SEA", "TEA"), "purple", "wordplay", "Each word sounds like a letter name."),
    CategoryTemplate("Keyboard shortcuts", ("COPY", "CUT", "PASTE", "UNDO"), "blue", "semantic", "Each is a common keyboard shortcut action."),
    CategoryTemplate("Medieval weapons", ("AXE", "LANCE", "MACE", "SWORD"), "blue", "semantic", "Each is a medieval weapon."),
)


THEME_TITLES = (
    "After Hours Archive",
    "Campus Weather",
    "Kitchen Radio",
    "City Crossword",
    "Signal Garden",
    "Midnight Desk",
    "Quiet Terminal",
    "Paper Observatory",
)


@dataclass(frozen=True, slots=True)
class CategoryPool:
    category: str
    words: tuple[str, ...]
    difficulty: str
    strategy: str
    explanation: str


# Broad offline pools. Each pool yields many distinct 4-word groups. This keeps
# the live generator local and reproducible while giving large batches enough
# room to avoid repeatedly surfacing the same answer group.
SEMANTIC_POOLS: tuple[CategoryPool, ...] = (
    CategoryPool("Fruits", ("APPLE", "PEAR", "PLUM", "PEACH", "MANGO", "PAPAYA", "KIWI", "APRICOT"), "yellow", "semantic", "Each is a familiar fruit."),
    CategoryPool("Berries", ("STRAWBERRY", "BLUEBERRY", "RASPBERRY", "BLACKBERRY", "CRANBERRY", "GOOSEBERRY", "MULBERRY", "ELDERBERRY"), "yellow", "semantic", "Each is a berry or berry-named fruit."),
    CategoryPool("Vegetables", ("CARROT", "ONION", "PEPPER", "CELERY", "POTATO", "TURNIP", "RADISH", "CUCUMBER"), "yellow", "semantic", "Each is a common vegetable."),
    CategoryPool("Leafy greens", ("KALE", "CHARD", "SPINACH", "LETTUCE", "ARUGULA", "ENDIVE", "ROMAINE", "CABBAGE"), "yellow", "semantic", "Each is a leafy green."),
    CategoryPool("Herbs", ("BASIL", "DILL", "MINT", "SAGE", "THYME", "PARSLEY", "CILANTRO", "OREGANO"), "yellow", "semantic", "Each is a culinary herb."),
    CategoryPool("Spices", ("CUMIN", "CLOVE", "GINGER", "NUTMEG", "PAPRIKA", "SAFFRON", "TURMERIC", "CINNAMON"), "green", "semantic", "Each is a spice."),
    CategoryPool("Nuts", ("ALMOND", "CASHEW", "PECAN", "WALNUT", "PISTACHIO", "HAZELNUT", "PEANUT", "CHESTNUT"), "yellow", "semantic", "Each is a nut or culinary nut."),
    CategoryPool("Cheeses", ("BRIE", "CHEDDAR", "GOUDA", "SWISS", "FETA", "MOZZARELLA", "PROVOLONE", "RICOTTA"), "yellow", "semantic", "Each is a kind of cheese."),
    CategoryPool("Breads", ("BAGEL", "BAGUETTE", "BRIOCHE", "CIABATTA", "FOCACCIA", "PITA", "RYE", "SOURDOUGH"), "yellow", "semantic", "Each is a bread or bread style."),
    CategoryPool("Desserts", ("BROWNIE", "COOKIE", "CUPCAKE", "PIE", "PUDDING", "SORBET", "TART", "TRIFLE"), "yellow", "semantic", "Each is a dessert."),
    CategoryPool("Beverages", ("COFFEE", "TEA", "JUICE", "WATER", "LEMONADE", "SMOOTHIE", "CIDER", "SODA"), "yellow", "semantic", "Each is a drink."),
    CategoryPool("Coffee drinks", ("LATTE", "MOCHA", "ESPRESSO", "CAPPUCCINO", "AMERICANO", "MACCHIATO", "CORTADO", "RISTRETTO"), "green", "semantic", "Each is a coffee drink or espresso preparation."),
    CategoryPool("Tea varieties", ("JASMINE", "OOLONG", "CHAI", "MATCHA", "SENCHA", "ASSAM", "DARJEELING", "ROOIBOS"), "yellow", "semantic", "Each is a tea variety or tea style."),
    CategoryPool("Pasta shapes", ("PENNE", "RIGATONI", "FUSILLI", "FARFALLE", "ORZO", "LINGUINE", "RAVIOLI", "ZITI"), "yellow", "semantic", "Each is a pasta shape."),
    CategoryPool("Cooking verbs", ("BAKE", "BOIL", "BROIL", "FRY", "GRILL", "ROAST", "SAUTE", "STEAM"), "yellow", "semantic", "Each is a cooking method."),
    CategoryPool("Kitchen utensils", ("LADLE", "PEELER", "TONGS", "WHISK", "SPATULA", "GRATER", "SKEWER", "STRAINER"), "yellow", "semantic", "Each is a kitchen utensil."),
    CategoryPool("Cookware", ("PAN", "POT", "SKILLET", "WOK", "GRIDDLE", "KETTLE", "ROASTER", "SAUCEPAN"), "green", "semantic", "Each is cookware or a cooking vessel."),
    CategoryPool("Tableware", ("PLATE", "BOWL", "CUP", "SAUCER", "FORK", "SPOON", "NAPKIN", "TUMBLER"), "yellow", "semantic", "Each appears at a table setting."),
    CategoryPool("Condiments", ("KETCHUP", "MUSTARD", "MAYO", "RELISH", "SALSA", "PESTO", "CHUTNEY", "SRIRACHA"), "green", "semantic", "Each is a condiment or sauce."),
    CategoryPool("Breakfast foods", ("BACON", "CEREAL", "OMELET", "TOAST", "WAFFLE", "PANCAKE", "GRITS", "YOGURT"), "yellow", "semantic", "Each is commonly associated with breakfast."),
    CategoryPool("Mammals", ("BEAR", "FOX", "MOOSE", "OTTER", "RABBIT", "WHALE", "ZEBRA", "BISON"), "yellow", "semantic", "Each is a mammal."),
    CategoryPool("Birds", ("ROBIN", "EAGLE", "FALCON", "SPARROW", "HERON", "RAVEN", "SWAN", "TURKEY"), "yellow", "semantic", "Each is a bird."),
    CategoryPool("Sea creatures", ("CLAM", "CRAB", "EEL", "OYSTER", "SHARK", "SQUID", "TROUT", "TUNA"), "yellow", "semantic", "Each is a sea or water creature."),
    CategoryPool("Insects", ("ANT", "BEE", "MOTH", "WASP", "BEETLE", "CICADA", "CRICKET", "TERMITE"), "yellow", "semantic", "Each is an insect."),
    CategoryPool("Dog breeds", ("BEAGLE", "BOXER", "COLLIE", "POODLE", "HUSKY", "MALTESE", "MASTIFF", "TERRIER"), "green", "semantic", "Each is a dog breed."),
    CategoryPool("Cat breeds", ("BENGAL", "BURMESE", "PERSIAN", "SIAMESE", "SPHYNX", "RAGDOLL", "SIBERIAN", "MANX"), "green", "semantic", "Each is a cat breed."),
    CategoryPool("Animal sounds", ("BARK", "BUZZ", "CHIRP", "GROWL", "HISS", "HOWL", "MEOW", "ROAR"), "green", "semantic", "Each can be an animal sound."),
    CategoryPool("Farm animals", ("COW", "GOAT", "HORSE", "LLAMA", "PIG", "SHEEP", "TURKEY", "DONKEY"), "yellow", "semantic", "Each is a farm animal."),
    CategoryPool("Reptiles and amphibians", ("FROG", "GECKO", "IGUANA", "LIZARD", "NEWT", "TOAD", "TURTLE", "VIPER"), "green", "semantic", "Each is a reptile or amphibian."),
    CategoryPool("Trees", ("ASH", "BIRCH", "CEDAR", "ELM", "MAPLE", "OAK", "PINE", "WILLOW"), "yellow", "semantic", "Each is a tree."),
    CategoryPool("Flowers", ("IRIS", "TULIP", "DAISY", "VIOLET", "ROSE", "LILY", "ORCHID", "PEONY"), "yellow", "semantic", "Each is a flower."),
    CategoryPool("Gemstones", ("AMBER", "AMETHYST", "EMERALD", "GARNET", "JADE", "OPAL", "RUBY", "SAPPHIRE"), "green", "semantic", "Each is a gemstone or gem material."),
    CategoryPool("Metals", ("COPPER", "GOLD", "IRON", "LEAD", "NICKEL", "SILVER", "TIN", "ZINC"), "yellow", "semantic", "Each is a metal."),
    CategoryPool("Severe weather", ("BLIZZARD", "CYCLONE", "HAIL", "TORNADO", "DROUGHT", "FLOOD", "MONSOON", "SQUALL"), "green", "semantic", "Each is a severe weather event or condition."),
    CategoryPool("Weather measures", ("HUMIDITY", "PRESSURE", "TEMPERATURE", "VISIBILITY", "DEWPOINT", "RAINFALL", "WINDCHILL", "BAROMETER"), "green", "semantic", "Each is tied to measuring or reporting weather."),
    CategoryPool("Cloud types", ("CIRRUS", "CUMULUS", "STRATUS", "NIMBUS", "ALTO", "MAMMATUS", "SCUD", "SHELF"), "blue", "semantic", "Each is a cloud type or cloud term."),
    CategoryPool("Landforms", ("CANYON", "CLIFF", "DELTA", "DUNE", "MESA", "PLATEAU", "VALLEY", "VOLCANO"), "yellow", "semantic", "Each is a landform."),
    CategoryPool("Bodies of water", ("BAY", "CANAL", "GULF", "LAKE", "POND", "RIVER", "STRAIT", "STREAM"), "yellow", "semantic", "Each is a body or channel of water."),
    CategoryPool("Space objects", ("ASTEROID", "COMET", "GALAXY", "METEOR", "MOON", "PLANET", "STAR", "NEBULA"), "yellow", "semantic", "Each is an object or feature in space."),
    CategoryPool("Solar system names", ("MERCURY", "VENUS", "EARTH", "MARS", "JUPITER", "SATURN", "URANUS", "NEPTUNE"), "yellow", "semantic", "Each is a planet in the solar system."),
    CategoryPool("Zodiac signs", ("ARIES", "TAURUS", "GEMINI", "CANCER", "LEO", "VIRGO", "LIBRA", "SCORPIO"), "green", "semantic", "Each is a zodiac sign."),
    CategoryPool("Musical instruments", ("PIANO", "FLUTE", "DRUM", "GUITAR", "VIOLIN", "CELLO", "TRUMPET", "CLARINET"), "yellow", "semantic", "Each is a musical instrument."),
    CategoryPool("Music genres", ("JAZZ", "BLUES", "FUNK", "SOUL", "COUNTRY", "DISCO", "REGGAE", "TECHNO"), "yellow", "semantic", "Each is a music genre."),
    CategoryPool("Art media", ("PAINT", "CLAY", "INK", "CHARCOAL", "PASTEL", "PENCIL", "WATERCOLOR", "CRAYON"), "yellow", "semantic", "Each is a material or medium used for art."),
    CategoryPool("Paint finishes", ("MATTE", "GLOSS", "SATIN", "EGGSHELL", "FLAT", "LUSTER", "PEARL", "METALLIC"), "green", "semantic", "Each is used to describe a paint or surface finish."),
    CategoryPool("Camera terms", ("FOCUS", "EXPOSURE", "ISO", "SHUTTER", "APERTURE", "FLASH", "LENS", "TRIPOD"), "green", "semantic", "Each is a camera or photography term."),
    CategoryPool("Theater terms", ("AISLE", "BALCONY", "CURTAIN", "STAGE", "ORCHESTRA", "PLAYBILL", "PROP", "WING"), "yellow", "semantic", "Each is a theater term."),
    CategoryPool("Film genres", ("ACTION", "COMEDY", "DRAMA", "HORROR", "MUSICAL", "ROMANCE", "THRILLER", "WESTERN"), "yellow", "semantic", "Each is a film genre."),
    CategoryPool("Book parts", ("COVER", "INDEX", "PREFACE", "SPINE", "CHAPTER", "GLOSSARY", "PROLOGUE", "TITLE"), "yellow", "semantic", "Each is a part of a book."),
    CategoryPool("Newspaper sections", ("ARTS", "BUSINESS", "OPINION", "SPORTS", "STYLE", "TRAVEL", "WEATHER", "OBITUARIES"), "yellow", "semantic", "Each is a newspaper section."),
    CategoryPool("Card games", ("BRIDGE", "CANASTA", "CRIBBAGE", "EUCHRE", "HEARTS", "PINOCHLE", "POKER", "SPADES"), "green", "semantic", "Each is a card game."),
    CategoryPool("Playing card terms", ("ACE", "CLUB", "DIAMOND", "HEART", "JACK", "KING", "QUEEN", "SPADE"), "yellow", "semantic", "Each is a standard playing-card term."),
    CategoryPool("Board games", ("CHESS", "CHECKERS", "MONOPOLY", "RISK", "SCRABBLE", "SORRY", "TROUBLE", "YAHTZEE"), "green", "semantic", "Each is a board or tabletop game."),
    CategoryPool("Chess terms", ("BISHOP", "CASTLE", "CHECK", "GAMBIT", "KNIGHT", "PAWN", "QUEEN", "ROOK"), "green", "semantic", "Each is a chess term."),
    CategoryPool("Track events", ("HURDLES", "MILE", "RELAY", "SPRINT", "DECATHLON", "MARATHON", "VAULT", "JAVELIN"), "green", "semantic", "Each is a track-and-field event."),
    CategoryPool("Swimming strokes", ("BACKSTROKE", "BREASTSTROKE", "BUTTERFLY", "FREESTYLE", "CRAWL", "MEDLEY", "SIDESTROKE", "DOGPADDLE"), "blue", "semantic", "Each is a swimming stroke or race style."),
    CategoryPool("Tennis terms", ("ACE", "DEUCE", "FAULT", "LOB", "RALLY", "SERVE", "SLICE", "VOLLEY"), "green", "semantic", "Each is a tennis term."),
    CategoryPool("Baseball positions", ("CATCHER", "PITCHER", "SHORTSTOP", "OUTFIELDER", "FIRST", "SECOND", "THIRD", "CENTER"), "green", "semantic", "Each names or abbreviates a baseball position."),
    CategoryPool("Basketball terms", ("ASSIST", "BLOCK", "DRIBBLE", "DUNK", "FOUL", "REBOUND", "SCREEN", "STEAL"), "yellow", "semantic", "Each is a basketball term."),
    CategoryPool("Soccer roles", ("DEFENDER", "FORWARD", "GOALIE", "MIDFIELDER", "STRIKER", "WINGER", "KEEPER", "SWEEPER"), "green", "semantic", "Each is a soccer role."),
    CategoryPool("Golf terms", ("BIRDIE", "BOGEY", "CADDIE", "DRIVER", "EAGLE", "FAIRWAY", "GREEN", "PUTTER"), "green", "semantic", "Each is a golf term."),
    CategoryPool("Browser actions", ("BACK", "FORWARD", "REFRESH", "BOOKMARK", "DOWNLOAD", "SEARCH", "SHARE", "ZOOM"), "green", "semantic", "Each is a browser action."),
    CategoryPool("Keyboard keys", ("ESCAPE", "OPTION", "RETURN", "SHIFT", "CONTROL", "DELETE", "ENTER", "TAB"), "green", "semantic", "Each names a keyboard key."),
    CategoryPool("File actions", ("COPY", "PASTE", "SAVE", "DELETE", "OPEN", "PRINT", "RENAME", "UPLOAD"), "yellow", "semantic", "Each is a file or editing action."),
    CategoryPool("Programming languages", ("BASIC", "GO", "JAVA", "RUST", "PYTHON", "RUBY", "SCALA", "SWIFT"), "blue", "wordplay", "Each word is also the name of a programming language."),
    CategoryPool("Data units", ("BIT", "BYTE", "KILOBYTE", "MEGABYTE", "GIGABYTE", "TERABYTE", "NIBBLE", "WORD"), "blue", "semantic", "Each is a data-size or computing unit."),
    CategoryPool("Email fields", ("TO", "FROM", "CC", "BCC", "SUBJECT", "BODY", "ATTACHMENT", "SIGNATURE"), "green", "semantic", "Each appears in or around an email message."),
    CategoryPool("Phone gestures", ("TAP", "SWIPE", "PINCH", "SCROLL", "DRAG", "HOLD", "PRESS", "SHAKE"), "green", "semantic", "Each is a touchscreen gesture or action."),
    CategoryPool("Social media actions", ("LIKE", "SHARE", "POST", "FOLLOW", "BLOCK", "MUTE", "TAG", "COMMENT"), "yellow", "semantic", "Each is a social-media action."),
    CategoryPool("Office supplies", ("BINDER", "CLIP", "FOLDER", "PENCIL", "MARKER", "STAPLER", "TAPE", "ENVELOPE"), "yellow", "semantic", "Each is an office supply."),
    CategoryPool("School subjects", ("ALGEBRA", "BIOLOGY", "CHEMISTRY", "HISTORY", "GEOMETRY", "PHYSICS", "SPANISH", "WRITING"), "yellow", "semantic", "Each is a school subject."),
    CategoryPool("College terms", ("ASSOCIATE", "BACHELOR", "MASTER", "DOCTOR", "DIPLOMA", "MAJOR", "MINOR", "CERTIFICATE"), "blue", "semantic", "Each is related to college credentials or programs of study."),
    CategoryPool("Class standings", ("FRESHMAN", "SOPHOMORE", "JUNIOR", "SENIOR", "ALUMNUS", "GRADUATE", "TRANSFER", "VISITOR"), "green", "semantic", "Each can describe a student's school status."),
    CategoryPool("Road types", ("AVENUE", "BOULEVARD", "DRIVE", "LANE", "ROAD", "STREET", "TERRACE", "COURT"), "yellow", "semantic", "Each is a road or street label."),
    CategoryPool("Transit modes", ("BUS", "FERRY", "METRO", "TAXI", "TRAIN", "TRAM", "TROLLEY", "SUBWAY"), "yellow", "semantic", "Each is a transit mode."),
    CategoryPool("Airport words", ("ARRIVAL", "BAGGAGE", "BOARDING", "CUSTOMS", "DEPARTURE", "GATE", "LUGGAGE", "RUNWAY"), "yellow", "semantic", "Each is an airport term."),
    CategoryPool("Map elements", ("BORDER", "LEGEND", "ROUTE", "SCALE", "COMPASS", "GRID", "KEY", "SYMBOL"), "green", "semantic", "Each can appear on a map."),
    CategoryPool("Furniture", ("BENCH", "CHAIR", "COUCH", "DESK", "DRESSER", "SOFA", "STOOL", "TABLE"), "yellow", "semantic", "Each is furniture."),
    CategoryPool("Rooms", ("ATTIC", "CELLAR", "KITCHEN", "LOUNGE", "NURSERY", "OFFICE", "PANTRY", "STUDIO"), "yellow", "semantic", "Each is a room or interior space."),
    CategoryPool("Hand tools", ("HAMMER", "WRENCH", "PLIERS", "SAW", "DRILL", "CHISEL", "FILE", "LEVEL"), "yellow", "semantic", "Each is a hand tool."),
    CategoryPool("Fasteners", ("BOLT", "BRAD", "CLAMP", "NAIL", "PIN", "RIVET", "SCREW", "TACK"), "green", "semantic", "Each fastens or secures something."),
    CategoryPool("Fabric types", ("COTTON", "DENIM", "LINEN", "VELVET", "CANVAS", "FLEECE", "SATIN", "TWEED"), "yellow", "semantic", "Each is a fabric."),
    CategoryPool("Clothing items", ("BLAZER", "COAT", "DRESS", "JACKET", "PANTS", "SHIRT", "SKIRT", "SWEATER"), "yellow", "semantic", "Each is an item of clothing."),
    CategoryPool("Shoe types", ("BOOT", "CLOG", "LOAFER", "SANDAL", "SNEAKER", "SLIPPER", "OXFORD", "MULE"), "green", "semantic", "Each is a shoe type."),
    CategoryPool("Jewelry", ("BRACELET", "BROOCH", "EARRING", "LOCKET", "NECKLACE", "PENDANT", "RING", "TIARA"), "green", "semantic", "Each is jewelry."),
    CategoryPool("Makeup items", ("BLUSH", "BRONZER", "CONCEALER", "EYELINER", "FOUNDATION", "MASCARA", "POWDER", "PRIMER"), "green", "semantic", "Each is a makeup item."),
    CategoryPool("Colors", ("AMBER", "CORAL", "INDIGO", "LAVENDER", "MAROON", "SCARLET", "TEAL", "VIOLET"), "yellow", "semantic", "Each is a color."),
    CategoryPool("Textures", ("COARSE", "FUZZY", "GRAINY", "ROUGH", "SATINY", "SILKY", "SMOOTH", "VELVETY"), "green", "semantic", "Each describes texture."),
    CategoryPool("Shapes", ("CIRCLE", "CONE", "CUBE", "OVAL", "RECTANGLE", "SPHERE", "SQUARE", "TRIANGLE"), "yellow", "semantic", "Each is a geometric shape."),
    CategoryPool("Math terms", ("ANGLE", "AXIS", "CURVE", "FACTOR", "GRAPH", "RADIUS", "SLOPE", "VECTOR"), "green", "semantic", "Each is a math term."),
)


PHRASE_POOLS: tuple[CategoryPool, ...] = (
    CategoryPool("___ LIGHT", ("GREEN", "RED", "STAGE", "TRAFFIC", "FLASH", "NIGHT", "SUN", "MOON"), "green", "phrase_completion", "Each word forms a common phrase or compound with LIGHT."),
    CategoryPool("___ BOARD", ("DASH", "KEY", "SCORE", "SKATE", "CLIP", "SURF", "CHESS", "CIRCUIT"), "green", "phrase_completion", "Each word forms a common phrase or compound with BOARD."),
    CategoryPool("___ RING", ("CLASS", "ENGAGEMENT", "MOOD", "WEDDING", "KEY", "ONION", "BOXING", "NAPKIN"), "blue", "phrase_completion", "Each word forms a common phrase or compound with RING."),
    CategoryPool("___ STAR", ("GUEST", "MOVIE", "POP", "ROCK", "NORTH", "SHOOTING", "SEA", "FALLING"), "green", "phrase_completion", "Each word forms a common phrase or compound with STAR."),
    CategoryPool("___ BOX", ("JUICE", "LUNCH", "MAIL", "TOOL", "SHADOW", "MUSIC", "BLACK", "BALLOT"), "green", "phrase_completion", "Each word forms a common phrase or compound with BOX."),
    CategoryPool("___ MARK", ("BOOK", "CHECK", "QUESTION", "TRADE", "BENCH", "BIRTH", "WATER", "POST"), "green", "phrase_completion", "Each word forms a common phrase or compound with MARK."),
    CategoryPool("___ SCHOOL", ("HIGH", "LAW", "MEDICAL", "MIDDLE", "GRADE", "SUMMER", "NIGHT", "CHARTER"), "green", "phrase_completion", "Each word forms a common phrase or compound with SCHOOL."),
    CategoryPool("___ SERVICE", ("CIVIL", "CUSTOMER", "ROOM", "SECRET", "TABLE", "WIRE", "FOOD", "POSTAL"), "green", "phrase_completion", "Each word forms a common phrase or compound with SERVICE."),
    CategoryPool("___ BIRD", ("BLACK", "BLUE", "HUMMING", "MOCKING", "LOVE", "SONG", "JAIL", "SNOW"), "blue", "phrase_completion", "Each word forms a common phrase or compound with BIRD."),
    CategoryPool("___ PRESS", ("BENCH", "FRENCH", "GARLIC", "PRINTING", "FREE", "CHEST", "COOKIE", "WINE"), "blue", "phrase_completion", "Each word forms a common phrase or compound with PRESS."),
    CategoryPool("___ LINE", ("AIR", "DEAD", "HEAD", "SKY", "BASE", "FINE", "FRONT", "FINISH"), "green", "phrase_completion", "Each word forms a common phrase or compound with LINE."),
    CategoryPool("___ HOUSE", ("GREEN", "LIGHT", "DOG", "TREE", "FIRE", "COURT", "FARM", "TOWN"), "green", "phrase_completion", "Each word forms a common phrase or compound with HOUSE."),
    CategoryPool("___ WATER", ("BATH", "DISH", "FRESH", "SALT", "RAIN", "GROUND", "SEA", "WASTE"), "green", "phrase_completion", "Each word forms a common compound with WATER."),
    CategoryPool("___ FIRE", ("CAMP", "WILD", "FOREST", "HOUSE", "BRUSH", "CROSS", "CEASE", "GUN"), "blue", "phrase_completion", "Each word forms a common compound or phrase with FIRE."),
    CategoryPool("___ BALL", ("BASE", "BASKET", "FOOT", "VOLLEY", "SNOW", "MEAT", "FIRE", "CANNON"), "yellow", "phrase_completion", "Each word forms a common compound or phrase with BALL."),
    CategoryPool("___ GAME", ("BOARD", "CARD", "VIDEO", "WORD", "MIND", "BALL", "END", "NAME"), "green", "phrase_completion", "Each word forms a common phrase or compound with GAME."),
    CategoryPool("___ TIME", ("BED", "DAY", "NIGHT", "LUNCH", "PRIME", "SHOW", "FACE", "SCREEN"), "green", "phrase_completion", "Each word forms a common phrase or compound with TIME."),
    CategoryPool("___ BOOK", ("ADDRESS", "CHECK", "COOK", "NOTE", "PHONE", "SCRAP", "TEXT", "WORK"), "yellow", "phrase_completion", "Each word forms a common phrase or compound with BOOK."),
    CategoryPool("___ CARD", ("CREDIT", "DEBIT", "GIFT", "REPORT", "SCORE", "POST", "FLASH", "INDEX"), "yellow", "phrase_completion", "Each word forms a common phrase or compound with CARD."),
    CategoryPool("___ ROOM", ("BED", "BATH", "CLASS", "COURT", "DARK", "GREEN", "SHOW", "BALL"), "green", "phrase_completion", "Each word forms a common compound or phrase with ROOM."),
    CategoryPool("___ WORK", ("HOME", "HOUSE", "FIELD", "TEAM", "ROAD", "YARD", "PAPER", "SCHOOL"), "green", "phrase_completion", "Each word forms a common compound or phrase with WORK."),
    CategoryPool("___ TABLE", ("COFFEE", "PERIODIC", "ROUND", "DINNER", "CARD", "WATER", "PIVOT", "TIME"), "blue", "phrase_completion", "Each word forms a common phrase or compound with TABLE."),
    CategoryPool("___ MAIL", ("AIR", "ELECTRONIC", "VOICE", "SNAIL", "JUNK", "CHAIN", "BLACK", "FAN"), "blue", "phrase_completion", "Each word forms a common phrase or compound with MAIL."),
    CategoryPool("___ KEY", ("ALT", "ARROW", "CAR", "HOUSE", "LOW", "MASTER", "PIANO", "ROOM"), "green", "phrase_completion", "Each word forms a common phrase or compound with KEY."),
)


WORDPLAY_POOLS: tuple[CategoryPool, ...] = (
    CategoryPool("Palindromes", ("LEVEL", "RADAR", "CIVIC", "KAYAK", "ROTOR", "MADAM", "REFER", "TENET"), "purple", "wordplay", "Each word reads the same forward and backward."),
    CategoryPool("Homophones of letters", ("BEE", "SEA", "TEA", "EYE", "YOU", "WHY", "ARE", "QUEUE"), "purple", "wordplay", "Each word sounds like a letter name."),
    CategoryPool("Words ending in -IGHT", ("BRIGHT", "FLIGHT", "NIGHT", "SIGHT", "LIGHT", "FIGHT", "MIGHT", "TIGHT"), "purple", "wordplay", "Each word ends with the same pronounced letter pattern."),
    CategoryPool("Words ending in -OUND", ("FOUND", "GROUND", "SOUND", "ROUND", "HOUND", "POUND", "BOUND", "WOUND"), "purple", "wordplay", "Each word ends with the same pronounced pattern."),
    CategoryPool("Words with silent first letters", ("KNEE", "KNIFE", "KNOCK", "KNIGHT", "WRIST", "WRONG", "WRECK", "WRITE"), "purple", "wordplay", "Each begins with a silent letter."),
    CategoryPool("NATO alphabet words", ("ALFA", "BRAVO", "CHARLIE", "DELTA", "ECHO", "FOXTROT", "GOLF", "HOTEL"), "blue", "wordplay", "Each is a NATO phonetic alphabet code word."),
    CategoryPool("Words beginning with TRI-", ("TRIANGLE", "TRIPOD", "TRILOGY", "TRIDENT", "TRICYCLE", "TRIO", "TRIPLE", "TRIVIA"), "purple", "wordplay", "Each begins with the TRI sound or spelling."),
    CategoryPool("Words ending in -ING", ("RING", "KING", "SING", "BRING", "STRING", "SPRING", "SWING", "THING"), "purple", "wordplay", "Each ends with the same letter pattern."),
    CategoryPool("Rhymes with TIME", ("DIME", "LIME", "MIME", "PRIME", "RHYME", "SLIME", "CHIME", "CRIME"), "purple", "wordplay", "Each rhymes with TIME."),
    CategoryPool("Words with silent B", ("LAMB", "COMB", "THUMB", "DOUBT", "DEBT", "SUBTLE", "CLIMB", "BOMB"), "purple", "wordplay", "Each contains a silent B."),
    CategoryPool("Words ending in -AIR", ("CHAIR", "FAIR", "FLAIR", "HAIR", "PAIR", "STAIR", "SQUARE", "PRAYER"), "purple", "wordplay", "Each ends with an AIR sound."),
    CategoryPool("Words ending in -OCK", ("BLOCK", "CLOCK", "FLOCK", "KNOCK", "LOCK", "ROCK", "SHOCK", "STOCK"), "purple", "wordplay", "Each ends with the OCK sound."),
    CategoryPool("Words ending in -ARK", ("BARK", "DARK", "LARK", "MARK", "PARK", "SHARK", "SPARK", "STARK"), "purple", "wordplay", "Each ends with the ARK sound."),
    CategoryPool("Words ending in -EEL", ("FEEL", "HEEL", "KEEL", "PEEL", "REEL", "STEEL", "WHEEL", "EEL"), "purple", "wordplay", "Each ends with an EEL sound."),
    CategoryPool("Words ending in -ATE", ("DATE", "FATE", "GATE", "LATE", "MATE", "PLATE", "RATE", "STATE"), "purple", "wordplay", "Each ends with the ATE sound."),
    CategoryPool("Words ending in -ASH", ("BASH", "CASH", "CLASH", "DASH", "FLASH", "MASH", "SLASH", "TRASH"), "purple", "wordplay", "Each ends with the ASH sound."),
)


ADDITIONAL_SEMANTIC_POOLS: tuple[CategoryPool, ...] = tuple(
    CategoryPool(category, words, difficulty, "semantic", explanation)
    for category, words, difficulty, explanation in (
        ("Days of the week", ("MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"), "yellow", "Each is a day of the week."),
        ("Months", ("JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE", "JULY", "AUGUST", "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER"), "yellow", "Each is a month."),
        ("Punctuation marks", ("COMMA", "PERIOD", "COLON", "DASH", "HYPHEN", "APOSTROPHE", "QUOTE", "QUESTION"), "green", "Each is a punctuation mark or punctuation term."),
        ("Parts of speech", ("NOUN", "VERB", "ADJECTIVE", "ADVERB", "PRONOUN", "PREPOSITION", "CONJUNCTION", "ARTICLE"), "green", "Each is a part of speech."),
        ("Body parts", ("ARM", "LEG", "HAND", "FOOT", "EYE", "EAR", "NOSE", "MOUTH"), "yellow", "Each is a body part."),
        ("Organs", ("HEART", "LIVER", "LUNG", "KIDNEY", "BRAIN", "STOMACH", "SPLEEN", "PANCREAS"), "green", "Each is an organ."),
        ("Bones", ("SKULL", "RIB", "FEMUR", "TIBIA", "FIBULA", "HUMERUS", "PELVIS", "VERTEBRA"), "blue", "Each is a bone or skeletal structure."),
        ("Medical jobs", ("DENTIST", "SURGEON", "NURSE", "DOCTOR", "THERAPIST", "PHARMACIST", "OPTOMETRIST", "PARAMEDIC"), "green", "Each is a medical or health-care role."),
        ("Occupations", ("PLUMBER", "BARBER", "BAKER", "PILOT", "FARMER", "NURSE", "TEACHER", "WAITER"), "yellow", "Each is an occupation."),
        ("Famous scientists", ("CURIE", "DARWIN", "EINSTEIN", "GALILEO", "NEWTON", "PASTEUR", "TESLA", "TURING"), "blue", "Each is the surname of a famous scientist or mathematician."),
        ("U.S. states", ("ALASKA", "ARIZONA", "FLORIDA", "GEORGIA", "MONTANA", "NEVADA", "OREGON", "VERMONT"), "green", "Each is a U.S. state."),
        ("State capitals", ("ALBANY", "AUSTIN", "BOSTON", "DENVER", "DOVER", "HELENA", "MADISON", "PHOENIX"), "blue", "Each is a U.S. state capital."),
        ("Countries", ("BRAZIL", "CANADA", "CHINA", "EGYPT", "FRANCE", "INDIA", "JAPAN", "MEXICO"), "yellow", "Each is a country."),
        ("Currencies", ("DOLLAR", "EURO", "PESO", "POUND", "YEN", "RUPEE", "FRANC", "KRONA"), "green", "Each is a currency."),
        ("Languages", ("ARABIC", "ENGLISH", "FRENCH", "GERMAN", "HINDI", "ITALIAN", "SPANISH", "SWAHILI"), "yellow", "Each is a language."),
        ("World cities", ("CAIRO", "DELHI", "LONDON", "PARIS", "ROME", "SEOUL", "SYDNEY", "TOKYO"), "yellow", "Each is a major world city."),
        ("U.S. cities", ("ATLANTA", "CHICAGO", "DALLAS", "DENVER", "MIAMI", "PHOENIX", "SEATTLE", "BOSTON"), "yellow", "Each is a U.S. city."),
        ("Rivers", ("AMAZON", "DANUBE", "GANGES", "HUDSON", "NILE", "RHINE", "SEINE", "THAMES"), "green", "Each is a river."),
        ("Mountain names", ("EVEREST", "FUJI", "KILIMANJARO", "DENALI", "OLYMPUS", "ROCKIES", "ANDES", "ALPS"), "green", "Each is a mountain or mountain range."),
        ("Islands", ("BALI", "CUBA", "CYPRUS", "HAITI", "ICELAND", "IRELAND", "JAVA", "SICILY"), "green", "Each is an island or island nation."),
        ("Seas and oceans", ("ATLANTIC", "PACIFIC", "INDIAN", "ARCTIC", "BALTIC", "CASPIAN", "CARIBBEAN", "MEDITERRANEAN"), "green", "Each names a sea or ocean."),
        ("Minerals", ("QUARTZ", "MICA", "TALC", "GYPSUM", "CALCITE", "FLUORITE", "HALITE", "GRAPHITE"), "blue", "Each is a mineral."),
        ("Chemical elements", ("CARBON", "OXYGEN", "HYDROGEN", "HELIUM", "NEON", "ARGON", "SODIUM", "CALCIUM"), "green", "Each is a chemical element."),
        ("Lab equipment", ("BEAKER", "FLASK", "PIPETTE", "BURETTE", "FUNNEL", "MICROSCOPE", "BURNER", "CENTRIFUGE"), "blue", "Each is used in a laboratory."),
        ("Scientific fields", ("BIOLOGY", "CHEMISTRY", "PHYSICS", "GEOLOGY", "ECOLOGY", "ASTRONOMY", "BOTANY", "ZOOLOGY"), "yellow", "Each is a scientific field."),
        ("Measurement units", ("INCH", "FOOT", "YARD", "MILE", "METER", "GRAM", "LITER", "SECOND"), "yellow", "Each is a unit of measurement."),
        ("Containers", ("BOTTLE", "BOX", "CAN", "CARTON", "JAR", "POUCH", "TUBE", "VIAL"), "yellow", "Each is a container."),
        ("Store types", ("BAKERY", "BUTCHER", "DELI", "FLORIST", "GROCERY", "PHARMACY", "MARKET", "BOOKSTORE"), "yellow", "Each is a type of store."),
        ("Building parts", ("ROOF", "WALL", "FLOOR", "CEILING", "WINDOW", "DOOR", "STAIR", "PORCH"), "yellow", "Each is a building part."),
        ("House exterior features", ("FENCE", "GATE", "GUTTER", "SIDING", "SHUTTER", "CHIMNEY", "GARAGE", "DRIVEWAY"), "green", "Each is part of or near a house exterior."),
        ("Garden tools", ("HOE", "RAKE", "SHOVEL", "TROWEL", "PRUNER", "SHEARS", "HOSE", "SPADE"), "yellow", "Each is a garden tool."),
        ("Plant parts", ("ROOT", "STEM", "LEAF", "FLOWER", "SEED", "PETAL", "POLLEN", "BRANCH"), "yellow", "Each is part of a plant."),
        ("Writing formats", ("ESSAY", "EMAIL", "MEMO", "NOVEL", "POEM", "REPORT", "SCRIPT", "STORY"), "yellow", "Each is a writing format."),
        ("Typography terms", ("FONT", "KERNING", "LEADING", "SERIF", "TRACKING", "BASELINE", "ASCENDER", "DESCENDER"), "blue", "Each is a typography term."),
        ("Print production terms", ("BLEED", "CROP", "FOLD", "GUTTER", "MARGIN", "PROOF", "SPREAD", "TRIM"), "blue", "Each is a print production term."),
        ("Emotions", ("ANGER", "FEAR", "JOY", "PRIDE", "SHAME", "SURPRISE", "TRUST", "ENVY"), "yellow", "Each is an emotion."),
        ("Personality traits", ("BRAVE", "CALM", "KIND", "LOYAL", "PATIENT", "PROUD", "SHY", "WITTY"), "yellow", "Each is a personality trait."),
        ("Movement verbs", ("CRAWL", "DIVE", "GLIDE", "HOP", "LEAP", "MARCH", "SKIP", "SPRINT"), "yellow", "Each is a way to move."),
        ("Dance styles", ("BALLET", "DISCO", "FOXTROT", "SALSA", "TANGO", "WALTZ", "TAP", "SWING"), "green", "Each is a dance style."),
        ("Music notation terms", ("CLEF", "NOTE", "REST", "SHARP", "FLAT", "STAFF", "TEMPO", "MEASURE"), "green", "Each is a music notation term."),
        ("Voice types", ("ALTO", "BASS", "BARITONE", "SOPRANO", "TENOR", "CONTRALTO", "MEZZO", "FALSETTO"), "blue", "Each is a singing voice type or range term."),
        ("Literary forms", ("FABLE", "FANTASY", "MYSTERY", "SATIRE", "SONNET", "EPIC", "LEGEND", "MEMOIR"), "green", "Each is a literary form or genre."),
        ("Mythical creatures", ("DRAGON", "FAIRY", "GIANT", "KRAKEN", "MERMAID", "PHOENIX", "UNICORN", "GRIFFIN"), "green", "Each is a mythical creature."),
        ("Casino games", ("BACCARAT", "BLACKJACK", "CRAPS", "ROULETTE", "SLOTS", "KENO", "LOTTERY", "BINGO"), "green", "Each is a casino or chance game."),
        ("Holidays", ("EASTER", "HALLOWEEN", "HANUKKAH", "KWANZAA", "PASSOVER", "RAMADAN", "THANKSGIVING", "CHRISTMAS"), "yellow", "Each is a holiday or observance."),
        ("Greek letters", ("ALPHA", "BETA", "GAMMA", "DELTA", "EPSILON", "THETA", "LAMBDA", "OMEGA"), "blue", "Each is a Greek letter name."),
        ("Computer hardware", ("MONITOR", "KEYBOARD", "MOUSE", "PRINTER", "ROUTER", "SCANNER", "SPEAKER", "WEBCAM"), "yellow", "Each is computer hardware."),
        ("Software terms", ("APP", "BROWSER", "DRIVER", "KERNEL", "PATCH", "SERVER", "WIDGET", "WINDOW"), "green", "Each is a software or computing term."),
        ("Cybersecurity terms", ("FIREWALL", "MALWARE", "PHISHING", "SPAM", "TOKEN", "VIRUS", "ENCRYPTION", "PASSWORD"), "blue", "Each is a cybersecurity term."),
        ("Finance terms", ("BOND", "BUDGET", "CREDIT", "DEBT", "EQUITY", "INVOICE", "PROFIT", "TAX"), "green", "Each is a finance term."),
        ("Banking terms", ("ACCOUNT", "BALANCE", "CHECK", "DEPOSIT", "INTEREST", "LOAN", "SAVINGS", "WITHDRAWAL"), "green", "Each is a banking term."),
        ("Insurance types", ("AUTO", "HEALTH", "HOME", "LIFE", "RENTERS", "TRAVEL", "DENTAL", "VISION"), "green", "Each is an insurance type or coverage area."),
        ("Civic offices", ("MAYOR", "GOVERNOR", "SENATOR", "PRESIDENT", "JUDGE", "SHERIFF", "TREASURER", "CLERK"), "green", "Each is a civic or public office."),
        ("Court terms", ("APPEAL", "CASE", "COURT", "JURY", "LAWYER", "MOTION", "VERDICT", "WITNESS"), "green", "Each is a court or legal term."),
        ("Military ranks", ("CAPTAIN", "COLONEL", "CORPORAL", "GENERAL", "MAJOR", "PRIVATE", "SERGEANT", "ADMIRAL"), "green", "Each is a military rank."),
        ("Family relations", ("AUNT", "BROTHER", "COUSIN", "FATHER", "MOTHER", "SISTER", "UNCLE", "NIECE"), "yellow", "Each is a family relation."),
        ("Baby items", ("BIB", "CRIB", "DIAPER", "PACIFIER", "RATTLE", "STROLLER", "ONESIE", "BOTTLE"), "yellow", "Each is an item for a baby."),
        ("Measuring tools", ("COMPASS", "RULER", "SCALE", "THERMOMETER", "TIMER", "GAUGE", "METER", "PROTRACTOR"), "green", "Each is a measuring tool."),
        ("Sewing items", ("NEEDLE", "THREAD", "THIMBLE", "BUTTON", "ZIPPER", "SEAM", "PIN", "SCISSORS"), "yellow", "Each is used in sewing or tailoring."),
        ("Hair salon terms", ("BANGS", "BRAID", "CURL", "DYE", "LAYER", "PERM", "TRIM", "WAVE"), "yellow", "Each is a hair salon term."),
        ("Spa services", ("FACIAL", "MASSAGE", "MANICURE", "PEDICURE", "SAUNA", "WAX", "WRAP", "SCRUB"), "green", "Each is a spa service or treatment."),
        ("Car parts", ("BRAKE", "BUMPER", "CLUTCH", "ENGINE", "FENDER", "HOOD", "MIRROR", "TIRE"), "yellow", "Each is a car part."),
        ("Traffic sign words", ("STOP", "YIELD", "MERGE", "DETOUR", "CROSSWALK", "EXIT", "SPEED", "SCHOOL"), "yellow", "Each commonly appears on a road sign."),
    )
)


def _variant_groups(words: tuple[str, ...]) -> tuple[tuple[str, str, str, str], ...]:
    normalized = tuple(dict.fromkeys(str(word).upper() for word in words))
    all_groups = [_as_group(combo) for combo in combinations(normalized, 4)]
    if len(all_groups) <= MAX_VARIANTS_PER_POOL:
        return tuple(all_groups)

    # Preserve broad coverage without letting a long pool dominate the bank.
    selected: list[tuple[str, str, str, str]] = []
    seen: set[tuple[str, ...]] = set()
    stride = max(1, len(all_groups) // MAX_VARIANTS_PER_POOL)
    for index in range(0, len(all_groups), stride):
        group = all_groups[index]
        signature = tuple(sorted(group))
        if signature in seen:
            continue
        seen.add(signature)
        selected.append(group)
        if len(selected) >= MAX_VARIANTS_PER_POOL:
            break
    return tuple(selected)


def _as_group(words: tuple[str, ...]) -> tuple[str, str, str, str]:
    return (str(words[0]).upper(), str(words[1]).upper(), str(words[2]).upper(), str(words[3]).upper())


def _expanded_category_bank() -> tuple[CategoryTemplate, ...]:
    templates = [
        CategoryTemplate(
            template.category,
            template.words,
            template.difficulty,
            template.strategy,
            _complete_explanation(template.explanation),
        )
        for template in CATEGORY_BANK
    ]
    seen = {tuple(sorted(template.words)) for template in templates}
    for pool in SEMANTIC_POOLS + ADDITIONAL_SEMANTIC_POOLS + PHRASE_POOLS + WORDPLAY_POOLS:
        for words in _variant_groups(pool.words):
            signature = tuple(sorted(words))
            if signature in seen:
                continue
            seen.add(signature)
            templates.append(CategoryTemplate(pool.category, words, pool.difficulty, pool.strategy, _complete_explanation(pool.explanation)))
    return tuple(templates)


def _complete_explanation(explanation: str) -> str:
    if len(explanation.strip().split()) >= 6:
        return explanation
    return explanation.rstrip(".") + "; the category is familiar and concrete."


CATEGORY_BANK = _expanded_category_bank()
THEME_TITLES = ()
COMMON_WORDS = frozenset(word for template in CATEGORY_BANK for word in template.words)
