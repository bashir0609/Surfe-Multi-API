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
        sid = request.cookies.get(app.session_cookie_name)
        if not sid:
            # If no session ID, create a new one
            sid = os.urandom(32).hex()
            return SupabaseSession(sid=sid, new=True)

        try:
            # Fetch the session from the database
            response = self.client.table("sessions").select("data, expiry").eq("id", sid).execute()
            
            if not response.data:
                # Session ID from cookie not found in DB
                return SupabaseSession(sid=sid, new=True)

            session_data = response.data[0]
            expiry_str = session_data.get("expiry")
            
            # Check if the session is expired
            if expiry_str:
                expiry = datetime.fromisoformat(expiry_str)
                if expiry < datetime.utcnow().replace(tzinfo=expiry.tzinfo):
                    # Session is expired, treat as new
                    return SupabaseSession(sid=sid, new=True)

            # Session is valid, load its data
            data = session_data.get("data")
            return SupabaseSession(data, sid=sid)
        except Exception as e:
            logger.error(f"Error opening session {sid}: {e}")
            # On error, create a fresh session to avoid crashing
            return SupabaseSession(sid=sid, new=True)


    def save_session(self, app, session, response):
        """This is called at the end of each request to save the session."""
        domain = self.get_cookie_domain(app)
        path = self.get_cookie_path(app)

        if not session:
            # If session was deleted, clear the cookie
            if session.modified:
                try:
                    self.client.table("sessions").delete().eq("id", session.sid).execute()
                except Exception as e:
                    logger.error(f"Error deleting session {session.sid}: {e}")
                response.delete_cookie(app.session_cookie_name, domain=domain, path=path)
            return

        if not self.should_set_cookie(app, session):
            return

        # Calculate expiry date
        lifetime = app.permanent_session_lifetime
        expiry = datetime.utcnow() + lifetime

        try:
            # Save the session data to Supabase
            self.client.table("sessions").upsert({
                "id": session.sid,
                "data": dict(session),
                "expiry": expiry.isoformat()
            }).execute()
        except Exception as e:
            logger.error(f"Error saving session {session.sid}: {e}")
            # Don't set the cookie if the save failed
            return

        # Set the session cookie on the user's browser
        response.set_cookie(
            app.session_cookie_name,
            session.sid,
            expires=self.get_expiration_time(app, session),
            httponly=self.get_cookie_httponly(app),
            domain=domain,
            path=path,
            secure=self.get_cookie_secure(app),
            samesite=self.get_cookie_samesite(app),
        )
