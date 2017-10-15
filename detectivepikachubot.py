#!/usr/bin/env python3.3
# -*- coding: UTF-8 -*-

#
# Command list for @botfather
# help - Muestra la ayuda
# raid - Crea una incursión nueva
# alerts - Configura alertas de incursiones
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
from unidecode import unidecode

from storagemethods import saveGroup, savePlaces, getGroup, getPlaces, saveUser, getUser, refreshUsername, saveRaid, getRaid, raidVoy, raidPlus1, raidEstoy, raidNovoy, getCreadorRaid, getRaidbyMessage, getPlace, deleteRaid, getRaidPeople, cancelRaid, getLastRaids, refreshDb, getPlacesByLocation, getAlerts, addAlert, delAlert, clearAlerts, getGroupsByUser
from supportmethods import is_admin, extract_update_info, delete_message_timed, pokemonlist, update_message, end_old_raids, send_alerts, error_callback, ensure_escaped

def cleanup(signum, frame):
    logging.info("Closing bot!")
    exit(0)
signal.signal(signal.SIGINT, cleanup)

logging.basicConfig(filename='/tmp/detectivepikachubot.log', format='%(asctime)s %(message)s', level=logging.DEBUG)
logging.info("--------------------- Starting bot! -----------------------")

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

refreshDb()
config = configparser.ConfigParser()
config.read(configfile)

updater = Updater(token=config["telegram"]["token"])
dispatcher = updater.dispatcher
dispatcher.add_error_handler(error_callback)
gmaps = googlemaps.Client(key=config["googlemaps"]["key"])

def start(bot, update):
    logging.debug("detectivepikachubot:start: %s %s" % (bot, update))
    bot.sendMessage(chat_id=update.message.chat_id, text="📖 ¡Echa un vistazo a <a href='http://telegra.ph/Detective-Pikachu-09-28'>la ayuda</a> para enterarte de todas las funciones!\n\n🆕 <b>Crear incursión</b>\n<code>/raid Suicune 12:00 Alameda</code>\n\n❄️🔥⚡️ <b>Registrar nivel/equipo</b>\nPregunta <code>quién soy?</code> a @profesoroak_bot y reenvíame la respuesta.\n\n⏰ <b>Configurar alertas (BETA)</b>\nEscríbeme por privado el comando <code>/alerts</code>.", parse_mode=telegram.ParseMode.HTML, disable_web_page_preview=True)

def setspreadsheet(bot, update, args=None):
  logging.debug("detectivepikachubot:setspreadsheet: %s %s %s" % (bot, update, args))
  (chat_id, chat_type, user_id, text, message) = extract_update_info(update)
  chat_title = message.chat.title

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
    group = getGroup(chat_id)
    if group == None:
        group = {"id":chat_id, "title":chat_title, "spreadsheet":spreadsheet_id}
    else:
        group["title"] = chat_title
        group["spreadsheet"] = spreadsheet_id
    saveGroup(group)
    bot.sendMessage(chat_id=update.message.chat_id, text="Establecida spreadsheet con ID %s.\nRecuerda que debes hacer /refresh para volver a cargar los gimnasios!" % spreadsheet_id )

def refresh(bot, update, args=None):
  logging.debug("detectivepikachubot:refresh: %s %s %s" % (bot, update, args))
  (chat_id, chat_type, user_id, text, message) = extract_update_info(update)
  chat_title = message.chat.title

  if not is_admin(chat_id, user_id, bot):
    return

  grupo = getGroup(chat_id)
  if grupo == None or grupo["spreadsheet"] == None:
    bot.sendMessage(chat_id=chat_id, text="No estoy configurado en este grupo :( Debes configurar primero el spreadsheet. Pregunta a @gentakojima")
    return

  bot.sendMessage(chat_id=update.message.chat_id, text="Refrescando lista de gimnasios...")
  response = requests.get("https://docs.google.com/spreadsheet/ccc?key=%s&output=csv" % grupo["spreadsheet"] )
  if response.status_code == 200:
    places = []
    f = StringIO(response.content.decode('utf-8'))
    csvreader = csv.reader(f, delimiter=',', quotechar='"')
    counter = 0
    for row in csvreader:
      names = row[3].split(",")
      latitude = str(row[1]).replace(",",".")
      longitude = str(row[2]).replace(",",".")
      m = re.search('^-?[0-9]+.[0-9]+$', latitude, flags=re.IGNORECASE)
      m2 = re.search('^-?[0-9]+.[0-9]+$', longitude, flags=re.IGNORECASE)
      if m == None or m2 == None:
        bot.sendMessage(chat_id=update.message.chat_id, text="❌ ¡No se han podido cargar los gimnasios! Parece que hay algún problema con el formato de las coordenadas. Recuerda que deben tener un único separador decimal. Si tienes problemas, elimina el formato de las celdas numéricas.")
        return
      for i,r in enumerate(names):
        names[i] = names[i].strip()
        if len(names[i]) < 3:
          del names[i]
      places.append({"desc":row[0],"latitude":latitude,"longitude":longitude,"names":names});
      counter = counter + 1

    if counter > 1:
      grupo["title"] = chat_title
      saveGroup(grupo)
      if savePlaces(chat_id, places):
          places = getPlaces(grupo["id"])
          bot.sendMessage(chat_id=update.message.chat_id, text="¡Cargados %i gimnasios!" % len(places))
      else:
          bot.sendMessage(chat_id=update.message.chat_id, text="❌ ¡No se han podido refrescar los gimnasios! Comprueba que no haya dos gimnasios con el mismo nombre")
    else:
      bot.sendMessage(chat_id=update.message.chat_id, text="❌ ¡No se han podido cargar los gimnasios! ¿Seguro que está en el formato correcto?")
  else:
    bot.sendMessage(chat_id=update.message.chat_id, text="❌ Error cargando la hoja de cálculo. ¿Seguro que es pública?")

def registerOak(bot, update):
    logging.debug("detectivepikachubot:registerOak: %s %s" % (bot, update))
    (chat_id, chat_type, user_id, text, message) = extract_update_info(update)
    this_date = message.date
    user_username = message.from_user.username
    try:
        forward_date = message.forward_date
        forward_id = message.forward_from.id
    except:
        forward_id = None
        forward_date = None

    m = re.search("@([a-zA-Z0-9]+), eres (Rojo|Azul|Amarillo) L([0-9]{1,2})[ .]",text, flags=re.IGNORECASE)
    if m != None:
        if forward_id == 201760961:
            if (this_date - forward_date).total_seconds() < 120:
                m2 = re.search("✅",text, flags=re.IGNORECASE)
                if m2 != None:
                    thisuser = {}
                    thisuser["id"] = user_id
                    thisuser["team"] = m.group(2)
                    thisuser["level"] = m.group(3)
                    thisuser["username"] = user_username
                    bot.sendMessage(chat_id=chat_id, text="👌 ¡De acuerdo! He reconocido que eres del equipo *%s* y de *nivel %s*.\n\nA partir de ahora aparecerá tu equipo y nivel en las incursiones en las que participes. Cuando subas de nivel, repite esta operación para que pueda reflejarlo bien en las incursiones." % (thisuser["team"],thisuser["level"]), parse_mode=telegram.ParseMode.MARKDOWN)
                    saveUser(thisuser)
                else:
                    bot.sendMessage(chat_id=chat_id, text="❌ Parece que no estás validado con @profesoroak\_bot. No puedo aceptar tu nivel y equipo hasta que te valides.", parse_mode=telegram.ParseMode.MARKDOWN)
            else:
                bot.sendMessage(chat_id=chat_id, text="❌ Ese mensaje es demasiado antiguo. ¡Debes reenviarme un mensaje más reciente!", parse_mode=telegram.ParseMode.MARKDOWN)
        else:
            bot.sendMessage(chat_id=chat_id, text="❌ ¿Has copiado y pegado el mensaje del @profesoroak\_bot? Tienes que usar la opción de *reenviar*, no sirve copiando y pegando.", parse_mode=telegram.ParseMode.MARKDOWN)
    else:
        if forward_id == 201760961:
            bot.sendMessage(chat_id=chat_id, text="❌ No he reconocido ese mensaje de @profesoroak\_bot. ¿Seguro que le has preguntado `Quién soy?` y no otra cosa?", parse_mode=telegram.ParseMode.MARKDOWN)


