from . import authBp
from .controllers import register, login, logout, get_me

@authBp.route('/register', methods=['POST'])
def route_register():
    return register()

@authBp.route('/login', methods=['POST'])
def route_login():
    return login()

@authBp.route('/logout', methods=['POST'])
def route_logout():
    return logout()

@authBp.route('/me', methods=['GET'])
def route_me():
    return get_me()