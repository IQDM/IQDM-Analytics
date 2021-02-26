from iqdma.importer import ReportImporter
from dvhastats.ui import DVHAStats


class IQDMStats(DVHAStats):
    def __init__(self, report_file_path, charting_column):
        imported_data = ReportImporter(report_file_path, charting_column)
        super().__init__(imported_data.data, x_axis=imported_data.x_axis)
