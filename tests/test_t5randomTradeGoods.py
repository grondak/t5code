import pytest
import random
from t5code.T5RandomTradeGoods import (
    TradeGood,
    TradeGoodsTypeTable,
    TradeClassificationGoodsTable,
    RandomTradeGoodsTable,
    T5RTGTable,
    clone_classification_table,
    ImbalanceTradeGood,
)


def test_clone_classification_table():
    # Setup a source table
    source = TradeClassificationGoodsTable("Src")
    source.add_type_table("Alpha", ["A1", "A2", "A3", "A4", "A5", "A6"])
    source.add_type_table("Beta", ["B1", "B2", "B3", "B4", "B5", "B6"])
    # Setup a target RandomTradeGoodsTable
    target = RandomTradeGoodsTable()
    # Clone
    new_table = clone_classification_table("Clone", source, target)
    # Check the new table is in the target
    assert "Clone" in target.classifications
    # Check the contents match
    for type_name in source.type_tables:
        for i in range(6):
            assert (
                new_table.type_tables[type_name].get_good(i).get_name()
                == source.type_tables[type_name].get_good(i).get_name()
            )


def test_fa_table_access():
    # This will execute the Fa table initialization code
    assert isinstance(T5RTGTable.classifications["Ga"], object)


def test_cs_table_access():
    assert isinstance(T5RTGTable.classifications["Fa"], object)


def test_fa_table_access():
    # This will execute the Fa table initialization code
    assert isinstance(T5RTGTable.classifications["Fa"], object)


def test_cs_table_access():
    assert isinstance(T5RTGTable.classifications["Cs"], object)


def test_cx_table_access():
    assert isinstance(T5RTGTable.classifications["Cx"], object)


def test_trade_good_static_name():
    g = TradeGood("Bulk Woods")
    assert g.get_name() == "Bulk Woods"


def test_trade_good_callable_name():
    g = TradeGood(lambda: "Mystery Dust")
    assert g.get_name() == "Mystery Dust"


def test_trade_goods_type_table_access():
    goods = ["A", "B", "C", "D", "E", "F"]
    table = TradeGoodsTypeTable("Test", goods)
    assert table.get_good(2).get_name() == "C"


def test_too_many_goods_in_a_table():
    goods = ["A", "B", "C", "D", "E", "F", "G"]
    with pytest.raises(ValueError, match="Test table must have exactly 6 trade goods."):
        table = TradeGoodsTypeTable("Test", goods)


def test_trade_goods_type_table_roll():
    goods = [f"Good{i}" for i in range(6)]
    table = TradeGoodsTypeTable("RollTable", goods)
    for _ in range(100):
        good = table.roll().get_name()
        assert good in goods


def test_trade_classification_table_access_and_roll():
    table = TradeClassificationGoodsTable("TestClass")
    type_data = {
        "Alpha": ["A1", "A2", "A3", "A4", "A5", "A6"],
        "Beta": ["B1", "B2", "B3", "B4", "B5", "B6"],
        "Gamma": ["C1", "C2", "C3", "C4", "C5", "C6"],
        "Delta": ["D1", "D2", "D3", "D4", "D5", "D6"],
        "Epsilon": ["E1", "E2", "E3", "E4", "E5", "E6"],
        "Zeta": ["Z1", "Z2", "Z3", "Z4", "Z5", "Z6"],
    }
    for k, v in type_data.items():
        table.add_type_table(k, v)

    # Validate fixed retrieval
    assert table.get_good("Alpha", 0).get_name() == "A1"

    # Validate random rolls return valid items
    for _ in range(100):
        result = table.roll().get_name()
        assert any(result in v for v in type_data.values())


def test_too_many_type_tables():
    table = TradeClassificationGoodsTable("Test")
    for i in range(6):
        table.add_type_table(f"type{i}", [f"good{j}" for j in range(6)])
    with pytest.raises(
        ValueError, match="Each classification may only have 6 TradeGoodsTypeTables."
    ):
        table.add_type_table("type6", [f"good{j}" for j in range(6)])


def test_random_trade_goods_get_and_roll():
    rtg = RandomTradeGoodsTable()
    tcgt = TradeClassificationGoodsTable("Foo")

    tcgt.add_type_table("Bar", ["G1", "G2", "G3", "G4", "G5", "G6"])
    tcgt.add_type_table("Baz", ["H1", "H2", "H3", "H4", "H5", "H6"])
    tcgt.add_type_table("Zap", ["I1", "I2", "I3", "I4", "I5", "I6"])
    tcgt.add_type_table("Qux", ["J1", "J2", "J3", "J4", "J5", "J6"])
    tcgt.add_type_table("Rofl", ["K1", "K2", "K3", "K4", "K5", "K6"])
    tcgt.add_type_table("Lol", ["L1", "L2", "L3", "L4", "L5", "L6"])

    rtg.add_classification_table("Foo", tcgt)

    assert rtg.get_good("Foo", "Bar", 1).get_name() == "G2"

    for _ in range(100):
        result = rtg.get_random("Foo")
        assert isinstance(result, str)
        assert result.startswith(("G", "H", "I", "J", "K", "L"))


class DummyRTGTable:
    def __init__(self, expected):
        self.expected = expected
        self.last_classification = None

    def get_random(self, classification):
        self.last_classification = classification
        return self.expected


def test_imbalance_trade_good_resolve_name():
    dummy_rtg = DummyRTGTable("TestGood")
    imbalance = ImbalanceTradeGood("As", dummy_rtg)
    result = imbalance.resolve_name()
    assert result == "Imbalance from As: TestGood (+Cr1,000 if sold on As)"
    assert dummy_rtg.last_classification == "As"
