from jsonrpc import jsonrpc_method
from models import AvailableUsers

@jsonrpc_method('sayHello')
def whats_the_time(request, name='Lester'):
    return str(AvailableUsers.objects.all())
    #return "Hello %s" % name

@jsonrpc_method('who')
def who(request):
    available = AvailableUsers.objects.all()
    if len(available) < 1:
        return "niemand da"
    else:
        return ", ".join([str(a) for a in available])

@jsonrpc_method('login')
def login(request, user):
    AvailableUsers(username=user).save()
    return "aye"
   
@jsonrpc_method('logout')
def logout(request, user):
    users = AvailableUsers.objects.filter(username=user)
    for u in users:
        AvailableUsers.delete(u)
    return "aye"
