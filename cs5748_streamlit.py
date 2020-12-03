import pandas as pd
import psycopg2
import streamlit as st
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

name_mapping = {'Cars': 'Cars_made_from_come_with', 'Car Manufacturers': 'Car_manufacturers', 'Tires': 'Tires_made_from', 'Tire Manufacturers': 'Tire_manufacturers', 'Dealers':'Dealers'}
table_names = ['Cars', 'Car Manufacturers', 'Tires', 'Tire Manufacturers', 'Dealers']
table_name = st.selectbox('Select a table', table_names)

if table_name:
    sql_table = f'select * from {name_mapping[table_name]};'
    df = query_db(sql_table)
    st.dataframe(df)



'## Query cars by manufacturer'

sql_manufacturer_names = 'select name from Car_manufacturers order by name asc;'
manufacturer_names = query_db(sql_manufacturer_names)['name'].tolist()
manufacturer_name = st.selectbox('Choose a manufacturer', manufacturer_names, key='manufacturers1')

if manufacturer_name:
    manufacturer_id = f"select car_manu_id from Car_manufacturers where name = '{manufacturer_name}';"
    id_info = query_db(manufacturer_id).loc[0]['car_manu_id']

    f'Cars by {manufacturer_name}:'
    cars_manufacturers_table = f"""select C.year, M.name, C.model 
                                   from Cars_made_from_come_with C, Car_manufacturers M
		                           where C.id_manu = M.car_manu_id and M.car_manu_id = {id_info};"""
    df = query_db(cars_manufacturers_table)
    st.dataframe(df)



'## Query for cars with at least a certain rating'

ratings_list = [4,3,2,1]
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



'## List the lowest rated car for a given manufacturer, along with the average rating of the car'

manufacturer_name2 = st.selectbox('Choose a manufacturer', manufacturer_names, key='manufacturers2')

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
    lr_year, lr_name, lr_model, lr_avg_rating = lowest_rate['year'], lowest_rate['name'], lowest_rate['model'], lowest_rate['avg_rating']
    st.write(f"The lowest rated car for {manufacturer_name2} is the {lr_year} {lr_name} {lr_model} with an average rating of {lr_avg_rating}")



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




'## Add a rating and comment'
# Dropdown for cars list
car_full_info = f"""select C.car_id, C.year, M.name, C.model
                    from Cars_made_from_come_with C, Car_manufacturers M
                    where C.id_manu = M.car_manu_id
                    order by C.car_id"""
c = query_db(car_full_info)
c_id, c_year, c_name, c_model = c['car_id'].tolist(), c['year'].tolist(), c['name'].tolist(), c['model'].tolist()

car_list = [str(a) + ' : ' + str(b) + ' ' + c + ' ' + d for a,b,c,d in zip(c_id, c_year, c_name, c_model)]

selected_car = st.selectbox('Choose a car to review', car_list)

# Dropdown for users list
sql_user_info = 'select user_id, username from Users order by username;'
user_info = query_db(sql_user_info)
user_ids, user_names = user_info['user_id'].tolist(), user_info['username'].tolist()

user_id_names = [a + ' : ' + str(b) for a, b in zip(user_names, user_ids)]

selected_user = st.selectbox('Select your username and id', user_id_names)

# Add rating/comment
user_rating = st.selectbox('Rate your car', [5,4,3,2,1])
user_comment = st.text_input('Comments:')

submit_button = st.button('Submit') 

if selected_car and selected_user and user_rating and user_comment and submit_button:

    user_id = selected_user.split(' : ')[1].strip() 
    car_id = selected_car.split(' : ')[0].strip()

    #serial gets unsynced after data import 
    next_id = "select max(rating_id) as max_id from ratings_rate"
    next_val = query_db(next_id)
    next_rating_id = next_val['max_id'].tolist()[0]+1

    sql_add_rc = f"""insert into Ratings_rate (rating_id, num_stars, comment, id_car, id_user) 
                    values ({next_rating_id}, {user_rating}, '{user_comment}', {car_id}, {user_id})"""

    #insert into db and refresh the cache to update
    insert_db(sql_add_rc)

    # show user statistics and previously submitted ratings:
    f'### Your statistics:'
    user_stats = f"""select COUNT(*) as ratings_count, ROUND(AVG(num_stars),1) as avg_rating 
                    from Ratings_rate
                    group by id_user 
                    having id_user ={user_id};"""
    user_stat = query_db(user_stats)
    u_count, u_avg = user_stat['ratings_count'].tolist()[0], user_stat['avg_rating'].tolist()[0]

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