def processLocation(bot, update):
    logging.debug("detectivepikachubot:processLocation: %s %s" % (bot, update))
    (chat_id, chat_type, user_id, text, message) = extract_update_info(update)
    location = message.location

    if chat_type == "private":
        places = getPlacesByLocation(location.latitude, location.longitude, 200)
        logging.debug(places)
        filtered_places = []
        for place in places:
            group = getGroup(place["grupo_id"])
            if group["testgroup"] == 1 or group["alerts"] == 0:
                continue
            ingroup = False
            groups = getGroupsByUser(user_id)
            for g in groups:
                if group["id"] == g["id"]:
                    ingroup = True
            if ingroup == False:
                continue
            filtered_places.append(place)
        if len(filtered_places) == 0:
            bot.sendMessage(chat_id=chat_id, text="❌ No se han encontrado gimnasios cerca de esta zona en grupos en los que hayas participado.", parse_mode=telegram.ParseMode.MARKDOWN)
        else:
            text_message = "🗺 Se han encontrado los siguientes gimnasios:\n"
            example_id = None
            alerts = getAlerts(user_id)
            alert_ids = []
            for alert in alerts:
                alert_ids.append(alert["place_id"])
            for place in filtered_places:
                group = getGroup(place["grupo_id"])
                if example_id == None:
                    example_id = place["id"]
                if place["id"] in alert_ids:
                    icon = "✅"
                else:
                    icon = "▪️"
                text_message = text_message + "\n%s `%s` %s - Grupo %s" % (icon, place["id"], place["name"], group["title"])
            text_message = text_message + "\n\nPara añadir una alerta para alguno de estos gimnasios, envíame el comando `/addalert` seguido del identificador numérico.\n\nPor ejemplo:\n`/addalert %s`" % example_id
            bot.sendMessage(chat_id=chat_id, text=text_message, parse_mode=telegram.ParseMode.MARKDOWN)

def processMessage(bot, update):
  (chat_id, chat_type, user_id, text, message) = extract_update_info(update)

  if chat_type == "private":
    registerOak(bot, update)
    return

  logging.debug("detectivepikachubot:processMessage: %s %s" % (bot, update))

  m2 = re.search('(dónde|donde).*(gimnasio|gym|gim) (.+)$', text, flags=re.IGNORECASE)
  m3 = re.search('(#noloc|#nl)', text, flags=re.IGNORECASE)
  if m2 != None and m3 == None:
    if chat_type == "private":
      bot.sendMessage(chat_id=chat_id, text="Solo funciono en canales y grupos")
      return
    gyms = getPlaces(chat_id)
    if len(gyms)==0:
      return
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
      bot.sendVenue(chat_id=chat_id, latitude=chosen["latitude"], longitude=chosen["longitude"], title=chosen["desc"], address=address)
    else:
      logging.info("Oops! No encontrado")

def list(bot, update):
  logging.debug("detectivepikachubot:list: %s %s" % (bot, update))
  (chat_id, chat_type, user_id, text, message) = extract_update_info(update)
  if chat_type == "private":
    bot.sendMessage(chat_id=chat_id, text="Solo funciono en canales y grupos")
    return

  if not is_admin(chat_id, user_id, bot):
    return

  gyms = getPlaces(chat_id)
  if len(gyms)==0:
    bot.sendMessage(chat_id=chat_id, text="No estoy configurado en este grupo")
    return
  output = "Lista de gimnasios conocidos (%i):" % len(gyms)
  bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
  for p in gyms:
    output = output + ("\n - %s" % p["desc"])
  bot.sendMessage(chat_id=chat_id, text=output)

def incursiones(bot, update):
    logging.debug("detectivepikachubot:incursiones: %s %s" % (bot, update))
    (chat_id, chat_type, user_id, text, message) = extract_update_info(update)
    if chat_type == "private":
        bot.sendMessage(chat_id=chat_id, text="Solo funciono en canales y grupos")
        return
    if not is_admin(chat_id, user_id, bot):
        return
    try:
        bot.deleteMessage(chat_id=chat_id,message_id=message.message_id)
    except:
        pass

    raids = getLastRaids(chat_id, 5)
    output = ""
    for r in raids:
        creador = getCreadorRaid(r["id"])
        output = ("\n - `%s` %s @%s" % (r["id"], r["pokemon"], ensure_escaped(creador["username"]))) + output
    output = "Últimas incursiones del grupo:" + output
    bot.sendMessage(chat_id=user_id, text=output, parse_mode=telegram.ParseMode.MARKDOWN)

keyboard = [[InlineKeyboardButton("🙋 ¡Voy!", callback_data='voy'), InlineKeyboardButton("👭 +1", callback_data='plus1'), InlineKeyboardButton("🙅 No voy", callback_data='novoy')],
              [InlineKeyboardButton("👀 ¡Ya estoy allí!", callback_data='estoy'),InlineKeyboardButton("🗺 Ubicación", callback_data='ubicacion')]]
reply_markup = InlineKeyboardMarkup(keyboard)

