def user_role(request):
    if not request.user.is_authenticated:
        return {'user_role': None}
    perfil = getattr(request.user, 'perfil', None)
    if perfil is None:
        return {'user_role': None}
    return {'user_role': perfil.rol}
