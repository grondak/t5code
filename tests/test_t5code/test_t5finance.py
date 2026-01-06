"""Tests for T5Finance module - financial accounting system."""

import pytest
import uuid
from t5code.T5Finance import LedgerEntry, Account, Ledger, InvalidTransferError


def is_guid(string):
    """Check if a string is a valid UUID."""
    try:
        uuid_obj = uuid.UUID(string, version=4)
        return str(uuid_obj) == string.lower()
    except ValueError:
        return False


class TestLedgerEntry:
    """Test cases for LedgerEntry dataclass."""

    def test_ledger_entry_creation(self):
        """LedgerEntry can be created with all required fields."""
        entry = LedgerEntry(
            time=360,
            amount=50000,
            balance_after=1050000,
            memo="Cargo sale - Electronics"
        )

        assert entry.time == 360
        assert entry.amount == 50000
        assert entry.balance_after == 1050000
        assert entry.memo == "Cargo sale - Electronics"
        assert entry.counterparty is None

    def test_ledger_entry_with_counterparty(self):
        """LedgerEntry can include counterparty information."""
        entry = LedgerEntry(
            time=100,
            amount=-5000,
            balance_after=995000,
            memo="Fuel purchase",
            counterparty="Regina Starport"
        )

        assert entry.counterparty == "Regina Starport"
        assert entry.amount == -5000

    def test_ledger_entry_immutable(self):
        """LedgerEntry is immutable (frozen dataclass)."""
        entry = LedgerEntry(
            time=100,
            amount=1000,
            balance_after=1000,
            memo="Test"
        )

        with pytest.raises(AttributeError):
            entry.amount = 2000

    def test_ledger_entry_negative_amount(self):
        """LedgerEntry can represent debits with negative amounts."""
        debit = LedgerEntry(
            time=200,
            amount=-10000,
            balance_after=990000,
            memo="Expenses"
        )

        assert debit.amount < 0
        assert debit.balance_after == 990000


class TestAccount:
    """Test cases for Account class."""

    def test_account_creation_default_balance(self):
        """Account can be created with default zero balance."""
        account = Account("Test Account")

        assert account.name == "Test Account"
        assert account.balance == 0
        assert len(account.ledger) == 0
        assert is_guid(account.serial)

    def test_account_creation_with_starting_balance(self):
        """Account can be created with starting balance."""
        account = Account("Trader_001", starting_balance=1_000_000)

        assert account.name == "Trader_001"
        assert account.balance == 1_000_000
        assert len(account.ledger) == 0
        assert is_guid(account.serial)

    def test_account_unique_serials(self):
        """Each account gets a unique UUID serial."""
        account1 = Account("Account1")
        account2 = Account("Account2")

        assert account1.serial != account2.serial
        assert is_guid(account1.serial)
        assert is_guid(account2.serial)

    def test_account_equality_by_serial(self):
        """Accounts are equal if they have the same serial."""
        account1 = Account("Test")
        account2 = Account("Test")

        assert account1 != account2  # Different serials
        # Same object   - intentional self-equality test
        assert account1 == account1  # NOSONAR

    def test_account_hashable(self):
        """Accounts can be used in sets/dicts."""
        account1 = Account("Test1")
        account2 = Account("Test2")

        account_set = {account1, account2}
        assert len(account_set) == 2
        assert account1 in account_set

    def test_post_credit_transaction(self):
        """post() increases balance for positive amounts."""
        account = Account("Ship", starting_balance=100000)

        account.post(
            time=360,
            amount=50000,
            memo="Cargo sale"
        )

        assert account.balance == 150000
        assert len(account.ledger) == 1
        assert account.ledger[0].amount == 50000
        assert account.ledger[0].memo == "Cargo sale"

    def test_post_debit_transaction(self):
        """post() decreases balance for negative amounts."""
        account = Account("Ship", starting_balance=100000)

        account.post(
            time=360,
            amount=-25000,
            memo="Fuel purchase"
        )

        assert account.balance == 75000
        assert len(account.ledger) == 1
        assert account.ledger[0].amount == -25000

    def test_post_with_counterparty(self):
        """post() records counterparty information."""
        account = Account("Ship", starting_balance=100000)

        account.post(
            time=100,
            amount=-5000,
            memo="Docking fees",
            counterparty="Regina Starport"
        )

        assert account.ledger[0].counterparty == "Regina Starport"

    def test_multiple_posts(self):
        """Account can handle multiple transactions."""
        account = Account("Ship", starting_balance=1000000)

        account.post(time=100, amount=-50000, memo="Fuel")
        account.post(time=200, amount=100000, memo="Cargo sale")
        account.post(time=300, amount=-10000, memo="Supplies")

        assert account.balance == 1040000
        assert len(account.ledger) == 3
        assert account.ledger[0].balance_after == 950000
        assert account.ledger[1].balance_after == 1050000
        assert account.ledger[2].balance_after == 1040000

    def test_balance_after_tracking(self):
        """Each ledger entry records balance after that transaction."""
        account = Account("Ship", starting_balance=100)

        account.post(time=1, amount=50, memo="Credit 1")
        account.post(time=2, amount=100, memo="Credit 2")
        account.post(time=3, amount=-30, memo="Debit 1")

        assert account.ledger[0].balance_after == 150
        assert account.ledger[1].balance_after == 250
        assert account.ledger[2].balance_after == 220
        assert account.balance == 220

    def test_balance_can_go_negative(self):
        """Account balance can go negative (debt)."""
        account = Account("Ship", starting_balance=100)

        account.post(time=100, amount=-200, memo="Overdraft")

        assert account.balance == -100
        assert account.ledger[0].balance_after == -100

    def test_ledger_preserves_chronology(self):
        """Ledger entries maintain chronological order."""
        account = Account("Ship")

        account.post(time=100, amount=1000, memo="First")
        account.post(time=200, amount=2000, memo="Second")
        account.post(time=300, amount=3000, memo="Third")

        assert account.ledger[0].time == 100
        assert account.ledger[1].time == 200
        assert account.ledger[2].time == 300
        assert account.ledger[0].memo == "First"
        assert account.ledger[2].memo == "Third"


