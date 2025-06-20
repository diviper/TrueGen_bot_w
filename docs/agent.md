# Информация для помощника

## Назначение бота

Ты — бот, который помогает монтажникам автоматизировать рутину с актами выполненных работ. Ты умеешь:
- Принимать текст с указанием даты, объекта и работ
- Показывать предварительный итог
- Спрашивать подтверждение
- Генерировать аккуратный акт в .docx и присылать его в чат

## Формат ввода

Пользователь отправляет сообщение в формате:
```
#АКТ 10.06.2025 | Объект: Название объекта
наименование1 количество1 ед.изм. × цена1₽
наименование2 количество2 ед.изм. × цена2₽
```

Пример:
```
#АКТ 10.06.2025 | Объект: Офис на Ленина 42
подрозетники 30×40₽
кабель 45 м × 25₽
```

## Обработка ошибок

При обработке ввода возможны следующие ошибки:
1. Неверный формат даты
2. Отсутствует объект
3. Неправильный формат позиций
4. Некорректные числовые значения

В случае ошибки нужно:
1. Записать её в лог
2. Отправить пользователю понятное сообщение об ошибке
3. Предложить правильный формат ввода

## Логика работы

1. При старте бот показывает приветственное сообщение и кнопки
2. При получении текста акта:
   - Парсим данные
   - Показываем предпросмотр
   - Запрашиваем подтверждение
3. При подтверждении:
   - Генерируем документ
   - Отправляем его пользователю
   - Сбрасываем состояние

## Дополнительно

- Все действия логируются
- Документы сохраняются в папку `out/`
- Логи пишутся в `logs/bot.log`
- Конфигурация в `.env`

## Планы по развитию

1. v1.1 - Генерация PDF
2. v1.2 - Автосохранение в Google Drive
3. v1.3 - Голосовой ввод (через Whisper)
4. v1.4 - GPT-декодер для каракулей
5. v2.0 - UI + CRM-связь, работа с 1С