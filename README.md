TaxFinder
=========

The TaxFinder module is a library to help with NCBI taxonomy ids.

Install it using `pip`, preferable into a virtual environment:

```sh
$ pip install taxfinder
```

TaxFinder needs to download and create a databse with taxonomy information. This database needs in the order of 300 MB disc space. To create the database, run

```sh
$ taxfinder_update
```

By default, TaxFinder tries to create the database in the installation directory. If you experience problems or you want to save the database to another path, set the environment variable `TFPATH` to the desired path. This path must be readable and writable for TaxFinder.

To use TaxFinder, you need to import it and instanciate the main class. This will open the database and also cache your queries so repeated queries are answered faster.

```python
from taxfinder import TaxFinder

TF = TaxFinder()

print(TF.getLineage(9606))
```

In an interactive session, you can also get help on the TaxFinder methods:

```python
>>> from taxfinder import TaxFinder
>>> help(TaxFinder)
```
