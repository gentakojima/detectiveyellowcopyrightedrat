#!/usr/bin/env python3.3
# -*- coding: UTF-8 -*-

#
# Command list for @botfather
# help - Muestra la ayuda
# list - Lista los gimnasios conocidos
# raid - Crea una incursión
#

from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, Filters
from telegram import ChatAction, InlineKeyboardButton, InlineKeyboardMarkup
import re
import googlemaps
import time
import logging
import requests
from io import StringIO
import csv
import signal
from os.path import expanduser
import os
import telegram
import base64
import configparser
import pymysql.cursors
from threading import Thread

from storagemethods import saveSpreadsheet, savePlaces, getSpreadsheet, getPlaces, saveUser, getUser, refreshUsername, saveRaid, getRaid, raidVoy, raidPlus1, raidEstoy, raidNovoy, getCreadorRaid, getRaidbyMessage, getPlace, deleteRaid
from supportmethods import is_admin, extract_update_info, delete_message_timed, pokemonlist, update_message

def cleanup(signum, frame):
  if db != None:
    db.close()
  exit(0)
signal.signal(signal.SIGINT, cleanup)

logging.basicConfig(filename='/tmp/detectivepikachubot.log',level=logging.DEBUG)

configdir = expanduser("~") + "/.config/detectivepikachu"
configfile = configdir + "/config.ini"

if not os.path.exists(configdir):
  os.makedirs(configdir)
if not os.path.exists(configfile):
  f = open(configfile, "w")
  f.write("[database]\nhost=localhost\nport=3306\nuser=detectivepikachu\npassword=detectivepikachu\nschema=detectivepikachu\n[telegram]\ntoken=xxx\n[googlemaps]\nkey=xxx\n")
  f.close()
  print("Se acaba de crear el fichero de configuración en «»%s».\nComprueba la configuración y vuelve a ejecutarme." % configfile)
  exit(1)

config = configparser.ConfigParser()
config.read(configfile)

try:
  db = pymysql.connect(host=config["database"]["host"], user=config["database"]["user"], password=config["database"]["password"], db=config["database"]["schema"], charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor)
except:
  print("No se puede conectar a la base de datos.\nComprueba el fichero de configuración!")
  exit(1)

updater = Updater(token=config["telegram"]["token"])
dispatcher = updater.dispatcher
gmaps = googlemaps.Client(key=config["googlemaps"]["key"])

def start(bot, update):
  bot.sendMessage(chat_id=update.message.chat_id, text="Aquí tienes información de todo lo que hago: http://telegra.ph/Detective-Pikachu-09-28\nDudas e insultos a @gentakojima.")

def setspreadsheet(bot, update, args=None):
  (chat_id, chat_type, user_id, text, message) = extract_update_info(update)
  if not is_admin(chat_id, user_id, bot):
    return

  if args == None or len(args)!=1:
    bot.sendMessage(chat_id=chat_id, text="Debes pasarme la URL de la Google Spreadsheet como un único parámetro.")
    return

  if chat_type == "private":
    bot.sendMessage(chat_id=chat_id, text="Solo funciono en canales y grupos :(")
    return

  m = re.search('docs.google.com/.*spreadsheets/d/([a-zA-Z0-9_-]+)', args[0], flags=re.IGNORECASE)
  if m == None:
    bot.sendMessage(chat_id=update.message.chat_id, text="Vaya, no he reconocido esa URL... %s" % args[0])
  else:
    spreadsheet_id = m.group(1)
    saveSpreadsheet(chat_id, spreadsheet_id, db)
    bot.sendMessage(chat_id=update.message.chat_id, text="Establecida spreadsheet con ID %s.\nRecuerda que debes hacer /refresh para volver a cargar los gimnasios!" % spreadsheet_id )

