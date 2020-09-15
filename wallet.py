import random
import discord
from discord.ext.commands import has_permissions, MissingPermissions
import time
import datetime
from discord.ext import commands
from discord.utils import get
import sqlite3
import asyncio
from data import MyDataBase
from abc import ABC, abstractmethod, abstractproperty


prefix = "//"
my_guilds = []
bot = commands.Bot(command_prefix=prefix)
bot.remove_command('help')


def is_me():
    def predicate(ctx):
        return ctx.author.id == 422424489020620811
    return commands.check(predicate)


def write_coin(x):
    x = abs(int(x))
    a = x % 10
    if a > 4 or a == 0:
        return ""
    elif 5 > a > 1:
        return "ы"
    elif a == 1:
        return "у"


def write_coin_bal(x):
    x = abs(int(x))
    x = x%100
    a = x % 10
    if a == 1:
        return "а"
    elif (a > 4) or (a == 0) or (21>x>9):
        return ""
    if 5 > a > 1:
        return "ы"


def write_coin_tr(x):
    x = abs(int(x))
    a = x % 10
    if a > 4 or a == 0 or (21>x>9):
        return ""
    elif 5 > a > 1:
        return "ы"
    elif a == 1:
        return "у"


def write_coin_gb(x):
    x = abs(int(x))
    a = x % 10
    if 5 > a > 1:
        return "ы"
    elif (a > 4) or (a == 0) or (x > 9):
        return ""
    elif a == 1:
        return "а"


@bot.event
async def on_guild_join(guild):
    W_Guild = WalletGuid(guild)
    W_Guild.members_reg()
    my_guilds.append(W_Guild)
    database.add_server(W_Guild)
    print("New Guild")


@bot.event
async def on_guild_remove(guild):
    W_Guild = get(my_guilds, guild=guild)
    my_guilds.remove(W_Guild)
    database.delete_server(guild.id)
    W_Guild.delete()


@bot.event
async def on_member_remove(member):
    W_Guild = get(my_guilds, guild=member.guild)
    W_Guild.delete_wallet(member)
    database.delete_member(member.guild.id, member.id)


@bot.event
async def on_member_join(member):
    W_Guild = get(my_guilds, guild=member.guild)
    W_Guild.create_wallet(member)
    database.add_member(member.guild.id, member.id)


@bot.event
async def on_ready():
    for server in database.get_servers():
        forb_roles = server[1]
        server = server[0]
        print(bot.get_guild(server))
        wal = WalletGuid(bot.get_guild(server))
        server_params = database.get_server(server)
        for params in server_params["jobs"]:
            name = params[0]
            c_name = params[3]
            salary = params[2]
            require = params[1]
            wal.job_hand.add_job(c_name, name, salary, require)
        for member in server_params["members"]:
            wallet = wal.create_wallet(bot.get_user(member[0]))
            wallet.balance = round(member[1], 2)
            try:
                job = wal.job_hand.get_job(member[2])
                wallet.job = job.c_name
                job.users.append(wallet)
            except NotInTheList:
                wallet.job = None
            wallet.securities = member[3]
            wallet.have = eval(member[4])
            wallet.salary = member[5]
            if member[6]:
                wallet.last_salary = member[6]
            else:
                wallet.last_salary = time.time()
        for user in server_params["bank"]:
            try:
                wallet = wal.get_wallet(bot.get_user(user[0]))
            except WalletDoesntExist:
                pass
            else:
                wal.bank.add_user(wallet, user[1])
        for good in server_params["goods"]:
            try:
                wal.shop.add_good(good)
            except NotInTheList:
                pass
            try:
                ShopRole = wal.shop.available["role"]
                ShopRole.forb_roles = eval(forb_roles)
            except AttributeError:
                pass
        my_guilds.append(wal)
    print('Logged on as', bot.user)


@bot.command()
async def casino(ctx, deposit: int):
    if not ctx.guild:
        return
    deposit = abs(deposit)
    if not deposit:
        await ctx.send(f"<@{ctx.author.id}>, депозит не может быть равным нулю")
        return
    await ctx.message.delete()
    end_time = time.strftime("%H:%M", time.gmtime(time.time() + 60))
    W_Guild = get(my_guilds, guild=ctx.guild)
    embed = discord.Embed(title='Это казино "MissFortune"',
                          description=f"Вы делает ставку в размере {deposit} монет(ы), которая уходит в банк.\nПо истечению определенного времени, один счастливчик забирает весь банк.\nПри недостатке средств, Ваш депозит не учитывается.\nПри 'выходе' из игры, ваша ставка остается в банке и даже может быть отдана человеку, у которого не хватает средств на собственную ставку",
                          color=0xff1117)
    embed.add_field(name='Для ставки поставьте реакцию "➕"', value="(:heavy\_plus_sign:)", inline=False)
    embed.add_field(name="обедитель будет объявлен в", value=end_time,
                    inline=True)
    message = await ctx.send(embed=embed)
    await message.add_reaction("➕")
    await Casino(ctx.channel, W_Guild, message, deposit).game()


@bot.command()
async def help(ctx):
    embed = discord.Embed(title="Список команд:", color=0x80ff00)
    embed.add_field(value=f"{prefix}bal", name="Узнать баланс", inline=True)
    embed.add_field(value=f"{prefix}gamble", name="Рулетка", inline=True)
    embed.add_field(value=f"{prefix}tr человек сумма", name="Перевод монет", inline=True)
    embed.add_field(value=f"{prefix}casino депозит ", name="Казино", inline=True)
    embed.add_field(value=f"{prefix}shop", name="Магазин", inline=True)
    embed.add_field(value=f"{prefix}bank", name="Банк", inline=True)
    embed.add_field(value=f"{prefix}shopsell", name="Черный рынок", inline=True)
    embed.add_field(value=f"{prefix}jobs", name="Биржа работ", inline=True)
    embed.add_field(value=f"{prefix}steal человек", name="Кража части средств человека", inline=True)
    embed.add_field(value=f"{prefix}me", name="Информация о Вас", inline=True)
    embed.add_field(value=f"{prefix}salary", name="Получить зарплату", inline=True)
    await ctx.send(embed=embed)


