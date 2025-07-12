import json
import os
from datetime import datetime, timedelta
from flask.sessions import SessionInterface, SessionMixin
from werkzeug.datastructures import CallbackDict
import logging

logger = logging.getLogger(__name__)

class SupabaseSession(CallbackDict, SessionMixin):
    """Custom session object that uses Supabase."""
    def __init__(self, initial=None, sid=None, new=False):
        def on_update(self):
            self.modified = True
        CallbackDict.__init__(self, initial, on_update)
        self.sid = sid
        self.new = new
        self.modified = False

class SupabaseSessionInterface(SessionInterface):
    """A session interface that uses Supabase as a backend."""

    def __init__(self, client):
        if client is None:
            raise ValueError("Supabase client cannot be None.")
        self.client = client

    def open_session(self, app, request):
        """This is called at the beginning of each request to load the session."""
        cookie_name = app.config.get("SESSION_COOKIE_NAME", "session")
        sid = request.cookies.get(cookie_name)
        
        if not sid:
            sid = os.urandom(32).hex()
            return SupabaseSession(sid=sid, new=True)

        try:
            # FINAL FIX: Access the underlying client object with .client
            response = self.client.client.table("sessions").select("data, expiry").eq("id", sid).execute()
            
            if not response.data:
                return SupabaseSession(sid=sid, new=True)

            session_data = response.data[0]
            expiry_str = session_data.get("expiry")
            
            if expiry_str:
                expiry = datetime.fromisoformat(expiry_str)
                if expiry < datetime.utcnow().replace(tzinfo=expiry.tzinfo):
                    return SupabaseSession(sid=sid, new=True)

            data = session_data.get("data")
            return SupabaseSession(data, sid=sid)
        except Exception as e:
            logger.error(f"Error opening session {sid}: {e}")
            return SupabaseSession(sid=sid, new=True)


    def save_session(self, app, session, response):
        """This is called at the end of each request to save the session."""
        domain = self.get_cookie_domain(app)
        path = self.get_cookie_path(app)
        cookie_name = app.config.get("SESSION_COOKIE_NAME", "session")

        if not session:
            if session.modified:
                try:
                    # FINAL FIX: Access the underlying client object with .client
                    self.client.client.table("sessions").delete().eq("id", session.sid).execute()
                except Exception as e:
                    logger.error(f"Error deleting session {session.sid}: {e}")
                response.delete_cookie(cookie_name, domain=domain, path=path)
            return

        if not self.should_set_cookie(app, session):
            return

        lifetime = app.permanent_session_lifetime
        expiry = datetime.utcnow() + lifetime

        try:
            # FINAL FIX: Access the underlying client object with .client
            self.client.client.table("sessions").upsert({
                "id": session.sid,
                "data": dict(session),
                "expiry": expiry.isoformat()
            }).execute()
        except Exception as e:
            logger.error(f"Error saving session {session.sid}: {e}")
            return

        response.set_cookie(
            cookie_name,
            session.sid,
            expires=self.get_expiration_time(app, session),
            httponly=self.get_cookie_httponly(app),
            domain=domain,
            path=path,
            secure=self.get_cookie_secure(app),
            samesite=self.get_cookie_samesite(app),
        )
