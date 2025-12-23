
import sys
import os
import random
from collections import Counter
import pandas as pd

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from src.core.generators.smart_generator import SmartNumberGenerator
from src.core.data_manager import LotteryDataManager

def get_all_ssq_history(data_manager):
    """Get all historical SSQ draw numbers."""
    history = data_manager.get_history_data('ssq')
    if history is None or history.empty:
        print("Warning: No history data found.")
        return []
    
    # Extract red numbers as a list of lists/sets
    # history['red_numbers'] typically contains lists of ints or strings
    return history['red_numbers'].tolist()

def check_overlap_all_history(red, history_list):
    """
    Check if the candidate 'red' has > 3 overlap with ANY historical draw.
    Returns True if valid (max overlap <= 3), False otherwise.
    """
    if not history_list:
        return True
    
    candidate_set = set(red)
    
    for hist_red in history_list:
        # hist_red might be a list or string, handle both
        if isinstance(hist_red, str):
            h_set = set(int(x) for x in hist_red.split(','))
        else:
            h_set = set(hist_red)
            
        overlap = len(candidate_set & h_set)
        if overlap > 3:
            return False # Failed: found a historical draw with > 3 matches
            
    return True # Passed: no historical draw has > 3 matches

def check_odd_even(red):
    # Odd: 1, 3, ... Even: 2, 4, ...
    odds = sum(1 for x in red if x % 2 != 0)
    evens = 6 - odds
    ratio = (odds, evens)
    return ratio in [(3, 3), (4, 2), (2, 4)]

def check_big_small(red):
    # SSQ Red: 1-33.
    # Usually: Small 1-16, Big 17-33.
    small = sum(1 for x in red if 1 <= x <= 16)
    big = sum(1 for x in red if 17 <= x <= 33)
    ratio = (big, small) # Requirement says "Big/Small ratio"
    # User said: "Big/Small ratio can be 3:3, 2:4, 4:2"
    # Order usually implies Big:Small.
    return ratio in [(3, 3), (2, 4), (4, 2)]

def check_zones(red):
    # Zone 1: 1-11, Zone 2: 12-22, Zone 3: 23-33
    z1 = sum(1 for x in red if 1 <= x <= 11)
    z2 = sum(1 for x in red if 12 <= x <= 22)
    z3 = sum(1 for x in red if 23 <= x <= 33)
    return (z1 == 2 and z2 == 2 and z3 == 2)

def main():
    print("Initializing Generator...")
    generator = SmartNumberGenerator('ssq')
    
    # Set strict anti-popular mode
    generator.set_anti_popular_config(enabled=True, mode='strict')
    
    # Get all history for overlap check
    data_manager = LotteryDataManager()
    history_list = get_all_ssq_history(data_manager)
    print(f"Loaded {len(history_list)} historical draws.")
    
    target_count = 1
    generated_count = 0
    attempts = 0
    max_attempts = 50000 # Increased attempts as constraint is harder
    
    print("\nStarting generation with constraints:")
    print("1. Strict Anti-Popular Algorithm")
    print("2. Overlap with ANY historical draw <= 3 (Strict History Check)")
    print("3. Odd/Even Ratio: 3:3, 4:2, or 2:4")
    print("4. Big/Small Ratio: 3:3, 2:4, or 4:2")
    print("5. Zone Distribution: 2-2-2")
    print("-" * 50)

    found_numbers = []

    while generated_count < target_count and attempts < max_attempts:
        attempts += 1
        
        # Suppress stdout briefly to avoid spamming 50k lines
        sys.stdout = open(os.devnull, 'w')
        try:
            candidates = generator.generate_anti_popular(1)
        except Exception:
            sys.stdout = sys.__stdout__
            continue
        sys.stdout = sys.__stdout__
        
        if not candidates:
            continue
            
        candidate = candidates[0]
        red = candidate.red
        blue = candidate.blue
        
        # Check constraints
        if not check_odd_even(red):
            continue
            
        if not check_big_small(red):
            continue
            
        if not check_zones(red):
            continue
            
        # Check history overlap LAST (most expensive check)
        if not check_overlap_all_history(red, history_list):
            continue
            
        # Found one!
        found_numbers.append(candidate)
        generated_count += 1
        print(f"\n✅ SUCCESS! Found a matching number after {attempts} attempts.")
        print(f"Red: {red}, Blue: {blue}")
        print(f"Details:")
        print(f"  Odd/Even: {sum(1 for x in red if x%2!=0)}:{sum(1 for x in red if x%2==0)}")
        print(f"  Big/Small: {sum(1 for x in red if x>=17)}:{sum(1 for x in red if x<=16)}")
        print(f"  Zones: {sum(1 for x in red if 1<=x<=11)}-{sum(1 for x in red if 12<=x<=22)}-{sum(1 for x in red if 23<=x<=33)}")
        print(f"  Verified against {len(history_list)} historical draws.")
        break

    if generated_count == 0:
        print(f"\n❌ Failed to generate a number satisfying all constraints after {max_attempts} attempts.")
if __name__ == "__main__":
    main()
