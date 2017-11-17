import re
from datetime import datetime
from pytz import timezone
import time
import logging
from threading import Thread
import telegram
from telegram import ChatAction, InlineKeyboardButton, InlineKeyboardMarkup
from Levenshtein import distance
import cv2
import tempfile
import os, sys
import numpy as np
import pytesseract
from PIL import Image, ImageOps
from skimage.measure import compare_ssim as ssim

from storagemethods import getRaidbyMessage, getCreadorRaid, getRaidPeople, getRaid, getAlertsByPlace, getGroup, updateRaidsStatus, updateValidationsStatus
from telegram.error import (TelegramError, Unauthorized, BadRequest, TimedOut, ChatMigrated, NetworkError)

pokemonlist = ['Bulbasaur','Ivysaur','Venusaur','Charmander','Charmeleon','Charizard','Squirtle','Wartortle','Blastoise','Caterpie','Metapod','Butterfree','Weedle','Kakuna','Beedrill','Pidgey','Pidgeotto','Pidgeot','Rattata','Raticate','Spearow','Fearow','Ekans','Arbok','Pikachu','Raichu','Sandshrew','Sandslash','Nidoran♀','Nidorina','Nidoqueen','Nidoran♂','Nidorino','Nidoking','Clefairy','Clefable','Vulpix','Ninetales','Jigglypuff','Wigglytuff','Zubat','Golbat','Oddish','Gloom','Vileplume','Paras','Parasect','Venonat','Venomoth','Diglett','Dugtrio','Meowth','Persian','Psyduck','Golduck','Mankey','Primeape','Growlithe','Arcanine','Poliwag','Poliwhirl','Poliwrath','Abra','Kadabra','Alakazam','Machop','Machoke','Machamp','Bellsprout','Weepinbell','Victreebel','Tentacool','Tentacruel','Geodude','Graveler','Golem','Ponyta','Rapidash','Slowpoke','Slowbro','Magnemite','Magneton','Farfetch\'d','Doduo','Dodrio','Seel','Dewgong','Grimer','Muk','Shellder','Cloyster','Gastly','Haunter','Gengar','Onix','Drowzee','Hypno','Krabby','Kingler','Voltorb','Electrode','Exeggcute','Exeggutor','Cubone','Marowak','Hitmonlee','Hitmonchan','Lickitung','Koffing','Weezing','Rhyhorn','Rhydon','Chansey','Tangela','Kangaskhan','Horsea','Seadra','Goldeen','Seaking','Staryu','Starmie','Mr.Mime','Scyther','Jynx','Electabuzz','Magmar','Pinsir','Tauros','Magikarp','Gyarados','Lapras','Ditto','Eevee','Vaporeon','Jolteon','Flareon','Porygon','Omanyte','Omastar','Kabuto','Kabutops','Aerodactyl','Snorlax','Articuno','Zapdos','Moltres','Dratini','Dragonair','Dragonite','Mewtwo','Mew','Chikorita','Bayleef','Meganium','Cyndaquil','Quilava','Typhlosion','Totodile','Croconaw','Feraligatr','Sentret','Furret','Hoothoot','Noctowl','Ledyba','Ledian','Spinarak','Ariados','Crobat','Chinchou','Lanturn','Pichu','Cleffa','Igglybuff','Togepi','Togetic','Natu','Xatu','Mareep','Flaaffy','Ampharos','Bellossom','Marill','Azumarill','Sudowoodo','Politoed','Hoppip','Skiploom','Jumpluff','Aipom','Sunkern','Sunflora','Yanma','Wooper','Quagsire','Espeon','Umbreon','Murkrow','Slowking','Misdreavus','Unown','Wobbuffet','Girafarig','Pineco','Forretress','Dunsparce','Gligar','Steelix','Snubbull','Granbull','Qwilfish','Scizor','Shuckle','Heracross','Sneasel','Teddiursa','Ursaring','Slugma','Magcargo','Swinub','Piloswine','Corsola','Remoraid','Octillery','Delibird','Mantine','Skarmory','Houndour','Houndoom','Kingdra','Phanpy','Donphan','Porygon2','Stantler','Smeargle','Tyrogue','Hitmontop','Smoochum','Elekid','Magby','Miltank','Blissey','Raikou','Entei','Suicune','Larvitar','Pupitar','Tyranitar','Lugia','Ho-Oh','Celebi','Treecko','Grovyle','Sceptile','Torchic','Combusken','Blaziken','Mudkip','Marshtomp','Swampert','Poochyena','Mightyena','Zigzagoon','Linoone','Wurmple','Silcoon','Beautifly','Cascoon','Dustox','Lotad','Lombre','Ludicolo','Seedot','Nuzleaf','Shiftry','Taillow','Swellow','Wingull','Pelipper','Ralts','Kirlia','Gardevoir','Surskit','Masquerain','Shroomish','Breloom','Slakoth','Vigoroth','Slaking','Nincada','Ninjask','Shedinja','Whismur','Loudred','Exploud','Makuhita','Hariyama','Azurill','Nosepass','Skitty','Delcatty','Sableye','Mawile','Aron','Lairon','Aggron','Meditite','Medicham','Electrike','Manectric','Plusle','Minun','Volbeat','Illumise','Roselia','Gulpin','Swalot','Carvanha','Sharpedo','Wailmer','Wailord','Numel','Camerupt','Torkoal','Spoink','Grumpig','Spinda','Trapinch','Vibrava','Flygon','Cacnea','Cacturne','Swablu','Altaria','Zangoose','Seviper','Lunatone','Solrock','Barboach','Whiscash','Corphish','Crawdaunt','Baltoy','Claydol','Lileep','Cradily','Anorith','Armaldo','Feebas','Milotic','Castform','Kecleon','Shuppet','Banette','Duskull','Dusclops','Tropius','Chimecho','Absol','Wynaut','Snorunt','Glalie','Spheal','Sealeo','Walrein','Clamperl','Huntail','Gorebyss','Relicanth','Luvdisc','Bagon','Shelgon','Salamence','Beldum','Metang','Metagross','Regirock','Regice','Registeel','Latias','Latios','Kyogre','Groudon','Rayquaza','Jirachi','Deoxys']
egglist = ['N1','N2','N3','N4','N5','EX']

