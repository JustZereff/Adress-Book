import json
from collections import UserDict
from datetime import datetime

class Field:
    def __init__(self, value):
        self._value = value

    def __str__(self):
        return str(self._value)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        self._value = new_value


class Name(Field):
    pass


class Phone(Field):
    def __init__(self, value):
        super().__init__(value)
        self.validate_phone()

    # Перевірка на валідність номера
    def validate_phone(self):
        if not (isinstance(self._value, str) and all(c.isdigit() for c in self._value) and len(self._value) == 10):
            raise ValueError("Incorrect recording format")


class Birthday:
    def __init__(self, date):
        # Перевірка на формат прийнятої дати
        try:
            # Приймає строку та перетворює її у datetime
            self.birthday_date = datetime.strptime(date, "%d.%m.%Y")
        except ValueError as e:
            raise ValueError("Incorrect birthday format. The expected format is dd.mm.yyyy.") from e

    def __call__(self):
        return self.birthday_date


class Record:
    def __init__(self, name, birthday=None):
        self.name = Name(name)
        self.phones = []
        self.birthday = Birthday(birthday) if birthday else None

    # Додавання номеру телефону
    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    # Зміна номеру телефону
    def edit_phone(self, old_phone, new_phone):
        for phone in self.phones:
            if phone.value == old_phone:
                phone.value = new_phone
                break
            else:
                raise ValueError
            
        # Обновление значения в словаре AddressBook.data
        address_book = AddressBook()
        address_book_record = address_book.find(self.name.value)
        if address_book_record:
            address_book_record.phones = self.phones

    # Пошук телефону
    def find_phone(self, phone):
        for record_phone in self.phones:
            if str(record_phone) == phone:
                return record_phone
        return None

    # Видалення телефону
    def remove_phone(self, phone):
        for phones in self.phones:
            if str(phones) == phone:
                self.phones.remove(phones)

    # Функция яка підраховує скільки залишилось до дня народження
    def days_to_birthday(self):
        if not self.birthday:
            return None
        current_date = datetime.now()
        next_birthday = self.birthday().replace(year=current_date.year)
        # Перевірка - чи було у цьому році ДР
        if current_date > next_birthday:
            next_birthday = next_birthday.replace(year=current_date.year + 1)
        days_until_birthday = (next_birthday - current_date).days
        return days_until_birthday

    def __str__(self):
        return f"Contact name: {self.name.value}, phones: {'; '.join(p.value for p in self.phones)}"


class AddressBook(UserDict):
    def __init__(self, records_per_page=5):
        super().__init__()
        self.records_per_page = records_per_page

    def __iter__(self):
        self._iter_index = 0
        return self

    # Генератор сторінок
    def __next__(self):
        start = self._iter_index
        end = start + self.records_per_page
        if start >= len(self.data):
            raise StopIteration
        records_slice = list(self.data.values())[start:end]
        self._iter_index = end
        return records_slice

    # Додавання до адресної книги
    def add_record(self, record):
        self.data[record.name.value] = record

    # Пошук контакту
    def find(self, name):
        return self.data.get(name, None)

    # Видалення контакту
    def delete(self, name):
        if name in self.data:
            del self.data[name]
    
    # Пошук за номером
    def find_by_phone(self, query):
        found_records = []
        for record in self.data.values():
            for phone in record.phones:
                if query.lower() in str(phone).lower():
                    found_records.append(record)
                    break  # Додано, щоб уникнути дублікатів записів
        return found_records

    # Пошук по імені
    def find_by_name(self, query):
        found_records = []
        for record in self.data.values():
            if query.lower() in record.name.value.lower():
                found_records.append(record)
        return found_records

    # Утворення Бєкапу
    def start_backup(self, filename):
        with open(filename, 'w') as fn:
            json.dump([{'name': record.name.value,
                        'phones': [phone.value for phone in record.phones],
                        'birthday': record.birthday().strftime("%d.%m.%Y") if record.birthday else None} for record in self.data.values()], fn)
            
    # Відкриття бєкапу
    @classmethod
    def open_backup(cls, filename):
        address_book = cls()
        with open(filename, 'r') as fn:
            data = json.load(fn)
            for record_data in data:
                record = Record(record_data['name'])
                record.phones = [Phone(phone) for phone in record_data.get('phones', [])]
                record.birthday = Birthday(record_data.get('birthday')) if record_data.get('birthday') else None
                address_book.add_record(record)
        return address_book
    
    def __str__(self):
        return f"Name: {self.name}, Phones: {', '.join(str(phone) for phone in self.phones)}, Birthday: {self.birthday() if self.birthday else 'None'}"


if __name__ == '__main__':
    # Створення нової адресної книги
    book = AddressBook()

    # Створення запису для John з днем народження
    john_record = Record("John", "01.01.1990")
    john_record.add_phone("1234567890")
    john_record.add_phone("5555555555")

    # Додавання запису John до адресної книги
    book.add_record(john_record)

    # Створення та додавання нового запису для Jane
    jane_record = Record("Jane")
    jane_record.add_phone("9876543210")
    book.add_record(jane_record)

    # Виведення всіх записів у книзі
    for name, record in book.data.items():
        print(record)

    # Знаходження та редагування телефону для John
    john = book.find("John")
    john.edit_phone("1234567890", "1112223333")

    print(john)  # Виведення: Contact name: John, phones: 1112223333; 5555555555

    # Пошук конкретного телефону у записі John
    found_phone = john.find_phone("5555555555")
    print(f"{john.name}: {found_phone}")  # Виведення: 5555555555

    book_records = AddressBook(records_per_page=5)

    for page_number, page_records in enumerate(book_records, start=1):
        print(f"=== Сторінка {page_number} ===")
        for record in page_records:
            print(record)

    # Видалення запису Jane
    book.delete("Jane")

    artem = Record("Artem", "24.12.1998")
    artem.add_phone("0733044444")
    book.add_record(artem)

    artem = book.find("Artem")
    print(artem)
    print(f"До дня народження залишилося {artem.days_to_birthday()} днів")

    file_name = 'back_up.json'

    # Створюєм Бєкап
    book.start_backup(file_name)

    # Відкриваем Бєкап
    backup_book = book.open_backup(file_name)
    for name, record in backup_book.data.items():
        print(record)

    # Пошук за номером
    found_by_phone = book.find_by_phone("5555555555")
    print("Знайдені записи за номером телефону:", len(found_by_phone))
    for record in found_by_phone:
        print(record)

    # Пошук за ім'ям
    found_by_name = book.find_by_name("Jo")
    print("Знайдені записи за ім'ям:", len(found_by_name))
    for record in found_by_name:
        print(record)
        
    # Пошук за номером телефону або ім'ям
    query = input("Введіть рядок для пошуку: ")
    found_by_phone = book.find_by_phone(query)
    found_by_name = book.find_by_name(query)

    if found_by_phone or found_by_name:
        print("Знайдені записи:")
        for record in found_by_phone + found_by_name:
            print(record)
    else:
        print('Нічого не знайдено.')