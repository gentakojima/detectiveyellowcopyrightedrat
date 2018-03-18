#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Detective Yellowcopyrightedrat - A Telegram bot to organize Pokémon GO raids
# Copyright (C) 2017 Jorge Suárez de Lis <hey@gentakojima.me>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
#
# Command list for @botfather
# help - Muestra la ayuda
# register - Inicia el proceso de registro (en privado)
# raid - Crea una incursión nueva (en grupo)
# alerts - Configura alertas de incursiones (en privado)
# raids - Muestra incursiones activas (en privado)
# profile - Muestra info de tu perfil (en privado)
# stats - Muestra tus estadísticas semanales (en privado)
#

from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, Filters
from telegram import ChatAction, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext.dispatcher import run_async

import re
import time
import logging
import requests
from io import StringIO
import csv
import signal
import os, sys
import telegram
from threading import Thread
from unidecode import unidecode
from datetime import datetime, timedelta, date
from pytz import timezone
import tempfile
import urllib.request
import random
from Levenshtein import distance
import html

from config import config
from storagemethods import saveGroup, savePlaces, savePlace, getGroup, getPlaces, saveUser, saveWholeUser, getUser, isBanned, refreshUsername, saveRaid, getRaid, raidVoy, raidPlus1, raidEstoy, raidNovoy, raidLlegotarde, getCreadorRaid, getRaidbyMessage, getPlace, deleteRaid, getRaidPeople, closeRaid, cancelRaid, uncancelRaid, getLastRaids, raidLotengo, raidEscapou, searchTimezone, getActiveRaidsforUser, getGrupoRaid, getCurrentValidation, saveValidation, getUserByTrainername, getActiveRaidsforGroup, getGroupsByUser, getGroupUserStats, getRanking, getRemovedAlerts, getCurrentGyms, getCachedRanking, saveCachedRanking, resetCachedRanking
from supportmethods import is_admin, extract_update_info, delete_message_timed, send_message_timed, pokemonlist, egglist, iconthemes, update_message, update_raids_status, send_alerts, send_alerts_delayed, error_callback, ensure_escaped, warn_people, get_settings_keyboard, update_settings_message, update_settings_message_timed, get_keyboard, format_message, edit_check_private, edit_check_private_or_reply, delete_message, parse_time, parse_pokemon, extract_time, extract_day, format_text_day, format_text_pokemon, parse_profile_image, validation_pokemons, validation_names, update_validations_status, already_sent_location, auto_refloat, format_gym_emojis, fetch_gym_address, get_pokemons_keyboard, get_gyms_keyboard, get_zones_keyboard, get_times_keyboard, get_endtimes_keyboard, get_days_keyboard, format_text_creating, remove_incomplete_raids, send_edit_instructions, ranking_time_periods, auto_ranking, ranking_text
from alerts import alerts, addalert, clearalerts, delalert, processLocation

def cleanup(signum, frame):
    logging.info("Closing bot!")
    exit(0)
signal.signal(signal.SIGINT, cleanup)

# Logging
logdir = sys.path[0] + "/logs"
if not os.path.exists(logdir):
    os.makedirs(logdir)
logging.basicConfig(filename=logdir+'/debug.log', format='%(asctime)s %(message)s', level=logging.DEBUG)
logging.info("--------------------- Starting bot! -----------------------")

updater = Updater(token=config["telegram"]["token"], workers=6)
dispatcher = updater.dispatcher
dispatcher.add_error_handler(error_callback)

@run_async
def start(bot, update):
    logging.debug("detectivepikachubot:start: %s %s" % (bot, update))
    (chat_id, chat_type, user_id, text, message) = extract_update_info(update)

    if chat_type != "private":
        deletion_text = "\n\n<i>(Este mensaje se borrará en 60 segundos)</i>"
        try:
            bot.deleteMessage(chat_id=chat_id,message_id=message.message_id)
        except:
            pass
    else:
        deletion_text = ""
    sent_message = bot.sendMessage(chat_id=update.message.chat_id, text="📖 ¡Echa un vistazo a <a href='%s'>la ayuda</a> para enterarte de todas las funciones!\n\n🆕 <b>Crear incursión</b>\n<code>/raid Suicune 12:00 Alameda</code>\n\n❄️🔥⚡️ <b>Registrar nivel/equipo</b>\nEscríbeme por privado en @%s el comando <code>/register</code>. En vez de eso, puedes preguntar <code>quién soy?</code> a @profesoroak_bot y reenviarme su respuesta.\n\n🔔 <b>Configurar alertas</b>\nEscríbeme por privado en @%s el comando <code>/alerts</code>.%s" % (config["telegram"]["bothelp"],config["telegram"]["botalias"],config["telegram"]["botalias"], deletion_text), parse_mode=telegram.ParseMode.HTML, disable_web_page_preview=True)
    if chat_type != "private":
        Thread(target=delete_message_timed, args=(chat_id, sent_message.message_id, 40, bot)).start()

@run_async
def pikaping(bot, update):
    logging.debug("detectivepikachubot:pikaping: %s %s" % (bot, update))
    (chat_id, chat_type, user_id, text, message) = extract_update_info(update)

    sent_dt = message.date
    now_dt = datetime.now()
    timediff = now_dt - sent_dt

    if chat_type != "private":
        try:
            bot.deleteMessage(chat_id=chat_id,message_id=message.message_id)
        except:
            pass
    sent_message = bot.sendMessage(chat_id=update.message.chat_id, text="Pikapong! %ds" % (timediff.seconds), parse_mode=telegram.ParseMode.HTML, disable_web_page_preview=True)
    if chat_type != "private":
        Thread(target=delete_message_timed, args=(chat_id, sent_message.message_id, 10, bot)).start()

@run_async
def register(bot, update):
    logging.debug("detectivepikachubot:raids: %s %s" % (bot, update))
    (chat_id, chat_type, user_id, text, message) = extract_update_info(update)
    user_username = message.from_user.username

    if not edit_check_private(chat_id, chat_type, user_username, "register", bot):
        delete_message(chat_id, message.message_id, bot)
        return

    validation = getCurrentValidation(user_id)
    logging.debug(validation)
    if validation is not None:
        bot.sendMessage(chat_id=chat_id, text="❌ Ya has iniciado un proceso de validación. Debes completarlo antes de intentar comenzar de nuevo, o esperar 6 horas a que caduque.", parse_mode=telegram.ParseMode.MARKDOWN)
        return

    user = getUser(user_id)
    if user is not None and user["validation"] != "none":
        bot.sendMessage(chat_id=chat_id, text="⚠ Ya te has validado anteriormente. *No es necesario* que vuelvas a validarte, a no ser que quieras cambiar tu nombre de entrenador, equipo o bajar de nivel. Si solo has subido de nivel, basta con que envíes una captura de pantalla de tu nuevo nivel, sin necesidad de hacer el proceso completo.\n\nSi aún así quieres, puedes continuar con el proceso, o sino *espera 6 horas* a que caduque.", parse_mode=telegram.ParseMode.MARKDOWN)
    else:
        user = {"id": user_id, "username": user_username}
        saveUser(user)

    pokemon = random.choice(validation_pokemons)
    name = random.choice(validation_names)
    validation = { "usuario_id": chat_id, "step": "waitingtrainername", "pokemon": pokemon, "pokemonname": name }
    saveValidation(validation)

    bot.sendMessage(chat_id=chat_id, text="¿Cómo es el nombre de entrenador que aparece en tu perfil del juego?\n\n_Acabas de iniciar el proceso de validación. Debes completarlo antes de 6 horas, o caducará. Si te equivocas y deseas volver a empezar, debes esperar esas 6 horas._", parse_mode=telegram.ParseMode.MARKDOWN)

@run_async
def settimezone(bot, update, args=None):
    logging.debug("detectivepikachubot:settimezone: %s %s %s" % (bot, update, args))
    (chat_id, chat_type, user_id, text, message) = extract_update_info(update)
    chat_title = message.chat.title
    group_alias = None
    if hasattr(message.chat, 'username') and message.chat.username is not None:
        group_alias = message.chat.username

    if chat_type != "channel" and (not is_admin(chat_id, user_id, bot) or isBanned(user_id)):
        return

    if chat_type == "private":
        bot.sendMessage(chat_id=chat_id, text="❌ Este comando solo funciona en canales y grupos")
        return

    try:
        bot.deleteMessage(chat_id=chat_id,message_id=message.message_id)
    except:
        pass

    if args is None or len(args)!=1 or len(args[0])<3 or len(args[0])>60:
        bot.sendMessage(chat_id=chat_id, text="❌ Debes pasarme un nombre de zona horaria en inglés, por ejemplo, `America/Montevideo` o `Europe/Madrid`.", parse_mode=telegram.ParseMode.MARKDOWN)
        return

    tz = searchTimezone(args[0])
    if tz is not None:
        group = getGroup(chat_id)
        group["timezone"] = tz["name"]
        group["title"] = chat_title
        group["alias"] = group_alias
        saveGroup(group)
        bot.sendMessage(chat_id=chat_id, text="👌 Establecida zona horaria *%s*." % group["timezone"], parse_mode=telegram.ParseMode.MARKDOWN)
        now = datetime.now(timezone(group["timezone"])).strftime("%H:%M")
        bot.sendMessage(chat_id=chat_id, text="🕒 Comprueba que la hora sea correcta: %s" % now, parse_mode=telegram.ParseMode.MARKDOWN)
    else:
        bot.sendMessage(chat_id=chat_id, text="❌ No se ha encontrado ninguna zona horaria válida con ese nombre.", parse_mode=telegram.ParseMode.MARKDOWN)

@run_async
def settalkgroup(bot, update, args=None):
    logging.debug("detectivepikachubot:settalkgroup: %s %s %s" % (bot, update, args))
    (chat_id, chat_type, user_id, text, message) = extract_update_info(update)
    chat_title = message.chat.title
    group_alias = None
    if hasattr(message.chat, 'username') and message.chat.username is not None:
        group_alias = message.chat.username

    if not is_admin(chat_id, user_id, bot) or isBanned(user_id):
        return

    if chat_type == "private":
        bot.sendMessage(chat_id=chat_id, text="❌ Este comando solo funciona en canales y grupos")
        return

    try:
        bot.deleteMessage(chat_id=chat_id,message_id=message.message_id)
    except:
        pass

    if args is None or len(args)!=1 or (args[0] != "-" and (len(args[0])<3 or len(args[0])>60 or re.match("@?[a-zA-Z]([a-zA-Z0-9_]+)$|https://t\.me/joinchat/[a-zA-Z0-9_]+$",args[0]) is None) ):
        bot.sendMessage(chat_id=chat_id, text="❌ Debes pasarme por parámetro un alias de grupo o un enlace de `t.me` de un grupo privado, por ejemplo `@pokemongobadajoz` o `https://t.me/joinchat/XXXXERK2ZfB3ntXXSiWUx`.", parse_mode=telegram.ParseMode.MARKDOWN)
        return

    group = getGroup(chat_id)
    group["alias"] = group_alias
    if args[0] != "-":
        group["title"] = chat_title
        group["talkgroup"] = args[0].replace("@","")
        saveGroup(group)
        if re.match("@?[a-zA-Z]([a-zA-Z0-9_]+)$",args[0]) is not None:
            bot.sendMessage(chat_id=chat_id, text="👌 Establecido grupo de charla a @%s." % ensure_escaped(group["talkgroup"]), parse_mode=telegram.ParseMode.MARKDOWN)
        else:
            bot.sendMessage(chat_id=chat_id, text="👌 Establecido grupo de charla a %s." % ensure_escaped(group["talkgroup"]), parse_mode=telegram.ParseMode.MARKDOWN)
    else:
        group["talkgroup"] = None
        saveGroup(group)
        bot.sendMessage(chat_id=chat_id, text="👌 Eliminada la referencia al grupo de charla.", parse_mode=telegram.ParseMode.MARKDOWN)

@run_async
def setspreadsheet(bot, update, args=None):
  logging.debug("detectivepikachubot:setspreadsheet: %s %s %s" % (bot, update, args))
  (chat_id, chat_type, user_id, text, message) = extract_update_info(update)
  chat_title = message.chat.title
  group_alias = None
  if hasattr(message.chat, 'username') and message.chat.username is not None:
      group_alias = message.chat.username

  if chat_type == "private":
    bot.sendMessage(chat_id=chat_id, text="❌ Este comando solo funciona en canales y grupos.")
    return

  if chat_type != "channel" and (not is_admin(chat_id, user_id, bot) or isBanned(user_id)):
    return

  try:
      bot.deleteMessage(chat_id=chat_id,message_id=message.message_id)
  except:
      pass

  if args is None or len(args)!=1:
    bot.sendMessage(chat_id=chat_id, text="❌ Debes pasarme la URL de la Google Spreadsheet como un único parámetro.")
    return

  m = re.search('docs.google.com/.*spreadsheets/d/([a-zA-Z0-9_-]+)', args[0], flags=re.IGNORECASE)
  if m is None:
    bot.sendMessage(chat_id=chat_id, text="❌ Vaya, no he reconocido esa URL... %s" % args[0])
  else:
    spreadsheet_id = m.group(1)
    group = getGroup(chat_id)

    if group is None:
        if chat_type == "channel":
            bot.sendMessage(chat_id=chat_id, text="No tengo información de este canal. Un administrador debe utilizar al menos una vez el comando `/settings` antes de poder utilizarme en un canal. Si estaba funcionando hasta ahora y he dejado de hacerlo, avisa en @detectivepikachuayuda.", parse_mode=telegram.ParseMode.MARKDOWN)
        else:
            bot.sendMessage(chat_id=chat_id, text="No consigo encontrar la información de este grupo. ¿He saludado al entrar? Prueba a echarme y a meterme de nuevo. Si lo has promocionado a supergrupo después de entrar yo, esto es normal. Si estaba funcionando hasta ahora y he dejado de hacerlo, avisa en @detectivepikachuayuda.", parse_mode=telegram.ParseMode.MARKDOWN)
        return

    group["title"] = chat_title
    group["spreadsheet"] = spreadsheet_id
    group["alias"] = group_alias
    saveGroup(group)
    bot.sendMessage(chat_id=chat_id, text="👌 Establecido hoja de cálculo con identificador `%s`.\n\nDebes usar `/refresh` ahora para hacer la carga inicial de los gimnasios y cada vez que modifiques el documento para recargarlos." % ensure_escaped(spreadsheet_id), parse_mode=telegram.ParseMode.MARKDOWN)

