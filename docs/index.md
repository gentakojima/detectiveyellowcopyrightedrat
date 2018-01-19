# Detective Pikachu #

Detective Pikachu es un bot de Telegram especializado en crear listados de participantes en incursiones de Pokémon GO.

Puedes pedir ayuda en el grupo [@detectivepikachuayuda](https://t.me/detectivepikachuayuda) y estar informado de las novedades en el canal [@detectivepikachunews](https://t.me/detectivepikachunews).

1. [Ayuda para entrenadores](#ayuda-para-entrenadores)
  1. [Registrarse en el bot](#registrarse-en-el-bot)
  2. [Crear una incursión](#crear-una-incursión)
  3. [Editar, cancelar, borrar y reflotar una incursión](#editar-cancelar-borrar-y-borrar-una-incursión)
  4. [Apuntarse a una incursión](#apuntarse-a-una-incursión)
  5. [Alertas de incursiones](#alertas-de-incursiones)
  6. [Más ayuda](#más-ayuda)
2. [Ayuda para administradores](#ayuda-para-administradores)


## Ayuda para entrenadores ##

### Registrarse en el bot ###

El registro es obligatorio en algunos grupos (a discreción de los administradores), pero sea obligatorio o no, te permite **mostrar tu nombre de entrenador, equipo y nivel** en las incursiones y **participar en los rankings**.

Para registrarte tienes dos opciones:

1. En un privado con [@detectivepikachubot](https://t.me/detectivepikachubot), escribe el comando `/register` y comenzarás el proceso de registro y validación. El proceso es automatizado y te pedirá que hagas una captura de pantalla del juego con unas condiciones.

2. Si estás registrado y validado con [@profesoroak_bot](https://t.me/profesoroak_bot), puedes sencillamente preguntarle `quién soy?` y reenviar la respuesta a [@detectivepikachubot](https://t.me/detectivepikachubot).

### Crear una incursión ###

La sintaxis para crear una incursión nueva es muy sencilla:

    /raid pokemon hora gimnasio

Es importante seguir este mismo orden, sino lo más seguro es que el bot no te entienda. También se puede añadir una hora a la que desaparece el Pokémon.

    /raid pokemon hora gimnasio horafin

Algunos ejemplos:

    /raid Raikou 14:30 Alameda
    /raid Entei 3:30 Plaza de la verdura
    /raid Metapod 12 Plaza Mayor 12:15

En lugar de especificar un Pokémon, se puede especificar un huevo, por ejemplo, para un huevo de nivel 4 se pondría *N4*:

    /raid N4 13:00 Alameda

Para crear incursiones EX se debe utilizar la palabra *EX* y especificar el día de la incursión con el siguiente formato:

    /raid EX dia/hora gimnasio

Por ejemplo, para una incursión EX el día 12 a las 15:30 en el gimnasio Crucero:

    /raid EX 12/15:30 Crucero

Para poder crear una incursión es **necesario tener un alias** definido en Telegram y. Además, algunos grupos exigen **estar validado** en el bot. Si no puedes crear una incursión por alguno de estos motivos, el bot te informará.

### Editar, cancelar, borrar y reflotar una incursión ###

Se pueden editar y añadir todos los detalles de la incursión después de crearla: cambiar la hora, el gimnasio, el Pokémon (o el huevo) y la hora a la que desaparece.

Para editar o añadir cualquiera de estos detalles, el creador de la incursión puede contestar al mensaje de la incursión con uno de estos comandos:

    /hora 12:00
    /pokemon Wartortle
    /gimnasio Plaza de Abastos
    /horafin 12:30

Una incursión también se puede cancelar contestando con el comando `/cancelar`, ser borrada con el comando `/borrar` y ser reflotada con el comando `/reflotar`.

Los participantes recibirán **avisos por privado** cuando se edite, cancele o borre una incursión.

Ten en cuenta que los comandos `/borrar` y `/reflotar` por defecto solo están activados para los administradores de los grupos y solo algunos grupos permiten que los usen los propios creadores de las incursiones.

### Apuntarse a una incursión ###

Una vez creada la incursión, puedes apuntarse pulsando en el botón **Voy**.

Si vas con acompañantes, puedes pulsar el botón **+1** por cada acompañante adicional. Si te has pasado, pulsa en **Voy** para poner esta cuenta a cero y volver a empezar. Ten en cuenta que los administradores de los grupos pueden limitar el número de acompañantes permitidos o deshabilitar completamente esta opción.

Cuando estés en el lugar de la incursión, puedes pulsar el botón **Estoy ahí** para indicarlo.

Si te has apuntado pero no vas a ir, pulsa en **No voy**. Si han pasado más de cinco minutos desde que te apuntaste, permanecerás en la lista con una ❌ para que la gente sepa que te has desapuntado.

Una vez llegue la hora de la incursión y hasta tres horas más tarde, puedes informar si has capturado al Pokémon de la incursión pulsando en **Lo tengo** o **Ha escapado**. Ten en cuenta que estos botones no están activados por defecto y los administradores de los grupos pueden decidir no habilitarlos.

Para poder apuntarse a una incursión es **necesario tener un alias** definido en Telegram. Además, algunos grupos exigen **estar validado** en el bot. Si no puedes apuntarte por alguno de estos motivos, el bot te informará.

### Alertas de incursiones ###

Cuando se creen incursiones en determinados gimnasios se pueden recibir alertas por mensaje privado. Para configurarlas, utiliza el comando `/alerts` y sigue las instrucciones.

Ten en cuenta que antes de configurar las alertas tienes que haber participado en alguna incursión y el grupo tiene que tener configuradas las ubicaciones de los gimnasios.

### Más ayuda ###

Si necesitas ayuda que no se encuentre en este manual, puedes preguntar en [@detectivepikachuayuda](https://t.me/detectivepikachuayuda). Si estás administrando un grupo o un canal, mira más abajo para la ayuda para ver administradores.

## Ayuda para administradores ##

Ver http://telegra.ph/Detective-Pikachu---Ayuda-para-administradores-de-grupos-11-09
