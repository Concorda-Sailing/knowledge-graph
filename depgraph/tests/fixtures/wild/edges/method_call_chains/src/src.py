class UserQuery:
    def filter(self):
        return self

    def first(self):
        return None


class UserSet:
    def get(self) -> UserQuery:
        return UserQuery()


class Client:
    def __init__(self):
        self.users = UserSet()


def run(client: Client):
    # chained method calls: client.users.get().filter().first()
    result = client.users.get().filter().first()
    return result