@run_async
def refresh(bot, update, args=None):
  logging.debug("detectivepikachubot:refresh: %s %s %s" % (bot, update, args))
  (chat_id, chat_type, user_id, text, message) = extract_update_info(update)
  chat_title = message.chat.title
  group_alias = None
  if hasattr(message.chat, 'username') and message.chat.username is not None:
      group_alias = message.chat.username

  if chat_type == "private":
    bot.sendMessage(chat_id=chat_id, text="❌ Este comando solo funciona en canales y grupos.")
    return

  if chat_type != "channel" and (not is_admin(chat_id, user_id, bot) or isBanned(user_id)):
    return

  try:
      bot.deleteMessage(chat_id=chat_id,message_id=message.message_id)
  except:
      pass

  grupo = getGroup(chat_id)
  if grupo is None or grupo["spreadsheet"] is None:
    bot.sendMessage(chat_id=chat_id, text="❌ Debes configurar primero la hoja de cálculo de las ubicaciones con el comando `/setspreadsheet`", parse_mode=telegram.ParseMode.MARKDOWN)
    return

  sent_message = bot.sendMessage(chat_id=chat_id, text="🌎 Refrescando lista de gimnasios...\n\n_Si no recibes una confirmación tras unos segundos, algo ha ido mal. Este mensaje se borrará en unos segundos._", parse_mode=telegram.ParseMode.MARKDOWN)
  Thread(target=delete_message_timed, args=(chat_id, sent_message.message_id, 15, bot)).start()

  response = requests.get("https://docs.google.com/spreadsheet/ccc?key=%s&output=csv" % grupo["spreadsheet"] )
  if response.status_code == 200:
    places = []
    f = StringIO(response.content.decode('utf-8'))
    csvreader = csv.reader(f, delimiter=',', quotechar='"')
    counter = 0
    incomplete_rows = []
    for row in csvreader:
      if counter > 3000:
          bot.sendMessage(chat_id=chat_id, text="❌ ¡No se permiten más de 3000 gimnasios por grupo!")
          return
      if counter == 0 and len(row) == 0:
          bot.sendMessage(chat_id=chat_id, text="❌ ¡No se han encontrado datos! ¿La hoja de cálculo es pública?")
      elif len(row) < 4:
          rownumber = counter + 1
          bot.sendMessage(chat_id=chat_id, text="❌ ¡No se han podido cargar los gimnasios! La fila %s no tiene las 4 columnas requeridas." % rownumber)
          return
      names = row[3].split(",")
      latitude = str(row[1]).replace(",",".")
      longitude = str(row[2]).replace(",",".")
      m = re.search('^-?[0-9]+.[0-9]+$', latitude, flags=re.IGNORECASE)
      m2 = re.search('^-?[0-9]+.[0-9]+$', longitude, flags=re.IGNORECASE)
      if m is None or m2 is None:
        rownumber = counter + 1
        bot.sendMessage(chat_id=chat_id, text="❌ ¡No se han podido cargar los gimnasios! El formato de las coordenadas en la fila %s es incorrecto. Recuerda que deben tener un único separador decimal. Si tienes problemas, elimina el formato de las celdas numéricas." % (rownumber))
        return
      for i,r in enumerate(names):
        names[i] = names[i].strip()
        if len(names[i]) < 2:
          del names[i]
      if len(names)==0:
        incomplete_rows.append(counter)
      if len(row) > 4:
          tags = row[4].split(",")
          for i,r in enumerate(tags):
              tags[i] = tags[i].strip()
      else:
          tags = []
      if len(row) > 5 and row[5].strip()!="":
          zones = row[5].split(",")
          for i,r in enumerate(zones):
              zones[i] = zones[i].strip()
      else:
          zones = []
      places.append({"desc":row[0],"latitude":latitude,"longitude":longitude,"names":names, "tags":tags, "zones":zones});
      counter = counter + 1

    if counter > 1:
      grupo["title"] = chat_title
      grupo["alias"] = group_alias
      saveGroup(grupo)
      removedalerts = getRemovedAlerts(chat_id, places)
      if savePlaces(chat_id, places):
          places = getPlaces(grupo["id"])
          if len(incomplete_rows) > 0:
              bot.sendMessage(chat_id=chat_id, text="👌 ¡Cargados %i gimnasios correctamente!\n⚠️ %i gimnasios no tienen palabras clave. Recuerda que son obligatorias para que puedan ser encontrados." % (len(places), len(incomplete_rows)))
          else:
              bot.sendMessage(chat_id=chat_id, text="👌 ¡Cargados %i gimnasios correctamente!" % len(places))
          # Warn users with removed alerts due to deleted/replaced gyms
          if removedalerts is not None and len(removedalerts)>0:
              for ra in removedalerts:
                  try:
                      bot.sendMessage(chat_id=ra["usuario_id"], text="🚫 Se ha borrado una alerta que tenías programada para el gimnasio <b>%s</b> del grupo <b>%s</b> porque un administrador lo ha borrado o reemplazado por otro con un nombre diferente." % (ra["gimnasio_name"],ra["grupo_title"]), parse_mode=telegram.ParseMode.HTML)
                  except:
                      logging.debug("detectivepikachubot:refresh: Can't alert user %s about deleted alert on %s" % (ra["usuario_id"],ra["gimnasio_name"]))
                      pass
      else:
          bot.sendMessage(chat_id=chat_id, text="❌ ¡No se han podido refrescar los gimnasios! Comprueba que no haya dos gimnasios con el mismo nombre.")
    else:
      bot.sendMessage(chat_id=chat_id, text="❌ ¡No se han podido cargar los gimnasios! ¿Seguro que está en el formato correcto? Ten en cuenta que para que funcione, debe haber al menos 2 gimnasios en el documento.")
  else:
    bot.sendMessage(chat_id=chat_id, text="❌ Error cargando la hoja de cálculo. ¿Seguro que es pública?")

@run_async
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

    if isBanned(user_id):
        return

    m = re.search("@?([a-zA-Z0-9]+), eres (Rojo|Azul|Amarillo) L([0-9]{1,2})[ .]",text, flags=re.IGNORECASE)
    if m is not None:
        if forward_id == 201760961:
            if (this_date - forward_date).total_seconds() < 120:
                m2 = re.search("✅",text, flags=re.IGNORECASE)
                if m2 is not None:
                    fuser = getUserByTrainername(text)
                    if fuser is None or fuser["trainername"] == m.group(1):
                        thisuser = {}
                        thisuser["id"] = user_id
                        thisuser["team"] = m.group(2)
                        thisuser["level"] = m.group(3)
                        thisuser["username"] = user_username
                        thisuser["trainername"] = m.group(1)
                        user = getUser(user_id)
                        if user is not None and user["validation"] == "internal":
                            thisuser["validation"] = "internal"
                        else:
                            thisuser["validation"] = "oak"
                        bot.sendMessage(chat_id=chat_id, text="👌 ¡De acuerdo! He reconocido que tu nombre de entrenador es *%s*, eres del equipo *%s* y de *nivel %s*.\n\nA partir de ahora aparecerá tu equipo y nivel en las incursiones en las que participes. Si subes de nivel o te cambias el nombre de entrenador, repite esta operación para que pueda reflejarlo bien en las incursiones." % (ensure_escaped(thisuser["trainername"]), thisuser["team"], thisuser["level"]), parse_mode=telegram.ParseMode.MARKDOWN)
                        saveWholeUser(thisuser)
                    else:
                        bot.sendMessage(chat_id=chat_id, text="❌ Ese nombre de entrenador ya está asociado a otra cuenta de Telegram. Envía un correo a `%s` indicando tu alias en telegram y tu nombre de entrenador en el juego para que revisemos el caso manualmente." % config["telegram"]["validationsmail"], parse_mode=telegram.ParseMode.MARKDOWN)
                        return
                else:
                    bot.sendMessage(chat_id=chat_id, text="❌ Parece que tu cuenta aún no está completamente validada con @profesoroak\_bot. No puedo aceptar tu nivel y equipo hasta que te valides.", parse_mode=telegram.ParseMode.MARKDOWN)
            else:
                bot.sendMessage(chat_id=chat_id, text="❌ Ese mensaje es demasiado antiguo. ¡Debes reenviarme un mensaje más reciente!", parse_mode=telegram.ParseMode.MARKDOWN)
        else:
            bot.sendMessage(chat_id=chat_id, text="❌ ¿Has copiado y pegado el mensaje del @profesoroak\_bot? Tienes que usar la opción de *reenviar*, no sirve copiando y pegando.", parse_mode=telegram.ParseMode.MARKDOWN)
    else:
        if forward_id == 201760961:
            bot.sendMessage(chat_id=chat_id, text="❌ No he reconocido ese mensaje de @profesoroak\_bot. ¿Seguro que le has preguntado `Quién soy?` y no otra cosa?", parse_mode=telegram.ParseMode.MARKDOWN)

@run_async
def joinedChat(bot, update):
    logging.debug("detectivepikachubot:joinedChat: %s %s" % (bot, update))
    (chat_id, chat_type, user_id, text, message) = extract_update_info(update)
    try:
        if len(message.new_chat_members)>0:
            new_chat_member = message.new_chat_members[0]
            if new_chat_member.username == config["telegram"]["botalias"] and chat_type != "private":
                chat_title = message.chat.title
                logging.debug("detectivepikachubot:joinedChat: Oh, I'm new at %s" % chat_title);
                group = getGroup(chat_id)
                if group is None:
                    saveGroup({"id":chat_id, "title":message.chat.title})
                message_text = "¡Hola a todos los miembros de *%s*!\n\nAntes de poder utilizarme, un administrador tiene que configurar algunas cosas. Comenzad viendo la ayuda con el comando `/help` para enteraros de todas las funciones. Aseguraos de ver la *ayuda para administradores*, donde se explica en detalle todos los pasos que se deben seguir." % ensure_escaped(chat_title)
                Thread(target=send_message_timed, args=(chat_id, message_text, 3, bot)).start()
    except Exception as e:
        logging.debug("detectivepikachubot:joinedChat: Exception entering in %s: %s" % (chat_title,str(e)));
        pass
    return

@run_async
def processMessage(bot, update):
    (chat_id, chat_type, user_id, text, message) = extract_update_info(update)

    if chat_type == "channel":
        return

    if chat_type == "group" or chat_type == "supergroup":
        group = getGroup(chat_id)
        if group is None or group["babysitter"] == 0:
            logging.debug("detectivepikachubot:processMessage ignoring message")
            return

    user_username = message.from_user.username

    if isBanned(user_id) or isBanned(chat_id):
        return

    if chat_type == "private":
        # Are we in a validation process?
        validation = getCurrentValidation(user_id)
        user = getUser(user_id)
        if validation is not None:
            # Expecting username
            if validation["step"] == "waitingtrainername" and text is not None:
                m = re.match(r'[a-zA-Z0-9]{4,15}$', text)
                if m is not None:
                    fuser = getUserByTrainername(text)
                    if fuser is None or fuser["id"] == user["id"]:
                        validation["trainername"] = text
                        validation["step"] = "waitingscreenshot"
                        saveValidation(validation)
                        bot.sendMessage(chat_id=chat_id, text="Así que tu nombre de entrenador es *%s*.\n\nPara completar el registro, debes enviarme una captura de pantalla de tu perfil del juego. En la captura de pantalla debes tener un *%s* llamado *%s* como compañero. Si no tienes ninguno, o no te apetece cambiar ahora de compañero, puedes volver a comenzar el registro en cualquier otro momento." % (validation["trainername"], validation["pokemon"].capitalize(),validation["pokemonname"]), parse_mode=telegram.ParseMode.MARKDOWN)
                    else:
                        bot.sendMessage(chat_id=chat_id, text="❌ Ese nombre de entrenador ya está asociado a otra cuenta de Telegram. Si realmente es tuyo, envía un correo a `%s` indicando tu alias de Telegram y tu nombre de entrenador para que revisemos el caso manualmente.\n\nSi lo has escrito mal y realmente no era ese el nombre, dime entonces, ¿cómo es el nombre de entrenador que aparece en tu perfil del juego?" % config["telegram"]["validationsmail"], parse_mode=telegram.ParseMode.MARKDOWN)
                        return
                else:
                    bot.sendMessage(chat_id=chat_id, text="❌ No te entiendo. Pon únicamente el nombre de entrenador que aparece en tu perfil del juego. No puede tener espacios y debe tener entre 4 y 15 caracteres de longitud.", parse_mode=telegram.ParseMode.MARKDOWN)
                    return
            # Expecting screenshot
            elif validation["step"] == "waitingscreenshot" and hasattr(message, 'photo') and message.photo is not None and len(message.photo) > 0:
                photo = bot.get_file(update.message.photo[-1]["file_id"])
                logging.debug("Downloading file %s" % photo)
                filename = sys.path[0] + "/photos/profile-%s-%s-%s.jpg" % (user_id, validation["id"], int(time.time()))
                urllib.request.urlretrieve(photo["file_path"], filename)
                try:
                    (trainer_name, level, chosen_color, chosen_pokemon, pokemon_name, chosen_profile) = parse_profile_image(filename, validation["pokemon"])
                    #output = "Información reconocida:\n - Nombre de entrenador: %s\n - Nivel: %s\n - Equipo: %s\n - Pokémon: %s\n - Nombre del Pokémon: %s" % (trainer_name, level, chosen_color, chosen_pokemon, pokemon_name)
                    #bot.sendMessage(chat_id=chat_id, text=text,parse_mode=telegram.ParseMode.MARKDOWN)
                    output = None
                except Exception as e:
                    logging.debug("Exception validating: %s" % str(e))
                    output = "❌ Ha ocurrido un error procesando la imagen. Asegúrate de enviar una captura de pantalla completa del juego en un teléfono móvil. No son válidas las capturas en tablets ni otros dispositivos ni capturas recortadas o alteradas. Puedes volver a intentarlo enviando otra captura. Si no consigues que la reconozca, envía un correo a `%s` indicando tu alias de Telegram y tu nombre de entrenador para que revisemos el caso manualmente." % config["telegram"]["validationsmail"]
                    bot.sendMessage(chat_id=chat_id, text=output, parse_mode=telegram.ParseMode.MARKDOWN)
                    return
                if chosen_profile is None:
                    output = "❌ La captura de pantalla no parece válida. Asegúrate de enviar una captura de pantalla completa del juego en un teléfono móvil. No son válidas las capturas en tablets ni otros dispositivos ni capturas recortadas o alteradas. Puedes volver a intentarlo enviando otra captura. Si no consigues que la reconozca, envía un correo a `%s` indicando tu alias de Telegram y tu nombre de entrenador para que revisemos el caso manualmente." % config["telegram"]["validationsmail"]
                elif trainer_name.lower() != validation["trainername"].lower() and distance(trainer_name.lower(),validation["trainername"].lower())>2:
                    output = "❌ No he reconocido correctamente el *nombre del entrenador*. ¿Seguro que lo has escrito bien? Puedes volver a enviar otra captura. Si te has equivocado, espera 6 horas a que caduque la validación y vuelve a comenzar de nuevo. Si lo has escrito bien y no consigues que lo reconozca, envía un correo a `%s` indicando tu alias de Telegram y tu nombre de entrenador para que revisemos el caso manualmente." % config["telegram"]["validationsmail"]
                elif level is None:
                    output = "❌ No he reconocido correctamente el *nivel*. Puedes volver a intentar completar la validación enviando otra captura. Si no consigues que la reconozca, envía un correo a `%s` indicando tu alias de Telegram y tu nombre de entrenador para que revisemos el caso manualmente." % config["telegram"]["validationsmail"]
                elif chosen_color is None:
                    output = "❌ No he reconocido correctamente el *equipo*. Puedes volver a intentar completar la validación enviando otra captura. Si no consigues que la reconozca, envía un correo a `%s` indicando tu alias de Telegram y tu nombre de entrenador para que revisemos el caso manualmente." % config["telegram"]["validationsmail"]
                elif pokemon_name.lower() != validation["pokemonname"].lower() and distance(pokemon_name.lower(),validation["pokemonname"].lower())>2:
                    output = "❌ No he reconocido correctamente el *nombre del Pokémon*. ¿Le has cambiado el nombre a *%s* como te dije? Puedes volver a intentar completar la validación enviando otra captura. Si no consigues que la reconozca, envía un correo a `%s` indicando tu alias de Telegram y tu nombre de entrenador para que revisemos el caso manualmente." % (validation["pokemonname"], config["telegram"]["validationsmail"])
                elif chosen_pokemon != validation["pokemon"]:
                    output = "❌ No he reconocido correctamente el *Pokémon*. ¿Has puesto de compañero a *%s* como te dije? Puedes volver a intentarlo enviando otra captura. Si no consigues que la reconozca, envía un correo a `%s` indicando tu alias de Telegram y tu nombre de entrenador para que revisemos el caso manualmente." % (validation["pokemon"], config["telegram"]["validationsmail"])
                if output is not None:
                    validation["tries"] = validation["tries"] + 1
                    if validation["tries"] > 3:
                        validation["step"] = "failed"
                    saveValidation(validation)
                    bot.sendMessage(chat_id=chat_id, text=output, parse_mode=telegram.ParseMode.MARKDOWN)
                    return
                # Validation ok!
                user["level"] = level
                user["team"] = chosen_color
                user["trainername"] = validation["trainername"]
                user["validation"] = "internal"
                saveWholeUser(user)
                validation["level"] = level
                validation["team"] = chosen_color
                validation["step"] = "completed"
                saveValidation(validation)
                output = "👌 Has completado el proceso de validación correctamente. Se te ha asignado el equipo *%s* y el nivel *%s*.\n\nA partir de ahora aparecerán tu nivel y equipo reflejados en las incursiones en las que participes.\n\nSi subes de nivel en el juego y quieres que se refleje en las incursiones, puedes enviarme en cualquier momento otra captura de tu perfil del juego, no es necesario que cambies tu Pokémon acompañante." % (validation["team"], validation["level"])
                bot.sendMessage(chat_id=chat_id, text=output,parse_mode=telegram.ParseMode.MARKDOWN)
            elif validation["step"] == "failed":
                output = "❌ Has excedido el número máximo de intentos para esta validación. Debes esperar a que caduque la validación actual para volver a intentarlo. También puedes enviar un correo a `%s` indicando tu alias de Telegram y tu nombre de entrenador para que revisemos el caso manualmente." % config["telegram"]["validationsmail"]
                bot.sendMessage(chat_id=chat_id, text=output,parse_mode=telegram.ParseMode.MARKDOWN)
        # Not expecting validation, probably screenshot to update level
        elif user is not None and (user["validation"] == "internal" or user["validation"] == "oak") and hasattr(message, 'photo') and message.photo is not None and len(message.photo) > 0:
            photo = bot.get_file(update.message.photo[-1]["file_id"])
            logging.debug("Downloading file %s" % photo)
            filename = sys.path[0] + "/photos/profile-%s-updatelevel-%s.jpg" % (user_id, int(time.time()))
            urllib.request.urlretrieve(photo["file_path"], filename)
            try:
                (trainer_name, level, chosen_color, chosen_pokemon, pokemon_name, chosen_profile) = parse_profile_image(filename, None)
                #output = "Información reconocida:\n - Nombre de entrenador: %s\n - Nivel: %s\n - Equipo: %s\n - Pokémon: %s\n - Nombre del Pokémon: %s" % (trainer_name, level, chosen_color, chosen_pokemon, pokemon_name)
                #bot.sendMessage(chat_id=chat_id, text=text,parse_mode=telegram.ParseMode.MARKDOWN)
                output = None
            except Exception as e:
                bot.sendMessage(chat_id=chat_id, text="❌ Ha ocurrido un error procesando la imagen. Asegúrate de enviar una captura de pantalla completa del juego en un teléfono móvil. No son válidas las capturas en tablets ni otros dispositivos ni capturas recortadas o alteradas. Si no consigues que la reconozca, pide ayuda en @detectivepikachuayuda.", parse_mode=telegram.ParseMode.MARKDOWN)
                return
            if chosen_profile is None:
                output = "❌ La captura de pantalla no parece válida. Asegúrate de enviar una captura de pantalla completa del juego en un teléfono móvil. No son válidas las capturas en tablets ni otros dispositivos ni capturas recortadas o alteradas. Puedes volver a intentarlo enviando otra captura. Si no consigues que la reconozca, envía un correo a `%s` indicando tu alias de Telegram y tu nombre de entrenador para que revisemos el caso manualmente." % config["telegram"]["validationsmail"]
            elif trainer_name.lower() != user["trainername"].lower() and distance(trainer_name.lower(),user["trainername"].lower())>2:
                output = "❌ No he reconocido correctamente el *nombre del entrenador*. Si no consigues que lo reconozca, envía un correo a `%s` indicando tu alias de Telegram y tu nombre de entrenador para que revisemos el caso manualmente." % config["telegram"]["validationsmail"]
            elif level is None:
                output = "❌ No he reconocido correctamente el *nivel*. Si no consigues que la reconozca, envía un correo a `%s` indicando tu alias de Telegram y tu nombre de entrenador para que revisemos el caso manualmente." % config["telegram"]["validationsmail"]
            elif int(user["level"]) == int(level):
                output = "❌ En la captura pone que eres *nivel %s*, pero yo ya sabía que tenías ese nivel." % user["level"]
            elif int(user["level"]) > int(level):
                output = "❌ En la captura pone que eres *nivel %s*, pero ya eras *nivel %s*. ¿Cómo has bajado de nivel?" % (level,user["level"])
            elif chosen_color != user["team"]:
                output = "❌ No he reconocido correctamente el *equipo*. Si no consigues que la reconozca, envía un correo a `%s` indicando tu alias de Telegram y tu nombre de entrenador para que revisemos el caso manualmente." % config["telegram"]["validationsmail"]
            if output is not None:
                bot.sendMessage(chat_id=chat_id, text=output, parse_mode=telegram.ParseMode.MARKDOWN)
                return
            # Validation ok!
            user["level"] = level
            saveWholeUser(user)
            output = "👌 Se ha actualizado tu nivel al *%s*.\n\nSi vuelves a subir de nivel en el juego y quieres que se refleje en las incursiones, puedes enviarme en cualquier momento otra captura de tu perfil del juego." % (user["level"])
            bot.sendMessage(chat_id=chat_id, text=output,parse_mode=telegram.ParseMode.MARKDOWN)
        # Is this a forwarded message from Oak?
        if text is not None and len(text) > 0:
            logging.debug(text)
            registerOak(bot, update)
    else:
        if group is not None and group["babysitter"] == 1 and not is_admin(chat_id, user_id, bot):
            delete_message(chat_id, message.message_id, bot)
            if group["talkgroup"] is not None:
                if re.match("@?[a-zA-Z]([a-zA-Z0-9_]+)$", group["talkgroup"]) is not None:
                    text_talkgroup="\n\nPara hablar puedes utilizar el grupo @%s." % ensure_escaped(group["talkgroup"])
                else:
                    text_talkgroup="\n\nPara hablar puedes utilizar el grupo %s." % ensure_escaped(group["talkgroup"])
            else:
                text_talkgroup="";
            if user_username is not None:
                text = "@%s en este canal solo se pueden crear incursiones y participar en ellas, pero no se puede hablar.%s\n\n_(Este mensaje se borrará en unos segundos)_" % (ensure_escaped(user_username), text_talkgroup)
            else:
                text = "En este canal solo se pueden crear incursiones y participar en ellas, pero no se puede hablar.%s\n\n_(Este mensaje se borrará en unos segundos)_" % text_talkgroup
            sent_message = bot.sendMessage(chat_id=chat_id, text=text,parse_mode=telegram.ParseMode.MARKDOWN)
            Thread(target=delete_message_timed, args=(chat_id, sent_message.message_id, 13, bot)).start()
    return

