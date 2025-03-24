
import re

# Simple Soundex implementation for Arabic and English letters
# Adjust this as needed for accuracy or replace with Metaphone logic

def soundex(name):
    name = name.upper()
    name = re.sub(r'[^A-Zء-ي]', '', name)  # remove non-alphabetical characters (English and Arabic)
    name = name.replace("ء", "")  # Hamza (ء)

    # Soundex codes (adjust mapping for Arabic letters accordingly)
    codes = {
        'B': '1', 'F': '1', 'P': '1', 'V': '1',
        'C': '2', 'G': '2', 'J': '2', 'K': '2', 'Q': '2', 'S': '2', 'X': '2', 'Z': '2',
        'D': '3', 'T': '3',
        'L': '4',
        'M': '5', 'N': '5',
        'R': '6',

        # Arabic examples (can be expanded/improved)
        'ب': '1',  # ب
        'ف': '1',  # ف
        'ك': '2',  # ك
        'ق': '2',  # ق
        'س': '2',  # س
        'ش': '2',  # ش
        'ج': '2',  # ج
        'د': '3',  # د
        'ت': '3',  # ت
        'ل': '4',  # ل
        'م': '5',  # م
        'ن': '5',  # ن
        'ر': '6',  # ر
    }

    if not name:
        return "0000"

    first_letter = name[0]
    tail = name[1:]
    encoding = [codes.get(ch, '') for ch in tail]

    # Remove duplicates
    filtered = []
    prev = ''
    for ch in encoding:
        if ch != prev:
            filtered.append(ch)
        prev = ch

    result = first_letter + ''.join(filtered)
    result = result.replace("0", "")
    return (result + "000")[:4]

def arabic_to_phonetic(name):
    return soundex(name)

def english_to_phonetic(name):
    return soundex(name)
