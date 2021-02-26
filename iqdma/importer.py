from os.path import basename
from dvhastats.utilities import widen_data, csv_to_dict
from IQDMPDF.parsers.sncpatient import SNCPatientReport2020, SNCPatientCustom
from IQDMPDF.parsers.delta4 import Delta4Report
from IQDMPDF.parsers.verisoft import VeriSoftReport

PARSERS = {'SNCPatient2020': SNCPatientReport2020,
           'SNCPatientCustom': SNCPatientCustom,
           'Delta4Report': Delta4Report,
           'VeriSoftReport': VeriSoftReport}


class ReportImporter:
    def __init__(self, report_file_path, charting_column):
        data_dict = csv_to_dict(report_file_path)

        self.parser = PARSERS[basename(report_file_path).split('_')[0]]()
        self.columns = self.parser.columns
        self.analysis_columns = self.parser.analysis_columns

        kwargs = {'uid_columns': self._get_columns('uid'),
                  'x_data_cols': self._get_columns('criteria'),
                  'y_data_col': charting_column,
                  'date_col':  self.columns[self.analysis_columns['date']],
                  'dtype': float}
        self.data = widen_data(data_dict, **kwargs)
        self.x_axis = self.data.pop('date')
        self.uids = self.data.pop('uid')

    def _get_columns(self, key):
        return [self.columns[i] for i in self.analysis_columns[key]]
