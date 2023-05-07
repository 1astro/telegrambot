import json
import telebot
import re
from database import Database

# Telegram API KEY (created with BotFather telegram bot)
API_KEY = 'bot api key'
ADMIN_USER_ID = 'your_user_id'
bot = telebot.TeleBot(API_KEY)

# Database Management
database = Database()

# Load bot messages
with open('messages.json', 'r', encoding='utf-8') as file:
    messages = json.load(file)

# Commands
@bot.message_handler(commands=['pizza'])
def start(message):
    bot.send_message(chat_id=message.chat.id, text=messages['welcome_message']['text'], parse_mode='Markdown')

    if str(message.from_user.id) == ADMIN_USER_ID:
        bot.send_message(chat_id=message.chat.id, text=messages['dev_mode']['text'], parse_mode='Markdown')


@bot.message_handler(commands=['menu'])
def menu(message):
    pizzas = database.list_items()

    if len(pizzas) > 0:
        # Iterate over all pizzas
        for pizza_data in pizzas:
            pizza_name = pizza_data[0]
            pizza_description = pizza_data[1]
            pizza_price = pizza_data[3]

            # Create the message text
            message_text = f"*{pizza_name.capitalize()}*\n{pizza_description}\nPrice: ${pizza_price:.2f}\n\nTo order, use the command /{pizza_name}"

            # Send the message
            bot.send_message(chat_id=message.chat.id, text=message_text, parse_mode='Markdown')
    else:
        # No pizzas avaiable
        bot.send_message(chat_id=message.chat.id, text='There are no pizzas available.', parse_mode='Markdown')

# Checks if user is an admin so admin commands can be accessed
def dev_handler(func):
    def wrapper(message):
        print(str(message.from_user.id), ADMIN_USER_ID, str(message.from_user.id) != ADMIN_USER_ID)
        if str(message.from_user.id) != ADMIN_USER_ID:
            bot.reply_to(message, "Sorry, you are not authorized to use this command.")
        else:
            return func(message)
        
    return wrapper

@bot.message_handler(commands=['add'])
@dev_handler
def add(message):
    try:
        args = re.match(r'/add\s+name\((\S+)\)\s+description\((.+)\)\s+quantity\((\d+)\)\s+price\((\d+(?:\.\d+)?)\)', message.text)
        args = [args.group(1), args.group(2), int(args.group(3)), args.group(4)]

        response = database.add_item(args)

        if response:
            select_handler(args[0], args)

            bot.send_message(chat_id=message.chat.id, text='Pizza has been added successfully!', parse_mode='Markdown')
        else:
            bot.send_message(chat_id=message.chat.id, text='Failed to add pizza! It appears that the pizza you requested to add does not fit in the command or already exists.', parse_mode='Markdown')
    except:
        pass

@bot.message_handler(commands=['edit'])
@dev_handler
def edit(message):
    args = list(message.text.replace(message.text.split(' ')[0], '').split(' ')[1:])

    response = database.update_item(*args)

    if response:
        bot.send_message(chat_id=message.chat.id, text='Pizza has been edited successfully!', parse_mode='Markdown')
    else:
        bot.send_message(chat_id=message.chat.id, text='Failed to edit pizza! It appears that the pizza you requested to add does not exist. Please ensure you have entered the correct pizza details and try again.', parse_mode='Markdown')

@bot.message_handler(commands=['remove'])
@dev_handler
def remove(message):
    name = message.text.replace(message.text.split(' ')[0], '').split(' ')[1:][0]
    
    response = database.remove_item(name)

    if response:
        bot.send_message(chat_id=message.chat.id, text='Pizza has been removed successfully!', parse_mode='Markdown')
    else:
        bot.send_message(chat_id=message.chat.id, text='Failed to remove pizza! It appears that the pizza you requested to remove does not exist. Please ensure you have entered the correct pizza details and try again.', parse_mode='Markdown')

@bot.message_handler(commands=['list'])
@dev_handler
def list_pizzas(message):
    for pizza_data in database.list_items():
        pizza_name = pizza_data[0]
        pizza_description = pizza_data[1]
        pizza_quantity = pizza_data[2]
        pizza_price = pizza_data[3]

        # Create the message text
        message_text = f"*{pizza_name.capitalize()}*\n{pizza_description}\nQuantity: {pizza_quantity}\nPrice: ${pizza_price:.2f}"

        # Send the message
        bot.send_message(chat_id=message.chat.id, text=message_text, parse_mode='Markdown')
        bot.send_message(chat_id=message.chat.id, text='\n\nTo remove type /remove *pizza name*', parse_mode='Markdown')

@bot.message_handler(commands=['info'])
@dev_handler
def info(message):
    bot.send_message(chat_id=message.chat.id, text=messages['info']['text'], parse_mode='Markdown')

def select_handler(pizza_name, pizza_data):
    bot_commands = [(pizza[0], '') for pizza in database.list_items() if pizza[2] > 0]

    @bot.message_handler(commands=[pizza_name])
    def select_pizza(message):
        nonlocal bot_commands
        quantity = pizza_data[2]
        price = pizza_data[3]
        
        if quantity > 0:
            bot.send_message(chat_id=message.chat.id, text=messages['order_message']['success'].format(pizza_name=pizza_name, pizza_price=price), parse_mode='Markdown')
            database.update_item(pizza_name, 'quantity', quantity)

            if quantity - 1 == 0:
                database.remove_item(pizza_name)
                bot_commands = [(pizza[0], '') for pizza in database.list_items() if pizza[2] > 0]
                bot.set_my_commands(bot_commands)
            pizza_data[2] -= 1

            print(f'Sold {pizza_name} for {price}, quantity left: {pizza_data[2]}')
        else:
            bot.send_message(chat_id=message.chat.id, text=messages['order_message']['fail'], parse_mode='Markdown')

            if pizza_name in bot_commands:
                bot_commands.remove(pizza_name)
                bot.set_my_commands(bot_commands)

    return select_pizza


# Load select pizza commands
for pizza_data in database.list_items():
    handler = select_handler(pizza_data[0], pizza_data)

bot.polling()