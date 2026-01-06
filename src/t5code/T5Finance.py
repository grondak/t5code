"""Financial accounting system for Traveller 5 starship operations.

This module provides a double-entry accounting system for tracking starship
finances, including income from freight/passengers/cargo and expenses for
fuel/maintenance/crew. Each transaction is recorded with timestamp, amount,
memo, and counterparty information.

Classes:
    LedgerEntry: Immutable record of a financial transaction.
    Account: Individual account with balance and transaction history.
    Ledger: System for managing transfers between accounts.

Example:
    >>> ship_account = Account("Trader_001", starting_balance=1_000_000)
    >>> port_account = Account("Regina Starport")
    >>> ledger = Ledger()
    >>>
    >>> # Ship pays for fuel
    >>> ledger.transfer(
    ...     time=100,
    ...     from_acct=ship_account,
    ...     to_acct=port_account,
    ...     amount=5000,
    ...     memo="Refined fuel - 10 tons"
    ... )
    >>> print(ship_account.balance)
    995000
"""
import uuid
from dataclasses import dataclass
from typing import Optional

from t5code.T5Exceptions import T5Error


class InvalidTransferError(T5Error):
    """Raised when a financial transfer is invalid.

    Attributes:
        reason: Description of why the transfer is invalid
    """

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"Invalid transfer: {reason}")


@dataclass(frozen=True, slots=True)
class LedgerEntry:
    """Immutable record of a single financial transaction.

    Each entry captures the complete context of a transaction including
    timing, amount (positive for credits, negative for debits), resulting
    balance, and a descriptive memo. Optionally tracks the counterparty
    (other account) involved.

    Attributes:
        time: Simulation hour when transaction occurred (integer timestamp).
        amount: Transaction amount in credits (positive=credit,
            negative=debit).
        balance_after: Account balance immediately after this transaction.
        memo: Human-readable description of the transaction.
        counterparty: Name of the other account involved (None for
            single-account posts).

    Example:
        >>> entry = LedgerEntry(
        ...     time=360,
        ...     amount=50000,
        ...     balance_after=1050000,
        ...     memo="Cargo sale - Electronics",
        ...     counterparty="Regina Market"
        ... )
        >>> entry.amount
        50000
    """
    time: int                 # sim hour
    amount: int               # positive or negative
    balance_after: int
    memo: str
    counterparty: Optional[str] = None


class Account:
    """Individual account with balance tracking and transaction history.

    Maintains a running balance and complete ledger of all transactions.
    Each post() operation creates an immutable LedgerEntry record.

    Attributes:
        name: Account identifier (e.g., "Trader_001" or "Regina Starport").
        serial: Unique UUID identifier for this account.
        balance: Current account balance in credits (read-only property).
        ledger: Chronological list of all transactions (LedgerEntry objects).

    Example:
        >>> account = Account("Free Trader Beowulf",
                              starting_balance=1_000_000)
        >>> account.post(time=100, amount=-50000, memo="Fuel purchase")
        >>> account.balance
        950000
        >>> len(account.ledger)
        1
    """

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Account) and self.serial == other.serial

    def __hash__(self) -> int:
        return hash(self.serial)

    def __init__(self, name: str, starting_balance: int = 0):
        """Initialize a new account with optional starting balance.

        Args:
            name: Unique identifier for this account.
            starting_balance: Initial balance in credits (default: 0).

        Example:
            >>> ship = Account("Trader_001", starting_balance=1_000_000)
            >>> port = Account("Starport Services")
        """
        self.name = name
        self.serial: str = str(uuid.uuid4())
        self._balance = starting_balance
        self.ledger: list[LedgerEntry] = []

    @property
    def balance(self) -> int:
        """Current account balance in credits (read-only).

        Returns:
            Current balance as integer. Negative values indicate debt.

        Example:
            >>> account = Account("Trader", starting_balance=100000)
            >>> account.balance
            100000
        """
        return self._balance

    def post(
        self,
        *,
        time: int,
        amount: int,
        memo: str,
        counterparty: Optional[str] = None,
    ) -> None:
        """Record a transaction and update balance.

        Posts a transaction to this account, adjusting the balance and creating
        an immutable LedgerEntry. Positive amounts increase balance (credits),
        negative amounts decrease balance (debits).

        Args:
            time: Simulation hour when transaction occurs.
            amount: Credits to add (positive) or subtract (negative).
            memo: Description of the transaction.
            counterparty: Name of other account involved (optional).

        Example:
            >>> account = Account("Ship", starting_balance=1000000)
            >>> account.post(time=360,
                             amount=-5000,
                             memo="Fuel",
                             counterparty="Port")
            >>> account.balance
            995000
            >>> account.ledger[0].memo
            'Fuel'
        """
        self._balance += amount
        self.ledger.append(
            LedgerEntry(
                time=time,
                amount=amount,
                balance_after=self._balance,
                memo=memo,
                counterparty=counterparty,
            )
        )


class Ledger:
    """System for managing double-entry transfers between accounts.

    Coordinates transfers between accounts, ensuring that every debit from one
    account has a corresponding credit to another account. Maintains an audit
    trail of all transfers.

    Attributes:
        entries: List of all ledger entries
                 (currently unused, reserved for future).

    Example:
        >>> ship = Account("Trader_001", starting_balance=1_000_000)
        >>> port = Account("Regina Starport")
        >>> ledger = Ledger()
        >>> ledger.transfer(
        ...     time=100,
        ...     from_acct=ship,
        ...     to_acct=port,
        ...     amount=5000,
        ...     memo="Docking fees"
        ... )
        >>> ship.balance
        995000
        >>> port.balance
        5000
    """

    def __init__(self):
        """Initialize a new ledger system.

        Example:
            >>> ledger = Ledger()
        """
        self.entries: list[LedgerEntry] = []

    def transfer(
        self,
        *,
        time: int,
        from_acct: Account,
        to_acct: Account,
        amount: int,
        memo: str,
    ) -> None:
        """Transfer credits from one account to another.

        Performs a double-entry transfer, posting a debit to the source
        account and a credit to the destination account. Both accounts
        record the counterparty name for audit trail purposes.

        Args:
            time: Simulation hour when transfer occurs.
            from_acct: Source account (will be debited).
            to_acct: Destination account (will be credited).
            amount: Credits to transfer (must be positive).
            memo: Description of the transfer.

        Raises:
            InvalidTransferError: If amount is negative or accounts are
                identical.

        Example:
            >>> ship = Account("Trader_001", starting_balance=1_000_000)
            >>> vendor = Account("Ship Supplies")
            >>> ledger = Ledger()
            >>> ledger.transfer(
            ...     time=360,
            ...     from_acct=ship,
            ...     to_acct=vendor,
            ...     amount=25000,
            ...     memo="Life support supplies"
            ... )
            >>> ship.balance
            975000
            >>> vendor.balance
            25000
            >>> ship.ledger[0].counterparty
            'Ship Supplies'
        """
        # Validate transfer
        if amount < 0:
            raise InvalidTransferError(
                "transfer amount cannot be negative"
            )
        if from_acct == to_acct:
            raise InvalidTransferError(
                "cannot transfer to the same account"
            )

        from_acct.post(
            time=time,
            amount=-amount,
            memo=memo,
            counterparty=to_acct.name,
        )
        to_acct.post(
            time=time,
            amount=amount,
            memo=memo,
            counterparty=from_acct.name,
        )