def raid(bot, update, args=None):
  logging.debug("detectivepikachubot:raid: %s %s %s" % (bot, update, args))
  (chat_id, chat_type, user_id, text, message) = extract_update_info(update)
  user_username = message.from_user.username

  thisuser = refreshUsername(user_id, user_username)

  if chat_type == "private":
    bot.sendMessage(chat_id=chat_id, text="La incursiones solo funcionan en canales y grupos. Si quieres probarlas, puedes pasarte por @detectivepikachuayuda.")
    return

  current_raid = {}

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
    sent_message = bot.sendMessage(chat_id=chat_id, text="¡No te he entendido!\nDebes seguir el siguiente formato:\n`/raid <pokemon> <hora> <gimnasio> [horafin]`\nEjemplo: `/raid pikachu 12:00 la lechera 12:50`\n_(¡la hora de fin es opcional!)_\n\nEl mensaje original era:\n`%s`\n\n_(Este mensaje se borrará en unos segundos)_" % text, parse_mode=telegram.ParseMode.MARKDOWN)
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
    sent_message = bot.sendMessage(chat_id=chat_id, text="¡No he entendido el Pokémon! ¿Lo has escrito bien?\nRecuerda que debes seguir el siguiente formato:\n`/raid <pokemon> <hora> <gimnasio> [horafin]`\nEjemplo: `/raid pikachu 12:00 la lechera 12:50`\n_(¡la hora de fin es opcional!)_\n\nEl mensaje original era:\n`%s`\n\n_(Este mensaje se borrará en unos segundos)_" % text,parse_mode=telegram.ParseMode.MARKDOWN)
    t = Thread(target=delete_message_timed, args=(chat_id, sent_message.message_id, 15, bot))
    t.start()
    return

  del args[0]
  if args[0] == "a" and (args[1] == "las" or args[1] == "la"):
    del args[0]
    del args[0]

  m = re.match("([0-9]{1,2})[:.]?([0-9]{0,2})h?", args[0], flags=re.IGNORECASE)
  if m != None:
    hour = str(m.group(1))
    minute = m.group(2) or "00"
    if int(hour)<0 or int(hour)>24 or int(minute)<0 or int(minute)>59:
        sent_message = bot.sendMessage(chat_id=chat_id, text="¡No he entendido la hora! ¿La has escrito bien?\nRecuerda que debes seguir el siguiente formato:\n`/raid <pokemon> <hora> <gimnasio> [horafin]`\nEjemplo: `/raid pikachu 12:00 la lechera 12:50`\n_(¡la hora de fin es opcional!)_\n\nEl mensaje original era:\n`%s`\n\n_(Este mensaje se borrará en unos segundos)_" % text,parse_mode=telegram.ParseMode.MARKDOWN)
        t = Thread(target=delete_message_timed, args=(chat_id, sent_message.message_id, 15, bot))
        t.start()
        return
  else:
    sent_message = bot.sendMessage(chat_id=chat_id, text="¡No he entendido la hora! ¿La has escrito bien?\nRecuerda que debes seguir el siguiente formato:\n`/raid <pokemon> <hora> <gimnasio> [horafin]`\nEjemplo: `/raid pikachu 12:00 la lechera 12:50`\n_(¡la hora de fin es opcional!)_\n\nEl mensaje original era:\n`%s`\n\n_(Este mensaje se borrará en unos segundos)_" % text,parse_mode=telegram.ParseMode.MARKDOWN)
    t = Thread(target=delete_message_timed, args=(chat_id, sent_message.message_id, 15, bot))
    t.start()
    return
  current_raid["time"] = "%02d:%02d" % (int(hour),int(minute))

  m = re.match("([0-9]{1,2})[:.]?([0-9]{0,2})h?", args[-1], flags=re.IGNORECASE)
  if m != None:
    hour = str(m.group(1))
    minute = m.group(2) or "00"
    if int(hour)<0 or int(hour)>24 or int(minute)<0 or int(minute)>59:
        sent_message = bot.sendMessage(chat_id=chat_id, text="¡No he entendido la hora de finalización! ¿La has escrito bien?\nRecuerda que debes seguir el siguiente formato:\n`/raid <pokemon> <hora> <gimnasio> [horafin]`\nEjemplo: `/raid pikachu 12:00 la lechera 12:50`\n_(¡la hora de fin es opcional!)_\n\nEl mensaje original era:\n`%s`\n\n_(Este mensaje se borrará en unos segundos)_" % text,parse_mode=telegram.ParseMode.MARKDOWN)
        t = Thread(target=delete_message_timed, args=(chat_id, sent_message.message_id, 15, bot))
        t.start()
        return
    current_raid["endtime"] = "%02d:%02d" % (int(hour),int(minute))
    del args[-1]

    try:
        if args[-4] == "se" and args[-3] == "va" and args[-2] == "a" and (args[-1] == "las" or args[-1] == "la"):
            del args[-1]
            del args[-1]
            del args[-1]
            del args[-1]
        elif args[-3] == "está" and args[-2] == "hasta" and (args[-1] == "las" or args[-1] == "la"):
            del args[-1]
            del args[-1]
            del args[-1]
        elif args[-3] == "desaparece" and args[-2] == "a" and (args[-1] == "las" or args[-1] == "la"):
            del args[-1]
            del args[-1]
            del args[-1]
    except:
        pass

  del args[0]
  if args[0] == "en":
    del args[0]

  current_raid["gimnasio_text"] = ""
  for i in range (0,len(args)):
      current_raid["gimnasio_text"] = current_raid["gimnasio_text"] + "%s " % args[i]
  current_raid["gimnasio_text"] = current_raid["gimnasio_text"].strip()

  chosengym = None
  gyms = getPlaces(chat_id, ordering="id")
  for p in gyms:
    logging.debug("Testing gym «%s»»" % (p["desc"]))
    for n in p["names"]:
      if re.search(unidecode(n),unidecode(current_raid["gimnasio_text"]),flags=re.IGNORECASE) != None:
        logging.debug("Match! «%s» with «%s»" % (unidecode(n),unidecode(current_raid["gimnasio_text"])))
        chosengym = p
        break
    if chosengym != None:
      break
  if chosengym != None:
    current_raid["gimnasio_text"] = chosengym["desc"]
    current_raid["gimnasio_id"] = chosengym["id"]

  if "endtime" in current_raid.keys():
    text_endtime="\n_Se va a las %s_" % current_raid["endtime"]
  else:
    text_endtime=""
  send_text = "Incursión de *%s* a las *%s* en *%s*\nCreada por @%s%s\nEntrenadores apuntados (0):" % (current_raid["pokemon"], current_raid["time"], current_raid["gimnasio_text"], ensure_escaped(current_raid["username"]), text_endtime)

  sent_message = bot.sendMessage(chat_id=chat_id, text=send_text,parse_mode=telegram.ParseMode.MARKDOWN,reply_markup=reply_markup)

  current_raid["grupo_id"] = chat_id
  current_raid["usuario_id"] = user_id
  current_raid["message"] = sent_message.message_id

  current_raid["id"] = saveRaid(current_raid)

  if current_raid["endtime"] != None:
      show_endtime = current_raid["endtime"]
  else:
      show_endtime = current_raid["time"]

  bot.send_message(chat_id=user_id, text="Para editar/borrar la incursión de *%s* a las *%s* en *%s* pon aquí los siguientes comandos (mantén el identificador *%s*):\n\n🕒 *Cambiar hora*:\n`/cambiarhora %s %s`\n\n🕒 *Cambiar hora a la que se va*:\n`/cambiarhorafin %s %s`\n_(Pon un guión _`-`_ para borrarla)_\n\n🗺 *Cambiar gimnasio*:\n`/cambiargimnasio %s %s`\n\n👿 *Cambiar Pokémon*:\n`/cambiarpokemon %s %s`\n\n🚫 *Cancelar incursión*:\n`/cancelar %s`\n\n❌ *Borrar incursión*:\n`/borrar %s`" % (current_raid["pokemon"], current_raid["time"], current_raid["gimnasio_text"], current_raid["id"], current_raid["id"], current_raid["time"], current_raid["id"], show_endtime, current_raid["id"], current_raid["gimnasio_text"], current_raid["id"], current_raid["pokemon"], current_raid["id"], current_raid["id"]), parse_mode=telegram.ParseMode.MARKDOWN)

  if "gimnasio_id" in current_raid.keys():
    send_alerts(current_raid, bot)

