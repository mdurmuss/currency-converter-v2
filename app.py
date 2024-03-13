from flask import Flask, jsonify, request, render_template
import requests
from bs4 import BeautifulSoup
import datetime

app = Flask(__name__)
RESPONSE = requests.get('https://www.tcmb.gov.tr/kurlar/today.xml')
SOUP = BeautifulSoup(RESPONSE.content, 'xml')
RAW_CURRENCY_LIST = SOUP.find_all('Currency')
LAST_UPDATE_DATE = datetime.datetime.strptime(RESPONSE.headers['Last-Modified'],
                                              '%a, %d %b %Y %H:%M:%S %Z') + datetime.timedelta(hours=3)


def fetch_currencies() -> list:
    """
    Fetch currency list from TCMB and returns it as a list of tuples.
    (currency_code, currency_name, forex_buying, forex_selling)
    """
    currency_list_with_code_and_forex_info = []
    for currency in RAW_CURRENCY_LIST:
        if currency.get('Kod') and currency.get('Kod') != 'XDR':
            kod = currency.get('Kod')
            currency_name = currency.CurrencyName.text
            forex_buying = currency.ForexBuying.text
            forex_selling = currency.ForexSelling.text
            currency_list_with_code_and_forex_info.append((kod, currency_name, forex_buying, forex_selling))
    currency_list_with_code_and_forex_info.append(('TRY', 'TÜRK LİRASI', 1, 1))
    return currency_list_with_code_and_forex_info


@app.route('/')
def home():
    """
    Render the index.html template with currency list and last update date.
    """
    currencies = fetch_currencies()
    return render_template('index.html', currencies=currencies,
                           last_update=LAST_UPDATE_DATE)


@app.route('/convert', methods=['POST'])
def convert():
    """
    Convert the given amount from one currency to another.
    """
    data = request.get_json()

    amount = float(data['amount'])
    from_currency = data['from_currency']
    to_currency = data['to_currency']

    if amount <= 0:
        return jsonify({'conversionResult': 'Amount must be greater than 0'})

    from_rate = SOUP.find('Currency', {'Kod': from_currency})
    to_rate = SOUP.find('Currency', {'Kod': to_currency})

    # Dönüştürme işlemi yap
    if from_currency == 'TRY':
        if to_currency == 'TRY':
            result = f'{amount} {from_currency} = {amount} {to_currency}'
            return jsonify({'conversionResult': result})
        converted_amount = amount / float(to_rate.ForexBuying.text)
    elif to_currency == 'TRY':
        if from_currency == 'TRY':
            result = f'{amount} {from_currency} = {amount} {to_currency}'
            return jsonify({'conversionResult': result})
        converted_amount = amount * float(from_rate.ForexBuying.text)
    else:
        converted_amount = (amount / float(to_rate.ForexBuying.text)) * float(from_rate.ForexBuying.text)

    result = f'{amount} {from_currency} = {converted_amount:.2f} {to_currency}'

    # JSON olarak sonucu döndür
    return jsonify({'conversionResult': result})


if __name__ == '__main__':
    app.run(debug=True)
