"""Start the NAADP binder census dashboard on http://127.0.0.1:8175 (local only, read-only, reads git HEAD).

Run: python run_web.py   (needs: pip install -r requirements-web.txt)
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run("src.web.app:app", host="127.0.0.1", port=8175)