class TestLedger:
    """Test cases for Ledger class."""

    def test_ledger_creation(self):
        """Ledger can be instantiated."""
        ledger = Ledger()

        assert ledger.entries == []

    def test_transfer_basic(self):
        """transfer() moves credits from one account to another."""
        ship = Account("Ship", starting_balance=1_000_000)
        port = Account("Port", starting_balance=0)
        ledger = Ledger()

        ledger.transfer(
            time=360,
            from_acct=ship,
            to_acct=port,
            amount=5000,
            memo="Docking fees"
        )

        assert ship.balance == 995000
        assert port.balance == 5000

    def test_transfer_records_in_both_accounts(self):
        """transfer() creates ledger entries in both accounts."""
        ship = Account("Ship", starting_balance=100000)
        vendor = Account("Vendor")
        ledger = Ledger()

        ledger.transfer(
            time=100,
            from_acct=ship,
            to_acct=vendor,
            amount=25000,
            memo="Supplies"
        )

        assert len(ship.ledger) == 1
        assert len(vendor.ledger) == 1
        assert ship.ledger[0].amount == -25000
        assert vendor.ledger[0].amount == 25000

    def test_transfer_records_counterparties(self):
        """transfer() records counterparty names in both ledgers."""
        ship = Account("Trader_001", starting_balance=100000)
        port = Account("Regina Starport")
        ledger = Ledger()

        ledger.transfer(
            time=360,
            from_acct=ship,
            to_acct=port,
            amount=10000,
            memo="Fuel"
        )

        assert ship.ledger[0].counterparty == "Regina Starport"
        assert port.ledger[0].counterparty == "Trader_001"

    def test_transfer_same_memo_both_accounts(self):
        """transfer() uses same memo for both ledger entries."""
        from_acct = Account("A", starting_balance=100)
        to_acct = Account("B")
        ledger = Ledger()

        ledger.transfer(
            time=100,
            from_acct=from_acct,
            to_acct=to_acct,
            amount=50,
            memo="Test transaction"
        )

        assert from_acct.ledger[0].memo == "Test transaction"
        assert to_acct.ledger[0].memo == "Test transaction"

    def test_multiple_transfers(self):
        """Ledger can process multiple transfers."""
        ship = Account("Ship", starting_balance=1_000_000)
        fuel = Account("Fuel Vendor")
        cargo = Account("Cargo Broker")
        ledger = Ledger()

        ledger.transfer(time=100, from_acct=ship, to_acct=fuel,
                        amount=50000, memo="Fuel purchase")
        ledger.transfer(time=200, from_acct=ship, to_acct=cargo,
                        amount=200000, memo="Cargo purchase")
        ledger.transfer(time=300, from_acct=cargo, to_acct=ship,
                        amount=350000, memo="Cargo sale")

        assert ship.balance == 1_100_000
        assert fuel.balance == 50000
        # Net: paid 200k, received 350k from ship
        assert cargo.balance == -150000
        assert len(ship.ledger) == 3

    def test_transfer_preserves_time_sequence(self):
        """transfer() records transactions with provided timestamps."""
        ship = Account("Ship", starting_balance=100000)
        port = Account("Port")
        ledger = Ledger()

        ledger.transfer(time=360, from_acct=ship, to_acct=port,
                        amount=1000, memo="First")
        ledger.transfer(time=720, from_acct=ship, to_acct=port,
                        amount=2000, memo="Second")

        assert ship.ledger[0].time == 360
        assert ship.ledger[1].time == 720
        assert port.ledger[0].time == 360
        assert port.ledger[1].time == 720

    def test_transfer_zero_amount(self):
        """transfer() can handle zero amount (edge case)."""
        ship = Account("Ship", starting_balance=100)
        port = Account("Port")
        ledger = Ledger()

        ledger.transfer(
            time=100,
            from_acct=ship,
            to_acct=port,
            amount=0,
            memo="No-op transfer"
        )

        assert ship.balance == 100
        assert port.balance == 0
        assert len(ship.ledger) == 1
        assert len(port.ledger) == 1

    def test_transfer_negative_amount_raises_error(self):
        """transfer() raises InvalidTransferError for negative amounts."""
        ship = Account("Ship", starting_balance=100)
        port = Account("Port")
        ledger = Ledger()

        with pytest.raises(InvalidTransferError) as exc_info:
            ledger.transfer(
                time=100,
                from_acct=ship,
                to_acct=port,
                amount=-50,
                memo="Invalid"
            )

        assert "negative" in str(exc_info.value).lower()
        assert ship.balance == 100  # No change
        assert port.balance == 0  # No change

    def test_transfer_same_account_raises_error(self):
        """transfer() raises InvalidTransferError for same source/dest."""
        account = Account("Ship", starting_balance=100)
        ledger = Ledger()

        with pytest.raises(InvalidTransferError) as exc_info:
            ledger.transfer(
                time=100,
                from_acct=account,
                to_acct=account,
                amount=50,
                memo="Invalid self-transfer"
            )

        assert "same account" in str(exc_info.value).lower()
        assert account.balance == 100  # No change
        assert len(account.ledger) == 0  # No entries


