DROP TABLE IF EXISTS income;
DROP TABLE IF EXISTS expenses;
DROP TABLE IF EXISTS budget;
DROP TABLE IF EXISTS investments;
DROP TABLE IF EXISTS savings_goals;

CREATE TABLE income (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    amount DECIMAL(10,2) NOT NULL,
    date DATETIME NOT NULL
);

CREATE TABLE expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    amount DECIMAL(10,2) NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    date DATETIME NOT NULL
);

CREATE TABLE budget (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT UNIQUE NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    date DATETIME NOT NULL
);

CREATE TABLE investments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    amount DECIMAL(10,2) NOT NULL,
    type TEXT NOT NULL,
    date DATETIME NOT NULL
);

CREATE TABLE savings_goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    amount DECIMAL(10,2) NOT NULL,
    target_date DATE NOT NULL,
    date DATETIME NOT NULL
); 
