import time
import logging
import telegram

from storagemethods import getRaidbyMessage, getCreadorRaid, getRaidPeople, endOldRaids, getRaid, getAlertsByPlace, getGroup
from telegram.error import (TelegramError, Unauthorized, BadRequest, TimedOut, ChatMigrated, NetworkError)

pokemonlist = ['Bulbasaur','Ivysaur','Venusaur','Charmander','Charmeleon','Charizard','Squirtle','Wartortle','Blastoise','Caterpie','Metapod','Butterfree','Weedle','Kakuna','Beedrill','Pidgey','Pidgeotto','Pidgeot','Rattata','Raticate','Spearow','Fearow','Ekans','Arbok','Pikachu','Raichu','Sandshrew','Sandslash','Nidoran♀','Nidorina','Nidoqueen','Nidoran♂','Nidorino','Nidoking','Clefairy','Clefable','Vulpix','Ninetales','Jigglypuff','Wigglytuff','Zubat','Golbat','Oddish','Gloom','Vileplume','Paras','Parasect','Venonat','Venomoth','Diglett','Dugtrio','Meowth','Persian','Psyduck','Golduck','Mankey','Primeape','Growlithe','Arcanine','Poliwag','Poliwhirl','Poliwrath','Abra','Kadabra','Alakazam','Machop','Machoke','Machamp','Bellsprout','Weepinbell','Victreebel','Tentacool','Tentacruel','Geodude','Graveler','Golem','Ponyta','Rapidash','Slowpoke','Slowbro','Magnemite','Magneton','Farfetch\'d','Doduo','Dodrio','Seel','Dewgong','Grimer','Muk','Shellder','Cloyster','Gastly','Haunter','Gengar','Onix','Drowzee','Hypno','Krabby','Kingler','Voltorb','Electrode','Exeggcute','Exeggutor','Cubone','Marowak','Hitmonlee','Hitmonchan','Lickitung','Koffing','Weezing','Rhyhorn','Rhydon','Chansey','Tangela','Kangaskhan','Horsea','Seadra','Goldeen','Seaking','Staryu','Starmie','Mr.Mime','Scyther','Jynx','Electabuzz','Magmar','Pinsir','Tauros','Magikarp','Gyarados','Lapras','Ditto','Eevee','Vaporeon','Jolteon','Flareon','Porygon','Omanyte','Omastar','Kabuto','Kabutops','Aerodactyl','Snorlax','Articuno','Zapdos','Moltres','Dratini','Dragonair','Dragonite','Mewtwo','Mew','Chikorita','Bayleef','Meganium','Cyndaquil','Quilava','Typhlosion','Totodile','Croconaw','Feraligatr','Sentret','Furret','Hoothoot','Noctowl','Ledyba','Ledian','Spinarak','Ariados','Crobat','Chinchou','Lanturn','Pichu','Cleffa','Igglybuff','Togepi','Togetic','Natu','Xatu','Mareep','Flaaffy','Ampharos','Bellossom','Marill','Azumarill','Sudowoodo','Politoed','Hoppip','Skiploom','Jumpluff','Aipom','Sunkern','Sunflora','Yanma','Wooper','Quagsire','Espeon','Umbreon','Murkrow','Slowking','Misdreavus','Unown','Wobbuffet','Girafarig','Pineco','Forretress','Dunsparce','Gligar','Steelix','Snubbull','Granbull','Qwilfish','Scizor','Shuckle','Heracross','Sneasel','Teddiursa','Ursaring','Slugma','Magcargo','Swinub','Piloswine','Corsola','Remoraid','Octillery','Delibird','Mantine','Skarmory','Houndour','Houndoom','Kingdra','Phanpy','Donphan','Porygon2','Stantler','Smeargle','Tyrogue','Hitmontop','Smoochum','Elekid','Magby','Miltank','Blissey','Raikou','Entei','Suicune','Larvitar','Pupitar','Tyranitar','Lugia','Ho-Oh','Celebi','Treecko','Grovyle','Sceptile','Torchic','Combusken','Blaziken','Mudkip','Marshtomp','Swampert','Poochyena','Mightyena','Zigzagoon','Linoone','Wurmple','Silcoon','Beautifly','Cascoon','Dustox','Lotad','Lombre','Ludicolo','Seedot','Nuzleaf','Shiftry','Taillow','Swellow','Wingull','Pelipper','Ralts','Kirlia','Gardevoir','Surskit','Masquerain','Shroomish','Breloom','Slakoth','Vigoroth','Slaking','Nincada','Ninjask','Shedinja','Whismur','Loudred','Exploud','Makuhita','Hariyama','Azurill','Nosepass','Skitty','Delcatty','Sableye','Mawile','Aron','Lairon','Aggron','Meditite','Medicham','Electrike','Manectric','Plusle','Minun','Volbeat','Illumise','Roselia','Gulpin','Swalot','Carvanha','Sharpedo','Wailmer','Wailord','Numel','Camerupt','Torkoal','Spoink','Grumpig','Spinda','Trapinch','Vibrava','Flygon','Cacnea','Cacturne','Swablu','Altaria','Zangoose','Seviper','Lunatone','Solrock','Barboach','Whiscash','Corphish','Crawdaunt','Baltoy','Claydol','Lileep','Cradily','Anorith','Armaldo','Feebas','Milotic','Castform','Kecleon','Shuppet','Banette','Duskull','Dusclops','Tropius','Chimecho','Absol','Wynaut','Snorunt','Glalie','Spheal','Sealeo','Walrein','Clamperl','Huntail','Gorebyss','Relicanth','Luvdisc','Bagon','Shelgon','Salamence','Beldum','Metang','Metagross','Regirock','Regice','Registeel','Latias','Latios','Kyogre','Groudon','Rayquaza','Jirachi','Deoxys']