@bot.command()
async def gamble(ctx):
    if not ctx.guild:
        return
    W_Guild = get(my_guilds, guild=ctx.guild)
    wallet = W_Guild.get_wallet(ctx.author)
    try:
        last_time = time.time() - wallet.last_gamble
    except AttributeError:
        await ctx.send(f"<@{ctx.author.id}>, Вы еще не зарегестрированы. Для регистрации напишите {prefix}reg")
        return
    if last_time >= 60:
        x = random.randint(-3, 7)
        wallet.change_bal(x)
        wallet.last_gamble = time.time()
        if x < 0:
            await ctx.send(f"<@{ctx.author.id}>, Вы потеряли {x*-1} монет{write_coin(x)}")
        elif x == 0:
            await ctx.send(f"<@{ctx.author.id}>, Вы ничего не получили")
        else:
            await ctx.send(f"<@{ctx.author.id}>, Вы получили {x} монет{write_coin(x)}")
    else:
        left_time = int(60-last_time)
        await ctx.send(f"<@{ctx.author.id}>, вы можете использовать эту комманду только раз в минуту. Осталось {left_time} секунд{write_coin_gb(left_time)}")


@bot.command()
async def bal(ctx):
    if not ctx.guild:
        return
    W_Guild = get(my_guilds, guild=ctx.guild)
    wallet = W_Guild.get_wallet(ctx.author)
    name = f"<@{ctx.author.id}>"
    try:
        bal = wallet.balance
    except AttributeError:
        await ctx.send(f"{name}, Вы еще не зарегестрированы. Для регистрации напишите {prefix}reg")
        return
    message = await ctx.send(f"{name}, у Вас {bal} монет{write_coin_bal(bal)}")
    await asyncio.sleep(5)
    await message.delete()
    await ctx.message.delete()


@bot.command()
async def tr(ctx, to, money: float):
    if not ctx.guild:
        return
    money = round(abs(money), 2)
    try:
        to = ctx.message.mentions[0]
    except IndexError:
        await ctx.send(f"<@{ctx.author.id}>, отметьте человека, которому нужно перевести деньги")
        return
    if not money:
        await ctx.message.channel.send(f"<@{ctx.author.id}>, введите сумму")
        return
    W_Guild = get(my_guilds, guild=ctx.guild)
    try:
        W_Guild.transaction(_from=ctx.author, to=to, x=money)
    except NotEnoughMoney:
        await ctx.send(f"<@{ctx.author.id}>, у вас недостаточно денег")
        return
    except NotInTheList:
        await ctx.send(f"<@{ctx.author.id}>, данного человека нет на сервере")
        return
    except WalletDoesntExist:
        await ctx.send(f"<@{ctx.author.id}>, Вы еще не зарегестрированы. Для регистрации напишите {prefix}reg")
        return
    await ctx.message.delete()
    message = await ctx.send(f"<@{ctx.author.id}>, Вы перевели {money} монет{write_coin_tr(money)} <@{ctx.message.mentions[0].id}>")
    await asyncio.sleep(5)
    await message.delete()


@bot.command()
async def buy(ctx, c_name, *args):
    if not ctx.guild:
        return
    W_Guild = get(my_guilds, guild=ctx.guild)
    wallet = W_Guild.get_wallet(ctx.author)
    shop = W_Guild.shop
    try:
        name = await shop.find_and_buy(wallet, c_name, args, ctx)
    except AttributeError:
        await ctx.send(f"<@{ctx.author.id}>, Вы неправильно написали название товара")
        return
    except NotEnoughMoney:
        await ctx.send(f"<@{ctx.author.id}>, недостаточно денег")
        return
    except WalletDoesntExist:
        await ctx.send(f"<@{ctx.author.id}>, Вы еще не зарегестрированы. Для регистрации напишите {prefix}reg")
        return
    except Forbidden:
        await ctx.send(f"<@{ctx.author.id}>, Вы не можете купить данный товар")
        return
    await ctx.send(f"<@{ctx.author.id}>, вы успешно купили {name.lower()}")


@bot.command()
async def sell(ctx, c_name, count=1):
    if not ctx.guild:
        return
    count = int(abs(count))
    if count == 0:
        await ctx.send(f"<@{ctx.author.id}>, кол-во должно быть больше нуля")
        return
    W_Guild = get(my_guilds, guild=ctx.guild)
    wallet = W_Guild.get_wallet(ctx.author)
    shop = W_Guild.shop
    try:
        name = await shop.sell(wallet, c_name, count, ctx)
    except CantSell:
        await ctx.send(f"<@{ctx.author.id}>, {c_name} невозможно продать")
        return
    except AttributeError:
        await ctx.send(f"<@{ctx.author.id}>, Вы неправильно написали название товара")
        return
    except WalletDoesntExist:
        await ctx.send(f"<@{ctx.author.id}>, Вы еще не зарегестрированы. Для регистрации напишите {prefix}reg")
        return
    except NotInTheList:
        await ctx.send(f"<@{ctx.author.id}>, у вас нет {count} {c_name}")
        return
    await ctx.send(f"<@{ctx.author.id}>, вы успешно продали {name.lower()}")


@bot.command()
async def shopsell(ctx):
    W_Guild = get(my_guilds, guild=ctx.guild)
    embed = W_Guild.shop.show_sell()
    await ctx.send(embed=embed)


@bot.command()
async def jobs(ctx):
    W_Guild = get(my_guilds, guild=ctx.guild)
    job_hand = W_Guild.job_hand
    await ctx.send(embed=job_hand.show())


