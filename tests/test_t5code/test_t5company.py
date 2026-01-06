"""Tests for T5Company module - trading company with financial accounting."""

import pytest
import uuid
from t5code.T5Company import T5Company, CompanyError
from t5code.T5Finance import Account


def is_guid(string):
    """Check if a string is a valid UUID."""
    try:
        uuid_obj = uuid.UUID(string, version=4)
        return str(uuid_obj) == string.lower()
    except ValueError:
        return False


class TestT5Company:
    """Test cases for T5Company class."""

    def test_company_creation_with_capital(self):
        """Company can be created with starting capital."""
        company = T5Company("Free Traders Inc", starting_capital=1_000_000)

        assert company.name == "Free Traders Inc"
        assert company.balance == 1_000_000
        assert company.cash.balance == 1_000_000
        assert is_guid(company.serial)

    def test_company_creation_zero_capital(self):
        """Company can be created with zero starting capital."""
        company = T5Company("Startup Co", starting_capital=0)

        assert company.name == "Startup Co"
        assert company.balance == 0
        assert len(company.cash.ledger) == 0

    def test_company_unique_serials(self):
        """Each company gets a unique UUID serial."""
        company1 = T5Company("Company A", starting_capital=100000)
        company2 = T5Company("Company B", starting_capital=100000)

        assert company1.serial != company2.serial
        assert is_guid(company1.serial)
        assert is_guid(company2.serial)

    def test_company_equality_by_serial(self):
        """Companies are equal if they have the same serial."""
        company1 = T5Company("Test", starting_capital=100)
        company2 = T5Company("Test", starting_capital=100)

        assert company1 != company2  # Different serials
        # Same object   - intentional self-equality test
        assert company1 == company1  # NOSONAR

    def test_company_hashable(self):
        """Companies can be used in sets/dicts."""
        company1 = T5Company("Company1", starting_capital=100)
        company2 = T5Company("Company2", starting_capital=200)

        company_set = {company1, company2}
        assert len(company_set) == 2
        assert company1 in company_set

    def test_company_negative_capital_raises_error(self):
        """Creating company with negative capital raises CompanyError."""
        with pytest.raises(CompanyError) as exc_info:
            T5Company("Bad Company", starting_capital=-1000)

        assert "negative" in str(exc_info.value).lower()

    def test_company_ledger_initialized(self):
        """Company is created with initialized ledger."""
        company = T5Company("Test Co", starting_capital=50000)

        assert company.ledger is not None
        assert hasattr(company.ledger, 'transfer')

    def test_company_cash_account_initialized(self):
        """Company is created with initialized cash account."""
        company = T5Company("Traders", starting_capital=100000)

        assert company.cash is not None
        assert "Traders - Cash" in company.cash.name
        assert company.cash.balance == 100000

    def test_initial_capitalization_recorded(self):
        """Initial capital transfer is recorded in cash ledger."""
        company = T5Company("Test", starting_capital=500000)

        assert len(company.cash.ledger) == 1
        entry = company.cash.ledger[0]
        assert entry.time == 0
        assert entry.amount == 500000
        assert entry.memo == "Initial capitalization"
        assert "Owner Capital" in entry.counterparty

    def test_balance_property(self):
        """balance property returns current cash balance."""
        company = T5Company("Test Co", starting_capital=250000)

        assert company.balance == 250000
        assert company.balance == company.cash.balance

    def test_repr_format(self):
        """__repr__ returns formatted string with name and balance."""
        company = T5Company("Merchant Guild", starting_capital=1_500_000)

        repr_str = repr(company)
        assert "T5Company" in repr_str
        assert "Merchant Guild" in repr_str
        assert "1,500,000" in repr_str

    def test_company_can_make_purchases(self):
        """Company can transfer funds to make purchases."""
        company = T5Company("Traders", starting_capital=1_000_000)
        vendor = Account("Starship Supplies")

        company.ledger.transfer(
            time=100,
            from_acct=company.cash,
            to_acct=vendor,
            amount=50000,
            memo="Ship supplies"
        )

        assert company.balance == 950000
        assert vendor.balance == 50000
        assert len(company.cash.ledger) == 2  # Initial cap + purchase

    def test_company_can_receive_revenue(self):
        """Company can receive funds as revenue."""
        company = T5Company("Freight Co", starting_capital=500000)
        customer = Account("Customer Account")
        customer.post(time=0, amount=100000, memo="Initial funds")

        company.ledger.transfer(
            time=200,
            from_acct=customer,
            to_acct=company.cash,
            amount=75000,
            memo="Freight payment"
        )

        assert company.balance == 575000
        assert len(company.cash.ledger) == 2  # Initial cap + revenue

    def test_company_multiple_transactions(self):
        """Company can handle multiple transactions."""
        company = T5Company("Trading House", starting_capital=2_000_000)
        vendor1 = Account("Fuel Depot")
        vendor2 = Account("Cargo Broker")
        customer = Account("Customer")

        # Make purchases
        company.ledger.transfer(
            time=100, from_acct=company.cash, to_acct=vendor1,
            amount=50000, memo="Fuel"
        )
        company.ledger.transfer(
            time=200, from_acct=company.cash, to_acct=vendor2,
            amount=200000, memo="Cargo purchase"
        )

        # Receive payment
        customer.post(time=0, amount=500000, memo="Initial")
        company.ledger.transfer(
            time=300, from_acct=customer, to_acct=company.cash,
            amount=350000, memo="Cargo sale"
        )

        # Verify final balance: 2,000,000 - 50,000 - 200,000 + 350,000
        assert company.balance == 2_100_000
        assert len(company.cash.ledger) == 4  # Initial + 3 transactions


