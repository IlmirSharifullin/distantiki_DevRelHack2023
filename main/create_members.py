import pandas as pd

from devrelhack.settings import BASE_DIR, db


class WrongFileExtensionError(Exception):
    pass


def load_csv(filename: str):
    return pd.read_csv(BASE_DIR / f'data/members/{filename}', delimiter=';')


def load_xlsx(filename: str):
    return pd.read_excel(BASE_DIR / f'data/members/{filename}')


def are_equal(lst):
    for i in range(len(lst) - 1):
        if lst[i] != lst[i + 1]:
            return False
    return True


def create_members(filename: str):
    members = []
    db_members = db.get_collection('members')
    attributes: dict = db.get_collection('attributes').find_one().get('attributes')
    if filename.endswith('.csv'):
        df = load_csv(filename)
    elif filename.endswith('.xlsx') or filename.endswith('.xls'):
        df = load_xlsx(filename)
    else:
        return WrongFileExtensionError
    keys = df.keys()
    for key in keys:
        if key not in attributes.keys():
            print('Неправильный атрибут')
            return

    for line in df.values:
        changing_documents = []
        found_key = None

        obj = {}
        for i in range(len(keys)):
            key, value = keys[i], line[i]

            # Смотрим, есть ли совпадения среди уникальных атрибутов
            if attributes.get(key).get('unique') == 1:
                found = db_members.find_one(filter={key: value})
                if found:
                    # Если есть => сохраняем эти объекты
                    found_key = key
                    changing_documents.append(found)
            obj[key] = value
        print(obj)
        if changing_documents and are_equal(changing_documents) and found_key is not None:
            # Изменяется один объект => дополняем его новыми данными
            changing_document = changing_documents[0]
            print('changed')
            db_members.update_one(filter={found_key: changing_document[found_key]}, update={'$set': obj})
            members.append(changing_document.get('_id'))
        elif changing_documents and not are_equal(changing_documents):
            # Изменяются разные объекты => не меняем.
            pass
        else:
            # Не изменяется ни один объект => создаем новый
            member = db_members.insert_one(obj).inserted_id
            members.append(member)
    return members


def create_member(data: dict):
    attributes = db.get_collection('attributes').find_one().get('attributes')
    db_members = db.get_collection('members')
    changing_documents = []
    obj = {}
    found_key = None
    for key, value in data.items():
        if attributes.get(key).get('unique') == 1:
            found = db_members.find_one(filter={key: value})
            if found:
                # Если есть => сохраняем эти объекты
                found_key = key
                changing_documents.append(found)
        obj[key] = value
    if changing_documents and are_equal(changing_documents) and found_key is not None:
        # Изменяется один объект => дополняем его новыми данными
        changing_document = changing_documents[0]
        print('changed')
        db_members.update_one(filter={found_key: changing_document[found_key]}, update={'$set': obj})
        return changing_document.get('_id')
    elif changing_documents and not are_equal(changing_documents):
        # Изменяются разные объекты => не меняем.
        pass
    else:
        # Не изменяется ни один объект => создаем новый
        member = db_members.insert_one(obj).inserted_id
        return member


create_members('test.xlsx')