def alerts(bot, update, args=None):
    logging.debug("detectivepikachubot:alerts: %s %s %s" % (bot, update, args))
    (chat_id, chat_type, user_id, text, message) = extract_update_info(update)

    if chat_type != "private":
        try:
          bot.deleteMessage(chat_id=chat_id,message_id=message.message_id)
        except:
          pass
        sent_message = bot.sendMessage(chat_id=chat_id, text="¡Los comandos de alertas solo funcionan por privado!\n\n_(Este mensaje se borrará en unos segundos)_",parse_mode=telegram.ParseMode.MARKDOWN)
        t = Thread(target=delete_message_timed, args=(chat_id, sent_message.message_id, 15, bot))
        t.start()
        return

    alerts=getAlerts(user_id)
    if len(alerts)==0:
        text_message = "⏰ No tienes ninguna alerta de incursión definida."
    else:
        text_message = "⏰ Tienes definidas %s alertas para los siguientes gimnasios:\n" % len(alerts)
        for alert in alerts:
            place = getPlace(alert["place_id"])
            group = getGroup(place["group_id"])
            text_message = text_message + "\n✅ `%s` %s - Grupo %s" % (place["id"], place["desc"], group["title"])
        text_message = text_message + "\n\nPara borrar una alerta, envíame `/delalert` seguido del identificador numérico, o `/clearalerts` para borrarlas todas."
    text_message = text_message + "\n\nPara añadir alertas de incursión nuevas, *envíame una ubicación* con gimnasios cercanos y te explico."
    bot.send_message(chat_id=user_id, text=text_message, parse_mode=telegram.ParseMode.MARKDOWN)

def addalert(bot, update, args=None):
    logging.debug("detectivepikachubot:addalert: %s %s %s" % (bot, update, args))
    (chat_id, chat_type, user_id, text, message) = extract_update_info(update)

    if chat_type != "private":
        try:
          bot.deleteMessage(chat_id=chat_id,message_id=message.message_id)
        except:
          pass
        sent_message = bot.sendMessage(chat_id=chat_id, text="❌ ¡Los comandos de alertas solo funcionan por privado!\n\n_(Este mensaje se borrará en unos segundos)_",parse_mode=telegram.ParseMode.MARKDOWN)
        t = Thread(target=delete_message_timed, args=(chat_id, sent_message.message_id, 15, bot))
        t.start()
        return

    if len(args)<1 or not str(args[0]).isnumeric():
        bot.sendMessage(chat_id=chat_id, text="❌ ¡Tienes que pasarme un identificador numérico como parámetro!", parse_mode=telegram.ParseMode.MARKDOWN)
        return

    alerts = getAlerts(user_id)
    if len(alerts)>=20:
        bot.sendMessage(chat_id=chat_id, text="❌ ¡Solo se pueden configurar un máximo de 20 alertas!", parse_mode=telegram.ParseMode.MARKDOWN)
        return

    place = getPlace(args[0])
    if place == None:
        bot.sendMessage(chat_id=chat_id, text="❌ ¡No he reconocido ese gimnasio! ¿Seguro que has puesto bien el identificador?", parse_mode=telegram.ParseMode.MARKDOWN)
        return

    for alert in alerts:
        if alert["place_id"] == place["id"]:
            bot.sendMessage(chat_id=chat_id, text="❌ ¡Ya has configurado una alerta para ese gimnasio!", parse_mode=telegram.ParseMode.MARKDOWN)
            return

    if addAlert(user_id, place["id"]):
        bot.sendMessage(chat_id=chat_id, text="👌 Se ha añadido una alerta para el gimnasio *%s*.\n\nA partir de ahora, recibirás un mensaje privado cada vez que alguien cree una incursión en ese gimnasio." % place["desc"], parse_mode=telegram.ParseMode.MARKDOWN)
    else:
        bot.sendMessage(chat_id=chat_id, text="❌ No se ha podido añadir una alerta para ese gimnasio.", parse_mode=telegram.ParseMode.MARKDOWN)


def delalert(bot, update, args=None):
    logging.debug("detectivepikachubot:delalert: %s %s %s" % (bot, update, args))
    (chat_id, chat_type, user_id, text, message) = extract_update_info(update)

    if chat_type != "private":
        try:
          bot.deleteMessage(chat_id=chat_id,message_id=message.message_id)
        except:
          pass
        sent_message = bot.sendMessage(chat_id=chat_id, text="❌ ¡Los comandos de alertas solo funcionan por privado!\n\n_(Este mensaje se borrará en unos segundos)_",parse_mode=telegram.ParseMode.MARKDOWN)
        t = Thread(target=delete_message_timed, args=(chat_id, sent_message.message_id, 15, bot))
        t.start()
        return

    if len(args)<1 or not str(args[0]).isnumeric():
        bot.sendMessage(chat_id=chat_id, text="❌ ¡Tienes que pasarme un identificador numérico como parámetro!", parse_mode=telegram.ParseMode.MARKDOWN)
        return

    place = getPlace(args[0])
    if place == None:
        bot.sendMessage(chat_id=chat_id, text="❌ ¡No he reconocido ese gimnasio! ¿Seguro que has puesto bien el identificador?", parse_mode=telegram.ParseMode.MARKDOWN)
        return

    if delAlert(user_id, place["id"]):
        bot.sendMessage(chat_id=chat_id, text="👌 Se ha eliminado la alerta del gimnasio *%s*.\n\nA partir de ahora, ya no recibirás mensajes privados cada vez que alguien cree una incursión allí." % place["desc"], parse_mode=telegram.ParseMode.MARKDOWN)
    else:
        bot.sendMessage(chat_id=chat_id, text="❌ No se ha podido eliminar la alerta para ese gimnasio.", parse_mode=telegram.ParseMode.MARKDOWN)

def clearalerts(bot, update):
    logging.debug("detectivepikachubot:clearlerts: %s %s" % (bot, update))
    (chat_id, chat_type, user_id, text, message) = extract_update_info(update)

    if chat_type != "private":
        try:
          bot.deleteMessage(chat_id=chat_id,message_id=message.message_id)
        except:
          pass
        sent_message = bot.sendMessage(chat_id=chat_id, text="❌ ¡Los comandos de alertas solo funcionan por privado!\n\n_(Este mensaje se borrará en unos segundos)_",parse_mode=telegram.ParseMode.MARKDOWN)
        t = Thread(target=delete_message_timed, args=(chat_id, sent_message.message_id, 15, bot))
        t.start()
        return

    if clearAlerts(user_id):
        bot.sendMessage(chat_id=chat_id, text="👌 Se han eliminado las alertas de todos los gimnasios.\n\nA partir de ahora, ya no recibirás mensajes privados cada vez que alguien cree una incursión.", parse_mode=telegram.ParseMode.MARKDOWN)
    else:
        bot.sendMessage(chat_id=chat_id, text="❌ No se ha eliminado ninguna alerta.", parse_mode=telegram.ParseMode.MARKDOWN)

