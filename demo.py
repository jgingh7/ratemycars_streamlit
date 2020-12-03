import pandas as pd
import psycopg2
import streamlit as st
from configparser import ConfigParser

'# RateMyCar'


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


# Query for cars with certain tires
'## Query cars with selected tires'
sql_tire_info = 'select tire_id, model from tires_made_from;'
tire_info = query_db(sql_tire_info)
tire_ids, tire_models = tire_info['tire_id'].tolist(), tire_info['model'].tolist()

tire_ids_models = [a + ' : ' + str(b) for a, b in zip(tire_models, tire_ids)]

selection = st.multiselect(
    'Choose tires (Tire Model: Tire ID) to look for cars that use the selected tire.', tire_ids_models)
if selection:
    tire_id = [a.split(':')[1].strip() for a in selection]
    tire_id_str = ','.join([str(elem) for elem in tire_id])

    sql_cars = f"""select C.model as "car model", C.year as "car model year", T.model as "tire model", T.type as "tire type", T.size as "tire size"
                    from cars_made_from_come_with C, tires_made_from T
                    where C.id_tire in ({tire_id_str}) and T.tire_id in ({tire_id_str}) order by T.tire_id;"""
    car_info = query_db(sql_cars)
    if not car_info.empty:
        st.dataframe(car_info)
    else:
        st.write('No cars with selected tires.')


# Query for tires with the highest car ratings
'## Top 10 tires with the highest car ratings'
sql_top_rate_tire = f"""select T.model, round(avg(R.num_stars),2) as "average rating"
                        from ratings_rate R, cars_made_from_come_with C, tires_made_from T
                        where C.id_tire=T.tire_id and R.id_car=C.car_id group by T.tire_id order by "average rating" desc limit 10;"""
top_rate_tire_info = query_db(sql_top_rate_tire)
if not top_rate_tire_info.empty:
    st.dataframe(top_rate_tire_info)
else:
    st.write('No cars or no tires.')

# See cars sold by a specific dealer
'## Query cars sold by selected dealers'
sql_dealer_info = 'select dealer_id, name from dealers;'
dealer_info = query_db(sql_dealer_info)
dealer_ids, dealer_names = dealer_info['dealer_id'].tolist(), dealer_info['name'].tolist()

dealer_ids_names = [a + ' : ' + str(b)
                    for a, b in zip(dealer_names, dealer_ids)]

selection = st.selectbox('Choose a dealer', dealer_ids_names)
if selection:
    dealer_id = selection.split(':')[1].strip()
    dealer_name = selection.split(':')[0].strip()

    sql_cars = f"""select C.model as car_model, C.year as car_model_year, D.name as dealer_name, D.state as dealer_state, D.city as dealer_city
                    from cars_made_from_come_with C, sell S, dealers D
                    where S.id_car = C.car_id and S.id_dealer = {dealer_id} and D.dealer_id = {dealer_id};"""
    car_models, car_model_years = query_db(sql_cars)['car_model'].tolist(), query_db(sql_cars)['car_model_year'].tolist()

    car_models_years = [a + ', ' + str(b)
                        for a, b in zip(car_models, car_model_years)]
    car_models_years_str = '\n\n'.join(
        [str(elem) for elem in car_models_years])

    st.write(
        f"The below cars are sold by dealer '{dealer_name}'\n\n {car_models_years_str}")
#TOTAL HOW MANY CARS?

# Show the ratings received by a car
'## Query the ratings for the selected car'
sql_car_info = 'select car_id, model, year from cars_made_from_come_with;'
car_info = query_db(sql_car_info)
car_ids, car_models, car_model_years = car_info['car_id'].tolist(), car_info['model'].tolist(), car_info['year'].tolist()

car_models_years = [a + ', ' + str(b)
                        for a, b in zip(car_models, car_model_years)]
car_ids_models = [a + ' : ' + str(b)
                    for a, b in zip(car_models_years, car_ids)]

selection = st.selectbox('Choose a car', car_ids_models)
if selection:
    car_id = selection.split(':')[1].strip()
    sql_ratings = f"""select R.num_stars, R.comment, R.time_created
                        from cars_made_from_come_with C, ratings_rate R
                        where C.car_id = {car_id} and R.id_car = {car_id};"""
    rating_info = query_db(sql_ratings)
    if not rating_info.empty:
        st.dataframe(rating_info)
    else:
        st.write('No ratings exists.')
#WHAT IS THE AVERAGE RATING?


# For a given manufacturer, list top 3 cars with highest rating, along with the average rating of each car
# 
"## Query top 3 cars with highest rating, along with the average rating of each car"
sql_manu_name_info = 'select name from car_manufacturers;'
manu_name_info = query_db(sql_manu_name_info)
manu_names = manu_name_info['name'].tolist()

selection = st.selectbox('Choose a car manufacturer', manu_names)
if selection:
    sql_top_cars = f"""select C.model, round(avg(R.num_stars),2) as "average rating"
                    from cars_made_from_come_with C, ratings_rate R, car_manufacturers CM
                    where C.car_id = R.id_car and C.id_manu = CM.car_manu_id and CM.name = '{selection}'
                    group by C.car_id order by "average rating" desc limit 3;"""
    top_cars_info = query_db(sql_top_cars)
    if not top_cars_info.empty:
        st.dataframe(top_cars_info)
    else:
        st.write('No corresponding cars.')


# List top 5 tire manufacturers with highest rated cars on average
'## Top 5 tire manufacturers with highest rated cars on average'
sql_top_rate_tire_manu = f"""select TM.name, round(avg(R.num_stars),2) as "average rating"
                                from tire_manufacturers TM, tires_made_from T, cars_made_from_come_with C, ratings_rate R
                                where TM.tire_manu_id = T.id_manu and T.tire_id = C.id_tire and R.id_car = C.car_id group by TM.tire_manu_id
                                order by "average rating" desc limit 5;"""
top_rate_tire_manu_info = query_db(sql_top_rate_tire_manu)
if not top_rate_tire_manu_info.empty:
    st.dataframe(top_rate_tire_manu_info)
else:
    st.write('No corresponding tire manufacturer.')

# List top 10 users who have rated the most for selected country's cars
"## Query top 10 users who have rated the most for selected country's cars"
sql_manu_country_info = 'select hq_country from car_manufacturers group by hq_country;'
manu_country_info = query_db(sql_manu_country_info)
manu_countries = manu_country_info['hq_country'].tolist()

selection = st.selectbox('Choose a country', manu_countries)
if selection:
    sql_users = f"""select U.username, count(*) as "rating counts"
                        from cars_made_from_come_with C, car_manufacturers CM, ratings_rate R, Users U
                        where C.id_manu = CM.car_manu_id and R.id_car = C.car_id and R.id_user=U.user_id and CM.HQ_country='{selection}'
                        group by U.user_id order by "rating counts" desc limit 10;"""
    users = query_db(sql_users)['username'].tolist()
    users[-1] = "and " + users[-1]
    users_str = ', '.join([str(elem) for elem in users])
    st.write(f"The top 10 users who have rated the most for {selection} are {users_str}.")