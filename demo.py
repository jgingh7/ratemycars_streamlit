import pandas as pd
import psycopg2
import streamlit as st
from statistics import mean
from configparser import ConfigParser
from streamlit import caching

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


@st.cache
def insert_db(sql: str):
    # print(f'Running query_db(): {sql}')

    db_info = get_config()

    # Connect to an existing database
    conn = psycopg2.connect(**db_info)

    # Open a cursor to perform database operations
    cur = conn.cursor()

    # Execute a command: this creates a new table
    cur.execute(sql)

    # Make the changes to the database persistent
    conn.commit()

    # Close communication with the database
    cur.close()
    conn.close()

    # Clear cache after every submission to refresh the db
    caching.clear_cache()
    return


'## Read main entity tables'

name_mapping = {'Cars': 'Cars_made_from_come_with', 'Car Manufacturers': 'Car_manufacturers',
                'Tires': 'Tires_made_from', 'Tire Manufacturers': 'Tire_manufacturers', 'Dealers': 'Dealers'}
table_names = ['Cars', 'Car Manufacturers',
               'Tires', 'Tire Manufacturers', 'Dealers']
table_name = st.selectbox('Select a table', table_names)

if table_name:
    sql_table = f'select * from {name_mapping[table_name]};'
    df = query_db(sql_table)
    st.dataframe(df)


'## Add a rating and comment'
# Dropdown for cars list
car_full_info = f"""select C.car_id, C.year, M.name, C.model
                    from Cars_made_from_come_with C, Car_manufacturers M
                    where C.id_manu = M.car_manu_id
                    order by C.car_id"""
c = query_db(car_full_info)
c_id, c_year, c_name, c_model = c['car_id'].tolist(
), c['year'].tolist(), c['name'].tolist(), c['model'].tolist()

car_list = [str(a) + ' : ' + str(b) + ' ' + c + ' ' + d for a,
            b, c, d in zip(c_id, c_year, c_name, c_model)]

selected_car = st.selectbox('Choose a car to review', car_list)

# Dropdown for users list
sql_user_info = 'select user_id, username from Users order by username;'
user_info = query_db(sql_user_info)
user_ids, user_names = user_info['user_id'].tolist(
), user_info['username'].tolist()

user_id_names = [a + ' : ' + str(b) for a, b in zip(user_names, user_ids)]

selected_user = st.selectbox('Select your username and id', user_id_names)

# Add rating/comment
user_rating = st.selectbox('Rate your car', [5, 4, 3, 2, 1])
user_comment = st.text_input('Comments:')

submit_button = st.button('Submit')

if selected_car and selected_user and user_rating and user_comment and submit_button:

    user_id = selected_user.split(' : ')[1].strip()
    car_id = selected_car.split(' : ')[0].strip()

    # serial gets unsynced after data import
    next_id = "select max(rating_id) as max_id from ratings_rate"
    next_val = query_db(next_id)
    next_rating_id = next_val['max_id'].tolist()[0]+1

    sql_add_rc = f"""insert into Ratings_rate (rating_id, num_stars, comment, id_car, id_user) 
                    values ({next_rating_id}, {user_rating}, '{user_comment}', {car_id}, {user_id})"""

    # insert into db and refresh the cache to update
    insert_db(sql_add_rc)

    # show user statistics and previously submitted ratings:
    f'### Your statistics:'
    user_stats = f"""select COUNT(*) as ratings_count, ROUND(AVG(num_stars),1) as avg_rating 
                    from Ratings_rate
                    group by id_user 
                    having id_user ={user_id};"""
    user_stat = query_db(user_stats)
    u_count, u_avg = user_stat['ratings_count'].tolist(
    )[0], user_stat['avg_rating'].tolist()[0]

    f'You have rated a total of {u_count} times. Your average car rating is {u_avg}.'

    f'Your previous ratings:'
    prev_ratings = f"""select Ra.num_stars, Ra.comment, Ca.year, Ca.name, Ca.model, Ra.time_created 
                    from Ratings_rate Ra, 
                        (select C.car_id, C.year, M.name, C.model
                        from Cars_made_from_come_with C, Car_manufacturers M
                        where C.id_manu = M.car_manu_id) Ca
                    where Ra.id_car = Ca.car_id and Ra.id_user = {user_id}
                    order by Ra.time_created desc;"""
    your_prev_ratings = query_db(prev_ratings)
    st.dataframe(your_prev_ratings)


