
import sys
import os
import time

# Add project root to path
sys.path.append(os.getcwd())

from src.core.generators.smart_generator import SmartNumberGenerator
from src.core.data_manager import LotteryDataManager
from src.core.generators.anti_popular.sequence_analyzer import SequenceAnalyzer

def check_conditions(red_balls):
    # 1. Odd/Even Ratio 3:3
    odd_count = sum(1 for n in red_balls if n % 2 != 0)
    if odd_count != 3:
        return False, f"Odd/Even Ratio is {odd_count}:{6-odd_count}"

    # 2. Big/Small Ratio 3:3 (Small: 1-16, Big: 17-33)
    big_count = sum(1 for n in red_balls if n >= 17)
    if big_count != 3:
        return False, f"Big/Small Ratio is {big_count}:{6-big_count}"

    # 3. Zone Distribution 2-2-2
    # Zone 1: 1-11, Zone 2: 12-22, Zone 3: 23-33
    z1 = sum(1 for n in red_balls if 1 <= n <= 11)
    z2 = sum(1 for n in red_balls if 12 <= n <= 22)
    z3 = sum(1 for n in red_balls if 23 <= n <= 33)
    if not (z1 == 2 and z2 == 2 and z3 == 2):
        return False, f"Zone Dist is {z1}-{z2}-{z3}"

    # 4. Consecutive Numbers (At least one pair)
    # Using SequenceAnalyzer.max_consecutive_run
    # 1 means no consecutive (1, 3, 5). 2 means (1, 2).
    run = SequenceAnalyzer.max_consecutive_run(red_balls)
    if run < 2:
        return False, "No consecutive numbers"

    return True, "OK"

def main():
    print("Initializing Generator with Strict Anti-Popular Rules + Custom Filters...")
    print("Constraints:")
    print("  - Strict Anti-Popular Mode (Low Popularity Score)")
    print("  - Max History Overlap: <= 3")
    print("  - Odd/Even Ratio: 3:3")
    print("  - Big/Small Ratio: 3:3")
    print("  - Zone Distribution: 2-2-2 (1-11, 12-22, 23-33)")
    print("  - Consecutive Numbers: Contains at least one set")
    
    # 1. Load history data
    data_manager = LotteryDataManager()
    history = data_manager.get_history_data('ssq')
    
    if history is None or history.empty:
        print("Error: No historical data found.")
        return

    # Ensure red_numbers column exists and prepare list
    if 'red_numbers' not in history.columns:
        print("Error: 'red_numbers' column not found.")
        return
        
    history_reds = history['red_numbers'].tolist()
    # Simple parse check
    valid_history = []
    for h in history_reds:
        if isinstance(h, list):
            valid_history.append(h)
        elif isinstance(h, str):
            try:
                import ast
                valid_history.append(ast.literal_eval(h))
            except:
                pass
    history_reds = valid_history
    print(f"Loaded {len(history_reds)} valid historical records.")

    # 2. Initialize Generator
    generator = SmartNumberGenerator('ssq')
    # Use strict mode as base
    generator.set_anti_popular_config(enabled=True, mode='strict')
    
    max_history_overlap = 3
    found = False
    attempts = 0
    max_attempts = 10000 
    
    start_time = time.time()
    
    while not found and attempts < max_attempts:
        attempts += 1
        if attempts % 100 == 0:
            print(f"Scanning... {attempts} attempts...", end='\r')
        
        # We use standard random generation loop wrapped by our checks
        # because the 'strict' generator might be too slow if we just call it repeatedly 
        # and it filters internally.
        # However, to respect "Strict Anti-Popular Algorithm", we MUST use the generator's output.
        # The generator's `generate_anti_popular` tries to find low-score numbers.
        
        candidates = generator.generate_anti_popular(1)
        if not candidates:
            continue
            
        candidate = candidates[0]
        red = candidate.red
        blue = candidate.blue
        
        # 1. Custom Pattern Checks
        ok, reason = check_conditions(red)
        if not ok:
            # print(f"DEBUG: {red} failed: {reason}")
            continue
            
        # 2. History Overlap Check
        max_overlap_found = 0
        overlap_fail = False
        for past_red in history_reds:
            overlap = SequenceAnalyzer.overlap_count(red, past_red)
            if overlap > max_overlap_found:
                max_overlap_found = overlap
            
            if max_overlap_found > max_history_overlap:
                overlap_fail = True
                break
        
        if overlap_fail:
            continue
            
        # If we reached here, ALL conditions met
        found = True
        elapsed = time.time() - start_time
        print(f"\n\n✅ MATCH FOUND in {elapsed:.2f}s after {attempts} attempts!")
        print(f"🔴 Red Balls: {red}")
        print(f"🔵 Blue Ball: {blue}")
        print("-" * 30)
        print(f"Odd/Even: 3:3")
        print(f"Big/Small: 3:3")
        print(f"Zones: 2-2-2")
        print(f"Consecutive Run: {SequenceAnalyzer.max_consecutive_run(red)}")
        print(f"Max History Overlap: {max_overlap_found}")
        print("-" * 30)

    if not found:
        print(f"\n❌ Failed to find a number satisfying ALL criteria after {max_attempts} attempts.")
        print("The combination of 'Strict Anti-Popular' (which often avoids patterns) and specific patterns (like consecutive numbers) might be rare.")

if __name__ == "__main__":
    main()