validation_pokemons = ["chikorita", "machop", "growlithe", "diglett", "spinarak", "ditto", "teddiursa", "cubone"]
validation_profiles = ["model1", "model2", "model3"]
validation_names = ["Cebolla", "Calabaza", "Puerro", "Cebolleta", "Remolacha", "Aceituna", "Pimiento", "Zanahoria", "Tomate", "Guisante", "Coliflor", "Pepino", "Berenjena", "Perejil", "Batata", "Aguacate", "Cebolleta", "Alcaparra"]

def is_admin(chat_id, user_id, bot):
    is_admin = False
    for admin in bot.get_chat_administrators(chat_id):
      if user_id == admin.user.id:
        is_admin = True
    return is_admin

def extract_update_info(update):
    logging.debug("supportmethods:extract_update_info: %s" % (update))
    try:
        message = update.message
    except:
        message = update.channel_post
    if message == None:
        message = update.channel_post
    text = message.text
    try:
        user_id = message.from_user.id
    except:
        user_id = None
    chat_id = message.chat.id
    chat_type = message.chat.type
    return (chat_id, chat_type, user_id, text, message)

def send_message_timed(chat_id, text, sleep_time, bot):
    logging.debug("supportmethods:send_message_timed: %s %s %s %s" % (chat_id, text, sleep_time, bot))
    time.sleep(sleep_time)
    bot.sendMessage(chat_id=chat_id, text=text, parse_mode=telegram.ParseMode.MARKDOWN)

def delete_message_timed(chat_id, message_id, sleep_time, bot):
    time.sleep(sleep_time)
    delete_message(chat_id, message_id, bot)

def delete_message(chat_id, message_id, bot):
    try:
        bot.deleteMessage(chat_id=chat_id,message_id=message_id)
        return True
    except:
        return False

def count_people(gente):
    count = 0
    if gente != None:
        for user in gente:
            count = count + 1
            if user["plus"] != None and user["plus"] > 0:
                count = count + user["plus"]
    return count

def count_people_disaggregated(gente):
    numrojos = 0
    numazules = 0
    numamarillos = 0
    numotros = 0
    count = 0
    if gente != None:
        for user in gente:
            count = count + 1
            if user["plus"] != None and user["plus"] > 0:
                count = count + user["plus"]
                numotros = numotros + user["plus"]
            if user["team"] == "Rojo":
                numrojos = numrojos + 1
            elif user["team"] == "Azul":
                numazules = numazules + 1
            elif user["team"] == "Amarillo":
                numamarillos = numamarillos + 1
            else:
                numotros = numotros + 1
    return (numazules, numrojos, numamarillos, numotros, count)

def send_alerts(raid, bot):
    logging.debug("supportmethods:end_alerts: %s" % (raid))
    alerts = getAlertsByPlace(raid["gimnasio_id"])
    group = getGroup(raid["grupo_id"])
    if group["alerts"] == 1:
        what_text = format_text_pokemon(raid["pokemon"], raid["egg"])
        what_day = format_text_day(raid["timeraid"], group["timezone"])
        for alert in alerts:
            bot.sendMessage(chat_id=alert["user_id"], text="🔔 Se ha creado una incursión %s en *%s* %sa las *%s* en el grupo _%s_.\n\n_Recibes esta alerta porque has activado las alertas para ese gimnasio. Si no deseas recibir más alertas, puedes usar el comando_ `/clearalerts`" % (what_text, raid["gimnasio_text"], what_day, extract_time(raid["timeraid"]), group["title"]), parse_mode=telegram.ParseMode.MARKDOWN)

def update_message(chat_id, message_id, reply_markup, bot):
    logging.debug("supportmethods:update_message: %s %s %s" % (chat_id, message_id, reply_markup))
    raid = getRaidbyMessage(chat_id, message_id)
    text = format_message(raid)
    return bot.edit_message_text(text=text, chat_id=chat_id, message_id=message_id, reply_markup=reply_markup, parse_mode=telegram.ParseMode.HTML, disable_web_page_preview=True)