def cancelar(bot, update, args=None):
    logging.debug("detectivepikachubot:cancelar: %s %s %s" % (bot, update, args))
    (chat_id, chat_type, user_id, text, message) = extract_update_info(update)
    user_username = message.from_user.username

    thisuser = refreshUsername(user_id, user_username)

    if chat_type != "private":
        try:
          bot.deleteMessage(chat_id=chat_id,message_id=message.message_id)
        except:
          pass
        sent_message = bot.sendMessage(chat_id=chat_id, text="¡El comando de cancelar incursión solo funciona por privado!\n\n_(Este mensaje se borrará en unos segundos)_",parse_mode=telegram.ParseMode.MARKDOWN)
        t = Thread(target=delete_message_timed, args=(chat_id, sent_message.message_id, 15, bot))
        t.start()
        return

    if len(args)<1 or not str(args[0]).isnumeric():
        bot.sendMessage(chat_id=chat_id, text="¡No he reconocido los datos que me envías!\nCopia y pega el comando que recibiste por privado y no elimines el identificador numérico de la incursión.",parse_mode=telegram.ParseMode.MARKDOWN)
        return

    raid_id = args[0]
    raid = getRaid(raid_id)
    if raid != None:
        if raid["usuario_id"] == user_id or is_admin(raid["grupo_id"], user_id, bot):
            if cancelRaid(raid_id):
                if raid["ended"] == 1:
                    bot.sendMessage(chat_id=chat_id, text="No se puede editar una incursión tan antigua.", parse_mode=telegram.ParseMode.MARKDOWN)
                    return
                update_message(raid["grupo_id"], raid["message"], None, bot)
                bot.sendMessage(chat_id=chat_id, text="¡Has cancelado la incursión!",parse_mode=telegram.ParseMode.MARKDOWN)
                people = getRaidPeople(raid["id"])
                warned = []
                notwarned = []
                for p in people:
                    if p["username"] == user_username:
                        continue
                    try:
                        bot.sendMessage(chat_id=p["id"], text="❌ @%s ha *cancelado* la incursión de %s a las %s en %s" % (ensure_escaped(user_username), raid["pokemon"], raid["time"], raid["gimnasio_text"]), parse_mode=telegram.ParseMode.MARKDOWN)
                        warned.append(p["username"])
                    except:
                        notwarned.append(p["username"])
                if len(warned)>0:
                    bot.sendMessage(chat_id=chat_id, text="He avisado por privado a: %s" % ensure_escaped(", ".join(warned)), parse_mode=telegram.ParseMode.MARKDOWN)
                if len(notwarned)>0:
                    bot.sendMessage(chat_id=chat_id, text="No he podido avisar a: %s" % ensure_escaped(", ".join(notwarned)), parse_mode=telegram.ParseMode.MARKDOWN)
            else:
                bot.sendMessage(chat_id=chat_id, text="¡Esa incursión ya estaba cancelada!",parse_mode=telegram.ParseMode.MARKDOWN)
        else:
            bot.sendMessage(chat_id=chat_id, text="¡No tienes permiso para cancelar esta incursión!",parse_mode=telegram.ParseMode.MARKDOWN)
    else:
        bot.sendMessage(chat_id=chat_id, text="¡Esa incursión no existe!",parse_mode=telegram.ParseMode.MARKDOWN)

def cambiarhora(bot, update, args=None):
    logging.debug("detectivepikachubot:cambiarHora: %s %s %s" % (bot, update, args))
    (chat_id, chat_type, user_id, text, message) = extract_update_info(update)
    user_username = message.from_user.username

    thisuser = refreshUsername(user_id, user_username)

    if chat_type != "private":
        try:
          bot.deleteMessage(chat_id=chat_id,message_id=message.message_id)
        except:
          pass
        sent_message = bot.sendMessage(chat_id=chat_id, text="¡El comando de cambiar la hora solo funciona por privado!\n\n_(Este mensaje se borrará en unos segundos)_",parse_mode=telegram.ParseMode.MARKDOWN)
        t = Thread(target=delete_message_timed, args=(chat_id, sent_message.message_id, 15, bot))
        t.start()
        return

    if len(args)<2 or not str(args[0]).isnumeric():
        bot.sendMessage(chat_id=chat_id, text="¡No he reconocido los datos que me envías!\nCopia y pega el comando que recibiste por privado y no elimines el identificador numérico de la incursión.",parse_mode=telegram.ParseMode.MARKDOWN)
        return

    raid_id = args[0]
    raid = getRaid(raid_id)
    if raid != None:
        if raid["usuario_id"] == user_id or is_admin(raid["grupo_id"], user_id, bot):
            if raid["ended"] == 1:
                bot.sendMessage(chat_id=chat_id, text="No se puede editar una incursión tan antigua.", parse_mode=telegram.ParseMode.MARKDOWN)
                return
            if raid["cancelled"] == 1:
                bot.sendMessage(chat_id=chat_id, text="¡No se pueden editar incursiones canceladas!", parse_mode=telegram.ParseMode.MARKDOWN)
                return
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
                        saveRaid(raid)
                        update_message(raid["grupo_id"], raid["message"], reply_markup, bot)
                        bot.sendMessage(chat_id=chat_id, text="¡Se ha cambiado la hora a las *%s* correctamente!" % raid["time"], parse_mode=telegram.ParseMode.MARKDOWN)
                        people = getRaidPeople(raid["id"])
                        warned = []
                        notwarned = []
                        for p in people:
                            if p["username"] == user_username:
                                continue
                            try:
                                bot.sendMessage(chat_id=p["id"], text="⚠️ @%s ha cambiado la hora de la incursión de %s en %s para las *%s*" % (ensure_escaped(user_username), raid["pokemon"], raid["gimnasio_text"], raid["time"]), parse_mode=telegram.ParseMode.MARKDOWN)
                                warned.append(p["username"])
                            except:
                                notwarned.append(p["username"])
                        if len(warned)>0:
                            bot.sendMessage(chat_id=chat_id, text="He avisado por privado a: %s" % ensure_escaped(", ".join(warned)), parse_mode=telegram.ParseMode.MARKDOWN)
                        if len(notwarned)>0:
                            bot.sendMessage(chat_id=chat_id, text="No he podido avisar a: %s" % ensure_escaped(", ".join(notwarned)), parse_mode=telegram.ParseMode.MARKDOWN)
                else:
                  bot.sendMessage(chat_id=chat_id, text="¡No he entendido la hora! ¿La has escrito bien?\nDebe seguir el formato `hh:mm`.\nEjemplo: `12:15`", parse_mode=telegram.ParseMode.MARKDOWN)
        else:
            bot.sendMessage(chat_id=chat_id, text="¡No tienes permiso para editar esta incursión!",parse_mode=telegram.ParseMode.MARKDOWN)
    else:
        bot.sendMessage(chat_id=chat_id, text="¡Esa incursión no existe!",parse_mode=telegram.ParseMode.MARKDOWN)

