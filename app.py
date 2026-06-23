from flask import Flask, render_template, request
import json
import os
from urllib import error, request as urlrequest
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, template_folder="template")


# ---------------------------
# FALLBACK ENGINE (NO AI)
# ---------------------------
def _build_fallback_playlist(song_url, share_comment, private_notes, mood="auto", error_message=None):

    mood_text = (share_comment + " " + private_notes).strip().lower()

    # If user manually selects mood → override keyword detection
    if mood != "auto":
        mood_text = mood

    if any(word in mood_text for word in ["sad", "down", "tired", "lonely", "empty"]):
        mood_summary = "You sound like you need gentle comfort and emotional space."
        tracks = [
            {"title": "The Night We Met", "artist": "Lord Huron", "why": "Soft reflective emotional space."},
            {"title": "Liability", "artist": "Lorde", "why": "Feels like a private journal."},
            {"title": "Fix You", "artist": "Coldplay", "why": "Emotional release and hope."},
            {"title": "Skinny Love", "artist": "Bon Iver", "why": "Raw acoustic sadness."},
            {"title": "Holocene", "artist": "Bon Iver", "why": "Calm grounding atmosphere."},
        ]

    elif any(word in mood_text for word in ["happy", "excited", "hype", "party"]):
        mood_summary = "You sound upbeat and energized."
        tracks = [
            {"title": "Levitating", "artist": "Dua Lipa", "why": "High energy groove."},
            {"title": "Blinding Lights", "artist": "The Weeknd", "why": "Fast synth-driven vibe."},
            {"title": "As It Was", "artist": "Harry Styles", "why": "Light and catchy mood."},
            {"title": "On Top of the World", "artist": "Imagine Dragons", "why": "Feel-good energy."},
            {"title": "Good as Hell", "artist": "Lizzo", "why": "Confidence boost."},
        ]

    else:
        mood_summary = "Balanced and reflective mood."
        tracks = [
            {"title": "Sunset Lover", "artist": "Petit Biscuit", "why": "Calm warm vibe."},
            {"title": "Electric Feel", "artist": "MGMT", "why": "Light groove energy."},
            {"title": "Midnight City", "artist": "M83", "why": "Dreamy atmosphere."},
            {"title": "Dreams", "artist": "Fleetwood Mac", "why": "Easy listening flow."},
            {"title": "Yellow", "artist": "Coldplay", "why": "Soft optimistic tone."},
        ]

    if song_url.strip():
        tracks.insert(0, {
            "title": "Your selected Spotify song",
            "artist": "Seed track",
            "why": "Used as mood reference."
        })

    playlist = {
        "mood_summary": mood_summary,
        "tracks": tracks,
        "engine": "Fallback mood engine"
    }

    if error_message:
        playlist["error"] = error_message

    return playlist


# ---------------------------
# OPENAI CALL
# ---------------------------
def _generate_with_gpt(song_url, share_comment, private_notes):

    api_key = os.getenv("OPENAI_API_KEY", "").strip()

    if not api_key:
        return _build_fallback_playlist(
            song_url,
            share_comment,
            private_notes,
            error_message="Missing API key"
        )

    prompt = (
        "You are a music mood curator. "
        "Return STRICT JSON with mood_summary and 6 tracks."
    )

    body = {
        "model": "gpt-4o-mini",
        "input": [
            {
                "role": "system",
                "content": [{"type": "input_text", "text": prompt}]
            },
            {
                "role": "user",
                "content": [{"type": "input_text", "text": json.dumps({
                    "spotify_song_url": song_url,
                    "share_comment": share_comment,
                    "private_notes": private_notes
                })}]
            }
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "mood_playlist",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "mood_summary": {"type": "string"},
                        "tracks": {
                            "type": "array",
                            "minItems": 6,
                            "maxItems": 6,
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string"},
                                    "artist": {"type": "string"},
                                    "why": {"type": "string"}
                                },
                                "required": ["title", "artist", "why"]
                            }
                        }
                    },
                    "required": ["mood_summary", "tracks"]
                }
            }
        }
    }

    req = urlrequest.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urlrequest.urlopen(req, timeout=25) as response:
            payload = json.loads(response.read().decode("utf-8"))

            text_output = payload.get("output_text", "")

            parsed = json.loads(text_output) if text_output else {}

            if not parsed.get("tracks"):
                return _build_fallback_playlist(
                    song_url,
                    share_comment,
                    private_notes,
                    error_message="Empty AI response"
                )

            parsed["engine"] = "GPT-4o mini"
            return parsed

    except Exception as exc:
        return _build_fallback_playlist(
            song_url,
            share_comment,
            private_notes,
            error_message=str(exc)
        )


# ---------------------------
# WRAPPER (AI OR FALLBACK)
# ---------------------------
def _generate_with_gpt_or_fallback(song_url, share_comment, private_notes, mood):

    api_key = os.getenv("OPENAI_API_KEY", "").strip()

    if not api_key or mood != "auto":
        return _build_fallback_playlist(
            song_url,
            share_comment,
            private_notes,
            mood=mood
        )

    return _generate_with_gpt(song_url, share_comment, private_notes)


# ---------------------------
# ROUTES
# ---------------------------
@app.route("/")
def home():
    return render_template("index.html", playlist=None, form_data={})


@app.route("/create-playlist", methods=["POST"])
def create_playlist():

    song_url = request.form.get("songUrl", "")
    share_comment = request.form.get("shareComment", "")
    private_notes = request.form.get("privateNotes", "")
    mood = request.form.get("mood", "auto")

    playlist = _generate_with_gpt_or_fallback(
        song_url,
        share_comment,
        private_notes,
        mood
    )

    form_data = {
        "songUrl": song_url,
        "shareComment": share_comment,
        "privateNotes": private_notes,
        "mood": mood
    }

    return render_template("index.html", playlist=playlist, form_data=form_data)


if __name__ == "__main__":
    app.run(debug=True)