@bot.command()
async def work(ctx, c_name):
    if not ctx.guild:
        return
    W_Guild = get(my_guilds, guild=ctx.guild)
    wallet = W_Guild.get_wallet(ctx.author)
    if not wallet:
        await ctx.send(f"<@{ctx.author.id}>, Вы еще не зарегестрированы. Для регистрации напишите {prefix}reg")
        return
    if c_name == "quit":
        if not wallet.job:
            await ctx.send(f"<@{ctx.author.id}>, у Вас нет работы")
            return
        wallet.job = None
        wallet.salary = 0
        await ctx.send(f"<@{ctx.author.id}>, Вы уволились с работы")
        return
    job_hand = W_Guild.job_hand
    try:
        job_hand.get_work(c_name, wallet)
    except NotInTheList:
        await ctx.send(f"<@{ctx.author.id}>, такой работы не существует")
        return
    except Forbidden:
        await ctx.send(f"<@{ctx.author.id}>, у Вас не хватает чего-то")
        return
    await ctx.send(f"<@{ctx.author.id}>, Вы теперь работаете")


@bot.command()
async def shop(ctx):
    W_Guild = get(my_guilds, guild=ctx.guild)
    embed = W_Guild.shop.show_buy()
    await ctx.send(embed=embed)


@bot.command()
async def reg(ctx):
    if not ctx.guild:
        return
    W_Guild = get(my_guilds, guild=ctx.guild)
    if get(W_Guild.wallets, owner=ctx.author):
        await ctx.send(f"<@{ctx.author.id}>, Вы уже зарегестрированы.")
        return
    wallet = W_Guild.create_wallet(ctx.author)
    database.add_member(ctx.guild.id, ctx.author.id)
    await ctx.send(f"<@{ctx.author.id}>, Вы успешно зарегестрировались.")


@bot.command()
async def steal(ctx, person):
    if not ctx.guild:
        return
    W_Guild = get(my_guilds, guild=ctx.guild)
    wallet = W_Guild.get_wallet(ctx.author)
    s_wallet = W_Guild.get_wallet(ctx.message.mentions[0])
    if ctx.author == ctx.message.mentions[0]:
        await ctx.send(f"<@{ctx.author.id}>, Вы не можете ограбить самого себя")
        return
    if time.time() - wallet.last_steal < 600:
        await ctx.send(f"<@{ctx.author.id}>, копы ждали вас прямо за углом вашего дома. Вы струсили и решили не идти на дело.")
        return
    if time.time() - s_wallet.last_gotten_steal < 1200:
        await ctx.send(
            f"<@{ctx.author.id}>, около дома {ctx.message.mentions[0]} тусуется целая стая копов. Вы струсили и решили не идти на дело.")
        return
    f_weight = 99
    s_weight = 1
    try:
        if "lock" in s_wallet.have:
            f_weight -= 98
            s_weight += 98
    except AttributeError:
        await ctx.send(f"<@{ctx.author.id}>, такой пользователь не зарегестрирован")
        return
    try:
        if "lockpick" in wallet.have:
            f_weight += 29
            s_weight -= 29
    except AttributeError:
        await ctx.send(f"<@{ctx.author.id}>, Вы еще не зарегестрированы. Для регистрации напишите {prefix}reg")
        return
    weights = [1]*f_weight + [0]*s_weight
    result = random.choice(weights)

    if result:
        wallet.last_steal = time.time()
        s_wallet.last_gotten_steal = time.time()
        if s_wallet.balance < 5:
            await ctx.send(f"У {ctx.message.mentions[0]} настолько мало денег, что Вы их просто не смогли найти")
            return
        percent = random.randint(15, 30)/100
        money = s_wallet.balance*percent
        money = round(money, 2)
        s_wallet.change_bal(money*-1)
        wallet.change_bal(money)
        await ctx.send(f"<@{ctx.author.id}> украл у {ctx.message.mentions[0]} {money} монет{write_coin_tr(money)}")
        return
    wallet.last_steal = time.time()
    await ctx.send(f"<@{ctx.author.id}> ограбление не удалось. Сейф {ctx.message.mentions[0]} оказался сильнее Вас.")


@bot.command()
async def me(ctx):
    if not ctx.guild:
        return
    W_Guild = get(my_guilds, guild=ctx.guild)
    wallet = W_Guild.get_wallet(ctx.author)
    try:
        variables = vars(wallet)
    except TypeError:
        await ctx.send(f"<@{ctx.author.id}>, Вы еще не зарегестрированы. Для регистрации напишите {prefix}reg")
        return
    dontshow = ["owner", "W_Guild"]
    embed = discord.Embed(title=f"Информация о {ctx.author}", description="Все, что с Вами связанно:", color=0x0080ff)
    for key, value in variables.items():
        if key not in dontshow:
            if key.startswith("last"):
                cur_time = time.time()
                if value == 0:
                    value = cur_time
                value = time.strftime("%H:%M:%S", time.gmtime(cur_time-value))
            embed.add_field(value=str(value),
                            name=key, inline=True)
    message = await ctx.send(embed=embed)
    await asyncio.sleep(5)
    await message.delete()
    await ctx.message.delete()


@bot.command()
async def salary(ctx):
    if not ctx.guild:
        return
    W_Guild = get(my_guilds, guild=ctx.guild)
    wallet = W_Guild.get_wallet(ctx.author)
    try:
        if not wallet.job:
            await ctx.send(f"<@{ctx.author.id}>, у Вас нет работы")
            return
    except AttributeError:
        await ctx.send(f"<@{ctx.author.id}>, Вы еще не зарегестрированы. Для регистрации напишите {prefix}reg")
        return
    got = wallet.get_salary()
    message = await ctx.send(f"<@{ctx.author.id}>, Вы получили {got} монет{write_coin_tr(got)}")
    await ctx.message.delete()
    await asyncio.sleep(5)
    await message.delete()


