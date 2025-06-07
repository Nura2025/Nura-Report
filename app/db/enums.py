from enum import Enum

class Gender(str, Enum):
    male = "male"
    female = "female"
    other = "other"

class GameType(str, Enum):
    go_no_go = "go_no_go"
    sequence_memory = "sequence_memory"
    matching_cards = "matching_cards"
