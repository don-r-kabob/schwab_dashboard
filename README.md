# schwab_dashboard
A slightly better way to watch how you lose money

You will need:

An approved schwab personal trader API app. App key and secret. A Default account number is the superior way to run
the dashboard, but it is not required.

Install dependencies:

```pip3 install -r requirements.txt```


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

To confirm that the config works, the script will pull all your accounts. This is a good place to grab the account number and paste it into ```schwab.app_config.json```


Start dashbaord
```streamlit run streamlit_dashboard.py```

If you receive an error about streamlit running setup twice, just refresh the and it should work (I am looking into this)

click the link in the output or click below:
http://localhost:8501