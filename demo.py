import pandas as pd
import psycopg2
import streamlit as st
from configparser import ConfigParser

'# Demo: Streamlit + Postgres'


@st.cache
def get_config(filename='database.ini', section='postgresql'):
    parser = ConfigParser()
    parser.read(filename)
    return {k: v for k, v in parser.items(section)}


@st.cache
def query_db(sql: str):
    # print(f'Running query_db(): {sql}')

    db_info = get_config()

    # Connect to an existing database
    conn = psycopg2.connect(**db_info)

    # Open a cursor to perform database operations
    cur = conn.cursor()

    # Execute a command: this creates a new table
    cur.execute(sql)

    # Obtain data
    data = cur.fetchall()

    column_names = [desc[0] for desc in cur.description]

    # Make the changes to the database persistent
    conn.commit()

    # Close communication with the database
    cur.close()
    conn.close()

    df = pd.DataFrame(data=data, columns=column_names)

    return df


'## Read tables'

sql_all_table_names = "select relname from pg_class where relkind='r' and relname !~ '^(pg_|sql_)';"
all_table_names = query_db(sql_all_table_names)['relname'].tolist()
table_name = st.selectbox('Choose a table', all_table_names)
if table_name:
    f'Display the table'

    sql_table = f'select * from {table_name};'
    df = query_db(sql_table)
    st.dataframe(df)

# Query for cars with certain tires
'## Query for cars with tires'

sql_tire_info = 'select tire_id, model from tires_made_from;'
tire_info = query_db(sql_tire_info)
tire_ids, tire_models = tire_info['tire_id'].tolist(), tire_info['model'].tolist()

tire_ids_names = [a + ' : ' + str(b) for a, b in zip(tire_models, tire_ids)]

selection = st.selectbox(
    'Choose a tire (Tire Model: Tire ID) to look for cars that use the selected tire.', tire_ids_names)
if selection:
    tire_id = selection.split(':')[1].strip()

    sql_cars = f"""select C.model, C.year, T.model, T.type, T.size
                    from cars_made_from_come_with C, tires_made_from T
                    where id_tire={tire_id} and tire_id={tire_id};"""
    car_info = query_db(sql_cars)
    if not car_info.empty:
        st.dataframe(car_info)
    else:
        st.write('No cars.')


# Query for tires with the highest car ratings
# select T.tire_id, T.model, round(avg(R.num_stars),2) AS average_star_rating from ratings_rate R, cars_made_from_come_with C, tires_made_from T where C.id_tire=T.tire_id and R.id_car=C.car_id group
#  by T.tire_id order by average_star_rating desc;
'## Query for tires with the highest car ratings'


# '## Query customers'

# sql_customer_names = 'select name from customers;'
# customer_names = query_db(sql_customer_names)['name'].tolist()
# customer_name = st.selectbox('Choose a customer', customer_names)
# if customer_name:
#     sql_customer = f"select * from customers where name = '{customer_name}';"
#     customer_info = query_db(sql_customer).loc[0]
#     c_age, c_city, c_state = customer_info['age'], customer_info['city'], customer_info['state']
#     st.write(f"{customer_name} is {c_age}-year old, and lives in {customer_info['city']}, {customer_info['state']}.")

# '## Query orders'

# sql_order_ids = 'select order_id from orders;'
# order_ids = query_db(sql_order_ids)['order_id'].tolist()
# order_id = st.selectbox('Choose an order', order_ids)
# if order_id:
#     sql_order = f"""select C.name, O.order_date
#                     from orders as O, customers as C
#                     where O.order_id = {order_id}
#                     and O.customer_id = C.id;"""
#     customer_info = query_db(sql_order).loc[0]
#     customer_name = customer_info['name']
#     order_date = customer_info['order_date']
#     st.write(f'This order is placed by {customer_name} on {order_date}.')

# '## List the customers by city'

# sql_cities = 'select distinct city from customers;'
# cities=query_db(sql_cities)['city'].tolist()
# city_sel = st.radio('Choose a city', cities) #radio button

# if city_sel:
#     sql_customers = f"select name from customers where city = '{city_sel}' order by name;"
#     customer_names = query_db(sql_customers)['name'].tolist()
#     customer_names_str = '\n\n'.join([str(elem) for elem in customer_names])
#     st.write(f"The below customers live in the city '{city_sel}'\n\n {customer_names_str}")

# '## List the orders by customers'
# sql_customers_info = 'select id, name from customers;'
# cust_info = query_db(sql_customers_info)
# cust_ids, cust_names = cust_info['id'].tolist(), cust_info['name'].tolist()

# cust_id_names = [a + ' : ' + str(b) for a, b in zip(cust_names, cust_ids)]

# customer_name = st.multiselect('Choose customers (Customer Name: Customer ID) to look for their orders.', cust_id_names)
# if customer_name:
#     customer_id = [a.split(':')[1].strip() for a in customer_name]
#     customer_id_str = ','.join([str(elem) for elem in customer_id])

#     sql_orders = f"""select C.name, O.order_id, O.order_date, O.order_amount
#                     from orders as O, customers as C
#                     where O.customer_id in ({customer_id_str})
#                     and O.customer_id = C.id;"""
#     df_orders_info = query_db(sql_orders)
#     if (not df_orders_info.empty):
#         st.dataframe(df_orders_info)
#     else:
#         st.write('No orders.')