def refresh(bot, update, args=None):
  (chat_id, chat_type, user_id, text, message) = extract_update_info(update)
  if not is_admin(chat_id, user_id, bot):
    return

  spreadsheet_id = getSpreadsheet(chat_id, db)
  if spreadsheet_id == None:
    bot.sendMessage(chat_id=chat_id, text="No estoy configurado en este grupo :( Debes configurar primero el spreadsheet. Pregunta a @gentakojima")
    return

  bot.sendMessage(chat_id=update.message.chat_id, text="Refrescando lista de gimnasios...")
  response = requests.get("https://docs.google.com/spreadsheet/ccc?key=%s&output=csv" % spreadsheet_id )
  if response.status_code == 200:
    place = []
    f = StringIO(response.content.decode('utf-8'))
    csvreader = csv.reader(f, delimiter=',', quotechar='"')
    counter = 0
    for row in csvreader:
      names = row[3].split(",")
      for i,r in enumerate(names):
        names[i] = names[i].strip()
      place.append({"desc":row[0],"latitude":row[1],"longitude":row[2],"names":names});
      counter = counter + 1

    if counter > 1:
      savePlaces(chat_id, place, db)
      bot.sendMessage(chat_id=update.message.chat_id, text="Cargados %i gimnasios!" % counter)
    else:
      bot.sendMessage(chat_id=update.message.chat_id, text="No se han podido cargar los gimnasios! ¿Seguro que está en el formato correcto?")
  else:
    bot.sendMessage(chat_id=update.message.chat_id, text="Error cargando spreadsheet. ¿Seguro que está pública?")

def registerOak(bot, update):
  (chat_id, chat_type, user_id, text, message) = extract_update_info(update)
  this_date = message.date
  forward_date = message.forward_date
  user_username = message.from_user.username

  if (this_date - forward_date).total_seconds() < 120:
    bot.sendMessage(chat_id=chat_id, text="¡Recibido el mensaje de @profesoroak_bot! Vamos a ver...")
    m = re.search("@([a-zA-Z0-9]+), eres (Rojo|Azul|Amarillo) L([0-9]{1,2})[ .]",text, flags=re.IGNORECASE)
    if m != None:
      m2 = re.search("✅",text, flags=re.IGNORECASE)
      if m2 != None:
          thisuser = {}
          thisuser["id"] = user_id
          thisuser["team"] = m.group(2)
          thisuser["level"] = m.group(3)
          thisuser["username"] = user_username
          bot.sendMessage(chat_id=chat_id, text="He reconocido lo siguiente:\n - Equipo: %s\n - Nivel: %s" % (thisuser["team"],thisuser["level"]))
          saveUser(thisuser, db)
      else:
          bot.sendMessage(chat_id=chat_id, text="Parece que no estás validado, no puedo aceptar tu nivel y equipo hasta que te valides.")
    else:
      bot.sendMessage(chat_id=chat_id, text="No he reconocido ese mensaje de @profesoroak_bot... ¿Seguro que le has preguntado `Quién soy?` y no otra cosa?")
  else:
    bot.sendMessage(chat_id=chat_id, text="Ese mensaje es demasiado antiguo. Debes reenviarme un mensaje reciente!")


