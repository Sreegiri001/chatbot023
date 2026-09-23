import os
from flask import Flask,render_template,request,jsonify,session
from dotenv import load_dotenv
from google import genai
from chatbot_config import CHATBOT_TITLE,CHATBOT_DESCRIPTION,SYSTEM_PROMPT,DOMAIN_RULES,OUT_OF_SCOPE_RESPONSE
load_dotenv()
app=Flask(__name__);app.secret_key=os.getenv("FLASK_SECRET_KEY","change-this");app.config["MAX_CONTENT_LENGTH"]=16384
key=os.getenv("GEMINI_API_KEY","");client=genai.Client(api_key=key) if key else None
def domain_match(text): return bool(text.strip()) and any(x.lower() in text.lower() for x in DOMAIN_RULES)
@app.get("/")
def home(): return render_template("index.html",title=CHATBOT_TITLE,description=CHATBOT_DESCRIPTION)
@app.post("/api/chat")
def chat():
 d=request.get_json(silent=True) or {};m=str(d.get("message","")).strip()
 if not m:return jsonify(error="Please enter a message."),400
 if len(m)>4000:return jsonify(error="Message too long."),400
 if not domain_match(m):return jsonify(reply=OUT_OF_SCOPE_RESPONSE,out_of_scope=True)
 if not key:return jsonify(error="Add GEMINI_API_KEY to .env."),503
 h=session.get("history",[])
 try:
  r=client.models.generate_content(model="gemini-3.1-flash-lite",contents=SYSTEM_PROMPT+"\n"+str(h[-10:])+"\nUSER: "+m,config={"temperature":.35,"system_instruction":SYSTEM_PROMPT})
  reply=(r.text or "").strip() or "Please try again.";h += [{"role":"user","content":m},{"role":"assistant","content":reply}];session["history"]=h[-20:]
  return jsonify(reply=reply,out_of_scope=False)
 except Exception:
  app.logger.exception("Gemini error");return jsonify(error="AI service unavailable."),502
@app.post("/api/reset")
def reset():session.pop("history",None);return jsonify(ok=True)
if __name__=="__main__":app.run(host="0.0.0.0",port=int(os.getenv("PORT","5000")))