@bot.command()
@commands.check_any(is_me(), has_permissions(administrator=True))
async def add(ctx, *args):
    if not ctx.guild:
        return
    try:
        object = args[0]
        args = args[1:]
    except IndexError:
        embed = discord.Embed(title="Добавить что-то куда-то",
                              description="c_name = название для комманд на англ, name = название",
                              color=0x80ff00)
        embed.add_field(value=f"{prefix}add good", name="товар в магазин", inline=True)
        embed.add_field(value=f"{prefix}add forb_role", name="роль, которую нельзя купить", inline=True)
        embed.add_field(value=f"{prefix}add work", name="работа", inline=True)
        await ctx.send(embed=embed)
        return
    W_Guild = get(my_guilds, guild=ctx.guild)
    if object == "good":
        shop = W_Guild.shop
        if not args:
            embed = discord.Embed(title="Добавить товар", description="c_name = название для комманд на англ, name = название, price = стоимость, sell_price = деньги за продажу(0, если нельзя продавать)", color=0x80ff00)
            embed.add_field(value=f"{prefix}add good c_name name price sell_price", name=".", inline=True)
            await ctx.send(embed=embed)
            return
        c_name = args[0]
        try:
            price = int(args[-2])
            sell_price = int(args[-1])
        except ValueError:
            await ctx.send("sell_price и price должны быть int")
            return
        args = args[1:]
        args = args[:-2]
        name = " ".join(i for i in args)
        print(c_name,name,price,sell_price)
        desc = shop.create_good(c_name, name, price, sell_price)
        database.add_good(ctx.guild.id, name, c_name, price, desc, sell_price)
    elif object == "forb_role":
        shop = W_Guild.shop
        name = ctx.message.role_mentions[0].name
        print(name)
        if name:
            shop.available["role"].add_forb_role(ctx.guild.id, name)
        else:
            embed = discord.Embed(title="Добавить запрещенную роль",
                                  description="name = название роли",
                                  color=0x80ff00)
            embed.add_field(value=f"{prefix}add forb_role name", name=".", inline=True)
            await ctx.send(embed=embed)
            return
    elif object == "work":
        job_hand = W_Guild.job_hand
        if not args:
            embed = discord.Embed(title="Изменить список",
                                  description="c_name = название для комманд на англ, name = название, salary = зарплата, requirement = список нужных предметов(c_name, через пробел):",
                                  color=0x80ff00)
            embed.add_field(name=f"Добавить", value=f"{prefix}add work c_name name salary requirement", inline=True)
            await ctx.send(embed=embed)
            return
        c_name = args[0]
        name = args[1]
        try:
            salary = int(args[2])
        except ValueError:
            await ctx.send("Зарплата должны быть int")
            return
        args = args[3:]
        require = list(args)
        job_hand.create_job(c_name, name, salary, require)
    else:
        return
    await ctx.send("Успешно добавлено")


@bot.command()
@commands.check_any(is_me(), has_permissions(administrator=True))
async def edit(ctx, *args):
    if not ctx.guild:
        return
    try:
        object = args[0]
        args = args[1:]
    except IndexError:
        embed = discord.Embed(title="Изменить что-то где-то",
                              description="c_name = название для комманд на англ, name = название",
                              color=0x80ff00)
        embed.add_field(value=f"{prefix}edit good", name="товар в магазине", inline=True)
        embed.add_field(value=f"{prefix}edit work", name="работа", inline=True)
        await ctx.send(embed=embed)
        return
    if object == "good":
        W_Guild = get(my_guilds, guild=ctx.guild)
        shop = W_Guild.shop
        if not args:
            embed = discord.Embed(title="Изменить товар",
                                  description="c_name = название для комманд на англ, name = название, price = стоимость, sell_price = деньги за продажу(0, если нельзя продавать)",
                                  color=0x80ff00)
            embed.add_field(value=f"{prefix}edit c_name name price sell_price", name=".", inline=True)
            await ctx.send(embed=embed)
            return
        c_name = args[0]
        try:
            price = int(args[-2])
            sell_price = int(args[-1])
        except ValueError:
            await ctx.send("sell_price и price должны быть int")
            return
        args = args[1:]
        args = args[:-2]
        name = " ".join(i for i in args)
        try:
            shop.edit_good(ctx.guild.id, c_name, name, price, sell_price)
        except NotInTheList:
            await ctx.send("Такого товара нет")
            return
    elif object == "work":
        W_Guild = get(my_guilds, guild=ctx.guild)
        job_hand = W_Guild.job_hand
        if not args:
            embed = discord.Embed(title="Изменить список",
                                  description="c_name = название для комманд на англ, name = название, salary = зарплата, requirement = список нужных предметов(c_name, через пробел):",
                                  color=0x80ff00)
            embed.add_field(name=f"Изменить", value=f"{prefix}edit work c_name name salary requirement", inline=True)
            await ctx.send(embed=embed)
            return
        c_name = args[0]
        name = args[1]
        try:
            salary = int(args[2])
        except ValueError:
            await ctx.send("Зарплата должны быть int")
            return
        args = args[3:]
        require = list(args)
        try:
            job_hand.edit_job(c_name, name, salary, require)
        except NotInTheList:
            await ctx.send("Такой работы нет")
            return
    else:
        return
    await ctx.send("Изменено")


@bot.command()
@commands.check_any(is_me(),has_permissions(administrator=True))
async def delete(ctx, *args):
    if not ctx.guild:
        return
    try:
        object = args[0]
        args = args[1:]
    except IndexError:
        embed = discord.Embed(title="Удалить что-то где-то",
                              description="c_name = название для комманд на англ, name = название",
                              color=0x80ff00)
        embed.add_field(value=f"{prefix}delete good", name="товар в магазине", inline=True)
        embed.add_field(value=f"{prefix}delete work", name="работу", inline=True)
        embed.add_field(value=f"{prefix}delete messages", name="сообщения бота на определенном участке", inline=True)
        await ctx.send(embed=embed)
        return
    W_Guild = get(my_guilds, guild=ctx.guild)
    shop = W_Guild.shop
    if object == "good":
        if not args:
            embed = discord.Embed(title="Удалить товар",
                                  description="c_name = название для комманд на англ",
                                  color=0x80ff00)
            embed.add_field(value=f"{prefix}delete good c_name", name=".", inline=True)
            await ctx.send(embed=embed)
            return
        c_name = args[0]
        try:
            shop.del_good(ctx.guild.id, c_name)
        except NotInTheList:
            await ctx.send("Такого товара нет")
            return
    elif object == "work":
        W_Guild = get(my_guilds, guild=ctx.guild)
        job_hand = W_Guild.job_hand
        if not args:
            embed = discord.Embed(title="Изменить список",
                                  description="c_name = название с комманд",
                                  color=0x80ff00)
            embed.add_field(name=f".", value=f"{prefix}delete work c_name", inline=True)
            await ctx.send(embed=embed)
            return
        c_name = args[0]
        try:
            job_hand.delete_job(c_name)
        except NotInTheList:
            await ctx.send("Такой работы нет")
            return
    elif object == "messages":
        try:
            count = int(args[0])+1
        except KeyError:
            embed = discord.Embed(title="Удалить определенное кол-во сообщений бота",
                                  description="count = число сообщений, в списке который бот удалит все свои сообщения",
                                  color=0x80ff00)
            embed.add_field(value=f"{prefix}delete message count", name=".", inline=True)
            await ctx.send(embed=embed)
            return
        except ValueError:
            ctx.send("Count олжен быть числом")
            return
        async for message in ctx.history(limit=count):
            if message.author == bot.user:
                await message.delete()
        await ctx.message.delete()
        return

    else:
        return
    await ctx.send("Удалено")