def processMessage(bot, update):
  (chat_id, chat_type, user_id, text, message) = extract_update_info(update)
  try:
    forward_id = message.forward_from.id
  except:
    forward_id = None

  if chat_type == "private" and forward_id == 201760961:
    registerOak(bot, update)
    return

  m = re.search('(crear|nueva) (raid|incursión|incursion|#raid).* en (.+)', text, flags=re.IGNORECASE)
  m2 = re.search('(dónde|donde).*(gimnasio|gym|gim) (.+)$', text, flags=re.IGNORECASE)
  m3 = re.search('(#noloc|#nl)', text, flags=re.IGNORECASE)
  if (m != None or m2 != None) and m3 == None:
    if chat_type == "private":
      bot.sendMessage(chat_id=chat_id, text="Solo funciono en canales y grupos")
      return
    gyms = getPlaces(chat_id, db)
    if len(gyms)==0:
      bot.sendMessage(chat_id=chat_id, text="No estoy configurado en este grupo")
      return
    if m != None:
      place = m.group(3)
    else:
      place = m2.group(3)
    logging.info("Buscando sitio \"%s\"..." % place)
    chosen = None

    for p in gyms:
      for n in p["names"]:
        logging.debug("Matching '%s' with '%s'..." % (n,place))
        if re.search(n,place,flags=re.IGNORECASE) != None:
          logging.debug("Matched '%s'!!" % n)
          chosen = p
          break
      if chosen != None:
        break
    if chosen != None:
      bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
      logging.info("Encontrado: %s" % chosen["desc"])
      reverse_geocode_result = gmaps.reverse_geocode((chosen["latitude"], chosen["longitude"]))
      address = reverse_geocode_result[0]["formatted_address"]
      time.sleep(4)
      bot.sendVenue(chat_id=chat_id, latitude=chosen["latitude"], longitude=chosen["longitude"], title=chosen["desc"], address=address)
    else:
      logging.info("Oops! No encontrado")

def list(bot, update):
  (chat_id, chat_type, user_id, text, message) = extract_update_info(update)
  if chat_type == "private":
    bot.sendMessage(chat_id=chat_id, text="Solo funciono en canales y grupos")
    return

  gyms = getPlaces(chat_id, db)
  if len(gyms)==0:
    bot.sendMessage(chat_id=chat_id, text="No estoy configurado en este grupo")
    return
  output = "Lista de gimnasios conocidos (%i):" % len(gyms)
  bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
  for p in gyms:
    output = output + ("\n - %s" % p["desc"])
  bot.sendMessage(chat_id=chat_id, text=output)

keyboard = [[InlineKeyboardButton("🙋 ¡Voy!", callback_data='voy'), InlineKeyboardButton("👭 +1", callback_data='plus1'), InlineKeyboardButton("🙅 No voy", callback_data='novoy')],
              [InlineKeyboardButton("👀 ¡Ya estoy allí!", callback_data='estoy'),InlineKeyboardButton("🗺 Ubicación", callback_data='ubicacion')]]
reply_markup = InlineKeyboardMarkup(keyboard)

