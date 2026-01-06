"""Company representation for Traveller 5 trading operations.

This module provides a company class that owns accounts and manages
financial operations through a double-entry ledger system. Companies
can own starships, manage capital, and track all financial transactions.

Classes:
    T5Company: Trading company with cash account and transaction ledger.

Example:
    >>> from t5code import T5Company
    >>> company = T5Company("Free Traders Inc", starting_capital=5_000_000)
    >>> company.cash.balance
    5000000
    >>> # Buy supplies
    >>> from t5code import Account
    >>> vendor = Account("Starport Supplies")
    >>> company.ledger.transfer(
    ...     time=100,
    ...     from_acct=company.cash,
    ...     to_acct=vendor,
    ...     amount=50000,
    ...     memo="Ship supplies"
    ... )
    >>> company.cash.balance
    4950000
"""
import uuid

from t5code.T5Finance import Ledger, Account
from t5code.T5Exceptions import T5Error


class CompanyError(T5Error):
    """Raised when a company operation is invalid.

    Attributes:
        reason: Description of why the operation is invalid
    """

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"Company error: {reason}")


class T5Company:
    """Trading company with financial accounting and asset management.

    A company maintains a cash account and uses a double-entry ledger
    to track all financial transactions. Companies are identified by
    name and unique serial number.

    Attributes:
        name: Company name (e.g., "Free Traders Inc").
        serial: Unique UUID identifier for this company.
        ledger: Double-entry ledger for all transactions.
        cash: Primary cash account for the company.

    Example:
        >>> company = T5Company("Merchant Guild", starting_capital=1_000_000)
        >>> company.name
        'Merchant Guild'
        >>> company.cash.balance
        1000000
    """

    def __eq__(self, other: object) -> bool:
        return isinstance(other, T5Company) and self.serial == other.serial

    def __hash__(self) -> int:
        return hash(self.serial)

    def __init__(self, name: str, starting_capital: int):
        """Initialize a new trading company with starting capital.

        Creates a company with a cash account funded by initial owner
        capital. The capitalization transaction is recorded in the ledger
        at time=0.

        Args:
            name: Name of the company.
            starting_capital: Initial capital in credits (must be >= 0).

        Raises:
            CompanyError: If starting_capital is negative.

        Example:
            >>> company = T5Company("Star Traders", starting_capital=2_000_000)
            >>> company.cash.balance
            2000000
            >>> len(company.cash.ledger)
            1
        """
        if starting_capital < 0:
            raise CompanyError("starting capital cannot be negative")

        self.name = name
        self.serial: str = str(uuid.uuid4())
        self.ledger = Ledger()
        self.cash = Account(f"{name} - Cash")

        # Record initial capitalization
        if starting_capital > 0:
            owner_capital = Account(f"{name} - Owner Capital")
            self.ledger.transfer(
                time=0,
                from_acct=owner_capital,
                to_acct=self.cash,
                amount=starting_capital,
                memo="Initial capitalization",
            )

    @property
    def balance(self) -> int:
        """Current cash balance in credits (read-only).

        Returns:
            Current cash account balance as integer.

        Example:
            >>> company = T5Company("Traders", starting_capital=100000)
            >>> company.balance
            100000
        """
        return self.cash.balance

    def __repr__(self) -> str:
        """Return string representation of company.

        Returns:
            String showing company name and current balance.

        Example:
            >>> company = T5Company("Test Co", starting_capital=50000)
            >>> repr(company)
            "T5Company('Test Co', balance=Cr50,000)"
        """
        return f"T5Company('{self.name}', balance=Cr{self.balance:,})"