class TestCompanyIntegration:
    """Integration tests for company financial operations."""

    def test_company_trading_voyage(self):
        """Simulate complete trading voyage with company accounts."""
        company = T5Company("Star Traders", starting_capital=5_000_000)
        regina_port = Account("Regina Starport")
        efate_port = Account("Efate Starport")
        broker = Account("Trade Broker")

        # At Regina: expenses
        company.ledger.transfer(
            time=0, from_acct=company.cash, to_acct=regina_port,
            amount=100, memo="Docking fee"
        )
        company.ledger.transfer(
            time=1, from_acct=company.cash, to_acct=regina_port,
            amount=5000, memo="Fuel"
        )
        company.ledger.transfer(
            time=2, from_acct=company.cash, to_acct=broker,
            amount=50000, memo="Cargo purchase"
        )

        # Jump to Efate

        # At Efate: revenue
        company.ledger.transfer(
            time=170, from_acct=company.cash, to_acct=efate_port,
            amount=100, memo="Docking fee"
        )
        broker.post(time=0, amount=100000, memo="Initial")
        company.ledger.transfer(
            time=171, from_acct=broker, to_acct=company.cash,
            amount=75000, memo="Cargo sale"
        )

        # Verify profit
        # Started: 5,000,000
        # Expenses: -100 - 5,000 - 50,000 - 100 = -55,200
        # Revenue: +75,000
        # Net: 5,000,000 - 55,200 + 75,000 = 5,019,800
        assert company.balance == 5_019_800
        assert len(company.cash.ledger) == 6  # Initial + 5 transactions

    def test_company_cash_flow_tracking(self):
        """Verify complete cash flow tracking through ledger."""
        company = T5Company("Flow Traders", starting_capital=1_000_000)

        # Track all transactions
        vendor = Account("Vendor")
        customer = Account("Customer")
        customer.post(time=0, amount=200000, memo="Initial")

        company.ledger.transfer(
            time=100, from_acct=company.cash, to_acct=vendor,
            amount=50000, memo="Purchase 1"
        )
        company.ledger.transfer(
            time=200, from_acct=customer, to_acct=company.cash,
            amount=80000, memo="Sale 1"
        )
        company.ledger.transfer(
            time=300, from_acct=company.cash, to_acct=vendor,
            amount=30000, memo="Purchase 2"
        )
        company.ledger.transfer(
            time=400, from_acct=customer, to_acct=company.cash,
            amount=60000, memo="Sale 2"
        )

        # Verify ledger completeness
        assert len(company.cash.ledger) == 5  # Initial + 4 transactions

        # Verify all transactions have timestamps
        assert all(entry.time >= 0 for entry in company.cash.ledger)

        # Verify all transactions have counterparties
        assert all(
            entry.counterparty is not None
            for entry in company.cash.ledger
        )

        # Verify final balance
        # 1,000,000 - 50,000 + 80,000 - 30,000 + 60,000 = 1,060,000
        assert company.balance == 1_060_000

    def test_company_with_zero_starting_capital(self):
        """Company with zero capital can receive initial funding."""
        company = T5Company("Bootstrap Inc", starting_capital=0)
        investor = Account("Angel Investor")
        investor.post(time=0, amount=500000, memo="Initial funds")

        # Receive investment
        company.ledger.transfer(
            time=100,
            from_acct=investor,
            to_acct=company.cash,
            amount=250000,
            memo="Series A funding"
        )

        assert company.balance == 250000
        assert len(company.cash.ledger) == 1  # No initial cap, just investment
