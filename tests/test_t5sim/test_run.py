"""Test the CLI interface for t5sim."""

import pytest
from unittest.mock import patch
from t5sim.run import main


@pytest.fixture
def mock_run_simulation():
    """Mock the run_simulation function."""
    with patch('t5sim.run.run_simulation') as mock:
        mock.return_value = {
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
        yield mock


def test_main_default_args(mock_run_simulation, capsys):
    """Test main with default arguments."""
    with patch('sys.argv', ['run.py']):
        main()

    # Check run_simulation was called with defaults
    mock_run_simulation.assert_called_once_with(
        map_file='resources/t5_map.txt',
        ship_classes_file='resources/t5_ship_classes.csv',
        num_ships=10,
        duration_days=365.0,
        verbose=False,
        starting_year=1104,
        starting_day=360,
    )

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
        main()

    mock_run_simulation.assert_called_once()
    call_kwargs = mock_run_simulation.call_args[1]
    assert call_kwargs['map_file'] == 'custom/map.txt'
    assert call_kwargs['ship_classes_file'] == 'custom/ships.csv'


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
    assert "1. Ship1: Cr1,200,000.00 (5 voyages)" in captured.out
    assert "2. Ship2: Cr1,150,000.00 (4 voyages)" in captured.out

    # Check bottom ships
    assert "Bottom 5 ships by balance:" in captured.out
    assert "1. Ship6: Cr950,000.00 (3 voyages)" in captured.out
    assert "5. Ship10: Cr750,000.00 (2 voyages)" in captured.out


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
