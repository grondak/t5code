"""Demonstrate sequential flux rolls with deferred second die."""

from t5code.T5Basics import SequentialFlux


def demonstrate_sequential_flux():
    """Show how sequential flux works."""

    print("="*70)
    print("SEQUENTIAL FLUX DEMONSTRATION")
    print("="*70)
    print()

    # Example 1: Roll first, decide, then roll second
    print("Example 1: Conditional second roll")
    print("-" * 70)
    flux = SequentialFlux()
    print(f"First die rolled: {flux.first_die}")
    print(f"Possible range: {flux.potential_range}")

    # Make a decision based on first die
    if flux.first_die >= 4:
        print("First die is high (4+), rolling second die...")
        result = flux.roll_second()
        print(f"Second die: {flux.second_die}")
        print(f"Final flux result: {result:+d}")
    else:
        print("First die is low (1-3), skipping second roll")
        print(f"Status: {flux}")
    print()

    # Example 2: Show all six sub-tables
    print("Example 2: All possible sub-tables")
    print("-" * 70)
    for first in range(1, 7):
        flux = SequentialFlux(first_die=first)
        print(f"First die = {first}: Range {flux.potential_range}", end=" → ")
        # Show all possible outcomes for this first die
        outcomes = [first - second for second in range(1, 7)]
        print(f"Outcomes: {outcomes}")
    print()

    # Example 3: Multiple sequential rolls
    print("Example 3: Five sequential flux rolls")
    print("-" * 70)
    for i in range(1, 6):
        flux = SequentialFlux()
        result = flux.roll_second()
        print(f"Roll {i}: {flux.first_die} - "
              f"{flux.second_die} = {result:+3d}  "
              f"(range was {flux.potential_range})")
    print()

    # Example 4: Trading decision scenario
    print("Example 4: Trading decision scenario")
    print("-" * 70)
    print("You're deciding whether to buy goods...")
    flux = SequentialFlux()
    print(f"Market indicator (first die): {flux.first_die}")

    if flux.first_die <= 2:
        print("→ Market looks bad, not buying")
    elif flux.first_die >= 5:
        print("→ Market looks good, checking price...")
        result = flux.roll_second()
        if result >= 2:
            print(f"  → Flux result: {result:+d} - Great price! BUY")
        elif result >= 0:
            print(f"  → Flux result: {result:+d} - Fair price, BUY")
        else:
            print(f"  → Flux result: {result:+d} - Too expensive, PASS")
    else:
        print("→ Market uncertain, checking price anyway...")
        result = flux.roll_second()
        print(f"  → Flux result: {result:+d}")
        if result >= 1:
            print("  → Decent enough, BUY")
        else:
            print("  → Not worth it, PASS")
    print()

    print("="*70)


if __name__ == "__main__":
    demonstrate_sequential_flux()
