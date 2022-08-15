## Телеграм-бот для отправки сообщений другим пользователям
Для запуска бота требуется передать токен доступа к боту в переменную окружения TG_TOKEN:

export TG_TOKEN=1234567:A_SECRET_TG_TOKEN
python3 main.py

Функционал бота - отправка сообщений другим пользователям с задаваемой при отправке задержкой. Возможность создать сообщения будет предложена пользователю по команде /start или по отправке произвольного сообщения, если в данный момент он не создает другое сообщение. Далее он может выбрать получателя, задать сообщение и произвольную задержку в секундах. По прошествию задержки с момента окончания формирования сообщения получатель получит его, а также имя отправителя.