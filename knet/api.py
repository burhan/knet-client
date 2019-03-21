# encoding: UTF-8
"""
 
 This is a pure python implementation of the e24PaymentPipe class
 usually provided with ACI payment gateway modules.

 The default samples provided with the gateway are only in Java,
 ASP and ColdFusion so this class was created to provide an
 implementation in pure Python.

 @author Burhan Khalid <burhan.khalid@gmail.com>

 This code is provided with no license restrictions.
 You may use it, derive from it, modify it at your own peril.
 The author is not responsible should the use of this code
 lead to strange anomalies in the time space continuum.


"""

from io import StringIO
import itertools
import zipfile
import http.client
import urllib
import string

from xml.dom.minidom import parseString

class AliasNotFound(Exception): pass
class GatewayError(Exception): pass
class InvalidResponse(Exception): pass


class e24PaymentPipe():
    """

      This is the main class that defines the payment pipe. For historical
      reasons, the name of this class matches that of the Java class.

      However, this can easily be changed in any future revisions.

      The class provides the following methods and properties.

      See the example implementation for a working example.

      Properties
      ==========

      ERROR_URL = A fully qualified URL that will be used in case there is an error with the transaction
      RESPONSE_URL = The redirect URL after a successful response

      Sample use:
      from datetime import datetime
      from e24PaymentPipe import e24PaymentPipe as gateway

      gw = gateway('somefile.cgn','somealias')
      try:
        gw.parse()
      except (zipfile.BadZipfile,AliasNotFound):
        pass

      gw.ERROR_URL = 'https://www.example.com/error.html'
      gw.RESPONSE_URL = 'https://www.example.com/return.jsp'

      trackid = "{0.year}{0.month}{0.day}{0.hour}{0.minute}".format(datetime.now())

      try:
        r = gw.transaction(trackid,amount=2.000)
      except GatewayError:
        pass

      print('Payment ID: %s' % r[0])
      print('Gateway URL: %s' % r[1])


    """

    ERROR_URL = None
    RESPONSE_URL = None
    ALIAS = None
    RESOURCE = None

    def __init__(self, resource, alias):
        self._buffer = 2320 # Buffer for reading lines from the resource file
        self._nodes = ('id', 'password', 'webaddress', 'port', 'context')
        self._gw = dict() # Stores the various elements to create the gateway
        self._action = 1 # For payment

        self.RESOURCE = resource
        self.ALIAS = alias

    def _xor(self, s):
        key = "Those who profess to favour freedom and yet depreciate agitation are men who want rain "
        key += "without thunder and lightning"
        key = itertools.cycle(key)
        return ''.join(chr(ord(x) ^ ord(y)) for (x, y) in itertools.izip(s, key))


    def parse(self):
        """
          
          Method to parse the resource file for the terminal alias
          provided, and populate the gw array with the terminal information.

          Parameters
          ==========
             None

          Exceptions
          ==========

             zipfile.BadZipfile - in case resource file cannot be read
             AliasNotFound - if alias terminal not found in
             resource file

        """

        out = StringIO.StringIO() # Temporary "file" to hold the zipped content
        with open(self.RESOURCE, 'rb') as f:
            out.write(self._xor(f.read(self._buffer)))

        try:
            temp = zipfile.ZipFile(out)
        except zipfile.BadZipfile:
            raise zipfile.BadZipfile

        if self.ALIAS + ".xml" in temp.namelist():
            t = temp.open(self.ALIAS + ".xml")
            s = self._xor(''.join(f for f in t.read(self._buffer)))
        else:
            raise Exception(AliasNotFound, "%s not found in %s."
            % (self.ALIAS, self.RESOURCE))

        d = parseString(s) # Populate the DOM from the XML file

        for node in self._nodes:
            self._gw[node] = d.getElementsByTagName(node)[0].childNodes[0].nodeValue


    def connect(self, params):
        """

          Performs the connection to the gateway to retrieve the
          paymentid and gateway URL for submission of the payment request

          Parameters
          ==========

            params - a dictionary of various parameters required to submit to
            the payment gateway for a successful request.

          Exceptions
          ==========

            httplib.HTTPException
            httplib.NotConnected
            InvalidResponse - invalid response received from the gateway

          Returns
          =======

            Two member list, as a result of the gateway transaction

        """

        params = urllib.urlencode(params)

        try:
            if int(self._gw['port']) == httplib.HTTPS_PORT:
                conn = httplib.HTTPSConnection(self._gw['webaddress'], httplib.HTTPS_PORT)
            else:
                conn = httplib.HTTPConnection(self._gw['webaddress'], httplib.HTTP_PORT)
        except httplib.HTTPException:
            raise Exception(httplib.HTTPException, 'Cannot open a connection to %s on port %s. Error was %s' %
                                                   (self._gw['webaddress'], self._gw['port'], httplib.HTTPException))

        try:
            conn.connect()
        except httplib.NotConnected:
            raise Exception(httplib.NotConnected)

        if self._gw['context'][-1] != '/':
            context = self._gw['context'] + '/'
        else:
            context = self._gw['context']

        context = '/' + context + 'servlet/PaymentInitHTTPServlet'
        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}

        try:
            conn.request("POST", context, params, headers)
        except httplib.HTTPException:
            raise httplib.HTTPException

        result = conn.getresponse()
        data = result.read()

        try:
            return data.split(':', 1)
        except KeyError:
            raise Exception(InvalidResponse)


    def transaction(self, trackid, udf=None, amount=1.000, lang='ENG', currency=414, filter_=True):
        """

           Main method to initiate a transaction request for the gateway.

           Parameters
           ==========

             amount - float, minimum 1, default 1.000

             lang - code of the language to be used, defaults to 'ENG'

             currency - ISO currency code, defaults to 414 for Kuwaiti Dinars

             filter_ - Switch to filter UDF fields. Defaults to True

             udf - a dictionary object containing UDF fields for the
             transaction. See your gateway documentation on UDF fields. Format
             is:

                udf['udf1'] = 'some text'
                udf['udf2'] = 'some text

             trackid = a unique tracking id. Can be in any format, but must be
             unique for each transaction request; and must not contain any characters
             listed in the table "characters not allowed".

             Returns
             =======

             Two member list containing the payment id, and the gateway URL

             Exceptions
             ==========

             In case of an error, an exception is thrown with the text of the
             error message.

             Following characters are not allowed in UDF fields or trackid.
             For UDF fields, the code will do a simple substitution with "-",
             if you don't want this done, because you have already
             taken care of this, call the method with 'filter_=False'

             Sym   Hex  Name
             ===============
             ~     x7E  TILDE
             `     x60  LEFT SINGLE QUOTATION MARK, GRAVE ACCENT
             !     x21  EXCLAMATION POINT (bang)
             #     x23  NUMBER SIGN (pound sign)
             $     x24  DOLLAR SIGN
             %     x25  PERCENT SIGN
             ^     x5E  CIRCUMFLEX ACCENT
             |     x7C  VERTICAL LINE (pipe)
             \     x5C  REVERSE SLANT (REVERSE SOLIDUS)(backslash, backslant)
             :     x3A  COLON
             '     x27  APOSTROPHE, RIGHT SINGLE QUOTATION MARK, ACUTE ACCENT (single quote)
             "     x22  QUOTATION MARK, DIAERESIS
             /     x2F  SLANT (SOLIDUS), (slash)
        """

        if self.ERROR_URL is None:
            raise AttributeError('ERROR_URL not set.')

        if self.RESPONSE_URL is None:
            raise AttributeError('RESPONSE_URL not set.')

        params = dict()
        params['id'] = self._gw['id']
        params['password'] = self._gw['password']
        params['action'] = self._action

        params['amt'] = amount
        params['currencycode'] = currency
        params['langid'] = lang
        params['errorURL'] = self.ERROR_URL
        params['responseURL'] = self.RESPONSE_URL
        params['trackid'] = trackid

        if udf is not None:
            keys = udf.keys()
            if filter_:
                s = "~`!#$%^|\:'\"/"
                trans = string.maketrans(s, ''.join(['-'] * len(s)))
                for k in keys:
                    params[k.lower()] = udf[k].translate(trans)
            else:
                for k in keys:
                    params[k.lower()] = udf[k]

        try:
            r = self.connect(params)
        except KeyError:
            return False
        try:
            if r[0][1:6] == 'ERROR':
                raise Exception(GatewayError)
        except KeyError:
            raise Exception(GatewayError)

        return r