def raid(bot, update, args=None):
  (chat_id, chat_type, user_id, text, message) = extract_update_info(update)
  user_username = message.from_user.username

  thisuser = refreshUsername(user_id, user_username, db)

  current_raid = {}

  if str(chat_id) != "-1001145756055" and str(chat_id) != "-1001131268439" and str(chat_id) != "-1001134809812":
      bot.sendMessage(chat_id=chat_id, text="Las incursiones todavía están en desarrollo y solo se permiten en grupos preaprobados. Habla con @gentakojima.",parse_mode=telegram.ParseMode.MARKDOWN)

  try:
    bot.deleteMessage(chat_id=chat_id,message_id=update.message.message_id)
  except:
    pass

  if thisuser["username"] == None:
      sent_message = bot.sendMessage(chat_id=chat_id, text="¡Lo siento, pero no puedes crear una incursión si no tienes definido un alias!\nEn Telegram, ve a *Ajustes* y selecciona la opción *Alias* para establecer un alias.\n\n_(Este mensaje se borrará en unos segundos)_", parse_mode=telegram.ParseMode.MARKDOWN)
      t = Thread(target=delete_message_timed, args=(chat_id, sent_message.message_id, 15, bot))
      t.start()
      return

  if args == None or len(args)<3:
    sent_message = bot.sendMessage(chat_id=chat_id, text="¡No te he entendido!\nDebes seguir el siguiente formato:\n`/raid <pokemon> <hora> <gimnasio>`\nEjemplo: `/raid pikachu 12:00 la lechera`\n\nEl mensaje original era:\n`%s`\n\n_(Este mensaje se borrará en unos segundos)_" % text, parse_mode=telegram.ParseMode.MARKDOWN)
    t = Thread(target=delete_message_timed, args=(chat_id, sent_message.message_id, 20, bot))
    t.start()
    return

  current_raid["username"] = thisuser["username"]

  if args[0] == "de":
    del args[0]

  for pokemon in pokemonlist:
    m = re.match("^%s$" % pokemon, args[0], flags=re.IGNORECASE)
    if m != None:
      current_raid["pokemon"] = pokemon
      break

  if not "pokemon" in current_raid.keys():
    sent_message = bot.sendMessage(chat_id=chat_id, text="¡No he entendido el Pokémon! ¿Lo has escrito bien?\nRecuerda que debes seguir el siguiente formato:\n`/raid <pokemon> <hora> <gimnasio>`\nEjemplo: `/raid pikachu 12:00 la lechera`\n\nEl mensaje original era:\n`%s`\n\n_(Este mensaje se borrará en unos segundos)_" % text,parse_mode=telegram.ParseMode.MARKDOWN)
    t = Thread(target=delete_message_timed, args=(chat_id, sent_message.message_id, 15, bot))
    t.start()
    return

  del args[0]
  if args[0] == "a" and args[1] == "las":
    del args[0]
    del args[0]

  m = re.match("([0-9]{1,2})[:.]?([0-9]{0,2})h?", args[0], flags=re.IGNORECASE)
  if m != None:
    hour = str(m.group(1))
    minute = m.group(2) or "00"
    if int(hour)<0 or int(hour)>24 or int(minute)<0 or int(minute)>59:
        sent_message = bot.sendMessage(chat_id=chat_id, text="¡No he entendido la hora! ¿La has escrito bien?\nRecuerda que debes seguir el siguiente formato:\n`/raid <pokemon> <hora> <gimnasio>`\nEjemplo: `/raid pikachu 12:00 la lechera`\n\nEl mensaje original era:\n`%s`\n\n_(Este mensaje se borrará en unos segundos)_" % text,parse_mode=telegram.ParseMode.MARKDOWN)
        t = Thread(target=delete_message_timed, args=(chat_id, sent_message.message_id, 15, bot))
        t.start()
        return
  else:
    sent_message = bot.sendMessage(chat_id=chat_id, text="¡No he entendido la hora! ¿La has escrito bien?\nRecuerda que debes seguir el siguiente formato:\n`/raid <pokemon> <hora> <gimnasio>`\nEjemplo: `/raid pikachu 12:00 la lechera`\n\nEl mensaje original era:\n`%s`\n\n_(Este mensaje se borrará en unos segundos)_" % text,parse_mode=telegram.ParseMode.MARKDOWN)
    t = Thread(target=delete_message_timed, args=(chat_id, sent_message.message_id, 15, bot))
    t.start()
    return
  current_raid["time"] = "%02d:%02d" % (int(hour),int(minute))

  del args[0]
  if args[0] == "en":
    del args[0]

  current_raid["gimnasio_text"] = ""
  for i in range (0,len(args)):
      current_raid["gimnasio_text"] = current_raid["gimnasio_text"] + "%s " % args[i]
  current_raid["gimnasio_text"] = current_raid["gimnasio_text"].strip()

  chosengym = None
  gyms = getPlaces(chat_id, db)
  for p in gyms:
    for n in p["names"]:
      if re.search(n,current_raid["gimnasio_text"],flags=re.IGNORECASE) != None:
        chosengym = p
        break
    if chosengym != None:
      break
  if chosengym != None:
    current_raid["gimnasio_text"] = chosengym["desc"]
    current_raid["gimnasio_id"] = chosengym["id"]

  send_text = "Incursión de *%s* a las *%s* en *%s*\nCreada por @%s\nEntrenadores apuntados (0):" % (current_raid["pokemon"], current_raid["time"], current_raid["gimnasio_text"], current_raid["username"])
  sent_message = bot.sendMessage(chat_id=chat_id, text=send_text,parse_mode=telegram.ParseMode.MARKDOWN,reply_markup=reply_markup)

  current_raid["grupo_id"] = chat_id
  current_raid["usuario_id"] = user_id
  current_raid["message"] = sent_message.message_id

  current_raid["id"] = saveRaid(current_raid, db)

  bot.send_message(chat_id=user_id, text="Para editar o borrar la incursión de *%s* a las *%s* en *%s* debes poner los siguientes comandos por privado, cambiando el dato que aparece de ejemplo por el deseado\n\nEl número *%s* es un identificador que tienes que dejar intacto para identificar a la incursión.\n\n🕒 Para *cambiar la hora*:\n`/cambiarhora %s %s`\n\n🗺 Para *cambiar el gimnasio*:\n`/cambiargimnasio %s %s`\n\n👿 Para *cambiar el Pokémon*:\n`/cambiarpokemon %s %s`\n\n❌ Para *borrar la incursión*:\n`/borrar %s`" % (current_raid["pokemon"], current_raid["time"], current_raid["gimnasio_text"], current_raid["id"], current_raid["id"], current_raid["time"], current_raid["id"], current_raid["gimnasio_text"], current_raid["id"], current_raid["pokemon"], current_raid["id"]), parse_mode=telegram.ParseMode.MARKDOWN)

