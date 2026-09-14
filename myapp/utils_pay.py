import requests
from decouple import config

PAYSTACK_BASE_URL = "https://api.paystack.co"
PAYSTACK_SECRET_KEY = config('PAYSTACK_SECRET_KEY')
PAYSTACK_CALLBACK_URL = config('PAYSTACK_CALLBACK_URL', default='http://127.0.0.1:8000')


headers = {
    "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
    "Content-Type": "application/json",
}

def initializePaystackPayment(email : str, amount : float, reference : str):

    # Amount must be in the smallest currency unit (e.g., kobo for NGN, multiply by 100)
    data = {
        "email": email,
        "amount": amount,  # Represents 5,000 NGN
        "callback_url":PAYSTACK_CALLBACK_URL+'/paystack-success-redirect/',
        "reference" : reference
    }
    try :
        response = requests.post(f'{PAYSTACK_BASE_URL}/transaction/initialize', json=data, headers=headers)

        if response.status_code == 200:
            res_data = response.json()
            authorization_url = res_data["data"]["authorization_url"]
            reference = res_data["data"]["reference"]
            print(f"Redirect user to: {authorization_url}")
            print(f"Transaction reference: {reference}")
            return {
                "success" : True ,
                "payment_url" : authorization_url,
                'reference' : reference
            }
        else:
            print("Error:", response.json())
            return None
    except Exception as e :
        print(e)
        return None


def verifyPayment( reference : str):

    # Amount must be in the smallest currency unit (e.g., kobo for NGN, multiply by 100)
    try :
        response = requests.get(f'{PAYSTACK_BASE_URL}/transaction/verify/{reference}', headers=headers)

        if response.status_code == 200:
            res_data = response.json()
            if res_data['data']['status'] == 'success':
                return {
                    'success': True,
                    'amount' : res_data['data']['amount'] 
                }
            else :
                return {
                    'success' :False
                }
        else:
            print("Error:", response.json())
            
            return None
    except Exception as e :
        print(e)
        return None

# initializePayment("jojo453@gmail.com",6500000)
#  http://127.0.0.1:8000/paystack-success-redirect/?trxref=PAY-30A8F1B31955&reference=PAY-30A8F1B31955

'''
#!/bin/sh
url="https://api.paystack.co/transaction/verify/PAY-30A8F1B31955"
authorization="Authorization: Bearer sk_test_5d934af648940b265e1df2c73041e2454d4d7e14"

curl "$url" -H "$authorization" -X GET

'''

# verifyPayment('PAY-30A8F1B31955')