@bot.command()
async def bank(ctx, *args):
    if not ctx.guild:
        return
    name = f"<@{ctx.author.id}>"
    W_Guild = get(my_guilds, guild=ctx.guild)
    bank = W_Guild.bank
    wallet = W_Guild.get_wallet(ctx.author)
    if not wallet:
        await ctx.send(f"<@{ctx.author.id}>, Вы еще не зарегестрированы. Для регистрации напишите {prefix}reg")
        return
    try:
        object = args[0]
    except IndexError:
        embed = discord.Embed(title='Банк"',
                              description=f"Здесь вы можете надежно хранить свои средства.\nПри любой операции с деньгами, мы забираем 10%",
                              color=0x0080c0)
        embed.add_field(name=f'{prefix}bank reg', value="Получение своего счета", inline=False)
        embed.add_field(name=f'{prefix}bank dep сумма', value="Положить деньги на счет", inline=False)
        embed.add_field(name=f'{prefix}bank wdraw сумма', value="Вывести деньги", inline=False)
        embed.add_field(name=f'{prefix}bank tr человек сумма', value="Перевести деньги со счета на счет", inline=False)
        embed.add_field(name=f'{prefix}bank bal', value="Баланс на счете", inline=False)
        embed.add_field(name=f'{prefix}bank rob', value="Ограбление", inline=False)
        await ctx.send(embed=embed)
        return
    args = args[1:]
    if object == "bal":
        user = bank.get_user(wallet)
        try:
            bal = user.balance
        except AttributeError:
            await ctx.send(f"<@{ctx.author.id}>, у Вас нет лицевого счета. Для получения пропишите {prefix}bank reg")
            return
        message = await ctx.send(f"{name}, у Вас {bal} монет{write_coin_bal(bal)}")
        await asyncio.sleep(5)
        await message.delete()
        await ctx.message.delete()
    elif object == "reg":
        try:
            bank.reg(ctx.guild.id, wallet)
        except Forbidden:
            await ctx.send("Вы уже имеете счет")
            return
        await ctx.send("Вам был выдан лицевой счет")
    elif object == "tr":
        x = args[-1]
        transfer_wallet = W_Guild.get_wallet(ctx.message.mentions[0])
        if not transfer_wallet:
            await ctx.send(f"<@{ctx.author.id}>, Вам нужно упомянуть человека, которому нужно перевести деньги ")
            return
        try:
            x = float(x)
        except ValueError:
            await ctx.send(f"{name}, сумма должна быть числом")
            return
        x = round(abs(x), 2)
        try:
            money = bank.transfer(wallet, transfer_wallet, x)
        except WalletDoesntExist:
            await ctx.send(f"{name}, у Вас нет лицевого счета. Для получения пропишите {prefix}bank reg")
            return
        except NotEnoughMoney:
            await ctx.send(f"{name}, у Вас недостаточно денег")
            return
        except NotInTheList:
            await ctx.send(f"{ctx.message.mentions[0].name} не имеет лицевого счета")
            return
        message = await ctx.send(f"<@{ctx.author.id}>, Вы перевели {money} монет{write_coin_tr(money)} <@{ctx.message.mentions[0].id}>")
        await asyncio.sleep(5)
        await ctx.message.delete()
        await message.delete()
    elif object == "dep":
        x = args[0]
        try:
            x = float(x)
        except ValueError:
            await ctx.send(f"{name}, сумма должна быть числом")
            return
        x = round(abs(x), 2)
        try:
            x = bank.deposit(wallet, x)
        except WalletDoesntExist:
            await ctx.send(f"{name}, у Вас нет лицевого счета. Для получения пропишите {prefix}bank reg")
            return
        except NotEnoughMoney:
            await ctx.send(f"{name}, у Вас недостаточно денег")
            return
        message = await ctx.send(f"{name}, Вы положили {x} монет{write_coin(x)} на счет")
        await asyncio.sleep(5)
        await ctx.message.delete()
        await message.delete()
    elif object == "wdraw":
        x = args[0]
        try:
            x = float(x)
        except ValueError:
            await ctx.send(f"{name}, сумма должна быть числом")
            return
        x = round(abs(x), 2)
        try:
            x = bank.withdraw(wallet, x)
        except WalletDoesntExist:
            await ctx.send(f"{name}, у Вас нет лицевого счета. Для получения пропишите {prefix}bank reg")
            return
        except NotEnoughMoney:
            await ctx.send(f"{name}, у Вас недостаточно денег")
            return
        message = await ctx.send(f"{name}, Вы сняли {x} монет{write_coin(x)} со счета")
        await asyncio.sleep(5)
        await ctx.message.delete()
        await message.delete()
    elif object == "rob":
        if time.time() - wallet.last_rob < 600:
            await ctx.send(f"<@{ctx.author.id}>, копы ждали вас прямо за углом вашего дома. Вы струсили и решили не идти на дело.")
            return
        user = bank.get_user(wallet)
        if not user:
            await ctx.send(f"<@{ctx.author.id}>, у Вас нет лицевого счета. Для получения пропишите {prefix}bank reg")
            return
        try:
            money = bank.rob(wallet)
        except WalletDoesntExist:
            await ctx.send(f"<@{ctx.author.id}>, Вы еще не зарегестрированы. Для регистрации напишите {prefix}reg")
            return
        except Forbidden:
            await ctx.send(
                f"<@{ctx.author.id}>, около банка тусуется целая стая копов. Вы струсили и решили не идти на дело.")
            return
        if money:
            await ctx.send(f"{name}, поздравляем, Вы успешно ограбили банк. Вы получили {money} монет{write_coin_tr(money)}")
            return
        if user.balance > wallet.balance:
            balance = user.balance
            user.change_bal(balance * -0.2)
        else:
            balance = wallet.balance
            wallet.change_bal(balance*-0.2)
        await ctx.send(f"{name}, ограбление не удалось. У выс забрали 20% вашего баланса в качестве компенсации")
        return