def format_message(raid):
    logging.debug("supportmethods:format_message: %s" % (raid))
    creador = getCreadorRaid(raid["id"])
    gente = getRaidPeople(raid["id"])
    group = getGroup(raid["grupo_id"])

    if "edited" in raid.keys() and raid["edited"]>0:
        text_edited = " <em>(editada)</em>"
    else:
        text_edited = ""
    if "refloated" in raid.keys() and raid["refloated"]>0:
        text_refloated = " <em>(reflotada)</em>"
    else:
        text_refloated = ""
    if "timeend" in raid.keys() and raid["timeend"] != None:
        t = extract_time(raid["timeend"], group["timeformat"])
        text_endtime = "\n<em>Desaparece a las %s</em>" % t
    else:
        text_endtime = ""
    if group["locations"] == 1:
        if "gimnasio_id" in raid.keys() and raid["gimnasio_id"] != None:
            gym_emoji="🌎"
        else:
            gym_emoji="❓"
    else:
        gym_emoji=""
    what_text = format_text_pokemon(raid["pokemon"], raid["egg"], "html")
    what_day = format_text_day(raid["timeraid"], group["timezone"], "html")
    if creador["username"] != None:
        if creador["trainername"] != None:
            created_text = "\nCreada por <a href='https://t.me/%s'>%s</a>%s%s" % (creador["username"], creador["trainername"], text_edited, text_refloated)
        else:
            created_text = "\nCreada por @%s%s%s" % (creador["username"], text_edited, text_refloated)
    else:
        created_text = ""
    text = "Incursión %s %sa las <b>%s</b> en %s<b>%s</b>%s%s\n" % (what_text, what_day, extract_time(raid["timeraid"], group["timeformat"]), gym_emoji, raid["gimnasio_text"], created_text, text_endtime)
    if raid["status"] == "cancelled":
        text = text + "❌ <b>Incursión cancelada</b>"
    else:
        if group["disaggregated"] == 1:
            (numazules, numrojos, numamarillos, numotros, numgente) = count_people_disaggregated(gente)
            text = text + "❄️%s · 🔥%s · ⚡️%s · ❓%s · 👩‍👩‍👧‍👧%s" % (numazules, numrojos, numamarillos, numotros, numgente)
        else:
            numgente = count_people(gente)
            text = text + "%s entrenadores apuntados:" % numgente
    if raid["status"] != "cancelled" and gente != None:
        for user in gente:
            if user["plus"] != None and user["plus"]>0:
                plus_text = " +%i" % user["plus"]
            else:
                plus_text = ""
            if user["estoy"] != None and user["estoy"]>0:
                estoy_text = "✅ "
            elif user["tarde"] != None and user["tarde"]>0:
                estoy_text = "🕒 "
            else:
                estoy_text = "▪️ "
            if user["lotengo"] == 0:
                lotengo_text = "👎"
            elif user["lotengo"] == 1:
                lotengo_text = "👍"
            else:
                lotengo_text = ""
            if user["level"] != None and user["team"] != None:
                if user["team"] != None:
                    if user["team"]=="Rojo":
                        team_badge = "🔥"
                    elif user["team"]=="Amarillo":
                        team_badge = "⚡️"
                    else:
                        team_badge = "❄️"
                if user["trainername"] != None:
                    text = text + "\n%s%s%s <a href='https://t.me/%s'>%s</a>%s%s" % (estoy_text,team_badge,user["level"],user["username"],user["trainername"],lotengo_text,plus_text)
                else:
                    text = text + "\n%s%s%s @%s%s%s" % (estoy_text,team_badge,user["level"],user["username"],lotengo_text,plus_text)
            else:
                text = text + "\n%s➖ - - @%s%s%s" % (estoy_text,user["username"],lotengo_text,plus_text)
    return text

def format_text_pokemon(pokemon, egg, format="markdown"):
    if pokemon != None:
        what_text = "de <b>%s</b>" % pokemon if format == "html" else "de *%s*" % pokemon
    else:
        if egg == "EX":
            what_text = "<b>🌟EX</b>" if format == "html" else "*🌟EX*"
        else:
            what_text = egg.replace("N","de <b>nivel ") + "</b>" if format == "html" else egg.replace("N","de *nivel ") + "*"
    return what_text