def is_admin(chat_id, user_id, bot):
    is_admin = False
    for admin in bot.get_chat_administrators(chat_id):
      if user_id == admin.user.id:
        is_admin = True
    return is_admin

def extract_update_info(update):
    try:
        message = update.message
    except:
        message = update.channel_post
    text = message.text
    user_id = message.from_user.id
    chat_id = message.chat.id
    chat_type = message.chat.type
    return (chat_id, chat_type, user_id, text, message)

def delete_message_timed(chat_id, message_id, sleep_time, bot):
    time.sleep(sleep_time)
    bot.deleteMessage(chat_id=chat_id,message_id=message_id)

def count_people(gente):
    count = 0
    if gente != None:
        for user in gente:
            logging.debug(user)
            count = count + 1
            if user["plus"] != None and user["plus"] > 0:
                count = count + user["plus"]
    return count

def send_alerts(raid, bot):
    logging.debug("supportmethods:end_alerts: %s" % (raid))
    alerts = getAlertsByPlace(raid["gimnasio_id"])
    group = getGroup(raid["grupo_id"])
    for alert in alerts:
        bot.sendMessage(chat_id=alert["user_id"], text="🔔 Se ha creado una incursión de *%s* en *%s* a las *%s* en el grupo _%s_.\n\n_Recibes esta alerta porque has activado las alertas para ese gimnasio. Si no deseas recibir más alertas, puedes usar el comando_ `/clearalerts`" % (raid["pokemon"], raid["gimnasio_text"], raid["time"], group["title"]), parse_mode=telegram.ParseMode.MARKDOWN)

def update_message(chat_id, message_id, reply_markup, bot):
    logging.debug("supportmethods:update_message: %s %s %s" % (chat_id, message_id, reply_markup))
    raid = getRaidbyMessage(chat_id, message_id)
    creador = getCreadorRaid(raid["id"])
    gente = getRaidPeople(raid["id"])
    numgente = count_people(gente)
    if raid["edited"]>0:
        text_edited=" _(editada)_"
    else:
        text_edited=""
    if raid["endtime"] != None:
        text_endtime="\n_Se va a las %s_" % raid["endtime"]
    else:
        text_endtime=""
    text = "Incursión de *%s* a las *%s* en *%s*\nCreada por @%s%s%s\n" % (raid["pokemon"], raid["time"], raid["gimnasio_text"], ensure_escaped(creador["username"]), text_edited, text_endtime)
    if raid["cancelled"] == 1:
        text = text + "❌ *Incursión cancelada*"
    else:
        text = text + "Entrenadores apuntados (%s):" % numgente
    if raid["cancelled"] == 0 and gente != None:
        for user in gente:
            if user["plus"] != None and user["plus"]>0:
                plus_text = " +%i" % user["plus"]
            else:
                plus_text = ""
            if user["estoy"] != None and user["estoy"]>0:
                estoy_text = "✅ "
            else:
                estoy_text = "▪️ "
            if user["level"] != None and user["team"] != None:
                if user["team"] != None:
                    if user["team"]=="Rojo":
                        team_badge = "🔥"
                    elif user["team"]=="Amarillo":
                        team_badge = "⚡️"
                    else:
                        team_badge = "❄️"
                text = text + "\n%s%s%s @%s%s" % (estoy_text,team_badge,user["level"],ensure_escaped(user["username"]),plus_text)
            else:
                text = text + "\n%s➖ - - @%s%s" % (estoy_text,ensure_escaped(user["username"]),plus_text)

    return bot.edit_message_text(text=text, chat_id=raid["grupo_id"], message_id=raid["message"], reply_markup=reply_markup, parse_mode=telegram.ParseMode.MARKDOWN)

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