"""@bot.command()
@is_me()
async def prefix(ctx, pref):
    global prefix
    prefix = ctx.message.content.split()[1]"""


@bot.event
async def on_message(message):
    if message.author.id == bot.user:
        return
    """
    if "хихи" in message.content.lower():
        W_Guild = get(my_guilds, guild=message.guild)
        wallet = W_Guild.get_wallet(message.author)
        wallet.change_bal(-5)
        wallet = random.choice(W_Guild.wallets)
        wallet.change_bal(5)
        await message.channel.send(f"<@{message.author.id}> за 'хихи' твои 5 монет были переведены <@{wallet.owner.id}>")
        return"""
    if message.author.id == 422424489020620811:
        if message.content.startswith("Ферум скажи"):
            if "ъеъ" in message.content[12:]:
                await message.channel.send("Error")
                return
            await message.delete()
            await message.channel.send(message.content[12:])
    if message.content.startswith(f"{prefix}e-bal"):
        message.content = f"{prefix}bal"
    await bot.process_commands(message)


class Wallet:
    def __init__(self, guild, user):
        self.W_Guild = guild
        self.balance = 10
        self.last_gamble = 0
        self.owner = user
        self.job = None
        self.last_gotten_steal = 0
        self.last_steal = 0
        self.securities = 0
        self.salary = 0
        self.have = []
        self.last_salary = 0
        self.last_rob = 0

    def is_enough(self, x):
        if self.balance - x < 0:
            raise NotEnoughMoney

    def change_bal(self, x):
        self.balance += x
        self.balance = round(self.balance, 2)
        database.update_member(self.W_Guild.guild.id, self.owner.id, self)

    def do_have(self, thing):
        if thing not in self.have:
            raise KeyError

    def update(self):
        database.update_member(self.W_Guild.guild.id, self.owner.id, self)

    def get_salary(self):
        try:
            job = self.W_Guild.job_hand.get_job(self.job)
            self.salary = job.salary
        except NotInTheList:
            self.job = None
            self.salary = 0
            return
        if not all(req in self.have for req in job.requirement):
            self.job = None
            self.salary = 0
            return
        cur_time = time.time()
        left = (cur_time - self.last_salary)
        got = (left//3600)*self.salary
        if got:
            self.last_salary = cur_time - (left % 3600)
        self.change_bal(got)
        return got


class WalletGuid:
    def __init__(self, guild, roulette=None):
        self.guild = guild
        self.wallets = []
        self.roulette = roulette
        self.shop = Shop()
        self.bank = Bank(self)
        self.job_hand = JobHandler(self)

    def create_wallet(self, person):
        wallet = Wallet(self, person)
        self.wallets.append(wallet)
        return wallet

    def delete_wallet(self, member):
        wallet = get(self.wallets, owner=member)
        self.wallets.remove(wallet)
        del wallet

    def members_reg(self):
        for member in self.guild.members:
            self.create_wallet(member)

    def delete(self):
        for member in self.wallets:
            del member
        del self

    def get_wallet(self, user):
        return get(self.wallets, owner=user)

    def transaction(self, _from, to, x):
        _from_wallet = self.get_wallet(_from)
        try:
            _from_wallet.is_enough(x)
        except NotEnoughMoney:
            raise NotEnoughMoney
        except WalletDoesntExist:
            raise WalletDoesntExist
        to_wallet = self.get_wallet(to)
        try:
            to_wallet.change_bal(x)
        except AttributeError:
            raise NotInTheList  # нет пользователя
        _from_wallet.change_bal(-x)


class Job:
    def __init__(self, name, salary, requirement, c_name):
        self.salary = salary
        self.name = name
        self.requirement = requirement
        self.c_name = c_name
        self.users = []


class JobHandler:
    def __init__(self, W_Guild):
        self.W_Guild = W_Guild
        self.jobs = []

    def get_job(self, c_name):
        job = get(self.jobs, c_name=c_name)
        if not job:
            raise NotInTheList
        return job

    def create_job(self, c_name, name, salary, requirement):
        job = Job(name, salary, requirement, c_name)
        database.add_job(self.W_Guild.guild.id, name, str(requirement), salary, c_name)
        self.jobs.append(job)

    def add_job(self, c_name, name, salary, requirement):
        job = Job(name, salary, requirement, c_name)
        self.jobs.append(job)

    def delete_job(self, c_name):
        try:
            job = self.get_job(c_name)
        except NotInTheList:
            raise NotInTheList
        database.delete_job(self.W_Guild.guild.id, job.c_name)
        self.jobs.remove(job)
        del job

    def edit_job(self, c_name, name, salary, requirement):
        try:
            job = self.get_job(c_name)
        except NotInTheList:
            raise NotInTheList
        job.name = name
        job.salary = salary
        job.requirement = requirement
        database.update_job(self.W_Guild.guild.id, name, requirement, salary, c_name)

    def get_work(self, c_name, wallet):
        try:
            job = self.get_job(c_name)
        except NotInTheList:
            raise NotInTheList
        for req in job.requirement:
            if req not in wallet.have:
                raise Forbidden
        wallet.job = job.c_name
        wallet.salary = job.salary
        wallet.last_salary = time.time()
        wallet.update()

    def show(self):
        closed = ["bank"]
        embed = discord.Embed(title="Биржа работ", description="Здесь вы можете устроиться на(снизу список нужных предметов):", color=0x80ff00)
        for job in self.jobs:
            if job.c_name not in closed:
                embed.add_field(name=f"{job.name} - {job.salary} монет{write_coin(job.salary)}",
                                value=f"{prefix}work {job.c_name}\n{job.requirement}", inline=True)
        return embed


class NotEnoughMoney(Exception):
    pass


class NotInTheList(Exception):
    pass


class WalletDoesntExist(Exception):
    pass


class CantSell(Exception):
    pass


class Casino:
    def __init__(self, channel, W_Guild, message, deposit):
        self.guild = channel
        self.W_Guild = W_Guild
        self.message = message
        self.players = []
        self.wait_time = 60
        self.count = 0
        self.bank = 0
        self.deposit = deposit

    async def game(self):
        await asyncio.sleep(60)
        self.message = await self.guild.fetch_message(id=self.message.id)
        for reaction in self.message.reactions:
            if reaction.emoji == "➕":
                react = reaction
                break
        react_users = await react.users().flatten()
        new_players = react_users
        try:
            for new_player in new_players:
                new_player_wallet = get(self.W_Guild.wallets, owner=new_player)
                if new_player_wallet not in self.players and new_player != bot.user:
                    try:
                        new_player_wallet.is_enough(self.deposit)
                    except NotEnoughMoney:
                        pass
                    except AttributeError:
                        pass
                    else:
                        new_player_wallet.change_bal(self.deposit * -1)
                        self.players.append(new_player_wallet)
                        self.bank += self.deposit
        except KeyError:
            pass
        try:
            winner = random.choice(self.players)
        except IndexError:
            await self.guild.send(f"Никто не принял участие")
        else:
            winner.change_bal(self.bank)
            await self.message.delete()
            await self.guild.send(
                f"<@{winner.owner.id}> победил. Он(а) получает {self.bank} монет{write_coin(self.bank)}")


class Shop:
    def __init__(self):
        self.goods = []
        self.available = {"role": ShopRole(), "lock": ShopLock(), "lockpick": ShopLockPick(), "securities": ShopSecurities()}

    async def find_and_buy(self, wallet, c_name, arg, ctx):
        good = get(self.goods, c_name=c_name)
        try:
            name = await good.buy(wallet, arg, ctx)
        except AttributeError:
            raise AttributeError
        except NotEnoughMoney:
            raise NotEnoughMoney
        except WalletDoesntExist:
            raise WalletDoesntExist
        except Forbidden:
            raise Forbidden
        return name

    async def sell(self, wallet, c_name, count, ctx):
        good = get(self.goods, c_name=c_name)
        try:
            name = await good.sell(wallet, count, ctx)
        except AttributeError:
            raise AttributeError
        except CantSell:
            raise CantSell
        except WalletDoesntExist:
            raise WalletDoesntExist
        except NotInTheList:
            raise NotInTheList
        return name

    def show_buy(self):
        embed = discord.Embed(title="Магазин", description="Здесь вы можете купить:", color=0x80ff00)
        for good in self.goods:
            embed.add_field(name=f"{good.name} - {good.price} монет{write_coin(good.price)}",
                            value=f"{prefix}{good.desc}", inline=True)
        return embed

    def show_sell(self):
        embed = discord.Embed(title="Черный рынок", description="Здесь вы можете продать:", color=0x80ff00)
        for good in self.goods:
            if good.sell_price != 0:
                embed.add_field(name=f"{good.name} - {good.sell_price} монет{write_coin(good.sell_price)}",
                                value=f"{prefix}{'sell' + good.desc[3:]}", inline=True)
        return embed

    def add_good(self, params):
        name = params[0]
        c_name = params[1]
        price = params[2]
        desc = params[3]
        sell_price = params[4]
        if c_name not in self.available:
            good = GoodNotUsed(price, c_name, name, sell_price)
        else:
            good = self.available[c_name]
        good.price = price
        good.desc = desc
        good.name = name
        good.sell_price = sell_price
        self.goods.append(good)
        return good

    def create_good(self, c_name, name, price, sell_price):
        try:
            good = self.available[c_name]
            good.price = price
            good.name = name
            good.sell_price = sell_price
        except KeyError:
            good = GoodNotUsed(price, c_name, name, sell_price)
        self.goods.append(good)
        return good.desc

    def del_good(self, id, c_name):
        good = get(self.goods, c_name=c_name)
        if good:
            self.goods.remove(good)
            database.delete_good(id, c_name)
            return
        raise NotInTheList

    def edit_good(self, id, c_name, name, price, sell_price):
        good = get(self.goods, c_name=c_name)
        try:
            good.name = name
        except AttributeError:
            raise NotInTheList
        good.price = price
        good.sell_price = sell_price
        database.update_good(id, c_name, name, price,good.desc, sell_price)


class Bank:
    def __init__(self, W_Guild):
        self.W_Guild = W_Guild
        self.users = []
        self.last_rob = 0

    @staticmethod
    def calculate_percent(x):
        return round(x*0.9, 2)

    def deposit(self, wallet, x):
        user = self.get_user(wallet)
        try:
            wallet.is_enough(x)
        except NotEnoughMoney:
            raise NotEnoughMoney
        x_cal = self.calculate_percent(x)
        try:
            user.change_bal(x_cal)
        except AttributeError:
            raise WalletDoesntExist
        wallet.change_bal(x*-1)
        return x_cal

    def withdraw(self, wallet, x):
        user = self.get_user(wallet)
        try:
            user.is_enough(x)
        except NotEnoughMoney:
            raise NotEnoughMoney
        try:
            user.change_bal(x*-1)
        except AttributeError:
            raise WalletDoesntExist
        x_cal = self.calculate_percent(x)
        wallet.change_bal(x_cal)
        return x_cal

    def transfer(self, from_, to, x):
        from_ = self.get_user(from_)
        to = self.get_user(to)
        try:
            from_.is_enough(x)
        except AttributeError:
            raise WalletDoesntExist
        except NotEnoughMoney:
            raise NotEnoughMoney
        x_cal = self.calculate_percent(x)
        try:
            to.change_bal(x_cal)
        except AttributeError:
            raise NotInTheList
        from_.change_bal(x*-1)
        return x_cal

    def reg(self, id, wallet):
        if get(self.users, owner=wallet):
            return Forbidden
        user = BankUser(wallet)
        self.users.append(user)
        database.add_bank_user(id, wallet.owner.id)

    def add_user(self, wallet, balance):
        user = BankUser(wallet)
        user.balance = balance
        self.users.append(user)

    def get_user(self, wallet):
        user = get(self.users, owner=wallet)
        return user

    def rob(self, wallet):
        if time.time() - self.last_rob < 3600:
            raise Forbidden
        weights = [1]*1 + [0]*99
        result = random.choice(weights)
        if result:
            money = random.randint(100000, 500000)
            try:
                wallet.change_bal(money)
            except AttrtibuteError:
                raise WalletDoesntExist
            self.last_rob = time.time()
            wallet.last_rob = time.time()
            return money
        wallet.last_rob = time.time()
        return 0


class BankUser:
    def __init__(self, wallet):
        self.balance = 0
        self.owner = wallet

    def change_bal(self, x):
        self.balance += x
        self.balance = round(self.balance, 2)
        self.update()

    def is_enough(self, x):
        if not self.balance - x > -1:
            raise NotEnoughMoney

    def update(self):
        database.update_bank_user(self)


class Good(ABC):
    def __init__(self, price, c_name, name, sell_price, desc=""):
        self.price = price
        self.name = name
        self.desc = desc
        self.c_name = c_name
        self.sell_price = sell_price

    @abstractmethod
    def buy(self, *args):
        pass


class GoodNotUsed(Good):
    def __init__(self, price, c_name, name, sell_price):
        super().__init__(price, c_name, name, sell_price, f"buy {c_name}")

    async def buy(self, wallet, args, ctx):
        try:
            wallet.is_enough(self.price)
        except NotEnoughMoney:
            raise NotEnoughMoney
        except AttributeError:
            raise WalletDoesntExist
        wallet.have.append(self.c_name)
        wallet.change_bal(self.price*-1)
        return self.name

    async def sell(self, wallet, count, ctx):
        if self.sell_price == 0:
            raise Forbidden
        try:
            wallet.do_have(self.c_name)
        except AttributeError:
            raise WalletDoesntExist
        except KeyError:
            raise NotInTheList
        wallet.have.remove(self.c_name)
        wallet.change_bal(self.sell_price)
        return self.name


class ShopRole(Good):
    def __init__(self):
        super().__init__(100, "role", "Роль", "Роль", 0)
        self.forb_roles = []

    async def buy(self, wallet, args, ctx):
        try:
            wallet.is_enough(self.price)
        except NotEnoughMoney:
            raise NotEnoughMoney
        except AttributeError:
            raise WalletDoesntExist
        r, g, b = int(args[-3]) % 256, int(args[-2]) % 256, int(args[-1]) % 256
        colour = discord.Colour.from_rgb(r, g, b)
        name = " ".join(args[:-3])
        if name in self.forb_roles:
            raise Forbidden
        roles = ctx.guild.roles
        role = get(roles, name=name, colour=colour)
        if role:
            await ctx.author.add_roles(role, reason="bought")
        else:
            role = await ctx.guild.create_role(name=name, colour=colour)
            await ctx.author.add_roles(role, reason="bought")
        wallet.change_bal(self.price*-1)
        return self.name

    async def sell(self, wallet, count, ctx):
        raise CantSell

    def add_forb_role(self,id, name):
        self.forb_roles.append(name)
        self.forb_roles = list(set(self.forb_roles))
        database.update_forb_roles(id, str(self.forb_roles))


class ShopLock(Good):
    def __init__(self):
        super().__init__(50, "lock", "Сейф", "Защитит ваши деньги от кражи", 20)

    async def buy(self, wallet, args, ctx):
        try:
            wallet.is_enough(self.price)
        except NotEnoughMoney:
            raise NotEnoughMoney
        except AttributeError:
            raise WalletDoesntExist
        wallet.have.append("lock")
        wallet.change_bal(self.price * -1)
        return self.name

    async def sell(self, wallet, count, ctx):
        try:
            wallet.do_have(self.c_name)
        except AttributeError:
            raise WalletDoesntExist
        except KeyError:
            raise NotInTheList
        wallet.have.remove("lock")
        wallet.change_bal(self.sell_price)
        return self.name


class ShopLockPick(Good):
    def __init__(self):
        super().__init__(160, "lockpick", "Отмычка", "Может взломать сейф", 60)

    async def buy(self, wallet, args, ctx):
        try:
            wallet.is_enough(self.price)
        except NotEnoughMoney:
            raise NotEnoughMoney
        except AttributeError:
            raise WalletDoesntExist
        wallet.have.append("lockpick")
        wallet.change_bal(self.price * -1)
        return self.name

    async def sell(self, wallet, count, ctx):
        try:
            wallet.do_have(self.c_name)
        except AttributeError:
            raise WalletDoesntExist
        except KeyError:
            raise NotInTheList
        wallet.have.remove("lockpick")
        wallet.change_bal(self.sell_price)
        return self.name


class Forbidden(Exception):
    pass


class ShopSecurities(Good):
    def __init__(self):
        super().__init__(200, "securities", "Ценные бумаги, хранящиеся в банке", "Их никто не может украсть", 180)

    async def buy(self, wallet, args, ctx):
        try:
            count=abs(int(args[0]))
        except IndexError:
            count = 1
        except ValueError:
            count = 1
        try:
            wallet.is_enough(self.price*count)
        except NotEnoughMoney:
            raise NotEnoughMoney
        except AttributeError:
            raise WalletDoesntExist
        except NotInTheList:
            raise NotInTheList
        wallet.securities += count
        wallet.change_bal(count*self.price*-1)
        return self.name

    async def sell(self, wallet, count, ctx):
        try:
            if not wallet.securities >= count:
                raise NotInTheList
        except AttributeError:
            raise WalletDoesntExist
        wallet.securities -= count
        wallet.change_bal(self.sell_price*count)
        return self.name



database = MyDataBase()
bot.run('token')

