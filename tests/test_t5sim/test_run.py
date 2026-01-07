"""Test the CLI interface for t5sim."""

import pytest
from unittest.mock import patch, MagicMock
from t5sim.run import main


@pytest.fixture
def mock_run_simulation():
    """Mock the Simulation class."""
    with patch('t5sim.run.Simulation') as mock_sim_class:
        # Create mock instance
        mock_sim_instance = MagicMock()
        mock_sim_instance.run.return_value = {
            'total_voyages': 42,
            'cargo_sales': 150,
            'total_profit': 500000.0,
            'num_ships': 10,
            'ships': [
                {'name': 'Ship1', 'balance': 1200000.0, 'voyages': 5},
                {'name': 'Ship2', 'balance': 1150000.0, 'voyages': 4},
                {'name': 'Ship3', 'balance': 1100000.0, 'voyages': 4},
                {'name': 'Ship4', 'balance': 1050000.0, 'voyages': 4},
                {'name': 'Ship5', 'balance': 1000000.0, 'voyages': 4},
                {'name': 'Ship6', 'balance': 950000.0, 'voyages': 3},
                {'name': 'Ship7', 'balance': 900000.0, 'voyages': 3},
                {'name': 'Ship8', 'balance': 850000.0, 'voyages': 3},
                {'name': 'Ship9', 'balance': 800000.0, 'voyages': 2},
                {'name': 'Ship10', 'balance': 750000.0, 'voyages': 2},
            ]
        }
        mock_sim_class.return_value = mock_sim_instance
        yield mock_sim_class


def test_main_default_args(mock_run_simulation, capsys):
    """Test main with default arguments."""
    with patch('sys.argv', ['run.py']):
        main()

    # Check Simulation was called with defaults
    mock_run_simulation.assert_called_once()
    call_kwargs = mock_run_simulation.call_args[1]
    assert call_kwargs['num_ships'] == 10
    assert call_kwargs['duration_days'] == pytest.approx(365.0)
    assert call_kwargs['verbose'] is False
    assert call_kwargs['starting_year'] == 1104
    assert call_kwargs['starting_day'] == 360

    # Check output
    captured = capsys.readouterr()
    assert "T5SIM - Traveller 5 Trading Simulation" in captured.out
    assert "Ships: 10" in captured.out
    assert "Duration: 365.0 days" in captured.out
    assert "Total voyages completed: 42" in captured.out
    assert "Total profit: Cr500,000.00" in captured.out


def test_main_custom_ships(mock_run_simulation, capsys):
    """Test main with custom ship count."""
    with patch('sys.argv', ['run.py', '--ships', '25']):
        main()

    mock_run_simulation.assert_called_once()
    call_kwargs = mock_run_simulation.call_args[1]
    assert call_kwargs['num_ships'] == 25

    captured = capsys.readouterr()
    assert "Ships: 25" in captured.out


def test_main_custom_duration(mock_run_simulation, capsys):
    """Test main with custom duration."""
    with patch('sys.argv', ['run.py', '--days', '100.5']):
        main()

    mock_run_simulation.assert_called_once()
    call_kwargs = mock_run_simulation.call_args[1]
    assert call_kwargs['duration_days'] == pytest.approx(100.5)

    captured = capsys.readouterr()
    assert "Duration: 100.5 days" in captured.out


def test_main_custom_files(mock_run_simulation):
    """Test main with custom file paths."""
    with patch('sys.argv', [
        'run.py',
        '--map', 'custom/map.txt',
        '--ships-file', 'custom/ships.csv'
    ]):
        # Mock the file loading functions
        with patch('t5sim.run.gs_module.load_and_parse_t5_map') as mock_map, \
            patch('t5sim.run.gs_module.load_and_parse_t5_ship_classes') \
                as mock_ships:
            mock_map.return_value = {}
            mock_ships.return_value = {}
            main()

    # Check that the correct files were requested
    # (File paths are passed through but we mock the loaders)
    mock_run_simulation.assert_called_once()


def test_main_verbose(mock_run_simulation):
    """Test main with verbose flag."""
    with patch('sys.argv', ['run.py', '--verbose']):
        main()

    mock_run_simulation.assert_called_once()
    call_kwargs = mock_run_simulation.call_args[1]
    assert call_kwargs['verbose'] is True


def test_main_verbose_short_flag(mock_run_simulation):
    """Test main with short verbose flag."""
    with patch('sys.argv', ['run.py', '-v']):
        main()

    mock_run_simulation.assert_called_once()
    call_kwargs = mock_run_simulation.call_args[1]
    assert call_kwargs['verbose'] is True


