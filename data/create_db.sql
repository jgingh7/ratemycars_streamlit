drop table if exists Sell cascade;
drop table if exists Ratings_rate cascade;
drop table if exists Users cascade;
drop table if exists Dealers cascade;
drop table if exists Cars_made_from_come_with cascade;
drop table if exists Tires_made_from cascade;
drop table if exists Tire_Manufacturers cascade;
drop table if exists Car_Manufacturers cascade;


CREATE TABLE Car_Manufacturers (
  car_manu_id SERIAL PRIMARY KEY,
  name varchar(64) UNIQUE NOT NULL,
  HQ_country varchar(64)
);

CREATE TABLE Tire_Manufacturers (
  tire_manu_id SERIAL PRIMARY KEY,
  name varchar(64) UNIQUE NOT NULL,
  HQ_country varchar(64)
);

CREATE TABLE Tires_made_from (
  tire_id SERIAL PRIMARY KEY,
  model varchar(64) NOT NULL,
  type varchar(64),
  size int,
  id_manu int NOT NULL,
  FOREIGN KEY (id_manu) REFERENCES Tire_Manufacturers (tire_manu_id)
);

CREATE TABLE Cars_made_from_come_with (
  car_id SERIAL PRIMARY KEY,
  model varchar(64) NOT NULL,
  year int NOT NULL,
  UNIQUE(model, year),
  id_manu int NOT NULL,
  id_tire int NOT NULL,
  FOREIGN KEY (id_manu) REFERENCES Car_Manufacturers (car_manu_id),
  FOREIGN KEY (id_tire) REFERENCES Tires_made_from (tire_id)
);

CREATE TABLE Dealers (
  dealer_id SERIAL PRIMARY KEY,
  name varchar(64) UNIQUE NOT NULL,
  state varchar(64),
  city varchar(64)
);

CREATE TABLE Users (
  user_id SERIAL PRIMARY KEY,
  username varchar(128) UNIQUE NOT NULL,
  date_joined timestamp NOT NULL DEFAULT NOW()
);

CREATE TABLE Ratings_rate (
  rating_id SERIAL PRIMARY KEY,
  num_stars int NOT NULL,
  comment varchar(518),
  time_created timestamp NOT NULL DEFAULT NOW(),
  id_car int NOT NULL,
  id_user int NOT NULL,
  FOREIGN KEY (id_car) REFERENCES Cars_made_from_come_with (car_id),
  FOREIGN KEY (id_user) REFERENCES Users (user_id) ON DELETE CASCADE
);

CREATE TABLE Sell (
  id_car int,
  id_dealer int,
  PRIMARY KEY (id_car, id_dealer),
  FOREIGN KEY (id_car) REFERENCES Cars_made_from_come_with (car_id),
  FOREIGN KEY (id_dealer) REFERENCES Dealers (dealer_id)
);