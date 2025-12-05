from src.application.use_cases.auth_service import AuthService

# Fake User
class FakeUser:
    def __init__(self, email, pass_ok=True):
        self.email = email
        self.pass_ok = pass_ok

    def check_password(self, password):
        return self.pass_ok


# Fake Repo que simula UserRepository
class FakeRepo:
    def __init__(self, users_dict):
        self.users = users_dict

    def get_active_by_email(self, email):
        return self.users.get(email)


# -------------------------
# TESTS
# -------------------------

def test_authenticate_ok():
    user = FakeUser("a@a.com", pass_ok=True)
    repo = FakeRepo({"a@a.com": user})
    svc = AuthService(repo)

    result = svc.authenticate("a@a.com", "1234")

    assert result is user


def test_authenticate_fail_wrong_pass():
    user = FakeUser("a@a.com", pass_ok=False)
    repo = FakeRepo({"a@a.com": user})
    svc = AuthService(repo)

    result = svc.authenticate("a@a.com", "1234")

    assert result is None


def test_authenticate_fail_no_user():
    repo = FakeRepo({})
    svc = AuthService(repo)

    result = svc.authenticate("x@x.com", "1234")

    assert result is None
