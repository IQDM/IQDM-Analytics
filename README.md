# IQDM Analytics
**Under active development, not ready for wide use.**  
Code to Analyze Data Mining Results from IQDM-PDF with DVHA-Stats

### Requirements
Install these from github until made available on PyPI
* iqdmpdf >= 0.2.7 (`pip install git+https://github.com/IQDM/IQDM-PDF.git`)
* dvha-stats >= 0.2.4 (`pip install git+https://github.com/cutright/DVHA-Stats.git`)

### Example
Univariate Control Chart from SNCPatient2020 csv output from IQDM-PDF
~~~
>>> from iqdma.stats import IQDMStats
>>> s = IQDMStats('SNCPatient2020_results_2021-02-25_14-29-42_edit.csv', 'Pass (%)')
>>> s.print_data_index_by_criteria()

    index: 0
        Summary Type: Summary (DTA Analysis)
        Comparison Type: Absolute Dose Comparison (DTA/Gamma using 2D Mode)
        Difference (%): 3.0
        Distance (mm): 2.0
        Threshold (%): 10.0
        Use Global (%): Yes
        Meas Uncertainty: No
    index: 1
        Summary Type: Summary (Gamma Analysis)
        Comparison Type: Absolute Dose Comparison (DTA/Gamma using 2D Mode)
        Difference (%): 2.0
        Distance (mm): 2.0
        Threshold (%): 10.0
        Use Global (%): Yes
        Meas Uncertainty: No
    index: 2
        Summary Type: Summary (Gamma Analysis)
        Comparison Type: Absolute Dose Comparison (DTA/Gamma using 2D Mode)
        Difference (%): 2.0
        Distance (mm): 2.0
        Threshold (%): 3.0
        Use Global (%): Yes
        Meas Uncertainty: No
    index: 3
        Summary Type: Summary (Gamma Analysis)
        Comparison Type: Absolute Dose Comparison (DTA/Gamma using 2D Mode)
        Difference (%): 3.0
        Distance (mm): 2.0
        Threshold (%): 10.0
        Use Global (%): Yes
        Meas Uncertainty: No
    index: 4
        Summary Type: Summary (Gamma Analysis)
        Comparison Type: Absolute Dose Comparison (DTA/Gamma using 2D Mode)
        Difference (%): 3.0
        Distance (mm): 2.0
        Threshold (%): 3.0
        Use Global (%): Yes
        Meas Uncertainty: No
    index: 5
        Summary Type: Summary (Gamma Analysis)
        Comparison Type: Relative Comparison (DTA/Gamma using 2D Mode)
        Difference (%): 3.0
        Distance (mm): 2.0
        Threshold (%): 10.0
        Use Global (%): N/A
        Meas Uncertainty: No


>>> ucc = s.univariate_control_charts()
>>> ucc[3].show()  # based on the print out from print_data_index_by_criteria

~~~