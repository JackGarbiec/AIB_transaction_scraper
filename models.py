from sqlalchemy import Column, Integer, String, Date, Float, Boolean
from database import Base
import datetime

class Transaction(Base):
    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True)
    type = Column(String(50))
    payee = Column(String(120))
    amount = Column(Float)
    debit = Column(Boolean)
    date = Column(Date)
    created = Column(Date, default=datetime.datetime.now)
    synced = Column(Boolean, default=False)

    def __init__(self, payee_string, amount, debit, date):
        self.amount = amount
        self.debit = debit
        self.date = date

        if '-' in payee_string:
            self.type = payee_string.split('-')[0]
            self.payee = payee_string.split('-')[1]
        else:
            self.type = payee_string.split(' ')[0]
            self.payee = ' '.join([s for s in payee_string.split(' ')[1:]])


    def as_dict(self):
        return dict(type=self.type, payee=self.payee, amount=self.amount, debit=self.debit, date=self.date)