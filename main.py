#encoding: UTF-8
"""
A sample e24PaymentPipe client for KNET. Use this as inspiration
(or directly in your code) when you need to provide a KNET payment
gateway for your application.

It has minimal requirements and is written in Flask using SQLAlchemy
as the database ORM.

"""

from datetime import date
from datetime import datetime
from flask import Flask, request, redirect, render_template, flash
from flask.helpers import url_for
from flaskext.sqlalchemy import SQLAlchemy

from knet.api import e24PaymentPipe as gw

app = Flask(__name__)
app.config.from_pyfile('settings.cfg')

# Setting up a default database to be used for knet specific information
# In production, you should probably change this to point to an existing database

#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///knet.db'
#app.config['SECRET_KEY'] = 'changeme' # change this!
db = SQLAlchemy(app)

# Change these to match your server URLs
# These are required for KNET, but can
# be customized to your needs.

ERROR_URL = app.config['ERROR_URL']
SUCCESS_URL = app.config['SUCCESS_URL']
RESPONSE_URL = app.config['RESPONSE_URL']

knet = gw('resource.cgn',app.config['KNET_ALIAS'])
knet.ERROR_URL = ERROR_URL
knet.RESPONSE_URL = RESPONSE_URL

class Transaction(db.Model):
    __tablename__ = 'KNET_TRANS'
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(50))
    payment_id = db.Column(db.String(50))
    tracking_id = db.Column(db.String(50))
    reference = db.Column(db.String(50), default=None)
    total = db.Column(db.Float, default=0.000)
    result = db.Column(db.String(100))
    postdate = db.Column(db.Date)
    auth = db.Column(db.String(50))
    order_id = db.Column(db.String(50))

    def __init__(self,tracking,order,total=1.000):
        self.tracking_id = tracking
        self.total = total
        self.order_id = order

    def __repr__(self):
        return '<KNET R: {0} | T: {1} | O: {2}>'.format(self.payment_id,self.total,self.order_id)

@app.route('/error/<pid>')
def error(pid=None):
    if pid:
        t = Transaction.query.filter_by(payment_id=pid).first()
        flash('Oops! There was an error with your payment!')
        return render_template('error.html',t=t)
    else:
        return 'There was an error with your request'

@app.route('/thank-you/<pid>')
def thanks(pid):
    # Fetch the object for this payment ID
    if not pid:
       return 'ERROR'
    else:
       t = Transaction.query.filter_by(payment_id=pid).first()

    flash('Your payment was successful')
    return render_template('thanks.html',t=t)

@app.route('/result/',methods=['POST'])
def result():
    # Get the paymentid
    pid = request.form.get('paymentid')

    t = Transaction.query.filter_by(payment_id=pid).first() or None
    if not t:
        return redirect(url_for('error'))

    # We have the transaction, now fill in the rest of the fields

    r = request.form.get('result')

    t.result = r
    t.postdate = date(date.today().year,int(request.form.get('postdate')[:2]),int(request.form.get('postdate')[2:]))
    t.transaction_id = request.form.get('tranid')
    t.tracking_id = request.form.get('trackid')
    t.reference = request.form.get('ref')
    t.auth = request.form.get('auth')

    # Store the result
    db.session.add(t)
    db.session.commit()

    if r == unicode('CANCELLED') or r == unicode('NOT CAPTURED'):
        return 'REDIRECT=%s%s' % (ERROR_URL,pid)

    return 'REDIRECT=%s%s' % (SUCCESS_URL,pid)

@app.route('/<id>/<total>/<trackingid>/<udf>')
@app.route('/<id>/<total>/<trackingid>/')
@app.route('/<id>/<total>/')
def entry(id,trackingid=None,total=1.000,udf=None):

    """
    This is the main entry point for the server, you pass it three things:

    1. The ID of the transaction from your database - this could be a receipt
       number or any other unique identifier.

    2. The amount that needs to be paid. Minimum is 1, which is the default.

    3. A unique tracking ID. This is optional, but highly recommended. KNET
       requires this for their backend. If you don't pass one, the system
       generates one with the following pattern:

       YYYYMMDD-ID-HHMMSS

    5. Optional UDF fields (1-5)

    Example URL:

    /12/34.345/ABC-TRACK/abc,foo@bar.com,hello

    12 = ID
    34.345 = Amount to be charged
    ABC-TRACK = Tracking ID
    abc = UDF field 1
    foo@bar.com = UDF field 2
    hello = UDF field 3

    Restrictions - none of your fields can include the / character
    """
    # - Check if this order has already been paid
    t = Transaction.query.filter_by(order_id=id,result='CAPTURED').first()
    if t is not None:
        return 'You have already paid for this order.'

    # 2 - Build and dispatch KNET URL
    trackid = trackingid or '{0.year}{0.month}{0.day}-{1}-{0.hour}{0.minute}{0.second}'.format(datetime.now(),id)

    knet.parse()
    if udf is not None:
        udf = {'udf%s'%udf.find(x):x for x in udf if x is not ','}
    payment_id,payment_url = knet.transaction(trackid,amount=total,udf=udf)

    # Store information in DB
    t = Transaction(trackid,id,total)
    t.payment_id = payment_id
    db.session.add(t)
    db.session.commit()
    return redirect(payment_url+'?PaymentID='+payment_id)

if __name__ == '__main__':
    db.create_all() # This will reset and recreate the database on each restart of the system
    app.run(debug=True)


