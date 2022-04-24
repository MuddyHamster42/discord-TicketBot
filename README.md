# discord-TicketBot

## Создание бота:
Если вы не знаете что такое токен и откуда его брать - вероятно сначала вам нужно создать бота тут: https://discord.com/developers/

Сразу после создания бота копируем его токен. Находится он во кладке **Bot** сразу под ником бота.

Следующим шагом нужно включть **Privileged Gateway Intents**.
Для этого заходим во вкладку **Bot** и ставим ползунки в такое же положение как на скриншоте:

![1](https://user-images.githubusercontent.com/87133177/164997921-7ca8e24c-3f4a-4083-9314-4a1f53a032c9.jpg)

Далее нужно пригласить бота к себе на сервер.
Переходим во влкдаку **OAuth2** > **URL Generator**.

В поле "SCOPES" ставит галочку на **bot**.
В поле "BOT PERMISSIONS" либо выбираем **Administrator**, либо:

![2](https://user-images.githubusercontent.com/87133177/164997944-415134f4-e1b2-472a-b3ef-7eaf0f87ac16.jpg)

В самом низу сгенерируется ссылка для приглашения бота на свой сервер.

## Настройка бота:

В файл **config.py** вставляем скопированный ранее токен. По желанию все там-же можно поменять цветовую палитру и префикс.

В файле **localization.py** можно перевести фразы на любой язык.

## Запуск бота

Запустите файл **bot.py**. В среднем загрузка длится 5-6 секунд.
Если ошибок не возникло - прописывайте команду **%help_adm** чтобы подготовить бота к работе.

Примечание: Команда %**help_adm**, как и все команды которые она выдает - работают только если у вас права администратора.
Для обычных пользователей есть команда **%help**.

![3](https://user-images.githubusercontent.com/87133177/164998400-fbb47664-73d0-4c17-9205-b286938510e6.jpg)

## С чего начать?

Начать можно с настройки текста первого сообщения в кнале тикета. Это сообщение будет закреплено, и через него участники тикета смогут управлять его состоянием.

Для непосредственно начала работы - нужно создать сообщение с кнопкой создания тикетов.
Пишем сначала текст этого сообщения, а потом команду **%ticket_button** [#channel].
В канале #channel появится сообщение с кнопкой. Обратите внимание, что все каналы-тикеты будут создаваться в той-же категории где находится кнопка их создания.

Бот готов к работе.

P.s. Закрывать тикет могут все его участники, а открывать заново или удалять - только администраторы.