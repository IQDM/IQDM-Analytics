IQDM-Analytics
==============

|pypi| |Docs| |lgtm| |lgtm-cq| |lines| |repo-size| |code-style|

What does it do?
----------------
IQDM Analytics is a desktop application that mines IMRT QA reports with
`IQDM-PDF <https://github.com/IQDM/IQDM-PDF>`__ and performs statistical
analysis.


Executables
-----------
Single-file executables are available. See attachments in the `latest release <https://github.com/IQDM/IQDM-Analytics/releases/latest>`__.


Other information
-----------------
This library is part of the IMRT QA Data Mining (IQDM) project for
the AAPM `IMRT Working Group (WGIMRT) <https://www.aapm.org/org/structure/?committee_code=WGIMRT>`__.

-  Free software: `MIT license <https://github.com/IQDM/IQDM-Analytics/blob/master/LICENSE>`__
-  Documentation: `Read the docs <https://iqdma.readthedocs.io>`__

|screenshot|


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
- User manual (usage.rst)
- Unit testing (non-GUI stuff)
- Setup continuous integration


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



.. |pypi| image:: https://img.shields.io/pypi/v/iqdma.svg
   :target: https://pypi.org/project/iqdma
   :alt: PyPI
.. |Docs| image:: https://readthedocs.org/projects/iqdma/badge/?version=latest
   :target: https://iqdma.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status
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

.. |screenshot| raw:: html

    <img src='https://user-images.githubusercontent.com/4778878/110721238-b59e4e00-81d5-11eb-8a1e-5aae9266235a.jpg' align='center' width='500' alt="IQDM Analytics screenshot">
