import logging


class SearchLogger:
    headers = ["Node", "Best Sol", "LB", "Gap", "Message"]
    widths = [7, 10, 10, 7, 14]
    delimiter = " | "

    def __init__(
        self,
        logger: logging.Logger
    ):
        self.logger = logger

    def log_headers(self):
        # Create a formatted header row with fixed widths, centered
        formatted_headers = self._format_row(*self.headers)
        self.logger.info(formatted_headers)
        # Create and log an underscore line below the headers
        underscore_line = self._create_underscore_line()
        self.logger.info(underscore_line)

    def log_row(self, *row):
        # Log the formatted row with fixed widths, centered
        formatted_row = self._format_row(*row)
        self.logger.info(formatted_row)

    def _format_row(self, *row):
        # Format each element to a fixed width and centered
        formatted_row = self.delimiter.join(
            f"{str(item):^{width}}" for item, width in zip(row, self.widths)
        )
        return formatted_row

    def _create_underscore_line(self):
        # Create a line of underscores with the same width as each column
        underscore_line = self.delimiter.join(
            "-" * width for width in self.widths
        )
        return underscore_line
