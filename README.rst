IQDM-Analytics
==============

|pypi| |lgtm| |lgtm-cq| |lines| |repo-size| |code-style|

What does it do?
----------------
Desktop application for `IQDM-PDF <https://github.com/IQDM/IQDM-PDF>`__ with statistical analysis.

|screenshot|

Executables
-----------

Single-file executables are available. See attachments in the `latest release <https://github.com/IQDM/IQDM-Analytics/releases/latest>`__.


Other information
-----------------
This library is part of the IMRT QA Data Mining (IQDM) project for
the AAPM `IMRT Working Group (WGIMRT) <https://www.aapm.org/org/structure/?committee_code=WGIMRT>`__.

-  Free software: `MIT license <https://github.com/IQDM/IQDM-Analytics/blob/master/LICENSE>`__


Dependencies
------------
* `iqdmpdf <https://github.com/IQDM/IQDM-PDF>`__ - Mine IMRT QA PDF's
* `wxPython Phoenix <https://github.com/wxWidgets/Phoenix>`__ - Build a native GUI on Windows, Mac, or Unix systems
* `Bokeh <https://github.com/bokeh/bokeh>`__ - Interactive Web Plotting for Python
* `NumPy <http://numpy.org>`__ - The fundamental package for scientific computing with Python
* `selenium <https://github.com/SeleniumHQ/selenium/>`__ - A browser automation framework and ecosystem
* `PhantomJS <https://phantomjs.org/>`__ - PhantomJS is a headless web browser scriptable with JavaScript
* `pypubsub <https://github.com/schollii/pypubsub>`__ - A Python publish-subscribe library


Install and Run
---------------

If you prefer to run from source:

.. code-block:: console

    $ git clone https://github.com/IQDM/IQDM-Analytics.git
    $ cd IQDM-Analytics
    $ python iqdma_app.py


Note you *may* have to use pythonw instead of python, depending on your version.


TODO
----

- `MS Edge support <https://github.com/IQDM/IQDM-Analytics/issues/1>`__
- Ability to cancel PDF-Miner thread
- Documentation
- Docstrings


Credits
-------

----------------
Development Lead
----------------

* Dan Cutright, University of Chicago Medicine

------------
Contributors
------------

* Marc Chamberland, University of Vermont Health Network
* Serpil Kucuker Dogan, Northwestern Medicine
* Mahesh Gopalakrishnan, Northwestern Medicine
* Aditya Panchal, AMITA Health



.. |screenshot| image:: https://user-images.githubusercontent.com/4778878/110705765-76173800-81bc-11eb-8c36-af5b523b83ba.jpg
   :alt: Example Screenshot
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