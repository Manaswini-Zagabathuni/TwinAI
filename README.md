#  TwinAI - Advanced Edition

An AI-powered writing twin that learns your communication style and generates replies that sound exactly like you. Built with Streamlit + Claude (Anthropic).

##  Features (vs original)
 
| Feature | Original | Advanced |
|---|---|---|
| UI | None (CLI only) | Full web dashboard |
| Writing samples | Hardcoded | Add/remove dynamically |
| Style analysis | None | Auto-detects your traits |
| Reply variants | 1 | Up to 3 at once |
| Platform support | Generic | Email, Slack, LinkedIn, SMS |
| Tone control | None | Formal / Casual / Shorter / Detailed |
| History | None | Full history + JSON export |
| Model | Amazon Nova (broken) | Claude Sonnet (reliable) |

---

##  Deploy on Streamlit Community Cloud (Free)

### Step 1 - Push to GitHub
```bash
git init
git add .
git commit -m "TwinAI advanced"
gh repo create twinai-advanced --public --push
```

### Step 2 - Deploy
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click **New app**
4. Select your repo, branch `main`, file `app.py`
5. Click **Deploy**

### Step 3 - Add your API key (secrets)
In Streamlit Cloud dashboard → your app → **Settings → Secrets**, add:
```toml
ANTHROPIC_API_KEY = "sk-ant-your-key-here"
```

> **Get a free Anthropic API key:** [console.anthropic.com](https://console.anthropic.com)

---

##  Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

##  Project Structure

```
twinai/
├── app.py            # Main Streamlit app
├── requirements.txt  # Dependencies
└── README.md
```
