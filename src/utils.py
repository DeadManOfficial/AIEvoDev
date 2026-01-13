# src/utils.py

def calculate_average(numbers: list[int]) -> float:
    """
    Calculates the average of a list of numbers.

    Args:
        numbers: A list of integers.

    Returns:
        The average of the numbers as a float.

    Raises:
        ValueError: If the input list is empty.
    """
    if not numbers:
        raise ValueError("Input list cannot be empty.")
    return sum(numbers) / len(numbers)
