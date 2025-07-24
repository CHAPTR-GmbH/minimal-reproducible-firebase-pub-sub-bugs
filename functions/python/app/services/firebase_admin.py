from firebase_admin import initialize_app

_firebase_admin_app = None


def get_admin_app():
    global _firebase_admin_app

    if _firebase_admin_app is None:
        _firebase_admin_app = initialize_app(options={"projectId": "demo-local-development"})

    return _firebase_admin_app