def test_main_combined_args(mock_run_simulation, capsys):
    """Test main with multiple arguments."""
    with patch('sys.argv', [
        'run.py',
        '--ships', '15',
        '--days', '180',
        '--verbose'
    ]):
        main()

    mock_run_simulation.assert_called_once()
    call_kwargs = mock_run_simulation.call_args[1]
    assert call_kwargs['num_ships'] == 15
    assert call_kwargs['duration_days'] == pytest.approx(180.0)
    assert call_kwargs['verbose'] is True

    captured = capsys.readouterr()
    assert "Ships: 15" in captured.out
    assert "Duration: 180.0 days" in captured.out


def test_main_results_output(mock_run_simulation, capsys):
    """Test that results are properly formatted in output."""
    with patch('sys.argv', ['run.py', '--ships', '10']):
        main()

    captured = capsys.readouterr()

    # Check results section
    assert "SIMULATION RESULTS" in captured.out
    assert "Total voyages completed: 42" in captured.out
    assert "Total cargo sales: 150" in captured.out
    assert "Total profit: Cr500,000.00" in captured.out

    # Check timing output with parameters (after totals)
    assert "Simulation time:" in captured.out
    assert "seconds (10 ships, 365.0 days)" in captured.out

    # Check averages
    assert "Average per ship:" in captured.out
    assert "Voyages: 4.2" in captured.out
    assert "Profit: Cr50,000.00" in captured.out

    # Check top ships
    assert "Top 5 ships by balance:" in captured.out
    assert "1. Ship1, a Unknown @ Unknown: "\
           "Cr1,200,000.00 (5 voyages)" in captured.out
    assert "2. Ship2, a Unknown @ Unknown: "\
           "Cr1,150,000.00 (4 voyages)" in captured.out

    # Check bottom ships
    assert "Bottom 5 ships by balance:" in captured.out
    assert "1. Ship6, a Unknown @ Unknown: "\
           "Cr950,000.00 (3 voyages)" in captured.out
    assert "5. Ship10, a Unknown @ Unknown: "\
           "Cr750,000.00 (2 voyages)" in captured.out


def test_main_results_output_single_ship(mock_run_simulation, capsys):
    """Test that singular grammar is used when there's only 1 ship."""
    # Mock Simulation's run() to return results with 1 ship
    mock_run_simulation.return_value.run.return_value = {
        'total_voyages': 5,
        'cargo_sales': 10,
        'total_profit': 25000.0,
        'num_ships': 1,
        'ships': [
            {
                'name': 'Solo Ship',
                'balance': 1025000.0,
                'voyages': 5,
                'location': 'Unknown',
                'ship_class': 'Scout'
            }
        ]
    }

    with patch('sys.argv', ['run.py', '--ships', '1']):
        main()

    captured = capsys.readouterr()

    # Check singular grammar is used
    assert "Top ship by balance:" in captured.out
    assert "Bottom ship by balance:" in captured.out
    assert "Solo Ship, a Scout @ Unknown" in captured.out


