# schwab_dashboard
A slightly better way to watch how you lose money

You will need:

An approved schwab personal trader API app. App key and secret. A Default account number is the superior way to run
the dashboard, but it is not required.

Install instructions

1. Register App with schwab developer portal
1. Install python 3.10 or greater (instructions vary by platform)
2. pip install -r requirements.txt
3. python get_refresh_token.py

Recommended App Callback: https://127.0.0.1:8501/

This will prompt you for:

    1. App key
    2. App secret
    3. callback uri
    4. default account number (optional, but it makes things flow better, you can add it later too)

Then it will provide you with a page to go to for schwab login. Copy and paste callback url into the prompt. This will create your token.

To confirm that the config works, the script will pull all your accounts. This is a good place to grab the account number and paste it into ```schwab.app_config.json``` if you did not enter a default account number


5. Start dashbaord
```streamlit run streamlit_dashboard.py```

If you receive an error about streamlit running setup twice, just refresh the and it should work (I am looking into this)

click the link in the output or click below:
http://localhost:8501


### Storing your auth token to AWS

Use multiple machines? Watch to use the token with another app? I got your back.
Supports using free-tier dynamodn with AWS and will save the key. You must make a table and a primary key.
open ```dashboard_config.yaml``` and set useaws to "true" and then enter dynamodb values under "dyanmodb".