class TestIntegration:
    """Integration tests for complete financial workflows."""

    def test_starship_trading_voyage(self):
        """Simulate a complete trading voyage with multiple transactions."""
        ship = Account("Free Trader Beowulf", starting_balance=1_000_000)
        regina_port = Account("Regina Starport")
        efate_port = Account("Efate Starport")
        broker = Account("Trade Broker")
        ledger = Ledger()

        # At Regina: Pay docking, fuel, and cargo purchase
        ledger.transfer(time=0, from_acct=ship, to_acct=regina_port,
                        amount=100, memo="Docking fee")
        ledger.transfer(time=1, from_acct=ship, to_acct=regina_port,
                        amount=5000, memo="Fuel - 10 tons")
        ledger.transfer(time=2, from_acct=ship, to_acct=broker,
                        amount=50000, memo="Cargo purchase - 5 tons")

        # Jump to Efate (7 days)

        # At Efate: Sell cargo, pay docking
        ledger.transfer(time=170, from_acct=ship, to_acct=efate_port,
                        amount=100, memo="Docking fee")
        ledger.transfer(time=171, from_acct=broker, to_acct=ship,
                        amount=75000, memo="Cargo sale - 5 tons")

        # Verify final balances
        # Started: 1,000,000
        # Paid Regina docking: -100
        # Paid Regina fuel: -5,000
        # Paid broker for cargo: -50,000
        # Paid Efate docking: -100
        # Received from cargo sale: +75,000
        # Final: 1,019,800
        assert ship.balance == 1_019_800
        assert len(ship.ledger) == 5
        assert ship.ledger[-1].balance_after == 1_019_800

        # Verify all transactions recorded
        assert regina_port.balance == 5100
        assert efate_port.balance == 100  # Received docking fee

    def test_audit_trail(self):
        """Verify complete audit trail with counterparties."""
        ship = Account("Trader_001", starting_balance=500000)
        vendor1 = Account("Fuel Vendor")
        vendor2 = Account("Cargo Broker")
        ledger = Ledger()

        ledger.transfer(time=100, from_acct=ship, to_acct=vendor1,
                        amount=10000, memo="Fuel")
        ledger.transfer(time=200, from_acct=ship, to_acct=vendor2,
                        amount=50000, memo="Cargo purchase")
        ledger.transfer(time=300, from_acct=vendor2, to_acct=ship,
                        amount=80000, memo="Cargo sale")

        # Check ship's audit trail
        assert ship.ledger[0].counterparty == "Fuel Vendor"
        assert ship.ledger[1].counterparty == "Cargo Broker"
        assert ship.ledger[2].counterparty == "Cargo Broker"

        # Check vendors' audit trails
        assert vendor1.ledger[0].counterparty == "Trader_001"
        assert vendor2.ledger[0].counterparty == "Trader_001"
        assert vendor2.ledger[1].counterparty == "Trader_001"

        # Verify all transactions have timestamps
        assert all(entry.time > 0 for entry in ship.ledger)
