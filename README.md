# schwab_dashboard
A slightly better way to watch how you lose money


Getting a token:

```commandline
python3 utils/get_refresh_token.py
```

This will prompt you for:

1. App key
2. App secret
3. callback uri
4. default account number (optional, but it makes things flow better, you can add it later too)

Then it will provide you with a page to go to for schwab login. Copy and bpase callback url into the prompt. This will create your token.

Start dashbaord
```streamlit run streamlit_dashboard```

http://localhost:8501