@run_async
def channelCommands(bot, update):
    logging.debug("detectivepikachubot:channelCommands: %s %s" % (bot, update))
    (chat_id, chat_type, user_id, text, message) = extract_update_info(update)

    try:
        args = re.sub(r"^/[a-zA-Z0-9_]+", "", text).strip().split(" ")
        if len(args) == 1 and args[0] == "":
            args = []
    except:
        args = None
    m = re.match("/([a-zA-Z0-9_]+)", text)
    if m is not None:
        command = m.group(1).lower()
        logging.debug("detectivepikachubot:channelCommands: Possible command %s" % command)
        if command == "setspreadsheet":
            setspreadsheet(bot, update, args)
        elif command == "settimezone":
            settimezone(bot, update, args)
        elif command == "refresh":
            refresh(bot, update, args)
        elif command == "settings":
            settings(bot, update)
        elif command == "gym":
            gym(bot, update, args)
        elif command == "raid":
            raid(bot, update, args)
        elif command == "list":
            list(bot, update)
        elif command == "borrar":
            borrar(bot, update, args)
        elif command == "cancelar":
            cancelar(bot, update, args)
        elif command == "reflotar":
            reflotar(bot, update, args)
        elif command == "reflotartodo" or command=="reflotartodas":
            reflotartodas(bot, update, args)
        elif command == "reflotarhoy":
            reflotarhoy(bot, update, args)
        elif command == "reflotaractivas" or command=="reflotaractivo":
            reflotaractivas(bot, update, args)
        elif command == "cambiarhora" or command == "hora":
            cambiarhora(bot, update, args)
        elif command == "cambiarhorafin" or command == "horafin":
            cambiarhorafin(bot, update, args)
        elif command == "cambiargimnasio" or command == "gimnasio":
            cambiargimnasio(bot, update, args)
        elif command == "cambiarpokemon" or command == "pokemon":
            cambiarpokemon(bot, update, args)
        elif command == "stats" or command == "ranking":
            stats(bot, update, args)
        else:
            # Default to process normal message for babysitter mode
            processMessage(bot,update)

@run_async
def settings(bot, update):
    logging.debug("detectivepikachubot:settings: %s %s" % (bot, update))
    (chat_id, chat_type, user_id, text, message) = extract_update_info(update)
    chat_title = message.chat.title

    if chat_type == "private":
      bot.sendMessage(chat_id=chat_id, text="Solo funciono en canales y grupos")
      return
    if chat_type != "channel" and (not is_admin(chat_id, user_id, bot) or isBanned(user_id)):
      return

    try:
        bot.deleteMessage(chat_id=chat_id,message_id=message.message_id)
    except:
        pass

    group = getGroup(chat_id)
    if group is None and chat_type == "channel":
        saveGroup({"id":chat_id, "title":message.chat.title})
        group = getGroup(chat_id)
    elif group is None:
        bot.sendMessage(chat_id=chat_id, text="No consigo encontrar la información de este grupo. ¿He saludado al entrar? Prueba a echarme y a meterme de nuevo. Si lo has promocionado a supergrupo después de entrar yo, esto es normal. Si estaba funcionando hasta ahora y he dejado de hacerlo, avisa en @detectivepikachuayuda.", parse_mode=telegram.ParseMode.MARKDOWN)
        return

    if group["settings_message"] is not None:
        try:
            bot.deleteMessage(chat_id=chat_id,message_id=group["settings_message"])
        except:
            pass

    group_alias = None
    if hasattr(message.chat, 'username') and message.chat.username is not None:
        group_alias = message.chat.username
    group["alias"] = group_alias
    group["title"] = chat_title

    settings_markup = get_settings_keyboard(chat_id)
    message = bot.sendMessage(chat_id=chat_id, text="Cargando preferencias del grupo. Un momento...")
    group["settings_message"] = message.message_id
    saveGroup(group)
    Thread(target=update_settings_message_timed, args=(chat_id, 1, bot)).start()

@run_async
def list(bot, update):
  logging.debug("detectivepikachubot:list: %s %s" % (bot, update))
  (chat_id, chat_type, user_id, text, message) = extract_update_info(update)
  if chat_type == "private":
    bot.sendMessage(chat_id=chat_id, text="Solo funciono en canales y grupos")
    return

  try:
      bot.deleteMessage(chat_id=chat_id,message_id=message.message_id)
  except:
      pass

  if chat_type != "channel" and (not is_admin(chat_id, user_id, bot) or isBanned(user_id)):
    return

  gyms = getPlaces(chat_id)
  if len(gyms)==0:
    bot.sendMessage(chat_id=chat_id, text="No estoy configurado en este grupo")
    return
  output = "Lista de gimnasios conocidos (%i):" % len(gyms)
  bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
  for p in gyms:
    output = output + ("\n - %s%s" % (p["desc"], format_gym_emojis(p["tags"])))
  if len(output) > 4096:
      output = output[:4006].rsplit('\n', 1)[0]+"...\n_(El mensaje se ha cortado porque era demasiado largo)_"
  bot.sendMessage(chat_id=chat_id, text=output, parse_mode=telegram.ParseMode.MARKDOWN)

@run_async
def raids(bot, update):
    logging.debug("detectivepikachubot:raids: %s %s" % (bot, update))
    (chat_id, chat_type, user_id, text, message) = extract_update_info(update)
    user_username = message.from_user.username

    if isBanned(chat_id) or isBanned(user_id):
        return

    if not edit_check_private(chat_id, chat_type, user_username, "raids", bot):
        delete_message(chat_id, message.message_id, bot)
        return

    raids = getActiveRaidsforUser(user_id)
    if len(raids) > 0:
        output = "🐲 Estas son las incursiones activas en los grupos en los que participas activamente:\n"
        for r in raids:
            creador = getCreadorRaid(r["id"])
            group = getGrupoRaid(r["id"])
            gym_emoji = created_text = identifier_text = ""
            if group["alias"] is not None:
                incursion_text = "<a href='https://t.me/%s/%s'>Incursión</a>" % (group["alias"], r["message"])
                group_text =  "<a href='https://t.me/%s'>%s</a>" % (group["alias"], html.escape(group["title"]))
            else:
                incursion_text = "Incursión"
                try:
                    group_text = "<i>%s</i>" % (html.escape(group["title"]))
                except:
                    group_text = "<i>(Grupo sin nombre guardado)</i>"
            if group["locations"] == 1:
                if "gimnasio_id" in r.keys() and r["gimnasio_id"] is not None:
                    gym_emoji="🌎"
                else:
                    gym_emoji="❓"
            if r["pokemon"] is not None:
                what_text = "<b>%s</b>" % r["pokemon"]
            else:
                what_text= r["egg"].replace("N","<b>Nivel ").replace("EX","<b>EX") + "</b>"
            what_day = format_text_day(r["timeraid"], group["timezone"], "html")
            if creador["username"] is not None:
                created_text = " por @%s" % (creador["username"])
            if is_admin(r["grupo_id"], user_id, bot):
                identifier_text = " (id <code>%s</code>)" % r["id"]
            if r["status"] == "waiting":
                raid_emoji = "🕒"
            elif r["status"] == "started":
                raid_emoji = "💥"
            else:
                continue
            text = "\n%s %s %sa las <b>%s</b> en %s<b>%s</b>%s%s - %s en %s" % (raid_emoji, what_text, what_day, extract_time(r["timeraid"]), gym_emoji, r["gimnasio_text"], created_text, identifier_text, incursion_text, group_text)
            output = output + text
    else:
        output = "🐲 No hay incursiones activas en los grupos en los que has participado recientemente"
    bot.sendMessage(chat_id=user_id, text=output, parse_mode=telegram.ParseMode.HTML, disable_web_page_preview=True)

@run_async
def profile(bot, update):
    logging.debug("detectivepikachubot:profile: %s %s" % (bot, update))
    (chat_id, chat_type, user_id, text, message) = extract_update_info(update)
    user_username = message.from_user.username

    if isBanned(chat_id):
        return

    if not edit_check_private(chat_id, chat_type, user_username, "profile", bot):
        delete_message(chat_id, message.message_id, bot)
        return

    user = getUser(chat_id)
    if user is not None:
        text_alias = ("*%s*" % user["username"]) if user["username"] is not None else "_Desconocido_"
        text_trainername = ("*%s*" % user["trainername"]) if user["trainername"] is not None else "_Desconocido_"
        text_team = ("*%s*" % user["team"]) if user["team"] is not None else "_Desconocido_"
        text_level = ("*%s*" % user["level"]) if user["level"] is not None else "_Desconocido_"
        if user["banned"] == "1":
            text_validationstatus = "*Baneada*"
        elif user["validation"] == "internal" or user["validation"] == "oak":
            text_validationstatus = "*Validada*"
        else:
            text_validationstatus = "*No validada*"
        output = "ID de Telegram: *%s*\nAlias de Telegram: %s\nNombre de entrenador: %s\nEstado cuenta: %s\nEquipo: %s\nNivel: %s" % (user["id"], text_alias, text_trainername, text_validationstatus, text_team, text_level)
    else:
        output = "❌ No tengo información sobre ti."
    bot.sendMessage(chat_id=user_id, text=output, parse_mode=telegram.ParseMode.MARKDOWN)

@run_async
def stats(bot, update, args = None):
    logging.debug("detectivepikachubot:stats: %s %s" % (bot, update))
    (chat_id, chat_type, user_id, text, message) = extract_update_info(update)

    if isBanned(chat_id):
        return

    if chat_type == "private":
        # User stats
        user_username = message.from_user.username
        user = getUser(chat_id)
        if user is not None and user["validation"] != "none":
            groups = getGroupsByUser(user["id"])
            # Group count
            valid_groups = 0
            for g in groups:
                if g["testgroup"] == 1:
                    continue
                valid_groups = valid_groups + 1
            # Raids
            for g in groups:
                if g["testgroup"] == 1:
                    continue
                if g["alias"] is not None:
                    group_text = "<a href='https://t.me/%s'>%s</a>" % (g["alias"],html.escape(g["title"]))
                else:
                    try:
                        group_text = "<i>%s</i>" % (html.escape(g["title"]))
                    except:
                        group_text = "<i>(Grupo sin nombre guardado)</i>"
                now = datetime.now(timezone(g["timezone"])) + timedelta(hours=2)
                lastweek_start = now.replace(hour=0,minute=0) - timedelta(days=now.weekday(), weeks=1)
                lastweek_end = lastweek_start.replace(hour=23,minute=59) + timedelta(days=6)
                twoweeksago_start = now.replace(hour=0,minute=0) - timedelta(days=now.weekday(), weeks=2)
                twoweeksago_end = twoweeksago_start.replace(hour=23,minute=59) + timedelta(days=6)
                # Personal stats
                userstats_lastweek = getGroupUserStats(g["id"], user_id, lastweek_start, lastweek_end)
                userraids_lastweek = userstats_lastweek["incursiones"] if userstats_lastweek is not None else 0
                userstats_twoweeksago = getGroupUserStats(g["id"], user_id, twoweeksago_start, twoweeksago_end)
                userraids_twoweeksago = userstats_twoweeksago["incursiones"] if userstats_twoweeksago is not None else 0
                # Group stats
                groupstats_lastweek = getRanking(g["id"], lastweek_start, lastweek_end)
                groupsize_lastweek = len(groupstats_lastweek)
                if groupsize_lastweek == 0:
                    continue
                groupposition_lastweek = 0
                groupcounter_lastweek = 0
                lastraidno = 0
                userposition_lastweek = groupsize_lastweek
                for gs in groupstats_lastweek:
                    groupcounter_lastweek = groupcounter_lastweek + 1
                    if gs["incursiones"] != lastraidno:
                        groupposition_lastweek = groupcounter_lastweek
                    lastraidno = gs["incursiones"]
                    if gs["user_id"] == user["id"]:
                        userposition_lastweek = groupposition_lastweek
                        break
                relposition_lastweek = 100 - (100*userposition_lastweek/groupsize_lastweek)
                if userraids_lastweek > userraids_twoweeksago:
                    userraids_moreorless = "%s más" % (userraids_lastweek - userraids_twoweeksago)
                elif userraids_lastweek < userraids_twoweeksago:
                    userraids_moreorless = "%s menos" % (userraids_twoweeksago - userraids_lastweek)
                else:
                    userraids_moreorless = "las mismas"
                daymonth_text = "%s/%s" % (lastweek_start.day, lastweek_start.month)
                output = "%s\n - La semana del %s has hecho <b>%s</b> incursiones (%s que la semana anterior).\n - Estás en <b>%sª</b> posición en número de incursiones realizadas.\n - Son más incursiones que el <b>%.2f%%</b> de entrenadores activos." % (group_text, daymonth_text, userraids_lastweek, userraids_moreorless, userposition_lastweek, relposition_lastweek)
                bot.sendMessage(chat_id=user_id, text=output, parse_mode=telegram.ParseMode.HTML, disable_web_page_preview=True)
        else:
            output = "❌ No tengo información sobre ti. Para poder obtener estadísticas, es necesario estar validado y participar en incursiones."
            bot.sendMessage(chat_id=user_id, text=output, parse_mode=telegram.ParseMode.HTML, disable_web_page_preview=True)
    else:
        # Channel/group stats
        try:
            bot.deleteMessage(chat_id=chat_id,message_id=message.message_id)
        except:
            pass
        # Only for admins
        if chat_type != "channel" and not is_admin(chat_id, user_id, bot):
            return
        # Parse args
        show_week = True
        show_month = False
        if args is not None and len(args)>0:
            if args[0].lower() in ["mes","mensual","month"]:
                show_month = True
                show_week = False
            elif args[0].lower() in ["semana","semanal","week"]:
                show_month = False
                show_week = True
        # Get group info
        group = getGroup(chat_id)
        # Arrange time periods
        (lastweek_start, lastweek_end, lastmonth_start, lastmonth_end) = ranking_time_periods(group["timezone"])
        if show_month:
            if group["rankingmonth"] == 0:
                return
            logging.debug("Ranking from %s to %s" % (lastmonth_start, lastmonth_end))
            output = ranking_text(group, lastmonth_start, lastmonth_end, "month")
            bot.sendMessage(chat_id=chat_id, text=output, parse_mode=telegram.ParseMode.HTML, disable_web_page_preview=True)
        elif show_week:
            if group["rankingweek"] == 0:
                return
            logging.debug("Ranking from %s to %s" % (lastweek_start, lastweek_end))
            output = ranking_text(group, lastweek_start, lastweek_end, "week")
            bot.sendMessage(chat_id=chat_id, text=output, parse_mode=telegram.ParseMode.HTML, disable_web_page_preview=True)