def cambiarhorafin(bot, update, args=None):
    logging.debug("detectivepikachubot:cambiarHoraFin: %s %s %s" % (bot, update, args))
    (chat_id, chat_type, user_id, text, message) = extract_update_info(update)
    user_username = message.from_user.username

    thisuser = refreshUsername(user_id, user_username)

    if chat_type != "private":
        try:
          bot.deleteMessage(chat_id=chat_id,message_id=message.message_id)
        except:
          pass
        sent_message = bot.sendMessage(chat_id=chat_id, text="¡El comando de cambiar la hora de fin solo funciona por privado!\n\n_(Este mensaje se borrará en unos segundos)_",parse_mode=telegram.ParseMode.MARKDOWN)
        t = Thread(target=delete_message_timed, args=(chat_id, sent_message.message_id, 15, bot))
        t.start()
        return

    if len(args)<2 or not str(args[0]).isnumeric():
        bot.sendMessage(chat_id=chat_id, text="¡No he reconocido los datos que me envías!\nCopia y pega el comando que recibiste por privado y no elimines el identificador numérico de la incursión.",parse_mode=telegram.ParseMode.MARKDOWN)
        return

    raid_id = args[0]
    raid = getRaid(raid_id)
    if raid != None:
        if raid["usuario_id"] == user_id or is_admin(raid["grupo_id"], user_id, bot):
            if raid["ended"] == 1:
                bot.sendMessage(chat_id=chat_id, text="No se puede editar una incursión tan antigua.", parse_mode=telegram.ParseMode.MARKDOWN)
                return
            if raid["cancelled"] == 1:
                bot.sendMessage(chat_id=chat_id, text="¡No se pueden editar incursiones canceladas!", parse_mode=telegram.ParseMode.MARKDOWN)
                return
            if args[1] == raid["endtime"]:
                bot.sendMessage(chat_id=chat_id, text="¡La incursión ya tiene la hora de fin para esa hora!", parse_mode=telegram.ParseMode.MARKDOWN)
            else:
                m = re.match("([0-9]{1,2})[:.]?([0-9]{0,2})h?", args[1], flags=re.IGNORECASE)
                if m != None or args[1] == "-":
                    if m != None:
                        hour = str(m.group(1))
                        minute = m.group(2) or "00"
                        if int(hour)<0 or int(hour)>24 or int(minute)<0 or int(minute)>59:
                            bot.sendMessage(chat_id=chat_id, text="¡No he entendido la hora! ¿La has escrito bien?\nDebe seguir el formato `hh:mm`.\nEjemplo: `12:15`\n\nSi quieres borrar la hora de fin, pon un guión simple en lugar de la hora: `-`.", parse_mode=telegram.ParseMode.MARKDOWN)
                            return
                        raid["endtime"] = "%02d:%02d" % (int(hour),int(minute))
                    else:
                        raid["endtime"] = None
                    saveRaid(raid)
                    update_message(raid["grupo_id"], raid["message"], reply_markup, bot)
                    if raid["endtime"] != None:
                        bot.sendMessage(chat_id=chat_id, text="¡Se ha cambiado la hora de fin para las *%s* correctamente!" % raid["endtime"], parse_mode=telegram.ParseMode.MARKDOWN)
                    else:
                        bot.sendMessage(chat_id=chat_id, text="¡Se ha borrado la hora de fin correctamente!", parse_mode=telegram.ParseMode.MARKDOWN)
                    people = getRaidPeople(raid["id"])
                    warned = []
                    notwarned = []
                    for p in people:
                        if p["username"] == user_username:
                            continue
                        try:
                            if raid["endtime"] != None:
                                bot.sendMessage(chat_id=p["id"], text="⚠️ @%s ha cambiado la hora a la que se termina la incursión de %s en %s a las *%s* (¡ojo, la incursión sigue programada para la misma hora: %s!)" % (ensure_escaped(user_username), raid["pokemon"], raid["gimnasio_text"], raid["endtime"], raid["time"]), parse_mode=telegram.ParseMode.MARKDOWN)
                            else:
                                bot.sendMessage(chat_id=p["id"], text="⚠️ @%s ha borrado la hora a la que se termina la incursión de %s en %s (¡ojo, la incursión sigue programada para la misma hora: %s!)" % (ensure_escaped(user_username), raid["pokemon"], raid["gimnasio_text"], raid["time"]), parse_mode=telegram.ParseMode.MARKDOWN)
                            warned.append(p["username"])
                        except:
                            notwarned.append(p["username"])
                    if len(warned)>0:
                        bot.sendMessage(chat_id=chat_id, text="He avisado por privado a: %s" % ensure_escaped(", ".join(warned)), parse_mode=telegram.ParseMode.MARKDOWN)
                    if len(notwarned)>0:
                        bot.sendMessage(chat_id=chat_id, text="No he podido avisar a: %s" % ensure_escaped(", ".join(notwarned)), parse_mode=telegram.ParseMode.MARKDOWN)
                else:
                  bot.sendMessage(chat_id=chat_id, text="¡No he entendido la hora! ¿La has escrito bien?\nDebe seguir el formato `hh:mm`.\nEjemplo: `12:15`\n\nSi quieres borrar la hora de fin, pon un guión simple en lugar de la hora: `-`.", parse_mode=telegram.ParseMode.MARKDOWN)
        else:
            bot.sendMessage(chat_id=chat_id, text="¡No tienes permiso para editar esta incursión!",parse_mode=telegram.ParseMode.MARKDOWN)
    else:
        bot.sendMessage(chat_id=chat_id, text="¡Esa incursión no existe!",parse_mode=telegram.ParseMode.MARKDOWN)

def cambiargimnasio(bot, update, args=None):
    logging.debug("detectivepikachubot:cambiargimnasio: %s %s %s" % (bot, update, args))
    (chat_id, chat_type, user_id, text, message) = extract_update_info(update)
    user_username = message.from_user.username

    thisuser = refreshUsername(user_id, user_username)

    if chat_type != "private":
        try:
          bot.deleteMessage(chat_id=chat_id,message_id=message.message_id)
        except:
          pass
        sent_message = bot.sendMessage(chat_id=chat_id, text="¡El comando de cambiar el gimnasio solo funciona por privado!\n\n_(Este mensaje se borrará en unos segundos)_",parse_mode=telegram.ParseMode.MARKDOWN)
        t = Thread(target=delete_message_timed, args=(chat_id, sent_message.message_id, 15, bot))
        t.start()
        return

    if len(args)<2 or not str(args[0]).isnumeric():
        bot.sendMessage(chat_id=chat_id, text="¡No he reconocido los datos que me envías!\nCopia y pega el comando que recibiste por privado y no elimines el identificador numérico de la incursión.",parse_mode=telegram.ParseMode.MARKDOWN)
        return

    new_gymtext = ""
    for i in range (1,len(args)):
        new_gymtext = new_gymtext + "%s " % args[i]
    new_gymtext = new_gymtext.strip()

    raid_id = args[0]
    raid = getRaid(raid_id)
    if raid != None:
        if raid["usuario_id"] == user_id or is_admin(raid["grupo_id"], user_id, bot):
            if raid["ended"] == 1:
                bot.sendMessage(chat_id=chat_id, text="No se puede editar una incursión tan antigua.", parse_mode=telegram.ParseMode.MARKDOWN)
                return
            if raid["cancelled"] == 1:
                bot.sendMessage(chat_id=chat_id, text="¡No se pueden editar incursiones canceladas!", parse_mode=telegram.ParseMode.MARKDOWN)
                return
            if new_gymtext == raid["gimnasio_text"]:
                bot.sendMessage(chat_id=chat_id, text="¡La incursión ya está puesta en ese gimnasio!", parse_mode=telegram.ParseMode.MARKDOWN)
            else:
                chosengym = None
                gyms = getPlaces(raid["grupo_id"], ordering="id")
                for p in gyms:
                    logging.debug("Testing gym «%s»»" % (p["desc"]))
                    for n in p["names"]:
                        if re.search(unidecode(n), unidecode(new_gymtext), flags=re.IGNORECASE) != None:
                            logging.debug("Match! «%s» with «%s»" % (unidecode(n),unidecode(new_gymtext)))
                            chosengym = p
                            break
                    if chosengym != None:
                        break
                if chosengym != None:
                    raid["gimnasio_text"] = chosengym["desc"]
                    raid["gimnasio_id"] = chosengym["id"]
                    saveRaid(raid)
                    update_message(raid["grupo_id"], raid["message"], reply_markup, bot)
                    bot.sendMessage(chat_id=chat_id, text="¡Se ha cambiado el gimnasio a *%s* correctamente!" % raid["gimnasio_text"], parse_mode=telegram.ParseMode.MARKDOWN)
                else:
                    raid["gimnasio_text"] = new_gymtext
                    raid["gimnasio_id"] = None
                    saveRaid(raid)
                    update_message(raid["grupo_id"], raid["message"], reply_markup, bot)
                    bot.sendMessage(chat_id=chat_id, text="¡No he encontrado el gimnasio, pero lo he actualizado igualmente en la incursión a *%s*" % raid["gimnasio_text"], parse_mode=telegram.ParseMode.MARKDOWN)
                people = getRaidPeople(raid["id"])
                warned = []
                notwarned = []
                for p in people:
                    if p["username"] == user_username:
                        continue
                    try:
                        bot.sendMessage(chat_id=p["id"], text="⚠️ @%s ha cambiado el gimnasio de la incursión de %s para las %s a *%s*" % (ensure_escaped(user_username), raid["pokemon"], raid["time"], raid["gimnasio_text"]), parse_mode=telegram.ParseMode.MARKDOWN)
                        warned.append(p["username"])
                    except:
                        notwarned.append(p["username"])
                if len(warned)>0:
                    bot.sendMessage(chat_id=chat_id, text="He avisado por privado a: %s" % ensure_escaped(", ".join(warned)), parse_mode=telegram.ParseMode.MARKDOWN)
                if len(notwarned)>0:
                    bot.sendMessage(chat_id=chat_id, text="No he podido avisar a: %s" % ensure_escaped(", ".join(notwarned)), parse_mode=telegram.ParseMode.MARKDOWN)
        else:
            bot.sendMessage(chat_id=chat_id, text="¡No tienes permiso para editar esta incursión!",parse_mode=telegram.ParseMode.MARKDOWN)
    else:
        bot.sendMessage(chat_id=chat_id, text="¡Esa incursión no existe!",parse_mode=telegram.ParseMode.MARKDOWN)

