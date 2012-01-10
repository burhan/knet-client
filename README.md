# KNET Sample Client #

This is a fully contained KNET client application that demonstrates how to use
the *e24PaymentPipe* class that I wrote.

Simply run this with any valid _resource.cgn_ file and alias; a SSL server is not 
required.

It also includes all the database fields that you need to store from KNET and what 
you need to display in order to pass validation and testing.

Notes
=====

_*It uses a SQLite database for development purposes - *which is reset on restarting the system.*_

Setup
=====

* Check out the source code and install the requirements as listed in `requirements.txt` file with `pip`:

`$ virtualenv --no-site-packages myenv`
`$ pip install -E myenv -r requirements.txt`

* Place your `resource.cgn` file in the directory where you checked out the source

* Modify the `settings.cfg` file as required for your application.

* Run the test server `python main.py`

* Open a browser and go to `http://localhost:5000/1/123.456`

# Your browser should redirect to KNET payment page


