from enum import Enum

class Gender(str, Enum):
    male = "male"
    female = "female"
    other = "other"

class GameType(str, Enum):
    crop_recognition = "crop_recognition"
    sequence_memory = "sequence_memory"
    matching_cards = "matching_cards"