def cambiarpokemon(bot, update, args=None):
    logging.debug("detectivepikachubot:cambiarpokemon: %s %s %s" % (bot, update, args))
    (chat_id, chat_type, user_id, text, message) = extract_update_info(update)
    user_username = message.from_user.username

    thisuser = refreshUsername(user_id, user_username)

    if chat_type != "private":
        try:
          bot.deleteMessage(chat_id=chat_id,message_id=message.message_id)
        except:
          pass
        sent_message = bot.sendMessage(chat_id=chat_id, text="¡El comando de cambiar el Pokémon solo funciona por privado!\n\n_(Este mensaje se borrará en unos segundos)_",parse_mode=telegram.ParseMode.MARKDOWN)
        t = Thread(target=delete_message_timed, args=(chat_id, sent_message.message_id, 15, bot))
        t.start()
        return

    if len(args)<2 or not str(args[0]).isnumeric():
        bot.sendMessage(chat_id=chat_id, text="¡No he reconocido los datos que me envías!\nCopia y pega el comando que recibiste por privado y no elimines el identificador numérico de la incursión.",parse_mode=telegram.ParseMode.MARKDOWN)
        return

    raid_id = args[0]
    raid = getRaid(raid_id)
    if raid != None:
        if raid["usuario_id"] == user_id or is_admin(raid["grupo_id"], user_id, bot):
            if raid["ended"] == 1:
                bot.sendMessage(chat_id=chat_id, text="No se puede editar una incursión tan antigua.", parse_mode=telegram.ParseMode.MARKDOWN)
                return
            if raid["cancelled"] == 1:
                bot.sendMessage(chat_id=chat_id, text="¡No se pueden editar incursiones canceladas!", parse_mode=telegram.ParseMode.MARKDOWN)
                return
            if args[1] == raid["pokemon"]:
                bot.sendMessage(chat_id=chat_id, text="¡Ese ya es el Pokémon actual de la incursión!", parse_mode=telegram.ParseMode.MARKDOWN)
            else:
                for pokemon in pokemonlist:
                    m = re.match("^%s$" % pokemon, args[1], flags=re.IGNORECASE)
                    if m != None:
                        raid["pokemon"] = pokemon
                        saveRaid(raid)
                        update_message(raid["grupo_id"], raid["message"], reply_markup, bot)
                        bot.sendMessage(chat_id=chat_id, text="¡Se ha cambiado el Pokémon a *%s* correctamente!" % raid["pokemon"], parse_mode=telegram.ParseMode.MARKDOWN)
                        people = getRaidPeople(raid["id"])
                        warned = []
                        notwarned = []
                        for p in people:
                            if p["username"] == user_username:
                                continue
                            try:
                                bot.sendMessage(chat_id=p["id"], text="⚠️ @%s ha cambiado el Pokémon de la incursión para las %s en %s a *%s*" % (ensure_escaped(user_username), raid["time"], raid["gimnasio_text"], raid["pokemon"]), parse_mode=telegram.ParseMode.MARKDOWN)
                                warned.append(p["username"])
                            except:
                                notwarned.append(p["username"])
                        if len(warned)>0:
                            bot.sendMessage(chat_id=chat_id, text="He avisado por privado a: %s" % ensure_escaped(", ".join(warned)), parse_mode=telegram.ParseMode.MARKDOWN)
                        if len(notwarned)>0:
                            bot.sendMessage(chat_id=chat_id, text="No he podido avisar a: %s" % ensure_escaped(", ".join(notwarned)), parse_mode=telegram.ParseMode.MARKDOWN)
                        break
                else:
                    bot.sendMessage(chat_id=chat_id, text="¡No he reconocido ese Pokémon!",parse_mode=telegram.ParseMode.MARKDOWN)
        else:
            bot.sendMessage(chat_id=chat_id, text="¡No tienes permiso para editar esta incursión!",parse_mode=telegram.ParseMode.MARKDOWN)
    else:
        bot.sendMessage(chat_id=chat_id, text="¡Esa incursión no existe!",parse_mode=telegram.ParseMode.MARKDOWN)

