import psycopg2
import os
import time
import asyncio


class MyDataBase:
    def __init__(self):
        DATABASE_URL = 'url'
        DATABASE_URL = os.environ['DATABASE_URL'] = DATABASE_URL
        self.conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        self.c = self.conn.cursor()
        self.c.execute('CREATE TABLE IF NOT EXISTS servers (id bigint, forb_roles text)')
        self.conn.commit()

    def get_servers(self):
        self.c.execute('SELECT * FROM servers')
        return self.c.fetchall()

    def get_jobs(self, id):
        self.c.execute(f'SELECT * FROM "Jobs{id}"')
        fetched = []
        for job in self.c.fetchall():
            job = list(job)
            job[1] = eval(job[1])
            fetched.append(job)
        return fetched

    def get_bank(self, id):
        self.c.execute(f'SELECT * FROM "Bank{id}"')
        return self.c.fetchall()

    def get_goods(self, id):
        self.c.execute(f'SELECT * FROM "Goods{id}"')
        return self.c.fetchall()

    def get_members(self, id):
        self.c.execute(f'SELECT * FROM "Server{id}"')
        return self.c.fetchall()

    def get_roulette(self, id):
        self.c.execute(f'SELECT * FROM "Roulette{id}"')
        return self.c.fetchall()

    def get_server(self, id):
        members = self.get_members(id)
        goods = self.get_goods(id)
        jobs = self.get_jobs(id)
        bank = self.get_bank(id)
        return {'members': members, 'goods': goods, 'jobs': jobs, 'bank': bank}

    def add_good(self, id, name, c_name, price, desc, sell_price):
        self.c.execute(f'INSERT INTO "Goods{id}" VALUES (%s,%s,%s,%s,%s)', (name, c_name, price, desc, sell_price))
        self.conn.commit()

    def add_job(self, id, name, require, salary, c_name):
        require = str(require)
        self.c.execute(f'INSERT INTO "Jobs{id}" VALUES (%s,%s,%s,%s)', (name, require, salary, c_name,))
        self.conn.commit()

    def update_forb_roles(self, id, forb_roles):
        self.c.execute('UPDATE servers SET forb_roles = %s WHERE name = %s', (forb_roles, id,))
        self.conn.commit()

    def add_member(self, id, member_id):
        self.c.execute(f'INSERT INTO "Server{id}" VALUES (%s,%s,%s,%s,%s,%s,%s)', (member_id, 10, None, 0,'[]', 0, time.time(),))
        self.conn.commit()

    def add_server(self, server):
        id = server.guild.id
        members = []
        jobs = server.jobs
        roulette = server.roulette
        goods = server.shop.goods
        self.c.execute(f'CREATE TABLE "Server{id}" (id INTEGER, balance INTEGER, job TEXT, lock INTEGER, lockpick INTEGER, securities INTEGER, have TEXT, salary INTEGER, last_salary)')
        self.c.execute(f'CREATE TABLE "Jobs{id}" (name TEXT, require TEXT, salary INTEGER, c_name TEXT)')
        self.c.execute(f'CREATE TABLE "Roulette{id}" (params TEXT)')
        self.c.execute(f'CREATE TABLE "Goods{id}" (name TEXT, c_name TEXT, price INTEGER, desc TEXT, sel_price INTEGER)')
        self.c.execute(f'CREATE TABLE "Bank{id}" (name TEXT, c_name TEXT, price INTEGER, desc TEXT, sel_price INTEGER)')
        self.c.execute('INSERT INTO servers VALUES (%s,%s)', (id, '[]'))
        for good in goods:
            self.add_good(id, good.name, good.c_name, good.price, good.desc, good.sell_price)
        self.conn.commit()
        for job in jobs:
            self.add_job(id, job.name, job.requirement, job.salary, job.c_name)
        self.conn.commit()
        for member in members:
            self.add_member(id, member.owner.id)
        self.conn.commit()

    def delete_server(self, id):
        self.c.execute(f'DROP TABLE "Server{id}"')
        self.c.execute(f'DROP TABLE "Jobs{id}"')
        self.c.execute(f'DROP TABLE "Roulette{id}"')
        self.c.execute(f'DROP TABLE "Goods{id}"')
        self.c.execute(f'DROP TABLE "Bank{id}"')
        self.c.execute(f'DELETE FROM servers WHERE name={id}')
        self.conn.commit()

    def delete_member(self, id, member_id):
        self.c.execute(f'DELETE FROM "Server{id}" WHERE id={member_id}')
        self.conn.commit()

    def update_member(self, id, member_id, wallet):
        balance = wallet.balance
        job = wallet.job
        secur = wallet.securities
        have = str(wallet.have)
        salary = wallet.salary
        last_salary = wallet.last_salary
        self.c.execute(f'UPDATE "Server{id}" SET balance = %s, job = %s, securities = %s, have = %s, salary = %s, last_salary=%s WHERE id={member_id}', (balance, job, secur, have, salary,last_salary,))
        self.conn.commit()

    def delete_job(self, id, c_name):
        self.c.execute(f'DELETE FROM "Jobs{id}" WHERE c_name=%s', (c_name,))
        self.conn.commit()

    def update_job(self, id, name, require, salary, c_name):
        require = str(require)
        self.c.execute(f'UPDATE "Jobs{id}" SET name=%s, require=%s, salary=%s WHERE c_name=%s', (name, require, salary, c_name,))
        self.conn.commit()

    def delete_good(self, id, c_name):
        self.c.execute(f'DELETE FROM "Goods{id}" WHERE c_name=%s', (c_name,))
        self.conn.commit()

    def update_good(self, id, c_name, name, price, desc, sell_price):
        self.c.execute(f'UPDATE "Goods{id}" SET name=%s, price=%s, desc=%s, sell_price=%s WHERE c_name=%s',
                       (name, price, desc, sell_price, c_name,))
        self.conn.commit()

    def update_bank_user(self, user):
        balance = user.balance
        member_id = user.owner.owner.id
        id = user.owner.W_Guild.guild.id
        self.c.execute(
            f'UPDATE "Bank{id}" SET balance = %s WHERE id={member_id}', (balance,))
        self.conn.commit()

    def add_bank_user(self, id, mem_id):
        self.c.execute(f'INSERT INTO "Bank{id}" VALUES(%s,%s)', (mem_id, 0,))
        self.conn.commit()