@run_async
def gym(bot, update, args=None):
    logging.debug("detectivepikachubot:gym: %s %s %s" % (bot, update, args))
    (chat_id, chat_type, user_id, text, message) = extract_update_info(update)

    if isBanned(chat_id):
        return

    if chat_type == "private":
        bot.sendMessage(chat_id=chat_id, text="El comando de buscar gimnasios solo funcionan en canales y grupos. Si quieres probarlo, puedes pasarte por @detectivepikachuayuda.")
        return

    group = getGroup(chat_id)

    try:
      bot.deleteMessage(chat_id=chat_id,message_id=update.message.message_id)
    except:
      pass

    if chat_type != "channel" and (group["gymcommand"] == 0 and not is_admin(chat_id, user_id, bot)):
        return

    if chat_type != "channel" and isBanned(user_id):
        return

    if len(args) < 1:
        sent_message = bot.sendMessage(chat_id=chat_id, text="Debes indicar un texto para buscar un gimnasio como parámetro. Por ejemplo, `/gym alameda`.\n\n_(Este mensaje se borrará en unos segundos)_", parse_mode=telegram.ParseMode.MARKDOWN)
        Thread(target=delete_message_timed, args=(chat_id, sent_message.message_id, 15, bot)).start()
        return

    gym_text = ""
    for i in range (0,len(args)):
        gym_text = gym_text + "%s " % args[i]
    gym_text = gym_text.strip()

    chosengym = None
    gyms = getPlaces(chat_id, ordering="id")
    for p in gyms:
        for n in p["names"]:
            if re.search(re.escape(unidecode(n)),unidecode(gym_text),flags=re.IGNORECASE) is not None:
                logging.debug("Match! «%s» with «%s»" % (unidecode(n),unidecode(gym_text)))
                chosengym = p
                break
        if chosengym is not None:
            break
    if chosengym is not None:
        bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        logging.info("Encontrado: %s" % chosengym["desc"])
        if chosengym["address"] is None:
            chosengym = fetch_gym_address(chosengym)
        tags_emojis = format_gym_emojis(chosengym["tags"])
        bot.sendVenue(chat_id=chat_id, latitude=chosengym["latitude"], longitude=chosengym["longitude"], title=tags_emojis + chosengym["desc"], address=chosengym["address"])
    else:
        sent_message = bot.sendMessage(chat_id=chat_id, text="Lo siento, pero no he encontrado el gimnasio _%s_.\n\n_(Este mensaje se borrará en unos segundos)_" % gym_text, parse_mode=telegram.ParseMode.MARKDOWN)
        Thread(target=delete_message_timed, args=(chat_id, sent_message.message_id, 15, bot)).start()

