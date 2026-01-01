"""Custom exceptions for the t5code package.

This module defines a hierarchy of exceptions specific to Traveller 5
game mechanics and starship operations.
"""


class T5Error(Exception):
    """Base exception for all t5code errors."""
    pass


class InsufficientFundsError(T5Error):
    """Raised when ship lacks funds for a transaction.

    Attributes:
        required: Amount of credits needed
        available: Amount of credits currently available
    """

    def __init__(self, required: float, available: float):
        self.required = required
        self.available = available
        super().__init__(
            f"Insufficient funds: need {required:,.0f} credits, "
            f"have {available:,.0f} credits"
        )


class CapacityExceededError(T5Error):
    """Raised when cargo/passenger capacity is exceeded.

    Attributes:
        required: Space/capacity needed
        available: Space/capacity currently available
        capacity_type: Type of capacity (e.g., 'cargo', 'staterooms')
    """

    def __init__(self, required: float, available: float, capacity_type: str):
        self.required = required
        self.available = available
        self.capacity_type = capacity_type
        super().__init__(
            f"{capacity_type.capitalize()} capacity exceeded: "
            f"need {required}, have {available} available"
        )


class InvalidPassageClassError(T5Error):
    """Raised when an invalid passenger class is specified.

    Attributes:
        passage_class: The invalid passage class provided
        valid_classes: Tuple of valid passage classes
    """

    def __init__(self,
                 passage_class: str,
                 valid_classes: tuple = ("high", "mid", "low")):
        self.passage_class = passage_class
        self.valid_classes = valid_classes
        super().__init__(
            f"Invalid passage class '{passage_class}'. "
            f"Must be one of: {', '.join(valid_classes)}"
        )


class DuplicateItemError(T5Error):
    """Raised when attempting to add a duplicate item (lot, passenger, etc).

    Attributes:
        item_id: Identifier of the duplicate item
        item_type: Type of item (e.g., 'lot', 'passenger')
    """

    def __init__(self, item_id: str, item_type: str = "item"):
        self.item_id = item_id
        self.item_type = item_type
        super().__init__(
            f"Duplicate {item_type}: '{item_id}' is already present"
        )


class WorldNotFoundError(T5Error):
    """Raised when a world is not found in the game data.

    Attributes:
        world_name: Name of the world that was not found
    """

    def __init__(self, world_name: str):
        self.world_name = world_name
        super().__init__(f"World '{world_name}' not found in game data")


class InvalidLotTypeError(T5Error):
    """Raised when an invalid lot type is specified.

    Attributes:
        lot_type: The invalid lot type provided
        valid_types: Tuple of valid lot types
    """

    def __init__(self,
                 lot_type: str,
                 valid_types: tuple = ("cargo", "freight")):
        self.lot_type = lot_type
        self.valid_types = valid_types
        super().__init__(
            f"Invalid lot type '{lot_type}'. "
            f"Must be one of: {', '.join(valid_types)}"
        )


class InvalidThresholdError(T5Error):
    """Raised when a threshold value is out of valid range.

    Attributes:
        threshold: The invalid threshold value
        min_value: Minimum valid threshold
        max_value: Maximum valid threshold
    """

    def __init__(self,
                 threshold: float,
                 min_value: float = 0.0,
                 max_value: float = 1.0):
        self.threshold = threshold
        self.min_value = min_value
        self.max_value = max_value
        super().__init__(
            f"Threshold {threshold} out of range. "
            f"Must be between {min_value} and {max_value}"
        )