'## Query cars by manufacturer'

sql_manufacturer_names = 'select name from Car_manufacturers order by name asc;'
manufacturer_names = query_db(sql_manufacturer_names)['name'].tolist()
manufacturer_name = st.selectbox(
    'Choose a manufacturer', manufacturer_names, key='manufacturers1')

if manufacturer_name:
    manufacturer_id = f"select car_manu_id from Car_manufacturers where name = '{manufacturer_name}';"
    id_info = query_db(manufacturer_id).loc[0]['car_manu_id']

    f'Cars by {manufacturer_name}:'
    cars_manufacturers_table = f"""select C.year, M.name, C.model 
                                   from Cars_made_from_come_with C, Car_manufacturers M
		                           where C.id_manu = M.car_manu_id and M.car_manu_id = {id_info};"""
    df = query_db(cars_manufacturers_table)
    st.dataframe(df)


# Show the ratings received by a car
'## Query the ratings for the selected car'
sql_car_info = 'select car_id, model, year from cars_made_from_come_with;'
car_info = query_db(sql_car_info)
car_ids, car_models, car_model_years = car_info['car_id'].tolist(
), car_info['model'].tolist(), car_info['year'].tolist()

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
        rating_avg = round(mean(rating_info['num_stars'].tolist()), 2)
        st.write(f'Average rating: {rating_avg}')
        st.dataframe(rating_info)
    else:
        st.write('No ratings exists.')


'## Query cars with at least a certain rating'

ratings_list = [4, 3, 2, 1]
ratings_sel = st.radio('Choose a rating', ratings_list)

if ratings_sel:
    f'cars with a rating of at least {ratings_sel}:'
    cars_above_rating = f"""select Ca.year, Ca.name, Ca.model, Ra.avg_rating
                            from (select C.car_id, C.year, M.name, C.model
                                from Cars_made_from_come_with C, Car_manufacturers M
                                where C.id_manu = M.car_manu_id) Ca,
                                (select R.id_car, ROUND(AVG(R.num_stars),1) as avg_rating
                                from Ratings_rate R
                                group by R.id_car) Ra
                            where Ca.car_id = Ra.id_car and Ra.avg_rating >= {ratings_sel}
                            order by Ra.avg_rating desc"""

    ratings_df = query_db(cars_above_rating)
    st.dataframe(ratings_df)


# For a given manufacturer, list top 3 cars with highest rating, along with the average rating of each car
"## Query top 3 cars with highest rating for the selected car manufacturer, along with the average rating of each car"
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


'## List the lowest rated car for a given manufacturer, along with the average rating of the car'

manufacturer_name2 = st.selectbox(
    'Choose a manufacturer', manufacturer_names, key='manufacturers2')

if manufacturer_name2:
    lowest_rated = f"""select Ca.year, Ca.name, Ca.model, Ra.avg_rating
                        from (select C.car_id, C.year, M.name, C.model
                            from Cars_made_from_come_with C, Car_manufacturers M
                            where C.id_manu = M.car_manu_id) Ca,
                            (select R.id_car, ROUND(AVG(R.num_stars),1) as avg_rating
                            from Ratings_rate R
                            group by R.id_car) Ra
                        where Ca.car_id = Ra.id_car and Ca.name = '{manufacturer_name2}'
                        order by Ra.avg_rating asc
                        limit 1;"""

    lowest_rate = query_db(lowest_rated).loc[0]
    lr_year, lr_name, lr_model, lr_avg_rating = lowest_rate['year'], lowest_rate[
        'name'], lowest_rate['model'], lowest_rate['avg_rating']
    st.write(
        f"The lowest rated car for {manufacturer_name2} is the {lr_year} {lr_name} {lr_model} with an average rating of {lr_avg_rating}")


# Query for cars with certain tires
'## Query cars with selected tires'
sql_tire_info = 'select tire_id, model from tires_made_from;'
tire_info = query_db(sql_tire_info)
tire_ids, tire_models = tire_info['tire_id'].tolist(
), tire_info['model'].tolist()

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


