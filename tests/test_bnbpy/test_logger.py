import logging

import pytest

from bnbpy.logger import SearchLogger


@pytest.fixture
def mock_logger(mocker):
    """Fixture to create a mock logger."""
    return mocker.MagicMock(spec=logging.Logger)


@pytest.fixture
def search_logger(mock_logger):
    """Fixture to create a SearchLogger instance with a mock logger."""
    return SearchLogger(logger=mock_logger)


@pytest.mark.searchlogger
class TestLogger:

    underscores = '----- | ---------- | ---------- | ------- | --------------'
    header = 'Node  |  Best Sol  |     LB     |   Gap   |    Message    '
    ref_row = '  A   |    123     |  456.789   |   12%   |   Processing  '
    ref_args = ('A', '123', '456.789', '12%', 'Processing')

    def test_log_headers(self, search_logger, mock_logger):
        """
        Test that log_headers logs correctly formatted headers and underscores.
        """
        search_logger.log_headers()

        # Check that logger.info was called twice
        n_counts = 2
        assert mock_logger.info.call_count == n_counts

        # Retrieve the actual log messages
        header_call = mock_logger.info.call_args_list[0]
        underscore_call = mock_logger.info.call_args_list[1]

        # Check the header formatting
        assert header_call[0][0] == self.header

        # Check the underscore line
        assert underscore_call[0][0] == self.underscores

    def test_log_row(self, search_logger, mock_logger):
        """Test that log_row logs a correctly formatted row."""
        search_logger.log_row(*self.ref_args)

        # Check that logger.info was called once
        mock_logger.info.assert_called_once()

        # Retrieve the actual log message
        log_call = mock_logger.info.call_args

        # Check the row formatting
        assert log_call[0][0] == self.ref_row

    def test_format_row(self, search_logger):
        """Test the private _format_row method (optional)."""
        # Directly test the formatting
        formatted_row = search_logger._format_row(*self.ref_args)
        assert formatted_row == self.ref_row

    def test_create_underscore_line(self, search_logger):
        """Test the private _create_underscore_line method (optional)."""
        underscore_line = search_logger._create_underscore_line()
        assert underscore_line == self.underscores
