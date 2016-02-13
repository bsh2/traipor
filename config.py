import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    # TODO change for production deployment
    SECRET_KEY = '5192620744613252662622094929424228601290'

    SSL_DISABLE = False

    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_RECORD_QUERIES = True

    BROKER_URL = 'amqp://'
    CELERY_RESULT_BACKEND = 'amqp://'
    CELERYD_TASK_TIME_LIMIT = 60 * 60 * 24

    # TODO change for production deployment
    MAIL_SERVER = 'localhost'
    MAIL_PORT = 25
    MAIL_USE_TLS = False
    MAIL_USERNAME = 'root'
    MAIL_PASSWORD = None
    PORTAL_MAIL_SUBJECT_PREFIX = '[traipor]'
    PORTAL_MAIL_SENDER = 'traipor <traipor@portal-webserver.de>'

    # TODO change for production deployment
    PORTAL_ADMIN = 'dawe@localhost'

    MAX_CONTENT_LENGTH = 10 * 1024 * 1024   # max 10MB uploads

    BOOTSTRAP_SERVE_LOCAL = True

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'postgresql://portaldev:portaldevpw@localhost:5432/portaldevdb'


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'postgresql://portaltest:portaltestpw@localhost:5432/portaltestdb'
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    # TODO change password for production deployment
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://portalprod:portalprodpw@localhost:5432/portalproddb'

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

        # handle proxy server headers
        from werkzeug.contrib.fixers import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app)

        # email errors to the administrators
        import logging
        from logging.handlers import SMTPHandler
        credentials = None
        secure = None
        if getattr(cls, 'MAIL_USERNAME', None) is not None:
            credentials = (cls.MAIL_USERNAME, cls.MAIL_PASSWORD)
            if getattr(cls, 'MAIL_USE_TLS', None):
                secure = ()
        mail_handler = SMTPHandler(
            mailhost=(cls.MAIL_SERVER, cls.MAIL_PORT),
            fromaddr=cls.PORTAL_MAIL_SENDER,
            toaddrs=[cls.PORTAL_ADMIN],
            subject=cls.PORTAL_MAIL_SUBJECT_PREFIX + ' Application Error',
            credentials=credentials,
            secure=secure)
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)


class UnixConfig(ProductionConfig):
    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)

        # log to syslog
        import logging
        from logging.handlers import SysLogHandler
        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.WARNING)
        app.logger.addHandler(syslog_handler)


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'unix': UnixConfig,

    'default': DevelopmentConfig
}
