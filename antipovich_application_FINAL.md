# Виталий Антипович - "База таможенных деклараций"

## VK: https://vk.com/vitaly_antipovich

## [ НАЗВАНИЕ ПРОЕКТА ]
База таможенных деклараций

## [ ПРОБЛЕМНОЕ ПОЛЕ ] 
Грузовая таможенная декларация - основной документ, оформляемый на импортируемый товар (т.е. привезенный из других стран). В декларации указывается информация о товаре, поставщике, заводе производителя, стране производителя, стоимость и многое другое. Учёт ГТД важен как с правовой точки зрения, так и для бухгалтерской и управленческой отчетности. В компаниях при отсутствии соответствующих инструментов (программных комплексов) бухгалтеры тратят много времени на проверку, заведение, фиксирование необходимых данных из деклараций в учетных системах компании. Поэтому компаниям важно наличие автоматизированных инструментов для сокращения монотонного человеческого труда, а также для повышения точности отчётов и уменьшения количества ошибок.

## [ ЗАКАЗЧИК ]
ЗАО "ДАИЧИ" (дистрибьютор климатического оборудования)

## [ АППАРАТНЫЕ ТРЕБОВАНИЯ ]  
- версия Google Chrome от 96
- оперативная память от 2 Гбайт

## [ ФУНКЦИОНАЛЬНЫЕ ТРЕБОВАНИЯ ]
- Парсинг xml файлов ГТД
- Накопление и сохранения данных из электронных документов ГТД
- Построение статистических/аналитических отчётов (например, в разрезе данных по поставщикам, странам, ценам, таможенным кодам и т.д.)
- Подготовка данных для формирования ежегодного отчета по экологическому сбору
- Подготовка данных для экспорта в системы класса WMS
- Подготовка данных для экспорта в 1С ERP
- Ролевая модель доступа к функционалу системы

## [ ПОХОЖИЕ / АНАЛОГИЧНЫЕ ПРОДУКТЫ ]
 - Альта ГТД: Это **платный** программный комплекс для таможенного брокера (посредник между государством и компанией, которой требуется услуги таможенного оформления). Имеет функционал для отчётов, справочники. Отчетность по утилизации (в том числе и данные для отчета по эк. сбору) - в приложении к софту за отдельную **плату**. Нет экспорта xml в базу данных или в другие форматы. Этот продукт скорее для ***составления*** гтд, а не обработки.
 - Внешние модули для "1С Бухгалтерия" - открытый исходный код 1С позволяет при знании платформы сделать систему, в которой будет данный функционал, но это вероятно потребует привлечение дорогого специалиста 1С или же долгого изучения платформы (в том числе изучение ЯП 1С) Поскольку продукт 1С сам по себе периодически обновляется, может возникнуть конфликт версий.
 - продукция СТМ ВЭД (Контроль ГТД) - опять же, **платное** ПО для формирования и проверки документов перед подачей в таможенные органы. Для автоматизации формирования классификаторов, ведения расходов, получения справочников нужно приобрести другой продукт - "ВЭД Декларант".

Задача могла бы быть решена расширением функционала используемого заказчиком продукта на базе платформы 1С, но по требованию заказчика необходимо "обкатать" процесс на внешней системе с потенциальной возможностью переноса устоявшегося процесса в основную учетную систему компании. В качестве внешней системы принято решение использовать данное веб-приложение.

## [ ИНСТРУМЕНТЫ РАЗРАБОТКИ ]
- html, css, javascript
- Python 3.10
- Django 4.1
- MySQL 8.0.27

## [ ЭТАПЫ РАЗРАБОТКИ ]
1. Изучение литературы по теме
2. Разработка пользовательских сценариев
3. Создание каркаса функционала, заявленного в заявке
   1. Реализация функции добавления ГТД
   2. Создание страниц для выведения справочников
   3. Создание страниц для выведения документов ГТД
4. Добавление оставшейся части базового функционала
   1. Страницы для редактирования документов
   2. Страница формирования данных для отчета по экологическому сбору
   3. Страницы построения статистических отчетов
   4. Функция подготовки данных для WMS
   5. Функция подготовки данных для ERP
   6. Внедрение ролевой системы
5. Оптимизация функционала и приведение к более работоспособному виду
6. Тестирование, отладка
7. Передача в опытно-промышленную эксплуатацию

## [ ВОЗМОЖНЫЕ РИСКИ ]
- Расхождение изначальных ожиданий с полученным продуктом из-за нечёткого ТЗ