def cambiarhora(bot, update, args=None):
    (chat_id, chat_type, user_id, text, message) = extract_update_info(update)
    user_username = message.from_user.username

    thisuser = refreshUsername(user_id, user_username, db)

    if chat_type != "private":
        sent_message = bot.sendMessage(chat_id=chat_id, text="¡El comando de cambiar hora solo funciona en privado!")
        t = Thread(target=delete_message_timed, args=(chat_id, sent_message.message_id, 10, bot))
        t.start()
        return

    if len(args)<2 or not str(args[0]).isnumeric():
        bot.sendMessage(chat_id=chat_id, text="¡No he reconocido los datos que me envías!\nPulsa el botón de *Editar/Borrar* en la incursión y copia y pega el comando que pone de ejemplo, que lleva incorporados ya los datos.",parse_mode=telegram.ParseMode.MARKDOWN)
        return

    raid_id = args[0]
    raid = getRaid(raid_id, db)
    if raid != None:
        if raid["usuario_id"] == user_id:
            if args[1] == raid["time"]:
                bot.sendMessage(chat_id=chat_id, text="¡La incursión ya está puesta para esa hora!", parse_mode=telegram.ParseMode.MARKDOWN)
            else:
                m = re.match("([0-9]{1,2})[:.]?([0-9]{0,2})h?", args[1], flags=re.IGNORECASE)
                if m != None:
                    hour = str(m.group(1))
                    minute = m.group(2) or "00"
                    if int(hour)<0 or int(hour)>24 or int(minute)<0 or int(minute)>59:
                        bot.sendMessage(chat_id=chat_id, text="¡No he entendido la hora! ¿La has escrito bien?\nDebe seguir el formato `hh:mm`.\nEjemplo: `12:15`", parse_mode=telegram.ParseMode.MARKDOWN)
                    else:
                        raid["time"] = "%02d:%02d" % (int(hour),int(minute))
                        saveRaid(raid, db)
                        update_message(raid["grupo_id"], raid["message"], reply_markup, db, bot)
                        bot.sendMessage(chat_id=chat_id, text="¡Se ha cambiado la hora a las *%s* correctamente!" % raid["time"], parse_mode=telegram.ParseMode.MARKDOWN)
                else:
                  bot.sendMessage(chat_id=chat_id, text="¡No he entendido la hora! ¿La has escrito bien?\nDebe seguir el formato `hh:mm`.\nEjemplo: `12:15`", parse_mode=telegram.ParseMode.MARKDOWN)
        else:
            bot.sendMessage(chat_id=chat_id, text="¡No tienes permiso para editar esta incursión!",parse_mode=telegram.ParseMode.MARKDOWN)
    else:
        bot.sendMessage(chat_id=chat_id, text="¡Esa incursión no existe!",parse_mode=telegram.ParseMode.MARKDOWN)

