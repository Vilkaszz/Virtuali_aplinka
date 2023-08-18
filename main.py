import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from model import Base, Customer, Order, Product, ProductOrder, Status
from datetime import datetime

engine = create_engine('sqlite:///duomenu_baze.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Duomenų Bazės Aplikacija")
        self.root.geometry("800x600")

        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        self.add_customer_button = tk.Button(main_frame, text="Pridėti vartotoją", command=self.add_customer)
        self.add_customer_button.pack(fill=tk.X, padx=10, pady=5)

        self.add_product_button = tk.Button(main_frame, text="Naujas produktas", command=self.add_product)
        self.add_product_button.pack(fill=tk.X, padx=10, pady=5)

        self.add_order_button = tk.Button(main_frame, text="Naujas užsakymas", command=self.add_order_window)
        self.add_order_button.pack(fill=tk.X, padx=10, pady=5)

        self.view_data_button = tk.Button(main_frame, text="Peržiūrėti duomenis", command=self.open_data_window)
        self.view_data_button.pack(fill=tk.X, padx=10, pady=5)

        main_frame.columnconfigure(0, weight=1)

    def open_data_window(self):
        if hasattr(self, 'data_window'):
            self.data_window.destroy()
        data_window = tk.Toplevel(self.root)
        data_window.title("Duomenų Lentelės")
        self.data_window = data_window

        self.view_table_var = tk.StringVar()
        self.view_table_var.set("Pasirinkite lentelę")
        tables = ["Vartotojai", "Produktai", "Užsakymai"]
        self.view_table_dropdown = tk.OptionMenu(data_window, self.view_table_var, *tables)
        self.view_table_dropdown.pack()

        self.view_table_button = tk.Button(data_window, text="Rodyti", command=self.show_selected_table)
        self.view_table_button.pack()

        self.selected_table = None
        self.tree = None
        self.edit_button = None
        self.delete_button = None
        self.selected_item = None

    def show_selected_table(self):
        selected_table = self.view_table_var.get()
        if selected_table == "Vartotojai":
            self.view_customers()
        elif selected_table == "Produktai":
            self.view_products()
        elif selected_table == "Užsakymai":
            self.view_orders()

    def view_customers(self):
        self.selected_table = "Vartotojai"
        data_window = self.create_data_window("Vartotojai")
        columns = ("Vardas", "Pavardė", "El. paštas")
        customers = self.get_customers()
        data = [(customer.f_name, customer.l_name, customer.email) for customer in customers]
        self.create_table(data_window, columns, data)

    def view_products(self):
        self.selected_table = "Produktai"
        data_window = self.create_data_window("Produktai")
        columns = ("Pavadinimas", "Kaina")
        products = self.get_products()
        data = [(product.name, product.price) for product in products]
        self.create_table(data_window, columns, data)

    def view_orders(self):
        self.selected_table = "Užsakymai"
        data_window = self.create_data_window("Užsakymai")
        columns = ("Vartotojas", "Data", "Produktas", "Kiekis", "Statusas", "Vieneto Kaina", "Suma")
        orders = self.get_orders()
        data = []
        for order in orders:
            customer_name = f"{order.customer.f_name} {order.customer.l_name}"
            product_name = order.product_orders[0].product.name if order.product_orders else ""
            quantity = order.product_orders[0].quantity if order.product_orders else 0
            status = order.status.name
            unit_price = order.product_orders[0].product.price if order.product_orders else 0
            total_price = unit_price * quantity
            data.append((customer_name, order.date_, product_name, quantity, status, unit_price, total_price))
        self.create_table(data_window, columns, data)

    def create_data_window(self, title):
        data_window = tk.Toplevel(self.root)
        data_window.title(title)

        self.edit_button = tk.Button(data_window, text="Redaguoti", state=tk.DISABLED, command=self.edit_selected)
        self.edit_button.pack()

        self.delete_button = tk.Button(data_window, text="Šalinti", state=tk.DISABLED, command=self.delete_selected)
        self.delete_button.pack()

        return data_window

    def create_table(self, parent, columns, data):
        self.tree = ttk.Treeview(parent, columns=columns, show="headings")
        self.tree.pack()

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)

        for item in data:
            self.tree.insert("", "end", values=item)

        self.tree.bind("<ButtonRelease-1>", lambda event: self.on_table_click(event, self.tree))

    def edit_selected(self):
        if self.selected_item:
            item_data = self.tree.item(self.selected_item, "values")
            print("Redaguojamas elementas:", item_data)
            if self.selected_table == "Vartotojai":
                self.edit_customer(item_data)
            elif self.selected_table == "Produktai":
                self.edit_product(item_data)
            elif self.selected_table == "Užsakymai":
                self.edit_order(item_data)

    def is_data_used_in_orders(self, table_name, item_data):
        if table_name == "Vartotojai":
            f_name, l_name, _ = item_data
            customer = session.query(Customer).filter_by(f_name=f_name, l_name=l_name).first()
            if customer:
                orders = session.query(Order).filter_by(customer_id=customer.id).all()
                if orders:
                    return True
        elif table_name == "Produktai":
            name, _ = item_data
            product = session.query(Product).filter_by(name=name).first()
            if product:
                orders = session.query(Order).join(ProductOrder).filter(ProductOrder.product == product).all()
                if orders:
                    return True
        return False

    def ask_confirmation(self, message, warning):
        result = messagebox.askquestion("Patvirtinimas", f"{message}\n{warning}", icon='warning')
        return result == 'yes'

    def delete_item_with_confirmation(self, table_name, item_data):
        used_in_orders = self.is_data_used_in_orders(table_name, item_data)
        if used_in_orders:
            confirm = messagebox.askquestion("Šalinti duomenis",
                                             "Šie duomenys yra naudojami užsakyme. Ar tikrai norite juos ištrinti?",
                                             icon="warning")
            if confirm != "yes":
                return
        if table_name == "Vartotojai":
            self.delete_customer(item_data)
        elif table_name == "Produktai":
            self.delete_product(item_data)

    def delete_selected(self):
        if self.selected_item:
            item_data = self.tree.item(self.selected_item, "values")
            print("Ištrinamas elementas:", item_data)
            if self.selected_table == "Vartotojai":
                self.delete_item_with_confirmation("Vartotojai", item_data)
            elif self.selected_table == "Produktai":
                self.delete_item_with_confirmation("Produktai", item_data)
            elif self.selected_table == "Užsakymai":
                self.delete_order(item_data)
    def refresh_table(self):
        if self.tree is not None:
            for item in self.tree.get_children():
                self.tree.delete(item)

        if self.selected_table == "Vartotojai":
            self.view_customers()
        elif self.selected_table == "Produktai":
            self.view_products()
        elif self.selected_table == "Užsakymai":
            self.view_orders()

    def delete_customer(self, item_data):
        username = item_data[0]
        user = session.query(Customer).filter_by(username=username).first()
        if user:
            orders = session.query(Order).filter_by(user=user).all()
            for order in orders:
                for product_order in order.product_orders:
                    if product_order.product == self.selected_item[0]:
                        if self.ask_confirmation(f"Ar norite ištrinti užsakymą {order.id}?",
                                                 "Šis užsakymas naudoja šį produktą."):
                            self.delete_order(order)
                        break

            session.delete(user)
            session.commit()
            self.update_table("Vartotojai")

    def delete_product(self, item_data):
        name, _ = item_data
        product = session.query(Product).filter_by(name=name).first()
        if product:
            orders = session.query(Order).join(ProductOrder).filter(ProductOrder.product == product).all()
            for order in orders:
                if self.ask_confirmation(f"Ar norite ištrinti užsakymą {order.id}?",
                                         "Šis užsakymas naudoja šį produktą."):
                    self.delete_order(order)

            session.delete(product)
            session.commit()
            self.refresh_table()

    def delete_order(self, item_data):
        customer_name, date_, product_name, quantity, status, unit_price, _ = item_data

        f_name, l_name = customer_name.split()
        customer = session.query(Customer).filter_by(f_name=f_name, l_name=l_name).first()

        if customer:
            order = session.query(Order).filter_by(customer=customer, date_=date_).first()
            if order:
                try:
                    for product_order in order.product_orders:
                        session.delete(product_order)
                    session.delete(order)
                    session.commit()
                    print("Užsakymas ištrintas!")
                    self.refresh_table()
                except Exception as e:
                    print("Klaida trinant užsakymą:", e)
                    session.rollback()
            else:
                print("Klaida: Užsakymas nerastas.")
        else:
            print("Klaida: Vartotojas nerastas.")
    def edit_customer(self, item_data):
        f_name, l_name, email = item_data
        new_f_name = simpledialog.askstring("Redaguoti", "Naujas vardas:", initialvalue=f_name)
        new_l_name = simpledialog.askstring("Redaguoti", "Nauja pavardė:", initialvalue=l_name)
        new_email = simpledialog.askstring("Redaguoti", "Naujas el. paštas:", initialvalue=email)

        if new_f_name and new_l_name and new_email:
            customer = session.query(Customer).filter_by(f_name=f_name, l_name=l_name, email=email).first()
            if customer:
                customer.f_name = new_f_name
                customer.l_name = new_l_name
                customer.email = new_email
                session.commit()
                print("Vartotojas atnaujintas!")
                self.refresh_table()

    def edit_product(self, item_data):
        name, price = item_data
        new_name = simpledialog.askstring("Redaguoti", "Naujas pavadinimas:", initialvalue=name)
        new_price = simpledialog.askfloat("Redaguoti", "Nauja kaina:", initialvalue=float(price))

        if new_name and new_price:
            product = session.query(Product).filter_by(name=name, price=float(price)).first()
            if product:
                product.name = new_name
                product.price = new_price
                session.commit()
                print("Produktas atnaujintas!")
                self.refresh_table()

    def edit_order(self, item_data):
        customer_name, date_, product_name, quantity, status, unit_price, _ = item_data

        customer_names = [f"{customer.f_name} {customer.l_name}" for customer in self.get_customers()]
        product_names = [product.name for product in self.get_products()]
        status_names = self.get_statuses_with_names()

        edit_window = tk.Toplevel()
        edit_window.title("Redaguoti užsakymą")

        tk.Label(edit_window, text="Vartotojas:").pack()
        self.customer_var = tk.StringVar()
        self.customer_var.set(customer_name)
        self.customer_dropdown = tk.OptionMenu(edit_window, self.customer_var, *customer_names)
        self.customer_dropdown.pack()

        tk.Label(edit_window, text="Produktas:").pack()
        self.product_var = tk.StringVar()
        self.product_var.set(product_name)
        self.product_dropdown = tk.OptionMenu(edit_window, self.product_var, *product_names)
        self.product_dropdown.pack()

        tk.Label(edit_window, text="Vieneto Kaina:").pack()
        self.unit_price_entry = tk.Entry(edit_window)
        self.unit_price_entry.insert(0, unit_price)
        self.unit_price_entry.pack()

        tk.Label(edit_window, text="Kiekis:").pack()
        self.quantity_entry = tk.Entry(edit_window)
        self.quantity_entry.insert(0, quantity)
        self.quantity_entry.pack()

        tk.Label(edit_window, text="Statusas:").pack()
        self.status_var = tk.StringVar()
        self.status_var.set(status)
        self.status_dropdown = tk.OptionMenu(edit_window, self.status_var, *status_names)
        self.status_dropdown.pack()

        tk.Button(edit_window, text="Atnaujinti", command=lambda: self.update_order(item_data)).pack()

    def update_order(self, original_item_data):
        customer_name = self.customer_var.get()
        product_name = self.product_var.get()
        unit_price = float(self.unit_price_entry.get())
        quantity = int(self.quantity_entry.get())
        status = self.status_var.get()

        f_name, l_name = customer_name.split()
        customer = session.query(Customer).filter_by(f_name=f_name, l_name=l_name).first()
        product = session.query(Product).filter_by(name=product_name).first()
        status_db = session.query(Status).filter_by(name=status).first()

        if customer and product and status_db:
            order = session.query(Order).filter_by(customer=customer, date_=original_item_data[1]).first()
            if order:
                product_order = order.product_orders[0]
                product_order.product = product
                product_order.quantity = quantity
                product.price = unit_price
                order.status = status_db

                session.commit()
                print("Užsakymas atnaujintas!")
                self.refresh_table()
            else:
                print("Klaida: Užsakymas nerastas.")
        else:
            print("Klaida: Neteisingai įvesti duomenys.")
    def on_table_click(self, event, tree):
        self.selected_item = tree.selection()[0]
        self.edit_button.config(state=tk.NORMAL)
        self.delete_button.config(state=tk.NORMAL)
    def get_orders(self):
        orders = session.query(Order).all()
        return orders

    def get_customers(self):
        customers = session.query(Customer).all()
        return customers

    def get_products(self):
        products = session.query(Product).all()
        return products

    def get_statuses(self):
        statuses = session.query(Status).all()
        return [status.name for status in statuses]

    def add_customer(self):
        top = tk.Toplevel(self.root)
        top.title("Pridėti vartotoją")

        tk.Label(top, text="Vardas:").pack()
        self.f_name_entry = tk.Entry(top)
        self.f_name_entry.pack()

        tk.Label(top, text="Pavardė:").pack()
        self.l_name_entry = tk.Entry(top)
        self.l_name_entry.pack()

        tk.Label(top, text="El. paštas:").pack()
        self.email_entry = tk.Entry(top)
        self.email_entry.pack()

        tk.Button(top, text="Pridėti", command=self.save_customer).pack()

    def save_customer(self):
        f_name = self.f_name_entry.get()
        l_name = self.l_name_entry.get()
        email = self.email_entry.get()

        new_customer = Customer(f_name=f_name, l_name=l_name, email=email)
        session.add(new_customer)
        session.commit()
        print("Vartotojas pridėtas!")

    def add_product(self):
        top = tk.Toplevel(self.root)
        top.title("Pridėti produktą")

        tk.Label(top, text="Pavadinimas:").pack()
        self.name_entry = tk.Entry(top)
        self.name_entry.pack()

        tk.Label(top, text="Kaina:").pack()
        self.price_entry = tk.Entry(top)
        self.price_entry.pack()

        tk.Button(top, text="Pridėti", command=self.save_product).pack()

    def save_product(self):
        name = self.name_entry.get()
        price = float(self.price_entry.get())

        new_product = Product(name=name, price=price)
        session.add(new_product)
        session.commit()
        print("Produktas pridėtas!")

    def set_default_date(self):
        today = datetime.today().strftime("%Y-%m-%d")
        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, today)

    def add_order_window(self):
        top = tk.Toplevel()
        top.title("Pridėti užsakymą")

        tk.Label(top, text="Pasirinkite vartotoją:").pack()

        self.customer_var = tk.StringVar()
        self.customer_var.set("Pasirinkite vartotoją")
        customers = self.get_customers()
        customer_names = [f"{customer.f_name} {customer.l_name}" for customer in customers]
        customer_names.insert(0, "Pasirinkite vartotoją")
        self.customer_dropdown = tk.OptionMenu(top, self.customer_var, *customer_names)
        self.customer_dropdown.pack()

        tk.Label(top, text="Pasirinkite produktą:").pack()

        self.product_var = tk.StringVar()
        self.product_var.set("Pasirinkite produktą")
        products = self.get_products_with_names_and_prices()
        products.insert(0, "Pasirinkite produktą")
        self.product_dropdown = tk.OptionMenu(top, self.product_var, *products)
        self.product_dropdown.pack()

        tk.Label(top, text="Kiekis:").pack()
        self.quantity_entry = tk.Entry(top)
        self.quantity_entry.pack()

        tk.Label(top, text="Data (YYYY-MM-DD):").pack()
        self.date_entry = tk.Entry(top)
        self.date_entry.pack()

        self.set_default_date()
        tk.Button(top, text="Nustatyti šiandienos datą", command=self.set_default_date).pack()

        tk.Label(top, text="Pasirinkite statusą:").pack()

        self.status_var = tk.StringVar()
        self.status_var.set("Pasirinkite statusą")
        status_names = self.get_statuses_with_names()
        self.status_dropdown = tk.OptionMenu(top, self.status_var, *status_names)
        self.status_dropdown.pack()

        tk.Button(top, text="Pridėti", command=self.save_order).pack()
    def get_statuses_with_names(self):
        statuses = session.query(Status).all()
        return [status.name for status in statuses]

    def get_products_with_names_and_prices(self):
        products = session.query(Product).all()
        return [f"{product.name} - {product.price}" for product in products]

    def save_order(self):
        selected_customer = self.customer_var.get()
        selected_product_info = self.product_var.get()
        selected_status = self.status_var.get()
        quantity = self.quantity_entry.get()
        date_str = self.date_entry.get()

        if not selected_customer or selected_customer == "Pasirinkite vartotoją":
            print("Klaida: Pasirinkite vartotoją.")
            return

        if not selected_product_info or selected_product_info == "Pasirinkite produktą":
            print("Klaida: Pasirinkite produktą.")
            return

        if selected_status == "Pasirinkite statusą":
            print("Klaida: Pasirinkite statusą.")
            return

        if selected_status not in self.get_statuses_with_names():
            print("Klaida: Pasirinktas neteisingas statusas.")
            return

        try:
            quantity = int(quantity)
        except ValueError:
            print("Klaida: Neteisingai įvestas kiekis.")
            return

        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            date_formatted = date_obj.strftime("%Y-%m-%d")
        except ValueError:
            print("Klaida: Neteisingai įvestas datos formatas. Teisingas formatas: YYYY-MM-DD")
            return

        customer_name_parts = selected_customer.split()
        selected_customer_f_name = customer_name_parts[0]
        selected_customer_l_name = customer_name_parts[1]

        selected_product_name, selected_product_price = selected_product_info.split(" - ")

        status = session.query(Status).filter_by(name=selected_status).first()
        if not status:
            print("Klaida: Pasirinktas neteisingas statusas.")
            return

        product = session.query(Product).filter_by(name=selected_product_name,
                                                   price=float(selected_product_price)).first()
        if not product:
            print("Klaida: Pasirinkite teisingą produktą ir kainą.")
            return

        customer = session.query(Customer).filter_by(f_name=selected_customer_f_name,
                                                     l_name=selected_customer_l_name).first()

        if not customer:
            print("Klaida: Pasirinktas vartotojas nerastas.")
            return

        new_product_order = ProductOrder(product=product, quantity=quantity)

        order = Order(customer=customer, date_=date_formatted, status=status, product_orders=[new_product_order])
        session.add(order)
        session.commit()

        print("Užsakymas pridėtas!")


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()