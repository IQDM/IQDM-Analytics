IQDM-Analytics
==============

|pypi| |lgtm| |lgtm-cq| |lines| |repo-size| |code-style|

What does it do?
----------------
IMRT QA data mining with `IQDM-PDF <https://github.com/IQDM/IQDM-PDF>`__ and statistical analysis using `DVHA-Stats <http://stats.dvhanalytics.com>`__.


Other information
-----------------
This library is part of the IMRT QA Data Mining (IQDM) project for
the AAPM `IMRT Working Group (WGIMRT) <https://www.aapm.org/org/structure/?committee_code=WGIMRT>`__.

-  Free software: `MIT license <https://github.com/IQDM/IQDM-Analytics/blob/master/LICENSE>`__


Dependencies
------------
* `iqdmpdf <https://github.com/IQDM/IQDM-PDF>`__ - Mine IMRT QA PDF's
* `dvha-stats <http://stats.dvhanalytics.com>`__ - DVH Analytics statistics library
* `wxPython Phoenix <https://github.com/wxWidgets/Phoenix>`__ - Build a native GUI on Windows, Mac, or Unix systems
* `Bokeh <https://github.com/bokeh/bokeh>`__ - Interactive Web Plotting for Python
* `NumPy <http://numpy.org>`__ - The fundamental package for scientific computing with Python
* `matplotlib <http://matplotlib.org>`__ - Visualization with Python
* `selenium <https://github.com/SeleniumHQ/selenium/>`__
* `PhantomJS <https://phantomjs.org/>`__


Install
-------

.. code-block:: console

    $ pip install git+https://github.com/IQDM/IQDM-Analytics.git


Run
---

.. code-block:: console

    $ iqdma



TODO
----

- `MS Edge support <https://github.com/IQDM/IQDM-Analytics/issues/1>`__
- Ability to cancel PDF-Miner thread
- Documentation
- Docstrings
- Error Log


Credits
-------

----------------
Development Lead
----------------

* Dan Cutright


.. |pypi| image:: https://img.shields.io/pypi/v/iqdma.svg
   :target: https://pypi.org/project/iqdma
   :alt: PyPI
.. |lgtm-cq| image:: https://img.shields.io/lgtm/grade/python/g/IQDM/IQDM-Analytics.svg?logo=lgtm&label=code%20quality
   :target: https://lgtm.com/projects/g/IQDM/IQDM-Analytics/context:python
   :alt: lgtm code quality
.. |lgtm| image:: https://img.shields.io/lgtm/alerts/g/IQDM/IQDM-Analytics.svg?logo=lgtm
   :target: https://lgtm.com/projects/g/IQDM/IQDM-Analytics/alerts
   :alt: lgtm
.. |lines| image:: https://img.shields.io/tokei/lines/github/iqdm/iqdm-analytics
   :target: https://img.shields.io/tokei/lines/github/iqdm/iqdm-analytics
   :alt: Lines of code
.. |repo-size| image:: https://img.shields.io/github/languages/code-size/iqdm/iqdm-analytics
   :target: https://img.shields.io/github/languages/code-size/iqdm/iqdm-analytics
   :alt: Repo Size
.. |code-style| image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black
   :alt: Code style: black