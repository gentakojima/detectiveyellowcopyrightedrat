import re
from datetime import datetime
from pytz import timezone
import time
import logging
from threading import Thread
import telegram
from telegram import ChatAction, InlineKeyboardButton, InlineKeyboardMarkup
from Levenshtein import distance

from storagemethods import getRaidbyMessage, getCreadorRaid, getRaidPeople, endOldRaids, getRaid, getAlertsByPlace, getGroup, updateRaidsStatus
from telegram.error import (TelegramError, Unauthorized, BadRequest, TimedOut, ChatMigrated, NetworkError)

pokemonlist = ['Bulbasaur','Ivysaur','Venusaur','Charmander','Charmeleon','Charizard','Squirtle','Wartortle','Blastoise','Caterpie','Metapod','Butterfree','Weedle','Kakuna','Beedrill','Pidgey','Pidgeotto','Pidgeot','Rattata','Raticate','Spearow','Fearow','Ekans','Arbok','Pikachu','Raichu','Sandshrew','Sandslash','Nidoran♀','Nidorina','Nidoqueen','Nidoran♂','Nidorino','Nidoking','Clefairy','Clefable','Vulpix','Ninetales','Jigglypuff','Wigglytuff','Zubat','Golbat','Oddish','Gloom','Vileplume','Paras','Parasect','Venonat','Venomoth','Diglett','Dugtrio','Meowth','Persian','Psyduck','Golduck','Mankey','Primeape','Growlithe','Arcanine','Poliwag','Poliwhirl','Poliwrath','Abra','Kadabra','Alakazam','Machop','Machoke','Machamp','Bellsprout','Weepinbell','Victreebel','Tentacool','Tentacruel','Geodude','Graveler','Golem','Ponyta','Rapidash','Slowpoke','Slowbro','Magnemite','Magneton','Farfetch\'d','Doduo','Dodrio','Seel','Dewgong','Grimer','Muk','Shellder','Cloyster','Gastly','Haunter','Gengar','Onix','Drowzee','Hypno','Krabby','Kingler','Voltorb','Electrode','Exeggcute','Exeggutor','Cubone','Marowak','Hitmonlee','Hitmonchan','Lickitung','Koffing','Weezing','Rhyhorn','Rhydon','Chansey','Tangela','Kangaskhan','Horsea','Seadra','Goldeen','Seaking','Staryu','Starmie','Mr.Mime','Scyther','Jynx','Electabuzz','Magmar','Pinsir','Tauros','Magikarp','Gyarados','Lapras','Ditto','Eevee','Vaporeon','Jolteon','Flareon','Porygon','Omanyte','Omastar','Kabuto','Kabutops','Aerodactyl','Snorlax','Articuno','Zapdos','Moltres','Dratini','Dragonair','Dragonite','Mewtwo','Mew','Chikorita','Bayleef','Meganium','Cyndaquil','Quilava','Typhlosion','Totodile','Croconaw','Feraligatr','Sentret','Furret','Hoothoot','Noctowl','Ledyba','Ledian','Spinarak','Ariados','Crobat','Chinchou','Lanturn','Pichu','Cleffa','Igglybuff','Togepi','Togetic','Natu','Xatu','Mareep','Flaaffy','Ampharos','Bellossom','Marill','Azumarill','Sudowoodo','Politoed','Hoppip','Skiploom','Jumpluff','Aipom','Sunkern','Sunflora','Yanma','Wooper','Quagsire','Espeon','Umbreon','Murkrow','Slowking','Misdreavus','Unown','Wobbuffet','Girafarig','Pineco','Forretress','Dunsparce','Gligar','Steelix','Snubbull','Granbull','Qwilfish','Scizor','Shuckle','Heracross','Sneasel','Teddiursa','Ursaring','Slugma','Magcargo','Swinub','Piloswine','Corsola','Remoraid','Octillery','Delibird','Mantine','Skarmory','Houndour','Houndoom','Kingdra','Phanpy','Donphan','Porygon2','Stantler','Smeargle','Tyrogue','Hitmontop','Smoochum','Elekid','Magby','Miltank','Blissey','Raikou','Entei','Suicune','Larvitar','Pupitar','Tyranitar','Lugia','Ho-Oh','Celebi','Treecko','Grovyle','Sceptile','Torchic','Combusken','Blaziken','Mudkip','Marshtomp','Swampert','Poochyena','Mightyena','Zigzagoon','Linoone','Wurmple','Silcoon','Beautifly','Cascoon','Dustox','Lotad','Lombre','Ludicolo','Seedot','Nuzleaf','Shiftry','Taillow','Swellow','Wingull','Pelipper','Ralts','Kirlia','Gardevoir','Surskit','Masquerain','Shroomish','Breloom','Slakoth','Vigoroth','Slaking','Nincada','Ninjask','Shedinja','Whismur','Loudred','Exploud','Makuhita','Hariyama','Azurill','Nosepass','Skitty','Delcatty','Sableye','Mawile','Aron','Lairon','Aggron','Meditite','Medicham','Electrike','Manectric','Plusle','Minun','Volbeat','Illumise','Roselia','Gulpin','Swalot','Carvanha','Sharpedo','Wailmer','Wailord','Numel','Camerupt','Torkoal','Spoink','Grumpig','Spinda','Trapinch','Vibrava','Flygon','Cacnea','Cacturne','Swablu','Altaria','Zangoose','Seviper','Lunatone','Solrock','Barboach','Whiscash','Corphish','Crawdaunt','Baltoy','Claydol','Lileep','Cradily','Anorith','Armaldo','Feebas','Milotic','Castform','Kecleon','Shuppet','Banette','Duskull','Dusclops','Tropius','Chimecho','Absol','Wynaut','Snorunt','Glalie','Spheal','Sealeo','Walrein','Clamperl','Huntail','Gorebyss','Relicanth','Luvdisc','Bagon','Shelgon','Salamence','Beldum','Metang','Metagross','Regirock','Regice','Registeel','Latias','Latios','Kyogre','Groudon','Rayquaza','Jirachi','Deoxys']
egglist = ['N1','N2','N3','N4','N5','EX']


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
            bot.sendMessage(chat_id=alert["user_id"], text="🔔 Se ha creado una incursión %s en *%s* %sa las *%s* en el grupo _%s_.\n\n_Recibes esta alerta porque has activado las alertas para ese gimnasio. Si no deseas recibir más alertas, puedes usar el comando_ `/clearalerts`" % (what_text, raid["gimnasio_text"], what_day, raid["time"], group["title"]), parse_mode=telegram.ParseMode.MARKDOWN)