def format_text_day(timeraid, tzone, format="markdown"):
    logging.debug("supportmethods:format_text_day %s %s" % (timeraid, tzone))
    try:
        raid_datetime = datetime.strptime(timeraid,"%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone(tzone))
    except:
        raid_datetime = timeraid.replace(tzinfo=timezone(tzone))
    now_datetime = datetime.now(timezone(tzone))
    difftime = raid_datetime - now_datetime
    if difftime.total_seconds() > (3600*16):
        weekdays = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
        what_day = "el <b>%s día %s</b> " % (weekdays[raid_datetime.weekday()], raid_datetime.day) if format == "html" else "el *%s día %s* " % (weekdays[raid_datetime.weekday()], raid_datetime.day)
    else:
        what_day = ""
    return what_day

def ensure_escaped(username):
    if username.find("_") != -1 and username.find("\\_") == -1:
        username = username.replace("_","\\_")
    return username

def update_raids_status(bot):
    logging.debug("supportmethods:update_raids_status")
    raids = updateRaidsStatus()
    for raid in raids:
        logging.debug(raid)
        r = getRaid(raid["id"])
        logging.debug("Updating message for raid ID %s" % (raid["id"]))
        try:
            reply_markup = get_keyboard(r)
            updated = update_message(r["grupo_id"], r["message"], reply_markup, bot)
            logging.debug(updated)
        except Exception as e:
            logging.debug("supportmethods:update_raids_status error: %s" % str(e))
    time.sleep(0.05)

def update_validations_status(bot):
    logging.debug("supportmethods:update_validations_status")
    validations = updateValidationsStatus()
    for v in validations:
        logging.debug(v)
        logging.debug("Sending notification for validation ID %s, user ID %s" % (v["id"], v["usuario_id"]))
        try:
            bot.sendMessage(chat_id=v["usuario_id"], text="⚠ El proceso de validación pendiente ha caducado porque han pasado 6 horas desde que empezó. Si quieres validarte, debes volver a empezar el proceso.", parse_mode=telegram.ParseMode.MARKDOWN)
        except Exception as e:
            logging.debug("supportmethods:update_validations_status error: %s" % str(e))
    time.sleep(0.05)

def error_callback(bot, update, error):
    try:
        raise error
    except Unauthorized:
        logging.debug("TELEGRAM ERROR: Unauthorized - %s" % error)
    except BadRequest:
        logging.debug("TELEGRAM ERROR: Bad Request - %s" % error)
    except TimedOut:
        logging.debug("TELEGRAM ERROR: Slow connection problem - %s" % error)
    except NetworkError:
        logging.debug("TELEGRAM ERROR: Other connection problems - %s" % error)
    except ChatMigrated as e:
        logging.debug("TELEGRAM ERROR: Chat ID migrated?! - %s" % error)
    except TelegramError:
        logging.debug("TELEGRAM ERROR: Other error - %s" % error)
    except:
        logging.debug("TELEGRAM ERROR: Unknown - %s" % error)

def warn_people(warntype, raid, user_username, chat_id, bot):
    logging.debug("supportmethods:warn_people")
    people = getRaidPeople(raid["id"])
    group = getGroup(raid["grupo_id"])
    warned = []
    notwarned = []
    if people == None:
        return
    for p in people:
        if p["username"] == user_username:
            continue
        try:
            user_text = "@%s" % ensure_escaped(user_username) if user_username != None else "Se"
            if warntype == "cancelar":
                text = "❌ %s ha *cancelado* la incursión de %s a las %s en %s" % (user_text, raid["pokemon"], extract_time(raid["timeraid"]), ensure_escaped(raid["gimnasio_text"]))
            elif warntype == "borrar":
                text = "🚫 %s ha *borrado* la incursión de %s a las %s en %s" % (user_text, raid["pokemon"], extract_time(raid["timeraid"]), ensure_escaped(raid["gimnasio_text"]))
            elif warntype == "cambiarhora":
                text_day = format_text_day(raid["timeraid"], group["timezone"])
                if text_day != "":
                    text_day = " " + text_day
                text = "⚠️ %s ha cambiado la hora de la incursión de %s en %s para las *%s*%s" % (user_text, raid["pokemon"], ensure_escaped(raid["gimnasio_text"]), extract_time(raid["timeraid"]), text_day)
            elif warntype == "cambiarhorafin":
                text = "⚠️ %s ha cambiado la hora a la que se termina la incursión de %s en %s a las *%s* (¡ojo, la incursión sigue programada para la misma hora: %s!)" % (user_text, raid["pokemon"], ensure_escaped(raid["gimnasio_text"]), extract_time(raid["timeend"]), extract_time(raid["timeraid"]))
            elif warntype == "borrarhorafin":
                text = "⚠️ %s ha borrado la hora a la que se termina la incursión de %s en %s (¡ojo, la incursión sigue programada para la misma hora: %s!)" % (user_text, raid["pokemon"], ensure_escaped(raid["gimnasio_text"]), extract_time(raid["timeraid"]))
            elif warntype == "cambiargimnasio":
                text = "⚠️ %s ha cambiado el gimnasio de la incursión de %s para las %s a *%s*" % (user_text, raid["pokemon"], extract_time(raid["timeraid"]), ensure_escaped(raid["gimnasio_text"]))
            elif warntype == "cambiarpokemon":
                text_pokemon = format_text_pokemon(raid["pokemon"], raid["egg"])
                text = "⚠️ %s ha cambiado la incursión para las %s en %s a incursión %s" % (user_text, extract_time(raid["timeraid"]), ensure_escaped(raid["gimnasio_text"]), text_pokemon)
            bot.sendMessage(chat_id=p["id"], text=text, parse_mode=telegram.ParseMode.MARKDOWN)
            warned.append(p["username"])
        except Exception as e:
            logging.debug("supportmethods:warn_people error sending message to %s: %s" % (p["username"],str(e)))
            notwarned.append(p["username"])
    if len(warned)>0:
        bot.sendMessage(chat_id=chat_id, text="He avisado por privado a: @%s" % ensure_escaped(", @".join(warned)), parse_mode=telegram.ParseMode.MARKDOWN)
    if len(notwarned)>0:
        bot.sendMessage(chat_id=chat_id, text="No he podido avisar a: @%s" % ensure_escaped(", @".join(notwarned)), parse_mode=telegram.ParseMode.MARKDOWN)

def get_settings_keyboard(chat_id):
    logging.debug("supportmethods:get_settings_keyboard")
    group = getGroup(chat_id)
    if group["alerts"] == 1:
        alertas_text = "✅ Alertas"
    else:
        alertas_text = "▪️ Alertas"
    if group["disaggregated"] == 1:
        disaggregated_text = "✅ Total desagregado"
    else:
        disaggregated_text = "▪️ Total desagregado"
    if group["latebutton"] == 1:
        latebutton_text = "✅ ¡Llego tarde!"
    else:
        latebutton_text = "▪️ ¡Llego tarde!"
    if group["refloat"] == 1:
        refloat_text = "✅ Reflotar incursiones"
    else:
        refloat_text = "▪️ Reflotar incursiones"
    if group["candelete"] == 1:
        candelete_text = "✅ Borrar incursiones"
    else:
        candelete_text = "▪️ Borrar incursiones"
    if group["gotitbuttons"] == 1:
        gotitbuttons_text = "✅ ¡Lo tengo!"
    else:
        gotitbuttons_text = "▪️ ¡Lo tengo!"
    if group["locations"] == 1:
        locations_text = "✅ Ubicaciones"
    else:
        locations_text = "▪️ Ubicaciones"
    if group["gymcommand"] == 1:
        gymcommand_text = "✅ Comando /gym"
    else:
        gymcommand_text = "▪️ Comando /gym"
    if group["raidcommand"] == 1:
        raidcommand_text = "✅ Comando /raid"
    else:
        raidcommand_text = "▪️ Comando /raid"
    if group["babysitter"] == 1:
        babysitter_text = "✅ Modo niñero"
    else:
        babysitter_text = "▪️ Modo niñero"
    if group["timeformat"] == 1:
        timeformat_text = "✅ Horas AM/PM"
    else:
        timeformat_text = "▪️ Horas AM/PM"
    settings_keyboard = [[InlineKeyboardButton(locations_text, callback_data='settings_locations'), InlineKeyboardButton(alertas_text, callback_data='settings_alertas')],
    [InlineKeyboardButton(gymcommand_text, callback_data='settings_gymcommand'), InlineKeyboardButton(raidcommand_text, callback_data='settings_raidcommand')],
    [InlineKeyboardButton(refloat_text, callback_data='settings_reflotar'), InlineKeyboardButton(candelete_text, callback_data='settings_borrar')], [InlineKeyboardButton(latebutton_text, callback_data='settings_botonllegotarde'), InlineKeyboardButton(gotitbuttons_text, callback_data='settings_lotengo')], [InlineKeyboardButton(disaggregated_text, callback_data='settings_desagregado'), InlineKeyboardButton(timeformat_text, callback_data='settings_timeformat')], [InlineKeyboardButton(babysitter_text, callback_data='settings_babysitter')]]
    settings_markup = InlineKeyboardMarkup(settings_keyboard)
    return settings_markup

def get_keyboard(raid):
    group = getGroup(raid["grupo_id"])
    if raid["status"] == "started" or raid["status"] == "waiting":
        keyboard_row1 = [InlineKeyboardButton("🙋 ¡Voy!", callback_data='voy'), InlineKeyboardButton("👭 +1", callback_data='plus1'), InlineKeyboardButton("🙅 No voy", callback_data='novoy')]
        keyboard_row2 = [InlineKeyboardButton("✅ ¡Estoy allí!", callback_data='estoy')]
        if group["latebutton"] == 1:
            keyboard_row2.append(InlineKeyboardButton("🕒 ¡Llego tarde!", callback_data='llegotarde'))
        if raid["gimnasio_id"] != None:
            keyboard_row2.append(InlineKeyboardButton("🌎 Ubicación", callback_data='ubicacion'))
        keyboard = [keyboard_row1, keyboard_row2]
    else:
        keyboard = []
    if group != None and group["gotitbuttons"] == 1 and (raid["status"] == "started" or raid["status"] == "ended"):
        keyboard.append([InlineKeyboardButton("👍 ¡Lo tengo!", callback_data='lotengo'), InlineKeyboardButton("👎 ¡Ha escapado!", callback_data='escapou')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup

def update_settings_message(chat_id, bot):
    logging.debug("supportmethods:update_settings_message")
    group = getGroup(chat_id)

    settings_markup = get_settings_keyboard(chat_id)
    return bot.edit_message_text(text="Pulsa en los botones de las opciones para cambiarlas. Cuando acabes, puedes borrar el mensaje.\n\nTen en cuenta que los <strong>administradores de un grupo o canal</strong> pueden usar algunos comandos aunque estén desactivados.\n\nPara más información sobre estas funciones, <a href='http://telegra.ph/Detective-Pikachu-09-28'>consulta la ayuda</a>.", chat_id=chat_id, message_id=group["settings_message"], reply_markup=settings_markup, parse_mode=telegram.ParseMode.HTML, disable_web_page_preview=True)

def edit_check_private(chat_id, chat_type, user_username, command, bot):
    logging.debug("supportmethods:edit_check_private")
    if chat_type != "private":
        if user_username != None:
            text = "@%s el comando `/%s` solo funciona por privado.\n\n_(Este mensaje se borrará en unos segundos)_" % (ensure_escaped(user_username), command)
        else:
            text = "El comando `/%s` solo funciona por privado.\n\n_(Este mensaje se borrará en unos segundos)_" % command
        sent_message = bot.sendMessage(chat_id=chat_id, text=text,parse_mode=telegram.ParseMode.MARKDOWN)
        Thread(target=delete_message_timed, args=(chat_id, sent_message.message_id, 15, bot)).start()
        return False
    else:
        return True

def edit_check_private_or_reply(chat_id, chat_type, message, args, user_username, command, bot):
    logging.debug("supportmethods:edit_check_private_or_reply")
    if command == "borrar" or command == "cancelar" or command == "reflotar":
        expectedargs = 0
    else:
        expectedargs = 1
    if len(args)>=expectedargs and hasattr(message, 'reply_to_message') and message.reply_to_message != None:
        delete_message(chat_id, message.message_id, bot)
        reply_chat_id = message.reply_to_message.chat.id
        reply_message_id = message.reply_to_message.message_id
        raid = getRaidbyMessage(reply_chat_id, reply_message_id)
    elif chat_type == "private":
        if len(args)<(expectedargs+1) or (expectedargs>0 and not str(args[expectedargs-1]).isnumeric()):
            bot.sendMessage(chat_id=chat_id, text="¡No he reconocido los datos que me envías!",parse_mode=telegram.ParseMode.MARKDOWN)
            return
        raid_id = args[0]
        raid = getRaid(raid_id)
    else:
        delete_message(chat_id, message.message_id, bot)
        user_text = "@%s" % ensure_escaped(user_username) if user_username != None else "Se"
        text = "%s el comando `/%s` solo funciona por privado o contestando al mensaje de la incursión.\n\n_(Este mensaje se borrará en unos segundos)_" % (user_text, command)
        sent_message = bot.sendMessage(chat_id=chat_id, text=text,parse_mode=telegram.ParseMode.MARKDOWN)
        Thread(target=delete_message_timed, args=(chat_id, sent_message.message_id, 15, bot)).start()
        raid = None
    return raid

def parse_pokemon(pokestr):
    ret_pok = None
    ret_egg = None
    for pokemon in pokemonlist:
      m = re.match("^%s$" % pokemon, pokestr, flags=re.IGNORECASE)
      if m != None:
        ret_pok = pokemon
        break
    if ret_pok == None:
        for pokemon in pokemonlist:
            if distance(pokestr, pokemon) < 3:
                ret_pok = pokemon
                break

    if ret_pok == None:
        for egg in egglist:
            m = re.match("^%s$" % egg, pokestr, flags=re.IGNORECASE)
            if m != None:
                ret_egg = egg
                break
    return (ret_pok, ret_egg)

def parse_time(st, tz):
    logging.debug("supportmethods:parse_time")
    m = re.match("([0-9]{1,2}/)?([0-9]{1,2})[:.]?([0-9]{0,2})h?", st, flags=re.IGNORECASE)
    if m != None:
        hour = str(m.group(2))
        minute = m.group(3) or "00"
        logging.debug("supportmethods:parse_time parsing time %s %s" % (hour, minute))
        if m.group(1) != None:
            day = m.group(1).replace("/","")
        else:
            day = None
        if int(hour)<0 or int(hour)>24 or int(minute)<0 or int(minute)>59 or \
                                (day != None and (int(day)<0 or int(day)>31)):
            logging.debug("supportmethods::parse_time failed parsing time from %s" % st)
            return None
    else:
        logging.debug("supportmethods::parse_time failed parsing time from %s" % st)
        return None

    localdatetime = datetime.now(timezone(tz))
    localtime = localdatetime.time()
    if int(hour) <= 12 and day == None:
        if (int(hour) <= 5) or (int(localtime.hour) >= 15 and int(hour) <= 9 and int(hour)!=0):
                hour = int(hour) + 12

    dt = datetime.now(timezone(tz))
    if day != None:
        if int(day) >= dt.day:
            dt = dt.replace(day=int(day))
        else:
            if dt.month == 12:
                dt = dt.replace(month=1, year=dt.year+1)
            else:
                dt = dt.replace(month=dt.month+1)
    dt = dt.replace(hour=int(hour),minute=int(minute))
    dt_str = dt.strftime("%Y-%m-%d %H:%M:00")
    logging.debug("supportmethods::parse_time parsed %s" % dt_str)
    return dt_str

def extract_time(formatted_datetime, format=0):
    logging.debug("supportmethods:extract_time %s" % formatted_datetime)
    if not isinstance(formatted_datetime,str):
        formatted_datetime = formatted_datetime.strftime("%Y-%m-%d %H:%M:%S")
    m = re.search("([0-9]{1,2}):([0-9]{0,2}):[0-9]{0,2}", formatted_datetime, flags=re.IGNORECASE)
    if m != None:
        if format == 0:
            extracted_time = "%02d:%02d" % (int(m.group(1)), int(m.group(2)))
        else:
            hour = int(m.group(1))
            if hour >=12:
                ampm = "PM"
                if hour > 12:
                    hour = hour -12
            else:
                ampm = "AM"
            extracted_time = "%d:%02d %s" % (hour, int(m.group(2)), ampm)
        logging.debug("supportmethods::extract_time extracted %s" % extracted_time)
        return extracted_time
    else:
        logging.debug("supportmethods::parse_time failed extracting time from %s" % formatted_datetime)
        return None

def extract_day(timeraid, tzone):
    try:
        raid_datetime = datetime.strptime(timeraid,"%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone(tzone))
    except:
        raid_datetime = timeraid.replace(tzinfo=timezone(tzone))
    now_datetime = datetime.now(timezone(tzone))
    difftime = raid_datetime - now_datetime
    if difftime.days > 1:
        return raid_datetime.day
    else:
        return None

def parse_profile_image(filename):
    logging.debug("supportmethods:parse_profile_image %s" % filename)

    new_file, tmpfilename = tempfile.mkstemp(suffix=".png")
    os.close(new_file)

    # Load possible pokemons
    pokemons = {}
    for i in validation_pokemons:
        p = cv2.imread(sys.path[0] + "/modelimgs/pokemon/%s.png" % i)
        p = cv2.cvtColor(p, cv2.COLOR_BGR2GRAY)
        p = cv2.resize(p, (60,60))
        pokemons[i] = { "model":p }

    # Load possible profiles
    profiles = {}
    for i in validation_profiles:
        p = cv2.imread(sys.path[0] + "/modelimgs/profiles/%s.png" % i)
        p = cv2.cvtColor(p, cv2.COLOR_BGR2GRAY)
        p = cv2.resize(p, (120,120))
        profiles[i] = { "model":p }

    # Load the full image
    image = cv2.imread(filename)
    height, width, _ = image.shape
    aspect_ratio = height/width

    # Raise error for unsupported aspect ratios
    if aspect_ratio <= 1.74 or aspect_ratio >= 1.88:
        raise Exception("Aspect ratio not supported")

    # Crop large bars
    bottombar_img = image[int(height-height/14):int(height),int(0):int(width)] # y1:y2,x1:x2
    bottombar_gray = cv2.cvtColor(bottombar_img, cv2.COLOR_BGR2GRAY)
    if bottombar_gray.mean() < 40:
        image = image[int(0):int(height-height/14),int(0):int(width)] # y1:y2,x1:x2
        height, width, _ = image.shape

    # Crop small bars
    bottombar_img = image[int(height-height/17):int(height),int(0):int(width)] # y1:y2,x1:x2
    bottombar_gray = cv2.cvtColor(bottombar_img, cv2.COLOR_BGR2GRAY)
    if bottombar_gray.mean() < 40:
        image = image[int(0):int(height-height/17),int(0):int(width)] # y1:y2,x1:x2
        height, width, _ = image.shape

    # Extract profile layout for profile Testing
    profile_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    profile_gray = profile_gray[int(height/20):int(height),int(0):int(width)] # y1:y2,x1:x2
    profile_gray = cv2.resize(profile_gray, (120,120))
    cv2.rectangle(profile_gray,(60,1),(100,75),(255,255,255),-1) # delete trainer
    cv2.rectangle(profile_gray,(20,20),(60,75),(255,255,255),-1) # delete pokemon
    cv2.rectangle(profile_gray,(8,5),(60,20),(255,255,255),-1)   # delete nickname
    cv2.rectangle(profile_gray,(48,75),(72,85),(255,255,255),-1) # delete level

    # Test extracted profile leyout against possible profile models
    chosen_profile = None
    chosen_similarity = 0.0
    for i in validation_profiles:
        profiles[i]["similarity"] = ssim(profiles[i]["model"], profile_gray)
        logging.debug("supportmethods:parse_profile_image: Similarity with %s: %.2f" % (i,profiles[i]["similarity"]))
        if profiles[i]["similarity"] > 0.7 and (chosen_profile == None or chosen_similarity < profiles[i]["similarity"]):
            chosen_profile = i
            chosen_similarity = profiles[i]["similarity"]
            if profiles[i]["similarity"] > 0.9:
                break
    logging.debug("supportmethods:parse_profile_image: Chosen Pokemon: %s" % chosen_profile)

    # Extract Team
    team1_img = image[int(height/2):int(height/2+height/10),0:int(width/60)] # y1:y2,x1:x2
    boundaries = {
        "Rojo": ([0, 0, 150], [70, 20, 255]),
        "Azul": ([200, 90, 0], [255, 130, 20]),
        "Amarillo": ([0, 190, 200], [20, 215, 255])
    }
    chosen_color = None
    values = {}
    for color in boundaries:
        # create NumPy arrays from the boundaries
        lower = np.array(boundaries[color][0], dtype = "uint8")
        upper = np.array(boundaries[color][1], dtype = "uint8")

        # find the colors within the specified boundaries and apply
        # the mask
        mask = cv2.inRange(team1_img, lower, upper)
        output = cv2.bitwise_and(team1_img, team1_img, mask = mask)

        values[color] = output.mean()
        logging.debug("supportmethods:parse_profile_image: Mean value for color %s: %s" %(color,values[color]))

        if chosen_color == None or values[color] > values[chosen_color]:
            chosen_color = color
    logging.debug("supportmethods:parse_profile_image: Chosen color: %s" % chosen_color)

    # Extract and OCR trainer and Pokémon name
    nick1_img = image[int(height/9):int(height/9*2),int(width/15):int(width/15+2*width/5)] # y1:y2,x1:x2
    if chosen_color == "Amarillo":
        min_thres = 170
    elif chosen_color == "Rojo":
        nick1_img[:, :, 2] = 0
        min_thres = 50
    elif chosen_color == "Azul":
        nick1_img[:, :, 0] = 0
        min_thres = 110
    nick1_gray = cv2.cvtColor(nick1_img, cv2.COLOR_BGR2GRAY)
    ret,nick1_gray = cv2.threshold(nick1_gray,min_thres,255,cv2.THRESH_BINARY)
    cv2.imwrite(tmpfilename, nick1_gray)
    text = pytesseract.image_to_string(Image.open(tmpfilename))
    trainer_name = re.sub(r'\n+.*$','',text)
    trainer_name = trainer_name.replace(" ","").replace("|","l")
    pokemon_name = re.sub(r'^.*\n+([^ ]+)[ ]?','',text)
    logging.debug("supportmethods:parse_profile_image: Trainer name: %s" % trainer_name)
    logging.debug("supportmethods:parse_profile_image: Pokemon name: %s" % pokemon_name)

    # Extract and OCR level
    if aspect_ratio < 1.78:
        level1_img = image[int(height/2+2*height/13):int(height-height/4-height/22),int(width/2):int(width/2+width/7)] # y1:y2,x1:x2
    else:
        level1_img = image[int(height/2+height/8):int(height-height/4-height/16),int(width/2):int(width/2+width/7)] # y1:y2,x1:x2

    if chosen_color == "Amarillo":
        min_thres = 170
    elif chosen_color == "Rojo":
        level1_img[:, :, 2] = 0
        min_thres = 50
    elif chosen_color == "Azul":
        level1_img[:, :, 0] = 0
        min_thres = 130
    level1_gray = cv2.cvtColor(level1_img, cv2.COLOR_BGR2GRAY)
    ret,level1_gray = cv2.threshold(level1_gray,min_thres,255,cv2.THRESH_BINARY)
    cv2.imwrite(tmpfilename, level1_gray)
    level = pytesseract.image_to_string(Image.open(tmpfilename))
    logging.debug("supportmethods:parse_profile_image: Level: %s" % level)
    if int(level)<5 or int(level)>40:
        level = None

    # Extract Pokemon
    if aspect_ratio < 1.78:
        pokemon_img = image[int(height/3):int(height-height/3),int(width/8):int(width/2)] # y1:y2,x1:x2
    else:
        pokemon_img = image[int(height/3-height/42):int(height-height/3-height/42),int(width/8):int(width/2)] # y1:y2,x1:x2
    pokemon_gray = cv2.cvtColor(pokemon_img, cv2.COLOR_BGR2GRAY)
    pokemon_gray = cv2.resize(pokemon_gray, (60,60))

    # Test extracted pokemon against possible pokemons
    chosen_pokemon = None
    chosen_similarity = 0.0
    for i in validation_pokemons:
        pokemons[i]["similarity"] = ssim(pokemons[i]["model"], pokemon_gray)
        logging.debug("supportmethods:parse_profile_image: Similarity with %s: %.2f" % (i,pokemons[i]["similarity"]))
        if pokemons[i]["similarity"] > 0.7 and \
           (chosen_pokemon == None or chosen_similarity < pokemons[i]["similarity"]):
           chosen_pokemon = i
           chosen_similarity = pokemons[i]["similarity"]
           if pokemons[i]["similarity"] > 0.9:
               break
    logging.debug("supportmethods:parse_profile_image: Chosen Pokemon: %s" % chosen_pokemon)

    # Cleanup and return
    os.remove(tmpfilename)
    return (trainer_name, level, chosen_color, chosen_pokemon, pokemon_name, chosen_profile)
