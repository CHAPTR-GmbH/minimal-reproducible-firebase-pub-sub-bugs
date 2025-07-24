from firebase_admin import initialize_app, get_app


APP_NAME = "demo-local"
PROJECT_ID = "demo-local-development"


def initialise_admin_app():
    try:
        return get_app()
    except ValueError:
        return initialize_app(
            credential=None,
            options={
                "projectId": PROJECT_ID,
            },
        )
