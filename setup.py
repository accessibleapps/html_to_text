from setuptools import setup

__version__ = "0.11"
__doc__ = """Converts HTML to text"""

setup(
 name = "html_to_text",
 version = __version__,
 description = __doc__,
 py_modules = ["html_to_text"],
 install_requires = [
  'lxml',
 ],
 zip_safe=False,
)