@run_async
def raid(bot, update, args=None):
  logging.debug("detectivepikachubot:raid: %s %s %s" % (bot, update, args))
  (chat_id, chat_type, user_id, text, message) = extract_update_info(update)

  if chat_type != "channel":
    user_username = message.from_user.username
    thisuser = refreshUsername(user_id, user_username)

  if isBanned(chat_id) or isBanned(user_id):
    return

  if chat_type == "private":
    bot.sendMessage(chat_id=chat_id, text="Las incursiones solo funcionan en canales y grupos. Si quieres probarlas, puedes pasarte por @detectivepikachuayuda.")
    return

  current_raid = {}
  group = getGroup(chat_id)

  if group is None:
      if chat_type == "channel":
          bot.sendMessage(chat_id=chat_id, text="No tengo información de este canal. Un administrador debe utilizar al menos una vez el comando `/settings` antes de poder utilizarme en un canal. Si estaba funcionando hasta ahora y he dejado de hacerlo, avisa en @detectivepikachuayuda.", parse_mode=telegram.ParseMode.MARKDOWN)
      else:
          bot.sendMessage(chat_id=chat_id, text="No consigo encontrar la información de este grupo. ¿He saludado al entrar? Prueba a echarme y a meterme de nuevo. Si lo has promocionado a supergrupo después de entrar yo, esto es normal. Si estaba funcionando hasta ahora y he dejado de hacerlo, avisa en @detectivepikachuayuda.", parse_mode=telegram.ParseMode.MARKDOWN)
      return

  try:
    bot.deleteMessage(chat_id=chat_id,message_id=message.message_id)
  except:
    pass

  if chat_type != "channel" and (group["raidcommand"] == 0 and not is_admin(chat_id, user_id, bot)):
      return

  if chat_type != "channel" and isBanned(user_id):
      return

  if chat_type != "channel" and thisuser["username"] is None:
      sent_message = bot.sendMessage(chat_id=chat_id, text="¡Lo siento, pero no puedes crear una incursión si no tienes definido un alias!\nEn Telegram, ve a *Ajustes* y selecciona la opción *Alias* para establecer un alias.\n\n_(Este mensaje se borrará en unos segundos)_", parse_mode=telegram.ParseMode.MARKDOWN)
      Thread(target=delete_message_timed, args=(chat_id, sent_message.message_id, 15, bot)).start()
      return

  if chat_type != "channel" and thisuser["validation"] == "none" and group["validationrequired"] == 1:
      sent_message = bot.sendMessage(chat_id=chat_id, text="¡Lo siento, pero en este grupo es obligatorio validarse antes de poder crear incursiones o participar en ellas!\nAbre un privado con @%s y escribe `/help` para saber cómo puedes validarte.\n\n_(Este mensaje se borrará en unos segundos)_" % config["telegram"]["botalias"], parse_mode=telegram.ParseMode.MARKDOWN)
      Thread(target=delete_message_timed, args=(chat_id, sent_message.message_id, 15, bot)).start()
      return

  currgyms = getCurrentGyms(chat_id)
  if (len(args) == 0 or args == None) and len(currgyms) >= 2 and group["locations"] == 1:
      keyboard = get_pokemons_keyboard()
      if chat_type != "channel":
          creating_text = format_text_creating(thisuser)
      else:
          creating_text = format_text_creating(None)
      sent_message = bot.sendMessage(chat_id=chat_id, text="🤔 %s\n\nElige el <b>Pokémon</b> o el huevo del que quieres realizar la incursión. Si no está en la lista, pulsa <i>Cancelar</i> y créala manualmente.\n\n<i>(Este mensaje se borrará si no completas el proceso de creación en menos de un minuto)</i>" % creating_text, reply_markup=keyboard, parse_mode=telegram.ParseMode.HTML, disable_web_page_preview=True)

      current_raid = {}
      current_raid["grupo_id"] = chat_id
      current_raid["usuario_id"] = user_id
      current_raid["message"] = sent_message.message_id
      current_raid["status"] = "creating"
      current_raid["id"] = saveRaid(current_raid)
      return

  if args is None or len(args)<3:
    if chat_type != "channel":
        sent_message = bot.sendMessage(chat_id=chat_id, text="❌ @%s no te entiendo. Debes poner los parámetros de la incursión en este orden:\n`/raid pokemon hora gimnasio`\n\nEjemplo:\n `/raid pikachu 12:00 la lechera`\n\nEl mensaje original era:\n`%s`\n\n_(Este mensaje se borrará en unos segundos)_" % (ensure_escaped(thisuser["username"]), text), parse_mode=telegram.ParseMode.MARKDOWN)
    else:
        sent_message = bot.sendMessage(chat_id=chat_id, text="❌ No te entiendo. Debes poner los parámetros de la incursión en este orden:\n`/raid pokemon hora gimnasio`\n\nEjemplo:\n `/raid pikachu 12:00 la lechera`\n\nEl mensaje original era:\n`%s`\n\n_(Este mensaje se borrará en unos segundos)_" % (text), parse_mode=telegram.ParseMode.MARKDOWN)
    Thread(target=delete_message_timed, args=(chat_id, sent_message.message_id, 20, bot)).start()
    return

  if chat_type != "channel":
    current_raid["username"] = thisuser["username"]
  else:
    current_raid["username"] = None

  if args[0].lower() == "de":
    del args[0]

  if args[0].lower() == "nivel" and args[1] in ["1","2","3","4","5"]:
      del args[0]
      args[0] = "N%s" % args[0]

  if args[0].lower() == "legendaria":
      args[0] = "N5"

  (current_raid["pokemon"], current_raid["egg"]) = parse_pokemon(args[0])
  if current_raid["pokemon"] is None and current_raid["egg"] is None:
    if chat_type != "channel":
      sent_message = bot.sendMessage(chat_id=chat_id, text="❌ @%s no he entendido *el Pokémon* o *el huevo*. ¿Lo has escrito bien?\nRecuerda que debes poner los parámetros en este orden:\n`/raid pokemon hora gimnasio`\n\nEjemplos:\n`/raid pikachu 12:00 la lechera`\n`/raid N5 12:00 la alameda`\n`/raid EX 11/12:00 fuente vieja`\n\nEl mensaje original era:\n`%s`\n\n_(Este mensaje se borrará en unos segundos)_" % (ensure_escaped(thisuser["username"]), text),parse_mode=telegram.ParseMode.MARKDOWN)
    else:
      sent_message = bot.sendMessage(chat_id=chat_id, text="❌ No he entendido *el Pokémon* o *el huevo*. ¿Lo has escrito bien?\nRecuerda que debes poner los parámetros en este orden:\n`/raid pokemon hora gimnasio`\n\nEjemplos:\n`/raid pikachu 12:00 la lechera`\n`/raid N5 12:00 la alameda`\n`/raid EX 11/12:00 fuente vieja`\n\nEl mensaje original era:\n`%s`\n\n_(Este mensaje se borrará en unos segundos)_" % (text),parse_mode=telegram.ParseMode.MARKDOWN)
    Thread(target=delete_message_timed, args=(chat_id, sent_message.message_id, 20, bot)).start()
    return

  del args[0]
  if args[0].lower() == "a" and (args[1].lower() == "las" or args[1].lower() == "la"):
    del args[0]
    del args[0]

  current_raid["timeraid"] = parse_time(args[0], group["timezone"])
  if current_raid["timeraid"] is None:
      if chat_type != "channel":
        sent_message = bot.sendMessage(chat_id=chat_id, text="❌ @%s no he entendido *la hora*. ¿La has puesto bien?\nRecuerda que debes poner los parámetros de la incursión en este orden:\n`/raid pokemon hora gimnasio`\n\nEjemplo:\n `/raid pikachu 12:00 la lechera`\n\nEl mensaje original era:\n`%s`\n\n_(Este mensaje se borrará en unos segundos)_" % (ensure_escaped(thisuser["username"]), text),parse_mode=telegram.ParseMode.MARKDOWN)
      else:
        sent_message = bot.sendMessage(chat_id=chat_id, text="❌ No he entendido *la hora*. ¿La has puesto bien?\nRecuerda que debes poner los parámetros de la incursión en este orden:\n`/raid pokemon hora gimnasio`\n\nEjemplo:\n `/raid pikachu 12:00 la lechera`\n\nEl mensaje original era:\n`%s`\n\n_(Este mensaje se borrará en unos segundos)_" % (text),parse_mode=telegram.ParseMode.MARKDOWN)
      Thread(target=delete_message_timed, args=(chat_id, sent_message.message_id, 20, bot)).start()
      return

  raid_datetime = datetime.strptime(current_raid["timeraid"],"%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone(group["timezone"]))
  now_datetime = datetime.now(timezone(group["timezone"])).replace(tzinfo=timezone(group["timezone"]))
  if raid_datetime < now_datetime:
      now_datetime_str = now_datetime.strftime("%Y-%m-%d %H:%M:%S")
      now_time = extract_time(now_datetime_str)
      if chat_type != "channel":
        sent_message = bot.sendMessage(chat_id=chat_id, text="❌ @%s si no he entendido mal quieres poner la incursión a las *%s*, pero ya son las *%s*. ¿Has puesto bien la hora?\n\nEl mensaje original era:\n`%s`\n\n_(Este mensaje se borrará en unos segundos)_" % (ensure_escaped(thisuser["username"]), extract_time(current_raid["timeraid"]), now_time, text),parse_mode=telegram.ParseMode.MARKDOWN)
      else:
        sent_message = bot.sendMessage(chat_id=chat_id, text="❌ Si no he entendido mal quieres poner la incursión a las *%s*, pero ya son las *%s*. ¿Has puesto bien la hora?\n\nEl mensaje original era:\n`%s`\n\n_(Este mensaje se borrará en unos segundos)_" % (extract_time(current_raid["timeraid"]), now_time, text),parse_mode=telegram.ParseMode.MARKDOWN)
      Thread(target=delete_message_timed, args=(chat_id, sent_message.message_id, 20, bot)).start()
      return

  current_raid["timeend"] = parse_time(args[-1], group["timezone"], strict=True)

  if current_raid["timeend"] is not None:
      raidend_datetime = datetime.strptime(current_raid["timeend"],"%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone(group["timezone"]))
      raidend_datetime = raidend_datetime.replace(day=raid_datetime.day, month=raid_datetime.month, year=raid_datetime.year)
      if raidend_datetime < raid_datetime or raidend_datetime > (raid_datetime + timedelta(minutes = 180)):
          now_datetime_str = now_datetime.strftime("%Y-%m-%d %H:%M:%S")
          now_time = extract_time(now_datetime_str)
          if chat_type != "channel":
            sent_message = bot.sendMessage(chat_id=chat_id, text="❌ @%s si no he entendido mal quieres poner la hora de finalización de la incursión a las *%s*, pero la incursión es a las *%s*. ¿Has puesto bien la hora de finalización?\n\nEl mensaje original era:\n`%s`\n\n_(Este mensaje se borrará en unos segundos)_" % (ensure_escaped(thisuser["username"]), extract_time(current_raid["timeend"]), extract_time(current_raid["timeraid"]), text),parse_mode=telegram.ParseMode.MARKDOWN)
          else:
            sent_message = bot.sendMessage(chat_id=chat_id, text="❌ Si no he entendido mal quieres poner la hora de finalización de la incursión a las *%s*, pero la incursión es a las *%s*. ¿Has puesto bien la hora de finalización?\n\nEl mensaje original era:\n`%s`\n\n_(Este mensaje se borrará en unos segundos)_" % (extract_time(current_raid["timeend"]), extract_time(current_raid["timeraid"]), text),parse_mode=telegram.ParseMode.MARKDOWN)
          Thread(target=delete_message_timed, args=(chat_id, sent_message.message_id, 20, bot)).start()
          return

  if current_raid["timeend"] is not None:
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
  if args[0].lower() == "en":
    del args[0]

  current_raid["gimnasio_text"] = ""
  for i in range (0,len(args)):
      current_raid["gimnasio_text"] = current_raid["gimnasio_text"] + "%s " % args[i]
  current_raid["gimnasio_text"] = current_raid["gimnasio_text"].strip()

  if group["locations"] == 1:
      chosengym = None
      gyms = getPlaces(chat_id, ordering="id")
      for p in gyms:
        for n in p["names"]:
          if re.search(re.escape(unidecode(n)),unidecode(current_raid["gimnasio_text"]),flags=re.IGNORECASE) is not None:
            logging.debug("Match! «%s» with «%s»" % (unidecode(n),unidecode(current_raid["gimnasio_text"])))
            chosengym = p
            break
        if chosengym is not None:
          break
      if chosengym is not None:
        current_raid["gimnasio_text"] = chosengym["desc"]
        current_raid["gimnasio_id"] = chosengym["id"]

  current_raid["grupo_id"] = chat_id
  current_raid["usuario_id"] = user_id
  current_raid["id"] = saveRaid(current_raid)

  text  = format_message(current_raid)
  reply_markup = get_keyboard(current_raid)
  sent_message = bot.sendMessage(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode=telegram.ParseMode.HTML, disable_web_page_preview=True)
  current_raid["message"] = sent_message.message_id
  saveRaid(current_raid)

  if chat_type != "channel":
      send_edit_instructions(group, current_raid, user_id, bot)

  if group["locations"] == 1:
      if "gimnasio_id" in current_raid.keys() and current_raid["gimnasio_id"] is not None:
          Thread(target=send_alerts_delayed, args=(current_raid, bot)).start()
      elif chat_type != "channel":
          if group["alerts"] == 1:
              text_alertas = " y la gente que tenga activadas las alertas pueda recibirlas"
          else:
              text_alertas = ""
          try:
              bot.send_message(chat_id=user_id, text="⚠️ *¡Cuidado!* Parece que el gimnasio que has indicado no se ha reconocido: _%s_\n\nDebes cambiarlo por un gimnasio reconocido para que aparezca la ubicación%s. Para hacerlo, utiliza este comando cambiando el texto del final:\n\n`/cambiargimnasio %s %s`\n\nSi no consigues que reconozca el gimnasio, avisa a un administrador del grupo para que lo configure correctamente." % (current_raid["gimnasio_text"], text_alertas, current_raid["id"], current_raid["gimnasio_text"]), parse_mode=telegram.ParseMode.MARKDOWN)
          except:
              logging.debug("Error sending warning in private. Maybe conversation not started?")

  raid_difftime = raid_datetime - now_datetime
  if raid_difftime.total_seconds() < 900:
    suggested_datetime = raid_datetime + timedelta(minutes = 20)
    suggested_datetime_str = suggested_datetime.strftime("%Y-%m-%d %H:%M:%S")
    suggested_time = extract_time(suggested_datetime_str)
    try:
        bot.send_message(chat_id=user_id, text="⚠️ *¡Cuidado!* Has creado la incursión para dentro de muy poco tiempo, *solo faltan %s minutos*. ¿Quizás prefieras cambiarla para más tarde para que se pueda unir más gente? Para hacerlo, pon aquí este comando:\n\n`/cambiarhora %s %s`" % (int(raid_difftime.total_seconds()/60), current_raid["id"], suggested_time), parse_mode=telegram.ParseMode.MARKDOWN)
    except:
        logging.debug("Error sending warning in private. Maybe conversation not started?")

@run_async
def cerrar(bot, update, args=None):
    logging.debug("detectivepikachubot:cerrar: %s %s %s" % (bot, update, args))
    (chat_id, chat_type, user_id, text, message) = extract_update_info(update)

    if isBanned(chat_id):
        return

    if chat_type != "channel":
        user_username = message.from_user.username
        thisuser = refreshUsername(user_id, user_username)
        if isBanned(user_id):
            return
    else:
        user_username = None
        thisuser = None

    raid = edit_check_private_or_reply(chat_id, chat_type, message, args, user_username, "cerrar", bot)
    if raid is None:
        return

    if raid is not None:
        if raid["usuario_id"] == user_id or is_admin(raid["grupo_id"], user_id, bot):
            response = closeRaid(raid["id"])
            if response is True:
                raid["status"] = "ended"
                reply_markup = get_keyboard(raid)
                update_message(raid["grupo_id"], raid["message"], reply_markup, bot)
                if user_id is not None:
                    bot.sendMessage(chat_id=user_id, text="👌 ¡Se ha cerrado la incursión `%s` correctamente!" % raid["id"], parse_mode=telegram.ParseMode.MARKDOWN)
            elif response == "already_deleted":
                user_id = chat_id if user_id is None else user_id
                bot.sendMessage(chat_id=user_id, text="❌ No se puede cerrar la incursión `%s` porque ha sido borrada." % raid["id"], parse_mode=telegram.ParseMode.MARKDOWN)
            elif response == "already_cancelled":
                user_id = chat_id if user_id is None else user_id
                bot.sendMessage(chat_id=user_id, text="❌ No se puede cerrar la incursión `%s` porque ha sido cancelada." % raid["id"], parse_mode=telegram.ParseMode.MARKDOWN)
            elif response == "too_old_or_too_young":
                user_id = chat_id if user_id is None else user_id
                bot.sendMessage(chat_id=user_id, text="❌ No se puede cerrar la incursión `%s`. Solo se pueden cerrar incursiones comenzadas (o que estén a punto de comenzar) y que no han finalizado ya." % raid["id"], parse_mode=telegram.ParseMode.MARKDOWN)
        else:
            bot.sendMessage(chat_id=user_id, text="❌ No tienes permiso para cerrar la incursión `%s`." % raid["id"], parse_mode=telegram.ParseMode.MARKDOWN)

@run_async
def cancelar(bot, update, args=None):
    logging.debug("detectivepikachubot:cancelar: %s %s %s" % (bot, update, args))
    (chat_id, chat_type, user_id, text, message) = extract_update_info(update)

    if isBanned(chat_id):
        return

    if chat_type != "channel":
        user_username = message.from_user.username
        thisuser = refreshUsername(user_id, user_username)
        if isBanned(user_id):
            return
    else:
        user_username = None
        thisuser = None

    raid = edit_check_private_or_reply(chat_id, chat_type, message, args, user_username, "cancelar", bot)
    if raid is None:
        return

    if raid is not None:
        if raid["usuario_id"] == user_id or is_admin(raid["grupo_id"], user_id, bot):
            response = cancelRaid(raid["id"], force=is_admin(raid["grupo_id"], user_id, bot))
            if response is True:
                update_message(raid["grupo_id"], raid["message"], None, bot)
                if user_id is not None:
                    bot.sendMessage(chat_id=user_id, text="👌 ¡Se ha cancelado la incursión `%s` correctamente!" % raid["id"], parse_mode=telegram.ParseMode.MARKDOWN)
                group = getGroup(raid["grupo_id"])
                raid_datetime = raid["timeraid"].replace(tzinfo=timezone(group["timezone"]))
                threehoursago_datetime = datetime.now(timezone(group["timezone"])) - timedelta(minutes = 180)
                if raid_datetime > threehoursago_datetime:
                    warn_people("cancelar", raid, user_username, user_id, bot)
            elif response == "already_cancelled":
                user_id = chat_id if user_id is None else user_id
                bot.sendMessage(chat_id=user_id, text="❌ No se puede cancelar la incursión `%s` porque ya ha sido cancelada previamente." % raid["id"], parse_mode=telegram.ParseMode.MARKDOWN)
            elif response == "already_deleted":
                user_id = chat_id if user_id is None else user_id
                bot.sendMessage(chat_id=user_id, text="❌ No se puede cancelar la incursión `%s` porque ha sido borrada." % raid["id"], parse_mode=telegram.ParseMode.MARKDOWN)
            elif response == "too_old":
                user_id = chat_id if user_id is None else user_id
                bot.sendMessage(chat_id=user_id, text="❌ No se puede cancelar la incursión `%s` porque ya ha terminado." % raid["id"], parse_mode=telegram.ParseMode.MARKDOWN)
        else:
            bot.sendMessage(chat_id=user_id, text="❌ No tienes permiso para cancelar la incursión `%s`." % raid["id"], parse_mode=telegram.ParseMode.MARKDOWN)

@run_async
def descancelar(bot, update, args=None):
    logging.debug("detectivepikachubot:descancelar: %s %s %s" % (bot, update, args))
    (chat_id, chat_type, user_id, text, message) = extract_update_info(update)

    if isBanned(chat_id):
        return

    if chat_type != "channel":
        user_username = message.from_user.username
        thisuser = refreshUsername(user_id, user_username)
        if isBanned(user_id):
            return
    else:
        user_username = None
        thisuser = None

    raid = edit_check_private_or_reply(chat_id, chat_type, message, args, user_username, "descancelar", bot)
    if raid is None:
        return

    if raid is not None:
        if is_admin(raid["grupo_id"], user_id, bot):
            response = uncancelRaid(raid["id"])
            if response is True:
                raid = getRaid(raid["id"])
                reply_markup = get_keyboard(raid)
                update_message(raid["grupo_id"], raid["message"], reply_markup, bot)
                if user_id is not None:
                    bot.sendMessage(chat_id=user_id, text="👌 ¡Se ha descancelado la incursión `%s` correctamente!" % raid["id"], parse_mode=telegram.ParseMode.MARKDOWN)
                warn_people("descancelar", raid, user_username, user_id, bot)
            elif response == "not_cancelled":
                user_id = chat_id if user_id is None else user_id
                bot.sendMessage(chat_id=user_id, text="❌ No se puede descancelar la incursión `%s` porque no ha sido cancelada previamente." % raid["id"], parse_mode=telegram.ParseMode.MARKDOWN)
            elif response == "already_deleted":
                user_id = chat_id if user_id is None else user_id
                bot.sendMessage(chat_id=user_id, text="❌ No se puede descancelar la incursión `%s` porque ha sido borrada." % raid["id"], parse_mode=telegram.ParseMode.MARKDOWN)
        else:
            bot.sendMessage(chat_id=user_id, text="❌ No tienes permiso para descancelar la incursión `%s`." % raid["id"], parse_mode=telegram.ParseMode.MARKDOWN)

@run_async
def borrar(bot, update, args=None):
    logging.debug("detectivepikachubot:borrar: %s %s" % (bot, update))
    (chat_id, chat_type, user_id, text, message) = extract_update_info(update)

    if isBanned(chat_id):
        return

    if chat_type != "channel":
        user_username = message.from_user.username
        thisuser = refreshUsername(user_id, user_username)
        if isBanned(user_id):
            return
    else:
        user_username = None
        thisuser = None

    raid = edit_check_private_or_reply(chat_id, chat_type, message, args, user_username, "borrar", bot)
    if raid is None:
        return

    group = getGroup(raid["grupo_id"])
    if raid is not None:
        if chat_type == "channel" or is_admin(raid["grupo_id"], user_id, bot) or (group["candelete"] == 1 and raid["usuario_id"] == user_id):
            response = deleteRaid(raid["id"])
            if response is True:
                try:
                    bot.deleteMessage(chat_id=raid["grupo_id"],message_id=raid["message"])
                except:
                    pass
                warn_people("borrar", raid, user_username, user_id, bot)
                if user_id is not None:
                    bot.sendMessage(chat_id=user_id, text="👌 ¡Se ha borrado la incursión `%s` correctamente!" % raid["id"], parse_mode=telegram.ParseMode.MARKDOWN)
            elif response == "already_deleted":
                user_id = chat_id if user_id is None else user_id
                bot.sendMessage(chat_id=user_id, text="❌ No se puede borrar la incursión `%s` porque ya ha sido borrada previamente." % raid["id"], parse_mode=telegram.ParseMode.MARKDOWN)
            elif response == "too_old":
                user_id = chat_id if user_id is None else user_id
                bot.sendMessage(chat_id=user_id, text="❌ No se puede borrar la incursión `%s` porque ya ha terminado." % raid["id"], parse_mode=telegram.ParseMode.MARKDOWN)
        else:
            bot.sendMessage(chat_id=user_id, text="❌ No tienes permiso para borrar la incursión `%s`." % raid["id"], parse_mode=telegram.ParseMode.MARKDOWN)

@run_async
def cambiarhora(bot, update, args=None):
    logging.debug("detectivepikachubot:cambiarHora: %s %s %s" % (bot, update, args))
    (chat_id, chat_type, user_id, text, message) = extract_update_info(update)

    if isBanned(chat_id):
        return

    if chat_type != "channel":
        user_username = message.from_user.username
        thisuser = refreshUsername(user_id, user_username)
        if isBanned(user_id):
            return
    else:
        user_username = None
        thisuser = None

    raid = edit_check_private_or_reply(chat_id, chat_type, message, args, user_username, "cambiarhora", bot)
    if raid is None:
        return

    numarg = 1 if chat_type == "private" else 0
    group = getGroup(raid["grupo_id"])
    if raid is not None:
        if chat_type == "channel" or raid["usuario_id"] == user_id or is_admin(raid["grupo_id"], user_id, bot):
            if raid["status"] == "old":
                user_id = chat_id if user_id is None else user_id
                bot.sendMessage(chat_id=user_id, text="❌ No se puede editar la incursión `%s` porque ya ha terminado." % raid["id"], parse_mode=telegram.ParseMode.MARKDOWN)
                return
            if raid["status"] == "cancelled":
                user_id = chat_id if user_id is None else user_id
                bot.sendMessage(chat_id=user_id, text="❌ No se puede editar la incursión `%s` porque ha sido cancelada." % raid["id"], parse_mode=telegram.ParseMode.MARKDOWN)
                return
            if raid["status"] == "deleted":
                user_id = chat_id if user_id is None else user_id
                bot.sendMessage(chat_id=user_id, text="❌ No se puede editar la incursión `%s` porque ha sido borrada." % raid["id"], parse_mode=telegram.ParseMode.MARKDOWN)
                return
            oldtimeraid = raid["timeraid"]
            raid["timeraid"] = parse_time(args[numarg], group["timezone"])
            if raid["timeraid"] is None:
                user_id = chat_id if user_id is None else user_id
                sent_message = bot.sendMessage(chat_id=user_id, text="❌ No he entendido *la hora*. ¿La has escrito bien?\nDebe seguir el formato `hh:mm`.\nEjemplo: `12:15`", parse_mode=telegram.ParseMode.MARKDOWN)
                return

            raid_datetime = datetime.strptime(raid["timeraid"],"%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone(group["timezone"]))
            now_datetime = datetime.now(timezone(group["timezone"])).replace(tzinfo=timezone(group["timezone"]))
            if raid_datetime < now_datetime:
                now_datetime_str = now_datetime.strftime("%Y-%m-%d %H:%M:%S")
                now_time = extract_time(now_datetime_str)
                user_id = chat_id if user_id is None else user_id
                bot.sendMessage(chat_id=user_id, text="❌ Si no he entendido mal quieres cambiar la incursión para las *%s*, pero ya son las *%s*. ¿Has puesto bien la hora?" % (extract_time(raid["timeraid"]), now_time),parse_mode=telegram.ParseMode.MARKDOWN)
                return

            if oldtimeraid.strftime("%Y-%m-%d %H:%M:%S") == raid["timeraid"]:
                user_id = chat_id if user_id is None else user_id
                bot.sendMessage(chat_id=user_id, text="❌ La incursión `%s` ya está puesta para esa hora." % raid["id"], parse_mode=telegram.ParseMode.MARKDOWN)
            else:
                raid["edited"] = 1
                raid["status"] = "waiting"
                saveRaid(raid)
                reply_markup = get_keyboard(raid)
                update_message(raid["grupo_id"], raid["message"], reply_markup, bot)
                what_day = format_text_day(raid["timeraid"], group["timezone"])
                if user_id is not None:
                    bot.sendMessage(chat_id=user_id, text="👌 ¡Se ha cambiado la hora de la incursión `%s` a las *%s* %scorrectamente!" % (raid["id"], extract_time(raid["timeraid"]), what_day), parse_mode=telegram.ParseMode.MARKDOWN)
                warn_people("cambiarhora", raid, user_username, user_id, bot)
        else:
            bot.sendMessage(chat_id=user_id, text="❌ No tienes permiso para editar la incursión `%s`." % raid["id"],parse_mode=telegram.ParseMode.MARKDOWN)

@run_async
def cambiarhorafin(bot, update, args=None):
    logging.debug("detectivepikachubot:cambiarHoraFin: %s %s %s" % (bot, update, args))
    (chat_id, chat_type, user_id, text, message) = extract_update_info(update)

    if isBanned(chat_id):
        return

    if chat_type != "channel":
        user_username = message.from_user.username
        thisuser = refreshUsername(user_id, user_username)
        if isBanned(user_id):
            return
    else:
        user_username = None
        thisuser = None

    raid = edit_check_private_or_reply(chat_id, chat_type, message, args, user_username, "cambiarhorafin", bot)
    if raid is None:
        return

    numarg = 1 if chat_type == "private" else 0
    group = getGroup(raid["grupo_id"])
    if raid is not None:
        if chat_type == "channel" or raid["usuario_id"] == user_id or is_admin(raid["grupo_id"], user_id, bot):
            if raid["status"] == "old":
                user_id = chat_id if user_id is None else user_id
                bot.sendMessage(chat_id=user_id, text="❌ No se puede editar la incursión `%s` porque ya ha terminado." % raid["id"], parse_mode=telegram.ParseMode.MARKDOWN)
                return
            if raid["status"] == "cancelled":
                user_id = chat_id if user_id is None else user_id
                bot.sendMessage(chat_id=user_id, text="❌ No se puede editar la incursión `%s` porque ha sido cancelada." % raid["id"], parse_mode=telegram.ParseMode.MARKDOWN)
                return
            if raid["status"] == "deleted":
                user_id = chat_id if user_id is None else user_id
                bot.sendMessage(chat_id=user_id, text="❌ No se puede editar la incursión `%s` porque ha sido borrada." % raid["id"], parse_mode=telegram.ParseMode.MARKDOWN)
                return
            oldtimeraid = raid["timeend"]
            if args[numarg] == "-":
                raid["timeend"] = None
                if oldtimeraid == raid["timeend"]:
                    user_id = chat_id if user_id is None else user_id
                    bot.sendMessage(chat_id=user_id, text="❌ La incursión `%s` ya no tenía hora de fin." % raid["id"], parse_mode=telegram.ParseMode.MARKDOWN)
                raid["edited"] = 1
                saveRaid(raid)
                reply_markup = get_keyboard(raid)
                update_message(raid["grupo_id"], raid["message"], reply_markup, bot)
                if user_id is not None:
                    bot.sendMessage(chat_id=user_id, text="👌 ¡Se ha borrado la hora de fin de la incursión `%s` correctamente!" % raid["id"], parse_mode=telegram.ParseMode.MARKDOWN)
                warn_people("borrarhorafin", raid, user_username, user_id, bot)
            else:
                raid["timeend"] = parse_time(args[numarg], group["timezone"])
                if raid["timeend"] is None:
                    sent_message = bot.sendMessage(chat_id=user_id, text="❌ @%s no he entendido *la hora de finalización*. ¿La has escrito bien?\nDebe seguir el formato `hh:mm`.\nEjemplo: `12:15`\n\nSi quieres borrar la hora de fin, pon un guión simple en lugar de la hora: `-`." % thisuser["username"], parse_mode=telegram.ParseMode.MARKDOWN)
                    return
                if oldtimeraid == raid["timeend"]:
                    user_id = chat_id if user_id is None else user_id
                    bot.sendMessage(chat_id=user_id, text="❌ La incursión `%s` ya tiene esa misma hora de fin." % raid["id"], parse_mode=telegram.ParseMode.MARKDOWN)
                    return

                raid_datetime = raid["timeraid"].replace(tzinfo=timezone(group["timezone"]))
                raidend_datetime = datetime.strptime(raid["timeend"],"%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone(group["timezone"]))
                raidend_datetime = raidend_datetime.replace(day=raid_datetime.day, month=raid_datetime.month, year=raid_datetime.year)
                if raidend_datetime < raid_datetime or raidend_datetime > (raid_datetime + timedelta(minutes = 180)):
                    user_id = chat_id if user_id is None else user_id
                    bot.sendMessage(chat_id=user_id, text="❌ Si no he entendido mal quieres cambiar la hora de finalización de la incursión para las *%s*, pero la incursión es a las las *%s*. ¿Has puesto bien la hora?" % (extract_time(raid["timeend"]),extract_time(raid["timeraid"])), parse_mode=telegram.ParseMode.MARKDOWN)
                    return

                raid["edited"] = 1
                saveRaid(raid)
                reply_markup = get_keyboard(raid)
                update_message(raid["grupo_id"], raid["message"], reply_markup, bot)
                if user_id is not None:
                    bot.sendMessage(chat_id=user_id, text="👌 ¡Se ha cambiado la hora de fin de la incursión `%s` a las *%s* correctamente!" % (raid["id"], extract_time(raid["timeend"])), parse_mode=telegram.ParseMode.MARKDOWN)
                warn_people("cambiarhorafin", raid, user_username, user_id, bot)
        else:
            bot.sendMessage(chat_id=user_id, text="❌ No tienes permiso para editar la incursión `%s`." % raid["id"], parse_mode=telegram.ParseMode.MARKDOWN)

@run_async
def cambiargimnasio(bot, update, args=None):
    logging.debug("detectivepikachubot:cambiargimnasio: %s %s %s" % (bot, update, args))
    (chat_id, chat_type, user_id, text, message) = extract_update_info(update)

    if isBanned(chat_id):
        return

    if chat_type != "channel":
        user_username = message.from_user.username
        thisuser = refreshUsername(user_id, user_username)
        if isBanned(user_id):
            return
    else:
        user_username = None
        thisuser = None

    raid = edit_check_private_or_reply(chat_id, chat_type, message, args, user_username, "cambiargimnasio", bot)
    if raid is None:
        return

    numarg = 1 if chat_type == "private" else 0
    new_gymtext = ""
    for i in range (numarg,len(args)):
        new_gymtext = new_gymtext + "%s " % args[i]
    new_gymtext = new_gymtext.strip()

    group = getGroup(raid["grupo_id"])
    if raid is not None:
        if chat_type == "channel" or raid["usuario_id"] == user_id or is_admin(raid["grupo_id"], user_id, bot):
            if raid["status"] == "old":
                user_id = chat_id if user_id is None else user_id
                bot.sendMessage(chat_id=user_id, text="❌ No se puede editar la incursión `%s` porque ya ha terminado." % raid["id"], parse_mode=telegram.ParseMode.MARKDOWN)
                return
            if raid["status"] == "cancelled":
                user_id = chat_id if user_id is None else user_id
                bot.sendMessage(chat_id=user_id, text="❌ No se puede editar la incursión `%s` porque ha sido cancelada." % raid["id"], parse_mode=telegram.ParseMode.MARKDOWN)
                return
            if raid["status"] == "deleted":
                user_id = chat_id if user_id is None else user_id
                bot.sendMessage(chat_id=user_id, text="❌ No se puede editar la incursión `%s` porque ha sido borrada." % raid["id"], parse_mode=telegram.ParseMode.MARKDOWN)
                return
            if new_gymtext == raid["gimnasio_text"]:
                user_id = chat_id if user_id is None else user_id
                bot.sendMessage(chat_id=user_id, text="❌ La incursión `%s` ya está puesta en ese mismo gimnasio." % raid["id"], parse_mode=telegram.ParseMode.MARKDOWN)
            else:
                chosengym = None
                if group["locations"] == 1:
                    gyms = getPlaces(raid["grupo_id"], ordering="id")
                    for p in gyms:
                        for n in p["names"]:
                            if re.search(re.escape(unidecode(n)), unidecode(new_gymtext), flags=re.IGNORECASE) is not None:
                                logging.debug("Match! «%s» with «%s»" % (unidecode(n),unidecode(new_gymtext)))
                                chosengym = p
                                break
                        if chosengym is not None:
                            break
                if chosengym is not None:
                    raid["gimnasio_text"] = chosengym["desc"]
                    raid["gimnasio_id"] = chosengym["id"]
                    raid["edited"] = 1
                    saveRaid(raid)
                    reply_markup = get_keyboard(raid)
                    update_message(raid["grupo_id"], raid["message"], reply_markup, bot)
                    if user_id is not None:
                        bot.sendMessage(chat_id=user_id, text="👌 ¡Se ha cambiado el gimnasio de la incursión `%s` a *%s* correctamente!" % (raid["id"], raid["gimnasio_text"]), parse_mode=telegram.ParseMode.MARKDOWN)
                else:
                    raid["gimnasio_text"] = new_gymtext
                    raid["gimnasio_id"] = None
                    raid["edited"] = 1
                    saveRaid(raid)
                    reply_markup = get_keyboard(raid)
                    update_message(raid["grupo_id"], raid["message"], reply_markup, bot)
                    if group["locations"] == 1:
                        if user_id is not None:
                            bot.sendMessage(chat_id=user_id, text="⚠️ ¡No he encontrado la ubicación del gimnasio que indicas, pero lo he actualizado igualmente a *%s*." % raid["gimnasio_text"], parse_mode=telegram.ParseMode.MARKDOWN)
                    else:
                        if user_id is not None:
                            bot.sendMessage(chat_id=user_id, text="👌 ¡Se ha cambiado el gimnasio de la incursión `%s` a *%s* correctamente!" % (raid["id"], raid["gimnasio_text"]), parse_mode=telegram.ParseMode.MARKDOWN)
                warn_people("cambiargimnasio", raid, user_username, user_id, bot)
                if "gimnasio_id" in raid.keys() and raid["gimnasio_id"] is not None:
                    Thread(target=send_alerts_delayed, args=(raid, bot)).start()
        else:
            bot.sendMessage(chat_id=user_id, text="❌ No tienes permiso para editar la incursión `%s`." % raid["id"],parse_mode=telegram.ParseMode.MARKDOWN)

@run_async
def reflotartodas(bot, update, args=None):
    logging.debug("detectivepikachubot:reflotartodas: %s %s %s" % (bot, update, args))
    mass_refloat(bot, update, args, "all")

@run_async
def reflotarhoy(bot, update, args=None):
    logging.debug("detectivepikachubot:reflotarhoy: %s %s %s" % (bot, update, args))
    mass_refloat(bot, update, args, "today")

@run_async
def reflotaractivas(bot, update, args=None):
    logging.debug("detectivepikachubot:reflotaractivas: %s %s %s" % (bot, update, args))
    mass_refloat(bot, update, args, "active")

def mass_refloat(bot, update, args=None, mode="all"):
    logging.debug("detectivepikachubot:mass_refloat: %s %s %s %s" % (bot, update, args, mode))
    (chat_id, chat_type, user_id, text, message) = extract_update_info(update)

    if isBanned(chat_id):
        return

    if chat_type == "private":
      bot.sendMessage(chat_id=chat_id, text="Este comando solo funciona en canales y grupos.")
      return

    delete_message(chat_id, message.message_id, bot)

    if chat_type != "channel" and not is_admin(chat_id, user_id, bot):
        return

    group = getGroup(chat_id)
    raids = getActiveRaidsforGroup(chat_id)

    if mode == "active":
        refloat_datetime = datetime.now(timezone(group["timezone"])).replace(tzinfo=timezone(group["timezone"])) + timedelta(minutes = 90)
        refloat_all = False
    elif mode == "today":
        refloat_datetime = datetime.now(timezone(group["timezone"])).replace(tzinfo=timezone(group["timezone"]), hour=23, minute=59)
        refloat_all = False
    elif mode == "all":
        refloat_all = True

    for raid in raids:
        timeraid = raid["timeraid"].replace(tzinfo=timezone(group["timezone"]))
        if raid["id"] is not None and raid["status"] != "ended" and ( refloat_all is True or timeraid <= refloat_datetime):
            logging.debug("detectivepikachubot:mass_refloat: Refloating raid %s" % (raid["id"]))
            try:
                bot.deleteMessage(chat_id=raid["grupo_id"],message_id=raid["message"])
            except Exception as e:
                logging.debug("detectivepikachubot:mass_refloat: error borrando post antiguo %s" % raid["message"])
            raid["refloated"] = 1
            text = format_message(raid)
            reply_markup = get_keyboard(raid)
            sent_message = bot.sendMessage(chat_id=raid["grupo_id"], text=text, reply_markup=reply_markup, parse_mode=telegram.ParseMode.HTML, disable_web_page_preview=True)
            raid["message"] = sent_message.message_id
            saveRaid(raid)
            if user_id is not None:
                bot.sendMessage(chat_id=user_id, text="👌 ¡Se ha reflotado la incursión `%s` correctamente!" % raid["id"], parse_mode=telegram.ParseMode.MARKDOWN)
            time.sleep(1.0)

@run_async
def reflotar(bot, update, args=None):
    logging.debug("detectivepikachubot:reflotar: %s %s %s" % (bot, update, args))
    (chat_id, chat_type, user_id, text, message) = extract_update_info(update)

    if isBanned(chat_id):
        return

    if chat_type != "channel":
        user_username = message.from_user.username
        thisuser = refreshUsername(user_id, user_username)
        if isBanned(user_id):
            return
    else:
        user_username = None
        thisuser = None

    raid = edit_check_private_or_reply(chat_id, chat_type, message, args, user_username, "reflotar", bot)
    if raid is None:
        return

    group = getGroup(raid["grupo_id"])
    if raid is not None:
        if chat_type == "channel" or is_admin(raid["grupo_id"], user_id, bot) or (group["refloat"] == 1 and raid["usuario_id"] == user_id):
            if raid["status"] == "old":
                user_id = chat_id if user_id is None else user_id
                bot.sendMessage(chat_id=user_id, text="❌ No se puede reflotar la incursión `%s` porque ya ha terminado." % raid["id"], parse_mode=telegram.ParseMode.MARKDOWN)
                return
            if raid["status"] == "cancelled":
                user_id = chat_id if user_id is None else user_id
                bot.sendMessage(chat_id=user_id, text="❌ No se puede reflotar la incursión `%s` porque está cancelada." % raid["id"], parse_mode=telegram.ParseMode.MARKDOWN)
                return
            if raid["status"] == "deleted":
                user_id = chat_id if user_id is None else user_id
                bot.sendMessage(chat_id=user_id, text="❌ No se puede reflotar la incursión `%s` porque ha sido borrada." % raid["id"], parse_mode=telegram.ParseMode.MARKDOWN)
                return
            try:
                bot.deleteMessage(chat_id=raid["grupo_id"],message_id=raid["message"])
            except Exception as e:
                logging.debug("detectivepikachubot:reflotar: error borrando post antiguo %s" % raid["message"])
            raid["refloated"] = 1
            text = format_message(raid)
            reply_markup = get_keyboard(raid)
            sent_message = bot.sendMessage(chat_id=raid["grupo_id"], text=text, reply_markup=reply_markup, parse_mode=telegram.ParseMode.HTML, disable_web_page_preview=True)
            raid["message"] = sent_message.message_id
            saveRaid(raid)
            if user_id is not None:
                bot.sendMessage(chat_id=user_id, text="👌 ¡Se ha reflotado la incursión `%s` correctamente!" % raid["id"], parse_mode=telegram.ParseMode.MARKDOWN)
        else:
            bot.sendMessage(chat_id=user_id, text="❌ No tienes permiso para reflotar la incursión `%s`." % raid["id"], parse_mode=telegram.ParseMode.MARKDOWN)

@run_async
def cambiarpokemon(bot, update, args=None):
    logging.debug("detectivepikachubot:cambiarpokemon: %s %s %s" % (bot, update, args))
    (chat_id, chat_type, user_id, text, message) = extract_update_info(update)

    if isBanned(chat_id):
        return

    if chat_type != "channel":
        user_username = message.from_user.username
        thisuser = refreshUsername(user_id, user_username)
        if isBanned(user_id):
            return
    else:
        user_username = None
        thisuser = None

    raid = edit_check_private_or_reply(chat_id, chat_type, message, args, user_username, "cambiarpokemon", bot)
    if raid is None:
        return

    numarg = 1 if chat_type == "private" else 0
    if raid is not None:
        if chat_type == "channel" or raid["usuario_id"] == user_id or is_admin(raid["grupo_id"], user_id, bot):
            if raid["status"] == "old":
                user_id = chat_id if user_id is None else user_id
                bot.sendMessage(chat_id=user_id, text="❌ No se puede editar la incursión `%s` porque ya ha terminado." % raid["id"], parse_mode=telegram.ParseMode.MARKDOWN)
                return
            if raid["status"] == "cancelled":
                user_id = chat_id if user_id is None else user_id
                bot.sendMessage(chat_id=user_id, text="❌ No se puede editar la incursión `%s` porque ha sido cancelada." % raid["id"], parse_mode=telegram.ParseMode.MARKDOWN)
                return
            if raid["status"] == "deleted":
                user_id = chat_id if user_id is None else user_id
                bot.sendMessage(chat_id=user_id, text="❌ No se puede editar la incursión `%s` porque ha sido borrada." % raid["id"], parse_mode=telegram.ParseMode.MARKDOWN)
                return

            oldpoke = raid["pokemon"]
            oldegg = raid["egg"]
            (raid["pokemon"], raid["egg"]) = parse_pokemon(args[numarg])
            if (raid["pokemon"] == oldpoke and oldpoke is not None) or \
                (raid["egg"] == oldegg and oldegg is not None):
                user_id = chat_id if user_id is None else user_id
                bot.sendMessage(chat_id=user_id, text="❌ La incursión `%s` ya tiene ese mismo Pokémon/nivel." % raid["id"], parse_mode=telegram.ParseMode.MARKDOWN)
            else:
                if raid["pokemon"] is not None or raid["egg"] is not None:
                    raid["edited"] = 1
                    saveRaid(raid)
                    reply_markup = get_keyboard(raid)
                    update_message(raid["grupo_id"], raid["message"], reply_markup, bot)
                    what_text = format_text_pokemon(raid["pokemon"], raid["egg"])
                    if user_id is not None:
                        bot.sendMessage(chat_id=user_id, text="👌 ¡Se ha cambiado el Pokémon/nivel de la incursión `%s` a incursión %s correctamente!" % (raid["id"], what_text), parse_mode=telegram.ParseMode.MARKDOWN)
                    warn_people("cambiarpokemon", raid, user_username, user_id, bot)
                else:
                    user_id = chat_id if user_id is None else user_id
                    bot.sendMessage(chat_id=user_id, text="❌ No he reconocido ese Pokémon/nivel de incursión.", parse_mode=telegram.ParseMode.MARKDOWN)
        else:
            bot.sendMessage(chat_id=user_id, text="❌ No tienes permiso para editar la incursión `%s`." % raid["id"], parse_mode=telegram.ParseMode.MARKDOWN)

@run_async
def raidbutton(bot, update):
  query = update.callback_query
  original_text = query.message.text
  data = query.data
  user_id = query.from_user.id
  user_username = query.from_user.username
  chat_id = query.message.chat.id
  message_id = query.message.message_id
  chat_type = query.message.chat.type

  if isBanned(user_id) or isBanned(chat_id):
    return

  thisuser = refreshUsername(user_id, user_username)

  update_text = False

  logging.debug("detectivepikachubot:raidbutton:%s: %s %s" % (data, bot, update))

  if (data in ["voy", "plus1", "plus1red", "plus1yellow", "plus1blue", "novoy", "estoy", "lotengo", "escapou", "llegotarde"]) \
    and (thisuser["username"] is None or thisuser["username"] == "None"):
    bot.answerCallbackQuery(text="No puedes unirte a una incursión si no tienes definido un alias.\nEn Telegram, ve a 'Ajustes' y selecciona la opción 'Alias'.", show_alert="true", callback_query_id=update.callback_query.id)
    return

  group = getGroup(chat_id)

  if (data in ["voy", "plus1", "plus1red", "plus1yellow", "plus1blue", "novoy", "estoy", "lotengo", "escapou", "llegotarde"]) \
    and (group["validationrequired"] == 1 and thisuser["validation"] == "none"):
    bot.answerCallbackQuery(text="No puedes unirte a una incursión en este grupo si no te has validado antes.\nAbre un privado con @%s y escribe '/help' para saber cómo puedes hacerlo." % config["telegram"]["botalias"], show_alert="true", callback_query_id=update.callback_query.id)
    return

  if data == "voy":
      result = raidVoy(chat_id, message_id, user_id)
      if result is True:
          if group["plusmax"]>0:
              bot.answerCallbackQuery(text="¡Te has apuntado! Si vas con más gente, pulsa +1", callback_query_id=update.callback_query.id)
          else:
              bot.answerCallbackQuery(text="¡Te has apuntado correctamente!", callback_query_id=update.callback_query.id)
          update_text = True
      elif result == "no_changes":
          bot.answerCallbackQuery(text="¡Ya te habías apuntado antes!", callback_query_id=update.callback_query.id, show_alert="true")
      elif result == "old_raid":
          bot.answerCallbackQuery(text="Ya no te puedes apuntar a esta incursión", callback_query_id=update.callback_query.id, show_alert="true")
      elif result == "not_raid":
          bot.answerCallbackQuery(text="La incursión no existe. Pudo haberse borrado ya o puede estar fallando el bot.", callback_query_id=update.callback_query.id, show_alert="true")
      else:
          bot.answerCallbackQuery(text="¡No has podido apuntarte! Error desconocido", callback_query_id=update.callback_query.id, show_alert="true")
  elif data in ["plus1", "plus1red", "plus1yellow", "plus1blue"]:
      plus1type = data.replace("plus1","")
      result = raidPlus1(chat_id, message_id, user_id, plus1type = plus1type)
      if result == "old_raid":
          bot.answerCallbackQuery(text="Ya no te puedes apuntar a esta incursión", callback_query_id=update.callback_query.id, show_alert="true")
      elif result == "not_raid":
          bot.answerCallbackQuery(text="La incursión no existe. Pudo haberse borrado ya o puede estar fallando el bot.", callback_query_id=update.callback_query.id, show_alert="true")
      elif result == "demasiados":
          group = getGroup(chat_id)
          bot.answerCallbackQuery(text="No puedes apuntarte con más de %s personas. Si quieres borrar personas, pulsa en el botón «Voy»." % group["plusmax"], callback_query_id=update.callback_query.id, show_alert="true")
      elif str(result).isdigit():
          bot.answerCallbackQuery(text="¡Te has apuntado con %i más! Si sois más, pulsa +1" % result, callback_query_id=update.callback_query.id)
          update_text = True
      else:
          bot.answerCallbackQuery(text="¡No has podido apuntarte con más gente! Error desconocido", callback_query_id=update.callback_query.id, show_alert="true")
  elif data == "novoy":
      result = raidNovoy(chat_id, message_id, user_id)
      if result is True:
          bot.answerCallbackQuery(text="Te has desapuntado de la incursión", callback_query_id=update.callback_query.id)
          update_text = True
      elif result == "old_raid":
          bot.answerCallbackQuery(text="Ya no te puedes desapuntar de esta incursión", callback_query_id=update.callback_query.id, show_alert="true")
      elif result == "not_raid":
          bot.answerCallbackQuery(text="La incursión no existe. Pudo haberse borrado ya o puede estar fallando el bot.", callback_query_id=update.callback_query.id, show_alert="true")
      elif result == "no_changes":
          bot.answerCallbackQuery(text="¡Ya te habías desapuntado antes! Si te has equivocado, pulsa en «voy».", callback_query_id=update.callback_query.id, show_alert="true")
      else:
          bot.answerCallbackQuery(text="¡No has podido desapuntarte! Error desconocido", callback_query_id=update.callback_query.id, show_alert="true")
  elif data == "estoy":
      result = raidEstoy(chat_id, message_id, user_id)
      if result is True:
          bot.answerCallbackQuery(text="Has marcardo que has llegado a la incursión", callback_query_id=update.callback_query.id)
          update_text = True
      elif result == "no_changes":
          bot.answerCallbackQuery(text="¡Ya habías marcado antes que estás! Si te has equivocado, pulsa en «voy».", callback_query_id=update.callback_query.id, show_alert="true")
      elif result == "old_raid":
          bot.answerCallbackQuery(text="Ya no puedes marcar que estás en esta incursión", callback_query_id=update.callback_query.id, show_alert="true")
      elif result == "not_raid":
          bot.answerCallbackQuery(text="La incursión no existe. Pudo haberse borrado ya o puede estar fallando el bot.", callback_query_id=update.callback_query.id, show_alert="true")
      else:
          bot.answerCallbackQuery(text="¡No has podido marcar como llegado! Error desconocido", callback_query_id=update.callback_query.id, show_alert="true")
  elif data == "llegotarde":
      result = raidLlegotarde(chat_id, message_id, user_id)
      if result is True:
          bot.answerCallbackQuery(text="Has marcardo que llegarás tarde a la incursión", callback_query_id=update.callback_query.id)
          update_text = True
      elif result == "no_changes":
          bot.answerCallbackQuery(text="¡Ya habías marcado que llegas tarde! Si te has equivocado, pulsa en «voy».", callback_query_id=update.callback_query.id, show_alert="true")
      elif result == "old_raid":
          bot.answerCallbackQuery(text="Ya no puedes decir que has llegado tarde a esta incursión", callback_query_id=update.callback_query.id, show_alert="true")
      elif result == "not_raid":
          bot.answerCallbackQuery(text="La incursión no existe. Pudo haberse borrado ya o puede estar fallando el bot.", callback_query_id=update.callback_query.id, show_alert="true")
      else:
          bot.answerCallbackQuery(text="¡No has podido marcar como que llegas tarde! Error desconocido", callback_query_id=update.callback_query.id, show_alert="true")
  elif data == "lotengo":
      result = raidLotengo(chat_id, message_id, user_id)
      if result is True:
          bot.answerCallbackQuery(text="Has marcado que lo has capturado, ¡enhorabuena!", callback_query_id=update.callback_query.id)
          update_text = True
      elif result == "no_changes":
          bot.answerCallbackQuery(text="¡Ya habías marcado antes que lo has capturado!", callback_query_id=update.callback_query.id, show_alert="true")
      elif result == "old_raid":
          bot.answerCallbackQuery(text="Ya no puedes marcar que has capturado este Pokémon.", callback_query_id=update.callback_query.id, show_alert="true")
      elif result == "not_raid":
          bot.answerCallbackQuery(text="La incursión no existe. Pudo haberse borrado ya o puede estar fallando el bot.", callback_query_id=update.callback_query.id, show_alert="true")
      elif result == "not_going":
          bot.answerCallbackQuery(text="No pudes marcar que has capturado este Pokémon porque te habías desapuntado de la incursión.", callback_query_id=update.callback_query.id, show_alert="true")
      elif result == "not_now":
          bot.answerCallbackQuery(text="No puedes marcar que has capturado este Pokémon porque no te habías apuntado a la incursión.", callback_query_id=update.callback_query.id, show_alert="true")
      else:
          bot.answerCallbackQuery(text="¡No has podido marcar que lo has capturado! Error desconocido", callback_query_id=update.callback_query.id, show_alert="true")
  elif data == "escapou":
      result = raidEscapou(chat_id, message_id, user_id)
      if result is True:
          bot.answerCallbackQuery(text="Has marcado que ha escapado, ¡lo siento!", callback_query_id=update.callback_query.id)
          update_text = True
      elif result == "no_changes":
          bot.answerCallbackQuery(text="¡Ya habías marcado antes que se te ha escapado!", callback_query_id=update.callback_query.id, show_alert="true")
      elif result == "old_raid":
          bot.answerCallbackQuery(text="Ya no puedes marcar que se te ha escapado este Pokémon.", callback_query_id=update.callback_query.id, show_alert="true")
      elif result == "not_raid":
          bot.answerCallbackQuery(text="La incursión no existe. Pudo haberse borrado ya o puede estar fallando el bot.", callback_query_id=update.callback_query.id, show_alert="true")
      elif result == "not_going":
          bot.answerCallbackQuery(text="No pudes marcar que se te ha escapado este Pokémon porque te habías desapuntado de la incursión.", callback_query_id=update.callback_query.id, show_alert="true")
      elif result == "not_now":
          bot.answerCallbackQuery(text="No puedes marcar que se te ha escapado este Pokémon porque no te habías apuntado a la incursión.", callback_query_id=update.callback_query.id, show_alert="true")
      else:
          bot.answerCallbackQuery(text="¡No has podido marcar que se te ha escapado! Error desconocido", callback_query_id=update.callback_query.id, show_alert="true")
  if update_text:
      raid = getRaidbyMessage(chat_id, message_id)
      if raid is not None:
        reply_markup = get_keyboard(raid)
        update_message(chat_id, message_id, reply_markup, bot)
      else:
        bot.answerCallbackQuery(text="Error actualizando incursión", callback_query_id=update.callback_query.id, show_alert="true")

  if data=="ubicacion":
    raid = getRaidbyMessage(chat_id, message_id)
    if raid is not None and raid["gimnasio_id"] is not None:
      try:
        gym = getPlace(raid["gimnasio_id"])
        if gym is not None:
          if gym["address"] is None:
              gym = fetch_gym_address(gym)
          bot.sendVenue(chat_id=user_id, latitude=gym["latitude"], longitude=gym["longitude"], title=gym["desc"], address=gym["address"])
          if not already_sent_location(user_id, raid["gimnasio_id"]):
              bot.answerCallbackQuery(text="🌎 Te envío la ubicación por privado", callback_query_id=update.callback_query.id)
          else:
              bot.answerCallbackQuery(text="Cuando pulsas el botón de Ubicación, se envía un mensaje privado con la ubicación. Comprueba tu lista de conversaciones.", show_alert="true", callback_query_id=update.callback_query.id)
        else:
          bot.answerCallbackQuery(text="❌ La ubicación es desconocida", callback_query_id=update.callback_query.id)
      except:
        bot.answerCallbackQuery(text="Para que te pueda enviar la ubicación, debes abrir un privado antes con @%s y pulsar en 'Iniciar'" % config["telegram"]["botalias"], callback_query_id=update.callback_query.id, show_alert="true")
    else:
      bot.answerCallbackQuery(text="La ubicación es desconocida", callback_query_id=update.callback_query.id, show_alert="true")

  # Create raid interactively
  if re.match("^iraid_.+", data) != None:
    raid = getRaidbyMessage(chat_id, message_id)

    if (chat_type == "channel" and not is_admin(chat_id, user_id, bot)) or (chat_type != "channel" and user_id != raid["usuario_id"]):
        bot.answerCallbackQuery(text="Solo puede seleccionar las opciones de la incursión el usuario que la está creando.", callback_query_id=update.callback_query.id, show_alert="true")
        return

    if re.match("^iraid_pokemon_.+", data) != None:
        m = re.match("^iraid_pokemon_(.+)", data)
        if m.group(1) in pokemonlist:
            raid["pokemon"] = m.group(1)
        elif m.group(1) in egglist:
            raid["egg"] = m.group(1)
        else:
            return
        saveRaid(raid)
        text_pokemon = format_text_pokemon(raid["pokemon"], raid["egg"], "html")
        creating_text = format_text_creating(thisuser)
        if raid["egg"] != "EX":
            reply_markup = get_times_keyboard(group["timezone"])
            bot.edit_message_text(text="🤔 %s\n\nHas escogido una incursión %s. Ahora selecciona la hora a la que quieres crearla.\n\n<i>(Este mensaje se borrará si no completas el proceso de creación en menos de un minuto)</i>" % (creating_text, text_pokemon), chat_id=chat_id, message_id=message_id, reply_markup=reply_markup, parse_mode=telegram.ParseMode.HTML, disable_web_page_preview=True)
        else:
            reply_markup = get_days_keyboard(group["timezone"])
            bot.edit_message_text(text="🤔 %s\n\nHas escogido una incursión %s. Ahora selecciona el día en el que quieres crearla.\n\n<i>(Este mensaje se borrará si no completas el proceso de creación en menos de un minuto)</i>" % (creating_text, text_pokemon), chat_id=chat_id, message_id=message_id, reply_markup=reply_markup, parse_mode=telegram.ParseMode.HTML, disable_web_page_preview=True)

    if re.match("^iraid_date_[0-9]{1,2}/00:[0-9]{1,2}$", data) != None:
        m = re.match("^iraid_date_([0-9]{1,2}/00:[0-9]{1,2})$", data)
        raid["timeraid"] = parse_time(m.group(1), group["timezone"])
        saveRaid(raid)
        m2 = re.match("^iraid_date_[0-9]{1,2}/00:([0-9]{1,2})$", data)
        time_offset = False if m2.group(1) == "00" else True
        reply_markup = get_times_keyboard(group["timezone"], date=raid["timeraid"], offset=time_offset)
        text_pokemon = format_text_pokemon(raid["pokemon"], raid["egg"], "html")
        creating_text = format_text_creating(thisuser)
        text_day = format_text_day(raid["timeraid"], group["timezone"], "html")
        if text_day != "":
            text_day = " " + text_day
        text_time = extract_time(raid["timeraid"])
        bot.edit_message_text(text="🤔 %s\n\nHas escogido una incursión %s%s. Ahora selecciona la hora a la que quieres crearla.\n\n<i>(Este mensaje se borrará si no completas el proceso de creación en menos de un minuto)</i>" % (creating_text, text_pokemon, text_day), chat_id=chat_id, message_id=message_id, reply_markup=reply_markup, parse_mode=telegram.ParseMode.HTML, disable_web_page_preview=True)

    if re.match("^iraid_time_[0-9]{1,2}/[0-9]{2}:[0-9]{2}$", data) != None:
        m = re.match("^iraid_time_([0-9]{1,2}/[0-9]{2}:[0-9]{2})$", data)
        raid["timeraid"] = parse_time(m.group(1), group["timezone"])
        saveRaid(raid)
        reply_markup = get_gyms_keyboard(group["id"])
        text_pokemon = format_text_pokemon(raid["pokemon"], raid["egg"], "html")
        creating_text = format_text_creating(thisuser)
        text_day = format_text_day(raid["timeraid"], group["timezone"], "html")
        if text_day != "":
            text_day = " " + text_day
        text_time = extract_time(raid["timeraid"])
        gyms_ordering = "alphabetical" if group["raidcommandorder"] == 0 else "activity"
        reply_markup = get_zones_keyboard(group["id"], gyms_ordering)
        if reply_markup is False:
            reply_markup = get_gyms_keyboard(group["id"], order=gyms_ordering)
            bot.edit_message_text(text="🤔 %s\n\nHas escogido una incursión %s%s a las <b>%s</b>. Ahora selecciona el gimnasio en el que quieres crearla. Si no está en la lista, pulsa <i>Cancelar</i> y escribe el comando manualmente.\n\n<i>(Este mensaje se borrará si no completas el proceso de creación en menos de un minuto)</i>" % (creating_text, text_pokemon, text_day, text_time), chat_id=chat_id, message_id=message_id, reply_markup=reply_markup, parse_mode=telegram.ParseMode.HTML, disable_web_page_preview=True)
        else:
            bot.edit_message_text(text="🤔 %s\n\nHas escogido una incursión %s%s a las <b>%s</b>. Ahora selecciona la zona del gimnasio en el que quieres crearla.\n\n<i>(Este mensaje se borrará si no completas el proceso de creación en menos de un minuto)</i>" % (creating_text, text_pokemon, text_day, text_time), chat_id=chat_id, message_id=message_id, reply_markup=reply_markup, parse_mode=telegram.ParseMode.HTML, disable_web_page_preview=True)

    if re.match("^iraid_zone_.+$", data) != None:
        m = re.match("^iraid_zone_(.+)$", data)
        raid["gimnasio_text"] = m.group(1)
        saveRaid(raid)
        gyms_ordering = "alphabetical" if group["raidcommandorder"] == 0 else "activity"
        reply_markup = get_gyms_keyboard(group["id"], 0, m.group(1), order=gyms_ordering)
        text_pokemon = format_text_pokemon(raid["pokemon"], raid["egg"], "html")
        creating_text = format_text_creating(thisuser)
        text_day = format_text_day(raid["timeraid"], group["timezone"], "html")
        if text_day != "":
            text_day = " " + text_day
        text_time = extract_time(raid["timeraid"])
        bot.edit_message_text(text="🤔 %s\n\nHas escogido una incursión %s%s a las <b>%s</b>. Ahora selecciona el gimnasio en el que quieres crearla.\n\n<i>(Este mensaje se borrará si no completas el proceso de creación en menos de un minuto)</i>" % (creating_text, text_pokemon, text_day, text_time), chat_id=chat_id, message_id=message_id, reply_markup=reply_markup, parse_mode=telegram.ParseMode.HTML, disable_web_page_preview=True)

    if re.match("^iraid_gyms_page[1-9]$", data) != None:
        m = re.match("^iraid_gyms_page([1-9])$", data)
        gyms_ordering = "alphabetical" if group["raidcommandorder"] == 0 else "activity"
        reply_markup = get_gyms_keyboard(group["id"], page=int(m.group(1))-1, zone=raid["gimnasio_text"], order=gyms_ordering)
        text_pokemon = format_text_pokemon(raid["pokemon"], raid["egg"], "html")
        creating_text = format_text_creating(thisuser)
        text_day = format_text_day(raid["timeraid"], group["timezone"], "html")
        if text_day != "":
            text_day = " " + text_day
        text_time = extract_time(raid["timeraid"])
        bot.edit_message_text(text="🤔 %s\n\nHas escogido una incursión %s%s a las <b>%s</b>. Ahora selecciona el gimnasio en el que quieres crearla. Si no está en la lista, pulsa <i>Cancelar</i> y escribe el comando manualmente.\n\n<i>(Este mensaje se borrará si no completas el proceso de creación en menos de un minuto)</i>" % (creating_text, text_pokemon, text_day, text_time), chat_id=chat_id, message_id=message_id, reply_markup=reply_markup, parse_mode=telegram.ParseMode.HTML, disable_web_page_preview=True)

    if re.match("^iraid_gym_[0-9]+$", data) != None: # NEWCODE
        m = re.match("^iraid_gym_([0-9]+)$", data)
        gym = getPlace(m.group(1))
        raid["gimnasio_id"] = gym["id"]
        raid["gimnasio_text"] = gym["desc"]
        saveRaid(raid)
        text_pokemon = format_text_pokemon(raid["pokemon"], raid["egg"], "html")
        creating_text = format_text_creating(thisuser)
        text_day = format_text_day(raid["timeraid"], group["timezone"], "html")
        if text_day != "":
            text_day = " " + text_day
        text_time = extract_time(raid["timeraid"])
        text_gym = gym["desc"]
        reply_markup = get_endtimes_keyboard(raid["timeraid"])
        bot.edit_message_text(text="🤔 %s\n\nHas escogido una incursión %s%s a las <b>%s</b> en <b>%s</b>. Ahora selecciona la hora <b>a la que desaparece</b> el Pokémon.\n\n<i>(Este mensaje se borrará si no completas el proceso de creación en menos de un minuto)</i>" % (creating_text, text_pokemon, text_day, text_time, text_gym), chat_id=chat_id, message_id=message_id, reply_markup=reply_markup, parse_mode=telegram.ParseMode.HTML, disable_web_page_preview=True)

    if re.match("^iraid_endtime_.+$", data) != None: # OLDCODE
        m = re.match("^iraid_endtime_(.+)$", data)
        if m.group(1) != "unknown":
            raid["timeend"] = parse_time(m.group(1), group["timezone"])
        raid["status"] = "waiting"
        saveRaid(raid)
        reply_markup = get_keyboard(raid)
        updated = update_message(raid["grupo_id"], raid["message"], reply_markup, bot)
        if chat_type != "channel":
            send_edit_instructions(group, raid, user_id, bot)
        if raid["gimnasio_id"] is not None:
            Thread(target=send_alerts_delayed, args=(raid, bot)).start()

    if data == "iraid_cancel":
        raid["status"] = "deleted"
        saveRaid(raid)
        bot.deleteMessage(chat_id=chat_id, message_id=message_id)

  # Settings and admin stuff
  settings_goto = {"settings_goto_main":"main", "settings_goto_raids":"raids", "settings_goto_commands":"commands", "settings_goto_behaviour": "behaviour", "settings_goto_raidbehaviour": "raidbehaviour", "settings_goto_ranking":"ranking"}

  for k in settings_goto:
      if data==k:
        if not is_admin(chat_id, user_id, bot):
            bot.answerCallbackQuery(text="Solo los administradores del grupo pueden configurar el bot", callback_query_id=update.callback_query.id, show_alert="true")
        else:
            update_settings_message(chat_id, bot, keyboard = settings_goto[k])

  if data=="settings_done":
      if not is_admin(chat_id, user_id, bot):
          bot.answerCallbackQuery(text="Solo los administradores del grupo pueden configurar el bot", callback_query_id=update.callback_query.id, show_alert="true")
      else:
          delete_message(chat_id, message_id, bot)

  settings = {"settings_alertas":"alerts", "settings_desagregado":"disaggregated", "settings_botonllegotarde":"latebutton", "settings_reflotar": "refloat", "settings_lotengo": "gotitbuttons", "settings_borrar":"candelete", "settings_locations":"locations", "settings_raidcommand":"raidcommand", "settings_gymcommand":"gymcommand", "settings_babysitter":"babysitter", "settings_timeformat":"timeformat", "settings_validationrequired":"validationrequired", "settings_listorder":"listorder", "settings_plusdisaggregated":"plusdisaggregated", "settings_plusdisaggregatedinline":"plusdisaggregatedinline", "settings_raidcommandorder":"raidcommandorder", "settings_rankingauto":"rankingauto"}

  settings_categories = {"settings_alertas":"behaviour", "settings_desagregado":"raids", "settings_botonllegotarde":"raidbehaviour", "settings_reflotar": "commands", "settings_lotengo": "raidbehaviour", "settings_borrar":"commands", "settings_locations":"behaviour", "settings_raidcommand":"commands", "settings_gymcommand":"commands", "settings_babysitter":"behaviour", "settings_timeformat":"raids", "settings_validationrequired":"behaviour", "settings_icontheme":"raids", "settings_plusmax":"raidbehaviour", "settings_refloatauto":"behaviour", "settings_listorder":"raids", "settings_snail":"raids", "settings_plusdisaggregated":"raidbehaviour", "settings_plusdisaggregatedinline":"raids", "settings_raidcommandorder":"raids", "settings_rankingweek":"ranking", "settings_rankingmonth":"ranking", "settings_rankingauto":"ranking"}

  for k in settings:
      if data==k:
          if not is_admin(chat_id, user_id, bot):
              bot.answerCallbackQuery(text="Solo los administradores del grupo pueden configurar el bot", callback_query_id=update.callback_query.id, show_alert="true")
          else:
              group = getGroup(chat_id)
              if group[settings[k]] == 1:
                  group[settings[k]] = 0
                  if k == "settings_locations" and group["alerts"] == 1:
                      group["alerts"] = 0
                      bot.answerCallbackQuery(text="Al desactivar las ubicaciones, se han desactivado también automáticamente las alertas.", callback_query_id=update.callback_query.id, show_alert="true")
                  elif k == "settings_plusdisaggregated" and group["plusdisaggregatedinline"] == 1:
                      group["plusdisaggregatedinline"] = 0
                      bot.answerCallbackQuery(text="Al desactivar los botones +1 por equipo, se ha desactivado también automáticamente la visualización de +1 disgregados por línea en las opciones de vista.", callback_query_id=update.callback_query.id, show_alert="true")
              else:
                  group[settings[k]] = 1
                  if k == "settings_alertas" and group["locations"] == 0:
                      group["locations"] = 1
                      bot.answerCallbackQuery(text="Al activar las alertas, se han activado también automáticamente las ubicaciones.", callback_query_id=update.callback_query.id, show_alert="true")
                  elif k == "settings_plusdisaggregatedinline" and group["plusdisaggregated"] == 0:
                      group["plusdisaggregated"] = 1
                      bot.answerCallbackQuery(text="Al activar la visualización de +1 disagregados en línea, se han activado también automáticamente los botones +1 por equipo.", callback_query_id=update.callback_query.id, show_alert="true")
                  elif k == "settings_plusdisaggregated" and group["plusmax"] == 0:
                      group["plusmax"] = 5
                      bot.answerCallbackQuery(text="Al activar los botones +1 por cada equipo, se ha activado también automáticamente el botón «+1» con un máximo por defecto de 5 acompañantes.", callback_query_id=update.callback_query.id, show_alert="true")
              saveGroup(group)
              update_settings_message(chat_id, bot, settings_categories[k])

  if data=="settings_icontheme":
      if not is_admin(chat_id, user_id, bot):
          bot.answerCallbackQuery(text="Solo los administradores del grupo pueden configurar el bot", callback_query_id=update.callback_query.id, show_alert="true")
      else:
          group = getGroup(chat_id)
          group["icontheme"] = group["icontheme"] + 1
          if group["icontheme"] >= len(iconthemes):
              group["icontheme"] = 0
          saveGroup(group)
          update_settings_message(chat_id, bot, settings_categories[data])

  if data=="settings_plusmax":
      if not is_admin(chat_id, user_id, bot):
          bot.answerCallbackQuery(text="Solo los administradores del grupo pueden configurar el bot", callback_query_id=update.callback_query.id, show_alert="true")
      else:
          group = getGroup(chat_id)
          if group["plusmax"] == 0:
              group["plusmax"] = 1
          elif group["plusmax"] == 1:
              group["plusmax"] = 2
          elif group["plusmax"] == 2:
              group["plusmax"] = 3
          elif group["plusmax"] == 3:
              group["plusmax"] = 5
          elif group["plusmax"] == 5:
              group["plusmax"] = 10
          else:
              group["plusmax"] = 0
              if group["plusdisaggregatedinline"] == 1 or group["plusdisaggregated"] == 1:
                  group["plusdisaggregatedinline"] = 0
                  group["plusdisaggregated"] = 0
                  bot.answerCallbackQuery(text="Al desactivar el botón +1, se han desactivado también los botones +1 por equipo y la visualización de +1 disgregados por línea automáticamente.", callback_query_id=update.callback_query.id, show_alert="true")
          saveGroup(group)
          update_settings_message(chat_id, bot, settings_categories[data])

  if data=="settings_snail":
      if not is_admin(chat_id, user_id, bot):
          bot.answerCallbackQuery(text="Solo los administradores del grupo pueden configurar el bot", callback_query_id=update.callback_query.id, show_alert="true")
      else:
          group = getGroup(chat_id)
          if group["snail"] == 0:
              group["snail"] = 1
          elif group["snail"] == 1:
              group["snail"] = 3
          elif group["snail"] == 3:
              group["snail"] = 5
          elif group["snail"] == 5:
              group["snail"] = 10
          else:
              group["snail"] = 0
          saveGroup(group)
          update_settings_message(chat_id, bot, settings_categories[data])

  if data=="settings_rankingmonth":
      if not is_admin(chat_id, user_id, bot):
          bot.answerCallbackQuery(text="Solo los administradores del grupo pueden configurar el bot", callback_query_id=update.callback_query.id, show_alert="true")
      else:
          group = getGroup(chat_id)
          if group["rankingmonth"] == 0:
              group["rankingmonth"] = 15
          elif group["rankingmonth"] == 15:
              group["rankingmonth"] = 25
          elif group["rankingmonth"] == 25:
              group["rankingmonth"] = 35
          elif group["rankingmonth"] == 35:
              group["rankingmonth"] = 50
          else:
              group["rankingmonth"] = 0
          saveGroup(group)
          update_settings_message(chat_id, bot, settings_categories[data])
      (lastweek_start, lastweek_end, lastmonth_start, lastmonth_end) = ranking_time_periods("Europe/Madrid")
      resetCachedRanking(group["id"], lastmonth_start.strftime("%y-%m-%d"), lastmonth_end.strftime("%y-%m-%d"))

  if data=="settings_rankingweek":
        if not is_admin(chat_id, user_id, bot):
            bot.answerCallbackQuery(text="Solo los administradores del grupo pueden configurar el bot", callback_query_id=update.callback_query.id, show_alert="true")
        else:
            group = getGroup(chat_id)
            if group["rankingweek"] == 0:
                group["rankingweek"] = 5
            elif group["rankingweek"] == 5:
                group["rankingweek"] = 10
            elif group["rankingweek"] == 10:
                group["rankingweek"] = 15
            elif group["rankingweek"] == 15:
                group["rankingweek"] = 20
            elif group["rankingweek"] == 20:
                group["rankingweek"] = 25
            else:
                group["rankingweek"] = 0
            saveGroup(group)
            update_settings_message(chat_id, bot, settings_categories[data])
        (lastweek_start, lastweek_end, lastmonth_start, lastmonth_end) = ranking_time_periods("Europe/Madrid")
        resetCachedRanking(group["id"], lastweek_start.strftime("%y-%m-%d"), lastweek_end.strftime("%y-%m-%d"))


  if data=="settings_refloatauto":
    if not is_admin(chat_id, user_id, bot):
        bot.answerCallbackQuery(text="Solo los administradores del grupo pueden configurar el bot", callback_query_id=update.callback_query.id, show_alert="true")
    else:
        group = getGroup(chat_id)
        if group["refloatauto"] == 0:
            group["refloatauto"] = 5
        elif group["refloatauto"] == 5:
            group["refloatauto"] = 10
        elif group["refloatauto"] == 10:
            group["refloatauto"] = 15
        elif group["refloatauto"] == 15:
            group["refloatauto"] = 30
        else:
            group["refloatauto"] = 0
        saveGroup(group)
        update_settings_message(chat_id, bot, settings_categories[data])

# Basic and register commands
dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('pikaping', pikaping))
dispatcher.add_handler(CommandHandler('help', start))
dispatcher.add_handler(CommandHandler('register', register))
dispatcher.add_handler(CommandHandler('profile', profile))
dispatcher.add_handler(CommandHandler(['stats','ranking'], stats, pass_args=True))
# Admin commands
dispatcher.add_handler(CommandHandler('setspreadsheet', setspreadsheet, pass_args=True))
dispatcher.add_handler(CommandHandler('settimezone', settimezone, pass_args=True))
dispatcher.add_handler(CommandHandler('settalkgroup', settalkgroup, pass_args=True))
dispatcher.add_handler(CommandHandler('refresh', refresh))
dispatcher.add_handler(CommandHandler('list', list))
dispatcher.add_handler(CommandHandler(['raids','incursiones'], raids))
dispatcher.add_handler(CommandHandler('settings', settings))
# Commands related to raids
dispatcher.add_handler(CommandHandler('raid', raid, pass_args=True))
dispatcher.add_handler(CommandHandler(['cancelar','cancel'], cancelar, pass_args=True))
dispatcher.add_handler(CommandHandler(['cerrar','close'], cerrar, pass_args=True))
dispatcher.add_handler(CommandHandler(['descancelar','uncancel'], descancelar, pass_args=True))
dispatcher.add_handler(CommandHandler(['cambiarhora','hora'], cambiarhora, pass_args=True))
dispatcher.add_handler(CommandHandler(['cambiarhorafin','horafin'], cambiarhorafin, pass_args=True))
dispatcher.add_handler(CommandHandler(['cambiargimnasio','gimnasio'], cambiargimnasio, pass_args=True))
dispatcher.add_handler(CommandHandler(['cambiarpokemon','pokemon'], cambiarpokemon, pass_args=True))
dispatcher.add_handler(CommandHandler(['borrar','delete','remove'], borrar, pass_args=True))
dispatcher.add_handler(CommandHandler('reflotar', reflotar, pass_args=True))
dispatcher.add_handler(CommandHandler(['reflotartodo','reflotartodas'], reflotartodas, pass_args=True))
dispatcher.add_handler(CommandHandler(['reflotaractivo','reflotaractivas'], reflotaractivas, pass_args=True))
dispatcher.add_handler(CommandHandler(['reflotarhoy'], reflotarhoy, pass_args=True))
dispatcher.add_handler(CommandHandler('gym', gym, pass_args=True))
# Commands related to alerts
dispatcher.add_handler(MessageHandler(Filters.location, processLocation))
dispatcher.add_handler(CommandHandler('alerts', alerts, pass_args=True))
dispatcher.add_handler(CommandHandler('alertas', alerts, pass_args=True))
dispatcher.add_handler(CommandHandler('addalert', addalert, pass_args=True))
dispatcher.add_handler(CommandHandler('delalert', delalert, pass_args=True))
dispatcher.add_handler(CommandHandler('clearalerts', clearalerts))
dispatcher.add_handler(CallbackQueryHandler(raidbutton))
# Channel support and unknown commands
dispatcher.add_handler(MessageHandler(Filters.command, channelCommands))
# Text and welcome message
dispatcher.add_handler(MessageHandler(Filters.text | Filters.photo | Filters.voice | Filters.sticker | Filters.audio | Filters.video | Filters.contact | Filters.game, processMessage))
dispatcher.add_handler(MessageHandler(Filters.status_update, joinedChat))


j = updater.job_queue
def callback_update_raids_status(bot, job):
    Thread(target=update_raids_status, args=(bot,)).start()
job = j.run_repeating(callback_update_raids_status, interval=60, first=12)
def callback_update_validations_status(bot, job):
    Thread(target=update_validations_status, args=(bot,)).start()
job2 = j.run_repeating(callback_update_validations_status, interval=60, first=18)
def callback_auto_refloat(bot, job):
    Thread(target=auto_refloat, args=(bot,)).start()
job3 = j.run_repeating(callback_auto_refloat, interval=120, first=26)
def callback_remove_incomplete_raids(bot, job):
    Thread(target=remove_incomplete_raids, args=(bot,)).start()
job4 = j.run_repeating(callback_remove_incomplete_raids, interval=15, first=42)
def callback_auto_ranking(bot, job):
    Thread(target=auto_ranking, args=(bot,)).start()
job6 = j.run_repeating(callback_auto_ranking, interval=300, first=10) # FIXME change

updater.start_polling()
