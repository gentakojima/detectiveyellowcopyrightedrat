import telegram
import logging
from supportmethods import delete_message, edit_check_private, extract_update_info
from storagemethods import getAlerts, getPlace, getGroup, isBanned, delAlert, addAlert, clearAlerts, getPlacesByLocation, getGroupsByUser

def alerts(bot, update, args=None):
    logging.debug("detectivepikachubot:alerts: %s %s %s" % (bot, update, args))
    (chat_id, chat_type, user_id, text, message) = extract_update_info(update)
    user_username = message.from_user.username

    if user_id!=None and isBanned(user_id):
        return

    if edit_check_private(chat_id, chat_type, user_username, "alerts", bot) == False:
        delete_message(chat_id, message.message_id, bot)
        return

    alerts=getAlerts(user_id)
    if len(alerts)==0:
        text_message = "🔔 No tienes ninguna alerta de incursión definida."
    else:
        text_message = "🔔 Tienes definidas %s alertas para los siguientes gimnasios:\n" % len(alerts)
        for alert in alerts:
            place = getPlace(alert["place_id"])
            group = getGroup(place["group_id"])
            text_message = text_message + "\n✅ `%s` %s - Grupo %s" % (place["id"], place["desc"], group["title"])
        text_message = text_message + "\n\nPara borrar una alerta, envíame `/delalert` seguido del identificador numérico, o `/clearalerts` para borrarlas todas."
    text_message = text_message + "\n\nPara añadir alertas de incursión nuevas, *envíame una ubicación* con gimnasios cercanos (_usando la función de Telegram de enviar ubicaciones_) y te explico."
    bot.send_message(chat_id=user_id, text=text_message, parse_mode=telegram.ParseMode.MARKDOWN)

def addalert(bot, update, args=None):
    logging.debug("detectivepikachubot:addalert: %s %s %s" % (bot, update, args))
    (chat_id, chat_type, user_id, text, message) = extract_update_info(update)
    user_username = message.from_user.username

    if user_id!=None and isBanned(user_id):
        return

    if edit_check_private(chat_id, chat_type, user_username, "addalert", bot) == False:
        delete_message(chat_id, message.message_id, bot)
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
    user_username = message.from_user.username

    if user_id!=None and isBanned(user_id):
        return

    if edit_check_private(chat_id, chat_type, user_username, "delalert", bot) == False:
        delete_message(chat_id, message.message_id, bot)
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
    user_username = message.from_user.username

    if user_id!=None and isBanned(user_id):
        return

    if edit_check_private(chat_id, chat_type, user_username, "clearalerts", bot) == False:
        delete_message(chat_id, message.message_id, bot)
        return

    if clearAlerts(user_id):
        bot.sendMessage(chat_id=chat_id, text="👌 Se han eliminado las alertas de todos los gimnasios.\n\nA partir de ahora, ya no recibirás mensajes privados cada vez que alguien cree una incursión.", parse_mode=telegram.ParseMode.MARKDOWN)
    else:
        bot.sendMessage(chat_id=chat_id, text="❌ No se ha eliminado ninguna alerta.", parse_mode=telegram.ParseMode.MARKDOWN)

def processLocation(bot, update):
    logging.debug("detectivepikachubot:processLocation: %s %s" % (bot, update))
    (chat_id, chat_type, user_id, text, message) = extract_update_info(update)
    location = message.location

    if user_id!=None and isBanned(user_id):
        return

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
            bot.sendMessage(chat_id=chat_id, text="❌ No se han encontrado gimnasios cerca de esta zona en grupos en los que hayas participado en una incursión recientemente. Ten en cuenta que el radio de búsqueda es de aproximadamente 180 metros.", parse_mode=telegram.ParseMode.MARKDOWN)
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