# See cars sold by a specific dealer
'## Query cars sold by selected dealers'
sql_dealer_info = 'select dealer_id, name from dealers;'
dealer_info = query_db(sql_dealer_info)
dealer_ids, dealer_names = dealer_info['dealer_id'].tolist(
), dealer_info['name'].tolist()

dealer_ids_names = [a + ' : ' + str(b)
                    for a, b in zip(dealer_names, dealer_ids)]

selection = st.selectbox('Choose a dealer', dealer_ids_names)
if selection:
    dealer_id = selection.split(':')[1].strip()
    dealer_name = selection.split(':')[0].strip()

    sql_cars = f"""select C.model as car_model, C.year as car_model_year, D.name as dealer_name, D.state as dealer_state, D.city as dealer_city
                    from cars_made_from_come_with C, sell S, dealers D
                    where S.id_car = C.car_id and S.id_dealer = {dealer_id} and D.dealer_id = {dealer_id};"""
    car_models, car_model_years = query_db(sql_cars)['car_model'].tolist(
    ), query_db(sql_cars)['car_model_year'].tolist()

    car_models_years = [a + ', ' + str(b)
                        for a, b in zip(car_models, car_model_years)]
    car_models_years_str = '\n\n'.join(
        [str(elem) for elem in car_models_years])

    st.write(
        f"The below cars are sold by dealer '{dealer_name}' with total of {len(car_models_years)} car(s): \n\n {car_models_years_str}")


'## For a given dealer, list the top 3 rated cars, along with the average rating of each car'

sql_dealer_names = 'select name from Dealers order by name asc;'
dealer_names = query_db(sql_dealer_names)['name'].tolist()
dealer_name = st.selectbox('Choose a dealer', dealer_names, key='dealers')

if dealer_name:
    dealer_top_rated = f"""select DS.name as dealer, Ca.year, Ca.name, Ca.model, Ra.avg_rating
                        from (select D.dealer_id, D.name, S.id_car
                            from Dealers D, Sell S
                            where D.dealer_id = S.id_dealer) DS,
                            (select C.car_id, C.year, M.name, C.model
                            from Cars_made_from_come_with C, Car_manufacturers M
                            where C.id_manu = M.car_manu_id) Ca,
                            (select R.id_car, ROUND(AVG(R.num_stars),1) as avg_rating
                            from Ratings_rate R
                            group by R.id_car) Ra
                        where Ca.car_id = DS.id_car and Ca.car_id = Ra.id_car and DS.name = '{dealer_name}'
                        order by Ra.avg_rating desc
                        limit 3;"""

    dealer_top = query_db(dealer_top_rated)
    st.dataframe(dealer_top)


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

    if len(users) > 1:
        users[-1] = "and " + users[-1]

    users_str = ', '.join([str(elem) for elem in users])
    st.write(
        f"The top 10 users who have rated the most for {selection} are {users_str}.")


'## List the car and tire information of newer cars (released in 2018 or later) with an average car rating of 3 or above'

new_car_tires = f"""select Ca.year, Ca.name, Ca.model, T.tire_manufacturer, T.model as tire_model, T.type, Ra.avg_rating
                    from (select C.id_tire, C.car_id, C.year, M.name, C.model
                        from Cars_made_from_come_with C, Car_manufacturers M
                        where C.id_manu = M.car_manu_id) Ca,
                        (select R.id_car, ROUND(AVG(R.num_stars),1) as avg_rating
                        from Ratings_rate R
                        group by R.id_car
                        having ROUND(AVG(R.num_stars),1) >= 3) Ra,
                        (select Ti.tire_id, Ti.model, Ti.type, TM.name as tire_manufacturer
                        from Tires_made_from Ti, Tire_manufacturers TM
                        where Ti.id_manu = TM.tire_manu_id) T
                    where Ca.car_id = Ra.id_car and Ca.id_tire = T.tire_id and Ca.year >= 2018
                    order by Ca.year desc;"""

car_tires = query_db(new_car_tires)
st.dataframe(car_tires)


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