def error_callback(bot, update, error):
    try:
        raise error
    except Unauthorized:
        logging.debug("TELEGRAM ERROR: Unauthorized - %s" % update)
    except BadRequest:
        logging.debug("TELEGRAM ERROR: Bad Request - %s" % update)
    except TimedOut:
        logging.debug("TELEGRAM ERROR: Slow connection problem - %s" % update)
    except NetworkError:
        logging.debug("TELEGRAM ERROR: Other connection problems - %s" % update)
    except ChatMigrated as e:
        logging.debug("TELEGRAM ERROR: Chat ID migrated?! - %s" % update)
    except TelegramError:
        logging.debug("TELEGRAM ERROR: Other error - %s" % update)
    except:
        logging.debug("TELEGRAM ERROR: Unknown - %s" % update)

def warn_people(warntype, raid, user_username, chat_id, bot):
    people = getRaidPeople(raid["id"])
    warned = []
    notwarned = []
    for p in people:
        if p["username"] == user_username:
            continue
        try:
            if warntype == "cancelar":
                text = "❌ @%s ha *cancelado* la incursión de %s a las %s en %s" % (ensure_escaped(user_username), raid["pokemon"], raid["time"], raid["gimnasio_text"])
            elif warntype == "borrar":
                text = "🚫 @%s ha *borrado* la incursión de %s a las %s en %s" % (ensure_escaped(user_username), raid["pokemon"], raid["time"], raid["gimnasio_text"])
            elif warntype == "cambiarhora":
                text = "⚠️ @%s ha cambiado la hora de la incursión de %s en %s para las *%s*" % (ensure_escaped(user_username), raid["pokemon"], raid["gimnasio_text"], raid["time"])
            elif warntype == "cambiarhorafin":
                text = "⚠️ @%s ha cambiado la hora a la que se termina la incursión de %s en %s a las *%s* (¡ojo, la incursión sigue programada para la misma hora: %s!)" % (ensure_escaped(user_username), raid["pokemon"], raid["gimnasio_text"], raid["endtime"], raid["time"])
            elif warntype == "borrarhorafin":
                text = "⚠️ @%s ha borrado la hora a la que se termina la incursión de %s en %s (¡ojo, la incursión sigue programada para la misma hora: %s!)" % (ensure_escaped(user_username), raid["pokemon"], raid["gimnasio_text"], raid["time"])
            elif warntype == "cambiargimnasio":
                text = "⚠️ @%s ha cambiado el gimnasio de la incursión de %s para las %s a *%s*" % (ensure_escaped(user_username), raid["pokemon"], raid["time"], raid["gimnasio_text"])
            elif warntype == "cambiarpokemon":
                text = "⚠️ @%s ha cambiado el Pokémon de la incursión para las %s en %s a *%s*" % (ensure_escaped(user_username), raid["time"], raid["gimnasio_text"], raid["pokemon"])
            bot.sendMessage(chat_id=p["id"], text=text, parse_mode=telegram.ParseMode.MARKDOWN)
            warned.append(p["username"])
        except:
            notwarned.append(p["username"])
    if len(warned)>0:
        bot.sendMessage(chat_id=chat_id, text="He avisado por privado a: @%s" % ensure_escaped(", @".join(warned)), parse_mode=telegram.ParseMode.MARKDOWN)
    if len(notwarned)>0:
        bot.sendMessage(chat_id=chat_id, text="No he podido avisar a: @%s" % ensure_escaped(", @".join(notwarned)), parse_mode=telegram.ParseMode.MARKDOWN)