def cambiargimnasio(bot, update, args=None):
    (chat_id, chat_type, user_id, text, message) = extract_update_info(update)
    user_username = message.from_user.username

    thisuser = refreshUsername(user_id, user_username, db)

    if chat_type != "private":
        sent_message = bot.sendMessage(chat_id=chat_id, text="¡El comando de cambiar gimnasio solo funciona en privado!")
        t = Thread(target=delete_message_timed, args=(chat_id, sent_message.message_id, 10, bot))
        t.start()
        return

    if len(args)<2 or not str(args[0]).isnumeric():
        bot.sendMessage(chat_id=chat_id, text="¡No he reconocido los datos que me envías!\nPulsa el botón de *Editar/Borrar* en la incursión y copia y pega el comando que pone de ejemplo, que lleva incorporados ya los datos.",parse_mode=telegram.ParseMode.MARKDOWN)
        return

    new_gymtext = ""
    for i in range (1,len(args)):
        new_gymtext = new_gymtext + "%s " % args[i]
    new_gymtext = new_gymtext.strip()

    raid_id = args[0]
    raid = getRaid(raid_id, db)
    if raid != None:
        if raid["usuario_id"] == user_id:
            if new_gymtext == raid["gimnasio_text"]:
                bot.sendMessage(chat_id=chat_id, text="¡La incursión ya está puesta en ese gimnasio!", parse_mode=telegram.ParseMode.MARKDOWN)
            else:
                chosengym = None
                gyms = getPlaces(raid["grupo_id"], db)
                for p in gyms:
                    for n in p["names"]:
                        if re.search(n, new_gymtext, flags=re.IGNORECASE) != None:
                            chosengym = p
                            break
                    if chosengym != None:
                        break
                if chosengym != None:
                    raid["gimnasio_text"] = chosengym["desc"]
                    raid["gimnasio_id"] = chosengym["id"]
                    saveRaid(raid, db)
                    update_message(raid["grupo_id"], raid["message"], reply_markup, db, bot)
                    bot.sendMessage(chat_id=chat_id, text="¡Se ha cambiado el gimnasio a *%s* correctamente!" % raid["gimnasio_text"], parse_mode=telegram.ParseMode.MARKDOWN)
                else:
                    raid["gimnasio_text"] = new_gymtext
                    raid["gimnasio_id"] = None
                    saveRaid(raid, db)
                    update_message(raid["grupo_id"], raid["message"], reply_markup, db, bot)
                    bot.sendMessage(chat_id=chat_id, text="¡No he encontrado el gimnasio, pero lo he actualizado igualmente en la incursión a *%s*" % raid["gimnasio_text"], parse_mode=telegram.ParseMode.MARKDOWN)
        else:
            bot.sendMessage(chat_id=chat_id, text="¡No tienes permiso para editar esta incursión!",parse_mode=telegram.ParseMode.MARKDOWN)
    else:
        bot.sendMessage(chat_id=chat_id, text="¡Esa incursión no existe!",parse_mode=telegram.ParseMode.MARKDOWN)