def test_main_module_execution():
    """Test running the module as __main__."""
    import subprocess
    import sys

    # Run the module with --help to test it's executable
    result = subprocess.run(
        [sys.executable, "-m", "t5sim.run", "--help"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
    assert "Traveller 5 trade simulation" in result.stdout


def test_main_timing_output(mock_run_simulation, capsys):
    """Test that simulation timing is displayed."""
    with patch('sys.argv', ['run.py']):
        main()

    captured = capsys.readouterr()
    assert "Simulation time:" in captured.out
    assert "seconds" in captured.out
    # Verify the format matches expected pattern with parameters
    import re
    timing_match = re.search(
        r'Simulation time: (\d+\.\d{2}) seconds '
        r'\((\d+) ships, ([\d.]+) days\)',
        captured.out)
    assert timing_match is not None, \
        "Timing output should match pattern 'X.XX seconds (N ships, M days)'"
    # Timing should be a reasonable value (< 10 seconds for a mocked test)
    elapsed = float(timing_match.group(1))
    assert 0 <= elapsed < 10, \
        f"Elapsed time {elapsed} seems unreasonable for mocked test"
    # Verify parameters are captured correctly
    assert timing_match.group(2) == '10', "Ships count should be 10"
    assert timing_match.group(3) == '365.0', "Days should be 365.0"


def test_main_ledger_flag(capsys):
    """Test main with --ledger flag."""
    with patch('sys.argv', ['run.py', '--ledger', 'Ship1']):
        # Mock the Simulation class
        with patch('t5sim.run.Simulation') as MockSim:
            mock_sim_instance = MockSim.return_value
            mock_sim_instance.run.return_value = {
                'total_voyages': 42,
                'cargo_sales': 150,
                'total_profit': 500000.0,
                'num_ships': 10,
                'ships': [
                    {'name': 'Ship1', 'balance': 1200000.0, 'voyages': 5},
                ]
            }

            main()

            # Verify print_ledger was called with the ship name
            mock_sim_instance.print_ledger.assert_called_once_with('Ship1')


def test_main_ledger_all_flag(capsys):
    """Test main with --ledger-all flag."""
    with patch('sys.argv', ['run.py', '--ledger-all']):
        # Mock the Simulation class
        with patch('t5sim.run.Simulation') as MockSim:
            mock_sim_instance = MockSim.return_value
            mock_sim_instance.run.return_value = {
                'total_voyages': 42,
                'cargo_sales': 150,
                'total_profit': 500000.0,
                'num_ships': 10,
                'ships': [
                    {'name': 'Ship1', 'balance': 1200000.0, 'voyages': 5},
                ]
            }

            main()

            # Verify print_all_ledgers was called
            mock_sim_instance.print_all_ledgers.assert_called_once()


def test_main_ledger_invalid_ship(capsys):
    """Test main with --ledger flag for invalid ship name."""
    with patch('sys.argv', ['run.py', '--ledger', 'InvalidShip']):
        # Mock the Simulation class
        with patch('t5sim.run.Simulation') as MockSim:
            mock_sim_instance = MockSim.return_value
            mock_sim_instance.run.return_value = {
                'total_voyages': 42,
                'cargo_sales': 150,
                'total_profit': 500000.0,
                'num_ships': 10,
                'ships': [
                    {'name': 'Ship1', 'balance': 1200000.0, 'voyages': 5},
                ]
            }
            mock_sim_instance.print_ledger.side_effect = ValueError(
                "Ship 'InvalidShip' not found. "
                "Available ships: ['Ship1', 'Ship2']"
            )

            main()

            # Verify error message was printed
            captured = capsys.readouterr()
            assert "Error: Ship 'InvalidShip' not found" in captured.out


def test_filter_ships_by_role_no_flags():
    """Test that no role flags returns all ships."""
    from t5sim.run import _filter_ships_by_role

    raw_ships = {
        'Scout': {'role': 'civilian', 'class_name': 'Scout'},
        'Corsair': {'role': 'military', 'class_name': 'Corsair'},
        'Packet': {'role': 'specialized', 'class_name': 'Packet'},
    }

    result = _filter_ships_by_role(raw_ships, False, False, False)

    # Should return all ships when no flags are set
    assert len(result) == 3
    assert 'Scout' in result
    assert 'Corsair' in result
    assert 'Packet' in result


def test_filter_ships_by_role_civilian_only():
    """Test filtering for civilian ships only."""
    from t5sim.run import _filter_ships_by_role

    raw_ships = {
        'Scout': {'role': 'civilian', 'class_name': 'Scout'},
        'Free Trader': {'role': 'civilian', 'class_name': 'Free Trader'},
        'Corsair': {'role': 'military', 'class_name': 'Corsair'},
        'Packet': {'role': 'specialized', 'class_name': 'Packet'},
    }

    result = _filter_ships_by_role(raw_ships, True, False, False)

    # Should return only civilian ships
    assert len(result) == 2
    assert 'Scout' in result
    assert 'Free Trader' in result
    assert 'Corsair' not in result
    assert 'Packet' not in result


def test_filter_ships_by_role_military_only():
    """Test filtering for military ships only."""
    from t5sim.run import _filter_ships_by_role

    raw_ships = {
        'Scout': {'role': 'civilian', 'class_name': 'Scout'},
        'Corsair': {'role': 'military', 'class_name': 'Corsair'},
        'Corvette': {'role': 'military', 'class_name': 'Corvette'},
        'Packet': {'role': 'specialized', 'class_name': 'Packet'},
    }

    result = _filter_ships_by_role(raw_ships, False, True, False)

    # Should return only military ships
    assert len(result) == 2
    assert 'Corsair' in result
    assert 'Corvette' in result
    assert 'Scout' not in result
    assert 'Packet' not in result


def test_filter_ships_by_role_specialized_only():
    """Test filtering for specialized ships only."""
    from t5sim.run import _filter_ships_by_role

    raw_ships = {
        'Scout': {'role': 'civilian', 'class_name': 'Scout'},
        'Corsair': {'role': 'military', 'class_name': 'Corsair'},
        'Packet': {'role': 'specialized', 'class_name': 'Packet'},
        'Lab Ship': {'role': 'specialized', 'class_name': 'Lab Ship'},
    }

    result = _filter_ships_by_role(raw_ships, False, False, True)

    # Should return only specialized ships
    assert len(result) == 2
    assert 'Packet' in result
    assert 'Lab Ship' in result
    assert 'Scout' not in result
    assert 'Corsair' not in result


def test_filter_ships_by_role_multiple_roles():
    """Test filtering for multiple roles."""
    from t5sim.run import _filter_ships_by_role

    raw_ships = {
        'Scout': {'role': 'civilian', 'class_name': 'Scout'},
        'Corsair': {'role': 'military', 'class_name': 'Corsair'},
        'Packet': {'role': 'specialized', 'class_name': 'Packet'},
    }

    result = _filter_ships_by_role(raw_ships, True, True, False)

    # Should return civilian and military ships
    assert len(result) == 2
    assert 'Scout' in result
    assert 'Corsair' in result
    assert 'Packet' not in result


def test_filter_ships_by_role_missing_role():
    """Test error when requested role has no ships."""
    from t5sim.run import _filter_ships_by_role

    raw_ships = {
        'Scout': {'role': 'civilian', 'class_name': 'Scout'},
        'Corsair': {'role': 'military', 'class_name': 'Corsair'},
    }

    # Requesting specialized ships when none exist should raise error
    with pytest.raises(ValueError, match="No ships with role 'specialized'"):
        _filter_ships_by_role(raw_ships, False, False, True)


def test_filter_ships_by_role_no_matches():
    """Test error when filter results in no ships."""
    from t5sim.run import _filter_ships_by_role

    # Manually create a scenario where filtering results in empty dict
    # by directly testing the empty result path
    # Since the function checks for role availability first,
    # we need to test with a role that exists but gets filtered out
    # Actually, let's just verify the "no ships with role" error works
    empty_ships = {}

    # Requesting any role with no ships should raise the first error
    with pytest.raises(ValueError,
                       match="No ships with role 'civilian' found"):
        _filter_ships_by_role(empty_ships, True, False, False)


def test_main_with_role_filtering(mock_run_simulation, capsys):
    """Test main with role filtering flags."""
    with patch('sys.argv', ['run.py', '--ships', '5', '--include-civilian']):
        main()

    # Verify Simulation was called
    mock_run_simulation.assert_called_once()

    # Check output mentions ships
    captured = capsys.readouterr()
    assert "Ships: 5" in captured.out


def test_main_with_multiple_role_filters(mock_run_simulation, capsys):
    """Test main with multiple role filtering flags."""
    with patch('sys.argv', [
        'run.py', '--ships', '10',
        '--include-civilian', '--include-military'
    ]):
        main()

    # Verify Simulation was called
    mock_run_simulation.assert_called_once()

    # Check output
    captured = capsys.readouterr()
    assert "Ships: 10" in captured.out


def test_validate_role_frequencies_ok():
    """Frequencies summing to 1.0 per role should pass silently."""
    from t5sim.run import _validate_role_frequencies
    raw_ships = {
        'Scout': {'role': 'civilian', 'frequency': 0.6},
        'Free Trader': {'role': 'civilian', 'frequency': 0.4},
        'Corsair': {'role': 'military', 'frequency': 0.7},
        'Corvette': {'role': 'military', 'frequency': 0.3},
    }
    _validate_role_frequencies(raw_ships)  # no exception


def test_validate_role_frequencies_mismatch_single_role():
    """Mismatch in one role should raise with clear message."""
    from t5sim.run import _validate_role_frequencies
    raw_ships = {
        'Scout': {'role': 'civilian', 'frequency': 0.5},
        'Free Trader': {'role': 'civilian', 'frequency': 0.3},  # sums 0.8
        'Corsair': {'role': 'military', 'frequency': 0.7},
        'Corvette': {'role': 'military', 'frequency': 0.3},
    }
    with pytest.raises(ValueError, match=r"role 'civilian' sums to 0.80"):
        _validate_role_frequencies(raw_ships)


def test_main_stops_on_frequency_mismatch():
    """main() should stop (raise) when role totals are invalid."""
    bad_ships = {
        'Scout': {'role': 'civilian', 'frequency': 0.2},
        'Free Trader': {'role': 'civilian', 'frequency': 0.2},  # 0.4 total
        'Corsair': {'role': 'military', 'frequency': 1.0},
    }
    with patch('t5sim.run.gs_module.load_and_parse_t5_ship_classes',
               return_value=bad_ships), \
         patch('sys.argv', ['run.py']):
        with pytest.raises(ValueError, match='Frequency totals invalid'):
            main()


def test_validate_role_frequencies_non_numeric_frequency_treated_as_zero():
    """Non-numeric frequency values are treated as 0.0 during validation."""
    from t5sim.run import _validate_role_frequencies
    raw_ships = {
        'Scout': {'role': 'civilian', 'frequency': 'oops'},  # becomes 0.0
        'Free Trader': {'role': 'civilian', 'frequency': 1.0},
    }
    # Should not raise; totals for civilian = 1.0 after coercion
    _validate_role_frequencies(raw_ships)


def test_print_ship_leaderboards_broke_singular(capsys):
    """Ensure singular broke ship label is printed."""
    from t5sim.run import _print_ship_leaderboards

    results = {
        'ships': [
            {
                'name': 'BrokeShip',
                'balance': -1000.0,
                'voyages': 0,
                'ship_class': 'Scout',
                'location': 'Rhylanor',
                'broke': True,
            }
        ]
    }

    _print_ship_leaderboards(results, sim=None)
    out = capsys.readouterr().out
    assert "Broke ship:" in out


def test_print_ship_leaderboards_top_bottom_singular(capsys):
    """Ensure singular top/bottom labels are printed for one active ship."""
    from t5sim.run import _print_ship_leaderboards

    results = {
        'ships': [
            {
                'name': 'SoloShip',
                'balance': 12345.0,
                'voyages': 3,
                'ship_class': 'Free Trader',
                'location': 'Rhylanor',
                'broke': False,
            }
        ]
    }

    _print_ship_leaderboards(results, sim=None)
    out = capsys.readouterr().out
    assert "Top ship by balance:" in out
    assert "Bottom ship by balance:" in out


def test_print_ship_leaderboards_broke_plural(capsys):
    """Ensure plural broke ships label with count is printed."""
    from t5sim.run import _print_ship_leaderboards

    results = {
        'ships': [
            {
                'name': 'Broke1', 'balance': -100.0, 'voyages': 1,
                'ship_class': 'Scout', 'location': 'Rhylanor', 'broke': True,
            },
            {
                'name': 'Broke2', 'balance': -200.0, 'voyages': 2,
                'ship_class': 'Free Trader',
                'location': 'Rhylanor', 'broke': True,
            },
        ]
    }

    _print_ship_leaderboards(results, sim=None)
    out = capsys.readouterr().out
    assert "Broke ships (2):" in out


def test_calculate_role_proportions_all_roles():
    """Test role proportions when all 3 roles are selected."""
    from t5sim.simulation import calculate_role_proportions

    proportions = calculate_role_proportions(True, True, True)
    assert proportions == {
        "civilian": 0.7,
        "specialized": 0.2,
        "military": 0.1
    }


def test_calculate_role_proportions_no_roles():
    """Test role proportions when no roles selected (default to all)."""
    from t5sim.simulation import calculate_role_proportions

    proportions = calculate_role_proportions(False, False, False)
    assert proportions == {
        "civilian": 0.7,
        "specialized": 0.2,
        "military": 0.1
    }


def test_calculate_role_proportions_civ_spec():
    """Test role proportions for civilian + specialized."""
    from t5sim.simulation import calculate_role_proportions

    proportions = calculate_role_proportions(True, False, True)
    assert proportions == {"civilian": 0.8, "specialized": 0.2}


def test_calculate_role_proportions_civ_mil():
    """Test role proportions for civilian + military."""
    from t5sim.simulation import calculate_role_proportions

    proportions = calculate_role_proportions(True, True, False)
    assert proportions == {"civilian": 0.8, "military": 0.2}


def test_calculate_role_proportions_spec_mil():
    """Test role proportions for specialized + military."""
    from t5sim.simulation import calculate_role_proportions

    proportions = calculate_role_proportions(False, True, True)
    assert proportions == {"specialized": 0.7, "military": 0.3}


def test_calculate_role_proportions_civ_only():
    """Test role proportions for civilian only."""
    from t5sim.simulation import calculate_role_proportions

    proportions = calculate_role_proportions(True, False, False)
    assert proportions == {"civilian": 1.0}


def test_calculate_role_proportions_spec_only():
    """Test role proportions for specialized only."""
    from t5sim.simulation import calculate_role_proportions

    proportions = calculate_role_proportions(False, False, True)
    assert proportions == {"specialized": 1.0}


def test_calculate_role_proportions_mil_only():
    """Test role proportions for military only."""
    from t5sim.simulation import calculate_role_proportions

    proportions = calculate_role_proportions(False, True, False)
    assert proportions == {"military": 1.0}