def update_message(chat_id, message_id, reply_markup, bot):
    logging.debug("supportmethods:update_message: %s %s %s" % (chat_id, message_id, reply_markup))
    raid = getRaidbyMessage(chat_id, message_id)
    text = format_message(raid)
    return bot.edit_message_text(text=text, chat_id=chat_id, message_id=message_id, reply_markup=reply_markup, parse_mode=telegram.ParseMode.MARKDOWN)

def format_message(raid):
    logging.debug("supportmethods:format_message: %s" % (raid))
    creador = getCreadorRaid(raid["id"])
    gente = getRaidPeople(raid["id"])
    group = getGroup(raid["grupo_id"])

    if "edited" in raid.keys() and raid["edited"]>0:
        text_edited=" _(editada)_"
    else:
        text_edited=""
    if "endtime" in raid.keys() and raid["endtime"] != None:
        text_endtime="\n_Desaparece a las %s_" % raid["endtime"]
    else:
        text_endtime=""
    if group["locations"] == 1:
        if "gimnasio_id" in raid.keys() and raid["gimnasio_id"] != None:
            gym_emoji="🌎"
        else:
            gym_emoji="❓"
    else:
        gym_emoji=""
    what_text = format_text_pokemon(raid["pokemon"], raid["egg"])
    what_day = format_text_day(raid["timeraid"], group["timezone"])
    if creador["username"] != None:
        created_text = "\nCreada por @%s%s" % (ensure_escaped(creador["username"]), text_edited)
    else:
        created_text = ""
    text = "Incursión %s %sa las *%s* en %s*%s*%s%s\n" % (what_text, what_day, raid["time"], gym_emoji, raid["gimnasio_text"], created_text, text_endtime)
    if "cancelled" in raid.keys() and raid["cancelled"] == 1:
        text = text + "❌ *Incursión cancelada*"
    else:
        if group["disaggregated"] == 1:
            (numazules, numrojos, numamarillos, numotros, numgente) = count_people_disaggregated(gente)
            text = text + "❄️%s · 🔥%s · ⚡️%s · ❓%s · 👩‍👩‍👧‍👧%s" % (numazules, numrojos, numamarillos, numotros, numgente)
        else:
            numgente = count_people(gente)
            text = text + "%s entrenadores apuntados:" % numgente
    if (not "cancelled" in raid.keys() or raid["cancelled"] == 0) and gente != None:
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
                text = text + "\n%s%s%s @%s%s%s" % (estoy_text,team_badge,user["level"],ensure_escaped(user["username"]),lotengo_text,plus_text)
            else:
                text = text + "\n%s➖ - - @%s%s%s" % (estoy_text,ensure_escaped(user["username"]),lotengo_text,plus_text)
    return text

def format_text_pokemon(pokemon, egg):
    if pokemon != None:
        what_text = "de *%s*" % pokemon
    else:
        if egg == "EX":
            what_text="*🌟EX*"
        else:
            what_text= egg.replace("N","de *nivel ") + "*"
    return what_text