def borrar(bot, update, args=None):
    logging.debug("detectivepikachubot:borrar: %s %s" % (bot, update))
    (chat_id, chat_type, user_id, text, message) = extract_update_info(update)
    user_username = message.from_user.username

    thisuser = refreshUsername(user_id, user_username)

    if chat_type != "private":
        try:
          bot.deleteMessage(chat_id=chat_id,message_id=message.message_id)
        except:
          pass
        sent_message = bot.sendMessage(chat_id=chat_id, text="¡El comando de borrar incursión solo funciona por privado!\n\n_(Este mensaje se borrará en unos segundos)_",parse_mode=telegram.ParseMode.MARKDOWN)
        t = Thread(target=delete_message_timed, args=(chat_id, sent_message.message_id, 15, bot))
        t.start()
        return

    raid_id = args[0]
    if not str(raid_id).isnumeric():
        bot.sendMessage(chat_id=chat_id, text="¡No he reconocido los datos que me envías!\nCopia y pega el comando que recibiste por privado y no elimines el identificador numérico de la incursión.",parse_mode=telegram.ParseMode.MARKDOWN)
        return

    raid = getRaid(raid_id)
    if raid != None:
        if raid["usuario_id"] == user_id or is_admin(raid["grupo_id"], user_id):
            if raid["ended"] == 1:
                bot.sendMessage(chat_id=chat_id, text="No se puede borrar una incursión tan antigua.", parse_mode=telegram.ParseMode.MARKDOWN)
                return
            people = getRaidPeople(raid["id"])
            warned = []
            notwarned = []
            if people != None:
                for p in people:
                    if p["username"] == user_username:
                        continue
                    try:
                        bot.sendMessage(chat_id=p["id"], text="🚫 @%s ha *borrado* la incursión de %s a las %s en %s" % (ensure_escaped(user_username), raid["pokemon"], raid["time"], raid["gimnasio_text"]), parse_mode=telegram.ParseMode.MARKDOWN)
                        warned.append(p["username"])
                    except:
                        notwarned.append(p["username"])
                if len(warned)>0:
                    bot.sendMessage(chat_id=chat_id, text="He avisado por privado a: %s" % ensure_escaped(", ".join(warned)), parse_mode=telegram.ParseMode.MARKDOWN)
                if len(notwarned)>0:
                    bot.sendMessage(chat_id=chat_id, text="No he podido avisar a: %s" % ensure_escaped(", ".join(notwarned)), parse_mode=telegram.ParseMode.MARKDOWN)
            if deleteRaid(raid["id"]):
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

  thisuser = refreshUsername(user_id, user_username)

  update_text = False

  logging.debug("detectivepikachubot:raidbutton:%s: %s %s" % (data, bot, update))

  if (data == "voy" or data == "plus1" or data == "novoy" or data == "estoy") \
    and (thisuser["username"] == None or thisuser["username"] == "None"):
    bot.answerCallbackQuery(text="No puedes unirte a una incursión si no tienes definido un alias.\nEn Telegram, ve a 'Ajustes' y selecciona la opción 'Alias'.", show_alert="true", callback_query_id=update.callback_query.id)
    return

  if data == "voy":
      if raidVoy(chat_id, message_id, user_id) != False:
          bot.answerCallbackQuery(text="¡Te has apuntado! Si vas con más gente, pulsa +1", callback_query_id=update.callback_query.id)
          update_text = True
      else:
          bot.answerCallbackQuery(text="¡No has podido apuntarte! ¿La incursión ha caducado?", callback_query_id=update.callback_query.id)
  elif data == "plus1":
      result = raidPlus1(chat_id, message_id, user_id)
      if result != False:
          bot.answerCallbackQuery(text="¡Te has apuntado con %i más! Si sois más, pulsa +1" % result, callback_query_id=update.callback_query.id)
          update_text = True
      else:
          bot.answerCallbackQuery(text="No puedes apuntarte con más de 6 personas", callback_query_id=update.callback_query.id)
  elif data == "novoy":
      if raidNovoy(chat_id, message_id, user_id) != False:
          bot.answerCallbackQuery(text="Te has desapuntado de la incursión", callback_query_id=update.callback_query.id)
          update_text = True
      else:
          bot.answerCallbackQuery(text="¡No has podido desapuntarte! ¿La incursión ha caducado?", callback_query_id=update.callback_query.id)
  elif data == "estoy":
      if raidEstoy(chat_id, message_id, user_id) != False:
          bot.answerCallbackQuery(text="Has marcardo que has llegado a la incursión", callback_query_id=update.callback_query.id)
          update_text = True
      else:
          bot.answerCallbackQuery(text="¡No has podido marcar como llegado! ¿La incursión ha caducado?", callback_query_id=update.callback_query.id)
  if update_text == True:
      update_message(chat_id, message_id, reply_markup, bot)

  if data=="ubicacion":
    raid = getRaidbyMessage(chat_id, message_id)
    if raid["gimnasio_id"] != None:
      try:
        gym = getPlace(raid["gimnasio_id"])
        if gym != None:
          reverse_geocode_result = gmaps.reverse_geocode((gym["latitude"], gym["longitude"]))
          address = reverse_geocode_result[0]["formatted_address"]
          bot.sendVenue(chat_id=user_id, latitude=gym["latitude"], longitude=gym["longitude"], title=gym["desc"], address=address)
          bot.answerCallbackQuery(text="Te envío la ubicación por privado", callback_query_id=update.callback_query.id)
        else:
          bot.answerCallbackQuery(text="La ubicación es desconocida", callback_query_id=update.callback_query.id)
      except:
        bot.answerCallbackQuery(text="Para que te pueda enviar la ubicación, debes abrir un privado antes con @detectivepikachubot y pulsar en 'Iniciar'", callback_query_id=update.callback_query.id, show_alert="true")
    else:
      bot.answerCallbackQuery(text="La ubicación es desconocida", callback_query_id=update.callback_query.id)


start_handler = CommandHandler('start', start)
help_handler = CommandHandler('help', start)
list_handler = CommandHandler('list', list)
incursiones_handler = CommandHandler('incursiones', incursiones)
message_handler = MessageHandler(Filters.text, processMessage)
setspreadsheet_handler = CommandHandler('setspreadsheet', setspreadsheet, pass_args=True)
refresh_handler = CommandHandler('refresh', refresh)
raid_handler = CommandHandler('raid', raid, pass_args=True)
cancelar_handler = CommandHandler('cancelar', cancelar, pass_args=True)
cambiarhora_handler = CommandHandler('cambiarhora', cambiarhora, pass_args=True)
cambiarhorafin_handler = CommandHandler('cambiarhorafin', cambiarhorafin, pass_args=True)
cambiargimnasio_handler = CommandHandler('cambiargimnasio', cambiargimnasio, pass_args=True)
cambiarpokemon_handler = CommandHandler('cambiarpokemon', cambiarpokemon, pass_args=True)
borrar_handler = CommandHandler('borrar', borrar, pass_args=True)
location_handler = MessageHandler(Filters.location, processLocation)
alerts_handler = CommandHandler('alerts', alerts, pass_args=True)
alertas_handler = CommandHandler('alertas', alerts, pass_args=True)
addalert_handler = CommandHandler('addalert', addalert, pass_args=True)
delalert_handler = CommandHandler('delalert', delalert, pass_args=True)
clearalerts_handler = CommandHandler('clearalerts', clearalerts)
borrar_handler = CommandHandler('borrar', borrar, pass_args=True)
raidbutton_handler = CallbackQueryHandler(raidbutton)

dispatcher.add_handler(start_handler)
dispatcher.add_handler(help_handler)
dispatcher.add_handler(message_handler)
dispatcher.add_handler(list_handler)
dispatcher.add_handler(incursiones_handler)
dispatcher.add_handler(setspreadsheet_handler)
dispatcher.add_handler(refresh_handler)
dispatcher.add_handler(raid_handler)
dispatcher.add_handler(cancelar_handler)
dispatcher.add_handler(cambiarhora_handler)
dispatcher.add_handler(cambiarhorafin_handler)
dispatcher.add_handler(cambiargimnasio_handler)
dispatcher.add_handler(cambiarpokemon_handler)
dispatcher.add_handler(borrar_handler)
dispatcher.add_handler(location_handler)
dispatcher.add_handler(alerts_handler)
dispatcher.add_handler(alertas_handler)
dispatcher.add_handler(addalert_handler)
dispatcher.add_handler(delalert_handler)
dispatcher.add_handler(clearalerts_handler)
dispatcher.add_handler(raidbutton_handler)

def callback_oldraids(bot, job):
    t = Thread(target=end_old_raids, args=(bot,))
    t.start()
j = updater.job_queue
job_minute = j.run_repeating(callback_oldraids, interval=60, first=5)

updater.start_polling()
