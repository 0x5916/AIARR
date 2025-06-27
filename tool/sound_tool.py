import os
import pygame
import time

def get_sound_length(sound_path):
    """Gets the length of a sound file in seconds"""
    if not os.path.exists(sound_path):
        return 0
        
    try:
        sound = pygame.mixer.Sound(sound_path)
        length = sound.get_length()
        return length
    except Exception as e:
        print(f"Error getting sound length: {e}")
        return 0

def play_sound(sound_path):
    """Play a sound file"""
    if not os.path.exists(sound_path):
        print(f"Sound file not found: {sound_path}")
        return
        
    try:
        sound = pygame.mixer.Sound(sound_path)
        pygame.mixer.Sound.play(sound)
    except Exception as e:
        print(f"Error playing sound: {e}")