def format_text_day(timeraid, tzone):
    try:
        raid_datetime = datetime.strptime(timeraid,"%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone(tzone))
    except:
        raid_datetime = timeraid.replace(tzinfo=timezone(tzone))
    now_datetime = datetime.now(timezone(tzone))
    difftime = raid_datetime - now_datetime
    if difftime.days > 1:
        weekdays = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
        what_day = "el *%s día %s* " % (weekdays[raid_datetime.weekday()], raid_datetime.day)
    else:
        what_day = ""
    return what_day

def ensure_escaped(username):
    if username.find("_") != -1 and username.find("\\_") == -1:
        username = username.replace("_","\\_")
    return username

def end_old_raids(bot):
    logging.debug("supportmethods:end_old_raids")
    raids = endOldRaids()
    logging.debug(raids)
    for raid in raids:
        logging.debug(raid)
        r = getRaid(raid["id"])
        logging.debug("Updating message for raid ID %s" % (raid["id"]))
        try:
            updated = update_message(r["grupo_id"], r["message"], None, bot)
            logging.debug(updated)
        except:
            pass
        time.sleep(0.5)

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
    time.sleep(0.01)

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
            if warntype == "cancelar":
                text = "❌ @%s ha *cancelado* la incursión de %s a las %s en %s" % (ensure_escaped(user_username), raid["pokemon"], raid["time"], ensure_escaped(raid["gimnasio_text"]))
            elif warntype == "borrar":
                text = "🚫 @%s ha *borrado* la incursión de %s a las %s en %s" % (ensure_escaped(user_username), raid["pokemon"], raid["time"], ensure_escaped(raid["gimnasio_text"]))
            elif warntype == "cambiarhora":
                text_day = format_text_day(raid["timeraid"], group["timezone"])
                if text_day != "":
                    text_day = " " + text_day
                text = "⚠️ @%s ha cambiado la hora de la incursión de %s en %s para las *%s*%s" % (ensure_escaped(user_username), raid["pokemon"], ensure_escaped(raid["gimnasio_text"]), raid["time"], text_day)
            elif warntype == "cambiarhorafin":
                text = "⚠️ @%s ha cambiado la hora a la que se termina la incursión de %s en %s a las *%s* (¡ojo, la incursión sigue programada para la misma hora: %s!)" % (ensure_escaped(user_username), raid["pokemon"], ensure_escaped(raid["gimnasio_text"]), raid["endtime"], raid["time"])
            elif warntype == "borrarhorafin":
                text = "⚠️ @%s ha borrado la hora a la que se termina la incursión de %s en %s (¡ojo, la incursión sigue programada para la misma hora: %s!)" % (ensure_escaped(user_username), raid["pokemon"], ensure_escaped(raid["gimnasio_text"]), raid["time"])
            elif warntype == "cambiargimnasio":
                text = "⚠️ @%s ha cambiado el gimnasio de la incursión de %s para las %s a *%s*" % (ensure_escaped(user_username), raid["pokemon"], raid["time"], ensure_escaped(raid["gimnasio_text"]))
            elif warntype == "cambiarpokemon":
                text_pokemon = format_text_pokemon(raid["pokemon"], raid["egg"])
                text = "⚠️ @%s ha cambiado la incursión para las %s en %s a incursión %s" % (ensure_escaped(user_username), raid["time"], ensure_escaped(raid["gimnasio_text"]), text_pokemon)
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
        disaggregated_text = "👫 Totales desagregados"
    else:
        disaggregated_text = "👬 Total simplificado"
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
    settings_keyboard = [[InlineKeyboardButton(locations_text, callback_data='settings_locations'), InlineKeyboardButton(alertas_text, callback_data='settings_alertas')],
    [InlineKeyboardButton(gymcommand_text, callback_data='settings_gymcommand'), InlineKeyboardButton(raidcommand_text, callback_data='settings_raidcommand')],
    [InlineKeyboardButton(refloat_text, callback_data='settings_reflotar'), InlineKeyboardButton(candelete_text, callback_data='settings_borrar')], [InlineKeyboardButton(latebutton_text, callback_data='settings_botonllegotarde'), InlineKeyboardButton(gotitbuttons_text, callback_data='settings_lotengo')], [InlineKeyboardButton(disaggregated_text, callback_data='settings_desagregado')], [InlineKeyboardButton(babysitter_text, callback_data='settings_babysitter')]]
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
            text = "@%s el comando `/%s` solo funciona por privado.\n\n_(Este mensaje se borrará en unos segundos)_" % (user_username, command)
        else:
            text = "El comando `/%s` solo funciona por privado.\n\n_(Este mensaje se borrará en unos segundos)_" % command
        sent_message = bot.sendMessage(chat_id=chat_id, text=text,parse_mode=telegram.ParseMode.MARKDOWN)
        Thread(target=delete_message_timed, args=(chat_id, sent_message.message_id, 15, bot)).start()
        return False
    else:
        return True

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
    if int(hour) <= 12:
        if (int(hour) <= 6) or (int(localtime.hour) >= 15 and int(hour) <= 9):
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

def extract_time(formatted_datetime):
    logging.debug("supportmethods:extract_time %s" % formatted_datetime)
    m = re.search("([0-9]{1,2}):([0-9]{0,2}):[0-9]{0,2}", formatted_datetime, flags=re.IGNORECASE)
    if m != None:
        extracted_time = "%02d:%02d" % (int(m.group(1)), int(m.group(2)))
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
