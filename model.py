from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Float
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Customer(Base):
    __tablename__ = 'customer'
    id = Column(Integer, primary_key=True)
    f_name = Column(String(255))
    l_name = Column(String(255))
    email = Column(String(255))
    orders = relationship('Order', back_populates='customer')

class Order(Base):
    __tablename__ = 'order_'
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customer.id'))
    date_ = Column(String(255))
    status_id = Column(Integer, ForeignKey('status.id'))
    customer = relationship('Customer', back_populates='orders')
    status = relationship('Status', back_populates='orders')
    product_orders = relationship('ProductOrder', back_populates='order')

class Status(Base):
    __tablename__ = 'status'
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    orders = relationship('Order', back_populates='status')

class Product(Base):
    __tablename__ = 'product'
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    price = Column(Float)
    product_orders = relationship('ProductOrder', back_populates='product')

class ProductOrder(Base):
    __tablename__ = 'product_order'
    order_id = Column(Integer, ForeignKey('order_.id'), primary_key=True)
    product_id = Column(Integer, ForeignKey('product.id'), primary_key=True)
    quantity = Column(Integer)
    order = relationship('Order', back_populates='product_orders')
    product = relationship('Product', back_populates='product_orders')

engine = create_engine('sqlite:///duomenu_baze.db')
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

initial_status_names = ['Nepatvirtintas', 'Patvirtintas', 'Įvykdytas', 'Atmestas']

existing_statuses = session.query(Status).filter(Status.name.in_(initial_status_names)).all()
missing_statuses = [status_name for status_name in initial_status_names if status_name not in [status.name for status in existing_statuses]]

if missing_statuses:
    for status_name in missing_statuses:
        new_status = Status(name=status_name)
        session.add(new_status)
    session.commit()
else:
    print("Visi pradiniai status įrašai jau yra duomenų bazėje.")