def cambiarpokemon(bot, update, args=None):
    (chat_id, chat_type, user_id, text, message) = extract_update_info(update)
    user_username = message.from_user.username

    thisuser = refreshUsername(user_id, user_username, db)

    if chat_type != "private":
        sent_message = bot.sendMessage(chat_id=chat_id, text="¡El comando de cambiar Pokémon solo funciona en privado!")
        t = Thread(target=delete_message_timed, args=(chat_id, sent_message.message_id, 10, bot))
        t.start()
        return


    if len(args)<2 or not str(args[0]).isnumeric():
        bot.sendMessage(chat_id=chat_id, text="¡No he reconocido los datos que me envías!\nPulsa el botón de *Editar/Borrar* en la incursión y copia y pega el comando que pone de ejemplo, que lleva incorporados ya los datos.",parse_mode=telegram.ParseMode.MARKDOWN)
        return

    raid_id = args[0]
    raid = getRaid(raid_id, db)
    if raid != None:
        if raid["usuario_id"] == user_id:
            if args[1] == raid["pokemon"]:
                bot.sendMessage(chat_id=chat_id, text="¡Ese ya es el Pokémon actual de la incursión!", parse_mode=telegram.ParseMode.MARKDOWN)
            else:
                for pokemon in pokemonlist:
                    m = re.match("^%s$" % pokemon, args[1], flags=re.IGNORECASE)
                    if m != None:
                        raid["pokemon"] = pokemon
                        saveRaid(raid, db)
                        update_message(raid["grupo_id"], raid["message"], reply_markup, db, bot)
                        bot.sendMessage(chat_id=chat_id, text="¡Se ha cambiado el Pokémon a *%s* correctamente!" % raid["pokemon"], parse_mode=telegram.ParseMode.MARKDOWN)
                        break
                else:
                    bot.sendMessage(chat_id=chat_id, text="¡No he reconocido ese Pokémon!",parse_mode=telegram.ParseMode.MARKDOWN)
        else:
            bot.sendMessage(chat_id=chat_id, text="¡No tienes permiso para editar esta incursión!",parse_mode=telegram.ParseMode.MARKDOWN)
    else:
        bot.sendMessage(chat_id=chat_id, text="¡Esa incursión no existe!",parse_mode=telegram.ParseMode.MARKDOWN)

def borrar(bot, update, args=None):
    (chat_id, chat_type, user_id, text, message) = extract_update_info(update)
    user_username = message.from_user.username

    thisuser = refreshUsername(user_id, user_username, db)

    if chat_type != "private":
        sent_message = bot.sendMessage(chat_id=chat_id, text="¡El comando de borrar incursión solo funciona en privado!")
        t = Thread(target=delete_message_timed, args=(chat_id, sent_message.message_id, 10, bot))
        t.start()
        return

    raid_id = args[0]
    if not str(raid_id).isnumeric():
        bot.sendMessage(chat_id=chat_id, text="¡No he reconocido los datos que me envías!\nPulsa el botón de *Editar/Borrar* en la incursión y copia y pega el comando que pone de ejemplo, que lleva incorporados ya los datos.",parse_mode=telegram.ParseMode.MARKDOWN)
        return

    raid = getRaid(raid_id, db)
    if raid != None:
        if raid["usuario_id"] == user_id:
            if deleteRaid(raid["id"], db):
                bot.deleteMessage(chat_id=raid["grupo_id"],message_id=raid["message"])
                bot.sendMessage(chat_id=chat_id, text="Se ha borrado la incursión correctamente.",parse_mode=telegram.ParseMode.MARKDOWN)
        else:
            bot.sendMessage(chat_id=chat_id, text="¡No tienes permiso para borrar esta incursión!",parse_mode=telegram.ParseMode.MARKDOWN)
    else:
        bot.sendMessage(chat_id=chat_id, text="¡Esa incursión no existe!",parse_mode=telegram.ParseMode.MARKDOWN)

def raidbutton(bot, update):
  query = update.callback_query
  original_text = query.message.text
  data = query.data
  user_id = query.from_user.id
  user_username = query.from_user.username
  chat_id = query.message.chat.id
  message_id = query.message.message_id

  thisuser = refreshUsername(user_id, user_username, db)

  update_text = False

  if (data == "voy" or data == "plus1" or data == "novoy" or data == "estoy") \
    and (thisuser["username"] == None or thisuser["username"] == "None"):
    bot.answerCallbackQuery(text="No puedes unirte a una incursión si no tienes definido un alias.\nEn Telegram, ve a 'Ajustes' y selecciona la opción 'Alias'.", show_alert="true", callback_query_id=update.callback_query.id)
    return

  if data == "voy":
      if raidVoy(chat_id, message_id, user_id, db) != False:
          bot.answerCallbackQuery(text="¡Te has apuntado! Si vas con más gente, pulsa +1", callback_query_id=update.callback_query.id)
          update_text = True
  elif data == "plus1":
      result = raidPlus1(chat_id, message_id, user_id, db)
      if result != False:
          bot.answerCallbackQuery(text="¡Te has apuntado con %i más! Si sois más, pulsa +1" % result, callback_query_id=update.callback_query.id)
          update_text = True
      else:
          bot.answerCallbackQuery(text="No puedes apuntarte con más de 6 personas", callback_query_id=update.callback_query.id)
  elif data == "novoy":
      if raidNovoy(chat_id, message_id, user_id, db) != False:
          bot.answerCallbackQuery(text="Te has desapuntado de la incursión", callback_query_id=update.callback_query.id)
          update_text = True
  elif data == "estoy":
      if raidEstoy(chat_id, message_id, user_id, db) != False:
          bot.answerCallbackQuery(text="Has marcardo que has llegado a la incursión", callback_query_id=update.callback_query.id)
          update_text = True

  if update_text == True:
      update_message(chat_id, message_id, reply_markup, db, bot)

  if data=="ubicacion":
    raid = getRaidbyMessage(chat_id, message_id, db)
    if raid["gimnasio_id"] != None:
      try:
        gym = getPlace(raid["gimnasio_id"], db)
        if gym != None:
          bot.answerCallbackQuery(text="Te envío la ubicación por privado", callback_query_id=update.callback_query.id)
          reverse_geocode_result = gmaps.reverse_geocode((gym["latitude"], gym["longitude"]))
          address = reverse_geocode_result[0]["formatted_address"]
          bot.sendVenue(chat_id=user_id, latitude=gym["latitude"], longitude=gym["longitude"], title=gym["desc"], address=address)
        else:
          bot.answerCallbackQuery(text="La ubicación es desconocida", callback_query_id=update.callback_query.id)
      except:
        bot.answerCallbackQuery(text="Para que te pueda enviar la ubicación, debes abrir un privado antes con @detectivepikachubot y pulsar en 'Iniciar'", callback_query_id=update.callback_query.id, show_alert="true")
    else:
      bot.answerCallbackQuery(text="La ubicación es desconocida", callback_query_id=update.callback_query.id)


start_handler = CommandHandler('start', start)
help_handler = CommandHandler('help', start)
list_handler = CommandHandler('list', list)
message_handler = MessageHandler(Filters.text, processMessage)
setspreadsheet_handler = CommandHandler('setspreadsheet', setspreadsheet, pass_args=True)
refresh_handler = CommandHandler('refresh', refresh)
raid_handler = CommandHandler('raid', raid, pass_args=True)
cambiarhora_handler = CommandHandler('cambiarhora', cambiarhora, pass_args=True)
cambiargimnasio_handler = CommandHandler('cambiargimnasio', cambiargimnasio, pass_args=True)
cambiarpokemon_handler = CommandHandler('cambiarpokemon', cambiarpokemon, pass_args=True)
borrar_handler = CommandHandler('borrar', borrar, pass_args=True)
raidbutton_handler = CallbackQueryHandler(raidbutton)

dispatcher.add_handler(start_handler)
dispatcher.add_handler(help_handler)
dispatcher.add_handler(message_handler)
dispatcher.add_handler(list_handler)
dispatcher.add_handler(setspreadsheet_handler)
dispatcher.add_handler(refresh_handler)
dispatcher.add_handler(raid_handler)
dispatcher.add_handler(cambiarhora_handler)
dispatcher.add_handler(cambiargimnasio_handler)
dispatcher.add_handler(cambiarpokemon_handler)
dispatcher.add_handler(borrar_handler)
dispatcher.add_handler(raidbutton_handler)


updater.start_polling()
